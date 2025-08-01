"""
Debug failed transaction to understand why arbitrage trades are failing
"""

from web3 import Web3
from dotenv import load_dotenv
import os
import json

load_dotenv()

def debug_transaction():
    """Debug the failed transaction"""
    
    # Setup Web3
    rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print(f"Failed to connect to BSC")
        return
        
    print(f"Connected to BSC: Block {w3.eth.block_number}")
    
    # Transaction hash from the failed execution
    tx_hash = "0x0115ffecca3be2ab37366f2fd233025600077698527e1ad5e1024e1252ad38e1"
    
    try:
        print(f"\nDebugging transaction: {tx_hash}")
        
        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"\nTransaction Details:")
        print(f"  From: {tx['from']}")
        print(f"  To: {tx['to']}")
        print(f"  Value: {w3.from_wei(tx['value'], 'ether')} BNB")
        print(f"  Gas: {tx['gas']}")
        print(f"  Gas Price: {w3.from_wei(tx['gasPrice'], 'gwei')} gwei")
        print(f"  Nonce: {tx['nonce']}")
        print(f"  Block Number: {tx['blockNumber']}")
        
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"\nTransaction Receipt:")
        print(f"  Status: {receipt['status']} ({'SUCCESS' if receipt['status'] == 1 else 'FAILED'})")
        print(f"  Gas Used: {receipt['gasUsed']} / {tx['gas']} ({receipt['gasUsed']/tx['gas']*100:.1f}%)")
        print(f"  Cumulative Gas Used: {receipt['cumulativeGasUsed']}")
        print(f"  Effective Gas Price: {w3.from_wei(receipt['effectiveGasPrice'], 'gwei')} gwei")
        
        # Show logs (events)
        if receipt['logs']:
            print(f"\nTransaction Logs ({len(receipt['logs'])} events):")
            for i, log in enumerate(receipt['logs']):
                print(f"  Log {i}: {log['address']} - {len(log['topics'])} topics")
        else:
            print(f"\nNo transaction logs (this might indicate a revert)")
            
        # Try to get revert reason
        print(f"\nAnalyzing failure reason...")
        
        # Simulate the transaction to get revert reason
        try:
            # Get the transaction input data
            tx_data = {
                'from': tx['from'],
                'to': tx['to'],
                'value': tx['value'],
                'gas': tx['gas'],
                'gasPrice': tx['gasPrice'],
                'data': tx['input']
            }
            
            # Try to call the transaction to see what happens
            result = w3.eth.call(tx_data, tx['blockNumber'] - 1)
            print(f"  Call result: {result.hex()}")
            
        except Exception as call_error:
            error_msg = str(call_error)
            print(f"  Call failed with: {error_msg}")
            
            # Common revert reasons
            if "insufficient balance" in error_msg.lower():
                print(f"  >> REASON: Insufficient balance for the trade")
            elif "slippage" in error_msg.lower():
                print(f"  >> REASON: Slippage tolerance exceeded")
            elif "liquidity" in error_msg.lower():
                print(f"  >> REASON: Insufficient liquidity")
            elif "revert" in error_msg.lower():
                print(f"  >> REASON: Contract execution reverted")
            elif "gas" in error_msg.lower():
                print(f"  >> REASON: Gas-related issue")
            else:
                print(f"  >> REASON: Unknown - {error_msg}")
        
        # Check account balance at the time of transaction
        account_address = tx['from']
        balance_at_block = w3.eth.get_balance(account_address, tx['blockNumber'] - 1)
        balance_current = w3.eth.get_balance(account_address)
        
        print(f"\nAccount Analysis:")
        print(f"  Address: {account_address}")
        print(f"  Balance at tx block: {w3.from_wei(balance_at_block, 'ether'):.6f} BNB")
        print(f"  Current balance: {w3.from_wei(balance_current, 'ether'):.6f} BNB")
        
        # Calculate transaction cost
        tx_cost = receipt['gasUsed'] * receipt['effectiveGasPrice']
        print(f"  Transaction cost: {w3.from_wei(tx_cost, 'ether'):.6f} BNB")
        
        # Analyze the contract being called
        contract_address = tx['to']
        print(f"\nContract Analysis:")
        print(f"  Contract: {contract_address}")
        
        # Check if contract has code
        code = w3.eth.get_code(contract_address)
        if code and len(code) > 2:
            print(f"  Contract has code: {len(code)} bytes")
        else:
            print(f"  WARNING: Contract has no code (might be EOA)")
            
        # Decode the function call if possible
        input_data = tx['input']
        if len(input_data) >= 10:
            function_selector = input_data[:10]
            print(f"  Function selector: {function_selector}")
            
            # Known function selectors
            known_selectors = {
                '0x5f575529': 'flashloan(address,uint256,address[],address[])',
                '0xa9059cbb': 'transfer(address,uint256)',
                '0x23b872dd': 'transferFrom(address,address,uint256)',
                '0x095ea7b3': 'approve(address,uint256)'
            }
            
            if function_selector in known_selectors:
                print(f"  Function: {known_selectors[function_selector]}")
            else:
                print(f"  Function: Unknown")
                
        print(f"\n" + "="*60)
        print(f"FAILURE ANALYSIS SUMMARY:")
        print(f"="*60)
        
        if receipt['status'] == 0:
            print(f"❌ Transaction FAILED (status = 0)")
            print(f"💰 Gas used: {receipt['gasUsed']} / {tx['gas']} ({receipt['gasUsed']/tx['gas']*100:.1f}%)")
            
            if receipt['gasUsed'] == tx['gas']:
                print(f"🔥 OUT OF GAS - Transaction used all provided gas")
                print(f"💡 SOLUTION: Increase gas limit")
            elif receipt['gasUsed'] < tx['gas'] * 0.1:
                print(f"⚠️  EARLY REVERT - Transaction failed quickly")
                print(f"💡 SOLUTION: Check contract logic, balances, and approvals")
            else:
                print(f"🔄 MID-EXECUTION REVERT - Transaction failed during execution")
                print(f"💡 SOLUTION: Check slippage, liquidity, and market conditions")
        else:
            print(f"✅ Transaction SUCCESS")
            
    except Exception as e:
        print(f"Error debugging transaction: {e}")

