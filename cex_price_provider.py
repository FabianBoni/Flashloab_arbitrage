"""
CEX (Centralized Exchange) Price Provider for Arbitrage
Integrates with 8 major exchanges: Binance, Bybit, OKX, KuCoin, Gate.io, Bitget, MEXC, HTX
"""

import asyncio
import aiohttp
import time
import logging
import os
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class CexPrice:
    """CEX price data structure"""
    exchange: str
    symbol: str
    price: float
    volume: float
    timestamp: int
    bid: float
    ask: float

@dataclass
class CexConfig:
    """CEX configuration"""
    name: str
    api_base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    rate_limit: int = 10  # requests per second
    symbol_format: str = "{base}{quote}"  # Format function as string template

@dataclass
class CexDexOpportunity:
    """CEX-DEX arbitrage opportunity"""
    base_token: str
    quote_token: str
    amount_in: int
    profit_percentage: float
    cex_exchange: str
    dex_name: str
    cex_price: float
    dex_price: float
    direction: str  # 'CEX_TO_DEX' or 'DEX_TO_CEX'
    estimated_gas: int
    timestamp: int

class CexPriceProvider:
    """Centralized Exchange Price Provider"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_times: Dict[str, float] = {}
        
        # Load API keys from environment variables
        self._load_api_keys()
        
        # Initialize CEX configurations
        self.cex_configs = {
            'Binance': CexConfig(
                name='Binance',
                api_base_url='https://api.binance.com/api/v3',
                api_key=os.getenv('BINANCE_API_KEY'),
                api_secret=os.getenv('BINANCE_API_SECRET'),
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'Bybit': CexConfig(
                name='Bybit',
                api_base_url='https://api.bybit.com/v5',
                api_key=os.getenv('BYBIT_API_KEY'),
                api_secret=os.getenv('BYBIT_API_SECRET'),
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'OKX': CexConfig(
                name='OKX',
                api_base_url='https://www.okx.com/api/v5',
                api_key=os.getenv('OKX_API_KEY'),
                api_secret=os.getenv('OKX_API_SECRET'),
                rate_limit=20,
                symbol_format="{base}-{quote}"
            ),
            'KuCoin': CexConfig(
                name='KuCoin',
                api_base_url='https://api.kucoin.com/api/v1',
                api_key=os.getenv('KUCOIN_API_KEY'),
                api_secret=os.getenv('KUCOIN_API_SECRET'),
                rate_limit=10,
                symbol_format="{base}-{quote}"
            ),
            'Gate.io': CexConfig(
                name='Gate.io',
                api_base_url='https://api.gateio.ws/api/v4',
                api_key=os.getenv('GATEIO_API_KEY'),
                api_secret=os.getenv('GATEIO_API_SECRET'),
                rate_limit=10,
                symbol_format="{base}_{quote}"
            ),
            'Bitget': CexConfig(
                name='Bitget',
                api_base_url='https://api.bitget.com/api/v2',
                api_key=os.getenv('BITGET_API_KEY'),
                api_secret=os.getenv('BITGET_API_SECRET'),
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'MEXC': CexConfig(
                name='MEXC',
                api_base_url='https://api.mexc.com/api/v3',
                api_key=os.getenv('MEXC_API_KEY'),
                api_secret=os.getenv('MEXC_API_SECRET'),
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'HTX': CexConfig(
                name='HTX',
                api_base_url='https://api.huobi.pro/v1',
                api_key=os.getenv('HTX_API_KEY'),
                api_secret=os.getenv('HTX_API_SECRET'),
                rate_limit=10,
                symbol_format="{base}{quote}"
            )
        }
        
        logger.info(f"📈 Initialized {len(self.cex_configs)} CEX price providers")
    
    def _load_api_keys(self):
        """Load API keys from environment variables"""
        # This method can be extended to load from other sources
        # Currently, API keys are loaded directly in the config initialization
        pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'Flashloan-Arbitrage-Scanner/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _rate_limit(self, exchange: str) -> None:
        """Apply rate limiting per exchange"""
        now = time.time()
        last_request = self.last_request_times.get(exchange, 0)
        config = self.cex_configs[exchange]
        
        time_since_last = now - last_request
        min_interval = 1.0 / config.rate_limit  # Minimum time between requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_times[exchange] = time.time()
    
    def _format_symbol(self, exchange: str, base: str, quote: str) -> str:
        """Format trading pair symbol for specific exchange"""
        config = self.cex_configs[exchange]
        if exchange == 'HTX':
            return config.symbol_format.format(base=base.lower(), quote=quote.lower())
        else:
            return config.symbol_format.format(base=base.upper(), quote=quote.upper())
    
    async def _get_binance_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from Binance"""
        try:
            self._rate_limit('Binance')
            config = self.cex_configs['Binance']
            
            url = f"{config.api_base_url}/ticker/bookTicker?symbol={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return CexPrice(
                        exchange='Binance',
                        symbol=symbol,
                        price=(float(data['bidPrice']) + float(data['askPrice'])) / 2,
                        volume=0.0,  # Would need separate call
                        timestamp=int(time.time() * 1000),
                        bid=float(data['bidPrice']),
                        ask=float(data['askPrice'])
                    )
        except Exception as e:
            logger.debug(f"Error fetching Binance price for {symbol}: {e}")
        return None
    
    async def _get_bybit_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from Bybit"""
        try:
            self._rate_limit('Bybit')
            config = self.cex_configs['Bybit']
            
            url = f"{config.api_base_url}/market/tickers?category=spot&symbol={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {}).get('list', [])
                    if result:
                        item = result[0]
                        return CexPrice(
                            exchange='Bybit',
                            symbol=symbol,
                            price=float(item['lastPrice']),
                            volume=float(item.get('volume24h', 0)),
                            timestamp=int(time.time() * 1000),
                            bid=float(item.get('bid1Price', item['lastPrice'])),
                            ask=float(item.get('ask1Price', item['lastPrice']))
                        )
        except Exception as e:
            logger.debug(f"Error fetching Bybit price for {symbol}: {e}")
        return None
    
    async def _get_okx_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from OKX"""
        try:
            self._rate_limit('OKX')
            config = self.cex_configs['OKX']
            
            url = f"{config.api_base_url}/market/ticker?instId={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('data', [])
                    if result:
                        item = result[0]
                        return CexPrice(
                            exchange='OKX',
                            symbol=symbol,
                            price=float(item['last']),
                            volume=float(item.get('vol24h', 0)),
                            timestamp=int(time.time() * 1000),
                            bid=float(item.get('bidPx', item['last'])),
                            ask=float(item.get('askPx', item['last']))
                        )
        except Exception as e:
            logger.debug(f"Error fetching OKX price for {symbol}: {e}")
        return None
    
    async def _get_kucoin_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from KuCoin"""
        try:
            self._rate_limit('KuCoin')
            config = self.cex_configs['KuCoin']
            
            url = f"{config.api_base_url}/market/orderbook/level1?symbol={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('data')
                    if result:
                        return CexPrice(
                            exchange='KuCoin',
                            symbol=symbol,
                            price=float(result['price']),
                            volume=0.0,
                            timestamp=int(time.time() * 1000),
                            bid=float(result.get('bestBid', result['price'])),
                            ask=float(result.get('bestAsk', result['price']))
                        )
        except Exception as e:
            logger.debug(f"Error fetching KuCoin price for {symbol}: {e}")
        return None
    
    async def _get_gate_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from Gate.io"""
        try:
            self._rate_limit('Gate.io')
            config = self.cex_configs['Gate.io']
            
            url = f"{config.api_base_url}/spot/tickers?currency_pair={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        item = data[0]
                        return CexPrice(
                            exchange='Gate.io',
                            symbol=symbol,
                            price=float(item['last']),
                            volume=float(item.get('base_volume', 0)),
                            timestamp=int(time.time() * 1000),
                            bid=float(item.get('highest_bid', item['last'])),
                            ask=float(item.get('lowest_ask', item['last']))
                        )
        except Exception as e:
            logger.debug(f"Error fetching Gate.io price for {symbol}: {e}")
        return None
    
    async def _get_bitget_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from Bitget"""
        try:
            self._rate_limit('Bitget')
            config = self.cex_configs['Bitget']
            
            url = f"{config.api_base_url}/spot/market/tickers?symbol={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('data', [])
                    if result:
                        item = result[0]
                        return CexPrice(
                            exchange='Bitget',
                            symbol=symbol,
                            price=float(item['lastPr']),
                            volume=float(item.get('baseVolume', 0)),
                            timestamp=int(time.time() * 1000),
                            bid=float(item.get('bidPr', item['lastPr'])),
                            ask=float(item.get('askPr', item['lastPr']))
                        )
        except Exception as e:
            logger.debug(f"Error fetching Bitget price for {symbol}: {e}")
        return None
    
    async def _get_mexc_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from MEXC"""
        try:
            self._rate_limit('MEXC')
            config = self.cex_configs['MEXC']
            
            url = f"{config.api_base_url}/ticker/bookTicker?symbol={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return CexPrice(
                        exchange='MEXC',
                        symbol=symbol,
                        price=(float(data['bidPrice']) + float(data['askPrice'])) / 2,
                        volume=0.0,
                        timestamp=int(time.time() * 1000),
                        bid=float(data['bidPrice']),
                        ask=float(data['askPrice'])
                    )
        except Exception as e:
            logger.debug(f"Error fetching MEXC price for {symbol}: {e}")
        return None
    
    async def _get_htx_price(self, symbol: str) -> Optional[CexPrice]:
        """Get price from HTX (Huobi)"""
        try:
            self._rate_limit('HTX')
            config = self.cex_configs['HTX']
            
            url = f"{config.api_base_url}/market/detail/merged?symbol={symbol}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    tick = data.get('tick')
                    if tick:
                        return CexPrice(
                            exchange='HTX',
                            symbol=symbol,
                            price=float(tick['close']),
                            volume=float(tick.get('vol', 0)),
                            timestamp=int(time.time() * 1000),
                            bid=float(tick.get('bid', [tick['close']])[0]),
                            ask=float(tick.get('ask', [tick['close']])[0])
                        )
        except Exception as e:
            logger.debug(f"Error fetching HTX price for {symbol}: {e}")
        return None
    
    async def get_all_prices(self, base_token: str, quote_token: str) -> List[CexPrice]:
        """Get prices from all exchanges for a trading pair"""
        prices = []
        
        # Create tasks for all exchanges
        tasks = []
        for exchange_name in self.cex_configs.keys():
            symbol = self._format_symbol(exchange_name, base_token, quote_token)
            
            if exchange_name == 'Binance':
                task = self._get_binance_price(symbol)
            elif exchange_name == 'Bybit':
                task = self._get_bybit_price(symbol)
            elif exchange_name == 'OKX':
                task = self._get_okx_price(symbol)
            elif exchange_name == 'KuCoin':
                task = self._get_kucoin_price(symbol)
            elif exchange_name == 'Gate.io':
                task = self._get_gate_price(symbol)
            elif exchange_name == 'Bitget':
                task = self._get_bitget_price(symbol)
            elif exchange_name == 'MEXC':
                task = self._get_mexc_price(symbol)
            elif exchange_name == 'HTX':
                task = self._get_htx_price(symbol)
            else:
                continue
            
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in results:
            if isinstance(result, CexPrice):
                prices.append(result)
        
        logger.info(f"📊 Retrieved prices from {len(prices)}/{len(tasks)} CEX exchanges for {base_token}/{quote_token}")
        return prices
    
    async def find_cex_arbitrage_opportunities(self, base_token: str, quote_token: str) -> List[Dict]:
        """Find arbitrage opportunities between different CEX exchanges"""
        prices = await self.get_all_prices(base_token, quote_token)
        opportunities = []
        
        if len(prices) < 2:
            return opportunities
        
        # Compare all exchange pairs
        for i in range(len(prices)):
            for j in range(i + 1, len(prices)):
                price_a = prices[i]
                price_b = prices[j]
                
                # Direction 1: Buy on A, sell on B
                profit_ab = ((price_b.bid - price_a.ask) / price_a.ask) * 100
                if profit_ab > 0.1:  # Minimum 0.1% profit
                    opportunities.append({
                        'buy_exchange': price_a.exchange,
                        'sell_exchange': price_b.exchange,
                        'profit_percent': profit_ab,
                        'buy_price': price_a.ask,
                        'sell_price': price_b.bid
                    })
                
                # Direction 2: Buy on B, sell on A
                profit_ba = ((price_a.bid - price_b.ask) / price_b.ask) * 100
                if profit_ba > 0.1:  # Minimum 0.1% profit
                    opportunities.append({
                        'buy_exchange': price_b.exchange,
                        'sell_exchange': price_a.exchange,
                        'profit_percent': profit_ba,
                        'buy_price': price_b.ask,
                        'sell_price': price_a.bid
                    })
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
        return opportunities
    
    async def get_best_prices(self, base: str, quote: str) -> Dict[str, CexPrice]:
        """Get best prices from all exchanges for a trading pair"""
        prices = await self.get_all_prices(base, quote)
        
        if not prices:
            return {}
        
        # Find best bid and ask across all exchanges
        best_bid = max(prices, key=lambda p: p.bid) if prices else None
        best_ask = min(prices, key=lambda p: p.ask) if prices else None
        
        result = {}
        if best_bid:
            result['bestBid'] = best_bid
        if best_ask:
            result['bestAsk'] = best_ask
        
        # Calculate spread
        if best_bid and best_ask:
            spread = ((best_ask.ask - best_bid.bid) / best_bid.bid) * 100
            result['spread'] = spread
        
        # Also include all prices by exchange name
        for price in prices:
            result[price.exchange] = price
            
        return result
    
    def get_supported_pairs(self) -> List[Tuple[str, str]]:
        """Get list of supported trading pairs - Extended with volatile altcoins"""
        return [
            # Major crypto pairs
            ('BTC', 'USDT'),
            ('ETH', 'USDT'),
            ('BNB', 'USDT'),
            ('ADA', 'USDT'),
            ('XRP', 'USDT'),
            ('DOT', 'USDT'),
            ('LINK', 'USDT'),
            ('UNI', 'USDT'),
            ('MATIC', 'USDT'),
            ('DOGE', 'USDT'),
            
            # Volatile DeFi Tokens (Higher arbitrage potential)
            ('AAVE', 'USDT'),
            ('COMP', 'USDT'),
            ('CRV', 'USDT'),
            ('1INCH', 'USDT'),
            ('SUSHI', 'USDT'),
            ('YFI', 'USDT'),
            ('SNX', 'USDT'),
            ('ALPHA', 'USDT'),
            ('CAKE', 'USDT'),   # PancakeSwap - BSC native
            
            # Gaming & Metaverse (Very volatile)
            ('AXS', 'USDT'),    # Axie Infinity
            ('SAND', 'USDT'),   # The Sandbox
            ('MANA', 'USDT'),   # Decentraland
            ('ENJ', 'USDT'),    # Enjin Coin
            ('GALA', 'USDT'),   # Gala Games
            ('CHR', 'USDT'),    # Chromia
            ('TLM', 'USDT'),    # Alien Worlds
            
            # Emerging Layer 1s (High volatility)
            ('NEAR', 'USDT'),   # Near Protocol
            ('FTM', 'USDT'),    # Fantom
            ('AVAX', 'USDT'),   # Avalanche
            ('LUNA', 'USDT'),   # Terra Classic
            ('ATOM', 'USDT'),   # Cosmos
            ('SOL', 'USDT'),    # Solana
            ('ALGO', 'USDT'),   # Algorand
            ('ONE', 'USDT'),    # Harmony
            ('HBAR', 'USDT'),   # Hedera
            
            # Meme Coins (Extremely volatile)
            ('SHIB', 'USDT'),   # Shiba Inu
            ('FLOKI', 'USDT'),  # Floki Inu
            ('PEPE', 'USDT'),   # Pepe
            ('BONK', 'USDT'),   # Bonk
            ('WIF', 'USDT'),    # Dogwifhat
            ('MEME', 'USDT'),   # Memecoin
            
            # AI & Tech Tokens (Trending & volatile)
            ('FET', 'USDT'),    # Fetch.ai
            ('AGIX', 'USDT'),   # SingularityNET
            ('OCEAN', 'USDT'),  # Ocean Protocol
            ('RLC', 'USDT'),    # iExec RLC
            ('GRT', 'USDT'),    # The Graph
            
            # Small Cap Altcoins (High volatility potential)
            ('IOTX', 'USDT'),   # IoTeX
            ('HOT', 'USDT'),    # Holo
            ('BTT', 'USDT'),    # BitTorrent
            ('WIN', 'USDT'),    # WINkLink
            ('TRX', 'USDT'),    # Tron
            ('VET', 'USDT'),    # VeChain
            ('IOTA', 'USDT'),   # IOTA
            ('ZIL', 'USDT'),    # Zilliqa
            ('QTUM', 'USDT'),   # Qtum
            ('ICX', 'USDT'),    # ICON
            
            # Privacy Coins (Often mispriced)
            ('XMR', 'USDT'),    # Monero
            ('ZEC', 'USDT'),    # Zcash
            ('DASH', 'USDT'),   # Dash
            ('DCR', 'USDT'),    # Decred
            
            # Cross-chain & Bridge Tokens
            ('REN', 'USDT'),    # Ren Protocol
            ('CELR', 'USDT'),   # Celer Network
            ('SYN', 'USDT'),    # Synapse Protocol
            ('POLY', 'USDT'),   # Polymath
            
            # BTC pairs for volatile alts
            ('ETH', 'BTC'),
            ('BNB', 'BTC'),
            ('ADA', 'BTC'),
            ('LINK', 'BTC'),
            ('DOT', 'BTC'),
            ('AVAX', 'BTC'),
            ('SOL', 'BTC'),
            ('FTM', 'BTC'),
            ('NEAR', 'BTC'),
            ('AAVE', 'BTC'),
            
            # USDC pairs (often different spreads than USDT)
            ('BTC', 'USDC'),
            ('ETH', 'USDC'),
            ('BNB', 'USDC'),
            ('AVAX', 'USDC'),
            ('SOL', 'USDC'),
            ('LINK', 'USDC'),
            ('UNI', 'USDC'),
            ('AAVE', 'USDC'),
            
            # Stablecoin pairs (arbitrage opportunities)
            ('USDT', 'USDC'),
            ('BUSD', 'USDT'),
            ('BUSD', 'USDC'),
            ('DAI', 'USDT'),
            ('DAI', 'USDC')
        ]

