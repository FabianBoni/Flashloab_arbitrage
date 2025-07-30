import { ethers } from 'ethers';
import { DEXConfig, ArbitrageOpportunity } from './types';
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
  private providers: Map<number, ethers.JsonRpcProvider> = new Map();
  private routers: Map<string, ethers.Contract> = new Map();
  private demoMode: boolean;
  private rateLimiter: RateLimiter;

  constructor(chainConfigs: Array<{ chainId: number; rpcUrl: string; dexes: DEXConfig[] }>, demoMode = false) {
    this.demoMode = demoMode;
    this.rateLimiter = RateLimiter.getInstance();
    
    if (!demoMode) {
      // Initialize providers and router contracts only in live mode
      chainConfigs.forEach(config => {
        if (config.rpcUrl) {
          const provider = new ethers.JsonRpcProvider(config.rpcUrl);
          this.providers.set(config.chainId, provider);

          config.dexes.forEach(dex => {
            const router = new ethers.Contract(dex.router, UNISWAP_V2_ROUTER_ABI, provider);
            this.routers.set(`${config.chainId}-${dex.name}`, router);
          });
        }
      });
    }
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

      const routerKey = `${chainId}-${dexName}`;
      const router = this.routers.get(routerKey);
      
      if (!router) {
        throw new Error(`Router not found for ${routerKey}`);
      }

      const path = [tokenA, tokenB];
      
      // Use rate limiter for the RPC call
      const amounts = await this.rateLimiter.executeWithRateLimit(
        () => router.getAmountsOut(amountIn, path),
        `${dexName}-${chainId}-getAmountsOut`
      );
      
      if (!amounts) {
        return BigInt(0);
      }
      
      return amounts[amounts.length - 1];
    } catch (error) {
      console.error(`Error getting price from ${dexName} on chain ${chainId}:`, error);
      return BigInt(0);
    }
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
      const provider = this.providers.get(chainId);
      if (!provider) {
        throw new Error(`Provider not found for chain ${chainId}`);
      }

      const token = new ethers.Contract(tokenAddress, ERC20_ABI, provider);
      
      const [symbol, decimals] = await Promise.all([
        token.symbol(),
        token.decimals(),
      ]);

      return { symbol, decimals: Number(decimals) };
    } catch (error) {
      console.error(`Error getting token info for ${tokenAddress}:`, error);
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