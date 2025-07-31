import 'dotenv/config';
import { PriceMonitor } from './PriceMonitor';
import { ArbitrageExecutor } from './ArbitrageExecutor';
import { TelegramBotService } from './TelegramBot';
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
  private telegramBot: TelegramBotService;
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

    // Initialize Telegram bot service
    this.telegramBot = new TelegramBotService();

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
    
    // Use contract address from .env file
    const deployedContractAddress = process.env.FLASHLOAN_CONTRACT_ADDRESS;
    if (!deployedContractAddress) {
      throw new Error('FLASHLOAN_CONTRACT_ADDRESS environment variable is required');
    }
    contractAddresses.set(56, deployedContractAddress); // Use .env contract address for BSC
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
   * Start optimized monitoring for major tokens only
   */
  private async startOptimizedMonitoring(): Promise<void> {
    logger.info('🔍 Starting OPTIMIZED monitoring for major, liquid tokens...');
    
    const monitor = async () => {
      if (!this.isRunning) return;
      
      try {
        await this.priceMonitor.monitorLiquidTokens(this.handleOpportunities.bind(this));
      } catch (error) {
        logger.error('Error in optimized monitoring:', error);
      }
    };

    // Run initial scan
    await monitor();

    // Set up interval monitoring
    setInterval(monitor, OPPORTUNITY_CHECK_INTERVAL);
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
    logger.info(`   - Telegram notifications: ${this.telegramBot.isActive() ? 'Enabled' : 'Disabled'}`);

    this.isRunning = true;

    // Send Telegram notification
    await this.telegramBot.notifyBotStarted();

    // Prepare token list for monitoring
    const tokensToMonitor = this.prepareTokenList();

    // Start optimized price monitoring for major tokens only
    this.startOptimizedMonitoring();

    // Start stats reporting
    this.startStatsReporting();

    logger.success('✅ Bot started successfully!');
  }

  /**
   * Stop the arbitrage bot
   */
  async stop(): Promise<void> {
    logger.info('🛑 Stopping Flashloan Arbitrage Bot...');
    this.isRunning = false;
    
    // Send Telegram notification
    await this.telegramBot.notifyBotStopped();
    
    // Shutdown Telegram bot
    await this.telegramBot.shutdown();
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

    // Send Telegram notification for significant opportunities
    if (opportunities.length > 0) {
      await this.telegramBot.notifyOpportunityFound(opportunities);
    }

    // Log opportunity discovery (throttled)
    if (profitableOpportunities.length > 0) {
      logger.opportunity(`Found ${profitableOpportunities.length} profitable opportunities (${opportunities.length} total)`);
    }

    if (profitableOpportunities.length === 0) {
      return; // Skip if no opportunities
    }

    // AGGRESSIVE MODE: Skip pre-validation, go directly to execution
    logger.opportunity(`🚀 AGGRESSIVE EXECUTION: Found ${profitableOpportunities.length} opportunities, executing directly!`);

    // Sort by profitability (highest first)
    profitableOpportunities.sort((a, b) => b.profitPercent - a.profitPercent);

    // Execute the most profitable opportunities (limit to prevent spam)
    const toExecute = profitableOpportunities.slice(0, 2); // Max 2 parallel executions

    logger.success(`⚡ Attempting direct execution of ${toExecute.length} opportunities`);

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
        
        // Send Telegram notification for successful trade
        await this.telegramBot.notifyTradeExecution(opportunity, result);
      } else {
        logger.error(`Trade failed: ${result.error}`);
        
        // Send Telegram notification for failed trade
        await this.telegramBot.notifyTradeExecution(opportunity, result);
      }
    } catch (error) {
      logger.error('Error executing opportunity:', error);
      
      // Send Telegram error notification
      await this.telegramBot.notifyError(
        error instanceof Error ? error.message : 'Unknown error during trade execution',
        `Opportunity: ${opportunity.profitPercent.toFixed(2)}% profit on ${opportunity.dexA} -> ${opportunity.dexB}`
      );
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
    setInterval(async () => {
      if (!this.isRunning) return;

      this.stats.uptime = Date.now() - this.startTime;
      this.printStats();
      
      // Send periodic Telegram stats report
      await this.telegramBot.sendStatsReport(this.stats);
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
    process.on('SIGINT', async () => {
      logger.info('\n👋 Received SIGINT, shutting down gracefully...');
      await bot.stop();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      logger.info('\n👋 Received SIGTERM, shutting down gracefully...');
      await bot.stop();
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