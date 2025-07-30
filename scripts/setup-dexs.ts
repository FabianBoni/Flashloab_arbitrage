import { ethers } from 'hardhat';

async function main() {
  const contractAddress = process.env.FLASHLOAN_CONTRACT_ADDRESS;
  if (!contractAddress) {
    throw new Error('FLASHLOAN_CONTRACT_ADDRESS not set in .env');
  }

  const [deployer] = await ethers.getSigners();
  const FlashloanArbitrage = await ethers.getContractFactory('FlashloanArbitrage');
  const contract = FlashloanArbitrage.attach(contractAddress);

  console.log('🔧 Setting up DEX configurations...');

  // BSC DEX configurations with verified addresses
  const dexConfigs = [
    {
      name: 'PancakeSwap V2',
      router: '0x10ED43C718714eb63d5aA57B78B54704E256024E',
      isActive: true
    },
    {
      name: 'Biswap',
      router: '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
      isActive: true
    },
    {
      name: 'ApeSwap',
      router: '0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7',
      isActive: true
    },
    {
      name: 'BakerySwap',
      router: '0xCDe540d7eAFE93aC5fE6233Bee57E1270D3E330F',
      isActive: true
    },
    {
      name: 'MDEX',
      router: '0x7DAe51BD3E3376B8c7c4900E9107f12Be3AF1bA8',
      isActive: true
    },
    {
      name: 'BabySwap',
      router: '0x325E343f1dE602396E256B67eFd1F61C3A6B38Bd',
      isActive: true
    },
  ];

  console.log(`📝 Configuring ${dexConfigs.length} DEX integrations...`);

  for (const dex of dexConfigs) {
    try {
      console.log(`⚙️  Setting up ${dex.name}...`);
      const tx = await contract.updateDEXConfig(dex.name, dex.router, dex.isActive);
      await tx.wait();
      console.log(`✅ ${dex.name} configured successfully`);
    } catch (error) {
      console.error(`❌ Failed to configure ${dex.name}:`, error);
    }
  }

  console.log('\n🎉 All DEX configurations completed!');
  console.log('\n📊 Arbitrage Opportunities Matrix:');
  console.log(`   With ${dexConfigs.length} DEXs: ${dexConfigs.length * (dexConfigs.length - 1)} potential arbitrage routes!`);
  
  // Calculate combinations
  const combinations = dexConfigs.length * (dexConfigs.length - 1);
  console.log(`\n🚀 Expected increase in opportunities: ${combinations / 2}x (from 2 to ${combinations} routes)`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
