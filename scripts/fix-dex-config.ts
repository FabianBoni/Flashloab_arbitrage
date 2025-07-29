import { ethers } from 'hardhat';

const CONTRACT_ADDRESS = '0xDf9b5f44edae76901a6190496467002aEFCEf677';

async function main() {
  const [deployer] = await ethers.getSigners();
  
  const abi = [
    'function updateDEXConfig(string calldata dexName, address router, bool isActive, uint256 fee) external',
    'function dexConfigs(string memory) external view returns (address router, bool isActive, uint256 fee)'
  ];
  
  const contract = new ethers.Contract(CONTRACT_ADDRESS, abi, deployer);
  
  console.log('🔧 Reconfiguring DEXes with correct names...');
  
  // Configure PancakeSwap V2
  await contract.updateDEXConfig(
    'PancakeSwap V2',
    '0x10ED43C718714eb63d5aA57B78B54704E256024E',
    true,
    25
  );
  console.log('✅ PancakeSwap V2 configured');
  
  // Configure Biswap
  await contract.updateDEXConfig(
    'Biswap',
    '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
    true,
    10
  );
  console.log('✅ Biswap configured');
  
  // Verify configurations
  console.log('\n🔍 Verifying DEX configurations...');
  
  const pancakeConfig = await contract.dexConfigs('PancakeSwap V2');
  console.log(`PancakeSwap V2: ${pancakeConfig.router}, Active: ${pancakeConfig.isActive}, Fee: ${pancakeConfig.fee}`);
  
  const biswapConfig = await contract.dexConfigs('Biswap');
  console.log(`Biswap: ${biswapConfig.router}, Active: ${biswapConfig.isActive}, Fee: ${biswapConfig.fee}`);
  
  console.log('\n✅ DEX reconfiguration completed!');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