# Token mapping for CEX-DEX arbitrage - Extended with volatile altcoins
CEX_DEX_TOKEN_MAPPINGS = {
    # Major BSC Token mappings (DEX address -> CEX symbol)
    '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c': 'BNB',    # WBNB
    '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56': 'BUSD',   # BUSD
    '0x55d398326f99059fF775485246999027B3197955': 'USDT',   # USDT
    '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d': 'USDC',   # USDC
    '0x2170Ed0880ac9A755fd29B2688956BD959F933F8': 'ETH',    # ETH
    '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c': 'BTC',    # BTCB
    '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82': 'CAKE',   # CAKE
    '0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47': 'ADA',    # ADA
    '0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE': 'XRP',    # XRP
    '0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402': 'DOT',    # DOT
    '0xF8A0BF9cF54Bb92F17374d9e9A321E6a111a51bD': 'LINK',   # LINK
    '0xCC42724C6683B7E57334c4E856f4c9965ED682bD': 'MATIC',  # MATIC
    '0xBf5140A22578168FD562DCcF235E5D43A02ce9B1': 'UNI',    # UNI
    '0xbA2aE424d960c26247Dd6c32edC70B295c744C43': 'DOGE',   # DOGE
    
    # DeFi Tokens (High volatility)
    '0xfb6115445Bff7b52FeB98650C87f44907E58f802': 'AAVE',   # AAVE
    '0x52CE071Bd9b1C4B00A0b92D298c512478CaD67e8': 'COMP',   # COMP
    '0x16939ef78684453bfDFb47825F8a5F714f12623a': 'CRV',    # CRV
    '0x111111111117dC0aa78b770fA6A738034120C302': '1INCH',  # 1INCH
    '0x947950BcC74888a40Ffa2593C5798F11Fc9124C4': 'SUSHI',  # SUSHI
    '0x88f1A5ae2A3BF98AEAF342D26B30a79438c9142e': 'YFI',    # YFI
    '0x9Ac983826058b8a9C7Aa1C9171441191232E8404': 'SNX',    # SNX
    '0xa1faa113cbE53436Df28FF0aEe54275c13B40975': 'ALPHA',  # ALPHA
    
    # Gaming & Metaverse (Very volatile)
    '0x715D400F88537b51125d67541e9280063b99d1c': 'AXS',     # Axie Infinity
    '0x67b6D479c7bB412C54e03dCA8E5Cc726364C49a': 'SAND',    # The Sandbox
    '0x26433c8127d9b4e9B71Eaa15111DF99Ea2EeB2f8': 'MANA',   # Decentraland
    '0xf629cBd94d3791C9250152BD8dfBDF380E2a3B9c': 'ENJ',    # Enjin Coin
    '0x7dDEE176F665cD201F93eEDE625770E2fD911990': 'GALA',   # Gala Games
    '0xf2Cd2AA0c7926743B1D4310b2BC984a0a453c3d4': 'CHR',    # Chromia
    '0x2222227E22102Fe3322098e4CBfE18cFebD57c95': 'TLM',    # Alien Worlds
    
    # Layer 1 Protocols (High volatility)
    '0x1fa4a73a3F0133f0025378af00236f3aBDEE5D63': 'NEAR',   # Near Protocol
    '0xAD29AbB318791D579433D831ed122aFeAf29dcfe': 'FTM',    # Fantom
    '0x1CE0c2827e2eF14D5C4f29a091d735A204794041': 'AVAX',   # Avalanche
    '0x156ab3346823B651294766e23e6Cf87254d68962': 'LUNA',   # Terra Classic
    '0x0Eb3a705fc54725037CC9e008bDede697f62F335': 'ATOM',   # Cosmos
    '0x570A5D26f7765Ecb712C0924E4De545B89fD43dF': 'SOL',    # Solana
    '0xfb6115445Bff7b52FeB98650C87f44907E58f802': 'ALGO',   # Algorand
    '0x03fF0ff224f904be3118461335064bB48Df47938': 'ONE',    # Harmony
    '0x2dfF88A56767223A5529eA5960Da7A3F5f766406': 'HBAR',   # Hedera
    
    # Meme Coins (Extremely volatile)
    '0x2859e4544C4bB03966803b044A93563Bd2D0DD4D': 'SHIB',   # Shiba Inu
    '0xfb5B838b6cfEEdC2873aB27866079AC55363D37E': 'FLOKI',  # Floki Inu
    '0x25d887Ce7a35172C62FeBFD67a1856F20FaEbB00': 'PEPE',   # Pepe
    '0xA697e272a73744b343528C3Bc4702F2565b2F422': 'BONK',   # Bonk
    '0xa2681f5B229a54C5d2E0Ff5A2Ed69A7cfc4B4A4': 'WIF',    # Dogwifhat
    '0xC642682d50Ca5aC5B8CB01E44dF90E5CAC5e7D4E': 'MEME',   # Memecoin
    
    # AI & Tech Tokens (Trending & volatile)
    '0x031b41e504677879370e9DBcF937283A8691Fa7f': 'FET',    # Fetch.ai
    '0x2D4aa90C169E4C4ABc6b8d9b82067FE74b1fE20B': 'AGIX',   # SingularityNET
    '0x282d8efCe846A88B159800bd4130ad77443Fa1A1': 'OCEAN',  # Ocean Protocol
    '0x4E4b2e1B39C656E15d579690063a2f560C19Cc': 'RLC',     # iExec RLC
    '0x52429063E6D0F5cee894cC8a1F67E3b14b32a93': 'GRT',     # The Graph
    
    # Small Cap Altcoins (High volatility potential)
    '0x9678E42ceBEb63F23197D726B29b1CB20d0064E5': 'IOTX',   # IoTeX
    '0x2D2457e3c4d90414c52aBB3Ff01394d231D6a4E3': 'HOT',    # Holo
    '0x8595F9dA7b868b1822194fAEd312235E43007b49': 'BTT',    # BitTorrent
    '0xaeCaa3C2E742b18da8Fb7F578dE4c8e5b11D21e': 'WIN',     # WINkLink
    '0x85EAC5Ac2F758618dFa09bDbe0cf174e7d574D5B': 'TRX',    # Tron
    '0x6FDcdfef7c496407cCb0cDC90fc95b2a37af13b': 'VET',     # VeChain
    '0xd944f1D1e9d5f9Bb90b62f9D45e447D989580782': 'IOTA',   # IOTA
    '0xb86AbCb37C3A4B64f74f59301AFF131a1BEcC787': 'ZIL',    # Zilliqa
    '0x1F41E42D0a9e3c0Dd3BA15b18b5E80F9FaE2D2B': 'QTUM',   # Qtum
    '0x9F81a10A72ce90A10b0b0e6D7f0d8c4eCa5a3ab': 'ICX',    # ICON
    
    # Privacy Coins (Often mispriced)
    '0x3B81f45EfE9B64e48C4Ba17D4d6a40c027e65b2': 'XMR',    # Monero
    '0xE4Cc45Bb5DBDA06dB6183E8bf016569f40497Aa5': 'ZEC',    # Zcash
    '0x20EE7B720f4E4c4FFcB00C4065cdae55271aECCa': 'DASH',   # Dash
    '0x13e4aC1A8Ba12b4Fe65Fc8B3fB2A2aB34AAd0d9': 'DCR',    # Decred
    
    # Cross-chain & Bridge Tokens
    '0x20e7Ac1F2F13e0ad2A454CF29d2f3c8E89B9f7': 'REN',     # Ren Protocol
    '0x5D34bE54c1Cc63e2c83eA1B7f2C6E85fc1C56B3': 'CELR',   # Celer Network
    '0xA29b548056c3fD0f68BAd9d4829EC4E66f22f796': 'SYN',    # Synapse Protocol
    '0xdF6B861bcc4E2B6F5C4b6F0b2F7C7F06bCa8a2': 'POLY',   # Polymath
    
    # Popular BSC Native Tokens
    '0x8076C74C5e3F5852037F31Ff0093Eeb8c8ADd8D3': 'SAFEMOON', # SafeMoon
    '0x603c7f932ED1fc6575303D8Fb018fDCBb0f39a95': 'BABY',   # BabyDoge
    '0xa1faa113cbE53436Df28FF0aEe54275c13B40975': 'ALPACA', # Alpaca Finance
}

def get_cex_symbol(dex_address: str) -> Optional[str]:
    """Get CEX symbol from DEX token address"""
    return CEX_DEX_TOKEN_MAPPINGS.get(dex_address.lower())

def get_dex_address(cex_symbol: str) -> Optional[str]:
    """Get DEX token address from CEX symbol"""
    for address, symbol in CEX_DEX_TOKEN_MAPPINGS.items():
        if symbol == cex_symbol:
            return address
    return None