/**
 * Example script demonstrating Etherscan V2 API usage
 * This shows how to use the unified API across multiple chains
 */

import { EtherscanV2Helper } from './EtherscanV2Helper';

async function demonstrateEtherscanV2() {
  console.log('🔍 Etherscan V2 API Demo');
  console.log('========================');

  try {
    // Initialize helper with your API key
    const etherscan = new EtherscanV2Helper(process.env.ETHERSCAN_API_KEY || 'YOUR_API_KEY');

    // Example wallet address (Vitalik's address)
    const address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045';

    console.log('\n📊 Getting balances across multiple chains with single API key...');

    // Get balance on Ethereum
    console.log('\n🔗 Ethereum (Chain ID: 1)');
    try {
      const ethBalance = await etherscan.getBalance(address, 1);
      console.log(`   Balance: ${(Number(ethBalance) / 1e18).toFixed(4)} ETH`);
    } catch (error: any) {
      console.log(`   Error: ${error.message}`);
    }

    // Get balance on Polygon
    console.log('\n🔗 Polygon (Chain ID: 137)');
    try {
      const polygonBalance = await etherscan.getBalance(address, 137);
      console.log(`   Balance: ${(Number(polygonBalance) / 1e18).toFixed(4)} MATIC`);
    } catch (error: any) {
      console.log(`   Error: ${error.message}`);
    }

    // Get balance on Arbitrum
    console.log('\n🔗 Arbitrum (Chain ID: 42161)');
    try {
      const arbBalance = await etherscan.getBalance(address, 42161);
      console.log(`   Balance: ${(Number(arbBalance) / 1e18).toFixed(4)} ETH`);
    } catch (error: any) {
      console.log(`   Error: ${error.message}`);
    }

    // Get balance on BSC
    console.log('\n🔗 BSC (Chain ID: 56)');
    try {
      const bscBalance = await etherscan.getBalance(address, 56);
      console.log(`   Balance: ${(Number(bscBalance) / 1e18).toFixed(4)} BNB`);
    } catch (error: any) {
      console.log(`   Error: ${error.message}`);
    }

    console.log('\n🎯 Benefits of Etherscan V2:');
    console.log('   ✅ Single API key for all supported chains');
    console.log('   ✅ Unified endpoint: https://api.etherscan.io/v2/api');
    console.log('   ✅ Chain-specific queries using chainid parameter');
    console.log('   ✅ No need to manage multiple API keys');
    console.log('   ✅ Simplified configuration');

    console.log('\n🔧 Supported Chains:');
    const supportedChains = EtherscanV2Helper.getSupportedChains();
    Object.entries(supportedChains).forEach(([name, chainId]) => {
      console.log(`   • ${name}: ${chainId}`);
    });

  } catch (error: any) {
    console.error('❌ Demo failed:', error.message);
    console.log('\n💡 Make sure to set your ETHERSCAN_API_KEY environment variable');
  }
}

// Example of checking recent transactions across chains
async function checkRecentTransactions() {
  console.log('\n📈 Recent Transactions Demo');
  console.log('===========================');

  try {
    const etherscan = new EtherscanV2Helper(process.env.ETHERSCAN_API_KEY || 'YOUR_API_KEY');
    const address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045';

    // Get last 5 transactions on Ethereum
    console.log('\n🔍 Last 5 transactions on Ethereum:');
    const ethTxs = await etherscan.getTransactions(address, 1, 0, 99999999, 1, 5);
    ethTxs.forEach((tx, index) => {
      console.log(`   ${index + 1}. Hash: ${tx.hash.substring(0, 10)}... | Value: ${(Number(tx.value) / 1e18).toFixed(4)} ETH`);
    });

    // Get last 5 transactions on Polygon
    console.log('\n🔍 Last 5 transactions on Polygon:');
    const polygonTxs = await etherscan.getTransactions(address, 137, 0, 99999999, 1, 5);
    polygonTxs.forEach((tx, index) => {
      console.log(`   ${index + 1}. Hash: ${tx.hash.substring(0, 10)}... | Value: ${(Number(tx.value) / 1e18).toFixed(4)} MATIC`);
    });

  } catch (error: any) {
    console.error('❌ Transaction demo failed:', error.message);
  }
}

