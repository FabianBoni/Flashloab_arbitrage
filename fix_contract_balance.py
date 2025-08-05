#!/usr/bin/env python3
"""
Fix Contract Balance - Deposit Token zum Contract
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

print("💰 CONTRACT BALANCE FIX")

# Setup
load_dotenv()
rpc_url = os.getenv('BSC_RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))
private_key = os.getenv('PRIVATE_KEY')
account = w3.eth.account.from_key(private_key)

print(f"💼 Account: {account.address}")
print(f"💰 BNB Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether'):.6f}")

# Contract Setup
contract_address = os.getenv('CONTRACT_ADDRESS')
with open('deployed_contract.json', 'r') as f:
    contract_info = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=contract_info['abi'])

# Token Adressen
usdt_addr = contract.functions.USDT().call()
busd_addr = contract.functions.BUSD().call()

print(f"🪙 USDT: {usdt_addr}")
print(f"🪙 BUSD: {busd_addr}")

# ERC20 ABI für Token-Interaktion
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
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

def check_token_balances():
    """Check User und Contract Token Balances"""
    
    print("\n📊 TOKEN BALANCE CHECK")
    print("-" * 30)
    
    usdt_contract = w3.eth.contract(address=usdt_addr, abi=erc20_abi)
    busd_contract = w3.eth.contract(address=busd_addr, abi=erc20_abi)
    
    # User Balances
    user_usdt = usdt_contract.functions.balanceOf(account.address).call()
    user_busd = busd_contract.functions.balanceOf(account.address).call()
    
    # Contract Balances
    contract_usdt = usdt_contract.functions.balanceOf(contract_address).call()
    contract_busd = busd_contract.functions.balanceOf(contract_address).call()
    
    print(f"👤 User USDT: {w3.from_wei(user_usdt, 'ether'):.6f}")
    print(f"👤 User BUSD: {w3.from_wei(user_busd, 'ether'):.6f}")
    print(f"📍 Contract USDT: {w3.from_wei(contract_usdt, 'ether'):.6f}")
    print(f"📍 Contract BUSD: {w3.from_wei(contract_busd, 'ether'):.6f}")
    
    return {
        'user_usdt': user_usdt,
        'user_busd': user_busd,
        'contract_usdt': contract_usdt,
        'contract_busd': contract_busd
    }

def buy_usdt_with_bnb():
    """Kaufe USDT mit BNB über PancakeSwap"""
    
    print("\n💸 BUYING USDT WITH BNB")
    print("-" * 25)
    
    # PancakeSwap Router
    pancake_router = contract.functions.PANCAKESWAP_ROUTER().call()
    wbnb_addr = contract.functions.WBNB().call()
    
    router_abi = [
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactETHForTokens",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    
    router_contract = w3.eth.contract(address=pancake_router, abi=router_abi)
    
    try:
        # 0.01 BNB für USDT
        bnb_amount = w3.to_wei(0.01, 'ether')
        
        # Path: BNB -> USDT
        path = [wbnb_addr, usdt_addr]
        
        # Deadline (10 Minuten)
        deadline = w3.eth.get_block('latest').timestamp + 600
        
        # Gas
        gas_price = w3.eth.gas_price
        
        # Transaction bauen
        transaction = router_contract.functions.swapExactETHForTokens(
            0,  # amountOutMin (0 für Test)
            path,
            account.address,
            deadline
        ).build_transaction({
            'from': account.address,
            'value': bnb_amount,
            'gas': 300000,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        print(f"💸 Tausche 0.01 BNB für USDT...")
        
        # Signieren und senden
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
        tx_hash = w3.eth.send_raw_transaction(raw_transaction)
        
        print(f"⏳ TX Hash: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print("✅ USDT Kauf erfolgreich!")
            return True
        else:
            print("❌ USDT Kauf fehlgeschlagen!")
            return False
            
    except Exception as e:
        print(f"❌ USDT Kauf Fehler: {e}")
        return False

def deposit_tokens_to_contract():
    """Deponiere Token zum Contract"""
    
    print("\n📥 DEPOSITING TOKENS TO CONTRACT")
    print("-" * 35)
    
    balances = check_token_balances()
    
    if balances['user_usdt'] == 0:
        print("⚠️  Keine USDT vorhanden - kaufe zuerst USDT...")
        if not buy_usdt_with_bnb():
            return False
        
        # Update Balances
        balances = check_token_balances()
    
    if balances['user_usdt'] > 0:
        try:
            # Deponiere die Hälfte der USDT
            deposit_amount = balances['user_usdt'] // 2
            
            print(f"📥 Deponiere {w3.from_wei(deposit_amount, 'ether'):.6f} USDT zum Contract...")
            
            # Verwende depositToken Funktion
            function_call = contract.functions.depositToken(
                usdt_addr,
                deposit_amount
            )
            
            # Gas
            gas_price = w3.eth.gas_price
            estimated_gas = function_call.estimate_gas({'from': account.address})
            
            transaction = function_call.build_transaction({
                'from': account.address,
                'gas': int(estimated_gas * 1.2),
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(account.address)
            })
            
            # Signieren und senden
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
            tx_hash = w3.eth.send_raw_transaction(raw_transaction)
            
            print(f"⏳ Deposit TX Hash: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print("✅ Token Deposit erfolgreich!")
                return True
            else:
                print("❌ Token Deposit fehlgeschlagen!")
                return False
                
        except Exception as e:
            print(f"❌ Token Deposit Fehler: {e}")
            
            # Alternative: Direkte Transfer
            try:
                print("🔄 Versuche direkten Transfer...")
                
                usdt_contract = w3.eth.contract(address=usdt_addr, abi=erc20_abi)
                transfer_amount = balances['user_usdt'] // 2
                
                transfer_txn = usdt_contract.functions.transfer(
                    contract_address,
                    transfer_amount
                ).build_transaction({
                    'from': account.address,
                    'gas': 100000,
                    'gasPrice': gas_price,
                    'nonce': w3.eth.get_transaction_count(account.address)
                })
                
                signed_txn = w3.eth.account.sign_transaction(transfer_txn, private_key)
                raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
                tx_hash = w3.eth.send_raw_transaction(raw_transaction)
                
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                
                if receipt.status == 1:
                    print("✅ Direkter Transfer erfolgreich!")
                    return True
                    
            except Exception as e2:
                print(f"❌ Direkter Transfer auch fehlgeschlagen: {e2}")
                return False
    
    return False

def main():
    """Main execution"""
    
    print("🎯 CONTRACT BALANCE SETUP")
    print("=" * 30)
    
    # 1. Check aktuelle Balances
    initial_balances = check_token_balances()
    
    # 2. Kaufe USDT falls nötig
    if initial_balances['user_usdt'] == 0:
        print("\n💸 Kein USDT vorhanden - kaufe mit BNB...")
        buy_usdt_with_bnb()
    
    # 3. Deponiere zum Contract
    deposit_success = deposit_tokens_to_contract()
    
    # 4. Final Balance Check
    print("\n📊 FINAL BALANCE CHECK")
    final_balances = check_token_balances()
    
    if final_balances['contract_usdt'] > 0:
        print("\n✅ CONTRACT SETUP COMPLETE!")
        print("🚀 Contract hat jetzt USDT Balance")
        print("💡 Bereit für Arbitrage-Tests!")
        
        # Teste Contract nochmal
        print("\n🧪 Teste Contract mit Balance...")
        return True
    else:
        print("\n❌ Contract Setup fehlgeschlagen")
        print("🔧 Manuelle Intervention erforderlich")
        return False

if __name__ == "__main__":
    main()
