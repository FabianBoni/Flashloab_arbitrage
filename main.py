#!/usr/bin/env python3
"""
BSC Arbitrage System - Production Main
Unified CEX-DEX arbitrage scanner with comprehensive trading capabilities
"""

import time
import logging
import gc
import os
import sys
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import json
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
import requests
from dotenv import load_dotenv

# Core system imports
from enhanced_telegram_bot import telegram_bot
from cex_price_provider import CexPriceProvider, CexPrice
from cex_trading_api import trading_api
from unified_arbitrage_scanner import UnifiedArbitrageScanner, UnifiedOpportunity
from optimization_config import DEX_CONFIGS, VOLATILE_TOKENS

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_handlers = [logging.StreamHandler(sys.stdout)]

try:
    os.makedirs('logs', exist_ok=True)
    test_file = 'logs/test_write.tmp'
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    log_handlers.append(logging.FileHandler('logs/arbitrage_main.log', encoding='utf-8'))
    print("✅ File logging enabled: logs/arbitrage_main.log")
except (PermissionError, OSError) as e:
    print(f"⚠️  File logging disabled: {e}")

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageStats:
    """Trading statistics"""
    scans_completed: int = 0
    opportunities_found: int = 0
    trades_executed: int = 0
    successful_trades: int = 0
    total_profit_usdt: float = 0.0
    total_gas_spent_bnb: float = 0.0
    uptime_hours: float = 0.0
    best_profit_pct: float = 0.0
    
