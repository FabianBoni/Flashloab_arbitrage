import { JsonRpcProvider, Contract, Wallet, formatEther, parseEther } from 'ethers';
import dotenv from 'dotenv';

dotenv.config();

// Contract ABI for profitability checking
const contractABI = [
    "function minProfitThreshold() external view returns (uint256)",
    "function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)",
    "function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)",
    "function dexConfigs(string memory dexName) external view returns (address router, bool isActive, uint256 fee)"
];

const BSC_RPC = process.env.BSC_RPC || "https://bsc-dataseed1.binance.org/";
const CONTRACT_ADDRESS = "0x0FA4cab40651cfcb308C169fd593E92F2f0cf805";

// Test token addresses (WBNB/USDT pair) - properly checksummed
const WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c";
const USDT = "0x55d398326f99059fF775485246999027B3197955";

async function debugContractProfitability() {
    console.log("🔍 DEBUG: Contract Profitability Analysis\n");
    
    try {
        // Setup provider and contract
        const provider = new JsonRpcProvider(BSC_RPC);
        const contract = new Contract(CONTRACT_ADDRESS, contractABI, provider);
        
        console.log(`📋 Contract: ${CONTRACT_ADDRESS}`);
        console.log(`🌐 RPC: ${BSC_RPC}\n`);
        
        // 1. Check minimum profit threshold
        console.log("1️⃣ Checking minimum profit threshold...");
        try {
            const threshold = await contract.minProfitThreshold();
            console.log(`   Current threshold: ${formatEther(threshold)} ETH\n`);
        } catch (error: any) {
            console.log(`   ❌ Error getting threshold: ${error.message}\n`);
        }
        
        // 2. Check DEX configurations
        console.log("2️⃣ Checking DEX configurations...");
        const dexes = ["pancakeswap", "biswap"];
        for (const dex of dexes) {
            try {
                const config = await contract.dexConfigs(dex);
                console.log(`   ${dex}:`);
                console.log(`     Router: ${config[0]}`);
                console.log(`     Active: ${config[1]}`);
                console.log(`     Fee: ${config[2]} basis points`);
            } catch (error: any) {
                console.log(`   ${dex}: ❌ Error - ${error.message}`);
            }
        }
        console.log();
        
        // 3. Test profitability calculation with different amounts
        console.log("3️⃣ Testing profitability calculations...");
        const testAmounts = [
            parseEther("0.1"),  // 0.1 BNB
            parseEther("1.0"),  // 1.0 BNB
            parseEther("5.0"),  // 5.0 BNB
        ];
        
        const path = [WBNB, USDT];
        
        for (const amount of testAmounts) {
            console.log(`\n📊 Testing with ${formatEther(amount)} BNB:`);
            
            // Test PancakeSwap -> Biswap
            try {
                const profit = await contract.calculateArbitrageProfit(
                    amount,
                    "pancakeswap", 
                    "biswap",
                    path
                );
                
                const isProfitable = await contract.isArbitrageProfitable(
                    amount,
                    "pancakeswap", 
                    "biswap",
                    path
                );
                
                console.log(`   PancakeSwap -> Biswap:`);
                console.log(`     Calculated profit: ${formatEther(profit)} BNB`);
                console.log(`     Is profitable: ${isProfitable}`);
                
                if (profit > 0n) {
                    const profitPercent = Number(profit * 100n / amount);
                    console.log(`     Profit percentage: ${profitPercent.toFixed(4)}%`);
                }
                
            } catch (error: any) {
                console.log(`   PancakeSwap -> Biswap: ❌ Error - ${error.message}`);
            }
            
            // Test Biswap -> PancakeSwap
            try {
                const profit = await contract.calculateArbitrageProfit(
                    amount,
                    "biswap", 
                    "pancakeswap",
                    path
                );
                
                const isProfitable = await contract.isArbitrageProfitable(
                    amount,
                    "biswap", 
                    "pancakeswap",
                    path
                );
                
                console.log(`   Biswap -> PancakeSwap:`);
                console.log(`     Calculated profit: ${formatEther(profit)} BNB`);
                console.log(`     Is profitable: ${isProfitable}`);
                
                if (profit > 0n) {
                    const profitPercent = Number(profit * 100n / amount);
                    console.log(`     Profit percentage: ${profitPercent.toFixed(4)}%`);
                }
                
            } catch (error: any) {
                console.log(`   Biswap -> PancakeSwap: ❌ Error - ${error.message}`);
            }
        }
        
        // 4. Detailed analysis for a specific case
        console.log("\n4️⃣ Detailed analysis for 1 BNB trade...");
        const analyzeAmount = parseEther("1.0");
        
        try {
            // Get raw router outputs to see what's happening
            const routerABI = [
                "function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts)"
            ];
            
            const pancakeRouter = new Contract("0x10ED43C718714eb63d5aA57B78B54704E256024E", routerABI, provider);
            const biswapRouter = new Contract("0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8", routerABI, provider);
            
            console.log("   Getting raw DEX quotes...");
            
            // PancakeSwap: BNB -> USDT
            const pancakeOut = await pancakeRouter.getAmountsOut(analyzeAmount, path);
            console.log(`   PancakeSwap BNB->USDT: ${formatEther(pancakeOut[1])} USDT`);
            
            // Biswap: USDT -> BNB
            const reversePath = [USDT, WBNB];
            const biswapOut = await biswapRouter.getAmountsOut(pancakeOut[1], reversePath);
            console.log(`   Biswap USDT->BNB: ${formatEther(biswapOut[1])} BNB`);
            
            // Calculate gross profit
            const grossProfit = biswapOut[1] - analyzeAmount;
            console.log(`   Gross profit: ${formatEther(grossProfit)} BNB`);
            
            // Calculate flashloan fee (0.25% for PancakeSwap)
            const flashloanFee = analyzeAmount * 25n / 10000n;
            console.log(`   Flashloan fee: ${formatEther(flashloanFee)} BNB`);
            
            // Net profit
            const netProfit = grossProfit - flashloanFee;
            console.log(`   Net profit: ${formatEther(netProfit)} BNB`);
            
            const profitPercent = Number(netProfit * 10000n / analyzeAmount) / 100;
            console.log(`   Net profit %: ${profitPercent.toFixed(4)}%`);
            
        } catch (error: any) {
            console.log(`   ❌ Error in detailed analysis: ${error.message}`);
        }
        
    } catch (error: any) {
        console.error("❌ Fatal error:", error.message);
    }
}

debugContractProfitability();
