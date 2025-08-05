#!/usr/bin/env python3
"""
Repository Cleanup Script
Entfernt alle nicht mehr benötigten Dateien und Scripts
"""

import os
import shutil
from pathlib import Path

def cleanup_repository():
    """Räumt das Repository auf"""
    
    print("🧹 REPOSITORY CLEANUP")
    print("=" * 30)
    
    # Dateien die gelöscht werden sollen
    files_to_delete = [
        # Alte main Versionen
        "main_backup.py",
        "main_enhanced.py", 
        "main_new.py",
        
        # Test Scripts (nicht mehr benötigt)
        "test_corrected_trade.py",
        "test_direct_arbitrage.py", 
        "test_live_trade.py",
        "test_simple_trade.py",
        "test_smart_contract.py",
        "test_system.py",
        "test_transaction_fix.py",
        "test_enhanced_telegram.py",
        "test_extended_scanner.py",
        "test_volatile_tokens.py",
        
        # Fix Scripts (einmalig verwendet)
        "fix_allowance.py",
        "fix_contract_balance.py", 
        "fix_raw_transaction.py",
        "verify_transaction_fixes.py",
        
        # Analyse Scripts (nicht mehr benötigt)
        "analyze_cex_limitations.py",
        "cleanup_repository.py",
        "improved_arbitrage_strategy.py",
        "practical_cex_dex_arbitrage.py",
        "volatile_token_dashboard.py",
        
        # Deployment Scripts (haben wir bessere Versionen)
        "deploy_to_pi.sh",
        
        # Summary Dateien (informativ aber nicht notwendig)
        "final_cex_summary.py",
        
        # Telegram Service (in enhanced_telegram_bot integriert)
        "telegram_command_service.py",
        
        # Alte README Versionen
        "README_ENHANCED.md",
        "README_PRODUCTION.md"
    ]
    
    # Verzeichnisse die aufgeräumt werden sollen
    dirs_to_clean = [
        "__pycache__",
        ".venv",
        "node_modules", 
        "cache"
    ]
    
    deleted_count = 0
    
    # Lösche Dateien
    print("\n🗑️  DELETING OBSOLETE FILES:")
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   ✅ Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ Failed to delete {file}: {e}")
        else:
            print(f"   ⚠️  Not found: {file}")
    
    # Lösche Verzeichnisse
    print("\n📁 CLEANING DIRECTORIES:")
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"   ✅ Removed directory: {dir_name}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {dir_name}: {e}")
        else:
            print(f"   ⚠️  Not found: {dir_name}")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   🗑️  Files/Dirs deleted: {deleted_count}")
    print(f"   ✅ Repository cleaned!")
    
    # Zeige verbleibende wichtige Dateien
    print(f"\n📋 CORE FILES REMAINING:")
    core_files = [
        "main.py",
        "enhanced_telegram_bot.py",
        "cex_price_provider.py", 
        "cex_trading_api.py",
        "unified_arbitrage_scanner.py",
        "optimization_config.py",
        "deployed_contract.json",
        "deploy_contract.py",
        "pi_deployment.py",
        "requirements.txt",
        "docker-compose.yml",
        "Dockerfile",
        ".env",
        "README.md"
    ]
    
    for file in core_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ MISSING: {file}")
    
    return deleted_count

if __name__ == "__main__":
    cleanup_repository()
    print("\n🎉 REPOSITORY CLEANUP COMPLETE!")
    print("🚀 Your system is now clean and ready!")
