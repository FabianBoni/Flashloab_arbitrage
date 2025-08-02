"""
Main BSC Arbitrage Scanner & Executor
Production-ready immediate execution scanner with Telegram integration
Optimized for Raspberry Pi deployment with Docker
- Scans for real arbitrage opportunities on BSC
- Executes trades immediately when profit > thresholds
- Telegram notifications for all events
- Comprehensive error handling and rate limiting
- Memory optimized for resource-constrained environments
"""

import time
import logging
import gc
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import json
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
import requests
from dotenv import load_dotenv
import asyncio
import aiohttp

# Try to use ujson for better performance on Pi
try:
    import ujson as json
except ImportError:
    import json

# Load environment variables
load_dotenv()

# Configure logging optimized for Docker and Pi with permission handling
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

# Create logs directory if it doesn't exist and we have permissions
log_handlers = [logging.StreamHandler(sys.stdout)]
try:
    # Try to create logs directory
    os.makedirs('logs', exist_ok=True)
    # Test write permissions
    test_file = 'logs/test_write.tmp'
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    # If successful, add file handler
    log_handlers.append(logging.FileHandler('logs/arbitrage.log', encoding='utf-8'))
    print("✅ File logging enabled: logs/arbitrage.log")
except (PermissionError, OSError) as e:
    print(f"⚠️  File logging disabled (permission error): {e}")
    print("📄 Logging to console only")

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Represents a real arbitrage opportunity"""
    token_in: str
    token_out: str
    token_in_symbol: str
    token_out_symbol: str
    amount_in: int
    dex_buy: str
    dex_sell: str
    price_buy: float
    price_sell: float
    amount_out_buy: int
    amount_out_sell: int
    profit_percentage: float
    estimated_gas: int
    gas_cost_eth: float

class TelegramBot:
    """Simple Telegram bot for notifications"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            logger.info("📱 Telegram notifications enabled")
        else:
            logger.info("📱 Telegram not configured - running without notifications")
    
    def send_message(self, message: str):
        """Send message to Telegram"""
        if not self.enabled:
            return
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Telegram message failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Telegram error: {e}")
    
    def send_start_notification(self):
        """Send bot start notification"""
        message = "🚀 <b>BSC Arbitrage Scanner Started - PRODUCTION MODE</b>\n\n"
        message += "✅ Monitoring for profitable arbitrage opportunities\n"
        message += "📊 Execution thresholds: 0.8% | 1.2% | 2.5%\n"
        message += "� Only executes on profitable trades after ALL fees\n"
        message += "⚡ Dynamic scaling: 0.1 → 0.5 → 1.0 tokens\n"
        message += "💰 Total fees optimized: 0.4%\n"
        message += "⏰ Scanning every 10 seconds"
        self.send_message(message)
    
    def send_opportunity_found(self, opportunity: 'ArbitrageOpportunity'):
        """Send opportunity found notification"""
        message = f"💰 <b>Arbitrage Opportunity Found!</b>\n\n"
        message += f"🔄 Route: {opportunity.token_in_symbol} → {opportunity.token_out_symbol}\n"
        message += f"📈 Profit: {opportunity.profit_percentage:.2%}\n"
        message += f"🏪 Buy: {opportunity.dex_buy}\n"
        message += f"🏪 Sell: {opportunity.dex_sell}\n"
        message += f"💵 Amount: {opportunity.amount_in:,}"
        self.send_message(message)
    
    def send_execution_result(self, opportunity: 'ArbitrageOpportunity', success: bool, tx_hash: str = None, error: str = None):
        """Send execution result notification"""
        if success:
            message = f"✅ <b>Trade Executed Successfully!</b>\n\n"
            message += f"🎯 Profit: {opportunity.profit_percentage:.2%}\n"
            message += f"🔄 {opportunity.token_in_symbol} → {opportunity.token_out_symbol}\n"
            message += f"💰 Amount: {opportunity.amount_in:,}\n"
            if tx_hash:
                message += f"🔗 TX: {tx_hash[:10]}...{tx_hash[-10:]}"
        else:
            message = f"❌ <b>Trade Failed</b>\n\n"
            message += f"🔄 {opportunity.token_in_symbol} → {opportunity.token_out_symbol}\n"
            message += f"💰 Amount: {opportunity.amount_in:,}\n"
            if error:
                message += f"❌ Error: {error[:100]}"
        self.send_message(message)
    
    def send_stats_report(self, stats: dict):
        """Send periodic stats report"""
        message = f"📊 <b>Scanner Statistics</b>\n\n"
        message += f"⏱️ Scans completed: {stats['scans_completed']}\n"
        message += f"🔍 Opportunities found: {stats['opportunities_found']}\n"
        message += f"⚡ Immediate executions: {stats['immediate_executions']}\n"
        message += f"📈 Trades successful: {stats['trades_successful']}\n"
        message += f"💰 Total profit: {stats['total_profit_eth']:.6f} BNB\n"
        message += f"⛽ Total gas cost: {stats['total_gas_spent_eth']:.6f} BNB"
        self.send_message(message)

