import { ethers } from 'hardhat';

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with the account:', deployer.address);

  // Chain-specific configurations
  const chainConfigs = {
    // BSC Mainnet
    56: {
      aavePool: '0x0000000000000000000000000000000000000000', // No Aave on BSC
      weth: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', // WBNB
      name: 'BSC'
    },
    // Ethereum Mainnet
    1: {
      aavePool: '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2', // Aave V3 Pool
      weth: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', // WETH
      name: 'Ethereum'
    },
    // Polygon
    137: {
      aavePool: '0x794a61358D6845594F94dc1DB02A252b5b4814aD', // Aave V3 Pool
      weth: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', // WMATIC
      name: 'Polygon'
    },
    // Arbitrum
    42161: {
      aavePool: '0x794a61358D6845594F94dc1DB02A252b5b4814aD', // Aave V3 Pool
      weth: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1', // WETH
      name: 'Arbitrum'
    }
  };

  // Get current network
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log(`Deploying to chain ID: ${chainId}`);
  
  const config = chainConfigs[chainId as keyof typeof chainConfigs];
  if (!config) {
    throw new Error(`Chain ID ${chainId} not supported`);
  }
  
  console.log(`Deploying to ${config.name}`);
  console.log(`Aave Pool: ${config.aavePool}`);
  console.log(`WETH/Native: ${config.weth}`);

  // Deploy the contract with lower gas settings for BSC
  const UniversalFlashloanArbitrage = await ethers.getContractFactory('UniversalFlashloanArbitrage');
  const contract = await UniversalFlashloanArbitrage.deploy(config.aavePool, config.weth, {
    gasLimit: 3000000, // 3M gas limit
    gasPrice: ethers.parseUnits('3', 'gwei') // 3 gwei - very low for BSC
  });

  await contract.waitForDeployment();
  const contractAddress = await contract.getAddress();

  console.log(`✅ UniversalFlashloanArbitrage deployed to: ${contractAddress}`);

  // Configure DEXes based on chain
  if (chainId === 56) { // BSC
    console.log('🔧 Configuring BSC DEXes...');
    
    // PancakeSwap V2
    await contract.updateDEXConfig(
      'PancakeSwap V2',
      '0x10ED43C718714eb63d5aA57B78B54704E256024E',
      true,
      25 // 0.25% fee
    );
    
    // Biswap
    await contract.updateDEXConfig(
      'Biswap',
      '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
      true,
      10 // 0.1% fee
    );
    
    console.log('✅ BSC DEXes configured');
    
  } else if (chainId === 1) { // Ethereum
    console.log('🔧 Configuring Ethereum DEXes...');
    
    // Uniswap V2
    await contract.updateDEXConfig(
      'Uniswap V2',
      '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
      true,
      30 // 0.3% fee
    );
    
    // SushiSwap
    await contract.updateDEXConfig(
      'SushiSwap',
      '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
      true,
      30 // 0.3% fee
    );
    
    console.log('✅ Ethereum DEXes configured');
    
  } else if (chainId === 137) { // Polygon
    console.log('🔧 Configuring Polygon DEXes...');
    
    // QuickSwap
    await contract.updateDEXConfig(
      'QuickSwap',
      '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
      true,
      30 // 0.3% fee
    );
    
    // SushiSwap
    await contract.updateDEXConfig(
      'SushiSwap',
      '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
      true,
      30 // 0.3% fee
    );
    
    console.log('✅ Polygon DEXes configured');
    
  } else if (chainId === 42161) { // Arbitrum
    console.log('🔧 Configuring Arbitrum DEXes...');
    
    // Uniswap V3
    await contract.updateDEXConfig(
      'Uniswap V3',
      '0xE592427A0AEce92De3Edee1F18E0157C05861564',
      true,
      30 // 0.3% fee
    );
    
    // SushiSwap
    await contract.updateDEXConfig(
      'SushiSwap',
      '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
      true,
      30 // 0.3% fee
    );
    
    console.log('✅ Arbitrum DEXes configured');
  }

  // Set deployer as authorized caller
  await contract.setAuthorizedCaller(deployer.address, true);
  console.log(`✅ Authorized caller set: ${deployer.address}`);

  console.log('\n📋 Deployment Summary:');
  console.log(`   Network: ${config.name} (Chain ID: ${chainId})`);
  console.log(`   Contract: ${contractAddress}`);
  console.log(`   Deployer: ${deployer.address}`);
  console.log(`   Gas Used: ${(await contract.deploymentTransaction()?.wait())?.gasUsed}`);

  // Save deployment info
  const deploymentInfo = {
    chainId,
    network: config.name,
    contractAddress,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    aavePool: config.aavePool,
    weth: config.weth
  };

  console.log('\n💾 Deployment info:', JSON.stringify(deploymentInfo, null, 2));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
