#!/usr/bin/env python3
"""
Corrected Live Trade Test
Verwendet die tatsächlich verfügbaren Contract-Funktionen
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

print("🔥 CORRECTED LIVE TRADE TEST!")

# Environment laden
load_dotenv()

# Web3 Setup
rpc_url = os.getenv('BSC_RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))
print(f"✅ BSC verbunden - Block: {w3.eth.block_number}")

# Account Setup
private_key = os.getenv('PRIVATE_KEY')
account = w3.eth.account.from_key(private_key)
balance = w3.eth.get_balance(account.address)
balance_bnb = w3.from_wei(balance, 'ether')

print(f"💼 Account: {account.address}")
print(f"💰 Balance: {balance_bnb:.6f} BNB")

# Contract Setup
contract_address = os.getenv('CONTRACT_ADDRESS')
with open('deployed_contract.json', 'r') as f:
    contract_info = json.load(f)

abi = contract_info['abi']
contract = w3.eth.contract(address=contract_address, abi=abi)

print(f"📍 Contract: {contract_address}")

# Token-Adressen aus Contract abrufen
print("\n🪙 TOKEN ADDRESSES FROM CONTRACT:")
try:
    usdt_addr = contract.functions.USDT().call()
    busd_addr = contract.functions.BUSD().call()
    wbnb_addr = contract.functions.WBNB().call()
    
    print(f"USDT: {usdt_addr}")
    print(f"BUSD: {busd_addr}")
    print(f"WBNB: {wbnb_addr}")
except Exception as e:
    print(f"⚠️  Token Address Fehler: {e}")

# Router-Adressen aus Contract
print("\n🔄 DEX ROUTERS FROM CONTRACT:")
try:
    pancake_router = contract.functions.PANCAKESWAP_ROUTER().call()
    biswap_router = contract.functions.BISWAP_ROUTER().call()
    apeswap_router = contract.functions.APESWAP_ROUTER().call()
    
    print(f"PancakeSwap: {pancake_router}")
    print(f"Biswap: {biswap_router}")
    print(f"ApeSwap: {apeswap_router}")
except Exception as e:
    print(f"⚠️  Router Address Fehler: {e}")

def test_contract_functions():
    """Teste die tatsächlich verfügbaren Funktionen"""
    
    print("\n🧪 TESTING ACTUAL CONTRACT FUNCTIONS")
    print("-" * 40)
    
    try:
        # 1. Owner Check
        owner = contract.functions.owner().call()
        print(f"✅ Owner: {owner}")
        
        # 2. Contract Token Balance
        usdt_balance = contract.functions.getTokenBalance(usdt_addr).call()
        print(f"✅ Contract USDT Balance: {usdt_balance}")
        
        # 3. Check Arbitrage Profit (Simulation)
        print("\n💡 TESTING ARBITRAGE PROFIT CHECK...")
        test_amount = w3.to_wei(1, 'ether')  # 1 USDT
        
        try:
            profit = contract.functions.checkArbitrageProfit(
                usdt_addr,      # tokenA
                busd_addr,      # tokenB  
                test_amount,    # amount
                pancake_router, # routerA
                biswap_router   # routerB
            ).call()
            
            print(f"✅ Arbitrage Profit Check: {profit}")
            
            # Profit interpretieren
            if profit > 0:
                profit_ether = w3.from_wei(profit, 'ether')
                print(f"💰 Erwarteter Profit: {profit_ether:.6f} Tokens")
                return True
            else:
                print(f"⚠️  Kein Profit möglich: {profit}")
                return False
                
        except Exception as e:
            print(f"❌ Arbitrage Profit Check Fehler: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Function Test Fehler: {e}")
        return False

def test_simple_arbitrage():
    """Teste Simple Arbitrage Funktion"""
    
    print("\n⚡ TESTING SIMPLE ARBITRAGE")
    print("-" * 30)
    
    try:
        test_amount = w3.to_wei(1, 'ether')  # 1 USDT
        
        # Simulation
        try:
            result = contract.functions.executeSimpleArbitrage(
                usdt_addr,      # tokenA
                busd_addr,      # tokenB
                test_amount,    # amount  
                pancake_router, # buyRouter
                biswap_router   # sellRouter
            ).call({'from': account.address})
            
            print(f"✅ Simple Arbitrage Simulation erfolgreich!")
            print(f"📊 Result: {result}")
            return True
            
        except Exception as e:
            print(f"❌ Simple Arbitrage Simulation Fehler: {e}")
            
            # Versuche mit anderen Parametern
            try:
                smaller_amount = w3.to_wei(0.1, 'ether')  # 0.1 USDT
                result = contract.functions.executeSimpleArbitrage(
                    usdt_addr,
                    busd_addr,
                    smaller_amount,
                    pancake_router,
                    biswap_router
                ).call({'from': account.address})
                
                print(f"✅ Simple Arbitrage (kleiner Amount) erfolgreich!")
                return True
                
            except Exception as e2:
                print(f"❌ Auch kleinerer Amount fehlgeschlagen: {e2}")
                return False
    
    except Exception as e:
        print(f"❌ Simple Arbitrage Test Fehler: {e}")
        return False

def execute_real_arbitrage():
    """Führe echten Arbitrage-Trade aus"""
    
    print("\n🚨 REAL ARBITRAGE EXECUTION")
    print("-" * 30)
    
    if balance_bnb < 0.01:
        print("❌ Zu wenig BNB für Gas!")
        return False
    
    try:
        # Sehr kleiner Test-Amount
        test_amount = w3.to_wei(0.1, 'ether')  # 0.1 USDT
        
        # Gas Preis
        gas_price = w3.eth.gas_price
        print(f"⛽ Gas Preis: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
        
        # Verwende executeSimpleArbitrage
        function_call = contract.functions.executeSimpleArbitrage(
            usdt_addr,
            busd_addr,
            test_amount,
            pancake_router,
            biswap_router
        )
        
        # Gas schätzen
        try:
            estimated_gas = function_call.estimate_gas({'from': account.address})
            gas_limit = int(estimated_gas * 1.5)
            
            print(f"⛽ Estimated Gas: {estimated_gas:,}")
            print(f"💸 Gas Cost: ~{(gas_limit * gas_price) / 10**18:.6f} BNB")
            
        except Exception as e:
            print(f"❌ Gas Estimation Fehler: {e}")
            # Verwende Standard Gas Limit
            gas_limit = 500000
            print(f"⚠️  Verwende Standard Gas Limit: {gas_limit:,}")
        
        # Transaction bauen
        transaction = function_call.build_transaction({
            'from': account.address,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Signieren und senden
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        
        print("📤 Sende Real Arbitrage Transaction...")
        raw_transaction = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
        tx_hash = w3.eth.send_raw_transaction(raw_transaction)
        
        print(f"⏳ TX Hash: {tx_hash.hex()}")
        print("⏳ Warte auf Bestätigung...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            print("✅ ARBITRAGE TRADE ERFOLGREICH!")
            print(f"🧾 Gas verwendet: {receipt.gasUsed:,}")
            print(f"🔗 BSCScan: https://bscscan.com/tx/{tx_hash.hex()}")
            
            # Check Balances nach Trade
            new_balance = w3.eth.get_balance(account.address)
            new_balance_bnb = w3.from_wei(new_balance, 'ether')
            print(f"💰 Neue BNB Balance: {new_balance_bnb:.6f} BNB")
            
            return True
        else:
            print("❌ ARBITRAGE TRADE FEHLGESCHLAGEN!")
            print(f"Receipt Status: {receipt.status}")
            return False
            
    except Exception as e:
        print(f"❌ Real Arbitrage Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

# Main Execution
if __name__ == "__main__":
    
    print("\n" + "="*50)
    print("🎯 COMPREHENSIVE CONTRACT TEST")
    print("="*50)
    
    # Test 1: Basic Functions
    basic_success = test_contract_functions()
    
    # Test 2: Arbitrage Simulation  
    arbitrage_success = test_simple_arbitrage()
    
    # Test 3: Real Execution (nur wenn Simulation erfolgreich)
    if basic_success and arbitrage_success:
        print("\n🚀 SIMULATION ERFOLGREICH!")
        print("💡 Bereit für echten Mini-Arbitrage!")
        print("💸 Kosten: ~0.002-0.01 BNB")
        
        real_success = execute_real_arbitrage()
        
        if real_success:
            print("\n🎉 COMPLETE SUCCESS!")
            print("✅ Ihr Arbitrage System funktioniert!")
            print("✅ Bereit für Live-Trading!")
        else:
            print("\n🔧 Real Trade fehlgeschlagen")
    else:
        print("\n❌ Simulation fehlgeschlagen")
        print("🔧 Contract debugging erforderlich")
