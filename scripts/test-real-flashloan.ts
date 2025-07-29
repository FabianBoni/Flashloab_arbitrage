import { ethers } from 'hardhat';

const CONTRACT_ADDRESS = '0x0FA4cab40651cfcb308C169fd593E92F2f0cf805';
const ABI = [
  'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
  'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)',
  'function executeArbitrage(address asset, uint256 amount, string calldata dexA, string calldata dexB, address[] calldata path, uint256 minProfit) external'
];

async function main() {
  const [deployer] = await ethers.getSigners();
  const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, deployer);
  
  console.log('🧪 Testing REAL PancakeSwap Flashloan Arbitrage...');
  console.log(`📝 Contract: ${CONTRACT_ADDRESS}`);
  console.log(`👤 Wallet: ${deployer.address}\n`);

  // Test with WBNB/USDT pair (most liquid on BSC)
  const amount = ethers.parseEther('0.1'); // 0.1 WBNB
  const path = [
    '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', // WBNB
    '0x55d398326f99059fF775485246999027B3197955'  // USDT
  ];

  console.log('🔍 Testing WBNB -> USDT arbitrage opportunity...');
  console.log(`   Amount: ${ethers.formatEther(amount)} WBNB`);
  console.log(`   DEX A: Biswap`);
  console.log(`   DEX B: PancakeSwap V2`);

  try {
    // Check profitability
    const profit = await contract.calculateArbitrageProfit(amount, 'Biswap', 'PancakeSwap V2', path);
    const profitEther = ethers.formatEther(profit);
    console.log(`💰 Calculated profit: ${profitEther} BNB`);

    const isProfitable = await contract.isArbitrageProfitable(amount, 'Biswap', 'PancakeSwap V2', path);
    console.log(`📊 Is profitable: ${isProfitable}`);

    if (parseFloat(profitEther) > 0) {
      const profitPercent = (parseFloat(profitEther) / parseFloat(ethers.formatEther(amount))) * 100;
      console.log(`📈 Profit percentage: ${profitPercent.toFixed(4)}%`);
      
      if (isProfitable && profitPercent > 0.1) {
        console.log('\n🚀 OPPORTUNITY DETECTED! Attempting real flashloan arbitrage...');
        
        const minProfit = ethers.parseEther('0.001'); // 0.001 BNB minimum
        
        // Execute REAL arbitrage with flashloan
        const tx = await contract.executeArbitrage(
          path[0], // WBNB
          amount,
          'Biswap',
          'PancakeSwap V2',
          path,
          minProfit,
          {
            gasLimit: 1500000, // 1.5M gas
            gasPrice: ethers.parseUnits('3', 'gwei')
          }
        );
        
        console.log(`📝 Transaction sent: ${tx.hash}`);
        console.log('⏳ Waiting for confirmation...');
        
        const receipt = await tx.wait();
        
        if (receipt && receipt.status === 1) {
          console.log('🎉 REAL FLASHLOAN ARBITRAGE EXECUTED SUCCESSFULLY!');
          console.log(`📝 Transaction: ${tx.hash}`);
          console.log(`⛽ Gas used: ${receipt.gasUsed}`);
          
          // Parse events for actual profit
          for (const log of receipt.logs) {
            try {
              const parsed = contract.interface.parseLog({
                topics: log.topics as string[],
                data: log.data,
              });
              
              if (parsed && parsed.name === 'ArbitrageExecuted') {
                console.log(`💰 Actual profit: ${ethers.formatEther(parsed.args.profit)} BNB`);
              } else if (parsed && parsed.name === 'FlashloanExecuted') {
                console.log(`🏦 Flashloan: ${ethers.formatEther(parsed.args.amount)} ${parsed.args.token}`);
                console.log(`💸 Fee: ${ethers.formatEther(parsed.args.fee)} tokens`);
              }
            } catch (error) {
              // Ignore parsing errors
            }
          }
        } else {
          console.log('❌ Transaction failed');
        }
      } else {
        console.log('⚠️  Profit too low for execution');
      }
    }

    // Test reverse direction
    console.log('\n🔄 Testing reverse direction...');
    const reversePath = [path[1], path[0]]; // USDT -> WBNB
    const reverseAmount = ethers.parseEther('60'); // 60 USDT
    
    const reverseProfit = await contract.calculateArbitrageProfit(reverseAmount, 'PancakeSwap V2', 'Biswap', reversePath);
    console.log(`💰 Reverse profit: ${ethers.formatEther(reverseProfit)} BNB`);

  } catch (error: any) {
    console.error('❌ Error testing contract:', error.message);
  }

  console.log('\n✅ Real flashloan test completed!');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
