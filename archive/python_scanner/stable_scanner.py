"""
Stable Immediate Execution BSC Arbitrage Scanner
Fixed Web3 issues and unrealistic profit filtering
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

# Configure logging for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stable_arbitrage.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
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

class StableArbitrageScanner:
    """Stable arbitrage scanner with fixed Web3 integration"""
    
    def __init__(self):
        logger.info("Starting Stable Execution BSC Arbitrage Scanner")
        
        # Web3 setup
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        self.contract = self._setup_flashloan_contract()
        
        # Core high-liquidity tokens
        self.tokens = {
            'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
            'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
            'USDT': '0x55d398326f99059fF775485246999027B3197955',
            'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
            'ETH': '0x2170Ed0826c71020356F2c44b6feab4E2eBAEf50',
            'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c'
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
        
        # Rate limiting
        self.last_request_time = 0
        self.request_delay = 2  # 2 seconds between requests
        
        # Configuration
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.005'))  # 0.5%
        self.max_profit_threshold = 0.2  # 20% max to filter unrealistic data
        self.immediate_execution_threshold = 0.01  # 1% - execute immediately
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'pairs_scanned': 0,
            'opportunities_found': 0,
            'realistic_opportunities': 0,
            'unrealistic_filtered': 0,
            'immediate_executions': 0,
            'trades_attempted': 0,
            'trades_successful': 0,
            'total_profit_eth': 0.0,
            'total_gas_spent_eth': 0.0
        }
        
        logger.info("Stable BSC Arbitrage Scanner initialized")
        logger.info(f"Min profit threshold: {self.min_profit_threshold:.1%}")
        logger.info(f"Max profit threshold: {self.max_profit_threshold:.1%}")
        logger.info(f"Immediate execution threshold: {self.immediate_execution_threshold:.1%}")
        
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
        """Get the flashloan contract ABI"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address[]", "name": "routers", "type": "address[]"},
                    {"internalType": "address[]", "name": "tokens", "type": "address[]"}
                ],
                "name": "flashloan",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
    def _setup_flashloan_contract(self):
        """Setup flashloan contract"""
        contract_address = os.getenv('FLASHLOAN_CONTRACT_ADDRESS', '0xb85d7dfE30d5eaF5c564816Efa8bad9E99097551')
        abi = self._get_flashloan_contract_abi()
        
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi
        )
        
        logger.info(f"Flashloan contract loaded: {contract_address}")
        return contract
        
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def _get_amounts_out(self, router_address: str, amount_in: int, path: List[str]) -> Optional[List[int]]:
        """Get amounts out with rate limiting"""
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
            return amounts
            
        except Exception as e:
            logger.debug(f"Error getting amounts out from {router_address}: {e}")
            return None
            
    def _is_realistic_opportunity(self, profit_percentage: float, token_in_symbol: str, token_out_symbol: str) -> bool:
        """Check if opportunity is realistic"""
        # Filter out unrealistic profits
        if profit_percentage > self.max_profit_threshold:
            logger.warning(f"[UNREALISTIC] {token_in_symbol}/{token_out_symbol}: {profit_percentage:.2%} profit - FILTERED OUT")
            self.stats['unrealistic_filtered'] += 1
            return False
            
        # Filter out negative profits
        if profit_percentage <= 0:
            return False
            
        return True
            
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
                if amount_out > 0:  # Valid amount
                    price = float(amount_out) / float(amount_in)
                    dex_prices[dex_name] = {
                        'price': price,
                        'amount_out': amount_out
                    }
                    logger.debug(f"  {dex_name}: {price:.6f}")
        
        # Need at least 2 DEXes for arbitrage
        if len(dex_prices) < 2:
            logger.debug(f"  Not enough DEX prices for {token_in_symbol}/{token_out_symbol}")
            return False
        
        # Find arbitrage opportunities
        dex_names = list(dex_prices.keys())
        best_opportunity = None
        max_profit = 0
        
        for i in range(len(dex_names)):
            for j in range(i + 1, len(dex_names)):
                dex_a = dex_names[i]
                dex_b = dex_names[j]
                
                price_a = dex_prices[dex_a]['price']
                price_b = dex_prices[dex_b]['price']
                
                # Check A -> B direction
                if price_b > price_a:
                    profit_percentage = (price_b - price_a) / price_a
                    
                    if (profit_percentage > self.min_profit_threshold and 
                        self._is_realistic_opportunity(profit_percentage, token_in_symbol, token_out_symbol)):
                        
                        if profit_percentage > max_profit:
                            max_profit = profit_percentage
                            best_opportunity = ArbitrageOpportunity(
                                token_in=token_in,
                                token_out=token_out,
                                token_in_symbol=token_in_symbol,
                                token_out_symbol=token_out_symbol,
                                amount_in=amount_in,
                                dex_buy=dex_a,
                                dex_sell=dex_b,
                                price_buy=price_a,
                                price_sell=price_b,
                                amount_out_buy=dex_prices[dex_a]['amount_out'],
                                amount_out_sell=dex_prices[dex_b]['amount_out'],
                                profit_percentage=profit_percentage,
                                estimated_gas=200000,
                                gas_cost_eth=0.002
                            )
                
                # Check B -> A direction
                if price_a > price_b:
                    profit_percentage = (price_a - price_b) / price_b
                    
                    if (profit_percentage > self.min_profit_threshold and 
                        self._is_realistic_opportunity(profit_percentage, token_in_symbol, token_out_symbol)):
                        
                        if profit_percentage > max_profit:
                            max_profit = profit_percentage
                            best_opportunity = ArbitrageOpportunity(
                                token_in=token_in,
                                token_out=token_out,
                                token_in_symbol=token_in_symbol,
                                token_out_symbol=token_out_symbol,
                                amount_in=amount_in,
                                dex_buy=dex_b,
                                dex_sell=dex_a,
                                price_buy=price_b,
                                price_sell=price_a,
                                amount_out_buy=dex_prices[dex_b]['amount_out'],
                                amount_out_sell=dex_prices[dex_a]['amount_out'],
                                profit_percentage=profit_percentage,
                                estimated_gas=200000,
                                gas_cost_eth=0.002
                            )
        
        # Execute best opportunity if found
        if best_opportunity:
            self.stats['opportunities_found'] += 1
            self.stats['realistic_opportunities'] += 1
            
            logger.info(f"[FOUND] {token_in_symbol}/{token_out_symbol}: {best_opportunity.profit_percentage:.2%} profit")
            logger.info(f"        Buy on {best_opportunity.dex_buy} ({best_opportunity.price_buy:.6f})")
            logger.info(f"        Sell on {best_opportunity.dex_sell} ({best_opportunity.price_sell:.6f})")
            
            # IMMEDIATE EXECUTION for profitable opportunities
            if best_opportunity.profit_percentage >= self.immediate_execution_threshold:
                logger.info(f"[IMMEDIATE] Profit {best_opportunity.profit_percentage:.2%} >= {self.immediate_execution_threshold:.1%} - EXECUTING NOW!")
                self.stats['immediate_executions'] += 1
                self.stats['trades_attempted'] += 1
                
                success = self.execute_arbitrage_trade(best_opportunity)
                if success:
                    logger.info(f"[SUCCESS] Immediate execution successful!")
                    return True
                else:
                    logger.warning(f"[FAILED] Immediate execution failed")
            else:
                logger.info(f"[SKIP] Profit {best_opportunity.profit_percentage:.2%} below execution threshold {self.immediate_execution_threshold:.1%}")
        
        return False
            
    def execute_arbitrage_trade(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute arbitrage trade using flashloan"""
        if not self.account:
            logger.info(f"[SIMULATION] Would execute arbitrage for {opportunity.token_in_symbol}/{opportunity.token_out_symbol}")
            logger.info(f"[SIMULATION] Buy on {opportunity.dex_buy}, sell on {opportunity.dex_sell}")
            logger.info(f"[SIMULATION] Expected profit: {opportunity.profit_percentage:.2%}")
            self.stats['trades_successful'] += 1
            return True
            
        try:
            logger.info(f"[EXECUTING] Real arbitrage trade for {opportunity.profit_percentage:.2%} profit")
            
            # Build transaction
            routers = [
                self.dex_routers[opportunity.dex_buy]['address'],
                self.dex_routers[opportunity.dex_sell]['address']
            ]
            
            tokens = [opportunity.token_in, opportunity.token_out]
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            logger.info(f"[TX] Gas price: {self.w3.from_wei(gas_price, 'gwei'):.1f} gwei")
            
            # Build transaction
            transaction = self.contract.functions.flashloan(
                opportunity.token_in,
                opportunity.amount_in,
                routers,
                tokens
            ).build_transaction({
                'from': self.account.address,
                'gas': opportunity.estimated_gas,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })
            
            # Calculate gas cost
            gas_cost_wei = transaction['gas'] * transaction['gasPrice']
            gas_cost_eth = self.w3.from_wei(gas_cost_wei, 'ether')
            
            logger.info(f"[TX] Estimated gas cost: {gas_cost_eth:.6f} BNB")
            
            # Sign and send transaction (FIXED)
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"[TX] Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                actual_gas_used = receipt.gasUsed
                actual_gas_cost = self.w3.from_wei(actual_gas_used * gas_price, 'ether')
                
                logger.info(f"[SUCCESS] Arbitrage successful!")
                logger.info(f"[SUCCESS] Profit: {opportunity.profit_percentage:.2%}")
                logger.info(f"[SUCCESS] Gas used: {actual_gas_used}")
                logger.info(f"[SUCCESS] Gas cost: {actual_gas_cost:.6f} BNB")
                
                self.stats['trades_successful'] += 1
                self.stats['total_profit_eth'] += opportunity.profit_percentage * 0.1  # Estimate
                self.stats['total_gas_spent_eth'] += float(actual_gas_cost)
                
                return True
            else:
                logger.warning(f"[FAILED] Arbitrage transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Error executing arbitrage: {e}")
            return False
            
    def run_continuous_stable_scanning(self):
        """Run continuous scanning with immediate execution"""
        scan_interval = int(os.getenv('SCAN_INTERVAL', '15'))  # 15 seconds
        
        logger.info(f"Starting continuous stable arbitrage scanning")
        logger.info(f"Scan interval: {scan_interval}s")
        logger.info(f"Request delay: {self.request_delay}s")
        
        # High-frequency pairs for stable execution
        stable_pairs = [
            # Stablecoin arbitrage (most reliable)
            ('BUSD', 'USDT'), ('BUSD', 'USDC'), ('USDT', 'USDC'),
            
            # Major liquid pairs
            ('WBNB', 'BUSD'), ('WBNB', 'USDT'), ('WBNB', 'ETH'),
            ('ETH', 'BUSD'), ('BTCB', 'BUSD')
        ]
        
        scan_count = 0
        
        try:
            while True:
                start_time = time.time()
                scan_count += 1
                
                logger.info("=" * 80)
                logger.info(f"Starting stable arbitrage scan #{scan_count}")
                
                executed_this_round = False
                
                for i, (token_in_symbol, token_out_symbol) in enumerate(stable_pairs, 1):
                    if token_in_symbol in self.tokens and token_out_symbol in self.tokens:
                        logger.info(f"[{i}/{len(stable_pairs)}] Checking {token_in_symbol}/{token_out_symbol}")
                        
                        amount_in = int(1e18)  # 1 token
                        executed = self._scan_pair_and_execute_immediately(token_in_symbol, token_out_symbol, amount_in)
                        
                        if executed:
                            executed_this_round = True
                            logger.info(f"[EXECUTED] Trade completed for {token_in_symbol}/{token_out_symbol}")
                            break  # Exit scan after successful execution
                        
                        self.stats['pairs_scanned'] += 1
                
                self.stats['scans_completed'] += 1
                scan_time = time.time() - start_time
                
                if executed_this_round:
                    logger.info(f"[ROUND] Scan #{scan_count} completed with EXECUTION in {scan_time:.2f}s")
                else:
                    logger.info(f"[ROUND] Scan #{scan_count} completed with no execution in {scan_time:.2f}s")
                
                # Print session statistics
                logger.info("Session Statistics:")
                logger.info(f"   Scans: {self.stats['scans_completed']}")
                logger.info(f"   Pairs scanned: {self.stats['pairs_scanned']}")
                logger.info(f"   Opportunities found: {self.stats['opportunities_found']}")
                logger.info(f"   Realistic opportunities: {self.stats['realistic_opportunities']}")
                logger.info(f"   Unrealistic filtered: {self.stats['unrealistic_filtered']}")
                logger.info(f"   Immediate executions: {self.stats['immediate_executions']}")
                logger.info(f"   Trades attempted: {self.stats['trades_attempted']}")
                logger.info(f"   Trades successful: {self.stats['trades_successful']}")
                logger.info(f"   Total profit: {self.stats['total_profit_eth']:.6f} BNB")
                logger.info(f"   Total gas cost: {self.stats['total_gas_spent_eth']:.6f} BNB")
                
                # Wait for next scan
                logger.info(f"Waiting {scan_interval} seconds until next scan...")
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            logger.info("Scanner stopped by user")
        except Exception as e:
            logger.error(f"Scanner error: {e}")

def main():
    """Main entry point"""
    logger.info("Starting Stable BSC Arbitrage Scanner")
    logger.info("============================================================")
    
    scanner = StableArbitrageScanner()
    scanner.run_continuous_stable_scanning()

if __name__ == "__main__":
    main()
