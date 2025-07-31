import TelegramBot from 'node-telegram-bot-api';
import { logger } from './logger';
import { ArbitrageOpportunity } from './types';

interface BotStats {
  opportunitiesFound: number;
  tradesExecuted: number;
  successfulTrades: number;
  totalProfit: number;
  uptime: number;
}

interface TradeResult {
  success: boolean;
  profit?: string;
  txHash?: string;
  error?: string;
}

export class TelegramBotService {
  private bot: TelegramBot | null = null;
  private chatId: string | null = null;
  private isEnabled: boolean = false;
  private lastStatsReport: number = 0;
  private statsReportInterval: number = 30 * 60 * 1000; // 30 minutes

  constructor() {
    this.initialize();
  }

  private initialize(): void {
    const token = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = process.env.TELEGRAM_CHAT_ID;

    if (!token || !chatId) {
      logger.info('📱 Telegram bot not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)');
      return;
    }

    try {
      this.bot = new TelegramBot(token, { polling: true });
      this.chatId = chatId;
      this.isEnabled = true;
      this.setupCommands();
      logger.success('📱 Telegram bot initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Telegram bot:', error);
      this.isEnabled = false;
    }
  }

  private setupCommands(): void {
    if (!this.bot) return;

    // Handle /start command
    this.bot.onText(/\/start/, (msg) => {
      this.sendMessage(`🤖 Welcome to Flashloan Arbitrage Bot!

Available commands:
/status - Get current bot status
/stats - Get detailed statistics
/stop - Stop the bot (admin only)
/help - Show this help message`);
    });

    // Handle /status command
    this.bot.onText(/\/status/, (msg) => {
      this.handleStatusCommand();
    });

    // Handle /stats command
    this.bot.onText(/\/stats/, (msg) => {
      this.handleStatsCommand();
    });

    // Handle /help command
    this.bot.onText(/\/help/, (msg) => {
      this.sendMessage(`🤖 Flashloan Arbitrage Bot Commands:

/start - Show welcome message
/status - Get current bot status
/stats - Get detailed statistics  
/stop - Stop the bot (admin only)
/help - Show this help message

The bot will automatically send:
• Start/stop notifications
• Trade execution results
• Periodic statistics reports
• Error alerts`);
    });

    // Handle /stop command
    this.bot.onText(/\/stop/, (msg) => {
      this.handleStopCommand();
    });

    logger.info('📱 Telegram bot commands configured');
  }

  /**
   * Handle /status command
   */
  private async handleStatusCommand(): Promise<void> {
    // Import FlashloanArbitrageBot dynamically to avoid circular imports
    const { FlashloanArbitrageBot } = await import('./index');
    const bot = FlashloanArbitrageBot.getInstance();
    
    if (!bot) {
      await this.sendMessage('❌ Bot instance not found. Please start the bot first.');
      return;
    }

    const isRunning = bot.getIsRunning();
    const stats = bot.getStats();
    const uptime = Math.floor(stats.uptime / 1000 / 60); // minutes

    const message = `📊 *Bot Status*

🔄 **Status:** ${isRunning ? '✅ Running' : '❌ Stopped'}
⏱️ **Uptime:** ${uptime} minutes
🔍 **Opportunities Found:** ${stats.opportunitiesFound}
📈 **Trades Executed:** ${stats.tradesExecuted}
✅ **Successful Trades:** ${stats.successfulTrades}
💰 **Total Profit:** \`${stats.totalProfit.toFixed(4)} ETH\`

${isRunning ? '🚀 Bot is actively monitoring for opportunities!' : '⏹️ Bot is currently stopped.'}`;

    await this.sendMessage(message);
  }

