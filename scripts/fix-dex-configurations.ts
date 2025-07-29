import { JsonRpcProvider, Contract, Wallet, getAddress } from 'ethers';
import dotenv from 'dotenv';

dotenv.config();

// Contract ABI for configuration
const contractABI = [
    "function updateDEXConfig(string calldata dexName, address router, bool isActive, uint256 fee) external",
    "function dexConfigs(string memory dexName) external view returns (address router, bool isActive, uint256 fee)",
    "function owner() external view returns (address)",
    "function minProfitThreshold() external view returns (uint256)"
];

const BSC_RPC = process.env.BSC_RPC || "https://bsc-dataseed1.binance.org/";
const PRIVATE_KEY = process.env.PRIVATE_KEY!;
const CONTRACT_ADDRESS = "0x0FA4cab40651cfcb308C169fd593E92F2f0cf805";

// DEX configurations with proper checksummed addresses
const DEX_CONFIGS = {
    pancakeswap: {
        router: "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        fee: 25 // 0.25% for PancakeSwap
    },
    biswap: {
        router: "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",
        fee: 10 // 0.1% for Biswap
    }
};

async function fixDEXConfigurations() {
    console.log("🔧 FIXING: DEX Configurations in Contract\n");
    
    try {
        // Setup provider and wallet
        const provider = new JsonRpcProvider(BSC_RPC);
        const wallet = new Wallet(PRIVATE_KEY, provider);
        const contract = new Contract(CONTRACT_ADDRESS, contractABI, wallet);
        
        console.log(`📋 Contract: ${CONTRACT_ADDRESS}`);
        console.log(`👤 Wallet: ${wallet.address}`);
        console.log(`🌐 RPC: ${BSC_RPC}\n`);
        
        // Check if we're the owner
        const owner = await contract.owner();
        console.log(`🔐 Contract owner: ${owner}`);
        console.log(`🔐 Current wallet: ${wallet.address}`);
        
        if (owner.toLowerCase() !== wallet.address.toLowerCase()) {
            console.log("❌ ERROR: Wallet is not the contract owner!");
            return;
        }
        
        console.log("✅ Wallet is contract owner, proceeding...\n");
        
        // Configure each DEX
        for (const [dexName, config] of Object.entries(DEX_CONFIGS)) {
            console.log(`🔧 Configuring ${dexName}...`);
            
            try {
                // Ensure router address is properly checksummed
                const routerAddress = getAddress(config.router);
                
                const tx = await contract.updateDEXConfig(
                    dexName,
                    routerAddress,
                    true, // isActive
                    config.fee
                );
                
                console.log(`   📝 Transaction: ${tx.hash}`);
                console.log(`   ⏳ Waiting for confirmation...`);
                
                await tx.wait();
                
                // Verify the configuration
                const updatedConfig = await contract.dexConfigs(dexName);
                console.log(`   ✅ ${dexName} configured:`);
                console.log(`      Router: ${updatedConfig[0]}`);
                console.log(`      Active: ${updatedConfig[1]}`);
                console.log(`      Fee: ${updatedConfig[2]} basis points\n`);
                
            } catch (error: any) {
                console.log(`   ❌ Error configuring ${dexName}: ${error.message}\n`);
            }
        }
        
        // Check current minimum profit threshold
        console.log("📊 Current minimum profit threshold:");
        const threshold = await contract.minProfitThreshold();
        console.log(`   ${threshold.toString()} wei (${Number(threshold) / 1e18} ETH)\n`);
        
        console.log("✅ DEX configuration completed!");
        
    } catch (error: any) {
        console.error("❌ Fatal error:", error.message);
    }
}

fixDEXConfigurations();
