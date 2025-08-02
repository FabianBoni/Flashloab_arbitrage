"""
CEX Trading API - Automated Trading Implementation
Implements automated trading APIs for all supported exchanges
"""

import asyncio
import aiohttp
import time
import logging
import hmac
import hashlib
import base64
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class TradeResult:
    """Result of a trade execution"""
    success: bool
    order_id: Optional[str]
    exchange: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    executed_amount: float
    executed_price: float
    fee: float
    timestamp: int
    error_message: Optional[str] = None

@dataclass
class ExchangeBalance:
    """Exchange balance information"""
    exchange: str
    currency: str
    available: float
    locked: float
    total: float

class CexTradingAPI:
    """Automated trading API for all supported exchanges"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_keys = self._load_api_keys()
        self.trading_enabled = self._check_trading_enabled()
        
        # Trading configuration
        self.max_trade_amount = {
            'BTC': 0.1,   # Max 0.1 BTC per trade
            'ETH': 2.0,   # Max 2 ETH per trade
            'BNB': 10.0,  # Max 10 BNB per trade
            'USDT': 5000, # Max 5000 USDT per trade
        }
        
        self.min_trade_amount = {
            'BTC': 0.001,  # Min 0.001 BTC
            'ETH': 0.01,   # Min 0.01 ETH
            'BNB': 0.1,    # Min 0.1 BNB
            'USDT': 10,    # Min 10 USDT
        }
        
        logger.info(f"🔧 CEX Trading API initialized - Trading enabled: {self.trading_enabled}")
    
    def _load_api_keys(self) -> Dict[str, Dict[str, str]]:
        """Load API keys from environment variables"""
        return {
            'Binance': {
                'api_key': os.getenv('BINANCE_API_KEY', ''),
                'api_secret': os.getenv('BINANCE_API_SECRET', ''),
                'enabled': bool(os.getenv('BINANCE_API_KEY', '').strip())
            },
            'Bybit': {
                'api_key': os.getenv('BYBIT_API_KEY', ''),
                'api_secret': os.getenv('BYBIT_API_SECRET', ''),
                'enabled': bool(os.getenv('BYBIT_API_KEY', '').strip())
            },
            'OKX': {
                'api_key': os.getenv('OKX_API_KEY', ''),
                'api_secret': os.getenv('OKX_API_SECRET', ''),
                'passphrase': os.getenv('OKX_PASSPHRASE', ''),
                'enabled': bool(os.getenv('OKX_API_KEY', '').strip())
            },
            'KuCoin': {
                'api_key': os.getenv('KUCOIN_API_KEY', ''),
                'api_secret': os.getenv('KUCOIN_API_SECRET', ''),
                'passphrase': os.getenv('KUCOIN_PASSPHRASE', ''),
                'enabled': bool(os.getenv('KUCOIN_API_KEY', '').strip())
            },
            'Gate.io': {
                'api_key': os.getenv('GATEIO_API_KEY', ''),
                'api_secret': os.getenv('GATEIO_API_SECRET', ''),
                'enabled': bool(os.getenv('GATEIO_API_KEY', '').strip())
            },
            'Bitget': {
                'api_key': os.getenv('BITGET_API_KEY', ''),
                'api_secret': os.getenv('BITGET_API_SECRET', ''),
                'passphrase': os.getenv('BITGET_PASSPHRASE', ''),
                'enabled': bool(os.getenv('BITGET_API_KEY', '').strip())
            },
            'MEXC': {
                'api_key': os.getenv('MEXC_API_KEY', ''),
                'api_secret': os.getenv('MEXC_API_SECRET', ''),
                'enabled': bool(os.getenv('MEXC_API_KEY', '').strip())
            },
            'HTX': {
                'api_key': os.getenv('HTX_API_KEY', ''),
                'api_secret': os.getenv('HTX_API_SECRET', ''),
                'enabled': bool(os.getenv('HTX_API_KEY', '').strip())
            }
        }
    
    def _check_trading_enabled(self) -> bool:
        """Check if any exchange has trading enabled"""
        # Check global trading enable flag
        global_enabled = os.getenv('ENABLE_CEX_TRADING', 'false').lower() == 'true'
        if not global_enabled:
            logger.warning("⚠️ CEX Trading globally disabled (ENABLE_CEX_TRADING=false)")
            return False
        
        enabled_exchanges = [ex for ex, config in self.api_keys.items() if config.get('enabled', False)]
        if enabled_exchanges:
            logger.info(f"📈 Trading enabled on: {', '.join(enabled_exchanges)}")
            return True
        else:
            logger.warning("⚠️ No CEX API keys configured - Trading disabled")
            # Debug info
            for ex, config in self.api_keys.items():
                if config.get('api_key'):
                    logger.info(f"🔑 {ex}: API key found ({config['api_key'][:10]}...)")
                else:
                    logger.debug(f"❌ {ex}: No API key")
            return False
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'FlashloanArbitrage/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _create_signature(self, exchange: str, method: str, path: str, params: Dict = None, body: str = '') -> Dict[str, str]:
        """Create API signature for exchange"""
        if not self.api_keys[exchange].get('enabled'):
            return {}
        
        api_key = self.api_keys[exchange]['api_key']
        api_secret = self.api_keys[exchange]['api_secret']
        timestamp = str(int(time.time() * 1000))
        
        headers = {'X-MBX-APIKEY': api_key} if exchange == 'Binance' else {}
        
        if exchange == 'Binance':
            # Binance signature
            query_string = '&'.join([f"{k}={v}" for k, v in (params or {}).items()])
            if body:
                query_string += body
            query_string += f"&timestamp={timestamp}"
            
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers.update({
                'X-MBX-APIKEY': api_key,
                'Content-Type': 'application/json'
            })
            
            return headers, f"{query_string}&signature={signature}"
        
        elif exchange == 'Bybit':
            # Bybit signature
            param_str = '&'.join([f"{k}={v}" for k, v in sorted((params or {}).items())])
            if body:
                param_str = body
            
            sign_str = f"{timestamp}{api_key}{param_str}"
            signature = hmac.new(
                api_secret.encode('utf-8'),
                sign_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers.update({
                'X-BAPI-API-KEY': api_key,
                'X-BAPI-SIGN': signature,
                'X-BAPI-TIMESTAMP': timestamp,
                'Content-Type': 'application/json'
            })
            
            return headers, param_str
        
        # Add other exchange signatures as needed
        return headers, ''
    
    async def get_balance(self, exchange: str, currency: str = 'USDT') -> Optional[ExchangeBalance]:
        """Get balance for specific currency on exchange"""
        if not self.api_keys[exchange].get('enabled'):
            logger.warning(f"❌ {exchange} API not configured")
            return None
        
        try:
            if exchange == 'Binance':
                return await self._get_binance_balance(currency)
            elif exchange == 'Bybit':
                return await self._get_bybit_balance(currency)
            # Add other exchanges...
            
        except Exception as e:
            logger.error(f"❌ Error getting {exchange} balance: {e}")
            return None
    
    async def _get_binance_balance(self, currency: str) -> Optional[ExchangeBalance]:
        """Get Binance account balance"""
        try:
            path = '/api/v3/account'
            headers, query = self._create_signature('Binance', 'GET', path)
            
            url = f"https://api.binance.com{path}?{query}"
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    for balance in data.get('balances', []):
                        if balance['asset'] == currency:
                            return ExchangeBalance(
                                exchange='Binance',
                                currency=currency,
                                available=float(balance['free']),
                                locked=float(balance['locked']),
                                total=float(balance['free']) + float(balance['locked'])
                            )
        except Exception as e:
            logger.error(f"❌ Binance balance error: {e}")
        return None
    
    async def _get_bybit_balance(self, currency: str) -> Optional[ExchangeBalance]:
        """Get Bybit account balance"""
        try:
            path = '/v5/account/wallet-balance'
            params = {'accountType': 'UNIFIED'}
            headers, _ = self._create_signature('Bybit', 'GET', path, params)
            
            url = f"https://api.bybit.com{path}"
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})
                    for account in result.get('list', []):
                        for coin in account.get('coin', []):
                            if coin['coin'] == currency:
                                return ExchangeBalance(
                                    exchange='Bybit',
                                    currency=currency,
                                    available=float(coin['availableToWithdraw']),
                                    locked=float(coin['locked']),
                                    total=float(coin['walletBalance'])
                                )
        except Exception as e:
            logger.error(f"❌ Bybit balance error: {e}")
        return None
    
    async def place_market_order(self, exchange: str, symbol: str, side: str, amount: float) -> TradeResult:
        """Place market order on exchange"""
        if not self.trading_enabled or not self.api_keys[exchange].get('enabled'):
            return TradeResult(
                success=False,
                order_id=None,
                exchange=exchange,
                symbol=symbol,
                side=side,
                amount=amount,
                price=0,
                executed_amount=0,
                executed_price=0,
                fee=0,
                timestamp=int(time.time()),
                error_message="Trading not enabled or API not configured"
            )
        
        # Validate trade amount
        base_currency = symbol.split('/')[0] if '/' in symbol else symbol[:3]
        if not self._validate_trade_amount(base_currency, amount):
            return TradeResult(
                success=False,
                order_id=None,
                exchange=exchange,
                symbol=symbol,
                side=side,
                amount=amount,
                price=0,
                executed_amount=0,
                executed_price=0,
                fee=0,
                timestamp=int(time.time()),
                error_message=f"Trade amount {amount} outside allowed limits"
            )
        
        try:
            if exchange == 'Binance':
                return await self._place_binance_order(symbol, side, amount)
            elif exchange == 'Bybit':
                return await self._place_bybit_order(symbol, side, amount)
            # Add other exchanges...
            
        except Exception as e:
            logger.error(f"❌ Error placing {exchange} order: {e}")
            return TradeResult(
                success=False,
                order_id=None,
                exchange=exchange,
                symbol=symbol,
                side=side,
                amount=amount,
                price=0,
                executed_amount=0,
                executed_price=0,
                fee=0,
                timestamp=int(time.time()),
                error_message=str(e)
            )
    
    def _validate_trade_amount(self, currency: str, amount: float) -> bool:
        """Validate trade amount is within limits"""
        max_amount = self.max_trade_amount.get(currency, 1000)  # Default 1000
        min_amount = self.min_trade_amount.get(currency, 0.001)  # Default 0.001
        
        return min_amount <= amount <= max_amount
    
    async def _place_binance_order(self, symbol: str, side: str, amount: float) -> TradeResult:
        """Place order on Binance"""
        try:
            path = '/api/v3/order'
            params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': str(amount)
            }
            
            headers, query = self._create_signature('Binance', 'POST', path, params)
            
            url = f"https://api.binance.com{path}"
            async with self.session.post(url, headers=headers, data=query) as response:
                data = await response.json()
                
                if response.status == 200:
                    return TradeResult(
                        success=True,
                        order_id=data['orderId'],
                        exchange='Binance',
                        symbol=symbol,
                        side=side,
                        amount=amount,
                        price=float(data.get('price', 0)),
                        executed_amount=float(data.get('executedQty', 0)),
                        executed_price=float(data.get('cummulativeQuoteQty', 0)) / max(float(data.get('executedQty', 1)), 1),
                        fee=0,  # Would need separate API call for fees
                        timestamp=int(time.time())
                    )
                else:
                    return TradeResult(
                        success=False,
                        order_id=None,
                        exchange='Binance',
                        symbol=symbol,
                        side=side,
                        amount=amount,
                        price=0,
                        executed_amount=0,
                        executed_price=0,
                        fee=0,
                        timestamp=int(time.time()),
                        error_message=data.get('msg', 'Unknown error')
                    )
        
        except Exception as e:
            raise e
    
    async def _place_bybit_order(self, symbol: str, side: str, amount: float) -> TradeResult:
        """Place order on Bybit"""
        try:
            path = '/v5/order/create'
            body = json.dumps({
                'category': 'spot',
                'symbol': symbol.replace('/', ''),
                'side': side.capitalize(),
                'orderType': 'Market',
                'qty': str(amount)
            })
            
            headers, _ = self._create_signature('Bybit', 'POST', path, body=body)
            
            url = f"https://api.bybit.com{path}"
            async with self.session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                
                if response.status == 200 and data.get('retCode') == 0:
                    result = data.get('result', {})
                    return TradeResult(
                        success=True,
                        order_id=result.get('orderId'),
                        exchange='Bybit',
                        symbol=symbol,
                        side=side,
                        amount=amount,
                        price=0,  # Market order, price determined at execution
                        executed_amount=0,  # Would need order status API
                        executed_price=0,
                        fee=0,
                        timestamp=int(time.time())
                    )
                else:
                    return TradeResult(
                        success=False,
                        order_id=None,
                        exchange='Bybit',
                        symbol=symbol,
                        side=side,
                        amount=amount,
                        price=0,
                        executed_amount=0,
                        executed_price=0,
                        fee=0,
                        timestamp=int(time.time()),
                        error_message=data.get('retMsg', 'Unknown error')
                    )
        
        except Exception as e:
            raise e
    
    async def execute_cex_arbitrage(self, buy_exchange: str, sell_exchange: str, symbol: str, amount: float) -> Tuple[TradeResult, TradeResult]:
        """Execute CEX-CEX arbitrage trade"""
        logger.info(f"🔄 Executing CEX arbitrage: {buy_exchange} → {sell_exchange} | {symbol} | {amount}")
        
        # Place buy order on buy exchange
        buy_result = await self.place_market_order(buy_exchange, symbol, 'buy', amount)
        
        if not buy_result.success:
            logger.error(f"❌ Buy order failed on {buy_exchange}: {buy_result.error_message}")
            return buy_result, None
        
        logger.info(f"✅ Buy order executed on {buy_exchange}: {buy_result.executed_amount} at {buy_result.executed_price}")
        
        # Place sell order on sell exchange
        sell_result = await self.place_market_order(sell_exchange, symbol, 'sell', buy_result.executed_amount)
        
        if not sell_result.success:
            logger.error(f"❌ Sell order failed on {sell_exchange}: {sell_result.error_message}")
            # TODO: Handle partial execution - might need to reverse buy order
        else:
            logger.info(f"✅ Sell order executed on {sell_exchange}: {sell_result.executed_amount} at {sell_result.executed_price}")
        
        return buy_result, sell_result
    
    async def check_arbitrage_feasibility(self, buy_exchange: str, sell_exchange: str, symbol: str, amount: float) -> bool:
        """Check if arbitrage is feasible (sufficient balances, etc.)"""
        try:
            # Check balance on buy exchange (need quote currency)
            quote_currency = symbol.split('/')[1] if '/' in symbol else 'USDT'
            buy_balance = await self.get_balance(buy_exchange, quote_currency)
            
            if not buy_balance or buy_balance.available < amount * 1.1:  # 10% buffer
                logger.warning(f"❌ Insufficient {quote_currency} balance on {buy_exchange}")
                return False
            
            # Check balance on sell exchange (need base currency)
            base_currency = symbol.split('/')[0] if '/' in symbol else symbol[:3]
            sell_balance = await self.get_balance(sell_exchange, base_currency)
            
            if not sell_balance or sell_balance.available < amount:
                logger.warning(f"❌ Insufficient {base_currency} balance on {sell_exchange}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking arbitrage feasibility: {e}")
            return False

# Global trading API instance
trading_api = CexTradingAPI()
