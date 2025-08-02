"""
Quick Start Guide for Enhanced CEX+DEX Arbitrage Scanner
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_cex_price_fetching():
    """Demonstrate CEX price fetching"""
    logger.info("🔍 Demo: CEX Price Fetching")
    
    from cex_price_provider import CexPriceProvider
    
    async with CexPriceProvider() as provider:
        # Get BTC/USDT prices from all exchanges
        prices = await provider.get_all_prices('BTC', 'USDT')
        
        if prices:
            logger.info(f"📊 Retrieved prices from {len(prices)} exchanges:")
            for price in prices[:3]:  # Show first 3
                logger.info(f"   {price.exchange}: ${price.price:,.2f}")
        else:
            logger.info("ℹ️ No prices available (likely due to API restrictions)")

async def demo_unified_scanning():
    """Demonstrate unified arbitrage scanning"""
    logger.info("🔍 Demo: Unified Arbitrage Scanning")
    
    from unified_arbitrage_scanner import UnifiedArbitrageScanner
    
    scanner = UnifiedArbitrageScanner()
    
    # Find all types of opportunities
    opportunities = await scanner.find_all_opportunities()
    
    total_opps = sum(len(opps) for opps in opportunities.values())
    logger.info(f"📊 Found {total_opps} total opportunities:")
    logger.info(f"   CEX-DEX: {len(opportunities.get('CEX_DEX', []))}")
    logger.info(f"   CEX-CEX: {len(opportunities.get('CEX_CEX', []))}")
    logger.info(f"   DEX-DEX: {len(opportunities.get('DEX_DEX', []))}")

def demo_enhanced_configuration():
    """Show how to configure the enhanced scanner"""
    logger.info("🔧 Demo: Enhanced Configuration")
    
    logger.info("📝 Environment Variables Needed:")
    logger.info("   BSC_RPC_URL=https://bsc-dataseed1.binance.org/")
    logger.info("   PRIVATE_KEY=your_private_key_here")
    logger.info("   TELEGRAM_BOT_TOKEN=your_telegram_bot_token")
    logger.info("   TELEGRAM_CHAT_ID=your_chat_id")
    logger.info("   SCAN_INTERVAL=30  # seconds")
    
    logger.info("\n💰 Profit Thresholds:")
    logger.info("   CEX-DEX: 0.3% minimum")
    logger.info("   CEX-CEX: 0.5% minimum")
    logger.info("   DEX-DEX: 0.5% minimum")
    logger.info("   Immediate Execution: 0.8%")

async def main():
    """Run all demos"""
    logger.info("🚀 Enhanced BSC Arbitrage Scanner - Quick Start Demo")
    logger.info("=" * 60)
    
    # Demo 1: CEX Price Fetching
    try:
        await demo_cex_price_fetching()
    except Exception as e:
        logger.error(f"CEX demo failed: {e}")
    
    logger.info("\n" + "-" * 40 + "\n")
    
    # Demo 2: Unified Scanning
    try:
        await demo_unified_scanning()
    except Exception as e:
        logger.error(f"Unified scanning demo failed: {e}")
    
    logger.info("\n" + "-" * 40 + "\n")
    
    # Demo 3: Configuration
    demo_enhanced_configuration()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Quick Start Commands:")
    logger.info("   python main_enhanced.py          # Run enhanced scanner")
    logger.info("   python main.py                   # Run original DEX scanner")
    logger.info("   python tests/test_cex_integration.py  # Test CEX integration")
    
    logger.info("\n📚 Documentation:")
    logger.info("   README_ENHANCED.md              # Enhanced documentation")
    logger.info("   README.md                       # Original documentation")

if __name__ == "__main__":
    asyncio.run(main())