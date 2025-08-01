# BSC Arbitrage Scanner - Raspberry Pi Docker Edition

🚀 **Production-ready arbitrage scanner optimized for Raspberry Pi deployment**

Monitor and execute profitable arbitrage trades on Binance Smart Chain (BSC) with zero configuration required.

## 🎯 Quick Start (3 Commands)

```bash
# 1. Clone and setup
git clone <your-repo-url> && cd Flashloab_arbitrage

# 2. One-command setup (installs everything)
chmod +x setup-pi.sh && ./setup-pi.sh

# 3. View live results
./manage.sh logs
```

**That's it!** Your arbitrage scanner is now running and monitoring BSC for profitable opportunities.

```bash
python main.py
```

## Configuration

### Trading Parameters

- `MIN_PROFIT_THRESHOLD`: Minimum profit percentage (default: 0.5%)
- `SCAN_INTERVAL`: Seconds between scans (default: 10s)
- Immediate execution threshold: 2% (hardcoded for safety)

### Telegram Setup

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get your bot token
3. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
4. Add both to your `.env` file

## How It Works

### Arbitrage Process

1. **Scanning**: Monitors DEX prices every 10 seconds
2. **Detection**: Identifies price differences between DEXes
3. **Validation**: Calculates real profit after fees and gas
4. **Execution**: Uses flashloan for zero-capital arbitrage
5. **Notification**: Sends results via Telegram

### Supported Trading Pairs

- **Stablecoins**: BUSD/USDT, BUSD/USDC, USDT/USDC
- **Major Pairs**: WBNB/BUSD, WBNB/ETH, ETH/BUSD, BTCB/BUSD
- **DeFi Pairs**: CAKE/BUSD, CAKE/WBNB

### Smart Contract

The bot uses a custom flashloan contract deployed on BSC that:
- Borrows tokens via PancakeSwap flashswap
- Executes arbitrage trades across multiple DEXes
- Automatically repays the loan + 0.3% fee
- Returns profit to your wallet

## Risk Management

- **Slippage Protection**: Built-in price impact calculations
- **Gas Optimization**: Dynamic gas price adjustment
- **Rate Limiting**: Prevents API rate limit issues
- **Error Handling**: Comprehensive error catching and reporting
- **Execution Throttling**: Minimum 30s between trades

## Monitoring

### Telegram Notifications

- 🚀 **Bot Start**: Confirmation when scanner starts
- 💰 **Opportunities**: Real-time alerts for profitable trades
- ✅ **Execution Results**: Success/failure notifications with details
- 📊 **Statistics**: Periodic reports every 30 minutes

### Log Files

- `immediate_arbitrage.log`: Detailed execution logs
- Console output: Real-time scanning information

## Project Structure

```
Flashloab_arbitrage/
├── main.py                 # Main arbitrage scanner
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
├── hardhat.config.ts      # Hardhat configuration
├── package.json           # Node.js dependencies
├── contracts/             # Smart contracts
│   └── FlashloanArbitrage.sol
├── scripts/               # Deployment scripts
│   └── deploy.ts
├── test/                  # Contract tests
└── archive/               # Old files (reference only)
```

## Statistics Tracking

The bot tracks comprehensive statistics:
- Total scans completed
- Opportunities found
- Successful executions  
- Total profit earned
- Gas costs incurred
- Success rate percentage

## Safety Features

- **Simulation Mode**: Test without real funds (remove PRIVATE_KEY)
- **Minimum Thresholds**: Only executes profitable trades
- **Gas Limits**: Prevents excessive gas consumption
- **Timeout Protection**: Prevents hanging transactions
- **Balance Monitoring**: Warns on low BNB balance

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check BSC RPC URL
2. **Transaction Failures**: Verify contract address and gas settings
3. **Low Profits**: Market conditions or high gas fees
4. **Telegram Issues**: Verify bot token and chat ID

### Support

- Check logs in `immediate_arbitrage.log`
- Monitor console output for real-time status
- Telegram notifications provide immediate feedback

## License

MIT License - see LICENSE.md

## Disclaimer

**This software is for educational purposes. Trading cryptocurrencies involves substantial risk. Always test with small amounts first and understand the risks involved.**

---

💡 **Pro Tip**: Start in simulation mode (without PRIVATE_KEY) to understand the bot's behavior before using real funds.