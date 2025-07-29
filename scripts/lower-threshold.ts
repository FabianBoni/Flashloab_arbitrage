import { ethers } from 'hardhat';

const CONTRACT_ADDRESS = '0x0FA4cab40651cfcb308C169fd593E92F2f0cf805';

async function main() {
  const [deployer] = await ethers.getSigners();
  
  const abi = [
    'function updateMinProfitThreshold(uint256 newThreshold) external',
    'function minProfitThreshold() external view returns (uint256)'
  ];
  
  const contract = new ethers.Contract(CONTRACT_ADDRESS, abi, deployer);
  
  console.log('🔧 Current profit threshold...');
  const currentThreshold = await contract.minProfitThreshold();
  console.log(`Current: ${ethers.formatEther(currentThreshold)} BNB`);
  
  // Lower threshold for testing
  const newThreshold = ethers.parseEther('0.0001'); // 0.0001 BNB (~$0.06)
  console.log(`Setting to: ${ethers.formatEther(newThreshold)} BNB`);
  
  await contract.updateMinProfitThreshold(newThreshold);
  console.log('✅ Profit threshold lowered for testing!');
  
  console.log('\n💡 Now restart the bot to test with lower threshold:');
  console.log('   npm start');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
