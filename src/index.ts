import 'dotenv/config';
import { PriceMonitor } from './PriceMonitor';
import { ArbitrageExecutor } from './ArbitrageExecutor';
import { SUPPORTED_CHAINS, POPULAR_TOKENS, MIN_PROFIT_THRESHOLD, OPPORTUNITY_CHECK_INTERVAL, getTestModeChains } from './config';
import { ArbitrageOpportunity } from './types';
import { logger } from './logger';

interface BotStats {
  opportunitiesFound: number;
  tradesExecuted: number;
  successfulTrades: number;
  totalProfit: number;
  uptime: number;
}

export class FlashloanArbitrageBot {
  private static instance: FlashloanArbitrageBot | null = null;
  private priceMonitor: PriceMonitor;
  private executor: ArbitrageExecutor;
  private stats: BotStats;
  private startTime: number;
  private isRunning: boolean = false;
  private currentOpportunities: ArbitrageOpportunity[] = [];

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
    const testMode = process.env.TEST_MODE === 'true';
    
    if (demoMode) {
      console.log('🎭 Running in DEMO MODE with mock data');
    }
    
    if (testMode) {
      console.log('🧪 Running in TEST MODE with limited DEXs');
    }

    // Get appropriate chain configuration
    const chainConfig = testMode ? getTestModeChains() : SUPPORTED_CHAINS;

    // Initialize price monitor
    this.priceMonitor = new PriceMonitor(chainConfig, demoMode);

    // Initialize executor with contract addresses
    const contractAddresses = new Map<number, string>();
    contractAddresses.set(1, '0x5FbDB2315678afecb367f032d93F642f64180aa3'); // Mock address for testing
    contractAddresses.set(56, '0x0FA4cab40651cfcb308C169fd593E92F2f0cf805'); // REAL PancakeSwap Flashloan Contract on BSC
    // contractAddresses.set(137, 'YOUR_POLYGON_CONTRACT_ADDRESS');
    // contractAddresses.set(42161, 'YOUR_ARBITRUM_CONTRACT_ADDRESS');

    const privateKey = process.env.PRIVATE_KEY;
    if (!privateKey) {
      throw new Error('PRIVATE_KEY environment variable is required');
    }

    this.executor = new ArbitrageExecutor(SUPPORTED_CHAINS, privateKey, contractAddresses);
    
