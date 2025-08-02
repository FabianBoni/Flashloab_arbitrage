# Enhanced BSC Arbitrage Scanner - CEX + DEX Integration

🚀 **Production-ready arbitrage scanner with comprehensive CEX and DEX integration**

Monitor and execute profitable arbitrage trades across **8 major centralized exchanges** and **multiple DEXes** on Binance Smart Chain (BSC).

## 🆕 New Features: CEX Integration

### Supported Centralized Exchanges (CEX)
- **Binance** - World's largest crypto exchange
- **Bybit** - Leading derivatives exchange 
- **OKX** - Top-tier global exchange
- **KuCoin** - Popular altcoin exchange
- **Gate.io** - Comprehensive trading platform
- **Bitget** - Growing derivatives platform
- **MEXC** - High-volume spot exchange
- **HTX (Huobi)** - Established Asian exchange

### Supported Decentralized Exchanges (DEX)
- **PancakeSwap V2** - Leading BSC DEX
- **Biswap** - Low-fee BSC DEX
- **ApeSwap** - Community-driven DEX
- **THENA** - Next-gen DEX on BSC

## 🎯 Quick Start (Enhanced Version)

```bash
# 1. Clone and setup
git clone <your-repo-url> && cd Flashloab_arbitrage

# 2. Install Python dependencies (including CEX support)
pip install -r requirements.txt

# 3. Run enhanced scanner with CEX+DEX integration
python main_enhanced.py
```

## 🔄 Arbitrage Types Supported

### 1. CEX-DEX Arbitrage
- Buy on centralized exchange, sell on DEX
- Executable with flashloans (no initial capital required)
- Higher profit potential due to price inefficiencies

### 2. DEX-CEX Arbitrage  
- Buy on DEX, sell on centralized exchange
- Executable with flashloans
- Leverages DEX liquidity advantages

### 3. CEX-CEX Arbitrage
- Price differences between centralized exchanges
- Requires manual execution or API trading
- Lower execution complexity

### 4. DEX-DEX Arbitrage (Original)
- Traditional DEX arbitrage (maintained)
- PancakeSwap, Biswap, ApeSwap, etc.
- Fully automated with flashloans

## 🏗️ Enhanced Architecture

```
Flashloab_arbitrage/
├── main_enhanced.py              # Enhanced scanner with CEX+DEX
├── cex_price_provider.py         # CEX API integration
├── unified_arbitrage_scanner.py  # Unified CEX+DEX scanner
├── test_cex_integration.py       # CEX integration tests
├── main.py                       # Original DEX-only scanner
├── src/
│   ├── cex/                      # CEX-specific modules
│   │   └── CexPriceProvider.ts   # TypeScript CEX provider
│   ├── dex/                      # DEX-specific modules
│   ├── unified/                  # Unified scanning modules
│   │   └── UnifiedArbitrageScanner.ts
│   └── [existing TypeScript modules]
├── tests/                        # Test files
├── contracts/                    # Smart contracts
├── logs/                         # Enhanced logging
└── [existing files]
```

## 📊 Enhanced Configuration

### Environment Variables

```bash
# Existing DEX configuration
BSC_RPC_URL=https://bsc-dataseed1.binance.org/
PRIVATE_KEY=your_private_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Enhanced scanning intervals
SCAN_INTERVAL=30  # 30 seconds for CEX+DEX scanning
LOG_LEVEL=INFO

# CEX API Keys (optional, for advanced features)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
# ... other exchange API keys
```

### Profit Thresholds

- **CEX-DEX Arbitrage**: 0.3% minimum (higher due to complexity)
- **CEX-CEX Arbitrage**: 0.5% minimum (manual execution required)  
- **DEX-DEX Arbitrage**: 0.5% minimum (original threshold)
- **Immediate Execution**: 0.8% for automated execution
- **Aggressive Execution**: 1.5% for maximum trade sizes

## 🔍 How It Works

### Enhanced Arbitrage Process

1. **Multi-Source Scanning**: Simultaneously monitors CEX and DEX prices
2. **Opportunity Detection**: Identifies price differences across all sources
3. **Profit Calculation**: Accounts for all fees (CEX, DEX, gas, flashloan)
4. **Smart Execution**: Determines optimal execution method
5. **Automated Execution**: Uses flashloans for CEX-DEX arbitrage
6. **Comprehensive Reporting**: Enhanced Telegram notifications

### Supported Trading Pairs

#### Major Cryptocurrency Pairs
- **BTC/USDT, ETH/USDT, BNB/USDT** - Highest volume pairs
- **ADA/USDT, XRP/USDT, DOT/USDT** - Popular altcoins
- **LINK/USDT, UNI/USDT, MATIC/USDT** - DeFi tokens

#### Cross-Quote Pairs
- **BTC/USDC, ETH/USDC, BNB/USDC** - USDC markets
- **ETH/BTC, BNB/BTC, ADA/BTC** - Bitcoin pairs

#### Stablecoin Arbitrage
- **USDT/USDC, BUSD/USDT, BUSD/USDC** - Stablecoin spreads

## 🚀 Usage Examples

