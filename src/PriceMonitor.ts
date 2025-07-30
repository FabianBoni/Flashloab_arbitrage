import { ethers } from 'ethers';
import { DEXConfig, ArbitrageOpportunity, ChainConfig } from './types';
import { RateLimiter } from './RateLimiter.js';

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
   * Get token price on a specific DEX
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
      
      // Use rate limiter for the RPC call with enhanced context
      const amounts = await this.rateLimiter.executeWithRateLimit(
        () => router.getAmountsOut(amountIn, path),
        `${dexName}-${chainId}-getAmountsOut`
      );
      
      if (!amounts) {
        return BigInt(0);
      }
      
      return amounts[amounts.length - 1];
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
      // Get prices from all DEXes
      const prices = await Promise.all(
        dexes.map(async (dex) => ({
          dex: dex.name,
          price: await this.getTokenPrice(chainId, dex.name, tokenA, tokenB, amountIn),
        }))
      );

      // Filter out failed price fetches
      const validPrices = prices.filter(p => p.price > 0);

      if (validPrices.length < 2) {
        return opportunities;
      }

      // Find arbitrage opportunities
      for (let i = 0; i < validPrices.length; i++) {
        for (let j = i + 1; j < validPrices.length; j++) {
          const priceA = validPrices[i];
          const priceB = validPrices[j];

          let buyDex, sellDex, buyPrice, sellPrice;

          if (priceA.price < priceB.price) {
            buyDex = priceA.dex;
            sellDex = priceB.dex;
            buyPrice = priceA.price;
            sellPrice = priceB.price;
          } else {
            buyDex = priceB.dex;
            sellDex = priceA.dex;
            buyPrice = priceB.price;
            sellPrice = priceA.price;
          }

          // Calculate potential profit
          const profit = sellPrice - buyPrice;
          const profitPercent = Number(profit * BigInt(10000) / buyPrice) / 100; // Convert to percentage

          // Calculate flashloan fee (0.25% for PancakeSwap flashloans)
          const flashloanFeePercent = 0.25;
          const netProfitPercent = profitPercent - flashloanFeePercent;

          // ULTRA AGGRESSIVE: Accept smaller profits for maximum capture rate
          // Require minimum 0.2% NET profit after all fees
          if (netProfitPercent > 0.2) { 
            opportunities.push({
              tokenA,
              tokenB,
              amountIn: amountIn.toString(),
              profitUSD: 0, // Will be calculated based on USD prices
              profitPercent: netProfitPercent, // Use NET profit percentage
              dexA: buyDex,
              dexB: sellDex,
              path: [tokenA, tokenB],
              gasEstimate: '0', // Will be estimated
              timestamp: Date.now(),
              chainId, // Add the chainId from the function parameter
            });
          }
        }
      }
    } catch (error) {
      console.error('Error finding arbitrage opportunities:', error);
    }

    return opportunities;
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
   * Monitor prices continuously
   */
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
            const opportunities = await this.findArbitrageOpportunities(
              token.chainId,
              token.address,
              otherToken.address,
              ethers.parseEther('1'), // 1 token
              dexes as DEXConfig[]
            );

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