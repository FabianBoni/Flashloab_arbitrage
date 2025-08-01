"""
Final Production BSC Arbitrage Scanner
- Debug price calculation issues
- All 60 high-volatility pairs
- Proper price validation
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
        logging.FileHandler('final_arbitrage.log', encoding='utf-8'),
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

class FinalArbitrageScanner:
    """Final production arbitrage scanner with price debugging"""
    
    def __init__(self):
        logger.info("Starting Final Production BSC Arbitrage Scanner")
        
        # Web3 setup
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        self.contract = self._setup_flashloan_contract()
        
        # All 60+ tokens for maximum arbitrage opportunities
        self.tokens = {
            # Major Tokens
            'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
            'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
            'USDT': '0x55d398326f99059fF775485246999027B3197955',
            'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
            'ETH': '0x2170Ed0826c71020356F2c44b6feab4E2eBAEf50',
            'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
            
            # DeFi Tokens (High Volatility)
            'CAKE': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
            'UNI': '0xBf5140A22578168FD562DCcF235E5D43A02ce9B1',
            'LINK': '0xF8A0BF9cF54Bb92F17374d9e9A321E6a111a51bD',
            'DOT': '0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402',
            'ADA': '0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47',
            'LTC': '0x4338665CBB7B2485A8855A139b75D5e34AB0DB94',
            'DOGE': '0xbA2aE424d960c26247Dd6c32edC70B295c744C43',
            'SHIB': '0x2859e4544C4bB03966803b044A93563Bd2D0DD4D',
            'AVAX': '0x1CE0c2827e2eF14D5C4f29a091d735A204794041',
            'MATIC': '0xCC42724C6683B7E57334c4E856f4c9965ED682bD',
            'ATOM': '0x0Eb3a705fc54725037CC9e008bDede697f62F335',
            'XRP': '0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE',
            'TRX': '0x85EAC5Ac2F758618dFa09bDbe0cf174e7d574D5B',
            'EOS': '0x56b6fB708fC5732DEC1Afc8D8556423A2EDcCbD6',
            
            # Meme Coins (Ultra High Volatility)
            'SAFEMOON': '0x42981d0bfbAf196529376EE702F2a9Eb9092fcB5',
            'BABYDOGE': '0xc748673057861a797275CD8A068AbB95A902e8de',
            'FLOKI': '0xfb5B838b6cfEEdC2873aB27866079AC55363D37E',
            'ELON': '0x761D38e5ddf6ccf6Cf7c55759d5210750B5D60F3',
            'KISHU': '0xA2B4C0Af19cC16a6CfAcCe81F192B024d625817D',
            
            # Gaming Tokens
            'AXS': '0x715D400F88537b51125958d2b4bC6E0c9Fc3b2dc',
            'SAND': '0x67b725d7e342d7B611fa85e859Df9697D9378B2e',
            'MANA': '0x26433c8127d9b4e9B71Eaa15111DF99Ea2EeB2f8',
            'ENJ': '0xF629cBd94d3791C9250152BD8dfBDF380E2a3B9c',
            'CHR': '0xf9CeC8d50f6c8ad3Fb6dcCEC577e05aA32B224FE',
            'ALICE': '0xAC51066d7bEC65Dc4589368da368b212745d63E8',
            'TLM': '0x2222227E22102Fe3322098e4CBfE18cFebD57c95',
            
            # DeFi Blue Chips
            'SUSHI': '0x947950BcC74888a40Ffa2593C5798F11Fc9124C4',
            'COMP': '0x52CE071Bd9b1C4B00A0b92D298c512478CaD67e8',
            'AAVE': '0xfb6115445Bff7b52FeB98650C87f44907E58f802',
            'MKR': '0x5f0Da599BB2ccCfcf6Fdfd7D81743B6020864350',
            'YFI': '0x88f1A5ae2A3BF98AEAF342D26B30a79438c9142e',
            'CRV': '0x96F859Ce0a2c7F7E2E3b2F2d225B4f6C4e9c4d6E',
            
            # Layer 1 Competitors
            'SOL': '0x570A5D26f7765Ecb712C0924E4De545B89fD43dF',
            'NEAR': '0x1FA4a73a3F0133f0025378af00236f3aBDEE5D63',
            'ALGO': '0xa1303E6199b319a891b79685F0537D289af1FC83',
            'FTM': '0xAD29AbB318791D579433D831ed122aFeAf29dcfe',
            'ONE': '0x03fF0ff224f904be3118461335064bB48Df47938',
            'LUNA': '0x156ab3346823B651294766e23e6Cf87254d68962',
            'ICP': '0xd8E5FFa5f5C3A0e35Fb68a9f51e25d6C5A30f3aE',
            
            # Exchange Tokens
            'CRO': '0xaD6CaEb32CD2c308980a548bD0Bc5AA4306c6c18',
            'FTT': '0x049d68029688eAbF473097a2fC38ef61633A3C7A',
            'HT': '0x5545153CCFcA01fbd7Dd11C0b23ba694D9509A6F',
            'OKB': '0xd9C442D36C40E5A2C2E6c9e1e0fCdDaA8f86c906',
            
            # Stable+ Volatility
            'TUSD': '0x14016E85a25aeb13065688cAFB43044C2ef86784',
            'PAX': '0xb7F8Cd00C5A06c0537E2aBfF0b58033d02e5E094',
            'HUSD': '0x0298c2b32eaE4da002a15f36fdf7615BEa3DA047',
            'DAI': '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3',
            'FRAX': '0x90c97f71e18723b0cf0dfa30ee176ab653e89f40',
            
            # New High-Volatility Additions
            'GMT': '0x3019BF2a2eF8040C242C9a4c5c4BD4C81678b2A1',
            'APE': '0xf0939011a9bb95c3B791f0cb546377Ed2693a574',
            'GALA': '0x7dDEE176F665cD201F93eEDE625770E2fD911990',
            'IMX': '0x0Ab43550A6915F9f67d0c454C2E90385E6497EaA',
            'LRC': '0xFC5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a',
            'CKB': '0x52f24a5e03aee338Da5fd9Df68D2b6FAe1178827',
            'WOO': '0x4691937a7508860F876c9c0a2a617E7d9E945d4B'
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
        self.request_delay = 1.5  # 1.5 seconds between requests
        
        # Configuration with much stricter validation
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.005'))  # 0.5%
        self.max_profit_threshold = 0.05  # 5% max - much more realistic
        self.immediate_execution_threshold = 0.008  # 0.8% - execute immediately
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'pairs_scanned': 0,
            'opportunities_found': 0,
            'realistic_opportunities': 0,
            'unrealistic_filtered': 0,
            'price_errors': 0,
            'immediate_executions': 0,
            'trades_attempted': 0,
            'trades_successful': 0,
            'total_profit_eth': 0.0,
            'total_gas_spent_eth': 0.0
        }
        
        logger.info("Final BSC Arbitrage Scanner initialized")
        logger.info(f"Min profit threshold: {self.min_profit_threshold:.1%}")
        logger.info(f"Max profit threshold: {self.max_profit_threshold:.1%}")
        logger.info(f"Immediate execution threshold: {self.immediate_execution_threshold:.1%}")
        logger.info(f"Total tokens available: {len(self.tokens)}")
        
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
        
    def _get_amounts_out_with_validation(self, router_address: str, amount_in: int, path: List[str], dex_name: str) -> Optional[List[int]]:
        """Get amounts out with comprehensive validation"""
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
            
            # VALIDATE AMOUNTS
            if not amounts or len(amounts) < 2:
                logger.debug(f"  {dex_name}: Invalid amounts length")
                return None
                
            amount_out = amounts[-1]
            
            # Validate amount_out is reasonable
            if amount_out <= 0:
                logger.debug(f"  {dex_name}: Zero or negative amount out")
                return None
                
            # Validate price isn't completely unrealistic
            price = float(amount_out) / float(amount_in)
            
            # Price should be within reasonable bounds (0.001 to 1000)
            if price < 0.001 or price > 1000:
                logger.warning(f"  {dex_name}: UNREALISTIC PRICE {price:.6f} - amount_in: {amount_in}, amount_out: {amount_out}")
                self.stats['price_errors'] += 1
                return None
                
            logger.debug(f"  {dex_name}: Valid price {price:.6f}")
            return amounts
            
        except Exception as e:
            logger.debug(f"  {dex_name}: Error - {e}")
            return None
            
    def _scan_pair_with_debug(self, token_in_symbol: str, token_out_symbol: str, amount_in: int) -> Optional[ArbitrageOpportunity]:
        """Scan a pair with detailed debugging"""
        token_in = self.tokens[token_in_symbol]
        token_out = self.tokens[token_out_symbol]
        path = [token_in, token_out]
        
        logger.debug(f"[DEBUG] Scanning {token_in_symbol}/{token_out_symbol}")
        logger.debug(f"[DEBUG] Path: {token_in} -> {token_out}")
        logger.debug(f"[DEBUG] Amount in: {amount_in}")
        
        # Get prices from all DEXes with validation
        dex_prices = {}
        
        for dex_name, dex_info in self.dex_routers.items():
            amounts = self._get_amounts_out_with_validation(
                dex_info['address'], 
                amount_in, 
                path, 
                dex_name
            )
            
            if amounts and len(amounts) >= 2:
                amount_out = amounts[-1]
                price = float(amount_out) / float(amount_in)
                dex_prices[dex_name] = {
                    'price': price,
                    'amount_out': amount_out
                }
                logger.debug(f"[DEBUG] {dex_name}: price={price:.6f}, amount_out={amount_out}")
        
        logger.debug(f"[DEBUG] Got {len(dex_prices)} valid DEX prices")
        
        # Need at least 2 DEXes for arbitrage
        if len(dex_prices) < 2:
            logger.debug(f"[DEBUG] Not enough DEX prices for arbitrage")
            return None
        
        # Find best arbitrage opportunity
        dex_names = list(dex_prices.keys())
        best_opportunity = None
        max_profit = 0
        
        for i in range(len(dex_names)):
            for j in range(i + 1, len(dex_names)):
                dex_a = dex_names[i]
                dex_b = dex_names[j]
                
                price_a = dex_prices[dex_a]['price']
                price_b = dex_prices[dex_b]['price']
                
                logger.debug(f"[DEBUG] Comparing {dex_a} ({price_a:.6f}) vs {dex_b} ({price_b:.6f})")
                
                # Check both directions
                profit_a_to_b = (price_b - price_a) / price_a if price_a > 0 else 0
                profit_b_to_a = (price_a - price_b) / price_b if price_b > 0 else 0
                
                logger.debug(f"[DEBUG] Profit A->B: {profit_a_to_b:.4%}, B->A: {profit_b_to_a:.4%}")
                
                # Choose best direction
                if profit_a_to_b > self.min_profit_threshold and profit_a_to_b <= self.max_profit_threshold:
                    if profit_a_to_b > max_profit:
                        max_profit = profit_a_to_b
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
                            profit_percentage=profit_a_to_b,
                            estimated_gas=200000,
                            gas_cost_eth=0.002
                        )
                        logger.debug(f"[DEBUG] New best opportunity: {profit_a_to_b:.4%}")
                
                if profit_b_to_a > self.min_profit_threshold and profit_b_to_a <= self.max_profit_threshold:
                    if profit_b_to_a > max_profit:
                        max_profit = profit_b_to_a
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
                            profit_percentage=profit_b_to_a,
                            estimated_gas=200000,
                            gas_cost_eth=0.002
                        )
                        logger.debug(f"[DEBUG] New best opportunity (reverse): {profit_b_to_a:.4%}")
        
        if best_opportunity:
            logger.debug(f"[DEBUG] Final best opportunity: {best_opportunity.profit_percentage:.4%}")
        else:
            logger.debug(f"[DEBUG] No profitable opportunities found")
            
        return best_opportunity
            
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
            
            # Build transaction parameters
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
            
            # Sign and send transaction
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
                logger.info(f"[SUCCESS] Gas cost: {actual_gas_cost:.6f} BNB")
                
                self.stats['trades_successful'] += 1
                self.stats['total_profit_eth'] += opportunity.profit_percentage * 0.1
                self.stats['total_gas_spent_eth'] += float(actual_gas_cost)
                
                return True
            else:
                logger.warning(f"[FAILED] Transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Error executing arbitrage: {e}")
            return False
            
    def run_continuous_final_scanning(self):
        """Run continuous scanning with all 60 pairs"""
        scan_interval = int(os.getenv('SCAN_INTERVAL', '15'))  # 15 seconds
        
        logger.info(f"Starting continuous final arbitrage scanning")
        logger.info(f"Scan interval: {scan_interval}s")
        logger.info(f"Request delay: {self.request_delay}s")
        
        # All 60 high-volatility pairs
        all_pairs = [
            # Major pairs with WBNB (highest liquidity)
            ('WBNB', 'BUSD'), ('WBNB', 'USDT'), ('WBNB', 'USDC'), ('WBNB', 'ETH'),
            ('WBNB', 'BTCB'), ('WBNB', 'CAKE'), ('WBNB', 'UNI'), ('WBNB', 'LINK'),
            ('WBNB', 'DOT'), ('WBNB', 'ADA'), ('WBNB', 'LTC'), ('WBNB', 'DOGE'),
            
            # Stablecoin arbitrage (most frequent opportunities)
            ('BUSD', 'USDT'), ('BUSD', 'USDC'), ('USDT', 'USDC'), ('BUSD', 'DAI'),
            ('USDT', 'DAI'), ('USDC', 'DAI'), ('BUSD', 'TUSD'), ('USDT', 'TUSD'),
            
            # DeFi token pairs
            ('CAKE', 'BUSD'), ('CAKE', 'USDT'), ('UNI', 'BUSD'), ('LINK', 'BUSD'),
            ('SUSHI', 'BUSD'), ('COMP', 'BUSD'), ('AAVE', 'BUSD'), ('YFI', 'BUSD'),
            
            # Meme coin volatility
            ('DOGE', 'BUSD'), ('SHIB', 'BUSD'), ('SAFEMOON', 'BUSD'), ('FLOKI', 'BUSD'),
            ('BABYDOGE', 'BUSD'), ('ELON', 'BUSD'), ('KISHU', 'BUSD'),
            
            # Gaming tokens
            ('AXS', 'BUSD'), ('SAND', 'BUSD'), ('MANA', 'BUSD'), ('ENJ', 'BUSD'),
            ('ALICE', 'BUSD'), ('TLM', 'BUSD'), ('CHR', 'BUSD'),
            
            # Layer 1 competitors
            ('SOL', 'BUSD'), ('AVAX', 'BUSD'), ('MATIC', 'BUSD'), ('ATOM', 'BUSD'),
            ('NEAR', 'BUSD'), ('FTM', 'BUSD'), ('ONE', 'BUSD'), ('ALGO', 'BUSD'),
            
            # Exchange tokens
            ('CRO', 'BUSD'), ('FTT', 'BUSD'), ('HT', 'BUSD'), ('OKB', 'BUSD'),
            
            # High volatility crosses
            ('ETH', 'BTCB'), ('ETH', 'BUSD'), ('BTCB', 'BUSD'), ('SOL', 'ETH'),
            ('AVAX', 'ETH'), ('MATIC', 'ETH'), ('LINK', 'ETH'), ('UNI', 'ETH'),
            
            # New additions
            ('GMT', 'BUSD'), ('APE', 'BUSD'), ('GALA', 'BUSD'), ('IMX', 'BUSD'),
            ('LRC', 'BUSD'), ('CKB', 'BUSD'), ('WOO', 'BUSD')
        ]
        
        logger.info(f"Total pairs to scan: {len(all_pairs)}")
        
        scan_count = 0
        
        try:
            while True:
                start_time = time.time()
                scan_count += 1
                
                logger.info("=" * 80)
                logger.info(f"Starting final arbitrage scan #{scan_count}")
                
                executed_this_round = False
                scanned_this_round = 0
                
                for i, (token_in_symbol, token_out_symbol) in enumerate(all_pairs, 1):
                    if token_in_symbol in self.tokens and token_out_symbol in self.tokens:
                        logger.info(f"[{i}/{len(all_pairs)}] Scanning {token_in_symbol}/{token_out_symbol}")
                        
                        amount_in = int(1e18)  # 1 token
                        opportunity = self._scan_pair_with_debug(token_in_symbol, token_out_symbol, amount_in)
                        
                        if opportunity:
                            self.stats['opportunities_found'] += 1
                            self.stats['realistic_opportunities'] += 1
                            
                            logger.info(f"[FOUND] {token_in_symbol}/{token_out_symbol}: {opportunity.profit_percentage:.2%} profit")
                            logger.info(f"        Buy on {opportunity.dex_buy} ({opportunity.price_buy:.6f})")
                            logger.info(f"        Sell on {opportunity.dex_sell} ({opportunity.price_sell:.6f})")
                            
                            # IMMEDIATE EXECUTION for profitable opportunities
                            if opportunity.profit_percentage >= self.immediate_execution_threshold:
                                logger.info(f"[IMMEDIATE] Profit {opportunity.profit_percentage:.2%} >= {self.immediate_execution_threshold:.1%} - EXECUTING NOW!")
                                self.stats['immediate_executions'] += 1
                                self.stats['trades_attempted'] += 1
                                
                                success = self.execute_arbitrage_trade(opportunity)
                                if success:
                                    logger.info(f"[SUCCESS] Immediate execution successful!")
                                    executed_this_round = True
                                    break  # Exit after successful execution
                                else:
                                    logger.warning(f"[FAILED] Immediate execution failed")
                            else:
                                logger.info(f"[SKIP] Profit {opportunity.profit_percentage:.2%} below execution threshold {self.immediate_execution_threshold:.1%}")
                        
                        scanned_this_round += 1
                        self.stats['pairs_scanned'] += 1
                
                self.stats['scans_completed'] += 1
                scan_time = time.time() - start_time
                
                if executed_this_round:
                    logger.info(f"[ROUND] Scan #{scan_count} completed with EXECUTION in {scan_time:.2f}s ({scanned_this_round} pairs)")
                else:
                    logger.info(f"[ROUND] Scan #{scan_count} completed with no execution in {scan_time:.2f}s ({scanned_this_round} pairs)")
                
                # Print session statistics
                logger.info("Session Statistics:")
                logger.info(f"   Scans: {self.stats['scans_completed']}")
                logger.info(f"   Pairs scanned: {self.stats['pairs_scanned']}")
                logger.info(f"   Opportunities found: {self.stats['opportunities_found']}")
                logger.info(f"   Realistic opportunities: {self.stats['realistic_opportunities']}")
                logger.info(f"   Unrealistic filtered: {self.stats['unrealistic_filtered']}")
                logger.info(f"   Price errors: {self.stats['price_errors']}")
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
    logger.info("Starting Final Production BSC Arbitrage Scanner")
    logger.info("============================================================")
    
    scanner = FinalArbitrageScanner()
    scanner.run_continuous_final_scanning()

if __name__ == "__main__":
    main()
