// MetaMask and Web3 Integration for Flashloan Arbitrage Bot
class ArbitrageBotUI {
    constructor() {
        this.web3 = null;
        this.account = null;
        this.chainId = null;
        this.isConnected = false;
        this.botRunning = false;
        this.stats = {
            opportunitiesFound: 0,
            tradesExecuted: 0,
            successfulTrades: 0,
            totalProfit: 0
        };
        
        this.init();
    }

    async init() {
        // Check if MetaMask is installed
        if (typeof window.ethereum !== 'undefined') {
            console.log('MetaMask detected');
            
            // Listen for account changes
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    this.handleAccountChange(accounts[0]);
                }
            });

            // Listen for chain changes
            window.ethereum.on('chainChanged', (chainId) => {
                this.handleChainChange(chainId);
            });

            // Check if already connected
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            if (accounts.length > 0) {
                await this.connectWallet();
            }
        } else {
            this.addLog('MetaMask not detected. Please install MetaMask to use this application.', 'error');
            document.getElementById('connectBtn').textContent = 'Install MetaMask';
            document.getElementById('connectBtn').onclick = () => {
                window.open('https://metamask.io/', '_blank');
            };
        }

        // Start polling for stats updates
        this.startStatsPolling();
    }

    async connectWallet() {
        try {
            if (typeof window.ethereum === 'undefined') {
                throw new Error('MetaMask not installed');
            }

            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length === 0) {
                throw new Error('No accounts found');
            }

            this.account = accounts[0];
            
            // Get chain ID
            this.chainId = await window.ethereum.request({
                method: 'eth_chainId'
            });

            // Get balance
            const balance = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [this.account, 'latest']
            });

            this.isConnected = true;
            await this.updateUI();
            this.addLog(`Connected to MetaMask: ${this.account}`, 'success');

            // Notify backend about wallet connection
            await this.notifyBackendConnection();

        } catch (error) {
            console.error('Error connecting to MetaMask:', error);
            this.addLog(`Connection failed: ${error.message}`, 'error');
        }
    }

    async disconnect() {
        this.isConnected = false;
        this.account = null;
        this.chainId = null;
        await this.updateUI();
        this.addLog('Disconnected from MetaMask', 'warning');
        
        // Stop bot if running
        if (this.botRunning) {
            await this.stopBot();
        }
    }

    async handleAccountChange(newAccount) {
        this.account = newAccount;
        await this.updateUI();
        this.addLog(`Account changed to: ${newAccount}`, 'warning');
        
        // Notify backend about account change
        await this.notifyBackendConnection();
    }

    async handleChainChange(newChainId) {
        this.chainId = newChainId;
        await this.updateUI();
        this.addLog(`Network changed to chain ID: ${parseInt(newChainId, 16)}`, 'warning');
        
        // Stop bot if running on unsupported network
        const supportedChains = [1, 137, 42161, 56]; // Ethereum, Polygon, Arbitrum, BSC
        const chainIdDecimal = parseInt(newChainId, 16);
        
        if (!supportedChains.includes(chainIdDecimal) && this.botRunning) {
            await this.stopBot();
            this.addLog('Bot stopped due to unsupported network', 'warning');
        }
    }

    async updateUI() {
        const statusDot = document.getElementById('statusDot');
        const connectionStatus = document.getElementById('connectionStatus');
        const connectBtn = document.getElementById('connectBtn');
        const connectBtnText = document.getElementById('connectBtnText');
        const walletInfo = document.getElementById('walletInfo');
        const startBtn = document.getElementById('startBtn');

        if (this.isConnected) {
            statusDot.classList.add('connected');
            connectionStatus.textContent = 'Connected';
            connectBtnText.textContent = 'Disconnect';
            connectBtn.onclick = () => this.disconnect();
            walletInfo.classList.add('show');
            startBtn.disabled = false;

            // Update wallet info
            document.getElementById('walletAddress').textContent = 
                `${this.account.substring(0, 6)}...${this.account.substring(38)}`;
            document.getElementById('chainId').textContent = parseInt(this.chainId, 16);
            document.getElementById('networkName').textContent = this.getNetworkName(parseInt(this.chainId, 16));

            // Get and display balance
            try {
                const balance = await window.ethereum.request({
                    method: 'eth_getBalance',
                    params: [this.account, 'latest']
                });
                const ethBalance = parseFloat(parseInt(balance, 16) / 1e18).toFixed(4);
                document.getElementById('ethBalance').textContent = `${ethBalance} ETH`;
            } catch (error) {
                document.getElementById('ethBalance').textContent = 'Error';
            }
        } else {
            statusDot.classList.remove('connected');
            connectionStatus.textContent = 'Not Connected';
            connectBtnText.textContent = 'Connect MetaMask';
            connectBtn.onclick = () => this.connectWallet();
            walletInfo.classList.remove('show');
            startBtn.disabled = true;
        }
    }

    getNetworkName(chainId) {
        const networks = {
            1: 'Ethereum Mainnet',
            137: 'Polygon',
            42161: 'Arbitrum',
            56: 'BSC',
            5: 'Goerli Testnet',
            80001: 'Mumbai Testnet'
        };
        return networks[chainId] || `Chain ${chainId}`;
    }

    async startBot() {
        if (!this.isConnected) {
            this.addLog('Please connect MetaMask first', 'error');
            return;
        }

        try {
            const response = await fetch('/api/bot/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account: this.account,
                    chainId: this.chainId
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.botRunning = true;
                this.updateBotStatus();
                this.addLog('🤖 Arbitrage bot started successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to start bot');
            }
        } catch (error) {
            console.error('Error starting bot:', error);
            this.addLog(`Failed to start bot: ${error.message}`, 'error');
        }
    }

    async stopBot() {
        try {
            const response = await fetch('/api/bot/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.botRunning = false;
                this.updateBotStatus();
                this.addLog('🛑 Arbitrage bot stopped', 'warning');
            } else {
                throw new Error(result.error || 'Failed to stop bot');
            }
        } catch (error) {
            console.error('Error stopping bot:', error);
            this.addLog(`Failed to stop bot: ${error.message}`, 'error');
        }
    }

    updateBotStatus() {
        const botStatusDot = document.getElementById('botStatusDot');
        const botStatus = document.getElementById('botStatus');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');

        if (this.botRunning) {
            botStatusDot.classList.add('connected');
            botStatus.textContent = 'Running';
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            botStatusDot.classList.remove('connected');
            botStatus.textContent = 'Stopped';
            startBtn.disabled = !this.isConnected;
            stopBtn.disabled = true;
        }
    }

    async notifyBackendConnection() {
        if (!this.isConnected) return;

        try {
            await fetch('/api/wallet/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account: this.account,
                    chainId: this.chainId
                })
            });
        } catch (error) {
            console.error('Error notifying backend:', error);
        }
    }

    startStatsPolling() {
        setInterval(async () => {
            if (this.botRunning) {
                await this.updateStats();
            }
        }, 5000); // Update every 5 seconds
    }

    async updateStats() {
        try {
            const response = await fetch('/api/bot/stats');
            const stats = await response.json();
            
            if (stats) {
                this.stats = stats;
                
                document.getElementById('opportunitiesFound').textContent = stats.opportunitiesFound || 0;
                document.getElementById('tradesExecuted').textContent = stats.tradesExecuted || 0;
                
                const successRate = stats.tradesExecuted > 0 
                    ? ((stats.successfulTrades / stats.tradesExecuted) * 100).toFixed(1)
                    : '0';
                document.getElementById('successRate').textContent = `${successRate}%`;
                
                document.getElementById('totalProfit').textContent = (stats.totalProfit || 0).toFixed(4);
            }
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    addLog(message, type = 'info') {
        const logContainer = document.getElementById('logContainer');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logContainer.appendChild(logEntry);
        
        // Keep only last 50 log entries
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }
        
        // Scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// Global functions for HTML onclick handlers
let botUI;

async function connectWallet() {
    if (botUI.isConnected) {
        await botUI.disconnect();
    } else {
        await botUI.connectWallet();
    }
}

async function startBot() {
    await botUI.startBot();
}

async function stopBot() {
    await botUI.stopBot();
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    botUI = new ArbitrageBotUI();
});

// Add some demo functionality for testing
window.addEventListener('load', () => {
    // Simulate some activity for demo purposes
    setTimeout(() => {
        if (typeof botUI !== 'undefined') {
            botUI.addLog('Price monitoring initialized for 3 chains', 'success');
            botUI.addLog('Monitoring WETH, USDC, USDT, DAI pairs', 'info');
        }
    }, 2000);
});