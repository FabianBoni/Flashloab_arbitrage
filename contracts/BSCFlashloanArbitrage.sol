// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// Simplified router interface for BSC DEXes
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
 * @title BSCFlashloanArbitrage
 * @dev Ultra-simple arbitrage contract for BSC without flashloans (for testing)
 */
contract BSCFlashloanArbitrage is ReentrancyGuard, Ownable {
    
    // Events
    event ArbitrageExecuted(
        address indexed tokenA,
        address indexed tokenB,
        uint256 amountIn,
        uint256 profit,
        address buyRouter,
        address sellRouter
    );
    
    // Router addresses - BSC
    address public constant PANCAKESWAP_ROUTER = 0x10ED43C718714eb63d5aA57B78B54704E256024E;
    address public constant BISWAP_ROUTER = 0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8;
    address public constant APESWAP_ROUTER = 0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7;
    
    // Common BSC tokens
    address public constant WBNB = 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c;
    address public constant BUSD = 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56;
    address public constant USDT = 0x55d398326f99059fF775485246999027B3197955;
    address public constant USDC = 0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d;
    
    constructor() Ownable(msg.sender) {
        // Contract is ready to use
    }
    
    /**
     * @dev Simple arbitrage without flashloan (for testing)
     * Owner must have tokens in the contract first
     */
    function executeSimpleArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        address buyRouter,
        address sellRouter
    ) external onlyOwner nonReentrant {
        require(tokenA != address(0) && tokenB != address(0), "Invalid tokens");
        require(amountIn > 0, "Invalid amount");
        require(buyRouter != sellRouter, "Same router");
        
        uint256 initialBalance = IERC20(tokenA).balanceOf(address(this));
        require(initialBalance >= amountIn, "Insufficient balance");
        
        // Step 1: Swap tokenA for tokenB on buyRouter
        address[] memory path1 = new address[](2);
        path1[0] = tokenA;
        path1[1] = tokenB;
        
        IERC20(tokenA).approve(buyRouter, amountIn);
        
        uint256[] memory amounts1 = IDEXRouter(buyRouter).swapExactTokensForTokens(
            amountIn,
            0,
            path1,
            address(this),
            block.timestamp + 300
        );
        
        uint256 tokenBAmount = amounts1[1];
        
        // Step 2: Swap tokenB back to tokenA on sellRouter
        address[] memory path2 = new address[](2);
        path2[0] = tokenB;
        path2[1] = tokenA;
        
        IERC20(tokenB).approve(sellRouter, tokenBAmount);
        
        IDEXRouter(sellRouter).swapExactTokensForTokens(
            tokenBAmount,
            0,
            path2,
            address(this),
            block.timestamp + 300
        );
        
        uint256 finalBalance = IERC20(tokenA).balanceOf(address(this));
        uint256 profit = finalBalance > initialBalance ? finalBalance - initialBalance : 0;
        
        emit ArbitrageExecuted(tokenA, tokenB, amountIn, profit, buyRouter, sellRouter);
    }
    
    /**
     * @dev Check arbitrage profitability
     */
    function checkArbitrageProfit(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        address buyRouter,
        address sellRouter
    ) external view returns (uint256 estimatedProfit, bool isProfitable) {
        try this._simulateArbitrage(tokenA, tokenB, amountIn, buyRouter, sellRouter)
        returns (uint256 profit) {
            return (profit, profit > 0);
        } catch {
            return (0, false);
        }
    }
    
    /**
     * @dev Simulate arbitrage trade
     */
    function _simulateArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        address buyRouter,
        address sellRouter
    ) external view returns (uint256 profit) {
        // Simulate tokenA -> tokenB on buyRouter
        address[] memory path1 = new address[](2);
        path1[0] = tokenA;
        path1[1] = tokenB;
        
        uint256[] memory amounts1 = IDEXRouter(buyRouter).getAmountsOut(amountIn, path1);
        uint256 tokenBAmount = amounts1[1];
        
        // Simulate tokenB -> tokenA on sellRouter
        address[] memory path2 = new address[](2);
        path2[0] = tokenB;
        path2[1] = tokenA;
        
        uint256[] memory amounts2 = IDEXRouter(sellRouter).getAmountsOut(tokenBAmount, path2);
        uint256 finalAmount = amounts2[1];
        
        profit = finalAmount > amountIn ? finalAmount - amountIn : 0;
        return profit;
    }
    
    /**
     * @dev Deposit tokens to contract
     */
    function depositToken(address token, uint256 amount) external onlyOwner {
        IERC20(token).transferFrom(msg.sender, address(this), amount);
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
    
    /**
     * @dev Get token balance
     */
    function getTokenBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }
    
    /**
     * @dev Receive BNB
     */
    receive() external payable {}
}
