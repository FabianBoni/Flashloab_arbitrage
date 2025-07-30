# 🚀 Flashloan Arbitrage Bot

A comprehensive flashloan arbitrage system that automatically detects and executes profitable arbitrage opportunities across multiple DEXes and blockchain networks, with full **MetaMask integration**.

> ✅ **Updated to Etherscan V2 API** - Now supports 50+ chains with a single API key!

## ✨ Key Features

### 🦊 MetaMask Integration
- **Browser-based interface** with MetaMask wallet connection
- **Multi-chain support** - Ethereum, Polygon, Arbitrum, BSC
- **Real-time wallet monitoring** - Balance, network, and connection status
- **Transaction signing** through MetaMask for secure execution
- **Network switching** and chain validation

### 🤖 Automated Trading
- **Multi-DEX price monitoring** across Uniswap, SushiSwap, QuickSwap
- **Cross-chain arbitrage detection** with bridge integration
- **Flashloan-based execution** via Aave V3 for capital efficiency
- **Risk management** with configurable profit thresholds and slippage protection

### 📱 Telegram Integration
- **Real-time notifications** for trade executions and opportunities
- **Bot commands** for status monitoring and control (/status, /stats, /stop)
- **Automated alerts** for errors and critical events
- **Periodic statistics reports** delivered directly to your Telegram
- **Graceful degradation** - works without Telegram configuration

### � Etherscan V2 Integration
- **Single API key** for all supported blockchain networks
- **Contract verification** across 50+ chains with one configuration
- **Real-time transaction monitoring** and balance queries
- **Future-proof** architecture that automatically supports new chains

### �📊 Real-time Dashboard
- **Live statistics** - opportunities found, trades executed, success rate, total profit
- **Activity monitoring** with detailed logging
- **Bot controls** - start/stop with wallet verification
- **Network status** indicators and chain information

## 🎯 Usage Modes

### 1. Web Interface (MetaMask Required)
Perfect for interactive monitoring and manual oversight:

```bash
# Start the web interface
npm run build
npm run start:web

# Open http://localhost:3000 in your browser
# Connect MetaMask and start trading
```

### 2. CLI Mode (Private Key)
Ideal for automated headless trading:

```bash
# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the CLI bot
npm run build
npm start
```

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **MetaMask** browser extension (for web interface)
- **RPC endpoints** for supported chains
- **Private key** (for CLI mode) or MetaMask (for web interface)

### Installation

```bash
# Clone the repository
git clone https://github.com/FabianBoni/Flashloab_arbitrage.git
cd Flashloab_arbitrage

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with your configuration
# Note: Only ETHERSCAN_API_KEY needed for all chains with V2!

# Compile smart contracts
npm run build:contracts

# Test your Etherscan V2 configuration
npm run test:etherscan

# Build the project
npm run build
```

### Web Interface Setup

1. **Start the web server:**
   ```bash
   npm run start:web
   ```

2. **Open your browser to:** `http://localhost:3000`

3. **Connect MetaMask:**
   - Ensure MetaMask is installed and unlocked
   - Click "Connect MetaMask" 
   - Approve the connection request
   - Switch to a supported network if needed

4. **Start trading:**
   - Click "Start Bot" once connected
   - Monitor real-time statistics and activity
   - Stop/start as needed

### CLI Setup

1. **Configure your environment:**
   ```bash
   # Edit .env file
   PRIVATE_KEY=your_private_key_here
   ETHEREUM_RPC_URL=https://eth-mainnet.alchemyapi.io/v2/your-api-key
   POLYGON_RPC_URL=https://polygon-mainnet.alchemyapi.io/v2/your-api-key
   # ... other settings
   ```

2. **Deploy contracts (if needed):**
   ```bash
   npm run deploy
   ```

3. **Start the bot:**
   ```bash
   npm start
   ```

### 📱 Telegram Setup (Optional)

To enable Telegram notifications:

1. **Create a Telegram Bot:**
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Use `/newbot` command and follow instructions
   - Save the bot token you receive

2. **Get your Chat ID:**
   - Start a chat with your bot
   - Send any message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

3. **Configure Environment:**
   ```bash
   # Add to your .env file
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

4. **Test the Integration:**
   ```bash
   # Test Telegram bot functionality
   node test-telegram.js
   ```

## 🌐 Supported Networks

| Network | Chain ID | DEXes | Flashloan Provider |
|---------|----------|-------|-------------------|
| **Ethereum** | 1 | Uniswap V2, SushiSwap | Aave V3 |
| **Polygon** | 137 | QuickSwap, SushiSwap | Aave V3 |
| **Arbitrum** | 42161 | Uniswap V2, SushiSwap | Aave V3 |
| **BSC** | 56 | PancakeSwap, SushiSwap | Aave V3 |

## 🔧 Configuration

### Environment Variables

```bash
# Network RPC URLs
ETHEREUM_RPC_URL=https://eth-mainnet.alchemyapi.io/v2/your-api-key
POLYGON_RPC_URL=https://polygon-mainnet.alchemyapi.io/v2/your-api-key
ARBITRUM_RPC_URL=https://arb-mainnet.alchemyapi.io/v2/your-api-key
BSC_RPC_URL=https://bsc-dataseed.binance.org/

