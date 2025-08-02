"""
Unified Arbitrage Scanner - CEX + DEX Integration
Combines centralized exchange prices with DEX prices for comprehensive arbitrage opportunities
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass

from cex_price_provider import CexPriceProvider, CexPrice, CexDexOpportunity, get_cex_symbol, get_dex_address
from cex_trading_api import CexTradingAPI, TradeResult

logger = logging.getLogger(__name__)

@dataclass
class UnifiedOpportunity:
    """Unified arbitrage opportunity (CEX-DEX or DEX-DEX)"""
    type: str  # 'CEX_DEX', 'DEX_CEX', 'DEX_DEX', 'CEX_CEX'
    token_in_symbol: str
    token_out_symbol: str
    amount_in: int
    profit_percentage: float
    buy_venue: str  # Exchange or DEX name
    sell_venue: str  # Exchange or DEX name
    buy_price: float
    sell_price: float
    estimated_gas: int
    timestamp: int

class UnifiedArbitrageScanner:
    """Unified scanner for both CEX and DEX arbitrage opportunities"""
    
    def __init__(self, dex_scanner=None):
        self.cex_provider = CexPriceProvider()
        self.trading_api = CexTradingAPI()
        self.dex_scanner = dex_scanner  # Reference to existing DEX scanner
        self.last_scan_time = 0
        self.scan_interval = 30  # 30 seconds between scans
        
        # Track DEX prices cache to avoid redundant calls
        self.dex_price_cache = {}
        self.cache_expiry = 10  # 10 seconds cache
        
        # Trading configuration
        self.auto_execute_cex = True  # Enable automatic CEX-CEX trading
        self.auto_execute_cex_dex = False  # CEX-DEX requires manual approval for now
        
        logger.info("🔄 Unified CEX-DEX arbitrage scanner initialized")
    
    async def get_dex_price(self, token_in_address: str, token_out_address: str, amount_in: int) -> Optional[float]:
        """Get DEX price with caching (simplified interface to existing DEX scanner)"""
        cache_key = f"{token_in_address}-{token_out_address}-{amount_in}"
        current_time = time.time()
        
        # Check cache first
        if cache_key in self.dex_price_cache:
            cached_data = self.dex_price_cache[cache_key]
            if current_time - cached_data['timestamp'] < self.cache_expiry:
                return cached_data['price']
        
        # If we have a DEX scanner reference, use it
        if self.dex_scanner:
            try:
                # Use the existing DEX scanner to get real prices
                price_data = await self.dex_scanner.get_quote(token_in_address, token_out_address, amount_in)
                if price_data and price_data.get('amount_out', 0) > 0:
                    # Convert to price per token
                    amount_out = price_data['amount_out']
                    price = float(amount_out) / float(amount_in)
                    
                    # Cache the result
                    self.dex_price_cache[cache_key] = {
                        'price': price,
                        'timestamp': current_time
                    }
                    
                    return price
            except Exception as e:
                logger.debug(f"Error getting real DEX price: {e}")
        
        # Fallback: Return None instead of mock data to prevent false opportunities
        return None
    
    async def find_cex_dex_opportunities(self) -> List[UnifiedOpportunity]:
        """Find arbitrage opportunities between CEX and DEX"""
        opportunities = []
        
        logger.info("🔍 Scanning for CEX-DEX arbitrage opportunities...")
        
        async with self.cex_provider:
            # Get supported trading pairs
            supported_pairs = self.cex_provider.get_supported_pairs()
            
            for base_token, quote_token in supported_pairs[:10]:  # Limit to top 10 pairs
                try:
                    # Get DEX addresses for these tokens
                    base_dex_address = get_dex_address(base_token)
                    quote_dex_address = get_dex_address(quote_token)
                    
                    if not base_dex_address or not quote_dex_address:
                        continue
                    
                    logger.info(f"🔍 Checking {base_token}/{quote_token}")
                    
                    # Get CEX prices
                    cex_prices = await self.cex_provider.get_all_prices(base_token, quote_token)
                    if not cex_prices:
                        continue
                    
                    # Get best CEX bid and ask
                    best_cex_bid = max(cex_prices, key=lambda x: x.bid)
                    best_cex_ask = min(cex_prices, key=lambda x: x.ask)
                    
                    # Get DEX price (base -> quote)
                    amount_in = int(1e18)  # 1 token with 18 decimals
                    dex_price = await self.get_dex_price(base_dex_address, quote_dex_address, amount_in)
                    
                    if dex_price is None:
                        continue
                    
                    # Calculate arbitrage opportunities
                    
                    # Direction 1: Buy on CEX, sell on DEX
                    if dex_price > best_cex_ask.ask:
                        profit_percent = ((dex_price - best_cex_ask.ask) / best_cex_ask.ask) * 100
                        
                        # Account for fees (flashloan, gas, CEX withdrawal, DEX fees)
                        total_fees_percent = 0.8  # 0.8% total fees
                        net_profit = profit_percent - total_fees_percent
                        
                        if net_profit > 0.2:  # Minimum 0.2% net profit
                            opportunities.append(UnifiedOpportunity(
                                type='CEX_DEX',
                                token_in_symbol=base_token,
                                token_out_symbol=quote_token,
                                amount_in=amount_in,
                                profit_percentage=net_profit,
                                buy_venue=best_cex_ask.exchange,
                                sell_venue='DEX',
                                buy_price=best_cex_ask.ask,
                                sell_price=dex_price,
                                estimated_gas=250000,
                                timestamp=int(time.time())
                            ))
                            
                            logger.info(f"✅ CEX→DEX: {base_token}/{quote_token} {net_profit:.3f}% profit")
                    
                    # Direction 2: Buy on DEX, sell on CEX
                    if best_cex_bid.bid > dex_price:
                        profit_percent = ((best_cex_bid.bid - dex_price) / dex_price) * 100
                        
                        # Account for fees
                        total_fees_percent = 0.8  # 0.8% total fees
                        net_profit = profit_percent - total_fees_percent
                        
                        if net_profit > 0.2:  # Minimum 0.2% net profit
                            opportunities.append(UnifiedOpportunity(
                                type='DEX_CEX',
                                token_in_symbol=base_token,
                                token_out_symbol=quote_token,
                                amount_in=amount_in,
                                profit_percentage=net_profit,
                                buy_venue='DEX',
                                sell_venue=best_cex_bid.exchange,
                                buy_price=dex_price,
                                sell_price=best_cex_bid.bid,
                                estimated_gas=250000,
                                timestamp=int(time.time())
                            ))
                            
                            logger.info(f"✅ DEX→CEX: {base_token}/{quote_token} {net_profit:.3f}% profit")
                
                except Exception as e:
                    logger.debug(f"Error scanning {base_token}/{quote_token}: {e}")
                    continue
        
        return opportunities
    
    async def find_cex_cex_opportunities(self) -> List[UnifiedOpportunity]:
        """Find arbitrage opportunities between different CEX exchanges"""
        opportunities = []
        
        logger.info("🔍 Scanning for CEX-CEX arbitrage opportunities...")
        
        async with self.cex_provider:
            supported_pairs = self.cex_provider.get_supported_pairs()
            
            for base_token, quote_token in supported_pairs[:5]:  # Limit to top 5 pairs
                try:
                    logger.info(f"🔍 Checking CEX arbitrage for {base_token}/{quote_token}")
                    
                    # Get prices from all exchanges
                    cex_prices = await self.cex_provider.get_all_prices(base_token, quote_token)
                    
                    if len(cex_prices) < 2:
                        continue
                    
                    # Find arbitrage opportunities between exchanges
                    for i in range(len(cex_prices)):
                        for j in range(i + 1, len(cex_prices)):
                            price_a = cex_prices[i]
                            price_b = cex_prices[j]
                            
                            # Direction 1: Buy on A, sell on B
                            if price_b.bid > price_a.ask:
                                profit_percent = ((price_b.bid - price_a.ask) / price_a.ask) * 100
                                
                                # Account for CEX fees (trading + withdrawal)
                                total_fees_percent = 0.5  # 0.5% total CEX fees
                                net_profit = profit_percent - total_fees_percent
                                
                                if net_profit > 0.3:  # Minimum 0.3% net profit for CEX arbitrage
                                    opportunities.append(UnifiedOpportunity(
                                        type='CEX_CEX',
                                        token_in_symbol=base_token,
                                        token_out_symbol=quote_token,
                                        amount_in=int(1e18),
                                        profit_percentage=net_profit,
                                        buy_venue=price_a.exchange,
                                        sell_venue=price_b.exchange,
                                        buy_price=price_a.ask,
                                        sell_price=price_b.bid,
                                        estimated_gas=0,
                                        timestamp=int(time.time())
                                    ))
                                    
                                    logger.info(f"✅ CEX-CEX: {base_token}/{quote_token} {net_profit:.3f}% profit ({price_a.exchange}→{price_b.exchange})")
                            
                            # Direction 2: Buy on B, sell on A
                            if price_a.bid > price_b.ask:
                                profit_percent = ((price_a.bid - price_b.ask) / price_b.ask) * 100
                                
                                # Account for CEX fees
                                total_fees_percent = 0.5  # 0.5% total CEX fees
                                net_profit = profit_percent - total_fees_percent
                                
                                if net_profit > 0.3:  # Minimum 0.3% net profit
                                    opportunities.append(UnifiedOpportunity(
                                        type='CEX_CEX',
                                        token_in_symbol=base_token,
                                        token_out_symbol=quote_token,
                                        amount_in=int(1e18),
                                        profit_percentage=net_profit,
                                        buy_venue=price_b.exchange,
                                        sell_venue=price_a.exchange,
                                        buy_price=price_b.ask,
                                        sell_price=price_a.bid,
                                        estimated_gas=0,
                                        timestamp=int(time.time())
                                    ))
                                    
                                    logger.info(f"✅ CEX-CEX: {base_token}/{quote_token} {net_profit:.3f}% profit ({price_b.exchange}→{price_a.exchange})")
                
                except Exception as e:
                    logger.debug(f"Error scanning CEX arbitrage for {base_token}/{quote_token}: {e}")
                    continue
        
        return opportunities
    
    async def execute_cex_arbitrage(self, opportunity: UnifiedOpportunity) -> bool:
        """Execute CEX-CEX arbitrage automatically"""
        if not self.auto_execute_cex or opportunity.type != 'CEX_CEX':
            logger.info(f"⚠️ Auto-execution disabled or wrong opportunity type: {opportunity.type}")
            return False
        
        if not self.trading_api.trading_enabled:
            logger.warning("⚠️ Trading API not enabled - skipping execution")
            return False
        
        try:
            # Convert amount from wei to normal units
            trade_amount = float(opportunity.amount_in) / 1e18
            
            # Validate trade amount
            if not self.trading_api._validate_trade_amount(opportunity.token_in_symbol, trade_amount):
                logger.warning(f"⚠️ Trade amount {trade_amount} outside limits")
                return False
            
            # Check if arbitrage is still feasible
            symbol = f"{opportunity.token_in_symbol}/{opportunity.token_out_symbol}"
            feasible = await self.trading_api.check_arbitrage_feasibility(
                opportunity.buy_venue, opportunity.sell_venue, symbol, trade_amount
            )
            
            if not feasible:
                logger.warning(f"⚠️ Arbitrage no longer feasible: {opportunity.buy_venue} → {opportunity.sell_venue}")
                return False
            
            logger.info(f"🔄 Executing CEX arbitrage: {opportunity.buy_venue} → {opportunity.sell_venue} | {symbol} | {trade_amount:.6f}")
            
            # Execute the arbitrage
            async with self.trading_api:
                buy_result, sell_result = await self.trading_api.execute_cex_arbitrage(
                    opportunity.buy_venue,
                    opportunity.sell_venue,
                    symbol,
                    trade_amount
                )
            
            if buy_result.success and sell_result and sell_result.success:
                profit = (sell_result.executed_price * sell_result.executed_amount) - (buy_result.executed_price * buy_result.executed_amount)
                logger.info(f"✅ CEX arbitrage executed successfully! Profit: ${profit:.4f}")
                return True
            else:
                logger.error("❌ CEX arbitrage execution failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error executing CEX arbitrage: {e}")
            return False
    
    async def find_all_opportunities(self) -> Dict[str, List[UnifiedOpportunity]]:
        """Find all types of arbitrage opportunities"""
        logger.info("🚀 Starting unified arbitrage scan...")
        start_time = time.time()
        
        # Run all scans concurrently
        tasks = [
            self.find_cex_dex_opportunities(),
            self.find_cex_cex_opportunities()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        cex_dex_opportunities = results[0] if not isinstance(results[0], Exception) else []
        cex_cex_opportunities = results[1] if not isinstance(results[1], Exception) else []
        
        # Get DEX-DEX opportunities from existing scanner if available
        dex_dex_opportunities = []
        if self.dex_scanner:
            # This would integrate with existing DEX scanning logic
            # For now, we'll leave it empty
            pass
        
        all_opportunities = {
            'CEX_DEX': cex_dex_opportunities,
            'CEX_CEX': cex_cex_opportunities,
            'DEX_DEX': dex_dex_opportunities
        }
        
        scan_time = time.time() - start_time
        total_opportunities = sum(len(opps) for opps in all_opportunities.values())
        
        logger.info(f"📊 Scan completed in {scan_time:.2f}s:")
        logger.info(f"   CEX-DEX: {len(cex_dex_opportunities)} opportunities")
        logger.info(f"   CEX-CEX: {len(cex_cex_opportunities)} opportunities")
        logger.info(f"   DEX-DEX: {len(dex_dex_opportunities)} opportunities")
        logger.info(f"   Total: {total_opportunities} opportunities")
        
        return all_opportunities
    
    def get_top_opportunities(self, all_opportunities: Dict[str, List[UnifiedOpportunity]], limit: int = 10) -> List[UnifiedOpportunity]:
        """Get top opportunities sorted by profit percentage"""
        all_opps = []
        for opp_type, opportunities in all_opportunities.items():
            all_opps.extend(opportunities)
        
        # Sort by profit percentage (descending)
        all_opps.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        return all_opps[:limit]
    
    async def start_continuous_monitoring(self, callback=None, interval: int = 30):
        """Start continuous monitoring for arbitrage opportunities"""
        logger.info(f"🔄 Starting continuous unified arbitrage monitoring (every {interval}s)")
        
        while True:
            try:
                current_time = time.time()
                
                # Only scan if enough time has passed
                if current_time - self.last_scan_time >= interval:
                    opportunities = await self.find_all_opportunities()
                    
                    if callback:
                        top_opportunities = self.get_top_opportunities(opportunities)
                        if top_opportunities:
                            callback(top_opportunities)
                    
                    self.last_scan_time = current_time
                
                # Sleep for a short time to avoid busy waiting
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"💥 Error in monitoring: {e}")
                await asyncio.sleep(10)  # Wait before retrying

# Integration function for existing main.py
def create_unified_scanner(dex_scanner=None):
    """Create a unified scanner instance"""
    return UnifiedArbitrageScanner(dex_scanner)

async def test_unified_scanner():
    """Test function for the unified scanner"""
    scanner = UnifiedArbitrageScanner()
    
    # Test CEX-DEX opportunities
    cex_dex_opps = await scanner.find_cex_dex_opportunities()
    print(f"Found {len(cex_dex_opps)} CEX-DEX opportunities")
    
    # Test CEX-CEX opportunities
    cex_cex_opps = await scanner.find_cex_cex_opportunities()
    print(f"Found {len(cex_cex_opps)} CEX-CEX opportunities")
    
    # Test full scan
    all_opps = await scanner.find_all_opportunities()
    top_opps = scanner.get_top_opportunities(all_opps, 5)
    
    print(f"\nTop 5 opportunities:")
    for i, opp in enumerate(top_opps, 1):
        print(f"{i}. {opp.type}: {opp.token_in_symbol}/{opp.token_out_symbol} - {opp.profit_percentage:.3f}% profit")
        print(f"   {opp.buy_venue} → {opp.sell_venue}")

if __name__ == "__main__":
    # Test the unified scanner
    asyncio.run(test_unified_scanner())