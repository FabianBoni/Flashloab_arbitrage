import { JsonRpcProvider, Contract, formatEther, parseEther } from 'ethers';
import dotenv from 'dotenv';

dotenv.config();

// Router ABI
const routerABI = [
    "function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts)"
];

// Contract ABI
const contractABI = [
    "function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)",
    "function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)"
];

const BSC_RPC = process.env.BSC_RPC || "https://bsc-dataseed1.binance.org/";
const CONTRACT_ADDRESS = "0x0FA4cab40651cfcb308C169fd593E92F2f0cf805";

// Router addresses
const PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E";
const BISWAP_ROUTER = "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8";

// Tokens
const WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c";
const USDT = "0x55d398326f99059fF775485246999027B3197955";

async function simulateExactBotLogic() {
    console.log("🔍 SIMULATING: Exact Bot vs Contract Logic\n");
    
    const provider = new JsonRpcProvider(BSC_RPC);
    const pancakeRouter = new Contract(PANCAKE_ROUTER, routerABI, provider);
    const biswapRouter = new Contract(BISWAP_ROUTER, routerABI, provider);
    const contract = new Contract(CONTRACT_ADDRESS, contractABI, provider);
    
    const testAmount = parseEther("1.0"); // 1 BNB
    const path = [WBNB, USDT];
    
    console.log("📊 Testing with 1 BNB WBNB->USDT->WBNB\n");
    
    try {
        // === BOT LOGIC ===
        console.log("🤖 BOT CALCULATION:");
        
        // Step 1: Get price on PancakeSwap (BNB -> USDT)
        const pancakeAmounts = await pancakeRouter.getAmountsOut(testAmount, path);
        const usdtAmount = pancakeAmounts[1];
        console.log(`   1. PancakeSwap: ${formatEther(testAmount)} WBNB -> ${formatEther(usdtAmount)} USDT`);
        
        // Step 2: Get price on Biswap (USDT -> BNB)
        const reversePath = [USDT, WBNB];
        const biswapAmounts = await biswapRouter.getAmountsOut(usdtAmount, reversePath);
        const finalBnbAmount = biswapAmounts[1];
        console.log(`   2. Biswap: ${formatEther(usdtAmount)} USDT -> ${formatEther(finalBnbAmount)} WBNB`);
        
        // Step 3: Calculate profit (BOT METHOD - simplified)
        const grossProfit = finalBnbAmount - testAmount;
        const grossProfitPercent = Number(grossProfit * 10000n / testAmount) / 100;
        console.log(`   3. Gross Profit: ${formatEther(grossProfit)} WBNB (${grossProfitPercent.toFixed(4)}%)`);
        
        // Step 4: Bot simple check (usually just checks > 0.5%)
        const botSaysProfit = grossProfitPercent > 0.5;
        console.log(`   4. Bot says profitable: ${botSaysProfit} (threshold: > 0.5%)\n`);
        
        // === CONTRACT LOGIC ===
        console.log("⚖️  CONTRACT CALCULATION:");
        
        // Contract method
        const contractProfit = await contract.calculateArbitrageProfit(
            testAmount,
            "pancakeswap",
            "biswap",
            path
        );
        
        const contractProfitable = await contract.isArbitrageProfitable(
            testAmount,
            "pancakeswap",
            "biswap",
            path
        );
        
        console.log(`   Contract profit: ${formatEther(contractProfit)} WBNB`);
        console.log(`   Contract says profitable: ${contractProfitable}\n`);
        
        // === DETAILED CONTRACT LOGIC BREAKDOWN ===
        console.log("🔬 DETAILED CONTRACT LOGIC:");
        
        // Manual recreation of contract logic
        const contractFlashloanFee = testAmount * 25n / 10000n; // 0.25%
        const netProfitAfterFee = grossProfit - contractFlashloanFee;
        const netProfitPercent = Number(netProfitAfterFee * 10000n / testAmount) / 100;
        
        console.log(`   1. Gross profit: ${formatEther(grossProfit)} WBNB (${grossProfitPercent.toFixed(4)}%)`);
        console.log(`   2. Flashloan fee: ${formatEther(contractFlashloanFee)} WBNB (0.25%)`);
        console.log(`   3. Net profit after fee: ${formatEther(netProfitAfterFee)} WBNB (${netProfitPercent.toFixed(4)}%)`);
        console.log(`   4. Contract minimum threshold: 0.001% (0.0001 ETH)`);
        
        const contractThresholdCheck = netProfitAfterFee > parseEther("0.0001");
        console.log(`   5. Passes threshold: ${contractThresholdCheck}\n`);
        
        // === COMPARISON ===
        console.log("📋 COMPARISON:");
        console.log(`   Bot method profit: ${grossProfitPercent.toFixed(4)}%`);
        console.log(`   Contract method profit: ${netProfitPercent.toFixed(4)}%`);
        console.log(`   Difference: ${(grossProfitPercent - netProfitPercent).toFixed(4)}% (flashloan fee)`);
        
        if (botSaysProfit && !contractProfitable) {
            console.log("\n   ❌ PROBLEM IDENTIFIED:");
            console.log("   - Bot finds opportunity WITHOUT accounting for flashloan fees");
            console.log("   - Contract REJECTS it AFTER accounting for flashloan fees");
            console.log("   - The 0.25% flashloan fee makes it unprofitable!");
        }
        
    } catch (error: any) {
        console.error("❌ Error:", error.message);
    }
}

simulateExactBotLogic();
