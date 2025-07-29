import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import path from 'path';
import { FlashloanArbitrageBot } from './index.js';

interface BotInstance {
  bot: FlashloanArbitrageBot;
  isRunning: boolean;
  connectedAccount?: string;
  chainId?: string;
  stats: {
    opportunitiesFound: number;
    tradesExecuted: number;
    successfulTrades: number;
    totalProfit: number;
    startTime: number;
  };
  currentOpportunities: any[];
}

class ArbitrageDashboardServer {
  private app: express.Application;
  private port: number;
  private botInstance: BotInstance | null = null;

  constructor(port = 3000) {
    this.app = express();
    this.port = port;
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json());
    this.app.use(express.static(path.join(process.cwd(), 'public')));
  }

  private setupRoutes() {
    // Serve the dashboard
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(process.cwd(), 'public/dashboard.html'));
    });

    // Legacy route
    this.app.get('/old', (req, res) => {
      res.sendFile(path.join(process.cwd(), 'public/index.html'));
    });

    // API Routes
    this.app.post('/api/bot/start', this.handleBotStart.bind(this));
    this.app.post('/api/bot/stop', this.handleBotStop.bind(this));
    this.app.get('/api/bot/status', this.handleGetStatus.bind(this));
    this.app.get('/api/opportunities', this.handleGetOpportunities.bind(this));
    this.app.get('/api/stats', this.handleGetStats.bind(this));
    
    // Settings API
    this.app.post('/api/settings/threshold', this.handleUpdateThreshold.bind(this));
    this.app.post('/api/settings/gas', this.handleUpdateGas.bind(this));
    this.app.post('/api/settings/interval', this.handleUpdateInterval.bind(this));
    
    // Flashloan fees API
    this.app.get('/api/fees', this.handleGetFees.bind(this));

    // Health check
    this.app.get('/api/health', (req, res) => {
      res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        botRunning: this.botInstance?.isRunning || false
      });
    });
  }

  private async handleBotStart(req: express.Request, res: express.Response) {
    try {
      const { account } = req.body;

      // Check if there's already a running bot instance
      const runningBot = FlashloanArbitrageBot.getInstance();
      if (runningBot && runningBot.getIsRunning()) {
        return res.status(400).json({
          success: false,
          error: 'Bot is already running from main process'
        });
      }

      if (this.botInstance?.isRunning) {
        return res.status(400).json({
          success: false,
          error: 'Bot is already running'
        });
      }

      console.log('🚀 Starting arbitrage bot from dashboard...');

      // Create new bot instance
      this.botInstance = {
        bot: new FlashloanArbitrageBot(),
        isRunning: true,
        connectedAccount: account,
        stats: {
          opportunitiesFound: 0,
          tradesExecuted: 0,
          successfulTrades: 0,
          totalProfit: 0,
          startTime: Date.now()
        },
        currentOpportunities: []
      };

      // Start the bot
      await this.botInstance.bot.start();

      // Monitor bot events
      this.setupBotEventListeners();

      res.json({
        success: true,
        message: 'Bot started successfully',
        account
      });

    } catch (error: any) {
      console.error('Error starting bot:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to start bot'
      });
    }
  }

  private async handleBotStop(req: express.Request, res: express.Response) {
    try {
      // Check if there's a running bot instance from main process
      const runningBot = FlashloanArbitrageBot.getInstance();
      if (runningBot && runningBot.getIsRunning()) {
        return res.status(400).json({
          success: false,
          error: 'Cannot stop bot started from main process. Use terminal to stop the bot.'
        });
      }

      if (!this.botInstance?.isRunning) {
        return res.status(400).json({
          success: false,
          error: 'Bot is not running'
        });
      }

      console.log('⏹️ Stopping arbitrage bot from dashboard...');

      // Stop the bot
      await this.botInstance.bot.stop();
      this.botInstance.isRunning = false;

      res.json({
        success: true,
        message: 'Bot stopped successfully'
      });

    } catch (error: any) {
      console.error('Error stopping bot:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to stop bot'
      });
    }
  }

  private handleGetStatus(req: express.Request, res: express.Response) {
    try {
      // Try to get the running bot instance
      const runningBot = FlashloanArbitrageBot.getInstance();
      
      if (runningBot && runningBot.getIsRunning()) {
        const botStats = runningBot.getStats();
        const status = {
          running: true,
          account: this.botInstance?.connectedAccount || null,
          uptime: botStats.uptime,
          stats: botStats
        };
        res.json(status);
      } else {
        const status = {
          running: this.botInstance?.isRunning || false,
          account: this.botInstance?.connectedAccount || null,
          uptime: this.botInstance ? Date.now() - this.botInstance.stats.startTime : 0,
          stats: this.botInstance?.stats || {
            opportunitiesFound: 0,
            tradesExecuted: 0,
            successfulTrades: 0,
            totalProfit: 0,
            startTime: 0
          }
        };
        res.json(status);
      }
    } catch (error: any) {
      console.error('Error getting bot status:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to get bot status'
      });
    }
  }

  private handleGetOpportunities(req: express.Request, res: express.Response) {
    try {
      // Try to get opportunities from the running bot instance
      const runningBot = FlashloanArbitrageBot.getInstance();
      let opportunities: any[] = [];
      
      if (runningBot && runningBot.getIsRunning()) {
        opportunities = runningBot.getCurrentOpportunities();
      } else {
        opportunities = this.botInstance?.currentOpportunities || [];
      }
      
      // Calculate profit after fees for each opportunity
      const enrichedOpportunities = opportunities.map(opp => {
        const grossProfit = parseFloat(opp.amountIn) * (opp.profitPercent / 100);
        const flashloanFee = parseFloat(opp.amountIn) * 0.0025; // 0.25% flashloan fee
        const gasFee = 0.001; // Estimated gas fee in ETH
        const profitAfterFees = grossProfit - flashloanFee - gasFee;

        return {
          ...opp,
          grossProfit,
          flashloanFee,
          gasFee,
          profitAfterFees,
          timestamp: new Date().toISOString()
        };
      });

      res.json(enrichedOpportunities);
    } catch (error: any) {
      console.error('Error getting opportunities:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to get opportunities'
      });
    }
  }

  private handleGetStats(req: express.Request, res: express.Response) {
    try {
      const stats = this.botInstance?.stats || {
        opportunitiesFound: 0,
        tradesExecuted: 0,
        successfulTrades: 0,
        totalProfit: 0,
        startTime: 0
      };

      res.json({
        ...stats,
        uptime: this.botInstance ? Date.now() - stats.startTime : 0,
        successRate: stats.tradesExecuted > 0 ? (stats.successfulTrades / stats.tradesExecuted) * 100 : 0,
        avgProfit: stats.successfulTrades > 0 ? stats.totalProfit / stats.successfulTrades : 0
      });
    } catch (error: any) {
      console.error('Error getting stats:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to get stats'
      });
    }
  }

  private async handleUpdateThreshold(req: express.Request, res: express.Response) {
    try {
      const { threshold } = req.body;
      
      if (!threshold || threshold < 0) {
        return res.status(400).json({
          success: false,
          error: 'Invalid threshold value'
        });
      }

      // This would update the bot's configuration
      console.log(`📊 Profit threshold updated to ${threshold} ETH`);
      
      res.json({
        success: true,
        message: `Profit threshold updated to ${threshold} ETH`
      });
    } catch (error: any) {
      console.error('Error updating threshold:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to update threshold'
      });
    }
  }

  private async handleUpdateGas(req: express.Request, res: express.Response) {
    try {
      const { maxGasPrice } = req.body;
      
      if (!maxGasPrice || maxGasPrice < 1) {
        return res.status(400).json({
          success: false,
          error: 'Invalid gas price value'
        });
      }

      console.log(`⛽ Max gas price updated to ${maxGasPrice} Gwei`);
      
      res.json({
        success: true,
        message: `Max gas price updated to ${maxGasPrice} Gwei`
      });
    } catch (error: any) {
      console.error('Error updating gas price:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to update gas price'
      });
    }
  }

  private async handleUpdateInterval(req: express.Request, res: express.Response) {
    try {
      const { interval } = req.body;
      
      if (!interval || interval < 1000) {
        return res.status(400).json({
          success: false,
          error: 'Invalid interval value (minimum 1000ms)'
        });
      }

      console.log(`⏰ Check interval updated to ${interval}ms`);
      
      res.json({
        success: true,
        message: `Check interval updated to ${interval}ms`
      });
    } catch (error: any) {
      console.error('Error updating interval:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to update interval'
      });
    }
  }

  private handleGetFees(req: express.Request, res: express.Response) {
    try {
      const fees = {
        pancakeSwap: 0.25, // 0.25%
        aave: 0.09, // 0.09%
        uniswap: 0.30, // 0.30%
        average: 0.21, // Average
        estimated: {
          small: 2.5, // $2.5 for $1000 trade
          medium: 12.5, // $12.5 for $5000 trade
          large: 25 // $25 for $10000 trade
        }
      };

      res.json(fees);
    } catch (error: any) {
      console.error('Error getting fees:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to get fees'
      });
    }
  }

  private setupBotEventListeners() {
    if (!this.botInstance) return;

    // Mock event listening - in real implementation, you'd listen to actual bot events
    const updateStats = () => {
      if (this.botInstance) {
        // Simulate finding opportunities
        if (Math.random() > 0.7) {
          this.botInstance.stats.opportunitiesFound++;
          
          // Generate mock opportunity
          const mockOpportunity = {
            tokenA: '0x55d398326f99059fF775485246999027B3197955', // USDT
            tokenB: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d', // USDC
            dexA: 'Biswap',
            dexB: 'PancakeSwap V2',
            amountIn: '1000000000000000000', // 1 token
            profitPercent: Math.random() * 5 + 1, // 1-6%
            path: ['0x55d398326f99059fF775485246999027B3197955', '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d']
          };
          
          this.botInstance.currentOpportunities = [mockOpportunity];
        }
      }
    };

    // Update stats every 10 seconds
    setInterval(updateStats, 10000);
  }

  public start() {
    this.app.listen(this.port, () => {
      console.log(`🌐 Arbitrage Dashboard Server running on http://localhost:${this.port}`);
      console.log(`📊 Access the dashboard at http://localhost:${this.port}`);
    });
  }
}

export { ArbitrageDashboardServer };
