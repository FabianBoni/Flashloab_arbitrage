import 'dotenv/config';
import { PriceMonitor } from './PriceMonitor';
import { ArbitrageExecutor } from './ArbitrageExecutor';
import { SUPPORTED_CHAINS, POPULAR_TOKENS, MIN_PROFIT_THRESHOLD, OPPORTUNITY_CHECK_INTERVAL } from './config';
import { ArbitrageOpportunity } from './types';

interface BotStats {
  opportunitiesFound: number;
  tradesExecuted: number;
  successfulTrades: number;
  totalProfit: number;
  uptime: number;
}

export class FlashloanArbitrageBot {
  private priceMonitor: PriceMonitor;
  private executor: ArbitrageExecutor;
  private stats: BotStats;
  private startTime: number;
  private isRunning: boolean = false;

  constructor() {
    this.startTime = Date.now();
    this.stats = {
      opportunitiesFound: 0,
      tradesExecuted: 0,
      successfulTrades: 0,
      totalProfit: 0,
      uptime: 0,
    };

    // Check for demo mode
    const demoMode = process.env.DEMO_MODE === 'true';
    if (demoMode) {
      console.log('🎭 Running in DEMO MODE with mock data');
    }

    // Initialize price monitor
    this.priceMonitor = new PriceMonitor(SUPPORTED_CHAINS, demoMode);

    // Initialize executor with contract addresses
    const contractAddresses = new Map<number, string>();
    contractAddresses.set(1, '0x5FbDB2315678afecb367f032d93F642f64180aa3'); // Mock address for testing
    contractAddresses.set(56, '0xDf9b5f44edae76901a6190496467002aEFCEf677'); // Universal Flashloan Contract on BSC
    // contractAddresses.set(137, 'YOUR_POLYGON_CONTRACT_ADDRESS');
    // contractAddresses.set(42161, 'YOUR_ARBITRUM_CONTRACT_ADDRESS');

    const privateKey = process.env.PRIVATE_KEY;
    if (!privateKey) {
      throw new Error('PRIVATE_KEY environment variable is required');
    }

    this.executor = new ArbitrageExecutor(SUPPORTED_CHAINS, privateKey, contractAddresses);
  }

  /**
   * Start the arbitrage bot
   */
  async start(): Promise<void> {
    console.log('🤖 Starting Flashloan Arbitrage Bot...');
    console.log('📊 Monitoring configuration:');
    console.log(`   - Minimum profit threshold: ${MIN_PROFIT_THRESHOLD * 100}%`);
    console.log(`   - Check interval: ${OPPORTUNITY_CHECK_INTERVAL}ms`);
    console.log(`   - Supported chains: ${SUPPORTED_CHAINS.length}`);

    this.isRunning = true;

    // Prepare token list for monitoring
    const tokensToMonitor = this.prepareTokenList();

    // Start price monitoring
    await this.priceMonitor.startPriceMonitoring(
      tokensToMonitor,
      this.handleOpportunities.bind(this),
      OPPORTUNITY_CHECK_INTERVAL
    );

    // Start stats reporting
    this.startStatsReporting();

    console.log('✅ Bot started successfully!');
  }

  /**
   * Stop the arbitrage bot
   */
  stop(): void {
    console.log('🛑 Stopping Flashloan Arbitrage Bot...');
    this.isRunning = false;
  }

  /**
   * Handle discovered arbitrage opportunities
   */
  private async handleOpportunities(opportunities: ArbitrageOpportunity[]): Promise<void> {
    this.stats.opportunitiesFound += opportunities.length;

    // Filter opportunities by profitability threshold
    const profitableOpportunities = opportunities.filter(
      op => op.profitPercent >= MIN_PROFIT_THRESHOLD * 100
    );

    if (profitableOpportunities.length === 0) {
      return;
    }

    console.log(`💡 Found ${profitableOpportunities.length} profitable opportunities`);

    // Sort by profitability (highest first)
    profitableOpportunities.sort((a, b) => b.profitPercent - a.profitPercent);

    // Execute the most profitable opportunities (limit to prevent spam)
    const toExecute = profitableOpportunities.slice(0, 3);

    for (const opportunity of toExecute) {
      await this.executeOpportunity(opportunity);
    }
  }

  /**
   * Execute a single arbitrage opportunity
   */
  private async executeOpportunity(opportunity: ArbitrageOpportunity): Promise<void> {
    try {
      console.log(`🎯 Executing opportunity: ${opportunity.profitPercent.toFixed(2)}% profit`);
      
      this.stats.tradesExecuted++;

      const result = await this.executor.executeArbitrage(opportunity);

      if (result.success) {
        this.stats.successfulTrades++;
        const profit = parseFloat(result.profit || '0');
        this.stats.totalProfit += profit;

        console.log(`✅ Trade successful! Profit: ${profit} ETH`);
        console.log(`📄 Transaction: ${result.txHash}`);
      } else {
        console.log(`❌ Trade failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Error executing opportunity:', error);
    }
  }

  /**
   * Prepare list of tokens to monitor
   */
  private prepareTokenList(): Array<{ chainId: number; address: string; symbol: string }> {
    const tokens: Array<{ chainId: number; address: string; symbol: string }> = [];

    SUPPORTED_CHAINS.forEach(chain => {
      const chainTokens = POPULAR_TOKENS[chain.chainId as keyof typeof POPULAR_TOKENS];
      if (chainTokens) {
        Object.entries(chainTokens).forEach(([symbol, address]) => {
          tokens.push({
            chainId: chain.chainId,
            address,
            symbol,
          });
        });
      }
    });

    return tokens;
  }

  /**
   * Start periodic stats reporting
   */
  private startStatsReporting(): void {
    setInterval(() => {
      if (!this.isRunning) return;

      this.stats.uptime = Date.now() - this.startTime;
      this.printStats();
    }, 60000); // Report every minute
  }

  /**
   * Print current bot statistics
   */
  private printStats(): void {
    const uptime = Math.floor(this.stats.uptime / 1000 / 60); // minutes
    const successRate = this.stats.tradesExecuted > 0 
      ? (this.stats.successfulTrades / this.stats.tradesExecuted * 100).toFixed(1)
      : '0';

    console.log('\n📊 Bot Statistics:');
    console.log(`   ⏱️  Uptime: ${uptime} minutes`);
    console.log(`   🔍 Opportunities found: ${this.stats.opportunitiesFound}`);
    console.log(`   📈 Trades executed: ${this.stats.tradesExecuted}`);
    console.log(`   ✅ Success rate: ${successRate}%`);
    console.log(`   💰 Total profit: ${this.stats.totalProfit.toFixed(4)} ETH`);
    console.log('');
  }

  /**
   * Get current bot statistics
   */
  getStats(): BotStats {
    return {
      ...this.stats,
      uptime: Date.now() - this.startTime,
    };
  }
}

// Main execution
async function main() {
  try {
    const bot = new FlashloanArbitrageBot();
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
      console.log('\n👋 Received SIGINT, shutting down gracefully...');
      bot.stop();
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      console.log('\n👋 Received SIGTERM, shutting down gracefully...');
      bot.stop();
      process.exit(0);
    });

    await bot.start();
  } catch (error) {
    console.error('💥 Failed to start bot:', error);
    process.exit(1);
  }
}

// Run the bot if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
}