def analyze_flashloan_contract():
    """Analyze the flashloan contract to understand requirements"""
    
    rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    contract_address = "0xb85d7dfE30d5eaF5c564816Efa8bad9E99097551"
    
    print(f"\n" + "="*60)
    print(f"FLASHLOAN CONTRACT ANALYSIS")
    print(f"="*60)
    print(f"Contract: {contract_address}")
    
    # Check if contract exists
    code = w3.eth.get_code(contract_address)
    if not code or len(code) <= 2:
        print(f"❌ ERROR: Contract has no code!")
        return
        
    print(f"✅ Contract exists with {len(code)} bytes of code")
    
    # Get contract balance
    balance = w3.eth.get_balance(contract_address)
    print(f"💰 Contract balance: {w3.from_wei(balance, 'ether'):.6f} BNB")
    
    # Check if it's a proxy contract (common pattern)
    if len(code) < 1000:
        print(f"⚠️  Small contract size - might be a proxy")
        
    print(f"\n💡 COMMON FLASHLOAN FAILURE REASONS:")
    print(f"   1. Contract doesn't have enough liquidity")
    print(f"   2. Flashloan fee not calculated correctly")
    print(f"   3. Arbitrage path not profitable after fees")
    print(f"   4. DEX router addresses incorrect")
    print(f"   5. Token addresses incorrect")
    print(f"   6. Insufficient gas for complex execution")
    print(f"   7. Slippage too high during execution")

if __name__ == "__main__":
    debug_transaction()
    analyze_flashloan_contract()