# Wallet Configuration
PRIVATE_KEY=your_private_key_here  # For CLI mode only

# 🆕 Etherscan V2 API Configuration (Single API Key for All Chains!)
ETHERSCAN_API_KEY=your_etherscan_api_key  # Works for Ethereum, Polygon, Arbitrum, BSC, and 50+ other chains!

# Legacy API keys (no longer needed with V2)
# POLYGONSCAN_API_KEY=your_polygonscan_api_key
# ARBISCAN_API_KEY=your_arbiscan_api_key  
# BSCSCAN_API_KEY=your_bscscan_api_key

# Trading Parameters
MIN_PROFIT_THRESHOLD=0.01          # Minimum 1% profit
MAX_GAS_PRICE=50                   # Max 50 gwei gas price
SLIPPAGE_TOLERANCE=0.005           # 0.5% slippage tolerance

# Monitoring Settings
PRICE_UPDATE_INTERVAL=5000         # Price check every 5 seconds
OPPORTUNITY_CHECK_INTERVAL=10000   # Opportunity scan every 10 seconds

# Web Server
WEB_PORT=3000                      # Web interface port

# 📱 Telegram Bot Configuration (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here    # Get from @BotFather
TELEGRAM_CHAT_ID=your_telegram_chat_id_here        # Your chat/group ID for notifications
```

### 🆕 Etherscan V2 Benefits

With the new Etherscan V2 API, you now enjoy:

✅ **Single API Key**: One key works across 50+ supported chains  
✅ **Unified Endpoint**: `https://api.etherscan.io/v2/api` for all chains  
✅ **Simplified Configuration**: No more managing multiple API keys  
✅ **Future-Proof**: Automatically supports new chains as they're added  
✅ **Better Rate Limits**: Improved performance and reliability  

**Supported Chains Include:**
- Ethereum (1)
- Polygon (137) 
- Arbitrum (42161)
- BSC (56)
- Optimism (10)
- Base (8453)
- Scroll (534352)
- Blast (81457)
- And many more!

#### 🧪 Test Your Configuration

Test the new Etherscan V2 setup:

```bash
# Simple test script
npm run test:etherscan

# Advanced demo with examples
npm run etherscan:demo
```

Both scripts will verify your API key works across multiple chains and show real-time balance queries.

### Risk Management

The system includes multiple safety mechanisms:

- **Profit validation** before execution
- **Gas price limits** to prevent high-cost transactions
- **Slippage protection** for all trades
- **Network validation** to ensure supported chains
- **User confirmation** required for MetaMask transactions

## 🏗️ Architecture

### Smart Contract Layer
```
contracts/FlashloanArbitrage.sol    # Core arbitrage logic with Aave V3 integration
```

### Backend Services
```
src/
├── index.ts                        # Main CLI bot orchestrator
├── web-server.ts                   # Express server for web interface
├── ArbitrageExecutor.ts            # Private key-based execution
├── MetaMaskArbitrageExecutor.ts    # MetaMask-based execution
├── PriceMonitor.ts                 # Multi-DEX price monitoring
├── CrossChainArbitrage.ts          # Cross-chain opportunity detection
├── config.ts                       # Chain and DEX configurations
└── types.ts                        # TypeScript interfaces
```

### Frontend
```
public/
├── index.html                      # Web interface
└── app.js                          # MetaMask integration and UI logic
```

## 📊 Web Interface Features

### 🔗 Wallet Connection
- **MetaMask detection** and connection status
- **Account information** with formatted address display
- **Network validation** and chain switching
- **Balance monitoring** with real-time updates

### 🤖 Bot Controls
- **Start/Stop functionality** with wallet verification
- **Real-time status** indicators
- **Connection requirements** enforcement

### 📈 Live Statistics
- **Opportunities found** - Total arbitrage opportunities detected
- **Trades executed** - Number of executed transactions
- **Success rate** - Percentage of successful trades
- **Total profit** - Cumulative profit in ETH

### 📝 Activity Log
- **Real-time logging** of bot activities
- **Color-coded messages** (success, warning, error)
- **Timestamped entries** with automatic scrolling
- **Activity filtering** and history management

### 📱 Telegram Features
- **Real-time notifications** for all bot activities
- **Trade alerts** with profit/loss details and transaction hashes
- **Periodic statistics reports** (every 30 minutes)
- **Error notifications** for critical issues
- **Remote bot control** via commands:
  - `/start` - Welcome message and command overview
  - `/status` - Current bot status and basic statistics  
  - `/stats` - Detailed performance statistics
  - `/stop` - Stop the bot remotely
  - `/help` - Show available commands and features

## 🛡️ Security

