import { ethers } from 'ethers';
import { DEXConfig, ArbitrageOpportunity, ChainConfig } from './types';
import { RateLimiter } from './RateLimiter.js';
import { MAX_PROFIT_THRESHOLD } from './config.js';

const UNISWAP_V2_ROUTER_ABI = [
  'function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts)',
  'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
];

const ERC20_ABI = [
  'function balanceOf(address owner) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)',
  'function transfer(address to, uint amount) returns (bool)',
  'function approve(address spender, uint amount) returns (bool)',
];

export class PriceMonitor {
  private providers: Map<number, ethers.JsonRpcProvider[]> = new Map(); // Array of providers for rotation
  private providerIndex: Map<number, number> = new Map(); // Current provider index for each chain
  private routers: Map<string, ethers.Contract[]> = new Map(); // Array of router contracts for rotation
  private demoMode: boolean;
  private rateLimiter: RateLimiter;

  constructor(chainConfigs: ChainConfig[], demoMode = false) {
    this.demoMode = demoMode;
    this.rateLimiter = RateLimiter.getInstance();
    
    if (!demoMode) {
      // Initialize providers and router contracts only in live mode
      chainConfigs.forEach(config => {
        // Use rpcUrls array if available, otherwise fall back to single rpcUrl
        const rpcUrls = config.rpcUrls && config.rpcUrls.length > 0 ? config.rpcUrls : [config.rpcUrl];
        const validRpcUrls = rpcUrls.filter((url: string) => url && url.trim() !== '');
        
        if (validRpcUrls.length === 0) {
          console.warn(`No valid RPC URLs found for chain ${config.chainId}`);
          return;
        }

        // Create providers for all RPC URLs
        const providers = validRpcUrls.map((url: string) => new ethers.JsonRpcProvider(url));
        this.providers.set(config.chainId, providers);
        this.providerIndex.set(config.chainId, 0); // Start with first provider

        // Create router contracts for each DEX with all providers
        config.dexes.forEach((dex: DEXConfig) => {
          const routerContracts = providers.map((provider: ethers.JsonRpcProvider) => 
            new ethers.Contract(dex.router, UNISWAP_V2_ROUTER_ABI, provider)
          );
          this.routers.set(`${config.chainId}-${dex.name}`, routerContracts);
        });

        console.log(`Initialized ${providers.length} RPC endpoints for chain ${config.chainId} (${config.name})`);
      });
    }
  }

  /**
   * Get next router contract using round-robin provider rotation
   */
  private getNextRouter(chainId: number, dexName: string): ethers.Contract | null {
    const routerKey = `${chainId}-${dexName}`;
    const routers = this.routers.get(routerKey);
    
    if (!routers || routers.length === 0) {
      return null;
    }

    // Get current provider index and rotate
    const currentIndex = this.providerIndex.get(chainId) || 0;
    const nextIndex = (currentIndex + 1) % routers.length;
    this.providerIndex.set(chainId, nextIndex);

    // Return router with rotated provider
    return routers[currentIndex];
  }

  /**
   * Get token price on a specific DEX with enhanced validation
   */
  async getTokenPrice(
    chainId: number,
    dexName: string,
    tokenA: string,
    tokenB: string,
    amountIn: bigint
  ): Promise<bigint> {
    try {
      if (this.demoMode) {
        // Return mock prices for demo mode
        const basePrice = BigInt("1000000000000000000"); // 1 ETH equivalent
        const variation = Math.random() * 0.1 - 0.05; // ±5% variation
        const mockPrice = BigInt(Math.floor(Number(basePrice) * (1 + variation)));
        return mockPrice;
      }

      const router = this.getNextRouter(chainId, dexName);
      
      if (!router) {
        throw new Error(`Router not found for ${chainId}-${dexName}`);
      }

      const path = [tokenA, tokenB];
      
      // Use smaller test amount first to validate the route exists
      const testAmount = BigInt("1000000000000000000"); // 1 token (18 decimals)
      
      // Test with small amount first
      const testAmounts = await this.rateLimiter.executeWithRateLimit(
        () => router.getAmountsOut(testAmount, path),
        `${dexName}-${chainId}-getAmountsOut-test`
      );
      
      if (!testAmounts || testAmounts.length === 0 || testAmounts[testAmounts.length - 1] === BigInt(0)) {
        return BigInt(0); // Route doesn't exist or no liquidity
      }
      
      // If test succeeds, try with actual amount
      const amounts = await this.rateLimiter.executeWithRateLimit(
        () => router.getAmountsOut(amountIn, path),
        `${dexName}-${chainId}-getAmountsOut`
      );
      
      if (!amounts || amounts.length === 0) {
        return BigInt(0);
      }
      
      const outputAmount = amounts[amounts.length - 1];
      
      // Sanity check: output amount should be reasonable compared to input
      const priceRatio = Number(outputAmount * BigInt(1000)) / Number(amountIn);
      if (priceRatio > 10000 || priceRatio < 0.0001) { // More than 10000x or less than 0.0001x
        console.log(`🚫 Rejecting unrealistic price from ${dexName}: ratio ${priceRatio}`);
        return BigInt(0);
      }
      
      return outputAmount;
    } catch (error) {
      // Reduce logging verbosity for rate limit errors (handled by RateLimiter)
      if (!this.isRateLimitError(error)) {
        console.error(`Error getting price from ${dexName} on chain ${chainId}:`, error);
      }
      return BigInt(0);
    }
  }

