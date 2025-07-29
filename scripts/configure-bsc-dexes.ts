import { ethers } from 'hardhat';

async function main() {
  console.log('🔧 Configuring BSC DEXes...');
  
  const contractAddress = '0xf8a1AFAF447891d26d271F471A2962db8eA45843';
  const abi = [
    'function updateDEXConfig(string calldata name, address router, bool isActive) external',
    'function dexConfigs(string memory name) external view returns (address router, string memory name, bool isActive)',
    'function owner() external view returns (address)'
  ];
  
  const [signer] = await ethers.getSigners();
  const contract = new ethers.Contract(contractAddress, abi, signer);
  
  console.log('👤 Contract Owner:', await contract.owner());
  console.log('👤 Current Signer:', signer.address);
  
  // Configure PancakeSwap V2 for BSC
  console.log('📝 Adding PancakeSwap V2...');
  const pancakeRouter = '0x10ED43C718714eb63d5aA57B78B54704E256024E';
  let tx = await contract.updateDEXConfig('PancakeSwap V2', pancakeRouter, true, {
    gasLimit: 100000,
    gasPrice: ethers.parseUnits('5', 'gwei')
  });
  await tx.wait();
  console.log('✅ PancakeSwap V2 configured');
  
  // Configure Biswap for BSC
  console.log('📝 Adding Biswap...');
  const biswapRouter = '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8';
  tx = await contract.updateDEXConfig('Biswap', biswapRouter, true, {
    gasLimit: 100000,
    gasPrice: ethers.parseUnits('5', 'gwei')
  });
  await tx.wait();
  console.log('✅ Biswap configured');
  
  // Verify configurations
  console.log('\n🔍 Verifying DEX configurations...');
  const pancakeConfig = await contract.dexConfigs('PancakeSwap V2');
  console.log('PancakeSwap V2:', {
    router: pancakeConfig.router,
    name: pancakeConfig.name,
    isActive: pancakeConfig.isActive
  });
  
  const biswapConfig = await contract.dexConfigs('Biswap');
  console.log('Biswap:', {
    router: biswapConfig.router,
    name: biswapConfig.name,
    isActive: biswapConfig.isActive
  });
  
  console.log('\n✅ BSC DEX configuration completed!');
}

main().catch(console.error);
