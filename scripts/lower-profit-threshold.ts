import { JsonRpcProvider, Contract, Wallet, parseEther } from 'ethers';
import dotenv from 'dotenv';

dotenv.config();

// Contract ABI
const contractABI = [
    "function updateMinProfitThreshold(uint256 _threshold) external",
    "function minProfitThreshold() external view returns (uint256)",
    "function owner() external view returns (address)"
];

const BSC_RPC = process.env.BSC_RPC || "https://bsc-dataseed1.binance.org/";
const PRIVATE_KEY = process.env.PRIVATE_KEY!;
const CONTRACT_ADDRESS = "0x0FA4cab40651cfcb308C169fd593E92F2f0cf805";

async function lowerProfitThreshold() {
    console.log("🔧 LOWERING: Minimum Profit Threshold\n");
    
    try {
        const provider = new JsonRpcProvider(BSC_RPC);
        const wallet = new Wallet(PRIVATE_KEY, provider);
        const contract = new Contract(CONTRACT_ADDRESS, contractABI, wallet);
        
        console.log(`📋 Contract: ${CONTRACT_ADDRESS}`);
        console.log(`👤 Wallet: ${wallet.address}\n`);
        
        // Check current threshold
        const currentThreshold = await contract.minProfitThreshold();
        console.log(`📊 Current threshold: ${currentThreshold.toString()} wei (${Number(currentThreshold) / 1e18} ETH)`);
        
        // Set new threshold to 0.00001 ETH (0.001%)
        const newThreshold = parseEther("0.00001");
        console.log(`📊 New threshold: ${newThreshold.toString()} wei (${Number(newThreshold) / 1e18} ETH)\n`);
        
        console.log("🔧 Updating threshold...");
        const tx = await contract.updateMinProfitThreshold(newThreshold);
        console.log(`📝 Transaction: ${tx.hash}`);
        console.log("⏳ Waiting for confirmation...");
        
        await tx.wait();
        
        // Verify the change
        const updatedThreshold = await contract.minProfitThreshold();
        console.log(`✅ Threshold updated to: ${updatedThreshold.toString()} wei (${Number(updatedThreshold) / 1e18} ETH)`);
        
        const thresholdPercent = (Number(updatedThreshold) / 1e18) * 100;
        console.log(`✅ This represents ${thresholdPercent.toFixed(6)}% minimum profit requirement`);
        
    } catch (error: any) {
        console.error("❌ Error:", error.message);
    }
}

lowerProfitThreshold();
