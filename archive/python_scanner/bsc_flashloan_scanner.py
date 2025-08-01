"""
BSC Native Flashloan Arbitrage using PancakeSwap Flashswaps
No external flashloan provider needed - uses DEX native flashloans
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import json
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bsc_flashloan.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FlashloanOpportunity:
    """BSC flashloan arbitrage opportunity"""
    token_a: str
    token_b: str
    token_a_symbol: str
    token_b_symbol: str
    amount_in: int
    pair_address: str  # PancakeSwap pair for flashloan
    dex_buy: str
    dex_sell: str
    price_buy: float
    price_sell: float
    profit_percentage: float
    estimated_gas: int

class BSCFlashloanArbitrage:
    """BSC Native Flashloan Arbitrage using PancakeSwap"""
    
    def __init__(self):
        logger.info("Starting BSC Native Flashloan Arbitrage")
        
        # Web3 setup
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        
        # BSC native tokens with high liquidity pairs
        self.tokens = {
            'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
            'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
            'USDT': '0x55d398326f99059fF775485246999027B3197955',
            'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
            'ETH': '0x2170Ed0826c71020356F2c44b6feab4E2eBAEf50',
            'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
            'CAKE': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
            'UNI': '0xBf5140A22578168FD562DCcF235E5D43A02ce9B1',
            'LINK': '0xF8A0BF9cF54Bb92F17374d9e9A321E6a111a51bD',
            'DOT': '0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402'
        }
        
        # DEX Routers for arbitrage
        self.dex_routers = {
            'PancakeSwap': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
            'Biswap': '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
            'ApeSwap': '0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7'
        }
        
        # PancakeSwap Factory for pair addresses
        self.pancake_factory = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
        
        # Configuration
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.01'))  # 1%
        self.max_profit_threshold = 0.05  # 5%
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'opportunities_found': 0,
            'flashloans_executed': 0,
            'successful_arbitrages': 0,
            'total_profit': 0.0
        }
        
        logger.info("BSC Flashloan Arbitrage initialized")
        logger.info(f"Min profit threshold: {self.min_profit_threshold:.1%}")
        logger.info(f"Account: {self.account.address if self.account else 'Simulation mode'}")
        
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection to BSC"""
        rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to BSC at {rpc_url}")
            
        latest_block = w3.eth.block_number
        logger.info(f"Connected to BSC: Block {latest_block}")
        return w3
        
    def _setup_account(self) -> Optional[object]:
        """Setup account for transactions"""
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            logger.warning("No private key - running in simulation mode")
            return None
            
        try:
            account = self.w3.eth.account.from_key(private_key)
            balance = self.w3.eth.get_balance(account.address)
            balance_bnb = self.w3.from_wei(balance, 'ether')
            logger.info(f"Account loaded: {account.address}")
            logger.info(f"Balance: {balance_bnb:.4f} BNB")
            return account
        except Exception as e:
            logger.error(f"Error loading account: {e}")
            return None
            
    def get_pair_address(self, token_a: str, token_b: str) -> Optional[str]:
        """Get PancakeSwap pair address for two tokens"""
        try:
            # PancakeSwap Factory ABI (getPair function)
            factory_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "tokenA", "type": "address"},
                        {"internalType": "address", "name": "tokenB", "type": "address"}
                    ],
                    "name": "getPair",
                    "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            factory_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.pancake_factory),
                abi=factory_abi
            )
            
            pair_address = factory_contract.functions.getPair(
                Web3.to_checksum_address(token_a),
                Web3.to_checksum_address(token_b)
            ).call()
            
            # Check if pair exists (non-zero address)
            if pair_address != '0x0000000000000000000000000000000000000000':
                return pair_address
            else:
                return None
                
        except Exception as e:
            logger.debug(f"Error getting pair address: {e}")
            return None
            
    def get_pair_reserves(self, pair_address: str) -> Optional[Tuple[int, int]]:
        """Get reserves from a PancakeSwap pair"""
        try:
            # Pair ABI (getReserves function)
            pair_abi = [
                {
                    "inputs": [],
                    "name": "getReserves",
                    "outputs": [
                        {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                        {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                        {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            pair_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=pair_abi
            )
            
            reserves = pair_contract.functions.getReserves().call()
            return (reserves[0], reserves[1])  # (reserve0, reserve1)
            
        except Exception as e:
            logger.debug(f"Error getting pair reserves: {e}")
            return None
            
    def calculate_flashloan_amount(self, reserve0: int, reserve1: int, profit_target: float = 0.02) -> int:
        """Calculate optimal flashloan amount based on reserves and profit target"""
        # Use a conservative percentage of the smaller reserve
        max_amount = min(reserve0, reserve1) * 0.1  # 10% of smaller reserve
        
        # Start with a reasonable amount (equivalent to ~$1000)
        if 'BUSD' in self.tokens.values() or 'USDT' in self.tokens.values():
            base_amount = int(1000 * 1e18)  # $1000 worth
        else:
            base_amount = int(max_amount * 0.1)  # 1% of smaller reserve
            
        return min(int(base_amount), int(max_amount))
        
    def get_dex_price(self, router_address: str, amount_in: int, token_in: str, token_out: str) -> Optional[float]:
        """Get price from a DEX router"""
        try:
            router_abi = [
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "address[]", "name": "path", "type": "address[]"}
                    ],
                    "name": "getAmountsOut",
                    "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            router_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(router_address),
                abi=router_abi
            )
            
            path = [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)]
            amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
            
            if len(amounts) >= 2:
                amount_out = amounts[-1]
                price = float(amount_out) / float(amount_in)
                return price
            else:
                return None
                
        except Exception as e:
            logger.debug(f"Error getting DEX price: {e}")
            return None
            
    def create_flashloan_contract(self) -> str:
        """Create and deploy a simple flashloan contract"""
        
        # Simple flashloan contract source code
        contract_source = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

interface IPancakePair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function token0() external view returns (address);
    function token1() external view returns (address);
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}

interface IPancakeRouter {
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

contract SimpleFlashloanArbitrage {
    address private owner;
    
    modifier onlyOwner {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    function executeFlashloanArbitrage(
        address pairAddress,
        uint256 amount0Out,
        uint256 amount1Out,
        address tokenIn,
        address tokenOut,
        address buyRouter,
        address sellRouter
    ) external onlyOwner {
        // Initiate flashloan via PancakeSwap pair
        bytes memory data = abi.encode(tokenIn, tokenOut, buyRouter, sellRouter, msg.sender);
        IPancakePair(pairAddress).swap(amount0Out, amount1Out, address(this), data);
    }
    
    function pancakeCall(address sender, uint amount0, uint amount1, bytes calldata data) external {
        // Decode parameters
        (address tokenIn, address tokenOut, address buyRouter, address sellRouter, address recipient) = 
            abi.decode(data, (address, address, address, address, address));
        
        uint256 amountIn = amount0 > 0 ? amount0 : amount1;
        
        // Execute arbitrage
        address[] memory buyPath = new address[](2);
        buyPath[0] = tokenIn;
        buyPath[1] = tokenOut;
        
        address[] memory sellPath = new address[](2);
        sellPath[0] = tokenOut;
        sellPath[1] = tokenIn;
        
        // Approve tokens
        IERC20(tokenIn).transfer(buyRouter, amountIn);
        
        // Buy on first DEX
        uint[] memory buyAmounts = IPancakeRouter(buyRouter).swapExactTokensForTokens(
            amountIn,
            0,
            buyPath,
            address(this),
            block.timestamp + 300
        );
        
        uint256 amountOut = buyAmounts[buyAmounts.length - 1];
        
        // Approve for sell
        IERC20(tokenOut).transfer(sellRouter, amountOut);
        
        // Sell on second DEX
        uint[] memory sellAmounts = IPancakeRouter(sellRouter).swapExactTokensForTokens(
            amountOut,
            0,
            sellPath,
            address(this),
            block.timestamp + 300
        );
        
        uint256 finalAmount = sellAmounts[sellAmounts.length - 1];
        
        // Calculate fee (0.3% + small buffer)
        uint256 fee = (amountIn * 3) / 1000 + 1;
        uint256 amountToRepay = amountIn + fee;
        
        require(finalAmount > amountToRepay, "Not profitable");
        
        // Repay flashloan
        IERC20(tokenIn).transfer(msg.sender, amountToRepay);
        
        // Send profit to recipient
        uint256 profit = finalAmount - amountToRepay;
        IERC20(tokenIn).transfer(recipient, profit);
    }
    
    function withdraw(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).transfer(owner, balance);
        }
    }
    
    function withdrawBNB() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
}
'''
        
        logger.info("Simple flashloan contract created")
        return contract_source
        
    def find_flashloan_opportunities(self) -> List[FlashloanOpportunity]:
        """Find flashloan arbitrage opportunities"""
        opportunities = []
        
        # High liquidity pairs for flashloans
        priority_pairs = [
            ('WBNB', 'BUSD'),
            ('WBNB', 'USDT'), 
            ('BUSD', 'USDT'),
            ('WBNB', 'ETH'),
            ('WBNB', 'BTCB')
        ]
        
        for token_a_symbol, token_b_symbol in priority_pairs:
            if token_a_symbol not in self.tokens or token_b_symbol not in self.tokens:
                continue
                
            token_a = self.tokens[token_a_symbol]
            token_b = self.tokens[token_b_symbol]
            
            # Get PancakeSwap pair for flashloan
            pair_address = self.get_pair_address(token_a, token_b)
            if not pair_address:
                logger.debug(f"No pair found for {token_a_symbol}/{token_b_symbol}")
                continue
                
            # Get pair reserves
            reserves = self.get_pair_reserves(pair_address)
            if not reserves:
                logger.debug(f"No reserves found for pair {pair_address}")
                continue
                
            reserve0, reserve1 = reserves
            
            # Calculate flashloan amount
            flashloan_amount = self.calculate_flashloan_amount(reserve0, reserve1)
            
            logger.info(f"Checking {token_a_symbol}/{token_b_symbol} - Pair: {pair_address}")
            logger.info(f"  Reserves: {reserve0:,} / {reserve1:,}")
            logger.info(f"  Flashloan amount: {flashloan_amount:,}")
            
            # Check prices on different DEXes
            dex_prices = {}
            
            for dex_name, router_address in self.dex_routers.items():
                # Price for token_a -> token_b
                price_a_to_b = self.get_dex_price(router_address, flashloan_amount, token_a, token_b)
                if price_a_to_b:
                    dex_prices[f"{dex_name}_a_to_b"] = {
                        'dex': dex_name,
                        'router': router_address,
                        'price': price_a_to_b,
                        'direction': 'a_to_b'
                    }
                    
                # Price for token_b -> token_a  
                price_b_to_a = self.get_dex_price(router_address, flashloan_amount, token_b, token_a)
                if price_b_to_a:
                    dex_prices[f"{dex_name}_b_to_a"] = {
                        'dex': dex_name,
                        'router': router_address,
                        'price': price_b_to_a,
                        'direction': 'b_to_a'
                    }
            
            # Find arbitrage opportunities
            price_keys = list(dex_prices.keys())
            for i in range(len(price_keys)):
                for j in range(i + 1, len(price_keys)):
                    key1, key2 = price_keys[i], price_keys[j]
                    data1, data2 = dex_prices[key1], dex_prices[key2]
                    
                    # Only compare same direction trades
                    if data1['direction'] != data2['direction']:
                        continue
                        
                    price1, price2 = data1['price'], data2['price']
                    
                    # Calculate profit percentage
                    if price1 > price2:
                        profit_pct = (price1 - price2) / price2
                        buy_dex, sell_dex = data2['dex'], data1['dex']
                        buy_price, sell_price = price2, price1
                    else:
                        profit_pct = (price2 - price1) / price1  
                        buy_dex, sell_dex = data1['dex'], data2['dex']
                        buy_price, sell_price = price1, price2
                    
                    # Check if profitable after fees (flashloan fee ~0.3% + gas)
                    min_profit_after_fees = 0.005  # 0.5%
                    
                    if profit_pct > min_profit_after_fees and profit_pct <= self.max_profit_threshold:
                        opportunity = FlashloanOpportunity(
                            token_a=token_a,
                            token_b=token_b,
                            token_a_symbol=token_a_symbol,
                            token_b_symbol=token_b_symbol,
                            amount_in=flashloan_amount,
                            pair_address=pair_address,
                            dex_buy=buy_dex,
                            dex_sell=sell_dex,
                            price_buy=buy_price,
                            price_sell=sell_price,
                            profit_percentage=profit_pct,
                            estimated_gas=300000
                        )
                        
                        opportunities.append(opportunity)
                        
                        logger.info(f"[FLASHLOAN OPPORTUNITY] {token_a_symbol}/{token_b_symbol}")
                        logger.info(f"  Profit: {profit_pct:.2%}")
                        logger.info(f"  Buy on {buy_dex} ({buy_price:.6f})")
                        logger.info(f"  Sell on {sell_dex} ({sell_price:.6f})")
                        logger.info(f"  Flashloan from pair: {pair_address}")
                        
        return opportunities
        
    def run_flashloan_scanner(self):
        """Run continuous flashloan arbitrage scanning"""
        scan_interval = 30  # 30 seconds
        
        logger.info("Starting BSC Flashloan Arbitrage Scanner")
        logger.info(f"Scan interval: {scan_interval}s")
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                logger.info("=" * 80)
                logger.info(f"BSC Flashloan Scan #{scan_count}")
                
                opportunities = self.find_flashloan_opportunities()
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} flashloan opportunities!")
                    
                    for opp in opportunities:
                        logger.info(f"OPPORTUNITY: {opp.token_a_symbol}/{opp.token_b_symbol}")
                        logger.info(f"  Profit: {opp.profit_percentage:.2%}")
                        logger.info(f"  Amount: {opp.amount_in:,}")
                        logger.info(f"  Buy: {opp.dex_buy} | Sell: {opp.dex_sell}")
                        
                        if self.account:
                            logger.info(f"  [SIMULATION] Would execute flashloan arbitrage")
                            self.stats['flashloans_executed'] += 1
                        else:
                            logger.info(f"  [SIMULATION] No account configured")
                            
                    self.stats['opportunities_found'] += len(opportunities)
                else:
                    logger.info("No profitable flashloan opportunities found")
                    
                self.stats['scans_completed'] += 1
                
                # Print statistics
                logger.info(f"Session Stats:")
                logger.info(f"  Scans: {self.stats['scans_completed']}")
                logger.info(f"  Opportunities: {self.stats['opportunities_found']}")
                logger.info(f"  Flashloans executed: {self.stats['flashloans_executed']}")
                
                logger.info(f"Waiting {scan_interval}s for next scan...")
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            logger.info("Flashloan scanner stopped by user")
        except Exception as e:
            logger.error(f"Scanner error: {e}")

def main():
    """Main entry point"""
    logger.info("Starting BSC Native Flashloan Arbitrage")
    logger.info("=" * 60)
    
    scanner = BSCFlashloanArbitrage()
    scanner.run_flashloan_scanner()

if __name__ == "__main__":
    main()
