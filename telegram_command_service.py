#!/usr/bin/env python3
"""
Telegram Command Polling Service
Läuft im Hintergrund und überwacht /stats und andere Commands
"""

import asyncio
import logging
import signal
import sys
from enhanced_telegram_bot import telegram_bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramCommandService:
    """Service für Telegram Command Polling"""
    
    def __init__(self):
        self.running = False
        self.bot = telegram_bot
        
    async def start(self):
        """Start the command polling service"""
        if not self.bot.enabled:
            logger.info("📱 Telegram not configured - command service disabled")
            return
            
        logger.info("🤖 Starting Telegram command polling service...")
        logger.info("📱 Available commands: /stats, /status, /help, /reset")
        
        self.running = True
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info("🛑 Stopping command service...")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start polling loop
        try:
            while self.running:
                await self.bot.check_commands()
                await asyncio.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Command service stopped by user")
        except Exception as e:
            logger.error(f"❌ Command service error: {e}")
        finally:
            logger.info("📱 Telegram command service stopped")

async def main():
    """Main entry point"""
    service = TelegramCommandService()
    await service.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Service interrupted")
        sys.exit(0)
