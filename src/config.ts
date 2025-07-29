import { ChainConfig, DEXConfig } from './types';

export const SUPPORTED_CHAINS: ChainConfig[] = [
  {
    chainId: 56,
    name: 'BSC',
    rpcUrl: process.env.BSC_RPC_URL || '',
    flashloanProvider: '0x6807dc923806fE8Fd134338EABCA509979a7e0cB', // Aave V3
    dexes: [
      {
        name: 'PancakeSwap V2',
        router: '0x10ED43C718714eb63d5aA57B78B54704E256024E', // Verified from docs
        factory: '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73', // Verified from docs
        isActive: true,
        chainId: 56,
      },
      {
        name: 'Biswap',
        router: '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
        factory: '0x858E3312ed3A876947EA49d572A7C42DE08af7EE',
        isActive: true,
        chainId: 56,
      },
      {
        name: 'ApeSwap',
        router: '0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7',
        factory: '0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6',
        isActive: true,
        chainId: 56,
      },
      {
        name: 'BabySwap',
        router: '0x325E343f1dE602396E256B67eFd1F61C3A6B38Bd',
        factory: '0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da',
        isActive: true,
        chainId: 56,
      },
    ],
  },
];

export const POPULAR_TOKENS = {
  56: { // BSC - EXPANDED for more opportunities
    WBNB: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
    USDT: '0x55d398326f99059fF775485246999027B3197955',
    BUSD: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
    USDC: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
    CAKE: '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82', // PancakeSwap
    BSW: '0x965F527D9159dCe6288a2219DB51fc6Eef120dD1',  // Biswap
    BTCB: '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c', // Bitcoin BEP20
    ETH: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',   // Ethereum BEP20
  },
};

export const MIN_PROFIT_THRESHOLD = parseFloat(process.env.MIN_PROFIT_THRESHOLD || '0.01');
export const MAX_GAS_PRICE = parseFloat(process.env.MAX_GAS_PRICE || '50');
export const SLIPPAGE_TOLERANCE = parseFloat(process.env.SLIPPAGE_TOLERANCE || '0.005');
export const PRICE_UPDATE_INTERVAL = parseInt(process.env.PRICE_UPDATE_INTERVAL || '5000');
export const OPPORTUNITY_CHECK_INTERVAL = parseInt(process.env.OPPORTUNITY_CHECK_INTERVAL || '10000');