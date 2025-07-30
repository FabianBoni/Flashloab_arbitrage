#!/usr/bin/env node

import dotenv from 'dotenv';
import { FlashloanArbitrageBot } from '../src/index.js';
import { logger } from '../src/logger.js';

// Load environment variables
dotenv.config();

async function main() {
    logger.info('🧪 Starting Rate Limiter Test with Limited DEXs...');
    
    // Temporarily override config to use only 3 DEXs for testing
    process.env.TEST_MODE = 'true';
    
    try {
        const bot = new FlashloanArbitrageBot();
        
        // Start the bot
        await bot.start();
        
        // Run for 60 seconds then stop
        setTimeout(() => {
            logger.info('🛑 Test completed, stopping bot...');
            process.exit(0);
        }, 60000);
        
    } catch (error) {
        logger.error('Test failed:', error);
        process.exit(1);
    }
}

main().catch((error) => {
    logger.error('Fatal error in test:', error);
    process.exit(1);
});
