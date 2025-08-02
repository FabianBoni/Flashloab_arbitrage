#!/usr/bin/env python3
"""
Praktische CEX-DEX Arbitrage Implementation
Nutzt vorhandene BSC Wallet und Flashloan Contracts
"""

import asyncio
import logging
from typing import Dict, Optional
from web3 import Web3
from unified_arbitrage_scanner import UnifiedArbitrageScanner
from cex_trading_api import trading_api
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PracticalCEXDEXArbitrage:
    """Praktische CEX-DEX Arbitrage ohne Withdrawal-Abhängigkeiten"""
    
    def __init__(self):
        self.scanner = UnifiedArbitrageScanner()
        
        # BSC Configuration (using your existing setup)
        self.w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
        self.chain_id = 56
        
        # Your wallet address (replace with actual)
        self.wallet_address = "0x742d35Cc6634C0532925a3b8D82F"  # Placeholder
        
        # Priority token pairs for CEX-DEX arbitrage
        self.priority_tokens = {
            'PEPE': {
                'address': '0x25d887Ce7a35172C62FeBFD67a1856F20FaEbB00',
                'decimals': 18,
                'min_profit_pct': 0.5
            },
            'SHIB': {
                'address': '0x2859e4544C4bB03966803b044A93563Bd2D0DD4D',
                'decimals': 18,
                'min_profit_pct': 0.4
            },
            'FLOKI': {
                'address': '0xfb5B838b6cfEEdC2873aB27866079AC55363D37E',
                'decimals': 9,
                'min_profit_pct': 0.6
            }
        }
        
    async def scan_cex_dex_opportunities(self) -> Dict:
        """Scanne für praktische CEX-DEX Möglichkeiten"""
        
        logger.info("🔍 Scanning for practical CEX-DEX arbitrage opportunities...")
        
        opportunities = {
            'profitable': [],
            'monitoring': [],
            'rejected': []
        }
        
        for token_symbol, token_info in self.priority_tokens.items():
            try:
                # 1. Get CEX prices from multiple exchanges
                cex_prices = await self._get_cex_prices(token_symbol)
                
                # 2. Get DEX price from PancakeSwap
                dex_price = await self._get_dex_price(token_symbol, token_info['address'])
                
                # 3. Calculate arbitrage potential
                best_opportunity = self._calculate_best_arbitrage(
                    token_symbol, cex_prices, dex_price, token_info
                )
                
                if best_opportunity:
                    if best_opportunity['profit_pct'] > token_info['min_profit_pct']:
                        opportunities['profitable'].append(best_opportunity)
                        logger.info(f"✅ PROFITABLE: {token_symbol} - {best_opportunity['profit_pct']:.3f}%")
                    else:
                        opportunities['monitoring'].append(best_opportunity)
                        logger.debug(f"👀 MONITORING: {token_symbol} - {best_opportunity['profit_pct']:.3f}%")
                else:
                    opportunities['rejected'].append({
                        'token': token_symbol,
                        'reason': 'No profitable direction found'
                    })
                    
            except Exception as e:
                logger.error(f"Error scanning {token_symbol}: {e}")
                opportunities['rejected'].append({
                    'token': token_symbol,
                    'reason': f'Error: {str(e)}'
                })
        
        return opportunities
    
    async def _get_cex_prices(self, token_symbol: str) -> Dict:
        """Hole CEX Preise von verfügbaren Exchanges"""
        prices = {}
        
        try:
            # Gate.io (meist günstig)
            gate_ticker = await trading_api.get_ticker('gate', f"{token_symbol}_USDT")
            if gate_ticker and 'bid' in gate_ticker:
                prices['gate'] = {
                    'bid': float(gate_ticker['bid']),
                    'ask': float(gate_ticker['ask']),
                    'mid': (float(gate_ticker['bid']) + float(gate_ticker['ask'])) / 2
                }
            
            # Binance (meist teuer)
            binance_ticker = await trading_api.get_ticker('binance', f"{token_symbol}USDT")
            if binance_ticker and 'bidPrice' in binance_ticker:
                prices['binance'] = {
                    'bid': float(binance_ticker['bidPrice']),
                    'ask': float(binance_ticker['askPrice']),
                    'mid': (float(binance_ticker['bidPrice']) + float(binance_ticker['askPrice'])) / 2
                }
            
            # Bybit
            bybit_ticker = await trading_api.get_ticker('bybit', f"{token_symbol}USDT")
            if bybit_ticker and 'bid1Price' in bybit_ticker:
                prices['bybit'] = {
                    'bid': float(bybit_ticker['bid1Price']),
                    'ask': float(bybit_ticker['ask1Price']),
                    'mid': (float(bybit_ticker['bid1Price']) + float(bybit_ticker['ask1Price'])) / 2
                }
                
        except Exception as e:
            logger.debug(f"Error getting CEX prices for {token_symbol}: {e}")
        
        return prices
    
    async def _get_dex_price(self, token_symbol: str, token_address: str) -> Optional[float]:
        """Hole DEX Preis von PancakeSwap"""
        try:
            # Mock implementation - replace with actual PancakeSwap price fetch
            # Using your existing scanner logic
            
            # Simulate price fetch from PancakeSwap
            mock_dex_price = 1.000  # Placeholder
            
            logger.debug(f"DEX price for {token_symbol}: ${mock_dex_price}")
            return mock_dex_price
            
        except Exception as e:
            logger.error(f"Error getting DEX price for {token_symbol}: {e}")
            return None
    
    def _calculate_best_arbitrage(self, token_symbol: str, cex_prices: Dict, 
                                dex_price: Optional[float], token_info: Dict) -> Optional[Dict]:
        """Berechne beste Arbitrage-Möglichkeit"""
        
        if not dex_price or not cex_prices:
            return None
        
        best_opportunity = None
        max_profit = 0
        
        for exchange, prices in cex_prices.items():
            # Strategy 1: Buy DEX, Sell CEX
            if prices['bid'] > dex_price:
                profit_pct = ((prices['bid'] - dex_price) / dex_price) * 100
                if profit_pct > max_profit:
                    max_profit = profit_pct
                    best_opportunity = {
                        'token': token_symbol,
                        'strategy': 'BUY_DEX_SELL_CEX',
                        'exchange': exchange,
                        'dex_price': dex_price,
                        'cex_price': prices['bid'],
                        'profit_pct': profit_pct,
                        'execution': f'Flashloan -> Buy {token_symbol} on PancakeSwap -> Sell on {exchange}',
                        'capital_needed': 0,  # Flashloan
                        'estimated_gas': 0.003  # BNB
                    }
            
            # Strategy 2: Buy CEX, Sell DEX (requires manual CEX deposit)
            if dex_price > prices['ask']:
                profit_pct = ((dex_price - prices['ask']) / prices['ask']) * 100
                if profit_pct > max_profit:
                    max_profit = profit_pct
                    best_opportunity = {
                        'token': token_symbol,
                        'strategy': 'BUY_CEX_SELL_DEX',
                        'exchange': exchange,
                        'cex_price': prices['ask'],
                        'dex_price': dex_price,
                        'profit_pct': profit_pct,
                        'execution': f'Manual: Buy {token_symbol} on {exchange} -> Transfer to DEX wallet -> Sell on PancakeSwap',
                        'capital_needed': 100,  # Manual deposit needed
                        'warning': 'Requires manual CEX deposit and withdrawal'
                    }
        
        return best_opportunity
    
    async def execute_flashloan_arbitrage(self, opportunity: Dict) -> bool:
        """Führe Flashloan Arbitrage aus (nur für BUY_DEX_SELL_CEX)"""
        
        if opportunity['strategy'] != 'BUY_DEX_SELL_CEX':
            logger.warning("Can only auto-execute BUY_DEX_SELL_CEX strategy")
            return False
        
        logger.info(f"🚀 Executing flashloan arbitrage for {opportunity['token']}")
        logger.info(f"   Strategy: {opportunity['execution']}")
        logger.info(f"   Expected profit: {opportunity['profit_pct']:.3f}%")
        
        try:
            # 1. Check if you have CEX account balance for selling
            exchange = opportunity['exchange']
            
            # This would normally check actual balance
            # balance = await trading_api.get_balance(exchange, opportunity['token'])
            
            # 2. Execute flashloan transaction (mock)
            logger.info("⚡ Initiating flashloan...")
            
            # Your existing flashloan contract logic would go here
            # This is a simplified placeholder
            
            logger.info("✅ Flashloan arbitrage simulation complete")
            return True
            
        except Exception as e:
            logger.error(f"Error executing flashloan arbitrage: {e}")
            return False
    
    def print_detailed_report(self, opportunities: Dict):
        """Drucke detaillierten Report"""
        
        logger.info("📊 PRACTICAL CEX-DEX ARBITRAGE REPORT")
        logger.info("=" * 60)
        
        if opportunities['profitable']:
            logger.info(f"💰 PROFITABLE OPPORTUNITIES ({len(opportunities['profitable'])})")
            logger.info("-" * 40)
            
            for i, opp in enumerate(opportunities['profitable'], 1):
                logger.info(f"#{i} {opp['token']} - {opp['profit_pct']:.3f}% profit")
                logger.info(f"    Exchange: {opp['exchange']}")
                logger.info(f"    Strategy: {opp['strategy']}")
                logger.info(f"    DEX Price: ${opp['dex_price']:.6f}")
                logger.info(f"    CEX Price: ${opp['cex_price']:.6f}")
                logger.info(f"    Capital: ${opp['capital_needed']}")
                
                if opp['strategy'] == 'BUY_DEX_SELL_CEX':
                    logger.info(f"    ✅ AUTO-EXECUTABLE with flashloan")
                else:
                    logger.info(f"    ⚠️ Requires manual steps")
                logger.info("")
        
        if opportunities['monitoring']:
            logger.info(f"👀 MONITORING ({len(opportunities['monitoring'])} below threshold)")
            for opp in opportunities['monitoring'][:3]:
                logger.info(f"    {opp['token']}: {opp['profit_pct']:.3f}%")
        
        if opportunities['rejected']:
            logger.info(f"❌ REJECTED ({len(opportunities['rejected'])})")
            for rej in opportunities['rejected'][:3]:
                logger.info(f"    {rej['token']}: {rej['reason']}")
        
        logger.info("\n💡 NEXT STEPS:")
        if opportunities['profitable']:
            auto_executable = [o for o in opportunities['profitable'] if o['strategy'] == 'BUY_DEX_SELL_CEX']
            if auto_executable:
                best = auto_executable[0]
                logger.info(f"🎯 Execute: {best['token']} flashloan arbitrage ({best['profit_pct']:.3f}%)")
                logger.info("   Command: python practical_cex_dex_arbitrage.py --execute")
            else:
                logger.info("📝 Manual arbitrage opportunities available")
                logger.info("   Requires depositing USDT to CEX first")
        else:
            logger.info("⏰ Continue monitoring - no immediate opportunities")

async def main():
    """Hauptprogramm"""
    arbitrage = PracticalCEXDEXArbitrage()
    
    logger.info("🚀 PRACTICAL CEX-DEX ARBITRAGE SCANNER")
    logger.info("Focusing on executable opportunities with your BSC wallet")
    logger.info("")
    
    opportunities = await arbitrage.scan_cex_dex_opportunities()
    arbitrage.print_detailed_report(opportunities)
    
    # Auto-execute if profitable flashloan opportunity exists
    auto_opportunities = [o for o in opportunities['profitable'] 
                         if o['strategy'] == 'BUY_DEX_SELL_CEX' and o['profit_pct'] > 1.0]
    
    if auto_opportunities:
        best = auto_opportunities[0]
        logger.info(f"\n🎯 High-profit opportunity detected: {best['profit_pct']:.3f}%")
        logger.info("Execute? This would run the flashloan arbitrage...")
        # Uncomment to auto-execute:
        # await arbitrage.execute_flashloan_arbitrage(best)

if __name__ == "__main__":
    asyncio.run(main())
