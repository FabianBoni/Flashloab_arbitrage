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
      const priceRatio = Number(outputAmount) / Number(amountIn);
      
      // Dynamic ratio validation - mehr tolerant für DeFi tokens
      let maxRatio = 50000;   // Erhöht für DeFi tokens
      let minRatio = 0.00002;  // Reduziert für sehr kleine tokens
      
      // For stablecoin to stablecoin pairs, expect closer to 1:1
      if (this.isStablecoin(path[0]) && this.isStablecoin(path[1])) {
        maxRatio = 2.0;   // Max 2:1 ratio for stablecoin pairs
        minRatio = 0.5;   // Min 0.5:1 ratio for stablecoin pairs
      }
      // For stablecoin to volatile token (like BUSD to ETH)
      else if (this.isStablecoin(path[0]) || this.isStablecoin(path[1])) {
        maxRatio = 10000;  // Allow higher ratios for stablecoin/volatile pairs
        minRatio = 0.00005; // Lower threshold for stablecoin to expensive tokens like ETH
      }
      
      if (priceRatio > maxRatio || priceRatio < minRatio) {
        console.log(`🚫 Rejecting unrealistic price from ${dexName}: ratio ${priceRatio.toFixed(6)}`);
        console.log(`   Input: ${ethers.formatEther(amountIn)} tokens`);
        console.log(`   Output: ${ethers.formatEther(outputAmount)} tokens`);
        console.log(`   Path: ${path.join(' -> ')}`);
        console.log(`   Token pair type: ${this.isStablecoin(path[0]) ? 'Stablecoin' : 'Volatile'} -> ${this.isStablecoin(path[1]) ? 'Stablecoin' : 'Volatile'}`);
        console.log(`   Expected range: ${minRatio.toFixed(6)} - ${maxRatio}`);
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
   * Check if a token address is a stablecoin
   */
  private isStablecoin(tokenAddress: string): boolean {
    const stablecoins = [
      '0x55d398326f99059fF775485246999027B3197955'.toLowerCase(), // USDT BSC
      '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'.toLowerCase(), // BUSD BSC
      '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d'.toLowerCase(), // USDC BSC
      '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3'.toLowerCase(), // DAI BSC
      '0x250632378E573c6Be1AC2f97Fcdf00515d0Aa91B'.toLowerCase(), // BETH BSC (Beacon ETH, relatively stable)
      '0xdAC17F958D2ee523a2206206994597C13D831ec7'.toLowerCase(), // USDT ETH
      '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c'.toLowerCase(), // USDC ETH
      '0x6B175474E89094C44Da98b954EedeAC495271d0F'.toLowerCase(), // DAI ETH
    ];
    return stablecoins.includes(tokenAddress.toLowerCase());
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

      // VERIFIED LIQUID TOKENS ONLY - mit korrekten Adressen und hoher Liquidität
      const liquidTokens = [
        // BSC Core Assets (höchste Liquidität)
        { address: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', symbol: 'WBNB', chainId: 56 },
        
        // Stablecoins (essentiell für Arbitrage)
        { address: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56', symbol: 'BUSD', chainId: 56 },
        { address: '0x55d398326f99059fF775485246999027B3197955', symbol: 'USDT', chainId: 56 },
        { address: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d', symbol: 'USDC', chainId: 56 },
        { address: '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3', symbol: 'DAI', chainId: 56 },
        
        // Major Crypto Assets (verifiziert auf BSC)
        { address: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8', symbol: 'ETH', chainId: 56 },
        { address: '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c', symbol: 'BTCB', chainId: 56 },
        { address: '0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE', symbol: 'XRP', chainId: 56 },
        { address: '0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47', symbol: 'ADA', chainId: 56 },
        
        // BSC DeFi Tokens (hohe Liquidität bestätigt)
        { address: '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82', symbol: 'CAKE', chainId: 56 }, // PancakeSwap
        { address: '0x603c7f932ED1fc6575303D8Fb018fDCBb0f39a95', symbol: 'BANANA', chainId: 56 }, // ApeSwap (korrekte Adresse)
        { address: '0x965F527D9159dCe6288a2219DB51fc6Eef120dD1', symbol: 'BSW', chainId: 56 },  // Biswap
        { address: '0x4B0F1812e5Df2A09796481Ff14017e6005508003', symbol: 'TWT', chainId: 56 },  // Trust Wallet
        
        // Additional verified tokens
        { address: '0xBf5140A22578168FD562DCcF235E5D43A02ce9B1', symbol: 'UNI', chainId: 56 },  // Uniswap
        { address: '0x85EAC5Ac2F758618dFa09bDbe0cf174e7d574D5B', symbol: 'TRX', chainId: 56 },  // TRON
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
          
          console.log(`🔍 Checking ${token.symbol}/${otherToken.symbol} (${token.address} -> ${otherToken.address})`);
          
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