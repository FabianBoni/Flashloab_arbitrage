import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import path from 'path';
import { FlashloanArbitrageBot } from './index';

interface BotInstance {
  bot: FlashloanArbitrageBot;
  isRunning: boolean;
  connectedAccount?: string;
  chainId?: string;
}

class ArbitrageBotWebServer {
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
    // Serve the main frontend
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(process.cwd(), 'public/index.html'));
    });

    // API Routes
    this.app.post('/api/wallet/connect', this.handleWalletConnect.bind(this));
    this.app.post('/api/bot/start', this.handleBotStart.bind(this));
    this.app.post('/api/bot/stop', this.handleBotStop.bind(this));
    this.app.get('/api/bot/stats', this.handleGetStats.bind(this));
    this.app.get('/api/bot/status', this.handleGetStatus.bind(this));

    // Health check
    this.app.get('/api/health', (req, res) => {
      res.json({ status: 'ok', timestamp: new Date().toISOString() });
    });
  }

  private async handleWalletConnect(req: express.Request, res: express.Response) {
    try {
      const { account, chainId } = req.body;

      if (!account || !chainId) {
        return res.status(400).json({
          success: false,
          error: 'Account and chainId are required'
        });
      }

      console.log(`🔗 Wallet connected: ${account} on chain ${parseInt(chainId, 16)}`);

      // Validate the chain is supported
      const supportedChains = [1, 137, 42161, 56]; // Ethereum, Polygon, Arbitrum, BSC
      const chainIdDecimal = parseInt(chainId, 16);
      
      if (!supportedChains.includes(chainIdDecimal)) {
        return res.status(400).json({
          success: false,
          error: `Unsupported chain ID: ${chainIdDecimal}. Please switch to Ethereum, Polygon, Arbitrum, or BSC.`
        });
      }

      // Store wallet connection info
      if (this.botInstance) {
        this.botInstance.connectedAccount = account;
        this.botInstance.chainId = chainId;
      }

      res.json({
        success: true,
        message: 'Wallet connected successfully',
        account,
        chainId: chainIdDecimal
      });

    } catch (error: any) {
      console.error('Error handling wallet connection:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Internal server error'
      });
    }
  }

  private async handleBotStart(req: express.Request, res: express.Response) {
    try {
      const { account, chainId } = req.body;

      if (!account || !chainId) {
        return res.status(400).json({
          success: false,
          error: 'Account and chainId are required'
        });
      }

      if (this.botInstance && this.botInstance.isRunning) {
        return res.status(400).json({
          success: false,
          error: 'Bot is already running'
        });
      }

      console.log(`🤖 Starting bot for account: ${account} on chain ${parseInt(chainId, 16)}`);

      // Create a new bot instance
      const bot = new FlashloanArbitrageBot();
      
      this.botInstance = {
        bot,
        isRunning: false,
        connectedAccount: account,
        chainId
      };

      // Start the bot (this will use the configured private key method for now)
      // In a full implementation, we would enhance this to use MetaMask providers
      await this.botInstance.bot.start();
      this.botInstance.isRunning = true;

      console.log('✅ Bot started successfully with MetaMask connection info');

      res.json({
        success: true,
        message: 'Bot started successfully',
        account,
        chainId: parseInt(chainId, 16)
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
      if (!this.botInstance || !this.botInstance.isRunning) {
        return res.status(400).json({
          success: false,
          error: 'Bot is not running'
        });
      }

      console.log('🛑 Stopping bot...');

      await this.botInstance.bot.stop();
      this.botInstance.isRunning = false;

      console.log('✅ Bot stopped successfully');

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

  private handleGetStats(req: express.Request, res: express.Response) {
    try {
      if (!this.botInstance) {
        return res.json({
          opportunitiesFound: 0,
          tradesExecuted: 0,
          successfulTrades: 0,
          totalProfit: 0,
          uptime: 0
        });
      }

      const stats = this.botInstance.bot.getStats();
      res.json(stats);

    } catch (error: any) {
      console.error('Error getting stats:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to get stats'
      });
    }
  }

  private handleGetStatus(req: express.Request, res: express.Response) {
    try {
      const status = {
        isRunning: this.botInstance?.isRunning || false,
        connectedAccount: this.botInstance?.connectedAccount || null,
        chainId: this.botInstance?.chainId ? parseInt(this.botInstance.chainId, 16) : null,
        uptime: this.botInstance ? this.botInstance.bot.getStats().uptime : 0
      };

      res.json(status);

    } catch (error: any) {
      console.error('Error getting status:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Failed to get status'
      });
    }
  }

  public start() {
    this.app.listen(this.port, () => {
      console.log('🌐 Flashloan Arbitrage Bot Web Interface Started');
      console.log(`📱 Open your browser to: http://localhost:${this.port}`);
      console.log('🦊 Make sure MetaMask is installed and connected');
      console.log('');
      console.log('Supported Networks:');
      console.log('  • Ethereum Mainnet (Chain ID: 1)');
      console.log('  • Polygon (Chain ID: 137)');
      console.log('  • Arbitrum (Chain ID: 42161)');
      console.log('  • BSC (Chain ID: 56)');
      console.log('');
    });

    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      console.log('\n👋 Shutting down web server...');
      if (this.botInstance && this.botInstance.isRunning) {
        console.log('🛑 Stopping bot...');
        await this.botInstance.bot.stop();
      }
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      console.log('\n👋 Received SIGTERM, shutting down gracefully...');
      if (this.botInstance && this.botInstance.isRunning) {
        console.log('🛑 Stopping bot...');
        await this.botInstance.bot.stop();
      }
      process.exit(0);
    });
  }
}

// Start the web server if this file is executed directly
if (require.main === module) {
  const port = parseInt(process.env.WEB_PORT || '3000');
  const server = new ArbitrageBotWebServer(port);
  server.start();
}

export { ArbitrageBotWebServer };