### MetaMask Integration
- **No private key storage** in browser environment
- **User approval required** for all transactions
- **Secure signing** through MetaMask extension
- **Network validation** before execution

### Smart Contract Security
- **ReentrancyGuard** protection against reentrancy attacks
- **Access control** with owner-only functions
- **Slippage protection** in all DEX interactions
- **Emergency withdrawal** functions for fund recovery

## 🚀 Development

### Available Scripts

```bash
# Build & Test
npm run build              # Compile TypeScript
npm run build:contracts    # Compile Solidity contracts
npm run test              # Run smart contract tests

# 🆕 Etherscan V2 Testing
npm run test:etherscan     # Quick API test across multiple chains
npm run etherscan:demo     # Comprehensive V2 demo with examples

# 📱 Telegram Integration Testing
npm run test:telegram      # Test Telegram bot configuration
npm run demo:telegram      # Demonstrate Telegram features

# Deployment & Production
npm run deploy            # Deploy contracts to networks
npm start                 # Start CLI bot
npm run start:web         # Start web interface

# Development
npm run dev               # Development mode (CLI)
npm run dev:web           # Development mode (web)
npm run example           # Run usage examples

# Code Quality
npm run lint              # ESLint code checking
npm run format            # Prettier code formatting
```

### Testing

```bash
# Run smart contract tests
npm test

# Test MetaMask integration
npm run start:web
# Open http://localhost:3000 and test with MetaMask
```

## 📝 Example Usage

### Web Interface Workflow

1. **Connect MetaMask:**
   ```
   🦊 Browser opens → Connect MetaMask → Approve connection
   ```

2. **Verify Network:**
   ```
   🌐 Check network → Switch if needed → Validate balance
   ```

3. **Start Trading:**
   ```
   🚀 Click "Start Bot" → MetaMask confirms → Bot begins monitoring
   ```

4. **Monitor Activity:**
   ```
   📊 Watch statistics → Review logs → Monitor profits
   ```

### CLI Workflow

```bash
# Set up environment
export PRIVATE_KEY="your_private_key"
export ETHEREUM_RPC_URL="your_rpc_url"

# Start bot
npm start

# Monitor output
🤖 Starting Flashloan Arbitrage Bot...
📊 Monitoring configuration:
   - Minimum profit threshold: 1%
   - Check interval: 10000ms
   - Supported chains: 4
✅ Bot started successfully!
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes. Trading cryptocurrencies involves significant risk. Users are responsible for their own trading decisions and should thoroughly test the system before using real funds.

## 🔗 Links

- **Repository:** [https://github.com/FabianBoni/Flashloab_arbitrage](https://github.com/FabianBoni/Flashloab_arbitrage)
- **Issues:** [https://github.com/FabianBoni/Flashloab_arbitrage/issues](https://github.com/FabianBoni/Flashloab_arbitrage/issues)
- **MetaMask:** [https://metamask.io/](https://metamask.io/)
- **Aave V3:** [https://aave.com/](https://aave.com/)
- **Etherscan V2:** [https://docs.etherscan.io/etherscan-v2](https://docs.etherscan.io/etherscan-v2)

---

## 📋 Changelog

### v1.1.0 - Etherscan V2 Update (July 29, 2025)

#### ✅ **New Features**
- **Etherscan V2 API Integration** - Single API key for all supported chains
- **EtherscanV2Helper Class** - Comprehensive API wrapper for V2 functionality
- **Multi-chain Contract Verification** - Unified verification across 50+ chains
- **Enhanced Testing Scripts** - `npm run test:etherscan` and `npm run etherscan:demo`

#### 🔧 **Configuration Improvements**
- **Simplified .env setup** - Removed need for separate POLYGONSCAN_API_KEY, ARBISCAN_API_KEY, BSCSCAN_API_KEY
- **Updated hardhat.config.ts** - V2 API endpoints and unified key configuration
- **Enhanced TypeScript support** - Fixed all compilation errors and improved type definitions

#### 🐛 **Bug Fixes & Build Improvements**
- **Fixed Smart Contract compilation** - Resolved interface placement and address checksum issues
- **Updated Solidity optimizer** - Added viaIR compilation to handle complex contract structures
- **Fixed BigInt arithmetic** - Corrected TypeScript errors in test files
- **Updated deprecated functions** - Replaced `safeApprove` with `forceApprove` for OpenZeppelin compatibility

#### 📖 **Documentation Updates**
- **Complete README overhaul** - Added V2 benefits, configuration guides, and testing instructions
- **Migration documentation** - Clear guidance for upgrading from V1 to V2
- **New utility scripts** - Comprehensive examples and demos

#### ⚡ **Performance & Reliability**
- **Better rate limits** - Improved API call efficiency with V2
- **Future-proof architecture** - Automatic support for new chains as they're added
- **Unified error handling** - Consistent API responses across all chains

**Migration Required:** Update your `.env` file to use only `ETHERSCAN_API_KEY` for all chains.