// Example of contract verification across chains
async function demonstrateContractVerification() {
  console.log('\n🔍 Contract Verification Demo');
  console.log('=============================');

  try {
    const etherscan = new EtherscanV2Helper(process.env.ETHERSCAN_API_KEY || 'YOUR_API_KEY');

    // Example: Check a well-known contract on different chains
    const uniswapV2Router = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D';

    console.log('\n🔍 Checking Uniswap V2 Router verification status:');

    // Check on Ethereum
    console.log('\n📍 Ethereum:');
    try {
      const ethContract = await etherscan.getContractVerificationStatus(uniswapV2Router, 1);
      console.log(`   Contract Name: ${ethContract.ContractName || 'Not verified'}`);
      console.log(`   Compiler Version: ${ethContract.CompilerVersion || 'N/A'}`);
      console.log(`   Optimization: ${ethContract.OptimizationUsed === '1' ? 'Enabled' : 'Disabled'}`);
    } catch (error: any) {
      console.log(`   Error: ${error.message}`);
    }

    // Check on other chains (if contract exists)
    console.log('\n📍 Other chains: Same API key, different chainid parameter');
    console.log('   This demonstrates the power of Etherscan V2 unified API');

  } catch (error: any) {
    console.error('❌ Contract verification demo failed:', error.message);
  }
}

// Migration helper for projects moving from V1 to V2
export function migrateFromV1ToV2() {
  console.log('\n🔄 Migration Guide: V1 → V2');
  console.log('============================');
  
  console.log('\n❌ OLD V1 Configuration:');
  console.log('   ETHERSCAN_API_KEY=your_eth_key');
  console.log('   POLYGONSCAN_API_KEY=your_polygon_key');
  console.log('   ARBISCAN_API_KEY=your_arbitrum_key');
  console.log('   BSCSCAN_API_KEY=your_bsc_key');
  console.log('');
  console.log('   // Separate endpoints');
  console.log('   eth: https://api.etherscan.io/api');
  console.log('   polygon: https://api.polygonscan.com/api');
  console.log('   arbitrum: https://api.arbiscan.io/api');
  console.log('   bsc: https://api.bscscan.com/api');

  console.log('\n✅ NEW V2 Configuration:');
  console.log('   ETHERSCAN_API_KEY=your_single_key  # Works for all chains!');
  console.log('');
  console.log('   // Single unified endpoint');
  console.log('   all chains: https://api.etherscan.io/v2/api');
  console.log('   // Use chainid parameter: ?chainid=1 (ETH), ?chainid=137 (Polygon), etc.');

  console.log('\n🎯 Benefits:');
  console.log('   • Reduced API key management');
  console.log('   • Unified codebase');
  console.log('   • Simplified configuration');
  console.log('   • Better error handling');
  console.log('   • Future-proof architecture');
}

// Run the demo
if (require.main === module) {
  console.log('🚀 Starting Etherscan V2 API Demonstration...');
  
  demonstrateEtherscanV2()
    .then(() => checkRecentTransactions())
    .then(() => demonstrateContractVerification())
    .then(() => migrateFromV1ToV2())
    .then(() => {
      console.log('\n✅ Demo completed successfully!');
      console.log('\n💡 Next steps:');
      console.log('   1. Update your .env file with a single ETHERSCAN_API_KEY');
      console.log('   2. Remove old POLYGONSCAN_API_KEY, ARBISCAN_API_KEY, BSCSCAN_API_KEY');
      console.log('   3. Update hardhat.config.ts to use the same key for all networks');
      console.log('   4. Use the EtherscanV2Helper class for API interactions');
    })
    .catch(error => {
      console.error('❌ Demo failed:', error);
      process.exit(1);
    });
}
