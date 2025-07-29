// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

// Aave V3 Pool interface for flashloans
interface IPool {
    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

// Generic DEX interface
interface IDEX {
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function getAmountsOut(uint256 amountIn, address[] calldata path)
        external
        view
        returns (uint256[] memory amounts);
}

/**
 * @title FlashloanArbitrage
 * @dev Smart contract for executing flashloan arbitrage trades
 */
contract FlashloanArbitrage is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    // Events
    event ArbitrageExecuted(
        address indexed token,
        uint256 amount,
        uint256 profit,
        address indexed dexA,
        address indexed dexB
    );

    event FlashloanExecuted(
        address indexed asset,
        uint256 amount,
        uint256 premium
    );

    // Aave pool address (mainnet) - Correct checksummed address
    IPool public constant AAVE_POOL = IPool(0x87870Bca3F8Fc6AA600bDEDbafB3Ba45c17D2B58);
    
    // DEX configurations
    struct DEXConfig {
        address router;
        string name;
        bool isActive;
    }

    mapping(string => DEXConfig) public dexConfigs;
    
    // Minimum profit threshold (in wei)
    uint256 public minProfitThreshold = 0.01 ether;
    
    // Maximum slippage tolerance (basis points, 50 = 0.5%)
    uint256 public maxSlippage = 50;

    constructor() Ownable(msg.sender) {
        // Initialize popular DEX configurations
        dexConfigs["uniswap"] = DEXConfig({
            router: 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D,
            name: "Uniswap V2",
            isActive: true
        });
        
        dexConfigs["sushiswap"] = DEXConfig({
            router: 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F,
            name: "SushiSwap",
            isActive: true
        });
    }

