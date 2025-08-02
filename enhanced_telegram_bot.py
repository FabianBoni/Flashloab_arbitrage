#!/usr/bin/env python3
"""
Enhanced Telegram Bot mit Stats-Funktion und Command-Handling
Nur Benachrichtigungen bei wichtigen Events + /stats Command
"""

import asyncio
import json
import logging
import os
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageStats:
    """Statistiken für Arbitrage-Activities"""
    # Zeiträume
    start_time: float
    last_reset: float
    
    # Opportunity Statistiken
    total_opportunities_found: int = 0
    cex_cex_opportunities: int = 0
    cex_dex_opportunities: int = 0
    dex_dex_opportunities: int = 0
    
    # Trading Statistiken
    total_trades_executed: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_profit_usd: float = 0.0
    
    # Performance Statistiken
    scans_completed: int = 0
    average_scan_time: float = 0.0
    best_opportunity_profit: float = 0.0
    best_opportunity_pair: str = ""
    
    # Letzte Aktivität
    last_opportunity_time: float = 0.0
    last_trade_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArbitrageStats':
        """Create from dictionary"""
        return cls(**data)

class EnhancedTelegramBot:
    """Enhanced Telegram Bot mit Stats und Commands"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        # Statistics tracking
        self.stats = ArbitrageStats(
            start_time=time.time(),
            last_reset=time.time()
        )
        
        # State tracking
        self.is_running = False
        self.last_update_id = 0
        
        # Notification settings
        self.notify_opportunities = True
        self.notify_trades = True
        self.notify_startup = True
        self.notify_shutdown = True
        
        if self.enabled:
            logger.info("📱 Enhanced Telegram bot enabled with /stats command")
        else:
            logger.info("📱 Telegram not configured - running without notifications")
    
    def start_polling(self):
        """Start command polling (call this from async context)"""
        if self.enabled:
            try:
                asyncio.create_task(self.start_command_polling())
            except RuntimeError:
                # If no event loop is running, create one
                pass
    
    async def start_command_polling(self):
        """Start polling for Telegram commands"""
        if not self.enabled:
            return
            
        while True:
            try:
                await self.check_commands()
                await asyncio.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.debug(f"Command polling error: {e}")
                await asyncio.sleep(5)
    
    async def check_commands(self):
        """Check for new Telegram commands"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {'offset': self.last_update_id + 1, 'timeout': 1}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                for update in data.get('result', []):
                    self.last_update_id = update['update_id']
                    
                    if 'message' in update:
                        message = update['message']
                        if message.get('chat', {}).get('id') == int(self.chat_id):
                            await self.handle_command(message)
                            
        except Exception as e:
            logger.debug(f"Error checking commands: {e}")
    
    async def handle_command(self, message: Dict[str, Any]):
        """Handle incoming Telegram command"""
        text = message.get('text', '').strip()
        
        if text == '/stats':
            await self.send_stats()
        elif text == '/help':
            await self.send_help()
        elif text == '/status':
            await self.send_status()
        elif text == '/reset':
            await self.reset_stats()
        elif text.startswith('/'):
            await self.send_unknown_command(text)
    
    def send_message(self, message: str):
        """Send message to Telegram"""
        if not self.enabled:
            return
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Telegram message failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Telegram error: {e}")
    
    async def send_stats(self):
        """Send current statistics"""
        now = time.time()
        uptime = now - self.stats.start_time
        uptime_str = str(timedelta(seconds=int(uptime)))
        
        # Calculate rates
        hours_running = uptime / 3600
        opportunities_per_hour = self.stats.total_opportunities_found / hours_running if hours_running > 0 else 0
        trades_per_hour = self.stats.total_trades_executed / hours_running if hours_running > 0 else 0
        
        # Success rate
        success_rate = (self.stats.successful_trades / self.stats.total_trades_executed * 100) if self.stats.total_trades_executed > 0 else 0
        
        # Last activity
        last_opp_ago = int((now - self.stats.last_opportunity_time) / 60) if self.stats.last_opportunity_time > 0 else "Never"
        last_trade_ago = int((now - self.stats.last_trade_time) / 60) if self.stats.last_trade_time > 0 else "Never"
        
        message = f"📊 <b>Arbitrage Bot Statistics</b>\n\n"
        message += f"⏰ <b>Uptime:</b> {uptime_str}\n"
        message += f"🔄 <b>Status:</b> {'🟢 Running' if self.is_running else '🔴 Stopped'}\n\n"
        
        message += f"🎯 <b>Opportunities Found:</b>\n"
        message += f"  • Total: {self.stats.total_opportunities_found} ({opportunities_per_hour:.1f}/hour)\n"
        message += f"  • CEX-CEX: {self.stats.cex_cex_opportunities}\n"
        message += f"  • CEX-DEX: {self.stats.cex_dex_opportunities}\n"
        message += f"  • DEX-DEX: {self.stats.dex_dex_opportunities}\n\n"
        
        message += f"💰 <b>Trading Performance:</b>\n"
        message += f"  • Trades: {self.stats.total_trades_executed} ({trades_per_hour:.1f}/hour)\n"
        message += f"  • Success Rate: {success_rate:.1f}%\n"
        message += f"  • Total Profit: ${self.stats.total_profit_usd:.2f}\n\n"
        
        message += f"🏆 <b>Best Opportunity:</b>\n"
        if self.stats.best_opportunity_pair:
            message += f"  • {self.stats.best_opportunity_pair}: {self.stats.best_opportunity_profit:.2f}%\n\n"
        else:
            message += f"  • None found yet\n\n"
        
        message += f"📈 <b>Performance:</b>\n"
        message += f"  • Scans: {self.stats.scans_completed}\n"
        message += f"  • Avg Scan Time: {self.stats.average_scan_time:.2f}s\n\n"
        
        message += f"🕐 <b>Last Activity:</b>\n"
        message += f"  • Opportunity: {last_opp_ago} min ago\n" if isinstance(last_opp_ago, int) else f"  • Opportunity: {last_opp_ago}\n"
        message += f"  • Trade: {last_trade_ago} min ago" if isinstance(last_trade_ago, int) else f"  • Trade: {last_trade_ago}"
        
        self.send_message(message)
    
    async def send_help(self):
        """Send help message"""
        message = f"🤖 <b>Arbitrage Bot Commands</b>\n\n"
        message += f"/stats - 📊 Show current statistics\n"
        message += f"/status - 🔄 Show bot status\n"
        message += f"/reset - 🔄 Reset statistics\n"
        message += f"/help - ❓ Show this help\n\n"
        message += f"<b>Automatic Notifications:</b>\n"
        message += f"✅ Arbitrage opportunities found\n"
        message += f"✅ Trades executed\n"
        message += f"✅ Bot start/stop events\n\n"
        message += f"<i>Bot only sends important updates to avoid spam.</i>"
        
        self.send_message(message)
    
    async def send_status(self):
        """Send bot status"""
        message = f"🔄 <b>Bot Status</b>\n\n"
        message += f"Status: {'🟢 Running' if self.is_running else '🔴 Stopped'}\n"
        message += f"Trading: {'✅ Enabled' if os.getenv('ENABLE_CEX_TRADING', 'false').lower() == 'true' else '❌ Disabled'}\n"
        message += f"Exchanges: Gate.io, Bitget\n"
        message += f"Token Pairs: 87\n"
        message += f"Scan Interval: 30s\n"
        message += f"Min Profit: CEX-CEX 0.2%, CEX-DEX 0.1%"
        
        self.send_message(message)
    
    async def send_unknown_command(self, command: str):
        """Send unknown command message"""
        message = f"❓ Unknown command: {command}\n\nUse /help to see available commands."
        self.send_message(message)
    
    async def reset_stats(self):
        """Reset statistics"""
        self.stats = ArbitrageStats(
            start_time=time.time(),
            last_reset=time.time()
        )
        
        message = f"🔄 <b>Statistics Reset</b>\n\nAll statistics have been reset to zero."
        self.send_message(message)
    
    # Event notification methods (only send when important events happen)
    
    def notify_bot_started(self):
        """Notify when bot starts"""
        if not self.notify_startup:
            return
            
        self.is_running = True
        message = f"🚀 <b>Arbitrage Bot Started</b>\n\n"
        message += f"✅ Monitoring 87 trading pairs\n"
        message += f"✅ CEX: 8 exchanges\n"
        message += f"✅ DEX: BSC (PancakeSwap, etc.)\n"
        message += f"🎯 Min profit: 0.2% CEX-CEX, 0.1% CEX-DEX\n"
        message += f"📱 Use /stats for statistics"
        
        self.send_message(message)
    
    def notify_bot_stopped(self):
        """Notify when bot stops"""
        if not self.notify_shutdown:
            return
            
        self.is_running = False
        message = f"🔴 <b>Arbitrage Bot Stopped</b>\n\n"
        message += f"📊 Session stats:\n"
        message += f"  • Opportunities: {self.stats.total_opportunities_found}\n"
        message += f"  • Trades: {self.stats.total_trades_executed}\n"
        message += f"  • Profit: ${self.stats.total_profit_usd:.2f}"
        
        self.send_message(message)
    
    def notify_opportunity_found(self, opportunity_type: str, token_pair: str, profit_percent: float, exchanges: str):
        """Notify when arbitrage opportunity is found"""
        if not self.notify_opportunities:
            return
            
        # Update stats
        self.stats.total_opportunities_found += 1
        self.stats.last_opportunity_time = time.time()
        
        if opportunity_type == "CEX_CEX":
            self.stats.cex_cex_opportunities += 1
        elif opportunity_type == "CEX_DEX":
            self.stats.cex_dex_opportunities += 1
        elif opportunity_type == "DEX_DEX":
            self.stats.dex_dex_opportunities += 1
        
        # Update best opportunity
        if profit_percent > self.stats.best_opportunity_profit:
            self.stats.best_opportunity_profit = profit_percent
            self.stats.best_opportunity_pair = token_pair
        
        # Only notify if profit is significant (>0.5%)
        if profit_percent < 0.5:
            return
            
        message = f"🎯 <b>Arbitrage Opportunity Found!</b>\n\n"
        message += f"💰 <b>{token_pair}</b>\n"
        message += f"📈 Profit: <b>{profit_percent:.3f}%</b>\n"
        message += f"🔄 Type: {opportunity_type}\n"
        message += f"🏪 {exchanges}\n"
        message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        self.send_message(message)
    
    def notify_trade_executed(self, token_pair: str, profit_usd: float, success: bool, details: str = ""):
        """Notify when trade is executed"""
        if not self.notify_trades:
            return
            
        # Update stats
        self.stats.total_trades_executed += 1
        self.stats.last_trade_time = time.time()
        
        if success:
            self.stats.successful_trades += 1
            self.stats.total_profit_usd += profit_usd
            
            message = f"✅ <b>Trade Executed Successfully!</b>\n\n"
            message += f"💰 {token_pair}\n"
            message += f"💵 Profit: <b>${profit_usd:.2f}</b>\n"
            if details:
                message += f"📝 {details}\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        else:
            self.stats.failed_trades += 1
            
            message = f"❌ <b>Trade Failed</b>\n\n"
            message += f"💰 {token_pair}\n"
            if details:
                message += f"❌ Error: {details}\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        self.send_message(message)
    
    def update_scan_stats(self, scan_time: float):
        """Update scan performance statistics"""
        self.stats.scans_completed += 1
        
        # Rolling average
        if self.stats.average_scan_time == 0:
            self.stats.average_scan_time = scan_time
        else:
            self.stats.average_scan_time = (self.stats.average_scan_time * 0.9) + (scan_time * 0.1)

# Global instance
telegram_bot = EnhancedTelegramBot()

if __name__ == "__main__":
    # Test the bot
    async def test_bot():
        bot = EnhancedTelegramBot()
        
        # Test notifications
        bot.notify_bot_started()
        await asyncio.sleep(1)
        
        bot.notify_opportunity_found("CEX_CEX", "PEPE/USDT", 0.75, "Buy: Binance, Sell: Gate.io")
        await asyncio.sleep(1)
        
        bot.notify_trade_executed("PEPE/USDT", 15.50, True, "Executed 1000 PEPE")
        await asyncio.sleep(1)
        
        await bot.send_stats()
        
    asyncio.run(test_bot())
