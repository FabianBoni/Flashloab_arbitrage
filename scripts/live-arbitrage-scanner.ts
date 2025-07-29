import { JsonRpcProvider, Contract, formatEther, parseEther } from 'ethers';
import dotenv from 'dotenv';

dotenv.config();

// Contract ABI for profitability checking
const contractABI = [
    "function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)",
    "function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)"
];

// Router ABI for direct quotes
const routerABI = [
    "function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts)"
];

const BSC_RPC = process.env.BSC_RPC || "https://bsc-dataseed1.binance.org/";
const CONTRACT_ADDRESS = "0x0FA4cab40651cfcb308C169fd593E92F2f0cf805";

// Router addresses
const PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E";
const BISWAP_ROUTER = "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8";

// Token addresses (properly checksummed)
const tokens = {
    WBNB: "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    USDT: "0x55d398326f99059fF775485246999027B3197955",
    BUSD: "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
    USDC: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d"
};

// Trading pairs to check
const pairs = [
    [tokens.WBNB, tokens.USDT],
    [tokens.WBNB, tokens.BUSD],
    [tokens.WBNB, tokens.USDC],
    [tokens.USDT, tokens.BUSD],
    [tokens.USDT, tokens.USDC],
    [tokens.BUSD, tokens.USDC]
];

// Test amounts in ETH (will be converted to appropriate token units)
const testAmounts = [
    parseEther("0.1"),
    parseEther("0.5"),
    parseEther("1.0"),
    parseEther("2.0"),
    parseEther("5.0")
];

async function scanForArbitrageOpportunities() {
    console.log("🔍 LIVE ARBITRAGE OPPORTUNITY SCANNER\n");
    
    const provider = new JsonRpcProvider(BSC_RPC);
    const contract = new Contract(CONTRACT_ADDRESS, contractABI, provider);
    const pancakeRouter = new Contract(PANCAKE_ROUTER, routerABI, provider);
    const biswapRouter = new Contract(BISWAP_ROUTER, routerABI, provider);
    
    console.log("🚀 Starting continuous scan...");
    console.log("Press Ctrl+C to stop\n");
    
    let scanCount = 0;
    
    while (true) {
        scanCount++;
        console.log(`📊 Scan #${scanCount} - ${new Date().toLocaleTimeString()}`);
        
        let foundOpportunities = 0;
        
        try {
            // Check all pairs and amounts
            for (const [tokenA, tokenB] of pairs) {
                for (const amount of testAmounts) {
                    const path = [tokenA, tokenB];
                    const reversePath = [tokenB, tokenA];
                    
                    try {
                        // Check PancakeSwap -> Biswap
                        await checkDirection(
                            "PancakeSwap", "Biswap",
                            pancakeRouter, biswapRouter,
                            contract, path, amount
                        );
                        
                        // Check Biswap -> PancakeSwap
                        await checkDirection(
                            "Biswap", "PancakeSwap",
                            biswapRouter, pancakeRouter,
                            contract, reversePath, amount
                        );
                        
                    } catch (error) {
                        // Skip this pair/amount combination
                        continue;
                    }
                }
            }
            
            if (foundOpportunities === 0) {
                console.log("   No profitable opportunities found");
            }
            
        } catch (error: any) {
            console.log(`   ❌ Scan error: ${error.message}`);
        }
        
        console.log();
        
        // Wait 5 seconds before next scan
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}

async function checkDirection(
    dexAName: string,
    dexBName: string,
    routerA: Contract,
    routerB: Contract,
    arbitrageContract: Contract,
    path: string[],
    amount: bigint
) {
    try {
        // Get quotes from both DEXes
        const amountsA = await routerA.getAmountsOut(amount, path);
        const intermediateAmount = amountsA[amountsA.length - 1];
        
        const reversePath = [path[1], path[0]];
        const amountsB = await routerB.getAmountsOut(intermediateAmount, reversePath);
        const finalAmount = amountsB[amountsB.length - 1];
        
        // Calculate gross profit
        const grossProfit = finalAmount - amount;
        
        if (grossProfit <= 0n) return; // No profit
        
        // Calculate flashloan fee (0.25% for PancakeSwap)
        const flashloanFee = amount * 25n / 10000n;
        const netProfit = grossProfit - flashloanFee;
        
        if (netProfit <= 0n) return; // No net profit
        
        // Calculate profit percentage
        const profitPercent = Number(netProfit * 10000n / amount) / 100;
        
        if (profitPercent < 0.01) return; // Less than 0.01%
        
        // Check with contract
        const contractProfit = await arbitrageContract.calculateArbitrageProfit(
            amount,
            dexAName.toLowerCase(),
            dexBName.toLowerCase(),
            path
        );
        
        const isProfitable = await arbitrageContract.isArbitrageProfitable(
            amount,
            dexAName.toLowerCase(),
            dexBName.toLowerCase(),
            path
        );
        
        // Get token symbols for display
        const tokenSymbols = getTokenSymbols(path);
        
        console.log(`   🎯 OPPORTUNITY FOUND!`);
        console.log(`      Route: ${dexAName} -> ${dexBName}`);
        console.log(`      Pair: ${tokenSymbols[0]}/${tokenSymbols[1]}`);
        console.log(`      Amount: ${formatEther(amount)} ${tokenSymbols[0]}`);
        console.log(`      Gross profit: ${formatEther(grossProfit)} ${tokenSymbols[0]} (${(Number(grossProfit * 10000n / amount) / 100).toFixed(4)}%)`);
        console.log(`      Flashloan fee: ${formatEther(flashloanFee)} ${tokenSymbols[0]}`);
        console.log(`      Net profit: ${formatEther(netProfit)} ${tokenSymbols[0]} (${profitPercent.toFixed(4)}%)`);
        console.log(`      Contract profit: ${formatEther(contractProfit)} ${tokenSymbols[0]}`);
        console.log(`      Contract says profitable: ${isProfitable}`);
        
        if (!isProfitable && netProfit > 0n) {
            console.log(`      ⚠️  CONTRACT REJECTS PROFITABLE OPPORTUNITY!`);
            console.log(`          This might be due to slippage tolerance or minimum threshold`);
        }
        
    } catch (error) {
        // Ignore individual pair errors
    }
}

function getTokenSymbols(path: string[]): string[] {
    const symbolMap: { [key: string]: string } = {
        [tokens.WBNB]: "WBNB",
        [tokens.USDT]: "USDT",
        [tokens.BUSD]: "BUSD",
        [tokens.USDC]: "USDC"
    };
    
    return path.map(token => symbolMap[token] || "UNKNOWN");
}

// Start scanning
scanForArbitrageOpportunities().catch(console.error);
