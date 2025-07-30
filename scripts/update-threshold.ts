import { ethers } from 'hardhat';

async function main() {
  // Get the deployed contract
  const contractAddress = process.env.FLASHLOAN_CONTRACT_ADDRESS;
  if (!contractAddress) {
    throw new Error('FLASHLOAN_CONTRACT_ADDRESS not set in .env');
  }

  const [deployer] = await ethers.getSigners();
  
  // Get contract instance
  const FlashloanArbitrage = await ethers.getContractFactory('FlashloanArbitrage');
  const contract = FlashloanArbitrage.attach(contractAddress);

  console.log('📊 Current contract configuration:');
  
  // Check current threshold
  const currentThreshold = await contract.minProfitThreshold();
  console.log(`Current minProfitThreshold: ${ethers.formatEther(currentThreshold)} ETH`);
  
  // Set new threshold to 0.001 ETH (~$2-3 USD)
  const newThreshold = ethers.parseEther('0.001');
  console.log(`Setting new minProfitThreshold: ${ethers.formatEther(newThreshold)} ETH`);
  
  const tx = await contract.updateMinProfitThreshold(newThreshold);
  await tx.wait();
  
  console.log('✅ Successfully updated minProfitThreshold');
  console.log(`Transaction hash: ${tx.hash}`);
  
  // Verify the change
  const updatedThreshold = await contract.minProfitThreshold();
  console.log(`✅ Verified new threshold: ${ethers.formatEther(updatedThreshold)} ETH`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
