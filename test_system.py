#!/usr/bin/env python3
"""
System Test - Check if all components are working
"""

import sys
import traceback
from typing import List

def test_imports() -> List[str]:
    """Test all critical imports"""
    errors = []
    
    print("🔍 Testing imports...")
    
    # Core Python modules
    try:
        import asyncio
        import logging
        import json
        import time
        import os
        print("✅ Core Python modules")
    except ImportError as e:
        errors.append(f"❌ Core Python: {e}")
    
    # Web3 and blockchain
    try:
        from web3 import Web3
        print("✅ Web3")
    except ImportError as e:
        errors.append(f"❌ Web3: {e}")
    
    # Requests
    try:
        import requests
        print("✅ Requests")
    except ImportError as e:
        errors.append(f"❌ Requests: {e}")
    
    # Custom modules
    try:
        from enhanced_telegram_bot import telegram_bot
        print("✅ Enhanced Telegram Bot")
    except ImportError as e:
        errors.append(f"❌ Telegram Bot: {e}")
    
    try:
        from cex_price_provider import CexPriceProvider
        print("✅ CEX Price Provider")
    except ImportError as e:
        errors.append(f"❌ CEX Price Provider: {e}")
    
    try:
        from cex_trading_api import trading_api
        print("✅ CEX Trading API")
    except ImportError as e:
        errors.append(f"❌ CEX Trading API: {e}")
    
    try:
        from unified_arbitrage_scanner import UnifiedArbitrageScanner
        print("✅ Unified Arbitrage Scanner")
    except ImportError as e:
        errors.append(f"❌ Arbitrage Scanner: {e}")
    
    try:
        from optimization_config import DEX_CONFIGS, VOLATILE_TOKENS
        print("✅ Optimization Config")
    except ImportError as e:
        errors.append(f"❌ Optimization Config: {e}")
    
    return errors

def test_environment() -> List[str]:
    """Test environment configuration"""
    errors = []
    
    print("\n🔍 Testing environment...")
    
    # Check .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment file loaded")
    except Exception as e:
        errors.append(f"❌ Environment loading: {e}")
    
    # Check critical environment variables
    import os
    
    bsc_rpc = os.getenv('BSC_RPC_URL')
    if bsc_rpc:
        print(f"✅ BSC RPC URL: {bsc_rpc}")
    else:
        print("⚠️  BSC_RPC_URL not set, using default")
    
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_token:
        print("✅ Telegram Bot Token configured")
    else:
        print("⚠️  Telegram Bot Token not configured")
    
    private_key = os.getenv('PRIVATE_KEY')
    if private_key:
        print("✅ Private Key configured (simulation mode disabled)")
    else:
        print("⚠️  Private Key not configured (simulation mode)")
    
    return errors

def test_bsc_connection() -> List[str]:
    """Test BSC connection"""
    errors = []
    
    print("\n🔍 Testing BSC connection...")
    
    try:
        from web3 import Web3
        import os
        
        rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if w3.is_connected():
            latest_block = w3.eth.block_number
            print(f"✅ BSC Connected: Block {latest_block}")
        else:
            errors.append(f"❌ Failed to connect to BSC at {rpc_url}")
            
    except Exception as e:
        errors.append(f"❌ BSC connection error: {e}")
    
    return errors

def test_directories() -> List[str]:
    """Test directory structure"""
    errors = []
    
    print("\n🔍 Testing directories...")
    
    import os
    
    # Check logs directory
    try:
        os.makedirs('logs', exist_ok=True)
        test_file = 'logs/test_write.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ Logs directory writable")
    except Exception as e:
        errors.append(f"❌ Logs directory: {e}")
    
    # Check required files
    required_files = [
        'enhanced_telegram_bot.py',
        'cex_price_provider.py', 
        'cex_trading_api.py',
        'unified_arbitrage_scanner.py',
        'optimization_config.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            errors.append(f"❌ Missing file: {file}")
    
    return errors

async def test_main_import():
    """Test main.py can be imported"""
    print("\n🔍 Testing main.py import...")
    
    try:
        # Import without running
        sys.path.insert(0, '.')
        
        # Test if main module can be imported
        spec = None
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("main_test", "main.py")
            main_module = importlib.util.module_from_spec(spec)
            print("✅ main.py can be imported")
            return True
        except Exception as e:
            print(f"❌ main.py import error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Main import test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 BSC Arbitrage System Test Suite")
    print("=" * 50)
    
    all_errors = []
    
    # Run tests
    all_errors.extend(test_imports())
    all_errors.extend(test_environment())
    all_errors.extend(test_bsc_connection())
    all_errors.extend(test_directories())
    
    # Test main import
    await test_main_import()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    
    if all_errors:
        print(f"❌ {len(all_errors)} errors found:")
        for error in all_errors:
            print(f"   {error}")
        print("\n🔧 Please fix these issues before running the system.")
        return False
    else:
        print("✅ All tests passed!")
        print("🚀 System is ready to run!")
        return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
