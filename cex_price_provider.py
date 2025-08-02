"""
CEX (Centralized Exchange) Price Provider for Arbitrage
Integrates with 8 major exchanges: Binance, Bybit, OKX, KuCoin, Gate.io, Bitget, MEXC, HTX
"""

import asyncio
import aiohttp
import time
import logging
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
        
        # Initialize CEX configurations
        self.cex_configs = {
            'Binance': CexConfig(
                name='Binance',
                api_base_url='https://api.binance.com/api/v3',
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'Bybit': CexConfig(
                name='Bybit',
                api_base_url='https://api.bybit.com/v5',
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'OKX': CexConfig(
                name='OKX',
                api_base_url='https://www.okx.com/api/v5',
                rate_limit=20,
                symbol_format="{base}-{quote}"
            ),
            'KuCoin': CexConfig(
                name='KuCoin',
                api_base_url='https://api.kucoin.com/api/v1',
                rate_limit=10,
                symbol_format="{base}-{quote}"
            ),
            'Gate.io': CexConfig(
                name='Gate.io',
                api_base_url='https://api.gateio.ws/api/v4',
                rate_limit=10,
                symbol_format="{base}_{quote}"
            ),
            'Bitget': CexConfig(
                name='Bitget',
                api_base_url='https://api.bitget.com/api/v2',
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'MEXC': CexConfig(
                name='MEXC',
                api_base_url='https://api.mexc.com/api/v3',
                rate_limit=10,
                symbol_format="{base}{quote}"
            ),
            'HTX': CexConfig(
                name='HTX',
                api_base_url='https://api.huobi.pro/v1',
                rate_limit=10,
                symbol_format="{base}{quote}"
            )
        }
        
        logger.info(f"📈 Initialized {len(self.cex_configs)} CEX price providers")
    
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
    
    def get_supported_pairs(self) -> List[Tuple[str, str]]:
        """Get list of supported trading pairs"""
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
            
            # BTC pairs
            ('ETH', 'BTC'),
            ('BNB', 'BTC'),
            ('ADA', 'BTC'),
            
            # USDC pairs
            ('BTC', 'USDC'),
            ('ETH', 'USDC'),
            ('BNB', 'USDC'),
            
            # Stablecoin pairs
            ('USDT', 'USDC'),
            ('BUSD', 'USDT'),
            ('BUSD', 'USDC')
        ]

# Token mapping for CEX-DEX arbitrage
CEX_DEX_TOKEN_MAPPINGS = {
    # BSC Token mappings (DEX address -> CEX symbol)
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