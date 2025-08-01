// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// PancakeSwap Pair interface for flashloans
interface IPancakePair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function token0() external view returns (address);
    function token1() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
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
 * @title BSCFlashloanArbitrageV2
 * @dev Real flashloan arbitrage contract for BSC using PancakeSwap flashswaps
 */
contract BSCFlashloanArbitrageV2 is ReentrancyGuard, Ownable {
    
    // Events
    event FlashloanArbitrage(
        address indexed tokenBorrow,
        address indexed tokenTarget,
        uint256 amountBorrowed,
        uint256 profit,
        address buyRouter,
        address sellRouter
    );
    
    // Common BSC tokens
    address public constant WBNB = 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c;
    address public constant BUSD = 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56;
    address public constant USDT = 0x55d398326f99059fF775485246999027B3197955;
    address public constant USDC = 0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d;
    
    // Router addresses
    address public constant PANCAKESWAP_ROUTER = 0x10ED43C718714eb63d5aA57B78B54704E256024E;
    address public constant BISWAP_ROUTER = 0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8;
    address public constant APESWAP_ROUTER = 0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7;
    
    constructor() Ownable(msg.sender) {}
    
    /**
     * @dev Execute flashloan arbitrage
     * @param pairAddress Pair to borrow from
     * @param amount0Out Amount of token0 to borrow (0 if borrowing token1)
     * @param amount1Out Amount of token1 to borrow (0 if borrowing token0)
     * @param tokenBorrow Token to borrow
     * @param tokenTarget Token to trade for
     * @param buyRouter Router to buy on
     * @param sellRouter Router to sell on
     */
    function executeFlashloan(
        address pairAddress,
        uint256 amount0Out,
        uint256 amount1Out,
        address tokenBorrow,
        address tokenTarget,
        address buyRouter,
        address sellRouter
    ) external onlyOwner nonReentrant {
        require(pairAddress != address(0), "Invalid pair");
        require(tokenBorrow != address(0) && tokenTarget != address(0), "Invalid tokens");
        require(amount0Out > 0 || amount1Out > 0, "Invalid amounts");
        require(amount0Out == 0 || amount1Out == 0, "Can only borrow one token");
        
        // Encode callback data
        bytes memory data = abi.encode(tokenBorrow, tokenTarget, buyRouter, sellRouter);
        
        // Execute flashloan
        IPancakePair(pairAddress).swap(amount0Out, amount1Out, address(this), data);
    }
    
    /**
     * @dev PancakeSwap flashloan callback
     */
    function pancakeCall(address sender, uint amount0, uint amount1, bytes calldata data) external {
        require(sender == address(this), "Invalid sender");
        
        // Decode callback data
        (address tokenBorrow, address tokenTarget, address buyRouter, address sellRouter) = 
            abi.decode(data, (address, address, address, address));
        
        uint256 amountBorrowed = amount0 > 0 ? amount0 : amount1;
        
        // Execute arbitrage
        uint256 profit = _executeArbitrage(tokenBorrow, tokenTarget, amountBorrowed, buyRouter, sellRouter);
        
        // Calculate repayment (0.3% fee)
        uint256 amountToRepay = amountBorrowed + ((amountBorrowed * 3) / 1000);
        
        // Ensure we can repay
        require(IERC20(tokenBorrow).balanceOf(address(this)) >= amountToRepay, "Insufficient balance to repay");
        
        // Repay flashloan
        IERC20(tokenBorrow).transfer(msg.sender, amountToRepay);
        
        emit FlashloanArbitrage(tokenBorrow, tokenTarget, amountBorrowed, profit, buyRouter, sellRouter);
    }
    
    /**
     * @dev Execute arbitrage trade
     */
    function _executeArbitrage(
        address tokenBorrow,
        address tokenTarget,
        uint256 amountBorrowed,
        address buyRouter,
        address sellRouter
    ) internal returns (uint256 profit) {
        uint256 initialBalance = IERC20(tokenBorrow).balanceOf(address(this));
        
        // Step 1: Buy tokenTarget with tokenBorrow
        address[] memory buyPath = new address[](2);
        buyPath[0] = tokenBorrow;
        buyPath[1] = tokenTarget;
        
        IERC20(tokenBorrow).approve(buyRouter, amountBorrowed);
        
        uint256[] memory buyAmounts = IDEXRouter(buyRouter).swapExactTokensForTokens(
            amountBorrowed,
            0,
            buyPath,
            address(this),
            block.timestamp + 300
        );
        
        uint256 targetAmount = buyAmounts[1];
        
        // Step 2: Sell tokenTarget back to tokenBorrow
        address[] memory sellPath = new address[](2);
        sellPath[0] = tokenTarget;
        sellPath[1] = tokenBorrow;
        
        IERC20(tokenTarget).approve(sellRouter, targetAmount);
        
        IDEXRouter(sellRouter).swapExactTokensForTokens(
            targetAmount,
            0,
            sellPath,
            address(this),
            block.timestamp + 300
        );
        
        uint256 finalBalance = IERC20(tokenBorrow).balanceOf(address(this));
        profit = finalBalance > initialBalance ? finalBalance - initialBalance : 0;
        
        return profit;
    }
    
    /**
     * @dev Calculate pair address for tokens on PancakeSwap
     */
    function getPairAddress(address tokenA, address tokenB) external pure returns (address pair) {
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        pair = address(uint160(uint256(keccak256(abi.encodePacked(
            hex'ff',
            0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73, // PancakeSwap factory
            keccak256(abi.encodePacked(token0, token1)),
            hex'00fb7f630766e6a796048ea87d01acd3068e8ff67d078148a3fa3f4a84f69bd5' // init code hash
        )))));
    }
    
    /**
     * @dev Check if arbitrage is profitable
     */
    function checkProfitability(
        address tokenBorrow,
        address tokenTarget,
        uint256 amount,
        address buyRouter,
        address sellRouter
    ) external view returns (uint256 profit, bool profitable) {
        try this._simulateArbitrage(tokenBorrow, tokenTarget, amount, buyRouter, sellRouter)
        returns (uint256 simProfit) {
            uint256 fee = (amount * 3) / 1000; // 0.3% flashloan fee
            profit = simProfit > fee ? simProfit - fee : 0;
            profitable = profit > 0;
        } catch {
            profit = 0;
            profitable = false;
        }
    }
    
    /**
     * @dev Simulate arbitrage (external for try/catch)
     */
    function _simulateArbitrage(
        address tokenBorrow,
        address tokenTarget,
        uint256 amount,
        address buyRouter,
        address sellRouter
    ) external view returns (uint256 profit) {
        // Simulate buy
        address[] memory buyPath = new address[](2);
        buyPath[0] = tokenBorrow;
        buyPath[1] = tokenTarget;
        
        uint256[] memory buyAmounts = IDEXRouter(buyRouter).getAmountsOut(amount, buyPath);
        uint256 targetAmount = buyAmounts[1];
        
        // Simulate sell
        address[] memory sellPath = new address[](2);
        sellPath[0] = tokenTarget;
        sellPath[1] = tokenBorrow;
        
        uint256[] memory sellAmounts = IDEXRouter(sellRouter).getAmountsOut(targetAmount, sellPath);
        uint256 finalAmount = sellAmounts[1];
        
        profit = finalAmount > amount ? finalAmount - amount : 0;
        return profit;
    }
    
    /**
     * @dev Emergency withdrawal
     */
    function emergencyWithdraw(address token) external onlyOwner {
        if (token == address(0)) {
            payable(owner()).transfer(address(this).balance);
        } else {
            uint256 balance = IERC20(token).balanceOf(address(this));
            IERC20(token).transfer(owner(), balance);
        }
    }
    
    receive() external payable {}
}