    // Set singleton instance
    FlashloanArbitrageBot.instance = this;
  }

  /**
   * Get the singleton instance of the bot
   */
  static getInstance(): FlashloanArbitrageBot | null {
    return FlashloanArbitrageBot.instance;
  }

  /**
   * Start the arbitrage bot
   */
  async start(): Promise<void> {
    logger.info('🤖 Starting Flashloan Arbitrage Bot...');
    logger.info('📊 Monitoring configuration:');
    logger.info(`   - Minimum profit threshold: ${MIN_PROFIT_THRESHOLD * 100}%`);
    logger.info(`   - Check interval: ${OPPORTUNITY_CHECK_INTERVAL}ms`);
    logger.info(`   - Supported chains: ${SUPPORTED_CHAINS.length}`);

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

    logger.success('✅ Bot started successfully!');
  }

  /**
   * Stop the arbitrage bot
   */
  stop(): void {
    logger.info('🛑 Stopping Flashloan Arbitrage Bot...');
    this.isRunning = false;
  }

  /**
   * Handle discovered arbitrage opportunities
   */
  private async handleOpportunities(opportunities: ArbitrageOpportunity[]): Promise<void> {
    // Store current opportunities for dashboard
    this.currentOpportunities = opportunities;
    
    // Count ALL opportunities found
    this.stats.opportunitiesFound += opportunities.length;

    // Filter opportunities by profitability threshold
    const profitableOpportunities = opportunities.filter(
      op => op.profitPercent >= MIN_PROFIT_THRESHOLD * 100
    );

    // Log opportunity discovery (throttled)
    if (profitableOpportunities.length > 0) {
      logger.opportunity(`Found ${profitableOpportunities.length} profitable opportunities (${opportunities.length} total)`);
    }

    if (profitableOpportunities.length === 0) {
      return; // Skip logging if no opportunities
    }

    // PRE-VALIDATE with smart contract before execution
    const validatedOpportunities: ArbitrageOpportunity[] = [];
    
    for (const opportunity of profitableOpportunities) {
      const isValid = await this.executor.preValidateOpportunity(opportunity);
      if (isValid) {
        validatedOpportunities.push(opportunity);
        logger.success(`Opportunity validated: ${opportunity.profitPercent.toFixed(2)}% profit`);
      } else {
        logger.warning(`Contract pre-validation FAILED for ${opportunity.profitPercent.toFixed(2)}% opportunity`);
        logger.warning(`   Route: ${opportunity.dexA} -> ${opportunity.dexB}`);
        logger.warning(`   Reason: Contract says not profitable (likely due to changed market conditions)`);
      }
    }

    if (validatedOpportunities.length === 0) {
      logger.warning('No opportunities passed contract validation (market conditions changed)');
      return;
    }

    logger.success(`${validatedOpportunities.length} opportunities passed contract validation`);

    // Sort by profitability (highest first)
    validatedOpportunities.sort((a, b) => b.profitPercent - a.profitPercent);

    // Execute the most profitable opportunities (limit to prevent spam)
    const toExecute = validatedOpportunities.slice(0, 3);

    for (const opportunity of toExecute) {
      await this.executeOpportunity(opportunity);
    }
  }

  /**
   * Execute a single arbitrage opportunity
   */
  private async executeOpportunity(opportunity: ArbitrageOpportunity): Promise<void> {
    try {
      logger.trade(`Executing opportunity: ${opportunity.profitPercent.toFixed(2)}% profit`);
      logger.trade(`Route: ${opportunity.dexA} -> ${opportunity.dexB}`);
      logger.trade(`Token: ${opportunity.tokenA} -> ${opportunity.tokenB}`);
      logger.trade(`Amount: ${opportunity.amountIn}`);
      
      this.stats.tradesExecuted++;

      const result = await this.executor.executeArbitrage(opportunity);

      if (result.success) {
        this.stats.successfulTrades++;
        const profit = parseFloat(result.profit || '0');
        this.stats.totalProfit += profit;

        logger.success(`Trade successful! Profit: ${profit} ETH`);
        logger.success(`Transaction: ${result.txHash}`);
      } else {
        logger.error(`Trade failed: ${result.error}`);
      }
    } catch (error) {
      logger.error('Error executing opportunity:', error);
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

    const statsMessage = `
📊 Bot Statistics:
   ⏱️  Uptime: ${uptime} minutes
   🔍 Opportunities found: ${this.stats.opportunitiesFound}
   📈 Trades executed: ${this.stats.tradesExecuted}
   ✅ Success rate: ${successRate}%
   💰 Total profit: ${this.stats.totalProfit.toFixed(4)} ETH`;

    logger.stats(statsMessage);
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

  /**
   * Get current opportunities
   */
  getCurrentOpportunities(): ArbitrageOpportunity[] {
    return [...this.currentOpportunities];
  }

  /**
   * Check if bot is running
   */
  getIsRunning(): boolean {
    return this.isRunning;
  }
}

// Main execution
async function main() {
  try {
    const bot = new FlashloanArbitrageBot();
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
      logger.info('\n👋 Received SIGINT, shutting down gracefully...');
      bot.stop();
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      logger.info('\n👋 Received SIGTERM, shutting down gracefully...');
      bot.stop();
      process.exit(0);
    });

    await bot.start();
  } catch (error) {
    logger.error('💥 Failed to start bot:', error);
    process.exit(1);
  }
}

// Run the bot if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
}