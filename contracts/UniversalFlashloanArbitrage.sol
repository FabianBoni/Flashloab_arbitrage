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

// PancakeSwap flashloan interface (BSC)
interface IPancakeCallee {
    function pancakeCall(address sender, uint amount0, uint amount1, bytes calldata data) external;
}

interface IPancakePair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function token0() external view returns (address);
    function token1() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
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

// Flashloan receiver interface for Aave
interface IFlashLoanReceiver {
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

/**
 * @title UniversalFlashloanArbitrage
 * @dev Universal smart contract for executing flashloan arbitrage trades across multiple chains
 */
contract UniversalFlashloanArbitrage is ReentrancyGuard, Ownable, IFlashLoanReceiver, IPancakeCallee {
    using SafeERC20 for IERC20;

    // Flashloan provider types
    enum FlashloanProvider { AAVE, PANCAKESWAP, DIRECT }

    // DEX configuration
    struct DEXConfig {
        address router;
        bool isActive;
        uint256 fee; // Fee in basis points (e.g., 25 = 0.25%)
    }

    // Arbitrage parameters
    struct ArbitrageParams {
        address asset;
        uint256 amount;
        string dexA;
        string dexB;
        address[] path;
        uint256 minProfit;
        FlashloanProvider provider;
        address flashloanSource; // Pool address for Aave, Pair address for PancakeSwap
    }

    // State variables
    mapping(string => DEXConfig) public dexConfigs;
    mapping(address => bool) public authorizedCallers;
    
    address public aavePool;
    address public weth;
    uint256 public minProfitThreshold = 1e15; // 0.001 ETH minimum profit
    uint256 public maxGasPrice = 50 gwei;
    
    // Events
    event ArbitrageExecuted(
        address indexed asset,
        uint256 amount,
        uint256 profit,
        string dexA,
        string dexB,
        FlashloanProvider provider
    );
    
    event DEXConfigUpdated(string indexed dexName, address router, bool isActive, uint256 fee);
    event FlashloanProviderUpdated(FlashloanProvider provider, address source);

    constructor(address _aavePool, address _weth) Ownable(msg.sender) {
        aavePool = _aavePool;
        weth = _weth;
        authorizedCallers[msg.sender] = true;
    }

    modifier onlyAuthorized() {
        require(authorizedCallers[msg.sender], "Not authorized");
        _;
    }

    /**
     * @dev Execute arbitrage with automatic flashloan provider selection
     */
    function executeArbitrage(
        address asset,
        uint256 amount,
        string calldata dexA,
        string calldata dexB,
        address[] calldata path,
        uint256 minProfit
    ) external onlyAuthorized nonReentrant {
        require(tx.gasprice <= maxGasPrice, "Gas price too high");
        require(dexConfigs[dexA].isActive && dexConfigs[dexB].isActive, "DEX not active");
        
        // Determine best flashloan provider
        FlashloanProvider provider = _getBestFlashloanProvider(asset, amount);
        address flashloanSource = _getFlashloanSource(provider, asset);
        
        ArbitrageParams memory params = ArbitrageParams({
            asset: asset,
            amount: amount,
            dexA: dexA,
            dexB: dexB,
            path: path,
            minProfit: minProfit,
            provider: provider,
            flashloanSource: flashloanSource
        });
        
        _executeFlashloan(params);
    }

    /**
     * @dev Execute flashloan based on provider
     */
    function _executeFlashloan(ArbitrageParams memory params) internal {
        if (params.provider == FlashloanProvider.AAVE) {
            _executeAaveFlashloan(params);
        } else if (params.provider == FlashloanProvider.PANCAKESWAP) {
            _executePancakeFlashloan(params);
        } else {
            _executeDirectTrade(params);
        }
    }

    /**
     * @dev Execute Aave flashloan
     */
    function _executeAaveFlashloan(ArbitrageParams memory params) internal {
        address[] memory assets = new address[](1);
        assets[0] = params.asset;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = params.amount;
        
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0; // No debt
        
        bytes memory paramData = abi.encode(params);
        
        IPool(aavePool).flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            paramData,
            0
        );
    }

    /**
     * @dev Execute PancakeSwap flashloan (BSC)
     */
    function _executePancakeFlashloan(ArbitrageParams memory params) internal {
        IPancakePair pair = IPancakePair(params.flashloanSource);
        
        address token0 = pair.token0();
        address token1 = pair.token1();
        
        uint256 amount0Out = params.asset == token0 ? params.amount : 0;
        uint256 amount1Out = params.asset == token1 ? params.amount : 0;
        
        bytes memory data = abi.encode(params);
        
        pair.swap(amount0Out, amount1Out, address(this), data);
    }

    /**
     * @dev Execute direct trade (no flashloan)
     */
    function _executeDirectTrade(ArbitrageParams memory params) internal {
        require(IERC20(params.asset).balanceOf(address(this)) >= params.amount, "Insufficient balance");
        _performArbitrage(params, 0);
    }

