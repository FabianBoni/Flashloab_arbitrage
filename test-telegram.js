#!/usr/bin/env node
/**
 * Simple test script to verify Telegram bot functionality
 * Run with: node test-telegram.js
 */

const { TelegramBotService } = require('./dist/src/TelegramBot');

async function testTelegramBot() {
  console.log('🧪 Testing Telegram Bot Service...');
  
  const telegramBot = new TelegramBotService();
  
  if (!telegramBot.isActive()) {
    console.log('⚠️  Telegram bot is not configured or active.');
    console.log('💡 To test Telegram integration:');
    console.log('   1. Create a bot via @BotFather on Telegram');
    console.log('   2. Add TELEGRAM_BOT_TOKEN to your .env file');
    console.log('   3. Add TELEGRAM_CHAT_ID to your .env file');
    console.log('   4. Run this test again');
    return;
  }
  
  console.log('✅ Telegram bot is active and configured');
  
  // Test basic message sending
  console.log('📱 Sending test message...');
  const success = await telegramBot.sendMessage('🧪 Test message from Flashloan Arbitrage Bot!\n\nTelegram integration is working correctly! 🚀');
  
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
  
  await telegramBot.sendStatsReport(mockStats);
  console.log('✅ Stats report test completed');
  
  // Cleanup
  await telegramBot.shutdown();
  console.log('🏁 Telegram bot test completed');
}

// Handle errors
testTelegramBot().catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});