    /**
     * @dev Execute arbitrage using flashloan
     * @param asset Token to borrow and arbitrage
     * @param amount Amount to borrow
     * @param dexA First DEX to buy from
     * @param dexB Second DEX to sell to
     * @param path Trading path [tokenA, tokenB, ...]
     */
    function executeArbitrage(
        address asset,
        uint256 amount,
        string calldata dexA,
        string calldata dexB,
        address[] calldata path
    ) external onlyOwner nonReentrant {
        require(dexConfigs[dexA].isActive && dexConfigs[dexB].isActive, "DEX not active");
        require(path.length >= 2, "Invalid path");
        require(path[0] == asset, "Path must start with borrowed asset");

        // Check if arbitrage is profitable before executing
        require(isArbitrageProfitable(amount, dexA, dexB, path), "Arbitrage not profitable");

        // Prepare flashloan parameters
        address[] memory assets = new address[](1);
        uint256[] memory amounts = new uint256[](1);
        uint256[] memory modes = new uint256[](1);
        
        assets[0] = asset;
        amounts[0] = amount;
        modes[0] = 0; // No debt mode

        // Encode parameters for flashloan callback
        bytes memory params = abi.encode(dexA, dexB, path, amount);

        // Execute flashloan
        AAVE_POOL.flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            params,
            0
        );
    }

    /**
     * @dev Aave flashloan callback
     */
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        require(msg.sender == address(AAVE_POOL), "Invalid caller");
        require(initiator == address(this), "Invalid initiator");

        // Decode parameters
        (string memory dexA, string memory dexB, address[] memory path, uint256 borrowAmount) = 
            abi.decode(params, (string, string, address[], uint256));

        address asset = assets[0];
        uint256 amountOwed = amounts[0] + premiums[0];

        // Execute arbitrage trade
        uint256 profit = _executeArbitrageTrade(asset, borrowAmount, dexA, dexB, path);

        // Ensure we have enough to repay the flashloan
        require(IERC20(asset).balanceOf(address(this)) >= amountOwed, "Insufficient balance to repay");

        // Approve repayment
        IERC20(asset).forceApprove(address(AAVE_POOL), amountOwed);

        emit FlashloanExecuted(asset, amounts[0], premiums[0]);
        emit ArbitrageExecuted(asset, borrowAmount, profit, dexConfigs[dexA].router, dexConfigs[dexB].router);

        return true;
    }

    /**
     * @dev Execute the actual arbitrage trade
     */
    function _executeArbitrageTrade(
        address asset,
        uint256 amount,
        string memory dexA,
        string memory dexB,
        address[] memory path
    ) internal returns (uint256 profit) {
        uint256 initialBalance = IERC20(asset).balanceOf(address(this));

        // Buy from DEX A
        IERC20(asset).forceApprove(dexConfigs[dexA].router, amount);
        
        uint256[] memory amountsOut = IDEX(dexConfigs[dexA].router).swapExactTokensForTokens(
            amount,
            0, // Accept any amount of tokens out
            path,
            address(this),
            block.timestamp + 300
        );

        // Get the intermediate token and amount
        address intermediateToken = path[path.length - 1];
        uint256 intermediateAmount = amountsOut[amountsOut.length - 1];

        // Create reverse path for selling back
        address[] memory reversePath = new address[](path.length);
        for (uint256 i = 0; i < path.length; i++) {
            reversePath[i] = path[path.length - 1 - i];
        }

        // Sell on DEX B
        IERC20(intermediateToken).forceApprove(dexConfigs[dexB].router, intermediateAmount);
        
        IDEX(dexConfigs[dexB].router).swapExactTokensForTokens(
            intermediateAmount,
            0, // Accept any amount of tokens out
            reversePath,
            address(this),
            block.timestamp + 300
        );

        uint256 finalBalance = IERC20(asset).balanceOf(address(this));
        profit = finalBalance > initialBalance ? finalBalance - initialBalance : 0;

        return profit;
    }

    /**
     * @dev Check if arbitrage opportunity is profitable
     */
    function isArbitrageProfitable(
        uint256 amount,
        string memory dexA,
        string memory dexB,
        address[] memory path
    ) public view returns (bool) {
        try this.calculateArbitrageProfit(amount, dexA, dexB, path) returns (uint256 profit) {
            return profit > minProfitThreshold;
        } catch {
            return false;
        }
    }

    /**
     * @dev Calculate potential arbitrage profit
     */
    function calculateArbitrageProfit(
        uint256 amount,
        string memory dexA,
        string memory dexB,
        address[] memory path
    ) external view returns (uint256 profit) {
        // Get output from DEX A
        uint256[] memory amountsOutA = IDEX(dexConfigs[dexA].router).getAmountsOut(amount, path);
        uint256 intermediateAmount = amountsOutA[amountsOutA.length - 1];

        // Create reverse path
        address[] memory reversePath = new address[](path.length);
        for (uint256 i = 0; i < path.length; i++) {
            reversePath[i] = path[path.length - 1 - i];
        }

        // Get output from DEX B
        uint256[] memory amountsOutB = IDEX(dexConfigs[dexB].router).getAmountsOut(intermediateAmount, reversePath);
        uint256 finalAmount = amountsOutB[amountsOutB.length - 1];

        // Calculate profit (subtract flashloan fee ~0.09%)
        uint256 flashloanFee = (amount * 9) / 10000; // 0.09% fee
        profit = finalAmount > (amount + flashloanFee) ? finalAmount - amount - flashloanFee : 0;

        return profit;
    }

    /**
     * @dev Add or update DEX configuration
     */
    function updateDEXConfig(string calldata name, address router, bool isActive) external onlyOwner {
        dexConfigs[name] = DEXConfig({
            router: router,
            name: name,
            isActive: isActive
        });
    }

    /**
     * @dev Update minimum profit threshold
     */
    function updateMinProfitThreshold(uint256 newThreshold) external onlyOwner {
        minProfitThreshold = newThreshold;
    }

    /**
     * @dev Emergency withdrawal function
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) {
            payable(owner()).transfer(amount);
        } else {
            IERC20(token).safeTransfer(owner(), amount);
        }
    }

    /**
     * @dev Receive ETH
     */
    receive() external payable {}
}