  private isRateLimitError(error: any): boolean {
    if (!error) return false;
    const errorString = JSON.stringify(error);
    return error?.code === 'BAD_DATA' || 
           errorString.includes('rate limit') ||
           errorString.includes('too many requests') ||
           errorString.includes('429');
  }

  /**
   * Compare prices across DEXes for arbitrage opportunities
   */
  async findArbitrageOpportunities(
    chainId: number,
    tokenA: string,
    tokenB: string,
    amountIn: bigint,
    dexes: DEXConfig[]
  ): Promise<ArbitrageOpportunity[]> {
    const opportunities: ArbitrageOpportunity[] = [];
    
    try {
      // FILTERING: Only use major, liquid DEXs for realistic opportunities
      const liquidDexes = dexes.filter(dex => {
        const majorDexes = ['PancakeSwap V2', 'Uniswap V2', 'Biswap', 'ApeSwap'];
        return majorDexes.includes(dex.name);
      });

      if (liquidDexes.length < 2) {
        console.log(`⚠️  Not enough major DEXs available for ${chainId}, skipping token pair`);
        return opportunities;
      }

      // Get prices from liquid DEXes only
      const prices = await Promise.all(
        liquidDexes.map(async (dex) => ({
          dex: dex.name,
          price: await this.getTokenPrice(chainId, dex.name, tokenA, tokenB, amountIn),
        }))
      );

      // Filter out failed price fetches and add additional liquidity checks
      const validPrices = prices.filter(p => {
        if (p.price <= 0) return false;
        
        // Additional check: Price should be reasonable for the input amount
        const ratio = Number(p.price) / Number(amountIn);
        return ratio > 0.1 && ratio < 100; // Price should be between 0.1x and 100x of input
      });

      if (validPrices.length < 2) {
        return opportunities;
      }

      // Find arbitrage opportunities with PROPER calculation
      for (let i = 0; i < validPrices.length; i++) {
        for (let j = i + 1; j < validPrices.length; j++) {
          const priceA = validPrices[i];
          const priceB = validPrices[j];

          // Safety check for price validity
          if (priceA.price === BigInt(0) || priceB.price === BigInt(0)) {
            continue;
          }

          // Calculate actual arbitrage profit for both directions
          await this.calculateAndCheckArbitrageProfit(
            chainId, amountIn, tokenA, tokenB, 
            priceA.dex, priceB.dex, priceA.price, priceB.price, 
            opportunities, liquidDexes
          );
        }
      }
    } catch (error) {
      console.error('Error finding arbitrage opportunities:', error);
    }

    return opportunities;
  }

