import { FlashloanArbitrageBot } from './index';

async function runExample() {
  console.log('🚀 Flashloan Arbitrage Bot Example');
  console.log('This example demonstrates how to use the arbitrage bot.');
  console.log('');
  console.log('⚠️  Note: This is a demonstration. To run with real funds:');
  console.log('   1. Deploy the smart contracts to your desired networks');
  console.log('   2. Update the contract addresses in the configuration');
  console.log('   3. Set up your environment variables (.env file)');
  console.log('   4. Ensure you have sufficient funds for trading');
  console.log('');

  try {
    // Create the bot instance
    console.log('📊 Initializing bot...');
    const bot = new FlashloanArbitrageBot();
    
    // Get initial statistics
    const stats = bot.getStats();
    console.log('📈 Initial statistics:', stats);
    
    console.log('');
    console.log('🔍 Bot would normally start monitoring for arbitrage opportunities...');
    console.log('💡 In production, the bot would:');
    console.log('   - Monitor prices across multiple DEXes');
    console.log('   - Detect profitable arbitrage opportunities');
    console.log('   - Execute flashloan arbitrage trades automatically');
    console.log('   - Report statistics and profits');
    console.log('');
    
    // In a real scenario, you would call:
    // await bot.start();
    
    console.log('✅ Example completed successfully!');
    console.log('💼 To use with real trading, follow the deployment guide in README.md');
    
  } catch (error: any) {
    console.error('❌ Example failed:', error.message);
    console.log('');
    console.log('🔧 Common issues:');
    console.log('   - Missing environment variables (.env file)');
    console.log('   - Invalid RPC URLs');
    console.log('   - Missing private key');
    console.log('   - Network connectivity issues');
  }
}

// Run the example
runExample().catch(console.error);