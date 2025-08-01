"""
Test the flashloan contract with a simple transaction to verify it's working
"""
import os
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

def test_flashloan_simple():
    # Setup Web3
    w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org/'))
    print(f"Connected to BSC: Block {w3.eth.block_number}")
    
    # Setup account
    private_key = os.getenv('PRIVATE_KEY')
    account = w3.eth.account.from_key(private_key)
    balance = w3.eth.get_balance(account.address)
    balance_bnb = w3.from_wei(balance, 'ether')
    print(f"Account: {account.address}")
    print(f"Balance: {balance_bnb:.4f} BNB")
    
    # Contract setup
    contract_address = os.getenv('FLASHLOAN_CONTRACT_ADDRESS')
    print(f"Testing contract: {contract_address}")
    
    # Simple ABI for testing
    abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "asset", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "address[]", "name": "routers", "type": "address[]"},
                {"internalType": "address[]", "name": "tokens", "type": "address[]"}
            ],
            "name": "flashloan",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi
        )
        
        # Test parameters - very small amount
        busd_address = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"
        usdc_address = "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d"
        
        routers = [
            "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",  # Biswap
            "0x10ED43C718714eb63d5aA57B78B54704E256024E"   # PancakeSwap
        ]
        
        tokens = [busd_address, usdc_address]
        
        # Very small test amount (0.01 BUSD)
        test_amount = int(0.01 * 1e18)
        
        print(f"\nTesting flashloan with:")
        print(f"  Asset: BUSD ({busd_address})")
        print(f"  Amount: {test_amount} (0.01 BUSD)")
        print(f"  Routers: Biswap -> PancakeSwap")
        
        # Estimate gas first
        try:
            gas_estimate = contract.functions.flashloan(
                busd_address,
                test_amount,
                routers,
                tokens
            ).estimate_gas({'from': account.address})
            
            print(f"  Estimated gas: {gas_estimate:,}")
            
        except Exception as e:
            print(f"  ❌ Gas estimation failed: {e}")
            print("  This suggests the transaction would fail")
            return False
        
        # If gas estimation succeeds, the transaction should work
        print("  ✅ Gas estimation succeeded - transaction should work!")
        
        # Get current gas price and nonce
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(account.address, 'pending')
        
        print(f"  Gas price: {w3.from_wei(gas_price, 'gwei')} gwei")
        print(f"  Nonce: {nonce}")
        
        # Ask user if they want to proceed with real transaction
        proceed = input("\nDo you want to send the real transaction? (y/N): ").lower().strip()
        
        if proceed == 'y':
            # Build and send transaction
            transaction = contract.functions.flashloan(
                busd_address,
                test_amount,
                routers,
                tokens
            ).build_transaction({
                'from': account.address,
                'gas': gas_estimate + 50000,  # Add buffer
                'gasPrice': gas_price,
                'nonce': nonce
            })
            
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print(f"Transaction sent: {tx_hash.hex()}")
            print("Waiting for confirmation...")
            
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                print("✅ SUCCESS! Flashloan transaction worked!")
                print(f"Gas used: {receipt.gasUsed:,}")
            else:
                print("❌ FAILED: Transaction reverted")
                print(f"Gas used: {receipt.gasUsed:,}")
                
        else:
            print("Transaction not sent (user choice)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_flashloan_simple()
