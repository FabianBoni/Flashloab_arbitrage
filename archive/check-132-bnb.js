const { Web3 } = require('web3');

async function checkWithReducedBNB() {
    console.log('💰 FLASHLOAN ANALYSIS MIT 0.132 BNB');
    console.log('='.repeat(45));
    
    // Your actual wallet
    const bnbAmount = 0.132;
    const usdcAmount = 59;
    const bnbPriceUSD = 600;
    
    console.log('📊 IHR WALLET:');
    console.log(`   BNB: ${bnbAmount} (~$${(bnbAmount * bnbPriceUSD).toFixed(2)})`);
    console.log(`   USDC: ${usdcAmount}`);
    console.log(`   Total Value: ~$${(bnbAmount * bnbPriceUSD + usdcAmount).toFixed(2)}`);
    
    // Gas costs for flashloan arbitrage
    const gasPrice = 8; // Gwei
    const flashloanGas = 400000;
    const gasCostBNB = (gasPrice * flashloanGas) / 1e9;
    const gasCostUSD = gasCostBNB * bnbPriceUSD;
    
    console.log('\n⛽ GAS-KOSTEN PRO ARBITRAGE:');
    console.log(`   Gas Cost: ${gasCostBNB.toFixed(6)} BNB (~$${gasCostUSD.toFixed(3)})`);
    
    // Calculate how many trades possible
    const reserveForSafety = 0.01; // Keep 0.01 BNB as safety reserve
    const availableForGas = bnbAmount - reserveForSafety;
    const maxTrades = Math.floor(availableForGas / gasCostBNB);
    
    console.log('\n🔥 IHRE ARBITRAGE-KAPAZITÄT:');
    console.log(`   Verfügbar für Gas: ${availableForGas.toFixed(6)} BNB`);
    console.log(`   Mögliche Trades: ${maxTrades} Flashloan-Arbitrages`);
    console.log(`   Sicherheitsreserve: ${reserveForSafety} BNB`);
    
    console.log('\n⚡ FLASHLOAN PROFIT-SZENARIEN:');
    
    // Different flashloan scenarios with 0.132 BNB
    const scenarios = [
        { amount: 1, token: 'WBNB', profit: 3 },
        { amount: 2, token: 'WBNB', profit: 4 },
        { amount: 3, token: 'WBNB', profit: 5 },
        { amount: 1000, token: 'USDT', profit: 3 },
        { amount: 2000, token: 'USDT', profit: 4 },
        { amount: 3000, token: 'USDT', profit: 5 }
    ];
    
    const flashloanFee = 0.25; // 0.25%
    
    scenarios.forEach(scenario => {
        const tradeValueUSD = scenario.amount * (scenario.token === 'WBNB' ? 600 : 1);
        const grossProfitUSD = tradeValueUSD * (scenario.profit / 100);
        const flashloanFeeUSD = tradeValueUSD * (flashloanFee / 100);
        const netProfitUSD = grossProfitUSD - flashloanFeeUSD - gasCostUSD;
        const netProfitBNB = netProfitUSD / bnbPriceUSD;
        
        const status = netProfitUSD > 5 ? '🔥 EXCELLENT' : netProfitUSD > 0 ? '✅ PROFITABLE' : '❌ LOSS';
        
        console.log(`\n💡 ${scenario.amount} ${scenario.token} @ ${scenario.profit}% Profit:`);
        console.log(`   Trade Value: $${tradeValueUSD.toLocaleString()}`);
        console.log(`   Gross Profit: $${grossProfitUSD.toFixed(2)}`);
        console.log(`   Fees & Gas: $${(flashloanFeeUSD + gasCostUSD).toFixed(2)}`);
        console.log(`   NET PROFIT: $${netProfitUSD.toFixed(2)} (${netProfitBNB.toFixed(6)} BNB) ${status}`);
    });
    
    console.log('\n🎯 RISIKO-ANALYSE:');
    console.log(`   Worst Case: ${maxTrades} fehlgeschlagene Trades = -${(maxTrades * gasCostBNB).toFixed(6)} BNB`);
    console.log(`   Best Case: 1 erfolgreicher 5% Trade = +$83+ Profit`);
    console.log(`   Break-Even: 1 erfolgreicher Trade deckt ~${Math.ceil(gasCostBNB / 0.01)} fehlgeschlagene ab`);
    
    console.log('\n💰 REALISTISCHE GEWINN-ERWARTUNGEN:');
    
    // Conservative success rate analysis
    const successRates = [5, 10, 20]; // 5%, 10%, 20% success rate
    
    successRates.forEach(rate => {
        const successful = Math.floor(maxTrades * rate / 100);
        const failed = maxTrades - successful;
        
        if (successful > 0) {
            const avgProfitPerSuccess = 50; // Conservative $50 per successful trade
            const totalProfit = successful * avgProfitPerSuccess;
            const totalGasCost = maxTrades * gasCostUSD;
            const netResult = totalProfit - totalGasCost;
            
            console.log(`\n📈 Bei ${rate}% Erfolgsrate (${successful}/${maxTrades} Trades):`);
            console.log(`   Erfolgreiche Trades: ${successful} x $${avgProfitPerSuccess} = $${totalProfit}`);
            console.log(`   Gesamte Gas-Kosten: $${totalGasCost.toFixed(2)}`);
            console.log(`   NET ERGEBNIS: $${netResult.toFixed(2)} ${netResult > 0 ? '✅' : '❌'}`);
        }
    });
    
    console.log('\n🚀 STRATEGIE-EMPFEHLUNGEN:');
    console.log('   1. Focus auf 4-5% Opportunities (höhere Erfolgsrate)');
    console.log('   2. Verwenden Sie 1-3 WBNB Flashloans (überschaubare Größe)');
    console.log('   3. Seien Sie selektiv - nicht jede Opportunity ausführen');
    console.log('   4. Überwachen Sie Gas-Verbrauch genau');
    console.log('   5. Nach ersten Erfolgen: Gewinne reinvestieren');
    
    console.log('\n✅ FAZIT MIT 0.132 BNB:');
    
    if (maxTrades >= 35) {
        console.log('   🎯 AUSREICHEND für Flashloan-Arbitrage!');
        console.log(`   ⚡ ${maxTrades} Arbitrage-Versuche möglich`);
        console.log('   💰 Ein erfolgreicher Trade kann Wochen-Gewinn bringen');
        console.log('   🔒 Risiko begrenzt auf Gas-Kosten');
        console.log('   ✅ EMPFEHLUNG: STARTEN SIE DEN BOT!');
    } else {
        console.log('   ⚠️  Knapp, aber machbar');
        console.log('   💡 Seien Sie sehr selektiv bei Opportunities');
        console.log('   🎯 Focus auf höhere Profit-Margins (5%+)');
    }
    
    console.log('\n🎉 WICHTIG: Flashloans funktionieren auch mit weniger BNB!');
    console.log('    Sie können immer noch $1000+ Kapital leihen und handeln!');
}

checkWithReducedBNB();
