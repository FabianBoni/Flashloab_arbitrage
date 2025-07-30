import { ethers } from 'ethers';
import { ArbitrageOpportunity, ChainConfig } from './types';

const PANCAKE_FLASHLOAN_ARBITRAGE_ABI = [
  'function executeArbitrage(address asset, uint256 amount, string calldata dexA, string calldata dexB, address[] calldata path, uint256 minProfit) external',
  'function isArbitrageProfitable(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (bool)',
  'function calculateArbitrageProfit(uint256 amount, string memory dexA, string memory dexB, address[] memory path) external view returns (uint256)',
  'function updateMinProfitThreshold(uint256 newThreshold) external',
  'function setAuthorizedCaller(address caller, bool authorized) external',
  'function owner() external view returns (address)',
  'event ArbitrageExecuted(address indexed asset, uint256 amount, uint256 profit, string dexA, string dexB)',
  'event FlashloanExecuted(address indexed pair, address indexed token, uint256 amount, uint256 fee)'
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
          PANCAKE_FLASHLOAN_ARBITRAGE_ABI,
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
        throw new Error(`⚠️  Contract not deployed for chain ${chainId}. Please deploy the flashloan arbitrage contract to this chain first, or set DEMO_MODE=true to test with mock data.`);
      }

      // CRITICAL: Use contract's own profitability check before execution
      console.log('🔍 VALIDATING OPPORTUNITY WITH CONTRACT...');
      
      try {
        const contractProfit = await contract.calculateArbitrageProfit(
          BigInt(opportunity.amountIn),
          opportunity.dexA,
          opportunity.dexB,
          opportunity.path
        );
        
        const contractProfitEth = ethers.formatEther(contractProfit);
        console.log(`📊 Contract calculated profit: ${contractProfitEth} ETH`);
        console.log(`📊 Bot calculated profit: ${opportunity.profitPercent.toFixed(2)}%`);
        
        if (contractProfit === 0n) {
          console.log('❌ Contract shows 0 profit - opportunity no longer valid');
          return {
            success: false,
            error: 'Contract validation failed: 0 profit calculated',
          };
        }
        
        const isProfitable = await contract.isArbitrageProfitable(
          BigInt(opportunity.amountIn),
          opportunity.dexA,
          opportunity.dexB,
          opportunity.path
        );
        
        if (!isProfitable) {
          console.log('❌ Contract profitability check failed');
          return {
            success: false,
            error: 'Contract profitability check failed',
          };
        }
        
        console.log('✅ CONTRACT VALIDATION PASSED - PROCEEDING WITH EXECUTION');
        
      } catch (validationError) {
        console.log('❌ Contract validation error:', validationError);
        return {
          success: false,
          error: `Contract validation failed: ${validationError}`,
        };
      }

      // Execute real arbitrage with flashloan
      console.log('🚀 EXECUTING REAL ARBITRAGE WITH FLASHLOAN');
      console.log(`📊 Trade details:`);
      console.log(`   Token A: ${opportunity.tokenA}`);
      console.log(`   Token B: ${opportunity.tokenB}`);
      console.log(`   Amount: ${opportunity.amountIn}`);
      console.log(`   Buy from: ${opportunity.dexA}`);
      console.log(`   Sell to: ${opportunity.dexB}`);
      console.log(`   Expected profit: ${opportunity.profitPercent.toFixed(2)}%`);
      
      // Calculate minimum profit - LOWERED for maximum capture rate
      const minProfit = BigInt(opportunity.amountIn) / BigInt(2000); // 0.05% minimum profit
      
      // Execute the arbitrage transaction with OPTIMIZED settings
      const tx = await contract.executeArbitrage(
        opportunity.tokenA,
        BigInt(opportunity.amountIn),
        opportunity.dexA,
        opportunity.dexB,
        opportunity.path,
        minProfit,
        {
          gasLimit: 1500000, // Higher gas limit for complex operations
          maxFeePerGas: ethers.parseUnits('15', 'gwei'), // EIP-1559 max fee
          maxPriorityFeePerGas: ethers.parseUnits('2', 'gwei') // EIP-1559 priority fee
          // Note: Removed gasPrice to avoid conflict with EIP-1559 fields
        }
      );
      
      console.log(`📝 Transaction sent: ${tx.hash}`);
      console.log('⏳ Waiting for confirmation...');
      
      const receipt = await tx.wait();
      
      if (receipt && receipt.status === 1) {
        // Parse the ArbitrageExecuted event to get actual profit
        const actualProfit = await this.calculateActualProfit(receipt, opportunity);
        const profitEth = ethers.formatEther(actualProfit);
        
        console.log(`✅ REAL ARBITRAGE EXECUTED SUCCESSFULLY!`);
        console.log(`📝 Transaction: ${tx.hash}`);
        console.log(`💰 Actual profit: ${profitEth} ETH`);
        
        return {
          success: true,
          txHash: tx.hash,
          profit: profitEth,
        };
      } else {
        throw new Error('Transaction failed');
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
   * Verify if opportunity is still profitable using smart contract
   */
  private async verifyProfitability(opportunity: ArbitrageOpportunity, chainId: number): Promise<boolean> {
    try {
      // AGGRESSIVE MODE: Skip contract pre-validation für schnellere Execution
      console.log(`� AGGRESSIVE EXECUTION MODE: Skipping contract pre-validation für ${opportunity.profitPercent.toFixed(2)}% opportunity`);
      console.log(`   Reason: Direct execution is faster than validation-then-execution`);
      
      // Simple checks that are much faster
      if (opportunity.profitPercent < 0.2) {
        console.log('⚠️  Profit too low even for aggressive mode (<0.2%)');
        return false;
      }
      
      if (opportunity.profitPercent > 50) {
        console.log('⚠️  Profit too high, likely calculation error (>50%)');
        return false;
      }
      
      console.log(`✅ FAST CHECK PASSED: Proceeding with direct execution of ${opportunity.profitPercent.toFixed(2)}% opportunity`);
      return true;
      
    } catch (error) {
      console.error('Error in fast profitability check:', error);
      // Even more aggressive fallback
      return opportunity.profitPercent > 0.3;
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
            topics: log.topics as string[],
            data: log.data,
          });

          if (parsed && parsed.name === 'ArbitrageExecuted') {
            console.log('📊 Arbitrage event found:');
            console.log(`   Asset: ${parsed.args.asset}`);
            console.log(`   Amount: ${ethers.formatEther(parsed.args.amount)} ETH`);
            console.log(`   Profit: ${ethers.formatEther(parsed.args.profit)} ETH`);
            console.log(`   DEX A: ${parsed.args.dexA}`);
            console.log(`   DEX B: ${parsed.args.dexB}`);
            console.log(`   Provider: ${parsed.args.provider}`);
            
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
    // Return the chainId from the opportunity
    return opportunity.chainId;
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

  /**
   * Pre-validate opportunity with contract before reporting it
   */
  async preValidateOpportunity(opportunity: ArbitrageOpportunity): Promise<boolean> {
    try {
      const chainId = opportunity.chainId;
      const contract = this.contracts.get(chainId);
      
      if (!contract) {
        console.log('⚠️  No contract available for pre-validation, skipping');
        return true; // Allow if no contract to validate with
      }

      // Quick contract check
      const isProfitable = await contract.isArbitrageProfitable(
        BigInt(opportunity.amountIn),
        opportunity.dexA.toLowerCase(),
        opportunity.dexB.toLowerCase(),
        opportunity.path
      );

      if (!isProfitable) {
        console.log(`⚠️  Contract pre-validation FAILED for ${opportunity.profitPercent.toFixed(2)}% opportunity`);
        console.log(`   Route: ${opportunity.dexA} -> ${opportunity.dexB}`);
        console.log(`   Reason: Contract says not profitable (likely due to changed market conditions)`);
        return false;
      }

      console.log(`✅ Contract pre-validation PASSED for ${opportunity.profitPercent.toFixed(2)}% opportunity`);
      return true;
    } catch (error: any) {
      console.log(`⚠️  Contract pre-validation error: ${error.message}`);
      return false; // Be conservative - reject if validation fails
    }
  }
}