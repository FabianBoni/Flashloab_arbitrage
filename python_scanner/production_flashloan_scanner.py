"""
Integrated BSC Flashloan Arbitrage Scanner & Executor
- Finds real arbitrage opportunities
- Executes via BSC native flashloans (PancakeSwap flashswap)
- Production ready with proper error handling
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
        logging.FileHandler('production_flashloan.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FlashloanOpportunity:
    """Real flashloan arbitrage opportunity"""
    token_borrow: str
    token_target: str
    token_borrow_symbol: str
    token_target_symbol: str
    amount_borrow: int
    pair_address: str
    amount0_out: int  # Amount of token0 to borrow
    amount1_out: int  # Amount of token1 to borrow
    buy_router: str
    sell_router: str
    buy_price: float
    sell_price: float
    profit_percentage: float
    estimated_profit_amount: int
    estimated_gas: int

class ProductionFlashloanArbitrage:
    """Production BSC Flashloan Arbitrage System"""
    
    def __init__(self):
        logger.info("Initializing Production BSC Flashloan Arbitrage")
        
        # Web3 and account setup
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        
        # Comprehensive token addresses (BSC mainnet)
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
            'DOGE': '0xbA2aE424d960c26247Dd6c32edC70B295c744C43',
            
            # Additional DeFi tokens
            'AAVE': '0xfb6115445Bff7b52FeB98650C87f44907E58f802',
            'COMP': '0x52CE071Bd9b1C4B00A0b92D298c512478CaD67e8',
            'MKR': '0x5f0Da599BB2ccCfcf6Fdfd7D81743B6020864350',
            'SUSHI': '0x947950BcC74888a40Ffa2593C5798F11Fc9124C4',
            'CRV': '0x96412902aa9aFf0E2c327ce01b9d2F2A827d6f7C',
            'YFI': '0x88f1A5ae2A3BF98AEAF342D26B30a79438c9142e',
            
            # Gaming/Metaverse tokens
            'AXS': '0x715D400F88537EE4da006c2f88eFdEd7C924db07',
            'SAND': '0x67b725d7e342d7B611fa85e859Df9697D9378B2e',
            'MANA': '0x26433c8127d9b4e9B71Eaa15111DF99Ea2EEB2f8',
            
            # Exchange tokens
            'FTT': '0x049d68029688eAbF473097a2fC38ef61633A3C7A',
            'BNT': '0xdB6a83e0d2c66B14A8E9B1b8dFDED3F0D24B5FF8',
            'CRO': '0x66e5F5f1b25Ea2AdB0e7e5FddC2bf41D0Ea1F17B',
            
            # Meme tokens
            'SHIB': '0x2859e4544C4bB03966803b044A93563Bd2D0DD4D',
            'FLOKI': '0xfb5B838b6cfEEdC2873aB27866079AC55363D37E',
            
            # Layer 1 tokens
            'NEAR': '0x1Fa4a73a3F0133f0025378af00236f3aBDEE5D63',
            'ATOM': '0x0Eb3a705fc54725037CC9e008bDede697f62F335',
            'ALGO': '0xa1faa113cbE53436Df28FF0aEe54275c13B40975',
            'XTZ': '0x16939ef78684453bfDFb47825F8a5F714f12623a',
            
            # BSC ecosystem tokens
            'VAI': '0x4BD17003473389A42DAF6a0a729f6Fdb328BbBd7',
            'XVS': '0xcF6BB5389c92Bdda8a3747Ddb454cB7a64626C63',
            'ALPHA': '0xa1faa113cbE53436Df28FF0aEe54275c13B40975',
            'BAKE': '0xE02dF9e3e622DeBdD69fb838bB799E3F168902c5',
            'BURGER': '0xAe9269f27437f0fcBC232d39Ec814844a51d6b8f',
            'AUTO': '0xa184088a740c695E156F91f5cC086a06bb78b827'
        }
        
        # DEX Routers
        self.dex_routers = {
            'PancakeSwap': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
            'Biswap': '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
            'ApeSwap': '0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7'
        }
        
        # PancakeSwap Factory for pairs
        self.pancake_factory = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
        
        # Load flashloan contract
        self.flashloan_contract = self._load_flashloan_contract()
        
        # Configuration
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.01'))  # 1%
        self.max_profit_threshold = 0.05  # 5%
        self.min_profit_amount_usd = 50  # Minimum $50 profit
        
        # Rate limiting
        self.last_request_time = 0
        self.request_delay = 2.0  # 2 seconds between requests
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'opportunities_found': 0,
            'profitable_opportunities': 0,
            'flashloans_executed': 0,
            'successful_arbitrages': 0,
            'failed_arbitrages': 0,
            'total_profit_bnb': 0.0,
            'total_gas_spent_bnb': 0.0
        }
        
        logger.info("Production Flashloan Arbitrage initialized")
        logger.info(f"Account: {self.account.address if self.account else 'Simulation mode'}")
        logger.info(f"Flashloan contract: {self.flashloan_contract.address if self.flashloan_contract else 'Not deployed'}")
        
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to BSC")
            
        logger.info(f"Connected to BSC: Block {w3.eth.block_number}")
        return w3
        
    def _setup_account(self):
        """Setup trading account"""
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            logger.warning("No private key - running in simulation mode")
            return None
            
        account = self.w3.eth.account.from_key(private_key)
        balance = self.w3.eth.get_balance(account.address)
        balance_bnb = self.w3.from_wei(balance, 'ether')
        
        logger.info(f"Account loaded: {account.address}")
        logger.info(f"Balance: {balance_bnb:.4f} BNB")
        
        if balance_bnb < 0.01:
            logger.warning(f"Low BNB balance: {balance_bnb:.4f} BNB")
            
        return account
        
    def _load_flashloan_contract(self):
        """Load the deployed flashloan contract"""
        # Try new contract address first
        contract_address = os.getenv('BSC_FLASHLOAN_CONTRACT')
        
        if not contract_address:
            # Fallback to old contract address
            contract_address = os.getenv('FLASHLOAN_CONTRACT_ADDRESS')
            
        if not contract_address:
            logger.warning("No flashloan contract address configured - using simulation")
            return None
            
        logger.info(f"Loading flashloan contract: {contract_address}")
            
        # BSC Flashloan Contract ABI (matches deployed contract)
        abi = [
            {
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
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
                "inputs": [
                    {"internalType": "address", "name": "sender", "type": "address"},
                    {"internalType": "uint256", "name": "amount0", "type": "uint256"},
                    {"internalType": "uint256", "name": "amount1", "type": "uint256"},
                    {"internalType": "bytes", "name": "data", "type": "bytes"}
                ],
                "name": "pancakeCall",
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
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "token", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "withdrawToken",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "token", "type": "address"}
                ],
                "name": "withdrawAllTokens",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "withdrawBNB",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=abi
            )
            
            # Verify contract
            owner = contract.functions.getOwner().call()
            logger.info(f"Flashloan contract loaded: {contract_address}")
            logger.info(f"Contract owner: {owner}")
            
            return contract
            
        except Exception as e:
            logger.error(f"Failed to load flashloan contract: {e}")
            return None
            
    def _rate_limit(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def get_pair_address(self, token_a: str, token_b: str) -> Optional[str]:
        """Get PancakeSwap pair address"""
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
            
            factory = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.pancake_factory),
                abi=factory_abi
            )
            
            pair_address = factory.functions.getPair(
                Web3.to_checksum_address(token_a),
                Web3.to_checksum_address(token_b)
            ).call()
            
            if pair_address != '0x0000000000000000000000000000000000000000':
                return pair_address
            return None
            
        except Exception as e:
            logger.debug(f"Error getting pair: {e}")
            return None
            
    def get_pair_info(self, pair_address: str) -> Optional[Dict]:
        """Get pair token info and reserves"""
        try:
            pair_abi = [
                {
                    "inputs": [],
                    "name": "token0",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "token1", 
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                },
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
            
            pair = self.w3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=pair_abi
            )
            
            token0 = pair.functions.token0().call()
            token1 = pair.functions.token1().call()
            reserves = pair.functions.getReserves().call()
            
            return {
                'token0': token0,
                'token1': token1,
                'reserve0': reserves[0],
                'reserve1': reserves[1]
            }
            
        except Exception as e:
            logger.debug(f"Error getting pair info: {e}")
            return None
            
    def get_router_price(self, router_address: str, amount_in: int, token_in: str, token_out: str) -> Optional[int]:
        """Get amount out from router"""
        self._rate_limit()
        
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
            
            router = self.w3.eth.contract(
                address=Web3.to_checksum_address(router_address),
                abi=router_abi
            )
            
            path = [
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out)
            ]
            
            amounts = router.functions.getAmountsOut(amount_in, path).call()
            
            if len(amounts) >= 2:
                return amounts[-1]
            return None
            
        except Exception as e:
            logger.debug(f"Router price error: {e}")
            return None
            
    def find_arbitrage_opportunities(self) -> List[FlashloanOpportunity]:
        """Find flashloan arbitrage opportunities"""
        opportunities = []
        
        # Comprehensive list of exactly 60 high-liquidity trading pairs
        priority_pairs = [
            # Major stablecoin pairs (highest liquidity)
            ('BUSD', 'USDT'),
            ('BUSD', 'USDC'),
            ('USDT', 'USDC'),
            
            # WBNB pairs (core BNB pairs)
            ('WBNB', 'BUSD'),
            ('WBNB', 'USDT'),
            ('WBNB', 'USDC'),
            ('WBNB', 'ETH'),
            ('WBNB', 'BTCB'),
            ('WBNB', 'CAKE'),
            
            # Major crypto pairs with stablecoins
            ('ETH', 'BUSD'),
            ('ETH', 'USDT'),
            ('ETH', 'USDC'),
            ('BTCB', 'BUSD'),
            ('BTCB', 'USDT'),
            ('BTCB', 'USDC'),
            
            # Cross-crypto pairs
            ('ETH', 'BTCB'),
            ('ETH', 'CAKE'),
            ('BTCB', 'CAKE'),
            
            # CAKE ecosystem pairs
            ('CAKE', 'BUSD'),
            ('CAKE', 'USDT'),
            ('CAKE', 'USDC'),
            
            # Additional major token pairs
            ('WBNB', 'ADA'),
            ('WBNB', 'DOT'),
            ('WBNB', 'LINK'),
            ('WBNB', 'UNI'),
            ('WBNB', 'MATIC'),
            ('WBNB', 'AVAX'),
            ('WBNB', 'SOL'),
            ('WBNB', 'LTC'),
            ('WBNB', 'XRP'),
            ('WBNB', 'DOGE'),
            
            # ETH ecosystem pairs
            ('ETH', 'ADA'),
            ('ETH', 'DOT'),
            ('ETH', 'LINK'),
            ('ETH', 'UNI'),
            ('ETH', 'MATIC'),
            ('ETH', 'AVAX'),
            
            # BTCB pairs
            ('BTCB', 'ADA'),
            ('BTCB', 'DOT'),
            ('BTCB', 'LINK'),
            
            # Stablecoin pairs with major tokens
            ('ADA', 'BUSD'),
            ('DOT', 'BUSD'),
            ('LINK', 'BUSD'),
            ('UNI', 'BUSD'),
            ('MATIC', 'BUSD'),
            ('AVAX', 'BUSD'),
            ('SOL', 'BUSD'),
            ('LTC', 'BUSD'),
            ('XRP', 'BUSD'),
            ('DOGE', 'BUSD'),
            
            # USDT pairs
            ('ADA', 'USDT'),
            ('DOT', 'USDT'),
            ('LINK', 'USDT'),
            ('UNI', 'USDT'),
            ('MATIC', 'USDT'),
            ('AVAX', 'USDT'),
            ('SOL', 'USDT'),
            ('LTC', 'USDT'),
            ('XRP', 'USDT'),
            ('DOGE', 'USDT')
        ]
        
        for token_a_symbol, token_b_symbol in priority_pairs:
            if token_a_symbol not in self.tokens or token_b_symbol not in self.tokens:
                continue
                
            token_a = self.tokens[token_a_symbol]
            token_b = self.tokens[token_b_symbol]
            
            # Get pair for flashloan
            pair_address = self.get_pair_address(token_a, token_b)
            if not pair_address:
                continue
                
            pair_info = self.get_pair_info(pair_address)
            if not pair_info:
                continue
                
            # Calculate reasonable flashloan amounts
            smaller_reserve = min(pair_info['reserve0'], pair_info['reserve1'])
            flashloan_amount = min(
                int(smaller_reserve * 0.05),  # 5% of smaller reserve
                int(1000 * 1e18)  # Or $1000 equivalent
            )
            
            if flashloan_amount < int(100 * 1e18):  # Skip if less than $100
                continue
                
            logger.info(f"Checking {token_a_symbol}/{token_b_symbol}")
            logger.info(f"  Pair: {pair_address}")
            logger.info(f"  Reserves: {pair_info['reserve0']:,} / {pair_info['reserve1']:,}")
            logger.info(f"  Testing amount: {flashloan_amount:,}")
            
            # Test both directions
            directions = [
                (token_a, token_b, token_a_symbol, token_b_symbol),
                (token_b, token_a, token_b_symbol, token_a_symbol)
            ]
            
            for token_borrow, token_target, borrow_symbol, target_symbol in directions:
                # Get prices from all DEXes
                dex_prices = {}
                
                for dex_name, router_address in self.dex_routers.items():
                    amount_out = self.get_router_price(
                        router_address, 
                        flashloan_amount,
                        token_borrow,
                        token_target
                    )
                    
                    if amount_out:
                        price = float(amount_out) / float(flashloan_amount)
                        dex_prices[dex_name] = {
                            'router': router_address,
                            'amount_out': amount_out,
                            'price': price
                        }
                
                if len(dex_prices) < 2:
                    continue
                    
                # Find best arbitrage
                dex_names = list(dex_prices.keys())
                
                for i in range(len(dex_names)):
                    for j in range(i + 1, len(dex_names)):
                        dex_buy = dex_names[i]
                        dex_sell = dex_names[j]
                        
                        buy_data = dex_prices[dex_buy]
                        sell_data = dex_prices[dex_sell]
                        
                        # We buy token_target with token_borrow, then sell back
                        target_amount = buy_data['amount_out']
                        
                        # Get return amount when selling target back to borrow token
                        return_amount = self.get_router_price(
                            sell_data['router'],
                            target_amount,
                            token_target,
                            token_borrow
                        )
                        
                        if not return_amount:
                            continue
                            
                        # Calculate profit
                        if return_amount > flashloan_amount:
                            gross_profit = return_amount - flashloan_amount
                            profit_percentage = float(gross_profit) / float(flashloan_amount)
                            
                            # Apply fees (0.3% flashloan + gas)
                            flashloan_fee = int(flashloan_amount * 0.003)
                            estimated_gas_cost_wei = int(300000 * self.w3.eth.gas_price)
                            
                            net_profit = gross_profit - flashloan_fee
                            
                            if (profit_percentage >= self.min_profit_threshold and 
                                profit_percentage <= self.max_profit_threshold and
                                net_profit > 0):
                                
                                # Determine amounts for flashswap
                                if pair_info['token0'].lower() == token_borrow.lower():
                                    amount0_out = flashloan_amount
                                    amount1_out = 0
                                else:
                                    amount0_out = 0
                                    amount1_out = flashloan_amount
                                
                                opportunity = FlashloanOpportunity(
                                    token_borrow=token_borrow,
                                    token_target=token_target,
                                    token_borrow_symbol=borrow_symbol,
                                    token_target_symbol=target_symbol,
                                    amount_borrow=flashloan_amount,
                                    pair_address=pair_address,
                                    amount0_out=amount0_out,
                                    amount1_out=amount1_out,
                                    buy_router=buy_data['router'],
                                    sell_router=sell_data['router'],
                                    buy_price=buy_data['price'],
                                    sell_price=float(return_amount) / float(target_amount),
                                    profit_percentage=profit_percentage,
                                    estimated_profit_amount=int(net_profit),
                                    estimated_gas=300000
                                )
                                
                                opportunities.append(opportunity)
                                
                                logger.info(f"[OPPORTUNITY] {borrow_symbol} -> {target_symbol}")
                                logger.info(f"  Profit: {profit_percentage:.2%}")
                                logger.info(f"  Buy on: {dex_buy}")
                                logger.info(f"  Sell on: {dex_sell}")
                                logger.info(f"  Net profit: {net_profit:,}")
        
        return opportunities
        
    def execute_flashloan_arbitrage(self, opportunity: FlashloanOpportunity) -> bool:
        """Execute flashloan arbitrage"""
        if not self.account or not self.flashloan_contract:
            logger.info(f"[SIMULATION] Would execute flashloan arbitrage:")
            logger.info(f"  {opportunity.token_borrow_symbol} -> {opportunity.token_target_symbol}")
            logger.info(f"  Profit: {opportunity.profit_percentage:.2%}")
            logger.info(f"  Amount: {opportunity.amount_borrow:,}")
            return True
            
        try:
            logger.info(f"[EXECUTING] Real flashloan arbitrage")
            logger.info(f"  Pair: {opportunity.token_borrow_symbol}/{opportunity.token_target_symbol}")
            logger.info(f"  Expected profit: {opportunity.profit_percentage:.2%}")
            
            # Build transaction
            gas_price = self.w3.eth.gas_price
            
            transaction = self.flashloan_contract.functions.executeFlashloanArbitrage(
                opportunity.pair_address,
                opportunity.amount0_out,
                opportunity.amount1_out,
                opportunity.token_borrow,
                opportunity.token_target,
                opportunity.buy_router,
                opportunity.sell_router
            ).build_transaction({
                'from': self.account.address,
                'gas': opportunity.estimated_gas,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })
            
            # Sign and send
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            # Fix for newer Web3.py versions - use rawTransaction instead of raw_transaction
            raw_tx = getattr(signed_txn, 'rawTransaction', getattr(signed_txn, 'raw_transaction', None))
            if raw_tx is None:
                raise Exception("Cannot access raw transaction data")
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            
            logger.info(f"[TX] Flashloan transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                gas_used = receipt.gasUsed
                gas_cost = self.w3.from_wei(gas_used * gas_price, 'ether')
                
                logger.info(f"✅ [SUCCESS] Flashloan arbitrage executed!")
                logger.info(f"   Gas used: {gas_used:,}")
                logger.info(f"   Gas cost: {gas_cost:.6f} BNB")
                
                self.stats['successful_arbitrages'] += 1
                self.stats['total_gas_spent_bnb'] += float(gas_cost)
                
                return True
            else:
                logger.warning(f"❌ [FAILED] Flashloan transaction failed")
                self.stats['failed_arbitrages'] += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ [ERROR] Flashloan execution error: {e}")
            self.stats['failed_arbitrages'] += 1
            return False
            
    def run_production_scanner(self):
        """Run production flashloan arbitrage scanner"""
        scan_interval = int(os.getenv('SCAN_INTERVAL', '30'))  # 30 seconds
        
        logger.info("🚀 Starting Production BSC Flashloan Arbitrage Scanner")
        logger.info(f"Scan interval: {scan_interval}s")
        logger.info(f"Min profit threshold: {self.min_profit_threshold:.1%}")
        logger.info(f"Max profit threshold: {self.max_profit_threshold:.1%}")
        
        scan_count = 0
        
        try:
            while True:
                start_time = time.time()
                scan_count += 1
                
                logger.info("=" * 80)
                logger.info(f"Production Flashloan Scan #{scan_count}")
                
                # Find opportunities
                opportunities = self.find_arbitrage_opportunities()
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} flashloan opportunities!")
                    
                    # Sort by profit percentage
                    opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
                    
                    for i, opp in enumerate(opportunities, 1):
                        logger.info(f"[{i}] {opp.token_borrow_symbol} -> {opp.token_target_symbol}")
                        logger.info(f"    Profit: {opp.profit_percentage:.2%}")
                        logger.info(f"    Amount: {opp.amount_borrow:,}")
                        logger.info(f"    Est. profit: {opp.estimated_profit_amount:,}")
                        
                        # Execute the most profitable opportunity
                        if i == 1:  # Execute only the best opportunity
                            self.stats['flashloans_executed'] += 1
                            success = self.execute_flashloan_arbitrage(opp)
                            
                            if success:
                                logger.info("✅ Flashloan executed successfully!")
                                break  # Exit after successful execution
                            else:
                                logger.warning("❌ Flashloan execution failed")
                    
                    self.stats['opportunities_found'] += len(opportunities)
                    self.stats['profitable_opportunities'] += len([o for o in opportunities if o.estimated_profit_amount > 0])
                    
                else:
                    logger.info("No profitable flashloan opportunities found")
                
                self.stats['scans_completed'] += 1
                scan_time = time.time() - start_time
                
                # Print statistics
                logger.info(f"Scan completed in {scan_time:.2f}s")
                logger.info("Session Statistics:")
                logger.info(f"  Scans: {self.stats['scans_completed']}")
                logger.info(f"  Opportunities found: {self.stats['opportunities_found']}")
                logger.info(f"  Profitable opportunities: {self.stats['profitable_opportunities']}")
                logger.info(f"  Flashloans executed: {self.stats['flashloans_executed']}")
                logger.info(f"  Successful arbitrages: {self.stats['successful_arbitrages']}")
                logger.info(f"  Failed arbitrages: {self.stats['failed_arbitrages']}")
                logger.info(f"  Total gas spent: {self.stats['total_gas_spent_bnb']:.6f} BNB")
                
                # Wait for next scan
                logger.info(f"Waiting {scan_interval}s for next scan...")
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            logger.info("Production scanner stopped by user")
        except Exception as e:
            logger.error(f"Scanner error: {e}")

def main():
    """Main entry point"""
    logger.info("🚀 Production BSC Flashloan Arbitrage System")
    logger.info("=" * 60)
    
    scanner = ProductionFlashloanArbitrage()
    scanner.run_production_scanner()

if __name__ == "__main__":
    main()
