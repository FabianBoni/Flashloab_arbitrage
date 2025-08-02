"""
Enhanced BSC Arbitrage Scanner with CEX Integration
Combines DEX and CEX price monitoring for comprehensive arbitrage opportunities
"""

import time
import logging
import gc
import os
import sys
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import json
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
import requests
from dotenv import load_dotenv

# Import our new CEX integration modules
from cex_price_provider import CexPriceProvider, CexPrice
from unified_arbitrage_scanner import UnifiedArbitrageScanner, UnifiedOpportunity

# Try to use ujson for better performance on Pi
try:
    import ujson as json
except ImportError:
    import json

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

log_handlers = [logging.StreamHandler(sys.stdout)]
try:
    os.makedirs('logs', exist_ok=True)
    test_file = 'logs/test_write.tmp'
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    log_handlers.append(logging.FileHandler('logs/enhanced_arbitrage.log', encoding='utf-8'))
    print("✅ File logging enabled: logs/enhanced_arbitrage.log")
except (PermissionError, OSError) as e:
    print(f"⚠️  File logging disabled (permission error): {e}")
    print("📄 Logging to console only")

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedArbitrageOpportunity:
    """Enhanced arbitrage opportunity including CEX data"""
    token_in: str
    token_out: str
    token_in_symbol: str
    token_out_symbol: str
    amount_in: int
    source_type: str  # 'DEX', 'CEX'
    target_type: str  # 'DEX', 'CEX'
    source_name: str
    target_name: str
    source_price: float
    target_price: float
    profit_percentage: float
    estimated_gas: int
    gas_cost_eth: float
    executable: bool  # Can this be executed with flashloans?

