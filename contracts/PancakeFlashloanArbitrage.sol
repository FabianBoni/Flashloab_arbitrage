// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// PancakeSwap V2 interfaces for flashloans
interface IPancakeCallee {
    function pancakeCall(address sender, uint amount0, uint amount1, bytes calldata data) external;
}

interface IPancakePair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function token0() external view returns (address);
    function token1() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

interface IPancakeFactory {
    function getPair(address tokenA, address tokenB) external view returns (address pair);
}

// DEX Router interface
interface IDEXRouter {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);

    function getAmountsOut(uint amountIn, address[] calldata path)
        external view returns (uint[] memory amounts);
}

/**
 * @title PancakeFlashloanArbitrage
 * @dev Real flashloan arbitrage using PancakeSwap flashloans on BSC
 */
contract PancakeFlashloanArbitrage is ReentrancyGuard, Ownable, IPancakeCallee {
    
    // DEX configuration
    struct DEXConfig {
        address router;
        bool isActive;
        uint256 fee; // Fee in basis points
    }

    // Arbitrage execution data
    struct ArbitrageData {
        address asset;
        uint256 amount;
        address dexARouter;
        address dexBRouter;
        address[] path;
        address[] reversePath;
        uint256 minProfit;
        address borrowToken;
        uint256 borrowAmount;
    }

    // State variables
    mapping(string => DEXConfig) public dexConfigs;
    mapping(address => bool) public authorizedCallers;
    
    address public constant PANCAKE_FACTORY = 0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73;
    uint256 public minProfitThreshold = 1e15; // 0.001 ETH minimum profit
    
    // Events
    event ArbitrageExecuted(
        address indexed asset,
        uint256 amount,
        uint256 profit,
        string dexA,
        string dexB
    );
    
    event FlashloanExecuted(
        address indexed pair,
        address indexed token,
        uint256 amount,
        uint256 fee
    );

    constructor() Ownable(msg.sender) {
        authorizedCallers[msg.sender] = true;
        
        // Configure PancakeSwap V2
        dexConfigs["PancakeSwap V2"] = DEXConfig({
            router: 0x10ED43C718714eb63d5aA57B78B54704E256024E,
            isActive: true,
            fee: 25 // 0.25%
        });
        
        // Configure Biswap
        dexConfigs["Biswap"] = DEXConfig({
            router: 0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8,
            isActive: true,
            fee: 10 // 0.1%
        });
    }

    modifier onlyAuthorized() {
        require(authorizedCallers[msg.sender], "Not authorized");
        _;
    }

    /**
     * @dev Execute arbitrage with PancakeSwap flashloan
     */
    function executeArbitrage(
        address asset,
        uint256 amount,
        string calldata dexA,
        string calldata dexB,
        address[] calldata path,
        uint256 minProfit
    ) external onlyAuthorized nonReentrant {
        require(dexConfigs[dexA].isActive && dexConfigs[dexB].isActive, "DEX not active");
        require(path.length >= 2, "Invalid path");
        
        // Create reverse path
        address[] memory reversePath = new address[](path.length);
        for (uint i = 0; i < path.length; i++) {
            reversePath[i] = path[path.length - 1 - i];
        }
        
        // Prepare arbitrage data
        ArbitrageData memory arbData = ArbitrageData({
            asset: asset,
            amount: amount,
            dexARouter: dexConfigs[dexA].router,
            dexBRouter: dexConfigs[dexB].router,
            path: path,
            reversePath: reversePath,
            minProfit: minProfit,
            borrowToken: path[0],
            borrowAmount: amount
        });
        
        // Find pair for flashloan
        address pair = IPancakeFactory(PANCAKE_FACTORY).getPair(path[0], path[1]);
        require(pair != address(0), "Pair not found");
        
        // Determine which token to borrow and amounts
        address token0 = IPancakePair(pair).token0();
        address token1 = IPancakePair(pair).token1();
        
        uint256 amount0Out = path[0] == token0 ? amount : 0;
        uint256 amount1Out = path[0] == token1 ? amount : 0;
        
        // Encode arbitrage data
        bytes memory data = abi.encode(arbData, dexA, dexB);
        
        // Execute flashloan
        IPancakePair(pair).swap(amount0Out, amount1Out, address(this), data);
    }

    /**
     * @dev PancakeSwap flashloan callback
     */
    function pancakeCall(
        address sender,
        uint amount0,
        uint amount1,
        bytes calldata data
    ) external override {
        // Verify caller is a valid PancakeSwap pair
        address token0 = IPancakePair(msg.sender).token0();
        address token1 = IPancakePair(msg.sender).token1();
        address pair = IPancakeFactory(PANCAKE_FACTORY).getPair(token0, token1);
        require(msg.sender == pair, "Invalid caller");
        require(sender == address(this), "Invalid sender");
        
        // Decode arbitrage data
        (ArbitrageData memory arbData, string memory dexA, string memory dexB) = abi.decode(data, (ArbitrageData, string, string));
        
        uint256 borrowedAmount = amount0 > 0 ? amount0 : amount1;
        
        // Execute arbitrage
        uint256 profit = _executeArbitrageTrade(arbData);
        
        // Calculate flashloan fee (0.25% for PancakeSwap)
        uint256 fee = (borrowedAmount * 25) / 10000;
        uint256 repayAmount = borrowedAmount + fee;
        
        require(profit >= arbData.minProfit, "Insufficient profit");
        
        // Repay flashloan
        IERC20(arbData.borrowToken).transfer(msg.sender, repayAmount);
        
        emit FlashloanExecuted(msg.sender, arbData.borrowToken, borrowedAmount, fee);
        emit ArbitrageExecuted(arbData.asset, arbData.amount, profit, dexA, dexB);
    }

    /**
     * @dev Execute the actual arbitrage trade
     */
    function _executeArbitrageTrade(ArbitrageData memory arbData) internal returns (uint256) {
        uint256 initialBalance = IERC20(arbData.borrowToken).balanceOf(address(this));
        
        // Step 1: Trade on DEX A
        IERC20(arbData.path[0]).approve(arbData.dexARouter, arbData.amount);
        
        uint[] memory amountsA = IDEXRouter(arbData.dexARouter).swapExactTokensForTokens(
            arbData.amount,
            0, // Accept any amount of output token
            arbData.path,
            address(this),
            block.timestamp + 300
        );
        
        uint256 intermediateAmount = amountsA[amountsA.length - 1];
        
        // Step 2: Trade back on DEX B
        IERC20(arbData.reversePath[0]).approve(arbData.dexBRouter, intermediateAmount);
        
        uint[] memory amountsB = IDEXRouter(arbData.dexBRouter).swapExactTokensForTokens(
            intermediateAmount,
            arbData.amount, // Minimum amount to get back
            arbData.reversePath,
            address(this),
            block.timestamp + 300
        );
        
        uint256 finalBalance = IERC20(arbData.borrowToken).balanceOf(address(this));
        uint256 profit = finalBalance - initialBalance;
        
        return profit;
    }

    /**
     * @dev Calculate potential profit (view function)
     */
    function calculateArbitrageProfit(
        uint256 amount,
        string memory dexA,
        string memory dexB,
        address[] memory path
    ) external view returns (uint256) {
        if (!dexConfigs[dexA].isActive || !dexConfigs[dexB].isActive) {
            return 0;
        }
        
        try IDEXRouter(dexConfigs[dexA].router).getAmountsOut(amount, path) returns (uint[] memory amountsA) {
            // Create reverse path
            address[] memory reversePath = new address[](path.length);
            for (uint i = 0; i < path.length; i++) {
                reversePath[i] = path[path.length - 1 - i];
            }
            
            try IDEXRouter(dexConfigs[dexB].router).getAmountsOut(amountsA[amountsA.length - 1], reversePath) returns (uint[] memory amountsB) {
                uint256 finalAmount = amountsB[amountsB.length - 1];
                
                // Subtract flashloan fee (0.25%)
                uint256 flashloanFee = (amount * 25) / 10000;
                
                if (finalAmount > amount + flashloanFee) {
                    return finalAmount - amount - flashloanFee;
                }
            } catch {
                return 0;
            }
        } catch {
            return 0;
        }
        
        return 0;
    }

    /**
     * @dev Check if arbitrage is profitable
     */
    function isArbitrageProfitable(
        uint256 amount,
        string memory dexA,
        string memory dexB,
        address[] memory path
    ) external view returns (bool) {
        uint256 profit = this.calculateArbitrageProfit(amount, dexA, dexB, path);
        return profit >= minProfitThreshold;
    }

    // Admin functions
    function updateDEXConfig(
        string calldata dexName,
        address router,
        bool isActive,
        uint256 fee
    ) external onlyOwner {
        dexConfigs[dexName] = DEXConfig(router, isActive, fee);
    }

    function updateMinProfitThreshold(uint256 _threshold) external onlyOwner {
        minProfitThreshold = _threshold;
    }

    function setAuthorizedCaller(address caller, bool authorized) external onlyOwner {
        authorizedCallers[caller] = authorized;
    }

    function emergencyWithdraw(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).transfer(owner(), balance);
        }
    }

    receive() external payable {}
}
