// Dashboard JavaScript for Flashloan Arbitrage Bot
class ArbitrageDashboard {
    constructor() {
        this.web3 = null;
        this.account = null;
        this.isConnected = false;
        this.botRunning = false;
        this.stats = {
            opportunitiesFound: 0,
            tradesExecuted: 0,
            successfulTrades: 0,
            totalProfit: 0,
            opportunities: []
        };
        
        this.contractAddress = '0x0FA4cab40651cfcb308C169fd593E92F2f0cf805';
        this.contractABI = [
            'function minProfitThreshold() external view returns (uint256)',
            'function updateMinProfitThreshold(uint256 newThreshold) external',
            'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
            'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)'
        ];
        
        this.init();
    }

    init() {
        this.updateUI();
        this.startDataPolling();
        this.log('Dashboard initialized', 'info');
        
        // Auto-connect if previously connected
        if (localStorage.getItem('walletConnected') === 'true') {
            this.connectWallet();
        }
    }

    async connectWallet() {
        try {
            if (typeof window.ethereum !== 'undefined') {
                this.web3 = new Web3(window.ethereum);
                const accounts = await window.ethereum.request({ 
                    method: 'eth_requestAccounts' 
                });
                
                this.account = accounts[0];
                this.isConnected = true;
                localStorage.setItem('walletConnected', 'true');
                
                await this.updateWalletInfo();
                this.updateUI();
                this.log(`Wallet connected: ${this.account}`, 'success');
                
                // Listen for account changes
                window.ethereum.on('accountsChanged', (accounts) => {
                    if (accounts.length > 0) {
                        this.account = accounts[0];
                        this.updateWalletInfo();
                    } else {
                        this.disconnectWallet();
                    }
                });
                
                // Listen for network changes
                window.ethereum.on('chainChanged', () => {
                    window.location.reload();
                });
                
            } else {
                this.log('MetaMask not detected. Please install MetaMask.', 'error');
            }
        } catch (error) {
            this.log(`Failed to connect wallet: ${error.message}`, 'error');
        }
    }

    disconnectWallet() {
        this.account = null;
        this.isConnected = false;
        localStorage.setItem('walletConnected', 'false');
        this.updateUI();
        this.log('Wallet disconnected', 'warning');
    }

    async updateWalletInfo() {
        if (!this.isConnected || !this.web3) return;

        try {
            const balance = await this.web3.eth.getBalance(this.account);
            const network = await this.web3.eth.net.getId();
            const chainId = await this.web3.eth.getChainId();
            
            const networkNames = {
                1: 'Ethereum Mainnet',
                56: 'BSC Mainnet',
                137: 'Polygon Mainnet',
                42161: 'Arbitrum One'
            };

            document.getElementById('walletAddress').textContent = 
                `${this.account.substring(0, 6)}...${this.account.substring(38)}`;
            document.getElementById('networkName').textContent = 
                networkNames[chainId] || `Chain ID ${chainId}`;
            document.getElementById('ethBalance').textContent = 
                `${(parseFloat(this.web3.utils.fromWei(balance, 'ether'))).toFixed(4)} ETH`;
            document.getElementById('chainId').textContent = chainId;
            
        } catch (error) {
            this.log(`Failed to update wallet info: ${error.message}`, 'error');
        }
    }

