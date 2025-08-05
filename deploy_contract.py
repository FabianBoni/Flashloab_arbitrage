#!/usr/bin/env python3
"""
BSC Smart Contract Deployment
Deployed den Flashloan Contract und speichert die Adresse
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

print("🚀 BSC Contract Deployment...")

# Environment laden
load_dotenv()

# Web3 Setup
rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("❌ BSC Verbindung fehlgeschlagen!")
    exit(1)

print(f"✅ BSC verbunden - Block: {w3.eth.block_number}")

# Account Setup
private_key = os.getenv('PRIVATE_KEY')
if not private_key:
    print("❌ PRIVATE_KEY fehlt!")
    exit(1)

account = w3.eth.account.from_key(private_key)
balance = w3.eth.get_balance(account.address)
balance_bnb = w3.from_wei(balance, 'ether')

print(f"💼 Account: {account.address}")
print(f"💰 Balance: {balance_bnb:.6f} BNB")

if balance_bnb < 0.02:
    print("❌ Zu wenig BNB für Deployment!")
    exit(1)

# Contract laden
contract_file = "artifacts/contracts/BSCFlashloanArbitrage.sol/BSCFlashloanArbitrage.json"

if not os.path.exists(contract_file):
    print(f"❌ Contract file nicht gefunden: {contract_file}")
    exit(1)

with open(contract_file, 'r') as f:
    contract_data = json.load(f)

abi = contract_data['abi']
bytecode = contract_data['bytecode']

print(f"📋 Contract ABI geladen: {len(abi)} Funktionen")

# Contract deployen
print("\n🚀 Deploying Contract...")

contract = w3.eth.contract(abi=abi, bytecode=bytecode)

# Gas Preis
gas_price = w3.eth.gas_price
gas_price_gwei = w3.from_wei(gas_price, 'gwei')
print(f"⛽ Gas Preis: {gas_price_gwei:.2f} Gwei")

try:
    # Constructor Transaction bauen
    constructor_txn = contract.constructor().build_transaction({
        'from': account.address,
        'gas': 3000000,  # 3M Gas Limit
        'gasPrice': gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    })

    print(f"💸 Deployment Kosten: ~{(constructor_txn['gas'] * gas_price) / 10**18:.6f} BNB")

    # Transaction signieren
    signed_txn = w3.eth.account.sign_transaction(constructor_txn, private_key)

    # Transaction senden
    print("📤 Sende Deployment Transaction...")
    # Fix für Web3.py Kompatibilität
    raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
    tx_hash = w3.eth.send_raw_transaction(raw_transaction)
    
    print(f"⏳ Transaction Hash: {tx_hash.hex()}")
    print("⏳ Warte auf Bestätigung...")

    # Auf Receipt warten
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

    if receipt.status == 1:
        contract_address = receipt.contractAddress
        print(f"✅ CONTRACT ERFOLGREICH DEPLOYED!")
        print(f"📍 Contract Address: {contract_address}")
        print(f"🧾 Gas verwendet: {receipt.gasUsed:,}")
        
        # Adresse in .env speichern
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # CONTRACT_ADDRESS hinzufügen oder ersetzen
            found = False
            for i, line in enumerate(lines):
                if line.startswith('CONTRACT_ADDRESS='):
                    lines[i] = f'CONTRACT_ADDRESS={contract_address}\n'
                    found = True
                    break
            
            if not found:
                lines.append(f'\nCONTRACT_ADDRESS={contract_address}\n')
            
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            print(f"✅ CONTRACT_ADDRESS in .env gespeichert")
        
        # Contract Info speichern
        contract_info = {
            "address": contract_address,
            "abi": abi,
            "deployment_block": receipt.blockNumber,
            "deployment_tx": tx_hash.hex(),
            "gas_used": receipt.gasUsed
        }
        
        with open("deployed_contract.json", 'w') as f:
            json.dump(contract_info, f, indent=2)
        
        print("✅ Contract Info in deployed_contract.json gespeichert")
        
        # Test Contract Call
        print("\n🧪 Teste deployed Contract...")
        deployed_contract = w3.eth.contract(address=contract_address, abi=abi)
        
        # Teste eine View-Funktion falls vorhanden
        try:
            # Teste owner() Funktion
            if hasattr(deployed_contract.functions, 'owner'):
                owner = deployed_contract.functions.owner().call()
                print(f"✅ Contract Owner: {owner}")
            
            print("✅ Contract Test erfolgreich!")
            
        except Exception as e:
            print(f"⚠️  Contract Test Fehler: {e}")
        
        print("\n🎉 DEPLOYMENT COMPLETE!")
        print(f"🔗 BSCScan: https://bscscan.com/address/{contract_address}")
        
    else:
        print("❌ Deployment fehlgeschlagen!")
        print(f"Receipt: {receipt}")

except Exception as e:
    print(f"❌ Deployment Fehler: {e}")
    import traceback
    traceback.print_exc()
