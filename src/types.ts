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
}

export interface ChainConfig {
  chainId: number;
  name: string;
  rpcUrl: string;
  flashloanProvider: string;
  dexes: DEXConfig[];
}

export interface CrossChainOpportunity extends ArbitrageOpportunity {
  sourceChain: number;
  targetChain: number;
  bridgeFee: number;
  bridgeTime: number;
}