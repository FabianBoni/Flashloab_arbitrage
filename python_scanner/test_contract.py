"""
Simple test to verify the deployed flashloan contract
"""
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

def test_contract():
    # Setup Web3
    w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org/'))
    print(f"Connected to BSC: Block {w3.eth.block_number}")
    
    # Contract details
    contract_address = os.getenv('BSC_FLASHLOAN_CONTRACT')
    print(f"Testing contract: {contract_address}")
    
    try:
        # Get some basic info about the contract first
        code = w3.eth.get_code(contract_address)
        print(f"Contract has code: {len(code) > 0}")
        print(f"Code size: {len(code)} bytes")
        
        if len(code) == 0:
            print("ERROR: No contract code at this address!")
            return
        else:
            print(f"Contract code (first 100 bytes): {code[:100].hex()}")
        
        # Check transaction that created the contract
        print(f"\nChecking if this address has any transaction history...")
        balance = w3.eth.get_balance(contract_address)
        print(f"Contract balance: {w3.from_wei(balance, 'ether')} BNB")
        
        # Try different function signatures that might exist
        common_functions = [
            {
                "inputs": [],
                "name": "owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getOwner", 
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "_owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        for func_abi in common_functions:
            try:
                abi = [func_abi]
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(contract_address),
                    abi=abi
                )
                
                # Test the function
                func_name = func_abi["name"]
                result = getattr(contract.functions, func_name)().call()
                print(f"✅ SUCCESS: {func_name}() = {result}")
                
                # Check our account
                account_address = "0x683A565636a889811625aa948aE7EC636267a189"
                print(f"Our account: {account_address}")
                print(f"Are we the owner? {result.lower() == account_address.lower()}")
                break
                
            except Exception as e:
                print(f"❌ FAILED: {func_abi['name']}() - {e}")
        
        print("\n" + "="*50)
        print("If all owner functions failed, the contract might be using a completely different interface.")
        
    except Exception as e:
        print(f"Error testing contract: {e}")

if __name__ == "__main__":
    test_contract()
