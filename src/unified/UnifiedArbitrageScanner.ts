import { ethers } from 'ethers';
import { PriceMonitor } from './PriceMonitor';
import { CexPriceProvider, CexPrice } from './CexPriceProvider';
import { ChainConfig, DEXConfig, CexDexArbitrageOpportunity } from './types';
import { RateLimiter } from './RateLimiter';

export interface TokenMapping {
  dexAddress: string;
  cexSymbol: string;
  decimals: number;
  chainId: number;
}

export class UnifiedArbitrageScanner {
  private dexPriceMonitor: PriceMonitor;
  private cexPriceProvider: CexPriceProvider;
  private rateLimiter: RateLimiter;
  private tokenMappings: Map<string, TokenMapping> = new Map();

  constructor(chainConfigs: ChainConfig[], demoMode = false) {
    this.dexPriceMonitor = new PriceMonitor(chainConfigs, demoMode);
    this.cexPriceProvider = new CexPriceProvider();
    this.rateLimiter = RateLimiter.getInstance();
    this.initializeTokenMappings();
  }

  private initializeTokenMappings() {
    // Map DEX token addresses to CEX symbols for major tokens on BSC
    const mappings: Array<{ key: string; mapping: TokenMapping }> = [
      // BSC Core tokens
      {
        key: 'WBNB-BSC',
        mapping: {
          dexAddress: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
          cexSymbol: 'BNB',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'BUSD-BSC',
        mapping: {
          dexAddress: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
          cexSymbol: 'BUSD',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'USDT-BSC',
        mapping: {
          dexAddress: '0x55d398326f99059fF775485246999027B3197955',
          cexSymbol: 'USDT',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'USDC-BSC',
        mapping: {
          dexAddress: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
          cexSymbol: 'USDC',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'ETH-BSC',
        mapping: {
          dexAddress: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
          cexSymbol: 'ETH',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'BTCB-BSC',
        mapping: {
          dexAddress: '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
          cexSymbol: 'BTC',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'CAKE-BSC',
        mapping: {
          dexAddress: '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
          cexSymbol: 'CAKE',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'ADA-BSC',
        mapping: {
          dexAddress: '0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47',
          cexSymbol: 'ADA',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'XRP-BSC',
        mapping: {
          dexAddress: '0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE',
          cexSymbol: 'XRP',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'DOT-BSC',
        mapping: {
          dexAddress: '0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402',
          cexSymbol: 'DOT',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'LINK-BSC',
        mapping: {
          dexAddress: '0xF8A0BF9cF54Bb92F17374d9e9A321E6a111a51bD',
          cexSymbol: 'LINK',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'MATIC-BSC',
        mapping: {
          dexAddress: '0xCC42724C6683B7E57334c4E856f4c9965ED682bD',
          cexSymbol: 'MATIC',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'UNI-BSC',
        mapping: {
          dexAddress: '0xBf5140A22578168FD562DCcF235E5D43A02ce9B1',
          cexSymbol: 'UNI',
          decimals: 18,
          chainId: 56
        }
      },
      {
        key: 'DOGE-BSC',
        mapping: {
          dexAddress: '0xbA2aE424d960c26247Dd6c32edC70B295c744C43',
          cexSymbol: 'DOGE',
          decimals: 8,
          chainId: 56
        }
      }
    ];

    mappings.forEach(({ key, mapping }) => {
      this.tokenMappings.set(key, mapping);
    });

    console.log(`🔗 Initialized ${mappings.length} token mappings for CEX-DEX arbitrage`);
  }

  /**
   * Get token mapping by DEX address
   */
  private getTokenMapping(dexAddress: string, chainId: number): TokenMapping | null {
    for (const [key, mapping] of this.tokenMappings.entries()) {
      if (mapping.dexAddress.toLowerCase() === dexAddress.toLowerCase() && 
          mapping.chainId === chainId) {
        return mapping;
      }
    }
    return null;
  }

  /**
   * Get DEX price for a token pair
   */
  private async getDexPrice(
    chainId: number,
    dexName: string,
    tokenA: string,
    tokenB: string,
    amountIn: bigint
  ): Promise<{ price: number; amountOut: bigint } | null> {
    try {
      const amountOut = await this.dexPriceMonitor.getTokenPrice(
        chainId, dexName, tokenA, tokenB, amountIn
      );

      if (amountOut === BigInt(0)) {
        return null;
      }

      const price = Number(amountOut) / Number(amountIn);
      return { price, amountOut };
    } catch (error) {
      console.error(`Error getting DEX price from ${dexName}:`, error);
      return null;
    }
  }

  /**
   * Find CEX-DEX arbitrage opportunities
   */
  async findCexDexArbitrageOpportunities(
    chainId: number = 56,
    amountIn: bigint = ethers.parseEther('1')
  ): Promise<CexDexArbitrageOpportunity[]> {
    const opportunities: CexDexArbitrageOpportunity[] = [];

    console.log('🔍 Scanning for CEX-DEX arbitrage opportunities...');

    try {
      // Get all available token mappings for this chain
      const chainMappings = Array.from(this.tokenMappings.values())
        .filter(mapping => mapping.chainId === chainId);

      if (chainMappings.length === 0) {
        console.log(`⚠️  No token mappings available for chain ${chainId}`);
        return opportunities;
      }

      // Check arbitrage opportunities for major pairs
      const majorPairs = [
        { base: 'ETH', quote: 'USDT' },
        { base: 'BTC', quote: 'USDT' },
        { base: 'BNB', quote: 'USDT' },
        { base: 'ETH', quote: 'USDC' },
        { base: 'BTC', quote: 'USDC' },
        { base: 'BNB', quote: 'USDC' },
        { base: 'USDT', quote: 'USDC' },
        { base: 'BUSD', quote: 'USDT' },
        { base: 'ADA', quote: 'USDT' },
        { base: 'DOT', quote: 'USDT' }
      ];

      for (const pair of majorPairs) {
        await this.scanPairForCexDexArbitrage(
          pair.base, pair.quote, chainId, amountIn, opportunities
        );
      }

    } catch (error) {
      console.error('Error finding CEX-DEX arbitrage opportunities:', error);
    }

    // Sort opportunities by profit percentage
    opportunities.sort((a, b) => b.profitPercent - a.profitPercent);

    if (opportunities.length > 0) {
      console.log(`💰 Found ${opportunities.length} CEX-DEX arbitrage opportunities`);
      opportunities.slice(0, 5).forEach((opp, i) => {
        console.log(`${i + 1}. ${opp.baseToken}/${opp.quoteToken}: ${opp.profitPercent.toFixed(3)}% profit (${opp.direction}) ${opp.cexExchange} vs ${opp.dexName}`);
      });
    } else {
      console.log('ℹ️  No profitable CEX-DEX opportunities found');
    }

    return opportunities;
  }

  /**
   * Scan a specific trading pair for CEX-DEX arbitrage
   */
  private async scanPairForCexDexArbitrage(
    baseSymbol: string,
    quoteSymbol: string,
    chainId: number,
    amountIn: bigint,
    opportunities: CexDexArbitrageOpportunity[]
  ): Promise<void> {
    try {
      // Find token mappings for base and quote tokens
      const baseMapping = Array.from(this.tokenMappings.values())
        .find(m => m.cexSymbol === baseSymbol && m.chainId === chainId);
      const quoteMapping = Array.from(this.tokenMappings.values())
        .find(m => m.cexSymbol === quoteSymbol && m.chainId === chainId);

      if (!baseMapping || !quoteMapping) {
        console.log(`⚠️  Missing token mappings for ${baseSymbol}/${quoteSymbol} on chain ${chainId}`);
        return;
      }

      console.log(`🔍 Scanning ${baseSymbol}/${quoteSymbol} for CEX-DEX arbitrage...`);

      // Get CEX prices
      const cexPrices = await this.cexPriceProvider.getAllPrices(baseSymbol, quoteSymbol);
      if (cexPrices.length === 0) {
        console.log(`📊 No CEX prices available for ${baseSymbol}/${quoteSymbol}`);
        return;
      }

      // Get DEX prices from major DEXes
      const dexNames = ['PancakeSwap V2', 'Biswap', 'ApeSwap'];
      
      for (const dexName of dexNames) {
        try {
          // Get DEX price for base -> quote
          const dexPriceResult = await this.getDexPrice(
            chainId, dexName, baseMapping.dexAddress, quoteMapping.dexAddress, amountIn
          );

          if (!dexPriceResult) {
            continue;
          }

          const dexPrice = dexPriceResult.price;

          // Compare with all CEX prices
          for (const cexPrice of cexPrices) {
            // Direction 1: Buy on CEX, sell on DEX
            // CEX bid vs DEX price (selling on DEX)
            const cexToDexProfit = ((dexPrice - cexPrice.ask) / cexPrice.ask) * 100;
            
            // Direction 2: Buy on DEX, sell on CEX  
            // DEX price vs CEX bid (selling on CEX)
            const dexToCexProfit = ((cexPrice.bid - dexPrice) / dexPrice) * 100;

            // Account for fees (flashloan, gas, DEX fees, CEX fees)
            const totalFeesPercent = 0.5; // 0.5% total fees estimate
            const minProfitThreshold = 0.3; // Minimum 0.3% profit after fees

            // Check CEX to DEX arbitrage
            if (cexToDexProfit > totalFeesPercent + minProfitThreshold) {
              const netProfit = cexToDexProfit - totalFeesPercent;
              opportunities.push({
                baseToken: baseSymbol,
                quoteToken: quoteSymbol,
                amountIn: amountIn.toString(),
                profitUSD: 0, // Would need USD price calculation
                profitPercent: netProfit,
                cexExchange: cexPrice.exchange,
                dexName: dexName,
                cexPrice: cexPrice.ask,
                dexPrice: dexPrice,
                direction: 'CEX_TO_DEX',
                gasEstimate: '200000',
                timestamp: Date.now(),
                chainId: chainId
              });

              console.log(`✅ CEX→DEX: Buy ${baseSymbol} on ${cexPrice.exchange} at ${cexPrice.ask.toFixed(6)}, sell on ${dexName} at ${dexPrice.toFixed(6)} → ${netProfit.toFixed(3)}% profit`);
            }

            // Check DEX to CEX arbitrage
            if (dexToCexProfit > totalFeesPercent + minProfitThreshold) {
              const netProfit = dexToCexProfit - totalFeesPercent;
              opportunities.push({
                baseToken: baseSymbol,
                quoteToken: quoteSymbol,
                amountIn: amountIn.toString(),
                profitUSD: 0, // Would need USD price calculation
                profitPercent: netProfit,
                cexExchange: cexPrice.exchange,
                dexName: dexName,
                cexPrice: cexPrice.bid,
                dexPrice: dexPrice,
                direction: 'DEX_TO_CEX',
                gasEstimate: '200000',
                timestamp: Date.now(),
                chainId: chainId
              });

              console.log(`✅ DEX→CEX: Buy ${baseSymbol} on ${dexName} at ${dexPrice.toFixed(6)}, sell on ${cexPrice.exchange} at ${cexPrice.bid.toFixed(6)} → ${netProfit.toFixed(3)}% profit`);
            }
          }
        } catch (error) {
          console.error(`Error scanning ${dexName} for ${baseSymbol}/${quoteSymbol}:`, error);
        }
      }
    } catch (error) {
      console.error(`Error scanning pair ${baseSymbol}/${quoteSymbol}:`, error);
    }
  }

  /**
   * Start continuous monitoring for both CEX-DEX and DEX-DEX arbitrage
   */
  async startUnifiedMonitoring(
    callback: (cexDexOpportunities: CexDexArbitrageOpportunity[], dexOpportunities: any[]) => void,
    interval: number = 30000 // 30 seconds
  ): Promise<void> {
    console.log('🚀 Starting unified CEX-DEX-DEX arbitrage monitoring...');

    const monitor = async () => {
      try {
        const startTime = Date.now();

        // Scan for CEX-DEX opportunities
        const cexDexOpportunities = await this.findCexDexArbitrageOpportunities();

        // Scan for traditional DEX-DEX opportunities for major tokens
        const dexOpportunities: any[] = []; // Would be populated by DEX scanner

        const scanTime = Date.now() - startTime;
        console.log(`📊 Scan completed in ${scanTime}ms: ${cexDexOpportunities.length} CEX-DEX + ${dexOpportunities.length} DEX-DEX opportunities`);

        if (cexDexOpportunities.length > 0 || dexOpportunities.length > 0) {
          callback(cexDexOpportunities, dexOpportunities);
        }

      } catch (error) {
        console.error('Error in unified monitoring:', error);
      }
    };

    // Run initial scan
    await monitor();

    // Set up interval monitoring
    setInterval(monitor, interval);
    console.log(`⏰ Monitoring every ${interval / 1000} seconds`);
  }

  /**
   * Get supported CEX-DEX trading pairs
   */
  getSupportedCexDexPairs(): Array<{ base: string; quote: string; chainId: number }> {
    const pairs: Array<{ base: string; quote: string; chainId: number }> = [];
    const chainMappings = Array.from(this.tokenMappings.values());

    // Generate pairs from available token mappings
    for (let i = 0; i < chainMappings.length; i++) {
      for (let j = i + 1; j < chainMappings.length; j++) {
        const tokenA = chainMappings[i];
        const tokenB = chainMappings[j];

        if (tokenA.chainId === tokenB.chainId) {
          pairs.push({
            base: tokenA.cexSymbol,
            quote: tokenB.cexSymbol,
            chainId: tokenA.chainId
          });
        }
      }
    }

    return pairs.slice(0, 20); // Return top 20 pairs
  }
}