    /**
     * @dev Aave flashloan callback
     */
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address /* initiator */,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == aavePool, "Invalid caller");
        
        ArbitrageParams memory arbParams = abi.decode(params, (ArbitrageParams));
        uint256 premium = premiums[0];
        
        _performArbitrage(arbParams, premium);
        
        // Repay flashloan
        uint256 repayAmount = amounts[0] + premium;
        IERC20(assets[0]).safeTransfer(aavePool, repayAmount);
        
        return true;
    }

    /**
     * @dev PancakeSwap flashloan callback
     */
    function pancakeCall(
        address /* sender */,
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external override {
        ArbitrageParams memory params = abi.decode(data, (ArbitrageParams));
        
        // Verify caller is the pair contract
        require(msg.sender == params.flashloanSource, "Invalid caller");
        
        uint256 amount = amount0 > 0 ? amount0 : amount1;
        
        // Calculate fee (0.25% for PancakeSwap)
        uint256 fee = (amount * 25) / 10000;
        
        _performArbitrage(params, fee);
        
        // Repay flashloan
        uint256 repayAmount = amount + fee;
        IERC20(params.asset).safeTransfer(msg.sender, repayAmount);
    }

    /**
     * @dev Perform the actual arbitrage trade
     */
    function _performArbitrage(ArbitrageParams memory params, uint256 flashloanFee) internal {
        uint256 initialBalance = IERC20(params.asset).balanceOf(address(this));
        
        // Step 1: Buy on DEX A
        uint256[] memory amountsA = _swapOnDEX(
            params.dexA,
            params.amount,
            params.path,
            0 // No minimum for first swap
        );
        
        // Step 2: Sell on DEX B (reverse path)
        address[] memory reversePath = new address[](params.path.length);
        for (uint i = 0; i < params.path.length; i++) {
            reversePath[i] = params.path[params.path.length - 1 - i];
        }
        
        uint256[] memory amountsB = _swapOnDEX(
            params.dexB,
            amountsA[amountsA.length - 1],
            reversePath,
            params.amount + flashloanFee + params.minProfit
        );
        
        uint256 finalBalance = IERC20(params.asset).balanceOf(address(this));
        uint256 profit = finalBalance - initialBalance - flashloanFee;
        
        require(profit >= params.minProfit, "Insufficient profit");
        
        emit ArbitrageExecuted(
            params.asset,
            params.amount,
            profit,
            params.dexA,
            params.dexB,
            params.provider
        );
    }

    /**
     * @dev Swap tokens on specified DEX
     */
    function _swapOnDEX(
        string memory dexName,
        uint256 amountIn,
        address[] memory path,
        uint256 amountOutMin
    ) internal returns (uint256[] memory) {
        DEXConfig memory config = dexConfigs[dexName];
        require(config.isActive, "DEX not active");
        
        IERC20(path[0]).approve(config.router, amountIn);
        
        return IDEX(config.router).swapExactTokensForTokens(
            amountIn,
            amountOutMin,
            path,
            address(this),
            block.timestamp + 300
        );
    }

    /**
     * @dev Get best flashloan provider for given asset and amount
     */
    function _getBestFlashloanProvider(address asset, uint256 amount) internal view returns (FlashloanProvider) {
        // For BSC, prefer PancakeSwap
        if (block.chainid == 56) {
            return FlashloanProvider.PANCAKESWAP;
        }
        
        // For other chains with Aave, use Aave
        if (aavePool != address(0)) {
            return FlashloanProvider.AAVE;
        }
        
        // Fallback to direct trade
        return FlashloanProvider.DIRECT;
    }

    /**
     * @dev Get flashloan source address
     */
    function _getFlashloanSource(FlashloanProvider provider, address asset) internal view returns (address) {
        if (provider == FlashloanProvider.AAVE) {
            return aavePool;
        } else if (provider == FlashloanProvider.PANCAKESWAP) {
            // Return a major pair address (would need to be configured per deployment)
            return address(0); // This should be set during deployment
        }
        return address(0);
    }

    // Admin functions
    function updateDEXConfig(
        string calldata dexName,
        address router,
        bool isActive,
        uint256 fee
    ) external onlyOwner {
        dexConfigs[dexName] = DEXConfig(router, isActive, fee);
        emit DEXConfigUpdated(dexName, router, isActive, fee);
    }

    function updateAavePool(address _aavePool) external onlyOwner {
        aavePool = _aavePool;
        emit FlashloanProviderUpdated(FlashloanProvider.AAVE, _aavePool);
    }

    function updateMinProfitThreshold(uint256 _threshold) external onlyOwner {
        minProfitThreshold = _threshold;
    }

    function updateMaxGasPrice(uint256 _maxGasPrice) external onlyOwner {
        maxGasPrice = _maxGasPrice;
    }

    function setAuthorizedCaller(address caller, bool authorized) external onlyOwner {
        authorizedCallers[caller] = authorized;
    }

    function emergencyWithdraw(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).safeTransfer(owner(), balance);
        }
    }

    // View functions
    function isArbitrageProfitable(
        uint256 amount,
        string memory dexA,
        string memory dexB,
        address[] memory path
    ) external view returns (bool) {
        try this.calculateArbitrageProfit(amount, dexA, dexB, path) returns (uint256 profit) {
            return profit >= minProfitThreshold;
        } catch {
            return false;
        }
    }

    function calculateArbitrageProfit(
        uint256 amount,
        string memory dexA,
        string memory dexB,
        address[] memory path
    ) external view returns (uint256) {
        // Get amounts from DEX A
        uint256[] memory amountsA = IDEX(dexConfigs[dexA].router).getAmountsOut(amount, path);
        
        // Create reverse path for DEX B
        address[] memory reversePath = new address[](path.length);
        for (uint i = 0; i < path.length; i++) {
            reversePath[i] = path[path.length - 1 - i];
        }
        
        // Get amounts from DEX B
        uint256[] memory amountsB = IDEX(dexConfigs[dexB].router).getAmountsOut(
            amountsA[amountsA.length - 1],
            reversePath
        );
        
        uint256 finalAmount = amountsB[amountsB.length - 1];
        
        if (finalAmount > amount) {
            return finalAmount - amount;
        }
        
        return 0;
    }

    receive() external payable {}
}