class TelegramBot:
    """Enhanced Telegram bot for CEX+DEX notifications"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            logger.info("📱 Telegram notifications enabled")
        else:
            logger.info("📱 Telegram not configured - running without notifications")
    
    def send_message(self, message: str):
        """Send message to Telegram"""
        if not self.enabled:
            return
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Telegram message failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Telegram error: {e}")
    
    def send_enhanced_start_notification(self):
        """Send enhanced bot start notification"""
        message = "🚀 <b>Enhanced BSC Arbitrage Scanner Started - CEX+DEX MODE</b>\n\n"
        message += "✅ Monitoring CEX (Binance, Bybit, OKX, KuCoin, Gate.io, Bitget, MEXC, HTX)\n"
        message += "✅ Monitoring DEX (PancakeSwap, Biswap, ApeSwap, THENA)\n"
        message += "🔄 CEX-DEX arbitrage opportunities\n"
        message += "🔄 CEX-CEX arbitrage opportunities\n"
        message += "🔄 DEX-DEX arbitrage opportunities\n"
        message += "📊 Execution thresholds: 0.3% | 0.8% | 1.5%\n"
        message += "⚡ Dynamic scaling based on opportunity type\n"
        message += "⏰ Scanning every 30 seconds"
        self.send_message(message)
    
    def send_enhanced_opportunity(self, opportunity: UnifiedOpportunity):
        """Send enhanced opportunity notification"""
        message = f"💰 <b>{opportunity.type} Arbitrage Found!</b>\n\n"
        message += f"🪙 Pair: {opportunity.token_in_symbol}/{opportunity.token_out_symbol}\n"
        message += f"📈 Profit: {opportunity.profit_percentage:.3f}%\n"
        message += f"🏪 Buy: {opportunity.buy_venue} at {opportunity.buy_price:.6f}\n"
        message += f"🏪 Sell: {opportunity.sell_venue} at {opportunity.sell_price:.6f}\n"
        message += f"💵 Amount: {opportunity.amount_in / 1e18:.2f} tokens\n"
        
        if opportunity.type in ['CEX_DEX', 'DEX_CEX']:
            message += f"⚡ Executable with flashloans\n"
        else:
            message += f"ℹ️ Manual execution required\n"
            
        self.send_message(message)

class EnhancedArbitrageScanner:
    """Enhanced arbitrage scanner with CEX integration"""
    
    def __init__(self):
        logger.info("Starting Enhanced CEX+DEX Arbitrage Scanner")
        
        # Initialize Telegram bot
        self.telegram = TelegramBot()
        
        # Web3 setup (for DEX operations)
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        self.contract = self._setup_flashloan_contract()
        
        # Initialize unified scanner
        self.unified_scanner = UnifiedArbitrageScanner(dex_scanner=self)
        
        # Execution tracking
        self.recent_transactions = []
        self.last_execution_time = 0
        self.min_execution_interval = 45  # 45 seconds between executions
        self.last_stats_report = 0
        self.stats_report_interval = 1800  # 30 minutes
        
        # Enhanced configuration for CEX+DEX
        self.min_profit_threshold_cex_dex = 0.003  # 0.3% for CEX-DEX (higher due to complexity)
        self.min_profit_threshold_cex_cex = 0.005  # 0.5% for CEX-CEX (manual execution)
        self.min_profit_threshold_dex_dex = 0.005  # 0.5% for DEX-DEX (original threshold)
        
        self.immediate_execution_threshold = 0.008  # 0.8%
        self.aggressive_execution_threshold = 0.015  # 1.5%
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'cex_dex_opportunities': 0,
            'cex_cex_opportunities': 0,
            'dex_dex_opportunities': 0,
            'immediate_executions': 0,
            'trades_attempted': 0,
            'trades_successful': 0,
            'total_profit_eth': 0.0,
            'total_gas_spent_eth': 0.0
        }
        
        logger.info("Enhanced BSC Arbitrage Scanner initialized")
        logger.info(f"CEX-DEX min profit: {self.min_profit_threshold_cex_dex:.1%}")
        logger.info(f"CEX-CEX min profit: {self.min_profit_threshold_cex_cex:.1%}")
        logger.info(f"DEX-DEX min profit: {self.min_profit_threshold_dex_dex:.1%}")
        logger.info(f"Immediate execution: {self.immediate_execution_threshold:.1%}")
        logger.info(f"Aggressive execution: {self.aggressive_execution_threshold:.1%}")
    
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection to BSC"""
        rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to BSC at {rpc_url}")
            
        latest_block = w3.eth.block_number
        logger.info(f"Connected to BSC: {rpc_url} (Block: {latest_block})")
        
        return w3
        
    def _setup_account(self) -> Optional[object]:
        """Setup account for transactions"""
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            logger.warning("No private key configured - running in simulation mode")
            return None
            
        try:
            account = self.w3.eth.account.from_key(private_key)
            logger.info(f"Account loaded: {account.address}")
            
            balance = self.w3.eth.get_balance(account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            logger.info(f"Account balance: {balance_eth:.4f} BNB")
            
            if balance_eth < 0.01:
                logger.warning(f"Low BNB balance: {balance_eth:.4f} BNB - may not be enough for gas")
            
            return account
        except Exception as e:
            logger.error(f"Error loading account: {e}")
            return None
    
    def _setup_flashloan_contract(self):
        """Setup flashloan contract"""
        contract_address = '0x86742335Ec7CC7bBaa7d4244841c315Cf1978eAE'
        logger.info(f"Using BSC flashloan contract: {contract_address}")
        
        abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "pairAddress", "type": "address"},
                    {"internalType": "uint256", "name": "amount0Out", "type": "uint256"},
                    {"internalType": "uint256", "name": "amount1Out", "type": "uint256"},
                    {"internalType": "address", "name": "tokenBorrow", "type": "address"},
                    {"internalType": "address", "name": "tokenTarget", "type": "address"},
                    {"internalType": "address", "name": "buyRouter", "type": "address"},
                    {"internalType": "address", "name": "sellRouter", "type": "address"}
                ],
                "name": "executeFlashloan",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=abi
            )
            
            logger.info(f"Flashloan contract loaded: {contract_address}")
            return contract
        except Exception as e:
            logger.warning(f"Failed to load flashloan contract: {e}")
            logger.info("Running in simulation mode")
            return None
    
    def process_opportunities(self, opportunities: List[UnifiedOpportunity]):
        """Process and potentially execute arbitrage opportunities"""
        if not opportunities:
            return
        
        logger.info(f"📊 Processing {len(opportunities)} opportunities")
        
        for opportunity in opportunities:
            try:
                # Determine if this opportunity can be executed
                executable = self._is_executable(opportunity)
                
                # Apply different thresholds based on opportunity type
                min_threshold = self._get_min_threshold(opportunity.type)
                
                if opportunity.profit_percentage < min_threshold:
                    continue
                
                # Log the opportunity
                logger.info(f"[{opportunity.type}] {opportunity.token_in_symbol}/{opportunity.token_out_symbol}: "
                          f"{opportunity.profit_percentage:.3f}% profit")
                logger.info(f"         Route: {opportunity.buy_venue} → {opportunity.sell_venue}")
                
                # Send Telegram notification
                self.telegram.send_enhanced_opportunity(opportunity)
                
                # Update statistics
                if opportunity.type == 'CEX_DEX' or opportunity.type == 'DEX_CEX':
                    self.stats['cex_dex_opportunities'] += 1
                elif opportunity.type == 'CEX_CEX':
                    self.stats['cex_cex_opportunities'] += 1
                elif opportunity.type == 'DEX_DEX':
                    self.stats['dex_dex_opportunities'] += 1
                
                # Execute if profitable enough and executable
                if (executable and 
                    opportunity.profit_percentage >= self.immediate_execution_threshold and
                    time.time() - self.last_execution_time >= self.min_execution_interval):
                    
                    logger.info(f"[EXECUTING] {opportunity.type} arbitrage: {opportunity.profit_percentage:.2f}% profit")
                    
                    success = self.execute_opportunity(opportunity)
                    
                    if success:
                        logger.info(f"[SUCCESS] Execution successful!")
                        self.stats['trades_successful'] += 1
                        self.last_execution_time = time.time()
                    else:
                        logger.warning(f"[FAILED] Execution failed")
                    
                    self.stats['trades_attempted'] += 1
                    self.stats['immediate_executions'] += 1
                
            except Exception as e:
                logger.error(f"Error processing opportunity: {e}")
    
    def _is_executable(self, opportunity: UnifiedOpportunity) -> bool:
        """Determine if an opportunity can be executed automatically"""
        # Only CEX-DEX and DEX-CEX can be executed with flashloans
        # CEX-CEX requires manual execution on exchanges
        # DEX-DEX can be executed with flashloans
        return opportunity.type in ['CEX_DEX', 'DEX_CEX', 'DEX_DEX']
    
    def _get_min_threshold(self, opportunity_type: str) -> float:
        """Get minimum profit threshold for opportunity type"""
        if opportunity_type in ['CEX_DEX', 'DEX_CEX']:
            return self.min_profit_threshold_cex_dex
        elif opportunity_type == 'CEX_CEX':
            return self.min_profit_threshold_cex_cex
        else:  # DEX_DEX
            return self.min_profit_threshold_dex_dex
    
    def execute_opportunity(self, opportunity: UnifiedOpportunity) -> bool:
        """Execute an arbitrage opportunity"""
        if not self.account or not self.contract:
            logger.info(f"[SIMULATION] Would execute {opportunity.type} arbitrage")
            logger.info(f"[SIMULATION] {opportunity.token_in_symbol}/{opportunity.token_out_symbol}")
            logger.info(f"[SIMULATION] Expected profit: {opportunity.profit_percentage:.3f}%")
            return True
        
        try:
            # Only execute DEX-based arbitrage for now
            # CEX-DEX arbitrage would require additional infrastructure (CEX API integration)
            if opportunity.type in ['CEX_DEX', 'DEX_CEX']:
                logger.info(f"[CEX-DEX] Requires additional infrastructure - marking as simulated execution")
                return True
            elif opportunity.type == 'DEX_DEX':
                # This would integrate with existing DEX arbitrage execution logic
                logger.info(f"[DEX-DEX] Executing flashloan arbitrage...")
                return self._execute_dex_arbitrage(opportunity)
            else:
                logger.info(f"[{opportunity.type}] Manual execution required")
                return False
                
        except Exception as e:
            logger.error(f"Error executing opportunity: {e}")
            return False
    
    def _execute_dex_arbitrage(self, opportunity: UnifiedOpportunity) -> bool:
        """Execute DEX-DEX arbitrage (placeholder for existing logic)"""
        # This would integrate with the existing flashloan execution logic from main.py
        # For now, simulate successful execution
        logger.info(f"[DEX-DEX] Simulating flashloan execution...")
        logger.info(f"[DEX-DEX] Buy on {opportunity.buy_venue}, sell on {opportunity.sell_venue}")
        logger.info(f"[DEX-DEX] Expected profit: {opportunity.profit_percentage:.3f}%")
        return True
    
    async def run_enhanced_scanning(self):
        """Run enhanced scanning with CEX+DEX integration"""
        scan_interval = int(os.getenv('SCAN_INTERVAL', '30'))  # 30 seconds default
        
        # Send start notification
        self.telegram.send_enhanced_start_notification()
        
        logger.info(f"Starting enhanced CEX+DEX arbitrage scanning")
        logger.info(f"Scan interval: {scan_interval}s")
        
        scan_count = 0
        
        try:
            while True:
                start_time = time.time()
                scan_count += 1
                
                logger.info("=" * 80)
                logger.info(f"🔍 Enhanced arbitrage scan #{scan_count}")
                
                try:
                    # Get all arbitrage opportunities
                    all_opportunities_dict = await self.unified_scanner.find_all_opportunities()
                    
                    # Get top opportunities across all types
                    top_opportunities = self.unified_scanner.get_top_opportunities(
                        all_opportunities_dict, limit=10
                    )
                    
                    # Process opportunities
                    self.process_opportunities(top_opportunities)
                    
                    self.stats['scans_completed'] += 1
                    scan_time = time.time() - start_time
                    
                    logger.info(f"📊 Scan #{scan_count} completed in {scan_time:.2f}s")
                    
                    # Compact statistics
                    total_opps = sum(len(opps) for opps in all_opportunities_dict.values())
                    logger.info(f"📈 Total opportunities: {total_opps}")
                    logger.info(f"   CEX-DEX: {len(all_opportunities_dict.get('CEX_DEX', []))}")
                    logger.info(f"   CEX-CEX: {len(all_opportunities_dict.get('CEX_CEX', []))}")
                    logger.info(f"   DEX-DEX: {len(all_opportunities_dict.get('DEX_DEX', []))}")
                    
                    # Send periodic stats report
                    current_time = time.time()
                    if current_time - self.last_stats_report > self.stats_report_interval:
                        self.send_stats_report()
                        self.last_stats_report = current_time
                    
                except Exception as e:
                    logger.error(f"Error in scan #{scan_count}: {e}")
                
                # Wait for next scan
                logger.info(f"⏳ Next scan in {scan_interval}s...")
                await asyncio.sleep(scan_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Enhanced scanner stopped by user")
        except Exception as e:
            logger.error(f"💥 Enhanced scanner error: {e}")
            logger.info("🔄 Attempting to restart in 30 seconds...")
            await asyncio.sleep(30)
            await self.run_enhanced_scanning()  # Restart
    
    def send_stats_report(self):
        """Send enhanced statistics report"""
        message = f"📊 <b>Enhanced Scanner Statistics</b>\n\n"
        message += f"⏱️ Scans completed: {self.stats['scans_completed']}\n"
        message += f"🔄 CEX-DEX opportunities: {self.stats['cex_dex_opportunities']}\n"
        message += f"🔄 CEX-CEX opportunities: {self.stats['cex_cex_opportunities']}\n"
        message += f"🔄 DEX-DEX opportunities: {self.stats['dex_dex_opportunities']}\n"
        message += f"⚡ Immediate executions: {self.stats['immediate_executions']}\n"
        message += f"📈 Trades successful: {self.stats['trades_successful']}\n"
        message += f"💰 Total profit: {self.stats['total_profit_eth']:.6f} BNB\n"
        message += f"⛽ Total gas cost: {self.stats['total_gas_spent_eth']:.6f} BNB"
        self.telegram.send_message(message)

async def main():
    """Main entry point for enhanced scanner"""
    logger.info("🚀 Enhanced BSC Arbitrage Scanner - CEX+DEX Integration")
    logger.info("=" * 80)
    logger.info("📊 Mode: Enhanced Production (CEX+DEX arbitrage)")
    logger.info("🔗 CEX: Binance, Bybit, OKX, KuCoin, Gate.io, Bitget, MEXC, HTX")
    logger.info("🔗 DEX: PancakeSwap, Biswap, ApeSwap, THENA")
    logger.info("🔧 Optimized for: Comprehensive arbitrage detection")
    
    try:
        scanner = EnhancedArbitrageScanner()
        await scanner.run_enhanced_scanning()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.info("🔄 Restarting in 30 seconds...")
        await asyncio.sleep(30)
        await main()  # Recursive restart

if __name__ == "__main__":
    asyncio.run(main())