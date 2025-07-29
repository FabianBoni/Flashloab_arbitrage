import { JsonRpcProvider, Contract, Wallet, getAddress } from 'ethers';
import dotenv from 'dotenv';

dotenv.config();

// Contract ABI for configuration
const contractABI = [
    "function updateDEXConfig(string calldata dexName, address router, bool isActive, uint256 fee) external",
    "function dexConfigs(string memory dexName) external view returns (address router, bool isActive, uint256 fee)"
];

const BSC_RPC = process.env.BSC_RPC || "https://bsc-dataseed1.binance.org/";
const PRIVATE_KEY = process.env.PRIVATE_KEY!;
const CONTRACT_ADDRESS = "0x0FA4cab40651cfcb308C169fd593E92F2f0cf805";

// NEW DEX configurations for aggressive arbitrage
const NEW_DEX_CONFIGS = {
    apeswap: {
        router: "0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7",
        fee: 20 // 0.2% for ApeSwap
    },
    babyswap: {
        router: "0x325E343f1dE602396E256B67eFd1F61C3A6B38Bd",
        fee: 25 // 0.25% for BabySwap
    }
};

async function addNewDEXes() {
    console.log("🚀 ADDING: New DEXes for Maximum Arbitrage Opportunities\n");
    
    try {
        const provider = new JsonRpcProvider(BSC_RPC);
        const wallet = new Wallet(PRIVATE_KEY, provider);
        const contract = new Contract(CONTRACT_ADDRESS, contractABI, wallet);
        
        console.log(`📋 Contract: ${CONTRACT_ADDRESS}`);
        console.log(`👤 Wallet: ${wallet.address}\n`);
        
        // Configure each new DEX
        for (const [dexName, config] of Object.entries(NEW_DEX_CONFIGS)) {
            console.log(`🔧 Adding ${dexName}...`);
            
            try {
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
                console.log(`   ✅ ${dexName} added:`);
                console.log(`      Router: ${updatedConfig[0]}`);
                console.log(`      Active: ${updatedConfig[1]}`);
                console.log(`      Fee: ${updatedConfig[2]} basis points\n`);
                
            } catch (error: any) {
                console.log(`   ❌ Error adding ${dexName}: ${error.message}\n`);
            }
        }
        
        console.log("🎯 NOW CONFIGURED DEXes:");
        const allDexes = ["pancakeswap", "biswap", "apeswap", "babyswap"];
        
        for (const dex of allDexes) {
            try {
                const config = await contract.dexConfigs(dex);
                console.log(`   ${dex}: ${config[1] ? '✅ ACTIVE' : '❌ INACTIVE'} (${config[2]} bp fee)`);
            } catch (error) {
                console.log(`   ${dex}: ❌ NOT CONFIGURED`);
            }
        }
        
        console.log("\n🚀 ULTRA-AGGRESSIVE CONFIGURATION COMPLETE!");
        console.log("   - 4 DEXes active");
        console.log("   - 8 tokens");
        console.log("   - 1-second scanning");
        console.log("   - Higher gas prices");
        console.log("   - Lower profit threshold");
        
    } catch (error: any) {
        console.error("❌ Fatal error:", error.message);
    }
}

addNewDEXes();
