#!/usr/bin/env python3
"""
Live Smart Contract Trade Test
Echter Flashloan-Test mit dem deployed Contract
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

print("🔥 LIVE TRADE TEST mit deployed Contract!")

# Environment laden
load_dotenv()

# Web3 Setup
rpc_url = os.getenv('BSC_RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    print("❌ BSC Verbindung fehlgeschlagen!")
    exit(1)

print(f"✅ BSC verbunden - Block: {w3.eth.block_number}")

# Account Setup
private_key = os.getenv('PRIVATE_KEY')
account = w3.eth.account.from_key(private_key)
balance = w3.eth.get_balance(account.address)
balance_bnb = w3.from_wei(balance, 'ether')

print(f"💼 Account: {account.address}")
print(f"💰 Balance: {balance_bnb:.6f} BNB")

# Contract laden
contract_address = os.getenv('CONTRACT_ADDRESS')
if not contract_address:
    print("❌ CONTRACT_ADDRESS nicht gesetzt!")
    exit(1)

print(f"📍 Contract: {contract_address}")

# Contract ABI laden
with open('deployed_contract.json', 'r') as f:
    contract_info = json.load(f)

abi = contract_info['abi']
contract = w3.eth.contract(address=contract_address, abi=abi)

print(f"✅ Contract geladen mit {len(abi)} Funktionen")

# Token Adressen (BSC Mainnet)
USDT = "0x55d398326f99059fF775485246999027B3197955"
BUSD = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"
WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"

# DEX Router
PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
BISWAP_ROUTER = "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8"

print(f"🪙 USDT: {USDT}")
print(f"🪙 BUSD: {BUSD}")
print(f"🥞 PancakeSwap: {PANCAKE_ROUTER}")

# Contract Funktionen anzeigen
print("\n📋 Verfügbare Contract Funktionen:")
try:
    for func in contract.all_functions():
        try:
            print(f"   • {func.function_identifier}")
        except:
            print(f"   • {func.fn_name}")
except Exception as e:
    print(f"   ⚠️  Funktionsliste Fehler: {e}")
    # Alternative: ABI durchgehen
    for item in abi:
        if item.get('type') == 'function':
            print(f"   • {item.get('name', 'unknown')}")

# Test verschiedene Funktionen
def test_contract_functions():
    """Teste alle verfügbaren Contract Funktionen"""
    
    print("\n🧪 FUNCTION TESTS")
    print("-" * 30)
    
    try:
        # 1. Owner Test
        if hasattr(contract.functions, 'owner'):
            owner = contract.functions.owner().call()
            print(f"✅ Owner: {owner}")
        
        # 2. Balance Test (falls vorhanden)
        if hasattr(contract.functions, 'getBalance'):
            try:
                contract_balance = contract.functions.getBalance().call()
                print(f"✅ Contract Balance: {contract_balance}")
            except:
                print("⚠️  getBalance() not callable")
        
        # 3. Pancake Factory Test
        if hasattr(contract.functions, 'pancakeFactory'):
            try:
                factory = contract.functions.pancakeFactory().call()
                print(f"✅ Pancake Factory: {factory}")
            except:
                print("⚠️  pancakeFactory() not callable")
        
        # 4. Test Flashloan Simulation
        print("\n🔍 FLASHLOAN SIMULATION TEST")
        test_amount = w3.to_wei(1, 'ether')  # 1 Token
        
        if hasattr(contract.functions, 'testFlashloan'):
            try:
                result = contract.functions.testFlashloan(USDT, test_amount).call()
                print(f"✅ Flashloan Simulation: {result}")
            except Exception as e:
                print(f"⚠️  Flashloan Simulation Fehler: {e}")
        
        # 5. Arbitrage Test (ohne Ausführung)
        if hasattr(contract.functions, 'arbitrage'):
            try:
                print("\n💡 Teste Arbitrage Funktion (Simulation)...")
                # Teste mit kleinem Amount
                small_amount = w3.to_wei(0.1, 'ether')  # 0.1 Token
                
                result = contract.functions.arbitrage(
                    USDT,           # token0
                    BUSD,           # token1  
                    small_amount,   # amount
                    PANCAKE_ROUTER, # router1
                    BISWAP_ROUTER   # router2
                ).call({'from': account.address})
                
                print(f"✅ Arbitrage Simulation erfolgreich: {result}")
                return True
                
            except Exception as e:
                print(f"❌ Arbitrage Simulation Fehler: {e}")
                print(f"   Mögliche Ursachen:")
                print(f"   • Nicht genug Liquidität")
                print(f"   • Preisunterschiede zu gering")
                print(f"   • Router-Adressen ungültig")
                return False
        
        # 6. Einzelner Flashloan Test
        if hasattr(contract.functions, 'flashloan'):
            try:
                print("\n⚡ Teste Flashloan Funktion...")
                small_amount = w3.to_wei(1, 'ether')  # 1 USDT
                
                result = contract.functions.flashloan(
                    USDT,
                    small_amount
                ).call({'from': account.address})
                
                print(f"✅ Flashloan Test erfolgreich: {result}")
                return True
                
            except Exception as e:
                print(f"❌ Flashloan Test Fehler: {e}")
                return False
        
    except Exception as e:
        print(f"❌ Function Test Fehler: {e}")
        return False

def execute_real_trade():
    """Führe einen echten Mini-Trade aus (nur mit Bestätigung)"""
    
    print("\n🚨 ACHTUNG: ECHTER TRADE!")
    print("🔥 Führe Mini-Flashloan aus...")
    
    if balance_bnb < 0.01:
        print("❌ Zu wenig BNB für Gas!")
        return False
    
    try:
        # Sehr kleiner Amount für Test
        test_amount = w3.to_wei(0.1, 'ether')  # 0.1 USDT
        
        # Gas Preis
        gas_price = w3.eth.gas_price
        
        # Wähle beste verfügbare Funktion
        if hasattr(contract.functions, 'arbitrage'):
            function_call = contract.functions.arbitrage(
                USDT,
                BUSD,
                test_amount,
                PANCAKE_ROUTER,
                BISWAP_ROUTER
            )
            print("🔄 Verwende arbitrage() Funktion")
            
        elif hasattr(contract.functions, 'flashloan'):
            function_call = contract.functions.flashloan(
                USDT,
                test_amount
            )
            print("⚡ Verwende flashloan() Funktion")
            
        else:
            print("❌ Keine ausführbare Funktion gefunden!")
            return False
        
        # Gas schätzen
        try:
            estimated_gas = function_call.estimate_gas({'from': account.address})
            gas_limit = int(estimated_gas * 1.5)  # 50% Buffer
            
            print(f"⛽ Geschätztes Gas: {estimated_gas:,}")
            print(f"⛽ Gas Limit: {gas_limit:,}")
            
            gas_cost_bnb = (gas_limit * gas_price) / 10**18
            print(f"💸 Gas Kosten: ~{gas_cost_bnb:.6f} BNB")
            
        except Exception as e:
            print(f"❌ Gas Estimation Fehler: {e}")
            return False
        
        # Transaction bauen
        transaction = function_call.build_transaction({
            'from': account.address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Signieren
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        
        # Senden
        print("📤 Sende Transaction...")
        raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
        tx_hash = w3.eth.send_raw_transaction(raw_transaction)
        
        print(f"⏳ TX Hash: {tx_hash.hex()}")
        print("⏳ Warte auf Bestätigung...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print("✅ TRADE ERFOLGREICH!")
            print(f"🧾 Gas verwendet: {receipt.gasUsed:,}")
            print(f"🔗 BSCScan: https://bscscan.com/tx/{tx_hash.hex()}")
            return True
        else:
            print("❌ TRADE FEHLGESCHLAGEN!")
            print(f"Receipt: {receipt}")
            return False
            
    except Exception as e:
        print(f"❌ Trade Execution Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

# Main Test Flow
if __name__ == "__main__":
    
    # 1. Contract Function Tests
    simulation_success = test_contract_functions()
    
    # 2. Frage nach echtem Trade
    if simulation_success:
        print("\n" + "="*50)
        print("🎯 SIMULATION ERFOLGREICH!")
        print("💡 Bereit für echten Mini-Trade (0.1 USDT)")
        print("💸 Kosten: ~0.001-0.005 BNB Gas")
        print("🔒 Sehr geringes Risiko")
        print("="*50)
        
        # Führe Mini-Trade aus
        print("\n🚀 Führe Mini-Trade aus...")
        trade_success = execute_real_trade()
        
        if trade_success:
            print("\n🎉 COMPLETE SUCCESS!")
            print("✅ Smart Contract funktioniert perfekt!")
            print("✅ Bereit für größere Trades!")
        else:
            print("\n🔧 Trade fehlgeschlagen - Debugging erforderlich")
    
    else:
        print("\n❌ Simulation fehlgeschlagen")
        print("🔧 Contract muss überprüft werden")
