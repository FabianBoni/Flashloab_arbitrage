import { ethers } from 'ethers';
import { ArbitrageOpportunity, ChainConfig } from './types';

const FLASHLOAN_ARBITRAGE_ABI = [
  'function executeArbitrage(address asset, uint256 amount, string calldata dexA, string calldata dexB, address[] calldata path) external',
  'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)',
  'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
  'function updateMinProfitThreshold(uint256 newThreshold) external',
  'function owner() external view returns (address)',
];

/**
 * MetaMask-compatible arbitrage executor for browser environments
 * This class is designed to work in the browser with MetaMask extension
 */
export class MetaMaskArbitrageExecutor {
  private contracts: Map<number, ethers.Contract> = new Map();
  private provider: ethers.BrowserProvider | null = null;
  private signer: ethers.JsonRpcSigner | null = null;
  private account: string | null = null;
  private currentChainId: number | null = null;

  constructor(
    private chainConfigs: ChainConfig[],
    private contractAddresses: Map<number, string>
  ) {
    // MetaMask provider will be set when user connects
  }

  /**
   * Connect to MetaMask and initialize contracts
   * This method should only be called from browser environment
   */
  async connectMetaMask(account: string, chainId: string): Promise<void> {
    try {
      // This is a browser-only class, so we expect window to exist
      if (typeof window === 'undefined') {
        throw new Error('MetaMask executor requires browser environment');
      }

      const ethereum = (window as any).ethereum;
      if (!ethereum) {
        throw new Error('MetaMask not installed');
      }

      this.account = account;
      this.currentChainId = parseInt(chainId, 16);

      // Create ethers provider from MetaMask
      this.provider = new ethers.BrowserProvider(ethereum);
      this.signer = await this.provider.getSigner();

      // Initialize contract for current chain
      await this.initializeContractForChain(this.currentChainId);

      console.log(`MetaMask connected: ${account} on chain ${this.currentChainId}`);
    } catch (error) {
      console.error('Error connecting to MetaMask:', error);
      throw error;
    }
  }

  /**
   * Initialize contract for a specific chain
   */
  private async initializeContractForChain(chainId: number): Promise<void> {
    if (!this.signer || !this.contractAddresses.has(chainId)) {
      console.warn(`Contract not available for chain ${chainId}`);
      return;
    }

    const contractAddress = this.contractAddresses.get(chainId)!;
    const contract = new ethers.Contract(
      contractAddress,
      FLASHLOAN_ARBITRAGE_ABI,
      this.signer
    );

    this.contracts.set(chainId, contract);
    console.log(`Contract initialized for chain ${chainId}: ${contractAddress}`);
  }

  /**
   * Handle chain/account changes from MetaMask
   */
  async handleMetaMaskChange(account?: string, chainId?: string): Promise<void> {
    if (account) {
      this.account = account;
    }

    if (chainId) {
      const newChainId = parseInt(chainId, 16);
      if (newChainId !== this.currentChainId) {
        this.currentChainId = newChainId;
        await this.initializeContractForChain(newChainId);
      }
    }

    if (this.provider) {
      this.signer = await this.provider.getSigner();
    }
  }

  /**
   * Execute arbitrage opportunity using MetaMask
   */
  async executeArbitrage(opportunity: ArbitrageOpportunity): Promise<{
    success: boolean;
    txHash?: string;
    error?: string;
    profit?: string;
  }> {
    try {
      if (!this.signer || !this.account) {
        throw new Error('MetaMask not connected');
      }

      console.log(`🚀 Executing arbitrage with MetaMask: ${opportunity.dexA} -> ${opportunity.dexB}`);
      console.log(`💰 Expected profit: ${opportunity.profitPercent.toFixed(2)}%`);

      const chainId = this.getChainIdFromOpportunity(opportunity);
      const contract = this.contracts.get(chainId);
      
      if (!contract) {
        throw new Error(`Contract not found for chain ${chainId}`);
      }

      // Verify the opportunity is still profitable
      const isProfitable = await this.verifyProfitability(opportunity, chainId);
      if (!isProfitable) {
        return {
          success: false,
          error: 'Opportunity no longer profitable',
        };
      }

      // Request user confirmation through MetaMask
      console.log('📱 Requesting MetaMask transaction approval...');

      // Execute the transaction
      const tx = await contract.executeArbitrage(
        opportunity.tokenA,
        BigInt(opportunity.amountIn),
        opportunity.dexA,
        opportunity.dexB,
        opportunity.path
      );

      console.log(`📝 Transaction submitted via MetaMask: ${tx.hash}`);
      
      // Wait for confirmation
      const receipt = await tx.wait(2); // Wait for 2 confirmations
      
      if (receipt && receipt.status === 1) {
        console.log(`✅ Arbitrage executed successfully via MetaMask!`);
        
        // Parse logs to get actual profit
        const profit = await this.calculateActualProfit(receipt, opportunity);
        
        return {
          success: true,
          txHash: tx.hash,
          profit: profit.toString(),
        };
      } else {
        return {
          success: false,
          txHash: tx.hash,
          error: 'Transaction failed',
        };
      }
    } catch (error: any) {
      console.error('❌ MetaMask arbitrage execution failed:', error);
      
      // Handle user rejection
      if (error.code === 4001) {
        return {
          success: false,
          error: 'Transaction rejected by user',
        };
      }
      
      return {
        success: false,
        error: error.message || 'Unknown error',
      };
    }
  }

