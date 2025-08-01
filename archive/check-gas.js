const { Web3 } = require('web3');

async function checkBSCGasPrice() {
    try {
        const web3 = new Web3('https://bsc-dataseed.binance.org');
        
        // Get current gas price
        const gasPrice = await web3.eth.getGasPrice();
        const gasPriceGwei = web3.utils.fromWei(gasPrice, 'gwei');
        
        console.log('=== BSC Transaktionskosten Analyse ===');
        console.log(`Aktueller Gas Preis: ${gasPriceGwei} Gwei`);
        console.log(`Ihr Max Gas Preis: 10 Gwei`);
        
        // Calculate costs for different transaction types
        const gasLimits = {
            'Einfacher Transfer': 21000,
            'Token Transfer (ERC-20)': 65000,
            'DEX Swap': 150000,
            'Flashloan Arbitrage': 300000,
            'Komplexe DeFi Operation': 500000
        };
        
        console.log('\n=== Geschätzte Transaktionskosten (bei aktuellem Gas Preis) ===');
        Object.entries(gasLimits).forEach(([operation, gasLimit]) => {
            const costWei = BigInt(gasPrice) * BigInt(gasLimit);
            const costBNB = web3.utils.fromWei(costWei.toString(), 'ether');
            const costUSD = parseFloat(costBNB) * 600; // Angenommen BNB = $600
            console.log(`${operation}: ${costBNB} BNB (~$${costUSD.toFixed(4)})`);
        });
        
        console.log('\n=== Transaktionskosten bei Ihrem Max Gas Preis (10 Gwei) ===');
        const yourGasPrice = web3.utils.toWei('10', 'gwei');
        Object.entries(gasLimits).forEach(([operation, gasLimit]) => {
            const costWei = BigInt(yourGasPrice) * BigInt(gasLimit);
            const costBNB = web3.utils.fromWei(costWei.toString(), 'ether');
            const costUSD = parseFloat(costBNB) * 600;
            console.log(`${operation}: ${costBNB} BNB (~$${costUSD.toFixed(4)})`);
        });
        
        // Recommendation
        console.log('\n=== Empfehlung ===');
        if (parseFloat(gasPriceGwei) <= 10) {
            console.log('✅ Ihre Gas-Einstellungen sind angemessen für das aktuelle Netzwerk');
        } else {
            console.log(`⚠️  Aktueller Gas Preis (${gasPriceGwei} Gwei) ist höher als Ihr Maximum (10 Gwei)`);
            console.log('Erwägen Sie eine Erhöhung auf:', Math.ceil(parseFloat(gasPriceGwei) * 1.1), 'Gwei');
        }
        
    } catch (error) {
        console.error('Fehler beim Abrufen der Gas-Daten:', error.message);
    }
}

checkBSCGasPrice();
