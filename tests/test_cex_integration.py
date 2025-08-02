"""
Test script for CEX integration functionality
"""

import asyncio
import logging
import sys
import time
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def test_cex_price_provider():
    """Test CEX price provider functionality"""
    logger.info("🧪 Testing CEX Price Provider...")
    
    try:
        from cex_price_provider import CexPriceProvider
        
        async with CexPriceProvider() as provider:
            # Test getting prices for BTC/USDT
            logger.info("📊 Testing BTC/USDT prices from all exchanges...")
            prices = await provider.get_all_prices('BTC', 'USDT')
            
            if prices:
                logger.info(f"✅ Retrieved {len(prices)} prices:")
                for price in prices:
                    logger.info(f"   {price.exchange}: ${price.price:,.2f} (bid: ${price.bid:,.2f}, ask: ${price.ask:,.2f})")
                
                # Test best prices
                best_prices = await provider.get_best_prices('BTC', 'USDT')
                if best_prices['bestBid'] and best_prices['bestAsk']:
                    logger.info(f"🎯 Best bid: {best_prices['bestBid'].exchange} - ${best_prices['bestBid'].bid:,.2f}")
                    logger.info(f"🎯 Best ask: {best_prices['bestAsk'].exchange} - ${best_prices['bestAsk'].ask:,.2f}")
                    logger.info(f"📊 Spread: {best_prices['spread']:.3f}%")
                
                # Test arbitrage opportunities
                logger.info("🔍 Testing CEX arbitrage opportunities...")
                opportunities = await provider.find_cex_arbitrage_opportunities('BTC', 'USDT')
                if opportunities:
                    logger.info(f"💰 Found {len(opportunities)} CEX arbitrage opportunities:")
                    for opp in opportunities[:3]:  # Show top 3
                        logger.info(f"   {opp['buy_exchange']} → {opp['sell_exchange']}: {opp['profit_percent']:.3f}% profit")
                else:
                    logger.info("ℹ️ No CEX arbitrage opportunities found")
                
                return True
            else:
                logger.error("❌ No prices retrieved from CEX exchanges")
                return False
                
    except Exception as e:
        logger.error(f"❌ CEX Price Provider test failed: {e}")
        return False

async def test_unified_scanner():
    """Test unified arbitrage scanner"""
    logger.info("🧪 Testing Unified Arbitrage Scanner...")
    
    try:
        from unified_arbitrage_scanner import UnifiedArbitrageScanner
        
        scanner = UnifiedArbitrageScanner()
        
        # Test CEX-DEX opportunities
        logger.info("🔍 Testing CEX-DEX arbitrage detection...")
        cex_dex_opps = await scanner.find_cex_dex_opportunities()
        logger.info(f"📊 Found {len(cex_dex_opps)} CEX-DEX opportunities")
        
        if cex_dex_opps:
            for opp in cex_dex_opps[:3]:  # Show top 3
                logger.info(f"   {opp.type}: {opp.token_in_symbol}/{opp.token_out_symbol} - {opp.profit_percentage:.3f}% profit")
                logger.info(f"     {opp.buy_venue} → {opp.sell_venue}")
        
        # Test CEX-CEX opportunities
        logger.info("🔍 Testing CEX-CEX arbitrage detection...")
        cex_cex_opps = await scanner.find_cex_cex_opportunities()
        logger.info(f"📊 Found {len(cex_cex_opps)} CEX-CEX opportunities")
        
        if cex_cex_opps:
            for opp in cex_cex_opps[:3]:  # Show top 3
                logger.info(f"   {opp.type}: {opp.token_in_symbol}/{opp.token_out_symbol} - {opp.profit_percentage:.3f}% profit")
                logger.info(f"     {opp.buy_venue} → {opp.sell_venue}")
        
        # Test full scan
        logger.info("🔍 Testing full unified scan...")
        all_opps = await scanner.find_all_opportunities()
        total_opps = sum(len(opps) for opps in all_opps.values())
        logger.info(f"📊 Total opportunities found: {total_opps}")
        
        # Get top opportunities
        top_opps = scanner.get_top_opportunities(all_opps, 5)
        if top_opps:
            logger.info("🏆 Top 5 opportunities:")
            for i, opp in enumerate(top_opps, 1):
                logger.info(f"   {i}. {opp.type}: {opp.token_in_symbol}/{opp.token_out_symbol} - {opp.profit_percentage:.3f}% profit")
                logger.info(f"      {opp.buy_venue} → {opp.sell_venue}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Unified Scanner test failed: {e}")
        return False

async def test_enhanced_main():
    """Test enhanced main functionality (brief test)"""
    logger.info("🧪 Testing Enhanced Main Scanner...")
    
    try:
        from main_enhanced import EnhancedArbitrageScanner
        
        # Initialize scanner (without running continuous loop)
        scanner = EnhancedArbitrageScanner()
        
        # Test opportunity processing with mock data
        from unified_arbitrage_scanner import UnifiedOpportunity
        
        mock_opportunity = UnifiedOpportunity(
            type='CEX_DEX',
            token_in_symbol='BTC',
            token_out_symbol='USDT',
            amount_in=int(1e18),
            profit_percentage=0.5,  # 0.5% profit
            buy_venue='Binance',
            sell_venue='PancakeSwap',
            buy_price=67000.0,
            sell_price=67335.0,
            estimated_gas=250000,
            timestamp=int(time.time())
        )
        
        # Test opportunity processing
        scanner.process_opportunities([mock_opportunity])
        
        logger.info("✅ Enhanced Main Scanner test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced Main Scanner test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    logger.info("🚀 Starting CEX Integration Tests...")
    logger.info("=" * 60)
    
    tests = [
        ("CEX Price Provider", test_cex_price_provider),
        ("Unified Scanner", test_unified_scanner),
        ("Enhanced Main", test_enhanced_main)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            start_time = time.time()
            result = await test_func()
            end_time = time.time()
            
            if result:
                logger.info(f"✅ {test_name} test PASSED ({end_time - start_time:.2f}s)")
            else:
                logger.error(f"❌ {test_name} test FAILED ({end_time - start_time:.2f}s)")
            
            results.append((test_name, result))
            
        except Exception as e:
            logger.error(f"❌ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 TEST SUMMARY:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! CEX integration is working correctly.")
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())