import { ethers } from 'hardhat';

const TOKENS = {
  BNB: {
    symbol: 'BNB',
    address: '0x0000000000000000000000000000000000000000', // Native BNB
    decimals: 18
  },
  WBNB: {
    symbol: 'WBNB',
    address: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
    decimals: 18
  },
  USDT: {
    symbol: 'USDT',
    address: '0x55d398326f99059fF775485246999027B3197955',
    decimals: 18
  },
  USDC: {
    symbol: 'USDC',
    address: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
    decimals: 18
  },
  BUSD: {
    symbol: 'BUSD',
    address: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
    decimals: 18
  }
};

async function main() {
  const [deployer] = await ethers.getSigners();
  const walletAddress = deployer.address;
  
  console.log('🔍 Checking wallet balances...');
  console.log(`👤 Wallet: ${walletAddress}\n`);

  // Check native BNB balance
  const bnbBalance = await ethers.provider.getBalance(walletAddress);
  const bnbFormatted = ethers.formatEther(bnbBalance);
  console.log(`💰 Native BNB: ${bnbFormatted} BNB`);
  
  const bnbUSD = parseFloat(bnbFormatted) * 650; // Approximate BNB price
  console.log(`💵 BNB Value: ~$${bnbUSD.toFixed(2)}\n`);

  // ERC-20 ABI for balance checking
  const erc20Abi = [
    'function balanceOf(address owner) view returns (uint256)',
    'function symbol() view returns (string)',
    'function decimals() view returns (uint8)'
  ];

  // Check token balances
  for (const [key, token] of Object.entries(TOKENS)) {
    if (token.address === '0x0000000000000000000000000000000000000000') continue;
    
    try {
      const contract = new ethers.Contract(token.address, erc20Abi, ethers.provider);
      const balance = await contract.balanceOf(walletAddress);
      const formatted = ethers.formatUnits(balance, token.decimals);
      
      if (parseFloat(formatted) > 0) {
        console.log(`🪙 ${token.symbol}: ${parseFloat(formatted).toFixed(6)} ${token.symbol}`);
        
        // Estimate USD value for stablecoins
        if (['USDT', 'USDC', 'BUSD'].includes(token.symbol)) {
          console.log(`💵 ${token.symbol} Value: ~$${parseFloat(formatted).toFixed(2)}`);
        }
      } else {
        console.log(`⚪ ${token.symbol}: 0 ${token.symbol}`);
      }
    } catch (error) {
      console.log(`❌ ${token.symbol}: Error checking balance`);
    }
  }

  // Calculate total funding
  const totalBNB = parseFloat(bnbFormatted);
  console.log('\n📊 FUNDING STATUS:');
  
  if (totalBNB >= 0.01) {
    console.log('✅ BNB: Sufficient for gas fees');
  } else {
    console.log('⚠️  BNB: Need more for gas fees (minimum 0.01 BNB)');
  }

  // Check if ready for arbitrage
  console.log('\n🎯 ARBITRAGE READINESS:');
  
  const hasGas = totalBNB >= 0.01;
  const needsTokens = true; // Will check USDT/USDC balances
  
  if (hasGas) {
    console.log('✅ Gas fees: Ready');
  } else {
    console.log('❌ Gas fees: Need more BNB');
  }
  
  console.log('⏳ Waiting for token transfers...');
  console.log('\n💡 Transfer checklist:');
  console.log('  1. 0.01+ BNB for gas fees');
  console.log('  2. $100+ USDT for trading capital');
  console.log('  3. Optional: USDC for more opportunities');
  
  console.log('\n🌐 BSCScan: https://bscscan.com/address/' + walletAddress);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
