# Flashloan Arbitrage System

A comprehensive cross-chain flashloan arbitrage system that automatically detects and executes profitable arbitrage opportunities across multiple DEXes and blockchain networks.

## 🚀 Features

- **Multi-Chain Support**: Ethereum, Polygon, Arbitrum, and BSC
- **Cross-Chain Arbitrage**: Execute arbitrage across different blockchain networks
- **Real-time Monitoring**: Continuous price monitoring across multiple DEXes
- **Automated Execution**: Smart contract-based flashloan arbitrage execution
- **Risk Management**: Built-in slippage protection and profit thresholds
- **Gas Optimization**: Efficient gas usage with dynamic fee estimation

## 🏗️ Architecture

### Smart Contracts
- `FlashloanArbitrage.sol`: Main contract for executing flashloan arbitrage trades
- Integrated with Aave V3 for flashloans
- Support for multiple DEXes (Uniswap, SushiSwap, etc.)

### Bot Components
- **PriceMonitor**: Real-time price monitoring and opportunity detection
- **ArbitrageExecutor**: Smart contract interaction and trade execution
- **CrossChainArbitrage**: Cross-chain opportunity detection and execution
- **FlashloanArbitrageBot**: Main orchestrator and bot controller

## 📋 Prerequisites

- Node.js 18+
- npm or yarn
- Ethereum wallet with private key
- RPC endpoints for supported networks
- API keys for block explorers (optional, for verification)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/FabianBoni/Flashloab_arbitrage.git
cd Flashloab_arbitrage
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Compile smart contracts:
```bash
npm run build
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Network RPC URLs
ETHEREUM_RPC_URL=https://eth-mainnet.alchemyapi.io/v2/your-api-key
POLYGON_RPC_URL=https://polygon-mainnet.alchemyapi.io/v2/your-api-key
ARBITRUM_RPC_URL=https://arb-mainnet.alchemyapi.io/v2/your-api-key
BSC_RPC_URL=https://bsc-dataseed.binance.org/

# Private key for deployment and transactions (without 0x prefix)
PRIVATE_KEY=your_private_key_here

# Trading Configuration
MIN_PROFIT_THRESHOLD=0.01    # Minimum profit percentage (1%)
MAX_GAS_PRICE=50            # Maximum gas price in Gwei
SLIPPAGE_TOLERANCE=0.005    # Maximum slippage (0.5%)

# Monitoring
PRICE_UPDATE_INTERVAL=5000      # Price update interval in ms
OPPORTUNITY_CHECK_INTERVAL=10000 # Opportunity check interval in ms
```

## 🚀 Deployment

### Deploy Smart Contracts

1. **Ethereum Mainnet**:
```bash
npx hardhat run scripts/deploy.ts --network ethereum
```

2. **Polygon**:
```bash
npx hardhat run scripts/deploy.ts --network polygon
```

3. **Arbitrum**:
```bash
npx hardhat run scripts/deploy.ts --network arbitrum
```

### Update Configuration

After deployment, update the contract addresses in your bot configuration:

```typescript
const contractAddresses = new Map<number, string>();
contractAddresses.set(1, 'YOUR_ETHEREUM_CONTRACT_ADDRESS');
contractAddresses.set(137, 'YOUR_POLYGON_CONTRACT_ADDRESS');
contractAddresses.set(42161, 'YOUR_ARBITRUM_CONTRACT_ADDRESS');
```

## 🤖 Running the Bot

### Development Mode
```bash
npm run dev
```

### Production Mode
```bash
npm run build
npm start
```

### Running Tests
```bash
npm test
```

## 📊 Monitoring

The bot provides real-time statistics including:

- **Opportunities Found**: Total arbitrage opportunities detected
- **Trades Executed**: Number of trades attempted
- **Success Rate**: Percentage of successful trades
- **Total Profit**: Cumulative profit in ETH
- **Uptime**: Bot operational time

Example output:
```
📊 Bot Statistics:
   ⏱️  Uptime: 120 minutes
   🔍 Opportunities found: 45
   📈 Trades executed: 12
   ✅ Success rate: 83.3%
   💰 Total profit: 0.0234 ETH
```

## 🔧 Advanced Configuration

### Adding New DEXes

To add support for a new DEX, update the contract:

```solidity
dexConfigs["newdex"] = DEXConfig({
    router: 0xNEW_DEX_ROUTER_ADDRESS,
    name: "New DEX",
    isActive: true
});
```

### Cross-Chain Configuration

Configure bridge settings in `CrossChainArbitrage.ts`:

```typescript
{
    name: 'Custom Bridge',
    sourceChain: 1,
    targetChain: 137,
    bridgeAddress: '0xBRIDGE_ADDRESS',
    fee: 0.1, // 0.1%
    estimatedTime: 15, // minutes
}
```

## 🛡️ Security Features

- **Reentrancy Protection**: All critical functions protected against reentrancy attacks
- **Access Control**: Owner-only functions for sensitive operations
- **Slippage Protection**: Configurable slippage tolerance
- **Profit Validation**: Pre-execution profitability verification
- **Emergency Withdrawal**: Emergency fund recovery mechanism

## 🔍 How It Works

1. **Price Monitoring**: The bot continuously monitors prices across multiple DEXes
2. **Opportunity Detection**: Identifies profitable arbitrage opportunities
3. **Profitability Check**: Validates opportunities account for gas costs and fees
4. **Flashloan Execution**: Borrows assets via Aave flashloan
5. **Arbitrage Trade**: Executes buy/sell trades across different DEXes
6. **Profit Realization**: Repays flashloan and keeps profit
7. **Cross-Chain**: Optionally executes arbitrage across different chains

## 📈 Supported DEXes

### Ethereum
- Uniswap V2
- SushiSwap
- 1inch (can be added)

### Polygon
- QuickSwap
- SushiSwap

### Arbitrum
- Uniswap V2
- SushiSwap

### BSC
- PancakeSwap (can be added)

## ⚠️ Risk Warnings

- **Market Risk**: Cryptocurrency prices are highly volatile
- **Smart Contract Risk**: Smart contracts may contain bugs
- **Slippage Risk**: High slippage can reduce or eliminate profits
- **Gas Cost Risk**: High gas prices can make arbitrage unprofitable
- **Liquidity Risk**: Low liquidity may prevent trade execution

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

- [Aave](https://aave.com/) for flashloan infrastructure
- [Uniswap](https://uniswap.org/) for DEX protocols
- [OpenZeppelin](https://openzeppelin.com/) for secure smart contract libraries
- [Hardhat](https://hardhat.org/) for development framework

## 📞 Support

For support and questions:
- Create an issue in this repository
- Join our community discussions
- Check the documentation for troubleshooting guides

---

**Disclaimer**: This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred while using this software.