### Enhanced Scanner
```bash
# Run comprehensive CEX+DEX arbitrage scanner
python main_enhanced.py
```

### Original DEX-Only Scanner  
```bash
# Run traditional DEX arbitrage scanner
python main.py
```

### Test CEX Integration
```bash
# Test CEX APIs and integration
python test_cex_integration.py
```

### TypeScript Integration
```bash
# Build and run TypeScript components
npm run build
npm run start
```

## 📈 Enhanced Monitoring

### Telegram Notifications

- 🚀 **Enhanced Start**: CEX+DEX scanner initialization
- 💰 **Multi-Source Opportunities**: CEX-DEX, CEX-CEX, DEX-DEX alerts
- ✅ **Execution Results**: Success/failure with detailed metrics
- 📊 **Comprehensive Statistics**: Multi-source performance reports

### Enhanced Log Files

- `logs/enhanced_arbitrage.log`: Comprehensive CEX+DEX activity
- `logs/arbitrage.log`: Original DEX-only logs (maintained)
- Console output: Real-time multi-source scanning

## 🔧 Advanced Features

### Rate Limiting
- **CEX APIs**: Intelligent rate limiting per exchange
- **DEX RPCs**: Optimized blockchain queries
- **Concurrent Processing**: Parallel price fetching

### Error Handling
- **API Failures**: Graceful fallback between exchanges
- **Network Issues**: Automatic retry with exponential backoff
- **Execution Errors**: Comprehensive error reporting

### Performance Optimization
- **Caching**: Price data caching to reduce API calls
- **Concurrent Execution**: Async processing for speed
- **Memory Management**: Optimized for Raspberry Pi deployment

## 🛡️ Risk Management

### Enhanced Safety Features
- **Multi-Source Validation**: Cross-verify prices across sources
- **Fee Accounting**: Comprehensive fee calculation
- **Execution Throttling**: Prevent over-execution
- **Balance Monitoring**: CEX and DEX balance tracking
- **Slippage Protection**: Price impact calculations

### Fee Structure
- **CEX Trading Fees**: 0.1-0.2% per trade
- **CEX Withdrawal Fees**: Variable per token
- **DEX Swap Fees**: 0.05-0.3% per swap
- **Flashloan Fees**: 0.05-0.3%
- **Gas Costs**: Dynamic BSC gas prices

## 📋 Requirements

### System Requirements
- **Python**: 3.8+ with async support
- **Node.js**: 16+ for TypeScript components
- **Memory**: 2GB+ RAM (4GB recommended)
- **Network**: Stable internet for CEX APIs

### Dependencies
```bash
# Python dependencies
pip install web3 aiohttp requests python-dotenv ccxt

# Node.js dependencies  
npm install ethers axios ws express
```

## 🧪 Testing

### Test CEX Integration
```bash
python test_cex_integration.py
```

### Test Individual Components
```bash
# Test CEX price fetching
python -c "from cex_price_provider import CexPriceProvider; import asyncio; asyncio.run(test_function())"

# Test unified scanner
python -c "from unified_arbitrage_scanner import test_unified_scanner; import asyncio; asyncio.run(test_unified_scanner())"
```

## 📚 Documentation

### Key Files
- `README_ENHANCED.md`: This enhanced documentation
- `OPTIMIZATION_GUIDE.md`: Performance optimization tips
- `QUICK_COMMANDS.md`: Command reference
- `src/types.ts`: TypeScript type definitions

## 🔮 Future Enhancements

### Planned Features
- **Cross-Chain Arbitrage**: Ethereum, Polygon, Avalanche
- **Advanced CEX Features**: Order book depth analysis
- **ML Price Prediction**: Machine learning for opportunity prediction
- **Portfolio Management**: Multi-token balance optimization
- **Advanced Analytics**: Profit optimization algorithms

## ⚠️ Important Notes

### CEX-DEX Arbitrage Considerations
- **API Rate Limits**: Respect exchange rate limits
- **Withdrawal Times**: CEX withdrawals may take time
- **Market Volatility**: Prices change rapidly
- **Capital Requirements**: CEX arbitrage may require initial capital

### Execution Limitations
- **CEX-DEX**: Currently requires additional infrastructure for full automation
- **CEX-CEX**: Requires manual execution or exchange API integration
- **DEX-DEX**: Fully automated with flashloans (original functionality)

## 📞 Support

For issues with the enhanced CEX integration:
1. Check logs in `logs/enhanced_arbitrage.log`
2. Verify CEX API connectivity with `test_cex_integration.py`
3. Monitor console output for real-time status
4. Review Telegram notifications for opportunity alerts

## 📄 License

MIT License - see LICENSE.md

## ⚠️ Enhanced Disclaimer

**This enhanced software includes centralized exchange integration for educational and research purposes. CEX-DEX arbitrage involves additional complexity and risks. Always verify exchange terms of service, understand API rate limits, and test with small amounts first. The authors are not responsible for any losses incurred through the use of this software.**

---

💡 **Pro Tip**: Start with the original DEX-only scanner (`main.py`) to understand the basics, then move to the enhanced CEX+DEX scanner (`main_enhanced.py`) for comprehensive arbitrage opportunities.