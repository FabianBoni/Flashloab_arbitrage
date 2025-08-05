#!/usr/bin/env python3
"""
Production Readiness Check
Überprüft alle kritischen Komponenten vor Live-Trading
"""

import os
import json
import asyncio
from web3 import Web3
from dotenv import load_dotenv

async def check_production_readiness():
    """Comprehensive production readiness check"""
    print("🔴 PRODUCTION READINESS CHECK")
    print("=" * 50)
    
    issues = []
    warnings = []
    
    # Load environment
    load_dotenv()
    
    # 1. BSC Connection Check
    print("\n1️⃣ BSC Connection...")
    rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if w3.is_connected():
        block = w3.eth.block_number
        print(f"   ✅ Connected to BSC - Block: {block}")
    else:
        issues.append("❌ BSC connection failed")
        print("   ❌ BSC connection failed")
    
    # 2. Account & Balance Check
    print("\n2️⃣ Account & Balance...")
    private_key = os.getenv('PRIVATE_KEY')
    if private_key:
        account = w3.eth.account.from_key(private_key)
        balance = w3.eth.get_balance(account.address)
        balance_bnb = w3.from_wei(balance, 'ether')
        
        print(f"   ✅ Account: {account.address}")
        print(f"   💰 Balance: {balance_bnb:.6f} BNB")
        
        # Balance warnings
        if balance_bnb < 0.01:
            warnings.append("⚠️  Low BNB balance for gas fees")
        if balance_bnb < 0.001:
            issues.append("❌ Insufficient BNB for gas fees")
    else:
        issues.append("❌ No PRIVATE_KEY configured")
        print("   ❌ No PRIVATE_KEY configured")
    
    # 3. Smart Contract Check
    print("\n3️⃣ Smart Contract...")
    if os.path.exists('deployed_contract.json'):
        with open('deployed_contract.json', 'r') as f:
            contract_data = json.load(f)
        
        contract_address = contract_data.get('address')
        if contract_address:
            # Check if contract exists on blockchain
            code = w3.eth.get_code(contract_address)
            if code and code != b'\\x':
                print(f"   ✅ Contract deployed: {contract_address}")
                
                # Check contract balance (USDT)
                usdt_contract = "0x55d398326f99059fF775485246999027B3197955"  # BSC USDT
                usdt_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
                usdt = w3.eth.contract(address=usdt_contract, abi=usdt_abi)
                
                try:
                    contract_usdt_balance = usdt.functions.balanceOf(contract_address).call()
                    contract_usdt_formatted = contract_usdt_balance / 1e18
                    print(f"   💰 Contract USDT: {contract_usdt_formatted:.6f}")
                    
                    if contract_usdt_formatted < 0.1:
                        warnings.append("⚠️  Low contract USDT balance")
                    if contract_usdt_formatted < 0.01:
                        issues.append("❌ Insufficient contract USDT for trades")
                except Exception as e:
                    warnings.append("⚠️  Could not check contract USDT balance")
                    
            else:
                issues.append("❌ Contract not found on blockchain")
                print("   ❌ Contract not found on blockchain")
        else:
            issues.append("❌ No contract address in deployed_contract.json")
            print("   ❌ No contract address in deployed_contract.json")
    else:
        issues.append("❌ deployed_contract.json not found")
        print("   ❌ deployed_contract.json not found")
    
    # 4. Environment Variables Check
    print("\n4️⃣ Environment Variables...")
    critical_vars = {
        'BSC_RPC_URL': 'BSC RPC endpoint',
        'PRIVATE_KEY': 'Trading account private key',
        'MIN_PROFIT_THRESHOLD': 'Minimum profit threshold',
        'MAX_GAS_PRICE': 'Maximum gas price',
    }
    
    optional_vars = {
        'TELEGRAM_BOT_TOKEN': 'Telegram notifications',
        'BINANCE_API_KEY': 'Binance CEX integration',
        'GATE_API_KEY': 'Gate.io CEX integration',
    }
    
    for var, desc in critical_vars.items():
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'TOKEN' in var:
                print(f"   ✅ {var}: ***{value[-4:]}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            issues.append(f"❌ Missing critical variable: {var}")
            print(f"   ❌ {var}: MISSING ({desc})")
    
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'TOKEN' in var:
                print(f"   ✅ {var}: ***{value[-4:]}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            warnings.append(f"⚠️  Optional variable missing: {var}")
            print(f"   ⚠️  {var}: MISSING ({desc})")
    
    # 5. Safety Configuration Check
    print("\n5️⃣ Safety Configuration...")
    min_profit = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5'))
    max_gas = float(os.getenv('MAX_GAS_PRICE', '5'))
    scan_interval = int(os.getenv('SCAN_INTERVAL', '10'))
    
    print(f"   📊 Min Profit: {min_profit}%")
    print(f"   ⛽ Max Gas: {max_gas} Gwei")
    print(f"   ⏱️  Scan Interval: {scan_interval}s")
    
    if min_profit < 0.3:
        warnings.append("⚠️  Very low profit threshold - high risk")
    if max_gas > 10:
        warnings.append("⚠️  High gas price limit")
    if scan_interval < 5:
        warnings.append("⚠️  Very fast scanning may hit rate limits")
    
    # 6. Results Summary
    print("\n" + "=" * 50)
    print("📋 PRODUCTION READINESS SUMMARY")
    print("=" * 50)
    
    if not issues:
        print("✅ ALL CRITICAL CHECKS PASSED")
        print("🔴 SYSTEM READY FOR LIVE TRADING")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} Warning(s):")
            for warning in warnings:
                print(f"   {warning}")
    else:
        print(f"❌ {len(issues)} Critical Issue(s) Found:")
        for issue in issues:
            print(f"   {issue}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} Warning(s):")
            for warning in warnings:
                print(f"   {warning}")
        
        print("\n🛑 RESOLVE ISSUES BEFORE PRODUCTION")
    
    return len(issues) == 0

if __name__ == "__main__":
    asyncio.run(check_production_readiness())
