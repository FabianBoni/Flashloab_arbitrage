import { ethers } from 'hardhat';

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('🚀 Deploying REAL PancakeSwap Flashloan Arbitrage Contract...');
  console.log('👤 Deployer:', deployer.address);

  // Get current network
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  if (chainId !== 56) {
    throw new Error('This contract is specifically for BSC (Chain ID 56)');
  }
  
  console.log('✅ Deploying to BSC Mainnet\n');

  // Deploy the real flashloan contract
  const PancakeFlashloanArbitrage = await ethers.getContractFactory('PancakeFlashloanArbitrage');
  const contract = await PancakeFlashloanArbitrage.deploy({
    gasLimit: 3000000,
    gasPrice: ethers.parseUnits('3', 'gwei')
  });

  await contract.waitForDeployment();
  const contractAddress = await contract.getAddress();

  console.log(`🎉 PancakeFlashloanArbitrage deployed to: ${contractAddress}`);

  // Set deployer as authorized caller
  await contract.setAuthorizedCaller(deployer.address, true);
  console.log(`✅ Authorized caller set: ${deployer.address}`);

  // Set a reasonable profit threshold
  const profitThreshold = ethers.parseEther('0.001'); // 0.001 BNB minimum profit
  await contract.updateMinProfitThreshold(profitThreshold);
  console.log(`✅ Profit threshold set: ${ethers.formatEther(profitThreshold)} BNB`);

  console.log('\n📋 Deployment Summary:');
  console.log(`   Network: BSC Mainnet (Chain ID: ${chainId})`);
  console.log(`   Contract: ${contractAddress}`);
  console.log(`   Deployer: ${deployer.address}`);
  console.log(`   Features: Real PancakeSwap Flashloans ✅`);
  console.log(`   Gas Used: ${(await contract.deploymentTransaction()?.wait())?.gasUsed}`);

  // Test the DEX configurations
  console.log('\n🔧 Testing DEX configurations...');
  
  const pancakeConfig = await contract.dexConfigs('PancakeSwap V2');
  console.log(`   PancakeSwap V2: ${pancakeConfig.router}, Active: ${pancakeConfig.isActive}`);
  
  const biswapConfig = await contract.dexConfigs('Biswap');
  console.log(`   Biswap: ${biswapConfig.router}, Active: ${biswapConfig.isActive}`);

  // Save deployment info
  const deploymentInfo = {
    chainId,
    network: 'BSC',
    contractAddress,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    type: 'PancakeFlashloanArbitrage',
    features: ['Real Flashloans', 'BSC Native', 'PancakeSwap Integration']
  };

  console.log('\n💾 Deployment info:', JSON.stringify(deploymentInfo, null, 2));
  
  console.log('\n🚀 Ready for REAL arbitrage trading with flashloans!');
  console.log('💡 Next steps:');
  console.log('   1. Update bot to use new contract address');
  console.log('   2. Fund wallet with trading tokens');
  console.log('   3. Start bot and execute real arbitrage!');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
