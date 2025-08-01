#!/usr/bin/env node
/**
 * Simple test script to verify Telegram bot functionality
 * Run with: node test-telegram.js
 */

require('dotenv').config();
const { TelegramBotService } = require('./dist/src/TelegramBot');

async function testTelegramBot() {
  console.log('🧪 Testing Telegram Bot Service...');
  
  const telegramBot = new TelegramBotService();
  
  // Wait a moment for initialization
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  if (!telegramBot.isActive()) {
    console.log('⚠️  Telegram bot is not configured or active.');
    console.log('💡 To test Telegram integration:');
    console.log('   1. Create a bot via @BotFather on Telegram');
    console.log('   2. Add TELEGRAM_BOT_TOKEN to your .env file');
    console.log('   3. Add TELEGRAM_CHAT_ID to your .env file');
    console.log('   4. Run this test again');
    console.log('\n📋 Current environment variables:');
    console.log('   TELEGRAM_BOT_TOKEN:', process.env.TELEGRAM_BOT_TOKEN ? 'Set' : 'Not set');
    console.log('   TELEGRAM_CHAT_ID:', process.env.TELEGRAM_CHAT_ID ? 'Set' : 'Not set');
    return;
  }
  
  console.log('✅ Telegram bot is active and configured');
  
  // Test basic message sending
  console.log('📱 Sending test message...');
  const success = await telegramBot.sendTestMessage();
  
  if (success) {
    console.log('✅ Test message sent successfully!');
  } else {
    console.log('❌ Failed to send test message');
  }
  
  // Test notification methods
  console.log('📊 Testing notification methods...');
  
  // Test stats report
  const mockStats = {
    opportunitiesFound: 10,
    tradesExecuted: 3,
    successfulTrades: 2,
    totalProfit: 0.0042,
    uptime: 300000 // 5 minutes
  };
  
  await telegramBot.sendStats(mockStats);
  console.log('✅ Stats report test completed');
  
  // Test arbitrage opportunity alert
  const mockOpportunity = {
    tokenA: 'WBNB',
    tokenB: 'BUSD',
    profitPercentage: 1.25,
    profitAmount: '0.0045 BNB',
    dexA: 'PancakeSwap',
    dexB: 'BabySwap',
    chainId: 56
  };
  
  await telegramBot.sendOpportunityAlert(mockOpportunity);
  console.log('✅ Opportunity alert test completed');
  
  // Cleanup
  await telegramBot.shutdown();
  console.log('🏁 Telegram bot test completed successfully! ✅');
}

// Handle errors
testTelegramBot().catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});
  process.exit(1);
});