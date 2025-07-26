import { ethers } from 'ethers';
import { ArbitrageOpportunity, ChainConfig } from './types';

const FLASHLOAN_ARBITRAGE_ABI = [
  'function executeArbitrage(address asset, uint256 amount, string calldata dexA, string calldata dexB, address[] calldata path) external',
  'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)',
  'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
  'function updateMinProfitThreshold(uint256 newThreshold) external',
  'function owner() external view returns (address)',
];

export class ArbitrageExecutor {
  private contracts: Map<number, ethers.Contract> = new Map();
  private wallets: Map<number, ethers.Wallet> = new Map();

  constructor(
    private chainConfigs: ChainConfig[],
    private privateKey: string,
    private contractAddresses: Map<number, string>
  ) {
    this.initializeContracts();
  }

  private initializeContracts() {
    this.chainConfigs.forEach(config => {
      if (config.rpcUrl && this.contractAddresses.has(config.chainId)) {
        const provider = new ethers.JsonRpcProvider(config.rpcUrl);
        const wallet = new ethers.Wallet(this.privateKey, provider);
        const contractAddress = this.contractAddresses.get(config.chainId)!;
        
        const contract = new ethers.Contract(
          contractAddress,
          FLASHLOAN_ARBITRAGE_ABI,
          wallet
        );

        this.contracts.set(config.chainId, contract);
        this.wallets.set(config.chainId, wallet);
      }
    });
  }

  /**
   * Execute arbitrage opportunity
   */
  async executeArbitrage(opportunity: ArbitrageOpportunity): Promise<{
    success: boolean;
    txHash?: string;
    error?: string;
    profit?: string;
  }> {
    try {
      console.log(`🚀 Executing arbitrage: ${opportunity.dexA} -> ${opportunity.dexB}`);
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

      // Estimate gas
      const gasEstimate = await this.estimateGas(opportunity, chainId);
      console.log(`⛽ Estimated gas: ${gasEstimate.toString()}`);

      // Execute the transaction
      const tx = await contract.executeArbitrage(
        opportunity.tokenA,
        BigInt(opportunity.amountIn),
        opportunity.dexA,
        opportunity.dexB,
        opportunity.path,
        {
          gasLimit: gasEstimate,
          maxFeePerGas: ethers.parseUnits('50', 'gwei'), // Max 50 gwei
          maxPriorityFeePerGas: ethers.parseUnits('2', 'gwei'),
        }
      );

      console.log(`📝 Transaction submitted: ${tx.hash}`);
      
      // Wait for confirmation
      const receipt = await tx.wait(2); // Wait for 2 confirmations
      
      if (receipt.status === 1) {
        console.log(`✅ Arbitrage executed successfully!`);
        
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
      console.error('❌ Arbitrage execution failed:', error);
      
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
   * Estimate gas for the transaction
   */
  private async estimateGas(opportunity: ArbitrageOpportunity, chainId: number): Promise<bigint> {
    try {
      const contract = this.contracts.get(chainId);
      if (!contract) throw new Error('Contract not found');

      const gasEstimate = await contract.executeArbitrage.estimateGas(
        opportunity.tokenA,
        BigInt(opportunity.amountIn),
        opportunity.dexA,
        opportunity.dexB,
        opportunity.path
      );

      // Add 20% buffer
      return gasEstimate * BigInt(120) / BigInt(100);
    } catch (error) {
      console.error('Error estimating gas:', error);
      // Return a reasonable default
      return BigInt(500000);
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
      // Parse the ArbitrageExecuted event
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
          // Log parsing failed, continue to next log
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
   * Get chain ID from opportunity (simplified - in reality would need more context)
   */
  private getChainIdFromOpportunity(opportunity: ArbitrageOpportunity): number {
    // For now, assume Ethereum mainnet. In a real implementation,
    // this would be determined from the DEX addresses or other context
    return 1;
  }

  /**
   * Check if executor is ready for a specific chain
   */
  isReady(chainId: number): boolean {
    return this.contracts.has(chainId) && this.wallets.has(chainId);
  }

  /**
   * Get wallet balance for a specific chain
   */
  async getBalance(chainId: number): Promise<bigint> {
    try {
      const wallet = this.wallets.get(chainId);
      if (!wallet) return BigInt(0);

      return await wallet.provider!.getBalance(wallet.address);
    } catch (error) {
      console.error(`Error getting balance for chain ${chainId}:`, error);
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
}