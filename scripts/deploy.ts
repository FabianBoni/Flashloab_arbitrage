import { ethers } from 'hardhat';

async function main() {
  console.log('🚀 Deploying BSCFlashloanArbitrageV2 contract (Real Flashloans)...');

  // Get the ContractFactory and Signers
  const [deployer] = await ethers.getSigners();
  console.log('📝 Deploying contracts with account:', deployer.address);

  // Check deployer balance
  const balance = await deployer.provider.getBalance(deployer.address);
  console.log('💰 Account balance:', ethers.formatEther(balance), 'ETH');

  // Deploy the BSC V2 contract with real flashloans
  const BSCFlashloanArbitrageV2 = await ethers.getContractFactory('BSCFlashloanArbitrageV2');
  const flashloanArbitrage = await BSCFlashloanArbitrageV2.deploy();

  await flashloanArbitrage.waitForDeployment();
  const contractAddress = await flashloanArbitrage.getAddress();

  console.log('✅ BSCFlashloanArbitrageV2 deployed to:', contractAddress);

  // Verify deployment
  console.log('🔍 Verifying contract deployment...');
  const owner = await flashloanArbitrage.owner();
  console.log('👤 Contract owner:', owner);
  console.log('🏪 Contract verified successfully!');

  // Save deployment information
  const deploymentInfo = {
    network: await ethers.provider.getNetwork(),
    contractAddress: contractAddress,
    deployer: deployer.address,
    blockNumber: await ethers.provider.getBlockNumber(),
    timestamp: new Date().toISOString(),
    txHash: flashloanArbitrage.deploymentTransaction()?.hash,
  };

  console.log('\n📄 Deployment Summary:');
  console.log('   Network:', deploymentInfo.network.name);
  console.log('   Contract Address:', deploymentInfo.contractAddress);
  console.log('   Deployer:', deploymentInfo.deployer);
  console.log('   Block Number:', deploymentInfo.blockNumber);
  console.log('   Transaction Hash:', deploymentInfo.txHash);

  return contractAddress;
}

main()
  .then((address) => {
    console.log(`\n🎉 Deployment completed successfully!`);
    console.log(`📋 Contract Address: ${address}`);
    process.exit(0);
  })
  .catch((error) => {
    console.error('💥 Deployment failed:', error);
    process.exit(1);
  });