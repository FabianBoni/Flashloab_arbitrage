export interface DEXConfig {
  name: string;
  router: string;
  factory: string;
  isActive: boolean;
  chainId: number;
}

export interface CexConfig {
  name: string;
  apiBaseUrl: string;
  apiKey?: string;
  apiSecret?: string;
  rateLimit: number;
  symbolFormat: (base: string, quote: string) => string;
}

export interface ArbitrageOpportunity {
  tokenA: string;
  tokenB: string;
  amountIn: string;
  profitUSD: number;
  profitPercent: number;
  dexA: string;
  dexB: string;
  path: string[];
  gasEstimate: string;
  timestamp: number;
  chainId: number; // Add chainId to identify which chain the opportunity is on
}

export interface CexDexArbitrageOpportunity {
  baseToken: string;
  quoteToken: string;
  amountIn: string;
  profitUSD: number;
  profitPercent: number;
  cexExchange: string;
  dexName: string;
  cexPrice: number;
  dexPrice: number;
  direction: 'CEX_TO_DEX' | 'DEX_TO_CEX'; // Buy on CEX, sell on DEX or vice versa
  gasEstimate: string;
  bridgeFee?: number;
  timestamp: number;
  chainId: number;
}

export interface ChainConfig {
  chainId: number;
  name: string;
  rpcUrl: string;
  rpcUrls?: string[]; // Optional array of RPC URLs for load balancing
  flashloanProvider: string;
  dexes: DEXConfig[];
}

export interface CrossChainOpportunity extends ArbitrageOpportunity {
  sourceChain: number;
  targetChain: number;
  bridgeFee: number;
  bridgeTime: number;
}