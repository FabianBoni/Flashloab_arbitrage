#!/usr/bin/env python3
"""
Improved CEX-DEX Arbitrage Strategy
Fokussiert auf machbare Arbitrage ohne CEX Withdrawals
"""

import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from unified_arbitrage_scanner import UnifiedArbitrageScanner
from cex_trading_api import trading_api

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FeasibleArbitrageOpportunity:
    """Machbare Arbitrage-Gelegenheit"""
    type: str  # 'CEX_ONLY', 'DEX_ONLY', 'CEX_DEX_FLASHLOAN'
    token_pair: str
    profit_percentage: float
    strategy: str
    execution_method: str
    capital_required: float
    risk_level: str
    details: Dict

class ImprovedArbitrageStrategy:
    """Verbesserte Arbitrage-Strategie ohne Withdrawal-Abhängigkeiten"""
    
    def __init__(self):
        self.scanner = UnifiedArbitrageScanner()
        
    async def find_feasible_opportunities(self) -> List[FeasibleArbitrageOpportunity]:
        """Finde alle machbaren Arbitrage-Möglichkeiten"""
        opportunities = []
        
        logger.info("🔍 Scanning for FEASIBLE arbitrage opportunities...")
        
        # 1. Same-Exchange Triangular Arbitrage
        triangular_opps = await self._find_triangular_arbitrage()
        opportunities.extend(triangular_opps)
        
        # 2. CEX-DEX with Flashloans (Most Promising)
        cex_dex_opps = await self._find_cex_dex_flashloan_opportunities()
        opportunities.extend(cex_dex_opps)
        
        # 3. Pure DEX Arbitrage (PancakeSwap routes)
        dex_opps = await self._find_pure_dex_arbitrage()
        opportunities.extend(dex_opps)
        
        # Sort by profit potential
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        return opportunities
    
    async def _find_triangular_arbitrage(self) -> List[FeasibleArbitrageOpportunity]:
        """Triangular Arbitrage auf derselben Exchange"""
        opportunities = []
        
        # Beispiel: USDT -> BTC -> ETH -> USDT auf Gate.io
        triangular_paths = [
            ('USDT', 'BTC', 'ETH', 'USDT'),
            ('USDT', 'ETH', 'BNB', 'USDT'),
            ('USDT', 'BTC', 'BNB', 'USDT'),
            ('USDT', 'PEPE', 'BTC', 'USDT'),  # Meme coin triangular
        ]
        
        for path in triangular_paths:
            try:
                # Mock calculation (in real implementation, get actual prices)
                mock_profit = 0.3  # 0.3% profit
                
                if mock_profit > 0.2:  # Profitable
                    opportunities.append(FeasibleArbitrageOpportunity(
                        type='CEX_ONLY',
                        token_pair=f"{path[0]}-{path[1]}-{path[2]}-{path[3]}",
                        profit_percentage=mock_profit,
                        strategy='Triangular Arbitrage',
                        execution_method='3 sequential trades on same exchange',
                        capital_required=100.0,  # $100 minimum
                        risk_level='LOW',
                        details={
                            'path': path,
                            'exchange': 'Gate.io',
                            'trades_needed': 3,
                            'no_withdrawals': True
                        }
                    ))
            except Exception as e:
                logger.debug(f"Error calculating triangular arbitrage: {e}")
        
        return opportunities
    
    async def _find_cex_dex_flashloan_opportunities(self) -> List[FeasibleArbitrageOpportunity]:
        """CEX-DEX Arbitrage mit Flashloans (Empfohlen)"""
        opportunities = []
        
        # High-potential volatile tokens
        volatile_tokens = ['PEPE', 'SHIB', 'FLOKI', 'GALA', 'NEAR', 'FTM']
        
        for token in volatile_tokens:
            try:
                # Mock: CEX price vs DEX price comparison
                # In real implementation, get actual prices from scanner
                cex_price = 1.0020  # Mock CEX price
                dex_price = 1.0000  # Mock DEX price
                
                profit_pct = ((cex_price - dex_price) / dex_price) * 100
                
                if profit_pct > 0.5:  # > 0.5% profit
                    opportunities.append(FeasibleArbitrageOpportunity(
                        type='CEX_DEX_FLASHLOAN',
                        token_pair=f"{token}/USDT",
                        profit_percentage=profit_pct,
                        strategy='CEX-DEX Flashloan',
                        execution_method='Flashloan -> Buy DEX -> Sell CEX -> Repay',
                        capital_required=0.0,  # No capital needed (flashloan)
                        risk_level='MEDIUM',
                        details={
                            'cex_price': cex_price,
                            'dex_price': dex_price,
                            'cex_exchange': 'Gate.io',
                            'dex': 'PancakeSwap',
                            'flashloan_needed': True,
                            'gas_cost_bnb': 0.002
                        }
                    ))
            except Exception as e:
                logger.debug(f"Error calculating CEX-DEX for {token}: {e}")
        
        return opportunities
    
    async def _find_pure_dex_arbitrage(self) -> List[FeasibleArbitrageOpportunity]:
        """Pure DEX Arbitrage (PancakeSwap routing)"""
        opportunities = []
        
        # Multi-path DEX arbitrage
        dex_paths = [
            ('WBNB', 'USDT', 'CAKE', 'WBNB'),  # BNB -> USDT -> CAKE -> BNB
            ('WBNB', 'ETH', 'USDT', 'WBNB'),   # BNB -> ETH -> USDT -> BNB
        ]
        
        for path in dex_paths:
            try:
                # Mock DEX arbitrage calculation
                mock_profit = 0.4  # 0.4% profit
                
                if mock_profit > 0.3:
                    opportunities.append(FeasibleArbitrageOpportunity(
                        type='DEX_ONLY',
                        token_pair=f"{path[0]}-{path[1]}-{path[2]}-{path[3]}",
                        profit_percentage=mock_profit,
                        strategy='Multi-DEX Routing',
                        execution_method='Flashloan -> Multi-hop swaps -> Repay',
                        capital_required=0.0,
                        risk_level='MEDIUM',
                        details={
                            'path': path,
                            'dexes': ['PancakeSwap', 'Biswap'],
                            'flashloan_needed': True,
                            'slippage_risk': 'MEDIUM'
                        }
                    ))
            except Exception as e:
                logger.debug(f"Error calculating DEX arbitrage: {e}")
        
        return opportunities
    
    def print_opportunity_report(self, opportunities: List[FeasibleArbitrageOpportunity]):
        """Drucke detaillierten Opportunity Report"""
        
        logger.info("📊 FEASIBLE ARBITRAGE OPPORTUNITIES REPORT")
        logger.info("=" * 60)
        
        if not opportunities:
            logger.info("❌ No profitable opportunities found at this time")
            return
        
        # Group by type
        by_type = {}
        for opp in opportunities:
            if opp.type not in by_type:
                by_type[opp.type] = []
            by_type[opp.type].append(opp)
        
        for opp_type, opps in by_type.items():
            logger.info(f"\n🎯 {opp_type} OPPORTUNITIES ({len(opps)} found):")
            logger.info("-" * 50)
            
            for i, opp in enumerate(opps[:3], 1):  # Top 3
                logger.info(f"#{i} {opp.token_pair}")
                logger.info(f"   💰 Profit: {opp.profit_percentage:.3f}%")
                logger.info(f"   🔧 Strategy: {opp.strategy}")
                logger.info(f"   ⚡ Method: {opp.execution_method}")
                logger.info(f"   💵 Capital: ${opp.capital_required:.0f}")
                logger.info(f"   ⚠️ Risk: {opp.risk_level}")
                
                if opp.details:
                    key_details = []
                    if 'no_withdrawals' in opp.details:
                        key_details.append("✅ No withdrawals needed")
                    if 'flashloan_needed' in opp.details:
                        key_details.append("🏦 Uses flashloan")
                    if 'exchange' in opp.details:
                        key_details.append(f"📊 {opp.details['exchange']}")
                    
                    if key_details:
                        logger.info(f"   📝 {' | '.join(key_details)}")
                
                logger.info("")
        
        # Recommendations
        logger.info("💡 RECOMMENDATIONS:")
        best_opp = opportunities[0] if opportunities else None
        
        if best_opp:
            logger.info(f"🏆 Best opportunity: {best_opp.token_pair} ({best_opp.profit_percentage:.3f}%)")
            
            if best_opp.type == 'CEX_DEX_FLASHLOAN':
                logger.info("✅ RECOMMENDED: CEX-DEX with flashloan")
                logger.info("   - No CEX withdrawals needed")
                logger.info("   - Uses your existing BSC wallet")
                logger.info("   - Automatic execution possible")
            elif best_opp.type == 'CEX_ONLY':
                logger.info("✅ RECOMMENDED: Same-exchange triangular")
                logger.info("   - Need to deposit USDT to exchange manually")
                logger.info("   - No cross-exchange transfers")
                logger.info("   - Lower risk")

async def main():
    """Hauptprogramm"""
    strategy = ImprovedArbitrageStrategy()
    
    logger.info("🚀 IMPROVED ARBITRAGE STRATEGY ANALYSIS")
    logger.info("Focusing on opportunities WITHOUT withdrawal dependencies")
    logger.info("")
    
    opportunities = await strategy.find_feasible_opportunities()
    strategy.print_opportunity_report(opportunities)

if __name__ == "__main__":
    asyncio.run(main())
