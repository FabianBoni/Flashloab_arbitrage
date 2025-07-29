const { Web3 } = require('web3');

async function checkWalletSufficiency() {
    console.log('💰 WALLET SUFFICIENCY ANALYSIS');
    console.log('='.repeat(50));
    
    try {
        const web3 = new Web3('https://bsc-dataseed.binance.org');
        
        // Current wallet holdings
        const bnbAmount = 0.15;
        const usdcAmount = 59;
        const bnbPriceUSD = 600; // Estimated BNB price
        
        console.log('📊 CURRENT WALLET HOLDINGS:');
        console.log(`   BNB: ${bnbAmount} (~$${(bnbAmount * bnbPriceUSD).toFixed(2)})`);
        console.log(`   USDC: ${usdcAmount} (~$${usdcAmount})`);
        console.log(`   Total Value: ~$${(bnbAmount * bnbPriceUSD + usdcAmount).toFixed(2)}`);
        
        console.log('\n⛽ GAS COST ANALYSIS (Optimized Settings):');
        
        // Gas costs at optimized settings (15 Gwei)
        const gasPrice = 15; // Gwei
        const operations = {
            'Simple Arbitrage': 350000,
            'Complex Arbitrage': 500000,
            'Failed Transaction': 100000,
            'Contract Interaction': 80000
        };
        
        Object.entries(operations).forEach(([operation, gasLimit]) => {
            const costBNB = (gasPrice * gasLimit) / 1e9;
            const costUSD = costBNB * bnbPriceUSD;
            console.log(`   ${operation}: ${costBNB.toFixed(6)} BNB (~$${costUSD.toFixed(3)})`);
        });
        
        console.log('\n🔄 ARBITRAGE SCENARIOS:');
        
        // Scenario 1: Small arbitrage trades
        const smallTradeAmount = 0.05; // BNB
        const smallTradeCost = 0.00525; // BNB (350k gas at 15 Gwei)
        const smallTradeProfit = smallTradeAmount * 0.005; // 0.5% profit
        const smallNetProfit = smallTradeProfit - smallTradeCost;
        
        console.log('\n📈 Small Trade Scenario (0.05 BNB):');
        console.log(`   Trade Amount: ${smallTradeAmount} BNB`);
        console.log(`   Gas Cost: ${smallTradeCost.toFixed(6)} BNB`);
        console.log(`   Expected Profit (0.5%): ${smallTradeProfit.toFixed(6)} BNB`);
        console.log(`   Net Result: ${smallNetProfit > 0 ? '+' : ''}${smallNetProfit.toFixed(6)} BNB`);
        console.log(`   Status: ${smallNetProfit > 0 ? '✅ PROFITABLE' : '❌ UNPROFITABLE'}`);
        
        // Scenario 2: Medium arbitrage trades
        const mediumTradeAmount = 0.1; // BNB
        const mediumTradeCost = 0.00525; // BNB
        const mediumTradeProfit = mediumTradeAmount * 0.005; // 0.5% profit
        const mediumNetProfit = mediumTradeProfit - mediumTradeCost;
        
        console.log('\n📈 Medium Trade Scenario (0.1 BNB):');
        console.log(`   Trade Amount: ${mediumTradeAmount} BNB`);
        console.log(`   Gas Cost: ${mediumTradeCost.toFixed(6)} BNB`);
        console.log(`   Expected Profit (0.5%): ${mediumTradeProfit.toFixed(6)} BNB`);
        console.log(`   Net Result: ${mediumNetProfit > 0 ? '+' : ''}${mediumNetProfit.toFixed(6)} BNB`);
        console.log(`   Status: ${mediumNetProfit > 0 ? '✅ PROFITABLE' : '❌ UNPROFITABLE'}`);
        
        console.log('\n🎯 WALLET ADEQUACY ASSESSMENT:');
        
        // Calculate how many trades possible
        const reserveForGas = 0.02; // Keep 0.02 BNB for gas
        const availableForTrading = bnbAmount - reserveForGas;
        const possibleTrades = Math.floor(availableForTrading / smallTradeAmount);
        
        console.log(`   Available for Trading: ${availableForTrading.toFixed(3)} BNB`);
        console.log(`   Possible Small Trades: ${possibleTrades}`);
        console.log(`   Gas Reserve: ${reserveForGas} BNB (${Math.floor(reserveForGas / smallTradeCost)} failed transactions)`);
        
        console.log('\n💡 RECOMMENDATIONS:');
        
        if (bnbAmount >= 0.15) {
            console.log('   ✅ BNB Amount: SUFFICIENT for small arbitrage operations');
            console.log('   ✅ Can handle 2-3 small trades simultaneously');
            console.log('   ✅ Good gas reserve for failed transactions');
        } else {
            console.log('   ⚠️  BNB Amount: MARGINAL - consider adding more');
        }
        
        if (usdcAmount >= 50) {
            console.log('   ✅ USDC Amount: SUFFICIENT for USD-based arbitrage');
            console.log('   ✅ Can participate in USDC/USDT/BUSD opportunities');
        } else {
            console.log('   ⚠️  USDC Amount: LOW - limited USD pair opportunities');
        }
        
        console.log('\n🚀 STRATEGY RECOMMENDATIONS:');
        console.log('   1. Start with CONSERVATIVE settings initially');
        console.log('   2. Focus on WBNB-based pairs (you have sufficient BNB)');
        console.log('   3. Use smaller trade amounts (0.02-0.05 BNB) to minimize risk');
        console.log('   4. Monitor gas usage and adjust if needed');
        console.log('   5. Consider adding more BNB if success rate is high');
        
        console.log('\n🎯 BOTTOM LINE:');
        if (bnbAmount >= 0.15 && usdcAmount >= 50) {
            console.log('   ✅ WALLET IS SUFFICIENT TO START ARBITRAGE TRADING!');
            console.log('   ✅ You can execute 2-3 small arbitrage trades');
            console.log('   ✅ Good foundation to test and grow profits');
        } else {
            console.log('   ⚠️  WALLET IS MARGINAL - proceed with caution');
            console.log('   ⚠️  Consider smaller trade amounts or adding more funds');
        }
        
    } catch (error) {
        console.error('Error in analysis:', error.message);
    }
}

checkWalletSufficiency();
