export interface DEXConfig {
  name: string;
  router: string;
  factory: string;
  isActive: boolean;
  chainId: number;
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