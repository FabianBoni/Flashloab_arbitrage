import { ethers } from 'hardhat';

const CONTRACT_ADDRESS = '0xDf9b5f44edae76901a6190496467002aEFCEf677';
const ABI = [
  'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
  'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)',
  'function updateMinProfitThreshold(uint256 newThreshold) external',
  'function minProfitThreshold() external view returns (uint256)'
];

async function main() {
  const [deployer] = await ethers.getSigners();
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, deployer);
  
  console.log('🧪 Testing Universal Flashloan Contract...');
  console.log(`📝 Contract: ${CONTRACT_ADDRESS}\n`);

  // Test parameters - USDT/USDC pair
  const amount = ethers.parseEther('100'); // 100 tokens
  const dexA = 'Biswap';
  const dexB = 'PancakeSwap V2';
  const path = [
    '0x55d398326f99059fF775485246999027B3197955', // USDT
    '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d'  // USDC
  ];

  try {
    // Check current profit threshold
    const threshold = await contract.minProfitThreshold();
    console.log(`💡 Current profit threshold: ${ethers.formatEther(threshold)} ETH`);

    // Lower the threshold for testing
    console.log('🔧 Lowering profit threshold for testing...');
    const newThreshold = ethers.parseEther('0.001'); // 0.001 ETH
    await contract.updateMinProfitThreshold(newThreshold);
    console.log('✅ Threshold updated\n');

    // Test profitability calculation
    console.log('🔍 Testing USDT -> USDC arbitrage...');
    console.log(`   Amount: ${ethers.formatEther(amount)} USDT`);
    console.log(`   DEX A: ${dexA}`);
    console.log(`   DEX B: ${dexB}`);

    const profit = await contract.calculateArbitrageProfit(amount, dexA, dexB, path);
    const profitEther = ethers.formatEther(profit);
    console.log(`💰 Calculated profit: ${profitEther} ETH`);

    const isProfitable = await contract.isArbitrageProfitable(amount, dexA, dexB, path);
    console.log(`📊 Is profitable: ${isProfitable}`);

    if (parseFloat(profitEther) > 0) {
      const profitPercent = (parseFloat(profitEther) / parseFloat(ethers.formatEther(amount))) * 100;
      console.log(`📈 Profit percentage: ${profitPercent.toFixed(4)}%`);
    }

    console.log('\n🧪 Testing reverse direction...');
    const reversePath = [path[1], path[0]]; // USDC -> USDT
    const reverseProfit = await contract.calculateArbitrageProfit(amount, dexB, dexA, reversePath);
    const reverseProfitEther = ethers.formatEther(reverseProfit);
    console.log(`💰 Reverse profit: ${reverseProfitEther} ETH`);

    const reverseIsProfitable = await contract.isArbitrageProfitable(amount, dexB, dexA, reversePath);
    console.log(`📊 Reverse is profitable: ${reverseIsProfitable}`);

    console.log('\n✅ Contract test completed!');
    
  } catch (error) {
    console.error('❌ Error testing contract:', error);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
