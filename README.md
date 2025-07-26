# 🚀 Flashloan Arbitrage Bot

A comprehensive flashloan arbitrage system that automatically detects and executes profitable arbitrage opportunities across multiple DEXes and blockchain networks, with full **MetaMask integration**.

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

### 📊 Real-time Dashboard
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

# Trading Parameters
MIN_PROFIT_THRESHOLD=0.01          # Minimum 1% profit
MAX_GAS_PRICE=50                   # Max 50 gwei gas price
SLIPPAGE_TOLERANCE=0.005           # 0.5% slippage tolerance

# Monitoring Settings
PRICE_UPDATE_INTERVAL=5000         # Price check every 5 seconds
OPPORTUNITY_CHECK_INTERVAL=10000   # Opportunity scan every 10 seconds

# Web Server
WEB_PORT=3000                      # Web interface port
```

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
npm run build              # Compile TypeScript
npm run build:contracts    # Compile Solidity contracts
npm run test              # Run smart contract tests
npm run deploy            # Deploy contracts to networks
npm start                 # Start CLI bot
npm run start:web         # Start web interface
npm run dev               # Development mode (CLI)
npm run dev:web           # Development mode (web)
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