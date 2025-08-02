import axios, { AxiosResponse } from 'axios';
import { RateLimiter } from './RateLimiter';

export interface CexPrice {
  exchange: string;
  symbol: string;
  price: number;
  volume: number;
  timestamp: number;
  bid: number;
  ask: number;
}

export interface CexConfig {
  name: string;
  apiBaseUrl: string;
  apiKey?: string;
  apiSecret?: string;
  rateLimit: number; // requests per second
  symbolFormat: (base: string, quote: string) => string;
}

export class CexPriceProvider {
  private rateLimiter: RateLimiter;
  private cexConfigs: Map<string, CexConfig> = new Map();

  constructor() {
    this.rateLimiter = RateLimiter.getInstance();
    this.initializeCexConfigs();
  }

  private initializeCexConfigs() {
    // Top 8 CEX exchanges for arbitrage opportunities
    const configs: CexConfig[] = [
      {
        name: 'Binance',
        apiBaseUrl: 'https://api.binance.com/api/v3',
        rateLimit: 10, // 10 requests per second (conservative)
        symbolFormat: (base, quote) => `${base}${quote}`.toUpperCase()
      },
      {
        name: 'Bybit',
        apiBaseUrl: 'https://api.bybit.com/v5',
        rateLimit: 10,
        symbolFormat: (base, quote) => `${base}${quote}`.toUpperCase()
      },
      {
        name: 'OKX',
        apiBaseUrl: 'https://www.okx.com/api/v5',
        rateLimit: 20,
        symbolFormat: (base, quote) => `${base}-${quote}`.toUpperCase()
      },
      {
        name: 'KuCoin',
        apiBaseUrl: 'https://api.kucoin.com/api/v1',
        rateLimit: 10,
        symbolFormat: (base, quote) => `${base}-${quote}`.toUpperCase()
      },
      {
        name: 'Gate.io',
        apiBaseUrl: 'https://api.gateio.ws/api/v4',
        rateLimit: 10,
        symbolFormat: (base, quote) => `${base}_${quote}`.toUpperCase()
      },
      {
        name: 'Bitget',
        apiBaseUrl: 'https://api.bitget.com/api/v2',
        rateLimit: 10,
        symbolFormat: (base, quote) => `${base}${quote}`.toUpperCase()
      },
      {
        name: 'MEXC',
        apiBaseUrl: 'https://api.mexc.com/api/v3',
        rateLimit: 10,
        symbolFormat: (base, quote) => `${base}${quote}`.toUpperCase()
      },
      {
        name: 'HTX',
        apiBaseUrl: 'https://api.huobi.pro/v1',
        rateLimit: 10,
        symbolFormat: (base, quote) => `${base}${quote}`.toLowerCase()
      }
    ];

    configs.forEach(config => {
      this.cexConfigs.set(config.name, config);
    });

    console.log(`📈 Initialized ${configs.length} CEX price providers`);
  }