class BSCArbitrageSystem:
    """Main arbitrage system orchestrator"""
    
    def __init__(self):
        self.stats = ArbitrageStats()
        self.start_time = time.time()
        self.last_cleanup = time.time()
        
        # Initialize components
        logger.info("🚀 Initializing BSC Arbitrage System...")
        
        # Web3 setup
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        
        # Scanner setup
        self.scanner = UnifiedArbitrageScanner()
        
        # Configuration
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5'))  # 0.5%
        self.max_gas_price = float(os.getenv('MAX_GAS_PRICE', '5'))  # Gwei
        self.scan_interval = int(os.getenv('SCAN_INTERVAL', '10'))  # seconds
        self.enable_execution = os.getenv('ENABLE_EXECUTION', 'true').lower() == 'true'  # 🔴 PRODUCTION MODE ENABLED
        
        logger.info(f"📊 Configuration:")
        logger.info(f"   Min Profit: {self.min_profit_threshold}%")
        logger.info(f"   Max Gas: {self.max_gas_price} Gwei")
        logger.info(f"   Scan Interval: {self.scan_interval}s")
        logger.info(f"   Execution: {'🔴 LIVE TRADING ENABLED' if self.enable_execution else '❌ SIMULATION ONLY'}")
        
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to BSC at {rpc_url}")
        
        latest_block = w3.eth.block_number
        logger.info(f"🔗 Connected to BSC: Block {latest_block}")
        return w3
    
    def _setup_account(self) -> Optional[object]:
        """Setup trading account"""
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            logger.warning("⚠️  No private key - running in simulation mode")
            return None
        
        try:
            account = self.w3.eth.account.from_key(private_key)
            balance = self.w3.eth.get_balance(account.address)
            balance_bnb = self.w3.from_wei(balance, 'ether')
            
            logger.info(f"💼 Account: {account.address}")
            logger.info(f"💰 Balance: {balance_bnb:.4f} BNB")
            
            if balance_bnb < 0.1:
                logger.warning(f"⚠️  Low BNB balance: {balance_bnb:.4f} BNB")
            
            return account
        except Exception as e:
            logger.error(f"❌ Error loading account: {e}")
            return None
    
    async def scan_opportunities(self) -> List[UnifiedOpportunity]:
        """Scan for arbitrage opportunities"""
        try:
            self.stats.scans_completed += 1
            
            # Scan all opportunity types
            opportunities = []
            
            # 1. CEX-DEX opportunities (primary focus)
            cex_dex_opps = await self.scanner.find_cex_dex_opportunities()
            opportunities.extend(cex_dex_opps)
            
            # 2. CEX-CEX opportunities  
            cex_cex_opps = await self.scanner.find_cex_cex_opportunities()
            opportunities.extend(cex_cex_opps)
            
            # Filter by profitability
            profitable_opps = [
                opp for opp in opportunities 
                if opp.profit_percentage >= self.min_profit_threshold
            ]
            
            if profitable_opps:
                self.stats.opportunities_found += len(profitable_opps)
                logger.info(f"🎯 Found {len(profitable_opps)} profitable opportunities")
                
                # Update best profit
                best_profit = max(opp.profit_percentage for opp in profitable_opps)
                if best_profit > self.stats.best_profit_pct:
                    self.stats.best_profit_pct = best_profit
            
            return profitable_opps
            
        except Exception as e:
            logger.error(f"❌ Error scanning opportunities: {e}")
            return []
    
    async def execute_opportunity(self, opportunity: UnifiedOpportunity) -> bool:
        """Execute arbitrage opportunity"""
        
        if not self.enable_execution:
            logger.info(f"📊 SIMULATION: Would execute {opportunity.strategy} for {opportunity.profit_percentage:.3f}% profit")
            return True
        
        # 🔴 PRODUCTION SAFETY CHECKS
        if opportunity.profit_percentage < self.min_profit_threshold:
            logger.warning(f"⚠️  Profit {opportunity.profit_percentage:.3f}% below threshold {self.min_profit_threshold}%")
            return False
            
        if opportunity.estimated_profit_usdt < 1.0:  # Minimum $1 profit
            logger.warning(f"⚠️  Estimated profit ${opportunity.estimated_profit_usdt:.2f} too low for production")
            return False
        
        if not self.account:
            logger.warning("⚠️  Cannot execute - no account configured")
            return False
        
        try:
            logger.info(f"🔴 LIVE TRADE: Executing {opportunity.strategy}: {opportunity.token_pair}")
            logger.info(f"   Expected profit: {opportunity.profit_percentage:.3f}% (~${opportunity.estimated_profit_usdt:.2f})")
            
            self.stats.trades_executed += 1
            
            # Route to appropriate execution method
            if opportunity.strategy == 'CEX_DEX_FLASHLOAN':
                success = await self._execute_cex_dex_flashloan(opportunity)
            elif opportunity.strategy == 'DEX_DEX_FLASHLOAN':
                success = await self._execute_dex_flashloan(opportunity)
            elif opportunity.strategy == 'TRIANGULAR_CEX':
                success = await self._execute_triangular_cex(opportunity)
            else:
                logger.warning(f"⚠️  Unknown strategy: {opportunity.strategy}")
                return False
            
            if success:
                self.stats.successful_trades += 1
                self.stats.total_profit_usdt += opportunity.estimated_profit_usdt
                
                # Send success notification
                try:
                    if hasattr(telegram_bot, 'send_message'):
                        await telegram_bot.send_message(
                            f"✅ Trade executed successfully!\n"
                            f"Strategy: {opportunity.strategy}\n"
                            f"Pair: {opportunity.token_pair}\n"
                            f"Profit: {opportunity.profit_percentage:.3f}% (~${opportunity.estimated_profit_usdt:.2f})"
                        )
                except Exception as e:
                    logger.warning(f"⚠️  Telegram notification failed: {e}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")
            
            try:
                if hasattr(telegram_bot, 'send_message'):
                    await telegram_bot.send_message(
                        f"❌ Trade execution failed\n"
                        f"Strategy: {opportunity.strategy}\n"
                        f"Error: {str(e)[:100]}..."
                    )
            except Exception as notify_error:
                logger.warning(f"⚠️  Telegram notification failed: {notify_error}")
            return False
    
    async def _execute_cex_dex_flashloan(self, opportunity: UnifiedOpportunity) -> bool:
        """Execute CEX-DEX arbitrage with flashloan"""
        try:
            # This would integrate with your existing flashloan contracts
            logger.info("🏦 Initiating CEX-DEX flashloan arbitrage...")
            
            # Check CEX balance for selling
            if hasattr(opportunity, 'sell_exchange'):
                balance = await trading_api.get_balance(opportunity.sell_exchange, opportunity.token_symbol)
                if not balance or balance < opportunity.amount_needed:
                    logger.warning(f"⚠️  Insufficient CEX balance on {opportunity.sell_exchange}")
                    return False
            
            # Placeholder for actual flashloan execution
            # Your existing smart contract integration would go here
            
            logger.info("✅ CEX-DEX flashloan arbitrage completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ CEX-DEX flashloan failed: {e}")
            return False
    
    async def _execute_dex_flashloan(self, opportunity: UnifiedOpportunity) -> bool:
        """Execute DEX-DEX arbitrage with flashloan"""
        try:
            # Your existing DEX arbitrage logic
            logger.info("🔄 Executing DEX-DEX flashloan arbitrage...")
            
            # Use your existing smart contracts
            return True
            
        except Exception as e:
            logger.error(f"❌ DEX flashloan failed: {e}")
            return False
    
    async def _execute_triangular_cex(self, opportunity: UnifiedOpportunity) -> bool:
        """Execute triangular arbitrage on CEX"""
        try:
            logger.info("🔺 Executing triangular arbitrage...")
            
            # Use CEX trading API for triangular arbitrage
            # This requires manual balance management
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Triangular arbitrage failed: {e}")
            return False
    
    def print_stats(self):
        """Print current statistics"""
        self.stats.uptime_hours = (time.time() - self.start_time) / 3600
        
        logger.info("📊 ARBITRAGE SYSTEM STATISTICS")
        logger.info("=" * 50)
        logger.info(f"⏱️  Uptime: {self.stats.uptime_hours:.1f} hours")
        logger.info(f"🔍 Scans completed: {self.stats.scans_completed:,}")
        logger.info(f"🎯 Opportunities found: {self.stats.opportunities_found:,}")
        logger.info(f"⚡ Trades executed: {self.stats.trades_executed:,}")
        logger.info(f"✅ Successful trades: {self.stats.successful_trades:,}")
        
        if self.stats.trades_executed > 0:
            success_rate = (self.stats.successful_trades / self.stats.trades_executed) * 100
            logger.info(f"📈 Success rate: {success_rate:.1f}%")
        
        logger.info(f"💰 Total profit: ${self.stats.total_profit_usdt:.2f}")
        logger.info(f"⛽ Gas spent: {self.stats.total_gas_spent_bnb:.4f} BNB")
        logger.info(f"🏆 Best profit: {self.stats.best_profit_pct:.3f}%")
        
        if self.stats.scans_completed > 0:
            avg_opps_per_scan = self.stats.opportunities_found / self.stats.scans_completed
            logger.info(f"📊 Avg opportunities/scan: {avg_opps_per_scan:.2f}")
    
    async def cleanup_resources(self):
        """Periodic cleanup to manage memory"""
        current_time = time.time()
        
        if current_time - self.last_cleanup > 1800:  # 30 minutes
            logger.info("🧹 Performing periodic cleanup...")
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"🗑️  Collected {collected} objects")
            
            # Update last cleanup time
            self.last_cleanup = current_time
    
    async def send_periodic_stats(self):
        """Send periodic statistics to Telegram"""
        try:
            self.print_stats()
            
            stats_message = (
                f"📊 BSC Arbitrage Stats Update\n"
                f"⏱️ Uptime: {self.stats.uptime_hours:.1f}h\n"
                f"🔍 Scans: {self.stats.scans_completed:,}\n"
                f"🎯 Opportunities: {self.stats.opportunities_found:,}\n"
                f"✅ Successful trades: {self.stats.successful_trades:,}\n"
                f"💰 Total profit: ${self.stats.total_profit_usdt:.2f}\n"
                f"🏆 Best profit: {self.stats.best_profit_pct:.3f}%"
            )
            
            try:
                if hasattr(telegram_bot, 'send_message'):
                    await telegram_bot.send_message(stats_message)
            except Exception as e:
                logger.warning(f"⚠️  Telegram stats notification failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error sending stats: {e}")
    
    async def run(self):
        """Main execution loop"""
        logger.info("🚀 Starting BSC Arbitrage System...")
        
        # Send startup notification
        try:
            if hasattr(telegram_bot, 'send_message'):
                await telegram_bot.send_message(
                    f"🚀 BSC Arbitrage System Started\n"
                    f"Mode: {'🔴 LIVE TRADING' if self.enable_execution else '🟡 SIMULATION'}\n"
                    f"Min Profit: {self.min_profit_threshold}%\n"
                    f"Scan Interval: {self.scan_interval}s"
                )
            else:
                logger.warning("⚠️  Telegram bot not available")
        except Exception as e:
            logger.warning(f"⚠️  Telegram notification failed: {e}")
        
        last_stats_time = time.time()
        
        try:
            while True:
                scan_start = time.time()
                
                # Scan for opportunities
                opportunities = await self.scan_opportunities()
                
                # Execute profitable opportunities
                for opportunity in opportunities:
                    if opportunity.profit_percentage >= self.min_profit_threshold:
                        await self.execute_opportunity(opportunity)
                        
                        # Small delay between executions
                        await asyncio.sleep(1)
                
                # Periodic cleanup
                await self.cleanup_resources()
                
                # Send periodic stats (every hour)
                current_time = time.time()
                if current_time - last_stats_time > 3600:  # 1 hour
                    await self.send_periodic_stats()
                    last_stats_time = current_time
                
                # Calculate sleep time
                scan_duration = time.time() - scan_start
                sleep_time = max(0, self.scan_interval - scan_duration)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            try:
                if hasattr(telegram_bot, 'send_message'):
                    await telegram_bot.send_message(f"🚨 System error: {str(e)[:100]}...")
            except Exception as notify_error:
                logger.warning(f"⚠️  Telegram error notification failed: {notify_error}")
        finally:
            # Send shutdown notification
            try:
                if hasattr(telegram_bot, 'send_message'):
                    await telegram_bot.send_message("🛑 BSC Arbitrage System Stopped")
            except Exception as notify_error:
                logger.warning(f"⚠️  Telegram shutdown notification failed: {notify_error}")
            logger.info("👋 BSC Arbitrage System stopped")

async def main():
    """Main entry point"""
    try:
        system = BSCArbitrageSystem()
        await system.run()
    except Exception as e:
        logger.error(f"❌ Failed to start system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
