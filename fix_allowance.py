#!/usr/bin/env python3
"""
Fix Token Allowance und Transfer
Korrekte Token-Übertragung zum Contract
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

print("🔧 TOKEN ALLOWANCE & TRANSFER FIX")

# Setup
load_dotenv()
rpc_url = os.getenv('BSC_RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))
private_key = os.getenv('PRIVATE_KEY')
account = w3.eth.account.from_key(private_key)

print(f"💼 Account: {account.address}")

# Contract Setup
contract_address = os.getenv('CONTRACT_ADDRESS')
with open('deployed_contract.json', 'r') as f:
    contract_info = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=contract_info['abi'])
usdt_addr = contract.functions.USDT().call()

print(f"📍 Contract: {contract_address}")
print(f"🪙 USDT: {usdt_addr}")

# ERC20 ABI
erc20_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

def check_balances():
    """Check alle Balances"""
    usdt_contract = w3.eth.contract(address=usdt_addr, abi=erc20_abi)
    
    user_usdt = usdt_contract.functions.balanceOf(account.address).call()
    contract_usdt = usdt_contract.functions.balanceOf(contract_address).call()
    allowance = usdt_contract.functions.allowance(account.address, contract_address).call()
    
    print(f"\n📊 CURRENT STATUS:")
    print(f"👤 User USDT: {w3.from_wei(user_usdt, 'ether'):.6f}")
    print(f"📍 Contract USDT: {w3.from_wei(contract_usdt, 'ether'):.6f}")
    print(f"✅ Allowance: {w3.from_wei(allowance, 'ether'):.6f}")
    
    return user_usdt, contract_usdt, allowance

def approve_tokens():
    """Approve Token für Contract"""
    
    print("\n✅ APPROVING TOKENS...")
    
    usdt_contract = w3.eth.contract(address=usdt_addr, abi=erc20_abi)
    user_usdt, _, current_allowance = check_balances()
    
    if user_usdt == 0:
        print("❌ Keine USDT zum Approve!")
        return False
    
    # Approve die Hälfte der Balance
    approve_amount = user_usdt // 2
    
    if current_allowance >= approve_amount:
        print(f"✅ Allowance bereits ausreichend: {w3.from_wei(current_allowance, 'ether'):.6f}")
        return True
    
    try:
        print(f"📝 Approve {w3.from_wei(approve_amount, 'ether'):.6f} USDT für Contract...")
        
        # Approve Transaction
        approve_txn = usdt_contract.functions.approve(
            contract_address,
            approve_amount
        ).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Signieren und senden
        signed_txn = w3.eth.account.sign_transaction(approve_txn, private_key)
        raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
        tx_hash = w3.eth.send_raw_transaction(raw_transaction)
        
        print(f"⏳ Approve TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print("✅ Approve erfolgreich!")
            
            # Check new allowance
            new_allowance = usdt_contract.functions.allowance(account.address, contract_address).call()
            print(f"✅ Neue Allowance: {w3.from_wei(new_allowance, 'ether'):.6f}")
            
            return True
        else:
            print("❌ Approve fehlgeschlagen!")
            return False
            
    except Exception as e:
        print(f"❌ Approve Fehler: {e}")
        return False

def deposit_with_allowance():
    """Deponiere Token mit korrekter Allowance"""
    
    print("\n📥 DEPOSITING WITH ALLOWANCE...")
    
    user_usdt, contract_usdt_before, allowance = check_balances()
    
    if allowance == 0:
        print("❌ Keine Allowance! Führe zuerst approve_tokens() aus")
        return False
    
    # Deponiere die erlaubte Menge
    deposit_amount = min(allowance, user_usdt // 2)
    
    try:
        print(f"📥 Deponiere {w3.from_wei(deposit_amount, 'ether'):.6f} USDT...")
        
        # Verwende depositToken Funktion
        deposit_txn = contract.functions.depositToken(
            usdt_addr,
            deposit_amount
        ).build_transaction({
            'from': account.address,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Signieren und senden
        signed_txn = w3.eth.account.sign_transaction(deposit_txn, private_key)
        raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
        tx_hash = w3.eth.send_raw_transaction(raw_transaction)
        
        print(f"⏳ Deposit TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print("✅ Deposit erfolgreich!")
            
            # Check final balances
            _, contract_usdt_after, _ = check_balances()
            
            if contract_usdt_after > contract_usdt_before:
                print(f"🎉 Contract Balance erhöht um {w3.from_wei(contract_usdt_after - contract_usdt_before, 'ether'):.6f} USDT!")
                return True
            else:
                print("⚠️  Contract Balance nicht verändert")
                return False
        else:
            print("❌ Deposit fehlgeschlagen!")
            return False
            
    except Exception as e:
        print(f"❌ Deposit Fehler: {e}")
        return False

def test_arbitrage_after_deposit():
    """Teste Arbitrage nach erfolgreichem Deposit"""
    
    print("\n🧪 TESTING ARBITRAGE AFTER DEPOSIT")
    print("-" * 35)
    
    try:
        # Kleine Test-Menge
        test_amount = w3.to_wei(0.1, 'ether')  # 0.1 USDT
        
        # Check if arbitrage profit check works now
        usdt_addr = contract.functions.USDT().call()
        busd_addr = contract.functions.BUSD().call()
        pancake_router = contract.functions.PANCAKESWAP_ROUTER().call()
        biswap_router = contract.functions.BISWAP_ROUTER().call()
        
        result = contract.functions.checkArbitrageProfit(
            usdt_addr,
            busd_addr,
            test_amount,
            pancake_router,
            biswap_router
        ).call()
        
        print(f"✅ Arbitrage Profit Check: {result}")
        
        # Try executeSimpleArbitrage
        arbitrage_result = contract.functions.executeSimpleArbitrage(
            usdt_addr,
            busd_addr,
            test_amount,
            pancake_router,
            biswap_router
        ).call({'from': account.address})
        
        print(f"✅ Simple Arbitrage Simulation: {arbitrage_result}")
        print("🎉 CONTRACT IS READY FOR ARBITRAGE!")
        
        return True
        
    except Exception as e:
        print(f"❌ Arbitrage Test Fehler: {e}")
        return False

def main():
    """Main execution"""
    
    print("🎯 COMPLETE TOKEN SETUP")
    print("=" * 30)
    
    # 1. Check initial state
    check_balances()
    
    # 2. Approve tokens
    if not approve_tokens():
        print("❌ Approve fehlgeschlagen!")
        return False
    
    # 3. Deposit tokens
    if not deposit_with_allowance():
        print("❌ Deposit fehlgeschlagen!")
        return False
    
    # 4. Test arbitrage
    if test_arbitrage_after_deposit():
        print("\n🎉 COMPLETE SUCCESS!")
        print("✅ Contract hat Token Balance")
        print("✅ Arbitrage Funktionen bereit")
        print("🚀 Bereit für Live-Trading!")
        return True
    else:
        print("\n⚠️  Setup erfolgreich, aber Arbitrage noch Probleme")
        return False

if __name__ == "__main__":
    main()