  /**
   * Get price from Binance
   */
  private async getBinancePrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('Binance')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/ticker/bookTicker?symbol=${symbol}`, {
          timeout: 5000
        }),
        `binance-${symbol}`
      );

      const data = response.data;
      return {
        exchange: 'Binance',
        symbol,
        price: parseFloat(data.bidPrice + data.askPrice) / 2, // mid price
        volume: 0, // would need separate call for volume
        timestamp: Date.now(),
        bid: parseFloat(data.bidPrice),
        ask: parseFloat(data.askPrice)
      };
    } catch (error) {
      console.error(`Error fetching Binance price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get price from Bybit
   */
  private async getBybitPrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('Bybit')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/market/tickers?category=spot&symbol=${symbol}`, {
          timeout: 5000
        }),
        `bybit-${symbol}`
      );

      const data = response.data.result?.list?.[0];
      if (!data) return null;

      return {
        exchange: 'Bybit',
        symbol,
        price: parseFloat(data.lastPrice),
        volume: parseFloat(data.volume24h),
        timestamp: Date.now(),
        bid: parseFloat(data.bid1Price),
        ask: parseFloat(data.ask1Price)
      };
    } catch (error) {
      console.error(`Error fetching Bybit price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get price from OKX
   */
  private async getOKXPrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('OKX')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/market/ticker?instId=${symbol}`, {
          timeout: 5000
        }),
        `okx-${symbol}`
      );

      const data = response.data.data?.[0];
      if (!data) return null;

      return {
        exchange: 'OKX',
        symbol,
        price: parseFloat(data.last),
        volume: parseFloat(data.vol24h),
        timestamp: Date.now(),
        bid: parseFloat(data.bidPx),
        ask: parseFloat(data.askPx)
      };
    } catch (error) {
      console.error(`Error fetching OKX price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get price from KuCoin
   */
  private async getKuCoinPrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('KuCoin')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/market/orderbook/level1?symbol=${symbol}`, {
          timeout: 5000
        }),
        `kucoin-${symbol}`
      );

      const data = response.data.data;
      if (!data) return null;

      return {
        exchange: 'KuCoin',
        symbol,
        price: parseFloat(data.price),
        volume: 0,
        timestamp: Date.now(),
        bid: parseFloat(data.bestBid),
        ask: parseFloat(data.bestAsk)
      };
    } catch (error) {
      console.error(`Error fetching KuCoin price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get price from Gate.io
   */
  private async getGatePrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('Gate.io')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/spot/tickers?currency_pair=${symbol}`, {
          timeout: 5000
        }),
        `gate-${symbol}`
      );

      const data = response.data?.[0];
      if (!data) return null;

      return {
        exchange: 'Gate.io',
        symbol,
        price: parseFloat(data.last),
        volume: parseFloat(data.base_volume),
        timestamp: Date.now(),
        bid: parseFloat(data.highest_bid),
        ask: parseFloat(data.lowest_ask)
      };
    } catch (error) {
      console.error(`Error fetching Gate.io price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get price from Bitget
   */
  private async getBitgetPrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('Bitget')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/spot/market/tickers?symbol=${symbol}`, {
          timeout: 5000
        }),
        `bitget-${symbol}`
      );

      const data = response.data.data?.[0];
      if (!data) return null;

      return {
        exchange: 'Bitget',
        symbol,
        price: parseFloat(data.lastPr),
        volume: parseFloat(data.baseVolume),
        timestamp: Date.now(),
        bid: parseFloat(data.bidPr),
        ask: parseFloat(data.askPr)
      };
    } catch (error) {
      console.error(`Error fetching Bitget price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get price from MEXC
   */
  private async getMEXCPrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('MEXC')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/ticker/bookTicker?symbol=${symbol}`, {
          timeout: 5000
        }),
        `mexc-${symbol}`
      );

      const data = response.data;
      return {
        exchange: 'MEXC',
        symbol,
        price: (parseFloat(data.bidPrice) + parseFloat(data.askPrice)) / 2,
        volume: 0,
        timestamp: Date.now(),
        bid: parseFloat(data.bidPrice),
        ask: parseFloat(data.askPrice)
      };
    } catch (error) {
      console.error(`Error fetching MEXC price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get price from HTX (Huobi)
   */
  private async getHTXPrice(symbol: string): Promise<CexPrice | null> {
    try {
      const config = this.cexConfigs.get('HTX')!;
      const response: AxiosResponse = await this.rateLimiter.executeWithRateLimit(
        () => axios.get(`${config.apiBaseUrl}/market/detail/merged?symbol=${symbol}`, {
          timeout: 5000
        }),
        `htx-${symbol}`
      );

      const data = response.data.tick;
      if (!data) return null;

      return {
        exchange: 'HTX',
        symbol,
        price: parseFloat(data.close),
        volume: parseFloat(data.vol),
        timestamp: Date.now(),
        bid: parseFloat(data.bid?.[0] || data.close),
        ask: parseFloat(data.ask?.[0] || data.close)
      };
    } catch (error) {
      console.error(`Error fetching HTX price for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get prices from all exchanges for a given trading pair
   */
  async getAllPrices(baseToken: string, quoteToken: string): Promise<CexPrice[]> {
    const prices: CexPrice[] = [];
    const exchanges = Array.from(this.cexConfigs.keys());

    // Use Promise.allSettled to handle partial failures gracefully
    const pricePromises = exchanges.map(async (exchangeName) => {
      const config = this.cexConfigs.get(exchangeName)!;
      const symbol = config.symbolFormat(baseToken, quoteToken);

      try {
        let price: CexPrice | null = null;

        switch (exchangeName) {
          case 'Binance':
            price = await this.getBinancePrice(symbol);
            break;
          case 'Bybit':
            price = await this.getBybitPrice(symbol);
            break;
          case 'OKX':
            price = await this.getOKXPrice(symbol);
            break;
          case 'KuCoin':
            price = await this.getKuCoinPrice(symbol);
            break;
          case 'Gate.io':
            price = await this.getGatePrice(symbol);
            break;
          case 'Bitget':
            price = await this.getBitgetPrice(symbol);
            break;
          case 'MEXC':
            price = await this.getMEXCPrice(symbol);
            break;
          case 'HTX':
            price = await this.getHTXPrice(symbol);
            break;
        }

        return price;
      } catch (error) {
        console.error(`Error fetching price from ${exchangeName}:`, error);
        return null;
      }
    });

    const results = await Promise.allSettled(pricePromises);
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value) {
        prices.push(result.value);
      }
    });

    console.log(`📊 Retrieved prices from ${prices.length}/${exchanges.length} CEX exchanges for ${baseToken}/${quoteToken}`);
    return prices;
  }

  /**
   * Get the best bid and ask prices across all exchanges
   */
  async getBestPrices(baseToken: string, quoteToken: string): Promise<{
    bestBid: CexPrice | null;
    bestAsk: CexPrice | null;
    spread: number;
  }> {
    const prices = await this.getAllPrices(baseToken, quoteToken);
    
    if (prices.length === 0) {
      return { bestBid: null, bestAsk: null, spread: 0 };
    }

    // Find best bid (highest) and best ask (lowest)
    const bestBid = prices.reduce((best, current) => 
      !best || current.bid > best.bid ? current : best
    );

    const bestAsk = prices.reduce((best, current) => 
      !best || current.ask < best.ask ? current : best
    );

    const spread = bestAsk && bestBid ? 
      ((bestAsk.ask - bestBid.bid) / bestBid.bid) * 100 : 0;

    return { bestBid, bestAsk, spread };
  }

  /**
   * Find arbitrage opportunities between different CEX exchanges
   */
  async findCexArbitrageOpportunities(baseToken: string, quoteToken: string): Promise<{
    buyExchange: string;
    sellExchange: string;
    profitPercent: number;
    buyPrice: number;
    sellPrice: number;
  }[]> {
    const prices = await this.getAllPrices(baseToken, quoteToken);
    const opportunities: any[] = [];

    if (prices.length < 2) {
      return opportunities;
    }

    // Compare all exchange pairs for arbitrage
    for (let i = 0; i < prices.length; i++) {
      for (let j = i + 1; j < prices.length; j++) {
        const priceA = prices[i];
        const priceB = prices[j];

        // Check both directions
        // Direction 1: Buy on A, sell on B
        const profitAB = ((priceB.bid - priceA.ask) / priceA.ask) * 100;
        if (profitAB > 0.1) { // Minimum 0.1% profit
          opportunities.push({
            buyExchange: priceA.exchange,
            sellExchange: priceB.exchange,
            profitPercent: profitAB,
            buyPrice: priceA.ask,
            sellPrice: priceB.bid
          });
        }

        // Direction 2: Buy on B, sell on A
        const profitBA = ((priceA.bid - priceB.ask) / priceB.ask) * 100;
        if (profitBA > 0.1) { // Minimum 0.1% profit
          opportunities.push({
            buyExchange: priceB.exchange,
            sellExchange: priceA.exchange,
            profitPercent: profitBA,
            buyPrice: priceB.ask,
            sellPrice: priceA.bid
          });
        }
      }
    }

    // Sort by profit percentage (highest first)
    opportunities.sort((a, b) => b.profitPercent - a.profitPercent);

    return opportunities;
  }

  /**
   * Get supported trading pairs for major tokens
   */
  getSupportedPairs(): Array<{ base: string; quote: string }> {
    return [
      // Major crypto pairs
      { base: 'BTC', quote: 'USDT' },
      { base: 'ETH', quote: 'USDT' },
      { base: 'BNB', quote: 'USDT' },
      { base: 'ADA', quote: 'USDT' },
      { base: 'XRP', quote: 'USDT' },
      { base: 'DOT', quote: 'USDT' },
      { base: 'LINK', quote: 'USDT' },
      { base: 'UNI', quote: 'USDT' },
      { base: 'MATIC', quote: 'USDT' },
      { base: 'DOGE', quote: 'USDT' },

      // BTC pairs
      { base: 'ETH', quote: 'BTC' },
      { base: 'BNB', quote: 'BTC' },
      { base: 'ADA', quote: 'BTC' },

      // USDC pairs
      { base: 'BTC', quote: 'USDC' },
      { base: 'ETH', quote: 'USDC' },
      { base: 'BNB', quote: 'USDC' },

      // Stablecoin pairs
      { base: 'USDT', quote: 'USDC' },
      { base: 'BUSD', quote: 'USDT' },
      { base: 'BUSD', quote: 'USDC' }
    ];
  }
}