  /**
   * Verify if opportunity is still profitable
   */
  private async verifyProfitability(opportunity: ArbitrageOpportunity, chainId: number): Promise<boolean> {
    try {
      const contract = this.contracts.get(chainId);
      if (!contract) return false;

      const isProfitable = await contract.isArbitrageProfitable(
        BigInt(opportunity.amountIn),
        opportunity.dexA,
        opportunity.dexB,
        opportunity.path
      );

      return isProfitable;
    } catch (error) {
      console.error('Error verifying profitability:', error);
      return false;
    }
  }

  /**
   * Calculate actual profit from transaction receipt
   */
  private async calculateActualProfit(
    receipt: ethers.TransactionReceipt,
    opportunity: ArbitrageOpportunity
  ): Promise<bigint> {
    try {
      const contract = this.contracts.get(this.getChainIdFromOpportunity(opportunity));
      if (!contract) return BigInt(0);

      for (const log of receipt.logs) {
        try {
          const parsed = contract.interface.parseLog({
            topics: log.topics,
            data: log.data,
          });

          if (parsed && parsed.name === 'ArbitrageExecuted') {
            return parsed.args.profit;
          }
        } catch (error) {
          continue;
        }
      }

      return BigInt(0);
    } catch (error) {
      console.error('Error calculating actual profit:', error);
      return BigInt(0);
    }
  }

  /**
   * Get chain ID from opportunity
   */
  private getChainIdFromOpportunity(opportunity: ArbitrageOpportunity): number {
    // Use current chain ID from MetaMask
    return this.currentChainId || 1;
  }

  /**
   * Check if executor is ready for MetaMask operations
   */
  isReady(): boolean {
    return (
      this.signer !== null &&
      this.account !== null &&
      this.currentChainId !== null &&
      this.contracts.has(this.currentChainId)
    );
  }

  /**
   * Get current wallet balance
   */
  async getBalance(): Promise<bigint> {
    try {
      if (!this.provider || !this.account) return BigInt(0);

      return await this.provider.getBalance(this.account);
    } catch (error) {
      console.error('Error getting balance:', error);
      return BigInt(0);
    }
  }

  /**
   * Get estimated profit for an opportunity
   */
  async getEstimatedProfit(opportunity: ArbitrageOpportunity): Promise<bigint> {
    try {
      const chainId = this.getChainIdFromOpportunity(opportunity);
      const contract = this.contracts.get(chainId);
      
      if (!contract) return BigInt(0);

      return await contract.calculateArbitrageProfit(
        BigInt(opportunity.amountIn),
        opportunity.dexA,
        opportunity.dexB,
        opportunity.path
      );
    } catch (error) {
      console.error('Error getting estimated profit:', error);
      return BigInt(0);
    }
  }

  /**
   * Switch to a specific network in MetaMask
   */
  async switchNetwork(chainId: number): Promise<boolean> {
    try {
      if (typeof window === 'undefined') {
        return false;
      }

      const ethereum = (window as any).ethereum;
      if (!ethereum) {
        return false;
      }

      const chainIdHex = `0x${chainId.toString(16)}`;
      
      await ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: chainIdHex }],
      });

      return true;
    } catch (error) {
      console.error('Error switching network:', error);
      return false;
    }
  }

  /**
   * Add a network to MetaMask
   */
  async addNetwork(chainConfig: ChainConfig): Promise<boolean> {
    try {
      if (typeof window === 'undefined') {
        return false;
      }

      const ethereum = (window as any).ethereum;
      if (!ethereum) {
        return false;
      }

      const networkParams = {
        chainId: `0x${chainConfig.chainId.toString(16)}`,
        chainName: chainConfig.name,
        rpcUrls: [chainConfig.rpcUrl],
        blockExplorerUrls: this.getBlockExplorerUrls(chainConfig.chainId),
        nativeCurrency: this.getNativeCurrency(chainConfig.chainId),
      };

      await ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [networkParams],
      });

      return true;
    } catch (error) {
      console.error('Error adding network:', error);
      return false;
    }
  }

  private getBlockExplorerUrls(chainId: number): string[] {
    const explorers: { [key: number]: string[] } = {
      1: ['https://etherscan.io'],
      137: ['https://polygonscan.com'],
      42161: ['https://arbiscan.io'],
      56: ['https://bscscan.com'],
    };
    return explorers[chainId] || [];
  }

  private getNativeCurrency(chainId: number): any {
    const currencies: { [key: number]: any } = {
      1: { name: 'Ethereum', symbol: 'ETH', decimals: 18 },
      137: { name: 'Polygon', symbol: 'MATIC', decimals: 18 },
      42161: { name: 'Ethereum', symbol: 'ETH', decimals: 18 },
      56: { name: 'Binance Coin', symbol: 'BNB', decimals: 18 },
    };
    return currencies[chainId] || { name: 'Ethereum', symbol: 'ETH', decimals: 18 };
  }

  /**
   * Get connected account
   */
  getAccount(): string | null {
    return this.account;
  }

  /**
   * Get current chain ID
   */
  getChainId(): number | null {
    return this.currentChainId;
  }

  /**
   * Disconnect from MetaMask
   */
  disconnect(): void {
    this.provider = null;
    this.signer = null;
    this.account = null;
    this.currentChainId = null;
    this.contracts.clear();
  }
}