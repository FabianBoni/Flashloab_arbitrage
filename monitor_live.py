#!/usr/bin/env python3
"""
Live Production Monitor
Überwacht das Live-Trading System in Echtzeit
"""

import time
import os
from datetime import datetime

def monitor_live_trading():
    """Monitor live trading system"""
    print("🔴 LIVE TRADING MONITOR")
    print("=" * 50)
    print("📊 Monitoring BSC Arbitrage System...")
    print("🔄 Press Ctrl+C to stop monitoring\n")
    
    log_file = "logs/arbitrage_main.log"
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return
    
    # Track statistics
    stats = {
        'scans': 0,
        'opportunities': 0,
        'trades': 0,
        'profits': [],
        'start_time': time.time()
    }
    
    # Read existing log content
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Get the last position in the file
    last_position = len(lines)
    
    try:
        while True:
            # Read new lines
            with open(log_file, 'r') as f:
                current_lines = f.readlines()
            
            if len(current_lines) > last_position:
                new_lines = current_lines[last_position:]
                last_position = len(current_lines)
                
                # Process new log entries
                for line in new_lines:
                    line = line.strip()
                    
                    # Count scans
                    if "Scanning for" in line:
                        stats['scans'] += 1
                    
                    # Count opportunities
                    if "Found" in line and "profitable opportunities" in line:
                        try:
                            count = int(line.split("Found ")[1].split(" profitable")[0])
                            stats['opportunities'] += count
                        except:
                            pass
                    
                    # Count trades
                    if "LIVE TRADE: Executing" in line:
                        stats['trades'] += 1
                    
                    # Track profits
                    if "Trade executed successfully" in line:
                        # Parse profit if available
                        pass
                    
                    # Display important events
                    if any(keyword in line for keyword in [
                        "LIVE TRADE:", "Trade executed", "opportunities",
                        "ERROR", "WARNING", "Connected to BSC"
                    ]):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] {line.split(' - ')[-1] if ' - ' in line else line}")
            
            # Display statistics every 30 seconds
            if int(time.time()) % 30 == 0:
                uptime = (time.time() - stats['start_time']) / 3600
                
                print("\\n" + "="*50)
                print(f"📊 LIVE STATS - Uptime: {uptime:.1f}h")
                print(f"🔍 Scans completed: {stats['scans']:,}")
                print(f"🎯 Opportunities found: {stats['opportunities']:,}")
                print(f"⚡ Trades executed: {stats['trades']:,}")
                print(f"📈 Success rate: {(stats['trades']/max(stats['opportunities'],1)*100):.1f}%" if stats['opportunities'] > 0 else "📈 Success rate: 0%")
                print("="*50 + "\\n")
                
                time.sleep(1)  # Prevent multiple prints in the same second
            
            time.sleep(0.5)  # Check for new logs every 0.5 seconds
            
    except KeyboardInterrupt:
        print("\\n🛑 Monitoring stopped")
        
        # Final statistics
        uptime = (time.time() - stats['start_time']) / 3600
        print("\\n📋 FINAL STATISTICS:")
        print(f"   ⏱️ Uptime: {uptime:.2f} hours")
        print(f"   🔍 Total scans: {stats['scans']:,}")
        print(f"   🎯 Total opportunities: {stats['opportunities']:,}")
        print(f"   ⚡ Total trades: {stats['trades']:,}")
        if stats['opportunities'] > 0:
            print(f"   📈 Success rate: {(stats['trades']/stats['opportunities']*100):.1f}%")

if __name__ == "__main__":
    monitor_live_trading()
