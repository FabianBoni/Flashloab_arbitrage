import { ethers } from 'hardhat';

const CONTRACT_ADDRESS = '0xDf9b5f44edae76901a6190496467002aEFCEf677';
const ABI = [
  'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
  'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)'
];

async function main() {
  const [deployer] = await ethers.getSigners();
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, deployer);
  
  console.log('🧪 Testing different token pairs...\n');

  // Test WBNB/USDT pair (very liquid)
  const amount = ethers.parseEther('1'); // 1 token
  
  console.log('🔍 Test 1: WBNB -> USDT');
  const wbnbUsdtPath = [
    '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', // WBNB
    '0x55d398326f99059fF775485246999027B3197955'  // USDT
  ];
  
  try {
    const profit1 = await contract.calculateArbitrageProfit(amount, 'Biswap', 'PancakeSwap V2', wbnbUsdtPath);
    console.log(`💰 Profit: ${ethers.formatEther(profit1)} ETH`);
    
    const isProfitable1 = await contract.isArbitrageProfitable(amount, 'Biswap', 'PancakeSwap V2', wbnbUsdtPath);
    console.log(`📊 Is profitable: ${isProfitable1}\n`);
  } catch (error: any) {
    console.log(`❌ Error: ${error.message}\n`);
  }

  console.log('🔍 Test 2: USDT -> WBNB');
  const usdtWbnbPath = [
    '0x55d398326f99059fF775485246999027B3197955', // USDT
    '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'  // WBNB
  ];
  
  try {
    const profit2 = await contract.calculateArbitrageProfit(amount, 'PancakeSwap V2', 'Biswap', usdtWbnbPath);
    console.log(`💰 Profit: ${ethers.formatEther(profit2)} ETH`);
    
    const isProfitable2 = await contract.isArbitrageProfitable(amount, 'PancakeSwap V2', 'Biswap', usdtWbnbPath);
    console.log(`📊 Is profitable: ${isProfitable2}\n`);
  } catch (error: any) {
    console.log(`❌ Error: ${error.message}\n`);
  }

  console.log('🔍 Test 3: USDT -> USDC (smaller amount)');
  const smallAmount = ethers.parseEther('10'); // 10 tokens
  const usdtUsdcPath = [
    '0x55d398326f99059fF775485246999027B3197955', // USDT
    '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d'  // USDC
  ];
  
  try {
    const profit3 = await contract.calculateArbitrageProfit(smallAmount, 'Biswap', 'PancakeSwap V2', usdtUsdcPath);
    console.log(`💰 Profit: ${ethers.formatEther(profit3)} ETH`);
    
    const isProfitable3 = await contract.isArbitrageProfitable(smallAmount, 'Biswap', 'PancakeSwap V2', usdtUsdcPath);
    console.log(`📊 Is profitable: ${isProfitable3}\n`);
  } catch (error: any) {
    console.log(`❌ Error: ${error.message}\n`);
  }

  console.log('✅ Testing completed!');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