  /**
   * Handle /stats command  
   */
  private async handleStatsCommand(): Promise<void> {
    // Import FlashloanArbitrageBot dynamically to avoid circular imports
    const { FlashloanArbitrageBot } = await import('./index');
    const bot = FlashloanArbitrageBot.getInstance();
    
    if (!bot) {
      await this.sendMessage('❌ Bot instance not found. Please start the bot first.');
      return;
    }

    const stats = bot.getStats();
    const uptime = Math.floor(stats.uptime / 1000 / 60); // minutes
    const successRate = stats.tradesExecuted > 0 
      ? (stats.successfulTrades / stats.tradesExecuted * 100).toFixed(1)
      : '0';

    const message = `📈 *Detailed Statistics*

⏱️ **Uptime:** ${uptime} minutes
🔍 **Opportunities Found:** ${stats.opportunitiesFound}
📈 **Trades Executed:** ${stats.tradesExecuted}
✅ **Successful Trades:** ${stats.successfulTrades}
❌ **Failed Trades:** ${stats.tradesExecuted - stats.successfulTrades}
📊 **Success Rate:** ${successRate}%
💰 **Total Profit:** \`${stats.totalProfit.toFixed(4)} ETH\`

${stats.totalProfit > 0 ? '🎉 Profitable trading session!' : '🔍 Still searching for profitable opportunities...'}

*Average per trade:* ${stats.tradesExecuted > 0 ? `\`${(stats.totalProfit / stats.tradesExecuted).toFixed(6)} ETH\`` : 'N/A'}`;

    await this.sendMessage(message);
  }

  /**
   * Handle /stop command
   */
  private async handleStopCommand(): Promise<void> {
    // Import FlashloanArbitrageBot dynamically to avoid circular imports
    const { FlashloanArbitrageBot } = await import('./index');
    const bot = FlashloanArbitrageBot.getInstance();
    
    if (!bot) {
      await this.sendMessage('❌ Bot instance not found.');
      return;
    }

    if (!bot.getIsRunning()) {
      await this.sendMessage('ℹ️ Bot is already stopped.');
      return;
    }

    await this.sendMessage('⏹️ Stopping bot via Telegram command...');
    
    try {
      await bot.stop();
      await this.sendMessage('✅ Bot stopped successfully via Telegram command.');
    } catch (error) {
      await this.sendMessage(`❌ Failed to stop bot: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Send a message to the configured chat
   */
  async sendMessage(message: string): Promise<boolean> {
    if (!this.isEnabled || !this.bot || !this.chatId) {
      return false;
    }

    try {
      await this.bot.sendMessage(this.chatId, message, {
        parse_mode: 'Markdown',
        disable_web_page_preview: true
      });
      return true;
    } catch (error) {
      logger.error('Failed to send Telegram message:', error);
      return false;
    }
  }

  /**
   * Send bot started notification
   */
  async notifyBotStarted(): Promise<void> {
    const message = `🚀 *Flashloan Arbitrage Bot Started*

✅ Bot is now monitoring for arbitrage opportunities
📊 Will report statistics every 30 minutes
🔔 You'll receive notifications for trades and important events

Use /status to check current status anytime.`;

    await this.sendMessage(message);
  }

  /**
   * Send bot stopped notification
   */
  async notifyBotStopped(): Promise<void> {
    const message = `⏹️ *Flashloan Arbitrage Bot Stopped*

🛑 Bot has stopped monitoring for opportunities
📈 Final statistics will be available via /stats command

Thank you for using the arbitrage bot!`;

    await this.sendMessage(message);
  }

