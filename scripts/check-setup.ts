import { ethers } from 'hardhat';

async function main() {
  console.log('🔍 Checking trading setup...');
  
  const [signer] = await ethers.getSigners();
  const address = signer.address;
  const balance = await signer.provider.getBalance(address);
  
  console.log('👤 Wallet Address:', address);
  console.log('💰 BNB Balance:', ethers.formatEther(balance), 'BNB');
  
  // Check if we have enough for gas (minimum 0.001 BNB recommended)
  const minBalance = ethers.parseEther('0.001');
  if (balance >= minBalance) {
    console.log('✅ Sufficient balance for trading');
  } else {
    console.log('⚠️  Low balance - consider adding more BNB for gas fees');
  }
  
  // Test contract interaction
  const contractAddress = '0xf8a1AFAF447891d26d271F471A2962db8eA45843';
  const abi = [
    'function owner() external view returns (address)',
    'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)'
  ];
  
  try {
    const contract = new ethers.Contract(contractAddress, abi, signer);
    const owner = await contract.owner();
    console.log('🏪 Contract Owner:', owner);
    console.log('✅ Contract is accessible and ready for trading');
  } catch (error) {
    console.log('❌ Contract interaction failed:', error);
  }
}

main().catch(console.error);
