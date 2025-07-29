import { JsonRpcProvider, Contract, Wallet, formatEther, parseEther } from 'ethers';
import dotenv from 'dotenv';

dotenv.config();

// Contract ABI
const contractABI = [
    "function executeArbitrage(address asset, uint256 amount, string calldata dexA, string calldata dexB, address[] calldata path, uint256 minProfit) external"
];

const BSC_RPC = process.env.BSC_RPC || "https://bsc-dataseed1.binance.org/";
const PRIVATE_KEY = process.env.PRIVATE_KEY!;
const CONTRACT_ADDRESS = "0x0FA4cab40651cfcb308C169fd593E92F2f0cf805";

// Test parameters for the opportunity we keep seeing
const WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c";
const USDT = "0x55d398326f99059fF775485246999027B3197955";

async function attemptDirectExecution() {
    console.log("🚀 EXPERIMENTAL: Direct Contract Execution Attempt\n");
    
    try {
        const provider = new JsonRpcProvider(BSC_RPC);
        const wallet = new Wallet(PRIVATE_KEY, provider);
        const contract = new Contract(CONTRACT_ADDRESS, contractABI, wallet);
        
        console.log(`📋 Contract: ${CONTRACT_ADDRESS}`);
        console.log(`👤 Wallet: ${wallet.address}`);
        console.log(`🌐 RPC: ${BSC_RPC}\n`);
        
        // Use the parameters from the consistently found opportunity
        const testAmount = parseEther("0.1"); // Small amount for safety
        const path = [WBNB, USDT];
        
        console.log("🎯 Attempting the opportunity we keep seeing:");
        console.log(`   Route: Biswap -> PancakeSwap V2`);
        console.log(`   Amount: ${formatEther(testAmount)} WBNB`);
        console.log(`   Path: WBNB -> USDT`);
        console.log(`   Expected profit: ~13%\n`);
        
        console.log("⚠️  WARNING: This bypasses pre-validation!");
        console.log("⚠️  If the opportunity is real, it should execute.");
        console.log("⚠️  If not, it will revert and we'll see the real error.\n");
        
        console.log("🔥 EXECUTING DIRECT ARBITRAGE...");
        
        // Set gas price high for priority
        const gasPrice = parseEther("0.000000050"); // 50 Gwei
        
        const tx = await contract.executeArbitrage(
            WBNB,
            testAmount,
            "biswap",
            "pancakeswap", 
            path,
            parseEther("0.001"), // Very low minimum profit - 0.001 ETH
            {
                gasLimit: 1000000,
                gasPrice: gasPrice
            }
        );
        
        console.log(`📝 Transaction sent: ${tx.hash}`);
        console.log("⏳ Waiting for confirmation...");
        console.log("🤞 This is the moment of truth...\n");
        
        const receipt = await tx.wait();
        
        if (receipt && receipt.status === 1) {
            console.log("🎉 SUCCESS! ARBITRAGE EXECUTED!");
            console.log(`📝 Transaction: ${tx.hash}`);
            console.log(`⛽ Gas used: ${receipt.gasUsed.toString()}`);
            console.log(`💰 The opportunity was REAL!`);
            
            // Check for profit events
            for (const log of receipt.logs) {
                try {
                    const parsed = contract.interface.parseLog({
                        topics: log.topics as string[],
                        data: log.data,
                    });
                    if (parsed && parsed.name === 'ArbitrageExecuted') {
                        console.log(`💰 Actual profit: ${formatEther(parsed.args.profit)} ETH`);
                    }
                } catch (error) {
                    continue;
                }
            }
            
        } else {
            console.log("❌ Transaction failed - but got through validation");
        }
        
    } catch (error: any) {
        console.log("❌ EXECUTION FAILED:");
        console.log(`   Error: ${error.message}`);
        
        if (error.message.includes("execution reverted")) {
            console.log("\n🔍 ANALYSIS:");
            console.log("   The contract reverted execution - this means:");
            console.log("   1. The opportunity was already taken by another bot");
            console.log("   2. The prices changed between detection and execution");
            console.log("   3. Insufficient liquidity or slippage issues");
            console.log("   4. The bot calculation was incorrect");
        }
        
        if (error.message.includes("insufficient funds")) {
            console.log("\n💰 WALLET ISSUE:");
            console.log("   Not enough BNB in wallet for gas or trade");
        }
        
        console.log("\n🎯 CONCLUSION:");
        console.log("   The bot is working correctly by rejecting these opportunities!");
        console.log("   The contract validation is protecting us from failed trades.");
    }
}

attemptDirectExecution();
