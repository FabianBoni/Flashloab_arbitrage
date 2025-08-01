# Raspberry Pi Docker Deployment Guide

## Quick Start (No Configuration Required)

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd Flashloab_arbitrage

# Copy environment file
cp .env.example .env

# Start the scanner (monitoring mode - no trading)
docker-compose up -d
```

### 2. View Logs
```bash
# Follow real-time logs
docker-compose logs -f

# View recent logs
docker-compose logs --tail=100
```

### 3. Control the Scanner
```bash
# Stop the scanner
docker-compose down

# Restart the scanner
docker-compose restart

# Update and restart
git pull
docker-compose up -d --build
```

## Configuration Options

### Basic Configuration (Edit .env file)
```bash
# Edit configuration
nano .env

# Required settings
BSC_RPC_URL=https://bsc-dataseed1.binance.org/
SCAN_INTERVAL=10
MIN_PROFIT_THRESHOLD=0.008
```

### Enable Telegram Notifications
1. Create a bot with @BotFather on Telegram
2. Get your chat ID from @userinfobot
3. Add to .env:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Enable Real Trading (ADVANCED)
⚠️ **WARNING: Only for experienced users**
```bash
# Add your BSC wallet private key (without 0x)
PRIVATE_KEY=your_private_key_here
```

## Raspberry Pi Optimization

### Performance Settings
- Memory limit: 512MB
- CPU limit: 1 core
- Automatic restart on failure
- Log rotation (max 10MB, 3 files)

### Resource Monitoring
```bash
# Check memory usage
docker stats bsc-arbitrage-scanner

# Check system resources
htop
```

### Troubleshooting
```bash
# Check container status
docker ps

# View detailed logs
docker logs bsc-arbitrage-scanner

# Restart if needed
docker-compose restart

# Clean up (if needed)
docker system prune -f
```

## Default Behavior

### Monitoring Mode (Default)
- Scans for arbitrage opportunities every 10 seconds
- Logs all findings to console and files
- No trading execution (safe mode)
- Telegram notifications (if configured)

### Production Thresholds
- Minimum profit: 0.8% after all fees
- Immediate execution: 1.2% profit
- Aggressive execution: 2.5% profit

### Supported Trading Pairs
- 44 high-liquidity pairs on BSC
- WBNB, BUSD, USDT, USDC, BTCB, CAKE
- Major altcoins: ADA, DOT, LINK, UNI, MATIC, etc.

## Security Features

- Non-root container user
- Read-only environment file mounting
- Resource limits to prevent system overload
- Health checks and automatic restart
- Private key never logged or exposed

## File Structure
```
/home/arbitrage/app/
├── main.py              # Main scanner application
├── logs/                # Log files (persisted)
├── .env                 # Your configuration
└── Dockerfile           # Container definition
```