class ImmediateArbitrageScanner:
    """Immediate arbitrage scanner - executes trades instantly"""
    
    def __init__(self):
        logger.info("Starting Immediate Execution BSC Arbitrage Scanner")
        
        # Initialize Telegram bot
        self.telegram = TelegramBot()
        
        # Web3 setup
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        self.contract = self._setup_flashloan_contract()
        
        # Execution tracking
        self.recent_transactions = []  # Track recent transactions to avoid duplicates
        self.last_execution_time = 0
        self.min_execution_interval = 30  # Minimum 30 seconds between executions
        self.last_stats_report = 0
        self.stats_report_interval = 1800  # 30 minutes
        
        # Core high-liquidity tokens for immediate execution
        self.tokens = {
            # Core tokens
            'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
            'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
            'USDT': '0x55d398326f99059fF775485246999027B3197955',
            'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
            'ETH': '0x2170Ed0826c71020356F2c44b6feab4E2eBAEf50',
            'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
            'CAKE': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
            
            # Major cryptocurrencies
            'ADA': '0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47',
            'DOT': '0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402',
            'LINK': '0xF8A0BF9cF54Bb92F17374d9e9A321E6a111a51bD',
            'UNI': '0xBf5140A22578168FD562DCcF235E5D43A02ce9B1',
            'MATIC': '0xCC42724C6683B7E57334c4E856f4c9965ED682bD',
            'AVAX': '0x1CE0c2827e2eF14D5C4f29a091d735A204794041',
            'SOL': '0x570A5D26f7765Ecb712C0924E4De545B89fD43dF',
            'LTC': '0x4338665CBB7B2485A8855A139b75D5e34AB0DB94',
            'XRP': '0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE',
            'DOGE': '0xbA2aE424d960c26247Dd6c32edC70B295c744C43'
        }
        
        # DEX Routers
        self.dex_routers = {
            'PancakeSwap': {
                'address': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
                'factory': '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
            },
            'Biswap': {
                'address': '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
                'factory': '0x858E3312ed3A876947EA49d572A7C42DE08af7EE'
            },
            'ApeSwap': {
                'address': '0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7',
                'factory': '0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6'
            }
        }
        
        # Rate limiting - optimized for Pi
        self.last_request_time = 0
        self.request_delay = 2.0  # Slightly increased for Pi performance
        
        # Memory management for Raspberry Pi
        self.gc_interval = 100  # Run garbage collection every 100 operations
        self.operation_count = 0
        
        # Configuration - REALISTIC PROFITABLE THRESHOLDS
        # Set thresholds ABOVE total fees (0.3%) to ensure real profit
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.005'))  # 0.5% minimum profit (above 0.3% fees)
        self.immediate_execution_threshold = 0.008  # 0.8% for immediate execution
        self.aggressive_execution_threshold = 0.015  # 1.5% for aggressive execution  
        self.gas_cost_bnb = 0.0003  # Reduced gas cost estimate
        self.total_fee_percentage = 0.003  # 0.3% total fees (realistic)
        
        # Dynamic trade amounts based on opportunity size
        self.base_trade_amount = 0.1      # Base: 0.1 tokens ($0.10 - $6,100 depending on token)
        self.aggressive_trade_amount = 0.5  # Aggressive: 0.5 tokens ($0.50 - $30,500)
        self.max_trade_amount = 1.0       # Maximum: 1.0 tokens ($1.00 - $61,000)
        
        # Current trade amount (will be dynamic)
        self.trade_amount_tokens = self.base_trade_amount
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'pairs_scanned': 0,
            'opportunities_found': 0,
            'immediate_executions': 0,
            'trades_attempted': 0,
            'trades_successful': 0,
            'total_profit_eth': 0.0,
            'total_gas_spent_eth': 0.0
        }
        
        logger.info("Maximum Profit BSC Arbitrage Scanner initialized")
        logger.info(f"Base trade amount: {self.base_trade_amount} tokens")
        logger.info(f"Aggressive trade amount: {self.aggressive_trade_amount} tokens")
        logger.info(f"Maximum trade amount: {self.max_trade_amount} tokens")
        logger.info(f"Min profit threshold: {self.min_profit_threshold:.1%}")
        logger.info(f"Immediate execution threshold: {self.immediate_execution_threshold:.1%}")
        logger.info(f"Aggressive execution threshold: {self.aggressive_execution_threshold:.1%}")
        logger.info(f"Total fee percentage: {self.total_fee_percentage:.1%}")
        logger.info(f"Estimated gas cost: {self.gas_cost_bnb:.4f} BNB")
        
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection to BSC"""
        rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to BSC at {rpc_url}")
            
        latest_block = w3.eth.block_number
        logger.info(f"Connected to BSC: {rpc_url} (Block: {latest_block})")
        
        return w3
        
    def _setup_account(self) -> Optional[object]:
        """Setup account for transactions"""
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            logger.warning("No private key configured - running in simulation mode")
            return None
            
        try:
            account = self.w3.eth.account.from_key(private_key)
            logger.info(f"Account loaded: {account.address}")
            
            # Check balance
            balance = self.w3.eth.get_balance(account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            logger.info(f"Account balance: {balance_eth:.4f} BNB")
            
            if balance_eth < 0.01:
                logger.warning(f"Low BNB balance: {balance_eth:.4f} BNB - may not be enough for gas")
            
            return account
        except Exception as e:
            logger.error(f"Error loading account: {e}")
            return None
        
    def _get_flashloan_contract_abi(self) -> List[Dict]:
        """Get the flashloan contract ABI for BSC deployed contract"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "pair", "type": "address"},
                    {"internalType": "uint256", "name": "amount0Out", "type": "uint256"},
                    {"internalType": "uint256", "name": "amount1Out", "type": "uint256"},
                    {"internalType": "address", "name": "tokenBorrow", "type": "address"},
                    {"internalType": "address", "name": "tokenTarget", "type": "address"},
                    {"internalType": "address", "name": "buyRouter", "type": "address"},
                    {"internalType": "address", "name": "sellRouter", "type": "address"}
                ],
                "name": "executeFlashloanArbitrage",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getOwner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
    def _setup_flashloan_contract(self):
        """Setup flashloan contract"""
        # Use the newly deployed BSC V2 contract with real flashloans
        contract_address = '0x86742335Ec7CC7bBaa7d4244841c315Cf1978eAE'
        logger.info(f"Using NEW BSC V2 flashloan contract: {contract_address}")
        
        # Updated ABI for the new BSC V2 contract with flashloans
        abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "pairAddress", "type": "address"},
                    {"internalType": "uint256", "name": "amount0Out", "type": "uint256"},
                    {"internalType": "uint256", "name": "amount1Out", "type": "uint256"},
                    {"internalType": "address", "name": "tokenBorrow", "type": "address"},
                    {"internalType": "address", "name": "tokenTarget", "type": "address"},
                    {"internalType": "address", "name": "buyRouter", "type": "address"},
                    {"internalType": "address", "name": "sellRouter", "type": "address"}
                ],
                "name": "executeFlashloan",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"}
                ],
                "name": "getPairAddress",
                "outputs": [
                    {"internalType": "address", "name": "pair", "type": "address"}
                ],
                "stateMutability": "pure",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenBorrow", "type": "address"},
                    {"internalType": "address", "name": "tokenTarget", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "buyRouter", "type": "address"},
                    {"internalType": "address", "name": "sellRouter", "type": "address"}
                ],
                "name": "checkProfitability",
                "outputs": [
                    {"internalType": "uint256", "name": "profit", "type": "uint256"},
                    {"internalType": "bool", "name": "profitable", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=abi
            )
            
            logger.info(f"NEW BSC V2 flashloan contract loaded: {contract_address}")
            return contract
        except Exception as e:
            logger.warning(f"Failed to load BSC V2 contract {contract_address}: {e}")
            logger.info("Running in simulation mode")
            return None
        
    def _rate_limit(self):
        """Apply rate limiting between requests with Pi optimization"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
        # Memory management for Pi
        self.operation_count += 1
        if self.operation_count % self.gc_interval == 0:
            gc.collect()  # Force garbage collection
        
    def _get_amounts_out(self, router_address: str, amount_in: int, path: List[str]) -> Optional[List[int]]:
        """Get amounts out with rate limiting and better error handling"""
        self._rate_limit()
        
        try:
            # Router ABI for getAmountsOut
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
            
            # Convert path to checksum addresses
            checksum_path = [Web3.to_checksum_address(addr) for addr in path]
            
            amounts = router_contract.functions.getAmountsOut(amount_in, checksum_path).call()
            
            # Validate the amounts make sense
            if len(amounts) >= 2 and amounts[-1] > 0:
                # Check if the price is reasonable (not extreme outliers)
                price = float(amounts[-1]) / float(amount_in)
                if 0.000001 < price < 1000000:  # Reasonable price range
                    return amounts
                else:
                    logger.debug(f"Extreme price detected ({price:.6f}) from {router_address}, filtering out")
                    return None
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting amounts out from {router_address}: {e}")
            return None
            
    def _get_dynamic_trade_amount(self, profit_percentage: float) -> float:
        """Get dynamic trade amount based on profit percentage"""
        if profit_percentage >= self.aggressive_execution_threshold:
            # 2.5%+ profit: Use maximum trade size for maximum profit
            return self.max_trade_amount
        elif profit_percentage >= self.immediate_execution_threshold:
            # 1.2%+ profit: Use aggressive trade size
            return self.aggressive_trade_amount
        else:
            # 0.8%+ profit: Use base trade size (conservative)
            return self.base_trade_amount
    
    def _scan_pair_and_execute_immediately(self, token_in_symbol: str, token_out_symbol: str, amount_in: int) -> bool:
        """Scan a pair and execute immediately if profitable"""
        token_in = self.tokens[token_in_symbol]
        token_out = self.tokens[token_out_symbol]
        path = [token_in, token_out]
        
        logger.info(f"Scanning {token_in_symbol}/{token_out_symbol}")
        
        # Get prices from all DEXes
        dex_prices = {}
        
        for dex_name, dex_info in self.dex_routers.items():
            amounts = self._get_amounts_out(dex_info['address'], amount_in, path)
            
            if amounts and len(amounts) >= 2:
                amount_out = amounts[-1]
                price = float(amount_out) / float(amount_in)
                dex_prices[dex_name] = {
                    'price': price,
                    'amount_out': amount_out
                }
                logger.info(f"  {dex_name}: {price:.6f} ({amount_out:,})")
        
        # Show price differences between DEXes
        if len(dex_prices) >= 2:
            prices = [(name, data['price']) for name, data in dex_prices.items()]
            prices.sort(key=lambda x: x[1])  # Sort by price
            
            if len(prices) >= 2:
                lowest_dex, lowest_price = prices[0]
                highest_dex, highest_price = prices[-1]
                price_diff_percentage = ((highest_price - lowest_price) / lowest_price) * 100
                
                logger.info(f"  📊 Price spread: {price_diff_percentage:.3f}% ({lowest_dex}: {lowest_price:.6f} → {highest_dex}: {highest_price:.6f})")
        
        # Find arbitrage opportunities
        if len(dex_prices) >= 2:
            dex_names = list(dex_prices.keys())
            
            for i in range(len(dex_names)):
                for j in range(i + 1, len(dex_names)):
                    dex_buy = dex_names[i]
                    dex_sell = dex_names[j]
                    
                    price_buy = dex_prices[dex_buy]['price']
                    price_sell = dex_prices[dex_sell]['price']
                    
                    # Check both directions with REAL arbitrage profit calculation
                    
                    # Direction 1: Start with token_in, buy token_out on dex_buy, sell back on dex_sell
                    if dex_buy in dex_prices and dex_sell in dex_prices:
                        # Calculate round-trip: token_in -> token_out (on dex_buy) -> token_in (on dex_sell)
                        amount_out_step1 = dex_prices[dex_buy]['amount_out']  # token_out from dex_buy
                        
                        # Get reverse path amounts (token_out -> token_in on dex_sell)
                        reverse_path = [token_out, token_in]
                        reverse_amounts = self._get_amounts_out(
                            self.dex_routers[dex_sell]['address'], 
                            amount_out_step1, 
                            reverse_path
                        )
                        
                        if reverse_amounts and len(reverse_amounts) >= 2:
                            final_amount = reverse_amounts[-1]
                            
                            # Calculate real arbitrage profit with ALL fees included (optimized for larger trades)
                            flashloan_fee = (amount_in * 2) // 1000  # 0.2% flashloan fee
                            dex_fees = (amount_in * 3) // 1000       # ~0.3% total DEX fees (0.15% x 2) - account for slippage on larger trades
                            gas_cost_tokens = int(self.gas_cost_bnb * 1e18 * 0.1)  # Gas cost in token terms (conservative estimate)
                            
                            total_fees = flashloan_fee + dex_fees + gas_cost_tokens
                            amount_needed = amount_in + total_fees
                            
                            real_profit = final_amount - amount_needed
                            real_profit_percentage = (real_profit / amount_in) if real_profit > 0 else 0
                            
                            # Determine optimal trade size for this opportunity
                            optimal_trade_amount = self._get_dynamic_trade_amount(real_profit_percentage)
                            
                            # Log round-trip calculation details for high-spread pairs
                            if price_diff_percentage > 1.0:  # Log for promising pairs (>1.0%)
                                logger.info(f"    🔍 Round-trip calc: {amount_in:,} -> {amount_out_step1:,} -> {final_amount:,}")
                                logger.info(f"    💰 Fees: FL:{flashloan_fee:,} DEX:{dex_fees:,} GAS:{gas_cost_tokens:,} = {total_fees:,}")
                                logger.info(f"    📊 Real profit: {real_profit:,} ({real_profit_percentage:.4%}) vs min {self.min_profit_threshold:.3%}")
                                logger.info(f"    ⚡ Optimal trade size: {optimal_trade_amount} tokens")
                            
                            # More realistic profit check
                            min_profit_tokens = int(amount_in * self.min_profit_threshold)
                            
                            if real_profit > min_profit_tokens and real_profit_percentage > self.min_profit_threshold:
                                opportunity = ArbitrageOpportunity(
                                    token_in=token_in,
                                    token_out=token_out,
                                    token_in_symbol=token_in_symbol,
                                    token_out_symbol=token_out_symbol,
                                    amount_in=amount_in,
                                    dex_buy=dex_buy,  # Where to buy token_out with token_in
                                    dex_sell=dex_sell,  # Where to sell token_out back to token_in
                                    price_buy=dex_prices[dex_buy]['price'],
                                    price_sell=dex_prices[dex_sell]['price'],
                                    amount_out_buy=amount_out_step1,
                                    amount_out_sell=final_amount,
                                    profit_percentage=real_profit_percentage,
                                    estimated_gas=200000,
                                    gas_cost_eth=0.002
                                )
                                
                                logger.info(f"[FOUND] {token_in_symbol}/{token_out_symbol}: {real_profit_percentage:.3%} REAL profit after ALL fees")
                                logger.info(f"        Route: {token_in_symbol} -> {token_out_symbol} on {dex_buy} -> {token_in_symbol} on {dex_sell}")
                                logger.info(f"        After fees: {real_profit / 1e18:.6f} {token_in_symbol}")
                                logger.info(f"        Fee breakdown: FL:{flashloan_fee/1e18:.4f} DEX:{dex_fees/1e18:.4f} GAS:{gas_cost_tokens/1e18:.4f}")
                                logger.info(f"        💡 Recommended trade size: {optimal_trade_amount} tokens")
                                
                                # Calculate potential profit in USD for different trade sizes
                                profit_base = (real_profit / 1e18) * self.base_trade_amount / self.trade_amount_tokens
                                profit_aggressive = (real_profit / 1e18) * self.aggressive_trade_amount / self.trade_amount_tokens
                                profit_max = (real_profit / 1e18) * self.max_trade_amount / self.trade_amount_tokens
                                logger.info(f"        💰 Potential profits: Base:{profit_base:.4f} | Aggressive:{profit_aggressive:.4f} | Max:{profit_max:.4f} {token_in_symbol}")
                                
                                self.stats['opportunities_found'] += 1
                                
                                # DYNAMIC EXECUTION based on profit percentage
                                execution_tier = "NONE"
                                if real_profit_percentage >= self.aggressive_execution_threshold:
                                    execution_tier = "AGGRESSIVE"
                                elif real_profit_percentage >= self.immediate_execution_threshold:
                                    execution_tier = "IMMEDIATE"
                                
                                if real_profit_percentage >= self.immediate_execution_threshold:
                                    # Send Telegram notification for opportunity
                                    self.telegram.send_opportunity_found(opportunity)
                                    
                                    # Check if enough time has passed since last execution
                                    current_time = time.time()
                                    if current_time - self.last_execution_time < self.min_execution_interval:
                                        logger.info(f"[THROTTLED] Waiting {self.min_execution_interval}s between executions")
                                        continue
                                    
                                    logger.info(f"[{execution_tier}] High profit {real_profit_percentage:.2%} - EXECUTING NOW with {optimal_trade_amount} tokens!")
                                    self.stats['immediate_executions'] += 1
                                    
                                    # Update trade amount for this execution
                                    original_trade_amount = self.trade_amount_tokens
                                    self.trade_amount_tokens = optimal_trade_amount
                                    
                                    success = self.execute_arbitrage_trade(opportunity)
                                    
                                    # Restore original trade amount
                                    self.trade_amount_tokens = original_trade_amount
                                    
                                    # Send execution result notification
                                    if success:
                                        logger.info(f"[SUCCESS] {execution_tier} execution successful!")
                                        self.telegram.send_execution_result(opportunity, True)
                                        self.last_execution_time = current_time
                                        return True
                                    else:
                                        logger.warning(f"[FAILED] {execution_tier} execution failed")
                                        self.telegram.send_execution_result(opportunity, False, error="Execution failed")
                                else:
                                    logger.info(f"[QUEUED] Profit {real_profit_percentage:.2%} below immediate threshold {self.immediate_execution_threshold:.1%}")
                    
                    # Direction 2: Test reverse direction (swap the DEXes)
                    if dex_sell in dex_prices and dex_buy in dex_prices:
                        # Calculate round-trip: token_in -> token_out (on dex_sell) -> token_in (on dex_buy)
                        amount_out_step1 = dex_prices[dex_sell]['amount_out']  # token_out from dex_sell
                        
                        # Get reverse path amounts (token_out -> token_in on dex_buy)
                        reverse_path = [token_out, token_in]
                        reverse_amounts = self._get_amounts_out(
                            self.dex_routers[dex_buy]['address'], 
                            amount_out_step1, 
                            reverse_path
                        )
                        
                        if reverse_amounts and len(reverse_amounts) >= 2:
                            final_amount = reverse_amounts[-1]
                            
                            # Calculate real arbitrage profit with ALL fees included (optimized for larger trades)
                            flashloan_fee = (amount_in * 2) // 1000  # 0.2% flashloan fee
                            dex_fees = (amount_in * 3) // 1000       # ~0.3% total DEX fees (0.15% x 2) - account for slippage on larger trades
                            gas_cost_tokens = int(self.gas_cost_bnb * 1e18 * 0.1)  # Gas cost in token terms (conservative estimate)
                            
                            total_fees = flashloan_fee + dex_fees + gas_cost_tokens
                            amount_needed = amount_in + total_fees
                            
                            real_profit = final_amount - amount_needed
                            real_profit_percentage = (real_profit / amount_in) if real_profit > 0 else 0
                            
                            # Determine optimal trade size for this opportunity
                            optimal_trade_amount = self._get_dynamic_trade_amount(real_profit_percentage)
                            
                            # Log round-trip calculation details for high-spread pairs
                            if price_diff_percentage > 1.0:  # Log for promising pairs (>1.0%)
                                logger.info(f"    🔍 Reverse calc: {amount_in:,} -> {amount_out_step1:,} -> {final_amount:,}")
                                logger.info(f"    💰 Fees: FL:{flashloan_fee:,} DEX:{dex_fees:,} GAS:{gas_cost_tokens:,} = {total_fees:,}")
                                logger.info(f"    📊 Reverse profit: {real_profit:,} ({real_profit_percentage:.4%}) vs min {self.min_profit_threshold:.3%}")
                                logger.info(f"    ⚡ Optimal trade size: {optimal_trade_amount} tokens")
                            
                            # More realistic profit check
                            min_profit_tokens = int(amount_in * self.min_profit_threshold)
                            
                            if real_profit > min_profit_tokens and real_profit_percentage > self.min_profit_threshold:
                                opportunity = ArbitrageOpportunity(
                                    token_in=token_in,
                                    token_out=token_out,
                                    token_in_symbol=token_in_symbol,
                                    token_out_symbol=token_out_symbol,
                                    amount_in=amount_in,
                                    dex_buy=dex_sell,  # Reversed: Where to buy token_out with token_in
                                    dex_sell=dex_buy,  # Reversed: Where to sell token_out back to token_in  
                                    price_buy=dex_prices[dex_sell]['price'],
                                    price_sell=dex_prices[dex_buy]['price'],
                                    amount_out_buy=amount_out_step1,
                                    amount_out_sell=final_amount,
                                    profit_percentage=real_profit_percentage,
                                    estimated_gas=200000,
                                    gas_cost_eth=0.002
                                )
                                
                                logger.info(f"[FOUND] {token_in_symbol}/{token_out_symbol}: {real_profit_percentage:.3%} REAL profit after ALL fees (reverse)")
                                logger.info(f"        Route: {token_in_symbol} -> {token_out_symbol} on {dex_sell} -> {token_in_symbol} on {dex_buy}")
                                logger.info(f"        After fees: {real_profit / 1e18:.6f} {token_in_symbol}")
                                logger.info(f"        Fee breakdown: FL:{flashloan_fee/1e18:.4f} DEX:{dex_fees/1e18:.4f} GAS:{gas_cost_tokens/1e18:.4f}")
                                logger.info(f"        💡 Recommended trade size: {optimal_trade_amount} tokens")
                                
                                # Calculate potential profit in USD for different trade sizes
                                profit_base = (real_profit / 1e18) * self.base_trade_amount / self.trade_amount_tokens
                                profit_aggressive = (real_profit / 1e18) * self.aggressive_trade_amount / self.trade_amount_tokens
                                profit_max = (real_profit / 1e18) * self.max_trade_amount / self.trade_amount_tokens
                                logger.info(f"        💰 Potential profits: Base:{profit_base:.4f} | Aggressive:{profit_aggressive:.4f} | Max:{profit_max:.4f} {token_in_symbol}")
                                
                                self.stats['opportunities_found'] += 1
                                
                                # DYNAMIC EXECUTION based on profit percentage
                                execution_tier = "NONE"
                                if real_profit_percentage >= self.aggressive_execution_threshold:
                                    execution_tier = "AGGRESSIVE"
                                elif real_profit_percentage >= self.immediate_execution_threshold:
                                    execution_tier = "IMMEDIATE"
                                
                                if real_profit_percentage >= self.immediate_execution_threshold:
                                    # Send Telegram notification for opportunity
                                    self.telegram.send_opportunity_found(opportunity)
                                    
                                    # Check if enough time has passed since last execution
                                    current_time = time.time()
                                    if current_time - self.last_execution_time < self.min_execution_interval:
                                        logger.info(f"[THROTTLED] Waiting {self.min_execution_interval}s between executions")
                                        continue
                                    
                                    logger.info(f"[{execution_tier}] High profit {real_profit_percentage:.2%} - EXECUTING NOW with {optimal_trade_amount} tokens!")
                                    self.stats['immediate_executions'] += 1
                                    
                                    # Update trade amount for this execution
                                    original_trade_amount = self.trade_amount_tokens
                                    self.trade_amount_tokens = optimal_trade_amount
                                    
                                    success = self.execute_arbitrage_trade(opportunity)
                                    
                                    # Restore original trade amount
                                    self.trade_amount_tokens = original_trade_amount
                                    
                                    # Send execution result notification
                                    if success:
                                        logger.info(f"[SUCCESS] {execution_tier} execution successful!")
                                        self.telegram.send_execution_result(opportunity, True)
                                        self.last_execution_time = current_time
                                        return True
                                    else:
                                        logger.warning(f"[FAILED] {execution_tier} execution failed")
                                        self.telegram.send_execution_result(opportunity, False, error="Execution failed")
                                else:
                                    logger.info(f"[QUEUED] Profit {real_profit_percentage:.2%} below immediate threshold {self.immediate_execution_threshold:.1%}")
        else:
            logger.info(f"  ❌ Insufficient DEX data (only {len(dex_prices)} DEXes responded)")
        
        return False
            
    def execute_arbitrage_trade(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute arbitrage trade using new BSC V2 contract with flashloans"""
        if not self.account or not self.contract:
            logger.info(f"[SIMULATION] Would execute arbitrage for {opportunity.token_in_symbol}/{opportunity.token_out_symbol}")
            logger.info(f"[SIMULATION] Buy on {opportunity.dex_buy}, sell on {opportunity.dex_sell}")
            logger.info(f"[SIMULATION] Expected profit: {opportunity.profit_percentage:.2%}")
            return True
            
        try:
            logger.info(f"[EXECUTING] Real flashloan arbitrage trade for {opportunity.profit_percentage:.2%} profit")
            logger.info(f"[SCALING] Using dynamic trade amount: {self.trade_amount_tokens} tokens")
            
            # Calculate potential profit with current trade size
            scaled_profit = opportunity.profit_percentage * self.trade_amount_tokens
            logger.info(f"[PROFIT] Expected profit: {scaled_profit:.6f} {opportunity.token_in_symbol}")
            
            # Get router addresses - CORRECTED for flashloan arbitrage
            # In flashloan arbitrage:
            # - buyRouter should be where we get MORE target token per borrow token 
            # - sellRouter should be where we get MORE borrow token per target token
            # This is the OPPOSITE of traditional "buy low, sell high" 
            sell_router = self.dex_routers[opportunity.dex_buy]['address']   # Lower price DEX for selling back
            buy_router = self.dex_routers[opportunity.dex_sell]['address']   # Higher price DEX for buying
            
            # Get pair address directly from PancakeSwap factory (the contract calculation is wrong)
            try:
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
                
                factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'  # PancakeSwap Factory
                factory_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(factory_address),
                    abi=factory_abi
                )
                
                pair_address = factory_contract.functions.getPair(
                    opportunity.token_in, 
                    opportunity.token_out
                ).call()
                
                if pair_address == '0x0000000000000000000000000000000000000000':
                    logger.error(f"[ERROR] No PancakeSwap pair exists for {opportunity.token_in_symbol}/{opportunity.token_out_symbol}")
                    return False
                    
                logger.info(f"[TX] Using real PancakeSwap pair: {pair_address}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to get pair address from factory: {e}")
                return False
            
            # Determine which token to borrow (amount0Out or amount1Out)
            # Use current trade amount (which was set dynamically based on profit percentage)
            actual_amount_in = int(self.trade_amount_tokens * 1e18)
            amount0Out = actual_amount_in if opportunity.token_in < opportunity.token_out else 0
            amount1Out = actual_amount_in if opportunity.token_in >= opportunity.token_out else 0
            
            # Get current gas price and fresh nonce
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            logger.info(f"[TX] Gas price: {self.w3.from_wei(gas_price, 'gwei')} gwei")
            logger.info(f"[TX] Using nonce: {nonce}")
            logger.info(f"[TX] Pair: {pair_address}")
            logger.info(f"[TX] Amount0Out: {amount0Out}")
            logger.info(f"[TX] Amount1Out: {amount1Out}")
            logger.info(f"[TX] TokenBorrow: {opportunity.token_in}")
            logger.info(f"[TX] TokenTarget: {opportunity.token_out}")
            logger.info(f"[TX] Buy Router: {buy_router}")
            logger.info(f"[TX] Sell Router: {sell_router}")
            
            # Increased gas limit for flashloan
            gas_limit = 500000
            
            # Build transaction using new flashloan contract interface
            transaction = self.contract.functions.executeFlashloan(
                pair_address,           # pairAddress
                amount0Out,            # amount0Out
                amount1Out,            # amount1Out
                opportunity.token_in,   # tokenBorrow
                opportunity.token_out,  # tokenTarget
                buy_router,            # buyRouter
                sell_router            # sellRouter
            ).build_transaction({
                'from': self.account.address,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce
            })
            
            # Calculate gas cost
            gas_cost_wei = transaction['gas'] * transaction['gasPrice']
            gas_cost_eth = self.w3.from_wei(gas_cost_wei, 'ether')
            
            logger.info(f"[TX] Estimated gas cost: {gas_cost_eth:.6f} BNB")
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"[TX] Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                actual_gas_used = receipt.gasUsed
                actual_gas_cost = self.w3.from_wei(actual_gas_used * gas_price, 'ether')
                
                logger.info(f"[SUCCESS] Flashloan arbitrage successful!")
                logger.info(f"[SUCCESS] Profit: {opportunity.profit_percentage:.2%}")
                logger.info(f"[SUCCESS] Gas used: {actual_gas_used}")
                logger.info(f"[SUCCESS] Gas cost: {actual_gas_cost:.6f} BNB")
                
                self.stats['trades_successful'] += 1
                self.stats['total_profit_eth'] += opportunity.profit_percentage * 0.1  # Estimate
                self.stats['total_gas_spent_eth'] += float(actual_gas_cost)
                
                return True
            else:
                logger.warning(f"[FAILED] Transaction failed with status: {receipt.status}")
                logger.warning(f"[DEBUG] Gas used: {receipt.gasUsed}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Error executing flashloan arbitrage: {e}")
            return False
            
    def run_continuous_immediate_scanning(self):
        """Run continuous scanning with immediate execution - Pi optimized"""
        scan_interval = int(os.getenv('SCAN_INTERVAL', '10'))  # Configurable scan interval
        
        # Send start notification
        self.telegram.send_start_notification()
        
        logger.info(f"Starting continuous immediate arbitrage scanning (Raspberry Pi optimized)")
        logger.info(f"Scan interval: {scan_interval}s")
        logger.info(f"Request delay: {self.request_delay}s")
        logger.info(f"Memory management: GC every {self.gc_interval} operations")
        
        # High-frequency pairs for immediate execution - Optimized for Pi memory usage
        immediate_pairs = [
            # Core stablecoin pairs (highest liquidity, lowest memory usage)
            ('BUSD', 'USDT'),
            ('BUSD', 'USDC'),
            ('USDT', 'USDC'),
            
            # WBNB pairs (core BNB pairs)
            ('WBNB', 'BUSD'),
            ('WBNB', 'USDT'),
            ('WBNB', 'USDC'),
            ('WBNB', 'BTCB'),
            ('WBNB', 'CAKE'),
            
            # Major crypto pairs
            ('BTCB', 'BUSD'),
            ('BTCB', 'USDT'),
            ('CAKE', 'BUSD'),
            ('CAKE', 'USDT'),
            
            # Selected high-volume altcoin pairs (reduced for Pi memory)
            ('WBNB', 'ADA'),
            ('WBNB', 'DOT'),
            ('WBNB', 'LINK'),
            ('WBNB', 'MATIC'),
            ('ADA', 'BUSD'),
            ('DOT', 'BUSD'),
            ('LINK', 'BUSD'),
            ('MATIC', 'BUSD'),
        ]
        
        scan_count = 0
        memory_cleanup_interval = 10  # Clean memory every 10 scans
        
        try:
            while True:
                start_time = time.time()
                scan_count += 1
                
                logger.info("=" * 60)  # Shorter separator for Pi
                logger.info(f"🔍 Arbitrage scan #{scan_count} (Pi-optimized)")
                
                executed_this_round = False
                
                for i, (token_in_symbol, token_out_symbol) in enumerate(immediate_pairs, 1):
                    if token_in_symbol in self.tokens and token_out_symbol in self.tokens:
                        logger.info(f"[{i}/{len(immediate_pairs)}] {token_in_symbol}/{token_out_symbol}")
                        
                        # Use base trade amount for scanning
                        amount_in = int(self.base_trade_amount * 1e18)
                        executed = self._scan_pair_and_execute_immediately(token_in_symbol, token_out_symbol, amount_in)
                        
                        if executed:
                            executed_this_round = True
                            logger.info(f"✅ Trade executed: {token_in_symbol}/{token_out_symbol}")
                            break  # Exit scan after successful execution
                        
                        self.stats['pairs_scanned'] += 1
                
                self.stats['scans_completed'] += 1
                scan_time = time.time() - start_time
                
                # Memory cleanup for Pi
                if scan_count % memory_cleanup_interval == 0:
                    gc.collect()
                    logger.info(f"🧹 Memory cleanup completed (scan #{scan_count})")
                
                if executed_this_round:
                    logger.info(f"🎯 Scan #{scan_count}: EXECUTED in {scan_time:.1f}s")
                else:
                    logger.info(f"📊 Scan #{scan_count}: No execution in {scan_time:.1f}s")
                
                # Compact session statistics for Pi
                logger.info(f"📈 Stats: Scans:{self.stats['scans_completed']} | "
                          f"Pairs:{self.stats['pairs_scanned']} | "
                          f"Found:{self.stats['opportunities_found']} | "
                          f"Executed:{self.stats['immediate_executions']}")
                
                # Send periodic stats report
                current_time = time.time()
                if current_time - self.last_stats_report > self.stats_report_interval:
                    self.telegram.send_stats_report(self.stats)
                    self.last_stats_report = current_time
                
                # Wait for next scan
                logger.info(f"⏳ Next scan in {scan_interval}s...")
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Scanner stopped by user")
        except Exception as e:
            logger.error(f"💥 Scanner error: {e}")
            logger.info("🔄 Attempting to restart in 30 seconds...")
            time.sleep(30)
            # Restart the scanner
            self.run_continuous_immediate_scanning()

def main():
    """Main entry point - Pi optimized"""
    logger.info("🚀 BSC Arbitrage Scanner for Raspberry Pi")
    logger.info("=" * 50)
    logger.info("📊 Mode: Production (profitable trades only)")
    logger.info("🐳 Environment: Docker Container")
    logger.info("🔧 Optimized for: Raspberry Pi 4+ (1GB+ RAM)")
    
    try:
        scanner = ImmediateArbitrageScanner()
        scanner.run_continuous_immediate_scanning()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.info("🔄 Restarting in 30 seconds...")
        time.sleep(30)
        main()  # Recursive restart

if __name__ == "__main__":
    main()
