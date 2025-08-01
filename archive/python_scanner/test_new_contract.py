"""
Test the new BSC contract deployment
"""

import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

def test_new_contract():
    """Test the newly deployed BSC contract"""
    
    # Setup Web3
    rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect to BSC")
        return False
    
    print(f"✅ Connected to BSC: Block {w3.eth.block_number}")
    
    # New contract details
    contract_address = '0xfe9cfddc6270480507E810C4F2a1EA16a88F90cc'
    
    # Basic contract ABI for testing
    abi = [
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "token", "type": "address"}
            ],
            "name": "getTokenBalance",
            "outputs": [
                {"internalType": "uint256", "name": "", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "tokenA", "type": "address"},
                {"internalType": "address", "name": "tokenB", "type": "address"},
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "address", "name": "buyRouter", "type": "address"},
                {"internalType": "address", "name": "sellRouter", "type": "address"}
            ],
            "name": "checkArbitrageProfit",
            "outputs": [
                {"internalType": "uint256", "name": "estimatedProfit", "type": "uint256"},
                {"internalType": "bool", "name": "isProfitable", "type": "bool"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi
        )
        
        print(f"✅ Contract loaded: {contract_address}")
        
        # Test 1: Check owner
        try:
            owner = contract.functions.owner().call()
            print(f"✅ Contract owner: {owner}")
        except Exception as e:
            print(f"❌ Failed to get owner: {e}")
            return False
        
        # Test 2: Check token balance (BUSD)
        busd_address = '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'
        try:
            balance = contract.functions.getTokenBalance(busd_address).call()
            print(f"✅ BUSD balance in contract: {balance}")
        except Exception as e:
            print(f"❌ Failed to get BUSD balance: {e}")
            return False
        
        # Test 3: Check arbitrage profit calculation
        usdc_address = '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d'
        pancake_router = '0x10ED43C718714eb63d5aA57B78B54704E256024E'
        biswap_router = '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8'
        amount_in = int(1e18)  # 1 BUSD
        
        try:
            profit, is_profitable = contract.functions.checkArbitrageProfit(
                busd_address,
                usdc_address,
                amount_in,
                biswap_router,
                pancake_router
            ).call()
            
            print(f"✅ Arbitrage check - Profit: {profit}, Profitable: {is_profitable}")
            
            if profit > 0:
                profit_percentage = (profit / amount_in) * 100
                print(f"✅ Estimated profit: {profit_percentage:.4f}%")
            
        except Exception as e:
            print(f"❌ Failed to check arbitrage profit: {e}")
            return False
        
        print("✅ All contract tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Contract test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing New BSC Contract")
    print("=" * 50)
    
    success = test_new_contract()
    
    if success:
        print("\n🎉 Contract is working properly!")
        print("🚀 Ready to use with the scanner")
    else:
        print("\n💥 Contract has issues")
        print("🔧 Check deployment and try again")
