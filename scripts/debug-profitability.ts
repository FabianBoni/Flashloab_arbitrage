import { ethers } from 'hardhat';

const CONTRACT_ADDRESS = '0x0FA4cab40651cfcb308C169fd593E92F2f0cf805';

async function main() {
  const [deployer] = await ethers.getSigners();
  
  // Contract ABI
  const abi = [
    'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
    'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)',
    'function dexConfigs(string memory) external view returns (address router, bool isActive, uint256 fee)',
    'function minProfitThreshold() external view returns (uint256)'
  ];
  
  // DEX Router ABI for direct comparison
  const routerAbi = [
    'function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts)'
  ];
  
  const contract = new ethers.Contract(CONTRACT_ADDRESS, abi, deployer);
  
  console.log('🔍 DEBUGGING: Warum Contract Opportunities als unprofitabel einstuft\n');
  
  // Test parameters - die gleichen wie der Bot verwendet
  const amount = ethers.parseEther('1'); // 1 WBNB
  const dexA = 'Biswap';
  const dexB = 'PancakeSwap V2';
  const path = [
    '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', // WBNB
    '0x55d398326f99059fF775485246999027B3197955'  // USDT
  ];
  
  console.log(`💰 Testing with ${ethers.formatEther(amount)} WBNB`);
  console.log(`🔀 Path: WBNB -> USDT`);
  console.log(`📊 DEX A: ${dexA}`);
  console.log(`📊 DEX B: ${dexB}\n`);
  
  // 1. Check current profit threshold
  try {
    const threshold = await contract.minProfitThreshold();
    console.log(`🎯 Current profit threshold: ${ethers.formatEther(threshold)} BNB\n`);
  } catch (error) {
    console.log('❌ Error getting threshold:', error.message);
  }
  
  // 2. Check DEX configurations
  try {
    const configA = await contract.dexConfigs(dexA);
    const configB = await contract.dexConfigs(dexB);
    
    console.log('🔧 DEX Configurations:');
    console.log(`   ${dexA}: ${configA.router}, Active: ${configA.isActive}, Fee: ${configA.fee}bp`);
    console.log(`   ${dexB}: ${configB.router}, Active: ${configB.isActive}, Fee: ${configB.fee}bp\n`);
    
    if (!configA.isActive || !configB.isActive) {
      console.log('❌ One or both DEXes are inactive!');
      return;
    }
    
    // 3. Test direct router calls
    console.log('🧪 Direct DEX Router Tests:');
    
    const routerA = new ethers.Contract(configA.router, routerAbi, deployer);
    const routerB = new ethers.Contract(configB.router, routerAbi, deployer);
    
    try {
      const amountsA = await routerA.getAmountsOut(amount, path);
      console.log(`   ${dexA} Output: ${ethers.formatEther(amountsA[1])} USDT`);
      
      // Reverse path für DEX B
      const reversePath = [path[1], path[0]]; // USDT -> WBNB
      const amountsB = await routerB.getAmountsOut(amountsA[1], reversePath);
      console.log(`   ${dexB} Output: ${ethers.formatEther(amountsB[1])} WBNB`);
      
      const grossProfit = amountsB[1] - amount;
      const grossProfitEth = ethers.formatEther(grossProfit);
      const profitPercent = (parseFloat(grossProfitEth) / parseFloat(ethers.formatEther(amount))) * 100;
      
      console.log(`\n💰 Direct Router Calculation:`);
      console.log(`   Input: ${ethers.formatEther(amount)} WBNB`);
      console.log(`   Output: ${ethers.formatEther(amountsB[1])} WBNB`);
      console.log(`   Gross Profit: ${grossProfitEth} WBNB (${profitPercent.toFixed(2)}%)`);
      
      // Calculate fees
      const flashloanFee = amount * BigInt(25) / BigInt(10000); // 0.25%
      const netProfit = grossProfit - flashloanFee;
      console.log(`   Flashloan Fee: ${ethers.formatEther(flashloanFee)} WBNB`);
      console.log(`   Net Profit: ${ethers.formatEther(netProfit)} WBNB\n`);
      
    } catch (error) {
      console.log(`❌ Error with direct router calls: ${error.message}\n`);
    }
    
  } catch (error) {
    console.log('❌ Error getting DEX configs:', error.message);
  }
  
  // 4. Test contract profit calculation
  try {
    console.log('🏦 Contract Profit Calculation:');
    const contractProfit = await contract.calculateArbitrageProfit(amount, dexA, dexB, path);
    console.log(`   Contract Profit: ${ethers.formatEther(contractProfit)} WBNB`);
    
    const isProfitable = await contract.isArbitrageProfitable(amount, dexA, dexB, path);
    console.log(`   Is Profitable: ${isProfitable}\n`);
    
    if (contractProfit > 0 && !isProfitable) {
      console.log('🤔 Contract shows profit but says not profitable - threshold issue!');
    } else if (contractProfit == 0) {
      console.log('🤔 Contract shows 0 profit - DEX liquidity or path issue!');
    }
    
  } catch (error) {
    console.log(`❌ Error with contract calculation: ${error.message}\n`);
  }
  
  // 5. Test with different amounts
  console.log('📏 Testing different trade sizes:');
  const testAmounts = [
    ethers.parseEther('0.1'),   // 0.1 WBNB
    ethers.parseEther('0.5'),   // 0.5 WBNB
    ethers.parseEther('2'),     // 2 WBNB
  ];
  
  for (const testAmount of testAmounts) {
    try {
      const profit = await contract.calculateArbitrageProfit(testAmount, dexA, dexB, path);
      const profitable = await contract.isArbitrageProfitable(testAmount, dexA, dexB, path);
      console.log(`   ${ethers.formatEther(testAmount)} WBNB: ${ethers.formatEther(profit)} profit, profitable: ${profitable}`);
    } catch (error) {
      console.log(`   ${ethers.formatEther(testAmount)} WBNB: Error - ${error.message}`);
    }
  }
  
  console.log('\n✅ Debug completed! Check results above.');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