    async startBot() {
        if (!this.isConnected) {
            this.log('Please connect your wallet first', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/bot/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ account: this.account })
            });
            
            if (response.ok) {
                this.botRunning = true;
                this.updateUI();
                this.log('Bot started successfully', 'success');
            } else {
                const errorData = await response.json();
                if (errorData.error && errorData.error.includes('already running from main process')) {
                    this.log('Bot is already running from terminal. Dashboard will show live data.', 'info');
                    this.botRunning = true;
                    this.updateUI();
                } else {
                    this.log(`Failed to start bot: ${errorData.error || 'Unknown error'}`, 'error');
                }
            }
        } catch (error) {
            this.log(`Failed to start bot: ${error.message}`, 'error');
        }
    }

    async stopBot() {
        try {
            const response = await fetch('/api/bot/stop', { method: 'POST' });
            
            if (response.ok) {
                this.botRunning = false;
                this.updateUI();
                this.log('Bot stopped', 'warning');
            } else {
                const errorData = await response.json();
                if (errorData.error && errorData.error.includes('main process')) {
                    this.log('Cannot stop bot from dashboard - it was started from terminal. Use Ctrl+C in terminal to stop.', 'warning');
                } else {
                    this.log(`Failed to stop bot: ${errorData.error || 'Unknown error'}`, 'error');
                }
            }
        } catch (error) {
            this.log(`Failed to stop bot: ${error.message}`, 'error');
        }
    }

    async updateProfitThreshold() {
        const threshold = document.getElementById('profitThreshold').value;
        
        if (!this.isConnected || !this.web3) {
            this.log('Please connect your wallet first', 'warning');
            return;
        }

        try {
            const contract = new this.web3.eth.Contract(this.contractABI, this.contractAddress);
            const thresholdWei = this.web3.utils.toWei(threshold, 'ether');
            
            const tx = await contract.methods.updateMinProfitThreshold(thresholdWei).send({
                from: this.account,
                gas: 100000
            });
            
            this.log(`Profit threshold updated to ${threshold} ETH. Tx: ${tx.transactionHash}`, 'success');
        } catch (error) {
            this.log(`Failed to update profit threshold: ${error.message}`, 'error');
        }
    }

    async updateGasPrice() {
        const gasPrice = document.getElementById('maxGasPrice').value;
        this.log(`Max gas price updated to ${gasPrice} Gwei`, 'info');
        // This would typically update bot configuration
    }

    async updateInterval() {
        const interval = document.getElementById('checkInterval').value;
        this.log(`Check interval updated to ${interval}ms`, 'info');
        // This would typically update bot configuration
    }

    startDataPolling() {
        // Poll for bot status and opportunities every 1 second for real-time updates
        setInterval(async () => {
            await this.updateBotStatus();
            await this.updateOpportunities();
        }, 1000);
        
        // Update flashloan fees less frequently (every 30 seconds)
        setInterval(async () => {
            await this.updateFlashloanFees();
        }, 30000);
        
        // Initial updates
        this.updateBotStatus();
        this.updateOpportunities();
        this.updateFlashloanFees();
    }

    async updateBotStatus() {
        try {
            const response = await fetch('/api/bot/status');
            if (response.ok) {
                const status = await response.json();
                this.updateStats(status);
                
                if (status.running !== this.botRunning) {
                    this.botRunning = status.running;
                    this.updateUI();
                }
            }
        } catch (error) {
            // Silently handle polling errors
        }
    }

    async updateOpportunities() {
        try {
            const response = await fetch('/api/opportunities');
            if (response.ok) {
                const opportunities = await response.json();
                this.displayOpportunities(opportunities);
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                this.showUpdateIndicator();
            }
        } catch (error) {
            // Silently handle polling errors
        }
    }

    async updateFlashloanFees() {
        // Calculate and display current flashloan fees
        const pancakeSwapFee = 0.25; // 0.25%
        const aaveFee = 0.09; // 0.09%
        const avgFee = (pancakeSwapFee + aaveFee) / 2;
        
        document.getElementById('avgFlashloanFee').textContent = `${avgFee.toFixed(2)}%`;
        document.getElementById('pancakeSwapFee').textContent = `${pancakeSwapFee}%`;
        document.getElementById('aaveFee').textContent = `${aaveFee}%`;
        
        // Estimate fee cost based on average trade size
        const avgTradeSize = 1000; // $1000 USD
        const feeCost = (avgTradeSize * avgFee / 100);
        document.getElementById('totalFeeCost').textContent = `$${feeCost.toFixed(2)}`;
    }

    updateStats(status) {
        if (status.stats) {
            this.stats = { ...this.stats, ...status.stats };
            
            document.getElementById('opportunitiesFound').textContent = this.stats.opportunitiesFound;
            document.getElementById('tradesExecuted').textContent = this.stats.tradesExecuted;
            document.getElementById('successfulTrades').textContent = this.stats.successfulTrades;
            document.getElementById('totalProfit').textContent = this.stats.totalProfit.toFixed(4);
            
            const successRate = this.stats.tradesExecuted > 0 
                ? (this.stats.successfulTrades / this.stats.tradesExecuted * 100).toFixed(1)
                : 0;
            document.getElementById('successRate').textContent = `${successRate}%`;
            
            const avgProfit = this.stats.successfulTrades > 0
                ? (this.stats.totalProfit / this.stats.successfulTrades).toFixed(4)
                : 0;
            document.getElementById('avgProfit').textContent = avgProfit;
        }
    }

    displayOpportunities(opportunities) {
        const container = document.getElementById('opportunityList');
        
        if (!opportunities || opportunities.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; color: #64748b; padding: 40px;">
                    No opportunities detected. Bot is scanning markets...
                </div>
            `;
            return;
        }

        container.innerHTML = opportunities.map(opp => {
            const isProfitable = opp.profitAfterFees > 0;
            const profitClass = isProfitable ? 'profitable' : 'unprofitable';
            const profitColor = isProfitable ? 'positive' : 'negative';
            
            return `
                <div class="opportunity-item ${profitClass}">
                    <div class="opportunity-header">
                        <div>
                            <strong>${opp.dexA} → ${opp.dexB}</strong>
                            <div class="opportunity-details">
                                ${opp.tokenA} → ${opp.tokenB} | Amount: ${opp.amount}
                            </div>
                        </div>
                        <div class="opportunity-profit ${profitColor}">
                            ${isProfitable ? '+' : ''}${opp.profitAfterFees.toFixed(4)} ETH
                            <div style="font-size: 0.8rem; opacity: 0.8;">
                                (${opp.profitPercent.toFixed(2)}%)
                            </div>
                        </div>
                    </div>
                    <div class="opportunity-details">
                        Gross Profit: ${opp.grossProfit.toFixed(4)} ETH | 
                        Flashloan Fee: ${opp.flashloanFee.toFixed(4)} ETH | 
                        Gas Fee: ${opp.gasFee.toFixed(4)} ETH
                    </div>
                </div>
            `;
        }).join('');
    }

    updateUI() {
        // Update connection status
        const statusDot = document.getElementById('statusDot');
        const connectionStatus = document.getElementById('connectionStatus');
        const connectBtn = document.getElementById('connectBtn');
        const connectBtnText = document.getElementById('connectBtnText');

        if (this.isConnected) {
            statusDot.classList.add('connected');
            connectionStatus.textContent = 'Connected';
            connectBtnText.textContent = 'Disconnect';
            connectBtn.onclick = () => this.disconnectWallet();
        } else {
            statusDot.classList.remove('connected');
            connectionStatus.textContent = 'Not Connected';
            connectBtnText.textContent = 'Connect MetaMask';
            connectBtn.onclick = () => this.connectWallet();
        }

        // Update bot status
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

    log(message, type = 'info') {
        const container = document.getElementById('logContainer');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        container.appendChild(logEntry);
        container.scrollTop = container.scrollHeight;
        
        // Keep only last 100 log entries
        while (container.children.length > 100) {
            container.removeChild(container.firstChild);
        }
    }

    showUpdateIndicator() {
        const indicator = document.getElementById('updateIndicator');
        indicator.classList.add('show');
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 2000);
    }

    resetStats() {
        this.stats = {
            opportunitiesFound: 0,
            tradesExecuted: 0,
            successfulTrades: 0,
            totalProfit: 0,
            opportunities: []
        };
        this.updateStats({ stats: this.stats });
        this.log('Statistics reset', 'info');
    }

    clearLogs() {
        document.getElementById('logContainer').innerHTML = '';
        this.log('Logs cleared', 'info');
    }
}

// Global functions for HTML onclick handlers
let dashboard;

function connectWallet() {
    dashboard.connectWallet();
}

function startBot() {
    dashboard.startBot();
}

function stopBot() {
    dashboard.stopBot();
}

function updateProfitThreshold() {
    dashboard.updateProfitThreshold();
}

function updateGasPrice() {
    dashboard.updateGasPrice();
}

function updateInterval() {
    dashboard.updateInterval();
}

function resetStats() {
    dashboard.resetStats();
}

function clearLogs() {
    dashboard.clearLogs();
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new ArbitrageDashboard();
});

// Add Web3 library
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/npm/web3@latest/dist/web3.min.js';
document.head.appendChild(script);