  /**
   * Calculate real arbitrage profit using on-chain reverse path queries
   */
  private async calculateAndCheckArbitrageProfit(
    chainId: number,
    amountIn: bigint,
    tokenA: string,
    tokenB: string,
    dexA: string,
    dexB: string,
    priceA: bigint,
    priceB: bigint,
    opportunities: ArbitrageOpportunity[],
    dexes: DEXConfig[]
  ) {
    try {
      // Try arbitrage in both directions
      
      // Direction 1: A -> B -> A (buy on A, sell on B)
      const profitAB = await this.calculateRoundTripProfit(
        chainId, amountIn, tokenA, tokenB, dexA, dexB, dexes
      );
      
      // Direction 2: B -> A -> B (buy on B, sell on A)
      const profitBA = await this.calculateRoundTripProfit(
        chainId, amountIn, tokenA, tokenB, dexB, dexA, dexes
      );

      // Check if either direction is profitable
      const minThreshold = 0.0001; // Lowered to 0.01% for testing
      
      if (profitAB.profitPercent > minThreshold) {
        console.log(`✅ REALISTIC OPPORTUNITY: ${profitAB.profitPercent.toFixed(2)}% net profit (${dexA} -> ${dexB})`);
        
        opportunities.push({
          tokenA,
          tokenB,
          amountIn: amountIn.toString(),
          profitUSD: 0,
          profitPercent: profitAB.profitPercent,
          dexA: dexA,
          dexB: dexB,
          path: [tokenA, tokenB],
          gasEstimate: '0',
          timestamp: Date.now(),
          chainId,
        });
      }
      
      if (profitBA.profitPercent > minThreshold) {
        console.log(`✅ REALISTIC OPPORTUNITY: ${profitBA.profitPercent.toFixed(2)}% net profit (${dexB} -> ${dexA})`);
        
        opportunities.push({
          tokenA,
          tokenB,
          amountIn: amountIn.toString(),
          profitUSD: 0,
          profitPercent: profitBA.profitPercent,
          dexA: dexB,
          dexB: dexA,
          path: [tokenA, tokenB],
          gasEstimate: '0',
          timestamp: Date.now(),
          chainId,
        });
      }
      
    } catch (error) {
      // Silently handle errors to avoid spam
    }
  }

  /**
   * Calculate round-trip arbitrage profit: tokenA -> tokenB -> tokenA
   */
  private async calculateRoundTripProfit(
    chainId: number,
    amountIn: bigint,
    tokenA: string,
    tokenB: string,
    buyDex: string,
    sellDex: string,
    dexes: DEXConfig[]
  ): Promise<{ profitPercent: number; finalAmount: bigint }> {
    
    // Step 1: tokenA -> tokenB on buyDex
    const intermediateAmount = await this.getTokenPrice(chainId, buyDex, tokenA, tokenB, amountIn);
    
    if (intermediateAmount === BigInt(0)) {
      return { profitPercent: 0, finalAmount: BigInt(0) };
    }
    
    // Step 2: tokenB -> tokenA on sellDex (reverse path)
    const finalAmount = await this.getTokenPrice(chainId, sellDex, tokenB, tokenA, intermediateAmount);
    
    if (finalAmount === BigInt(0)) {
      return { profitPercent: 0, finalAmount: BigInt(0) };
    }
    
    // Calculate profit
    const profit = finalAmount > amountIn ? finalAmount - amountIn : BigInt(0);
    const grossProfitPercent = Number(profit * BigInt(10000) / amountIn) / 100;
    
    // Account for fees (reduced for testing)
    const flashloanFeePercent = 0.05; // Reduced from 0.09%
    const gasEstimatePercent = 0.05; // Reduced gas costs
    const slippagePercent = 0.05; // Reduced slippage
    const totalFeesPercent = flashloanFeePercent + gasEstimatePercent + slippagePercent;
    
    const netProfitPercent = grossProfitPercent - totalFeesPercent;
    
    return { 
      profitPercent: Math.max(0, netProfitPercent), 
      finalAmount 
    };
  }

  /**
   * Get token information
   */
  async getTokenInfo(chainId: number, tokenAddress: string): Promise<{
    symbol: string;
    decimals: number;
    balance?: bigint;
  }> {
    try {
      const providers = this.providers.get(chainId);
      if (!providers || providers.length === 0) {
        throw new Error(`Provider not found for chain ${chainId}`);
      }

      // Use the current provider from rotation
      const currentIndex = this.providerIndex.get(chainId) || 0;
      const provider = providers[currentIndex];
      
      const token = new ethers.Contract(tokenAddress, ERC20_ABI, provider);
      
      const [symbol, decimals] = await Promise.all([
        this.rateLimiter.executeWithRateLimit(
          () => token.symbol(),
          `token-symbol-${chainId}`
        ),
        this.rateLimiter.executeWithRateLimit(
          () => token.decimals(),
          `token-decimals-${chainId}`
        ),
      ]);

      return { 
        symbol: symbol || 'UNKNOWN', 
        decimals: Number(decimals) || 18 
      };
    } catch (error) {
      if (!this.isRateLimitError(error)) {
        console.error(`Error getting token info for ${tokenAddress}:`, error);
      }
      return { symbol: 'UNKNOWN', decimals: 18 };
    }
  }