  /**
   * Send trade execution notification
   */
  async notifyTradeExecution(opportunity: ArbitrageOpportunity, result: TradeResult): Promise<void> {
    if (result.success) {
      const message = `💰 *Trade Executed Successfully*

🎯 Profit: \`${result.profit || 'N/A'} ETH\`
📈 Profit Percentage: \`${opportunity.profitPercent.toFixed(2)}%\`
🔄 Route: ${opportunity.dexA} → ${opportunity.dexB}
🪙 Token: ${opportunity.tokenA} → ${opportunity.tokenB}
💵 Amount: \`${opportunity.amountIn}\`
⛽ Gas Estimate: \`${opportunity.gasEstimate}\`
🌐 Chain: ${this.getChainName(opportunity.chainId)}
${result.txHash ? `🔗 TX: \`${result.txHash}\`` : ''}

Keep it up! 🚀`;

      await this.sendMessage(message);
    } else {
      const message = `❌ *Trade Execution Failed*

😞 Profit Lost: \`${opportunity.profitPercent.toFixed(2)}%\`
🔄 Route: ${opportunity.dexA} → ${opportunity.dexB}
🪙 Token: ${opportunity.tokenA} → ${opportunity.tokenB}
⚠️ Error: ${result.error || 'Unknown error'}
🌐 Chain: ${this.getChainName(opportunity.chainId)}

The bot will continue monitoring for new opportunities.`;

      await this.sendMessage(message);
    }
  }

  /**
   * Send opportunity discovered notification (throttled)
   */
  async notifyOpportunityFound(opportunities: ArbitrageOpportunity[]): Promise<void> {
    if (opportunities.length === 0) return;

    // Only notify for significant opportunities (>2% profit) and throttle notifications
    const significantOpportunities = opportunities.filter(op => op.profitPercent >= 2.0);
    
    if (significantOpportunities.length === 0) return;

    // Find the best opportunity
    const bestOpportunity = significantOpportunities.reduce((best, current) => 
      current.profitPercent > best.profitPercent ? current : best
    );

    const message = `🔍 *High-Profit Opportunity Detected*

💰 Best Profit: \`${bestOpportunity.profitPercent.toFixed(2)}%\`
🔄 Route: ${bestOpportunity.dexA} → ${bestOpportunity.dexB}
🪙 Token: ${bestOpportunity.tokenA} → ${bestOpportunity.tokenB}
📊 Total Found: ${significantOpportunities.length} opportunities (${opportunities.length} total)
🌐 Chain: ${this.getChainName(bestOpportunity.chainId)}

Bot is analyzing for execution...`;

    await this.sendMessage(message);
  }

  /**
   * Send periodic statistics report
   */
  async sendStatsReport(stats: BotStats): Promise<void> {
    const now = Date.now();
    
    // Check if enough time has passed since last report
    if (now - this.lastStatsReport < this.statsReportInterval) {
      return;
    }

    this.lastStatsReport = now;

    const uptime = Math.floor(stats.uptime / 1000 / 60); // minutes
    const successRate = stats.tradesExecuted > 0 
      ? (stats.successfulTrades / stats.tradesExecuted * 100).toFixed(1)
      : '0';

    const message = `📊 *Periodic Statistics Report*

⏱️ *Uptime:* ${uptime} minutes
🔍 *Opportunities Found:* ${stats.opportunitiesFound}
📈 *Trades Executed:* ${stats.tradesExecuted}
✅ *Success Rate:* ${successRate}%
💰 *Total Profit:* \`${stats.totalProfit.toFixed(4)} ETH\`

${stats.totalProfit > 0 ? '🚀 Great performance!' : '🔍 Still searching for profitable opportunities...'}

Use /stats for detailed information anytime.`;

    await this.sendMessage(message);
  }

  /**
   * Send error notification
   */
  async notifyError(error: string, context?: string): Promise<void> {
    const message = `🚨 *Error Alert*

⚠️ **Error:** ${error}
${context ? `📝 **Context:** ${context}` : ''}
🕐 **Time:** ${new Date().toISOString()}

The bot will continue running and attempt to recover automatically.`;

    await this.sendMessage(message);
  }

  /**
   * Get chain name from chain ID
   */
  private getChainName(chainId: number): string {
    const chainNames: { [key: number]: string } = {
      1: 'Ethereum',
      56: 'BSC',
      137: 'Polygon',
      42161: 'Arbitrum'
    };
    return chainNames[chainId] || `Chain ${chainId}`;
  }

  /**
   * Check if Telegram bot is enabled
   */
  isActive(): boolean {
    return this.isEnabled;
  }

  /**
   * Clean shutdown of the bot
   */
  async shutdown(): Promise<void> {
    if (this.bot) {
      try {
        await this.bot.stopPolling();
        logger.info('📱 Telegram bot stopped');
      } catch (error) {
        logger.error('Error stopping Telegram bot:', error);
      }
    }
  }
}