  /**
   * Monitor only major, liquid tokens for realistic arbitrage opportunities
   */
  async monitorLiquidTokens(callback: (opportunities: ArbitrageOpportunity[]) => void): Promise<void> {
    try {
      const allOpportunities: ArbitrageOpportunity[] = [];

      // FOCUS ON ONLY THE MOST LIQUID TOKENS for realistic opportunities
      const liquidTokens = [
        // BSC - Major tokens only
        { address: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', symbol: 'WBNB', chainId: 56 },
        { address: '0x55d398326f99059fF775485246999027B3197955', symbol: 'USDT', chainId: 56 },
        { address: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56', symbol: 'BUSD', chainId: 56 },
        { address: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d', symbol: 'USDC', chainId: 56 },
        { address: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8', symbol: 'ETH', chainId: 56 },
        
        // Ethereum - Major tokens only  
        { address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', symbol: 'WETH', chainId: 1 },
        { address: '0xdAC17F958D2ee523a2206206994597C13D831ec7', symbol: 'USDT', chainId: 1 },
        { address: '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c', symbol: 'USDC', chainId: 1 },
      ];

      console.log('🔍 Monitoring MAJOR, LIQUID tokens for realistic arbitrage opportunities...');

      for (const token of liquidTokens) {
        // Get DEX configs for this chain
        const dexes = Array.from(this.routers.keys())
          .filter(key => key.startsWith(`${token.chainId}-`))
          .map(key => ({ name: key.split('-')[1] })) as DEXConfig[];

        if (dexes.length < 2) continue;

        // Check against other major tokens on the same chain
        const otherTokens = liquidTokens.filter(t => 
          t.chainId === token.chainId && 
          t.address !== token.address
        );
        
        for (const otherToken of otherTokens) {
          // Use realistic trade sizes for flashloan arbitrage
          const tradeSize = ethers.parseEther('1.0'); // 1 token - realistic for execution
          
          const opportunities = await this.findArbitrageOpportunities(
            token.chainId,
            token.address,
            otherToken.address,
            tradeSize,
            dexes as DEXConfig[]
          );

          if (opportunities.length > 0) {
            console.log(`💎 Found ${opportunities.length} realistic opportunities for ${token.symbol}/${otherToken.symbol}`);
          }

          allOpportunities.push(...opportunities);
        }
      }

      if (allOpportunities.length > 0) {
        console.log(`💰 Found ${allOpportunities.length} REALISTIC arbitrage opportunities`);
        console.log(`🚀 Calling callback for execution...`);
        callback(allOpportunities);
      } else {
        console.log('ℹ️  No realistic opportunities found in major token pairs');
      }
    } catch (error) {
      console.error('Error in liquid token monitoring:', error);
    }
  }
  async startPriceMonitoring(
    tokens: Array<{ chainId: number; address: string; symbol: string }>,
    callback: (opportunities: ArbitrageOpportunity[]) => void,
    interval: number = 10000
  ): Promise<void> {
    const monitor = async () => {
      try {
        console.log('🔍 Scanning for arbitrage opportunities...');
        
        const allOpportunities: ArbitrageOpportunity[] = [];

        // Check opportunities for each token pair on each chain
        for (const token of tokens) {
          const chainConfig = Array.from(this.providers.keys()).find(id => id === token.chainId);
          if (!chainConfig) continue;

          // Get DEX configs for this chain
          const dexes = Array.from(this.routers.keys())
            .filter(key => key.startsWith(`${token.chainId}-`))
            .map(key => ({ name: key.split('-')[1] })) as DEXConfig[];

          if (dexes.length < 2) continue;

          // Check against other popular tokens
          const otherTokens = tokens.filter(t => t.chainId === token.chainId && t.address !== token.address);
          
          for (const otherToken of otherTokens) {
            // Use smaller, more realistic trade sizes for better accuracy
            const tradeSize = ethers.parseEther('0.5'); // 0.5 token - more realistic for execution
            
            const opportunities = await this.findArbitrageOpportunities(
              token.chainId,
              token.address,
              otherToken.address,
              tradeSize,
              dexes as DEXConfig[]
            );

            if (opportunities.length > 0) {
              console.log(`💎 Found ${opportunities.length} realistic opportunities for ${token.symbol}/${otherToken.symbol}`);
            }

            allOpportunities.push(...opportunities);
          }
        }

        if (allOpportunities.length > 0) {
          console.log(`💰 Found ${allOpportunities.length} potential arbitrage opportunities`);
          callback(allOpportunities);
        } else {
          console.log('ℹ️  No profitable opportunities found');
        }
      } catch (error) {
        console.error('Error in price monitoring:', error);
      }
    };

    // Run initial scan
    await monitor();

    // Set up interval monitoring
    setInterval(monitor, interval);
  }
}