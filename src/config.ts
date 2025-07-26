import { ChainConfig, DEXConfig } from './types';

export const SUPPORTED_CHAINS: ChainConfig[] = [
  {
    chainId: 1,
    name: 'Ethereum',
    rpcUrl: process.env.ETHEREUM_RPC_URL || '',
    flashloanProvider: '0x87870Bca3F8fC6aa600BDeDBaFB3ba45C17D2b5', // Aave V3
    dexes: [
      {
        name: 'Uniswap V2',
        router: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        factory: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
        isActive: true,
        chainId: 1,
      },
      {
        name: 'Sushiswap',
        router: '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
        factory: '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
        isActive: true,
        chainId: 1,
      },
    ],
  },
  {
    chainId: 137,
    name: 'Polygon',
    rpcUrl: process.env.POLYGON_RPC_URL || '',
    flashloanProvider: '0x794a61358D6845594F94dc1DB02A252b5b4814aD', // Aave V3
    dexes: [
      {
        name: 'Quickswap',
        router: '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
        factory: '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
        isActive: true,
        chainId: 137,
      },
      {
        name: 'Sushiswap',
        router: '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
        factory: '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
        isActive: true,
        chainId: 137,
      },
    ],
  },
  {
    chainId: 42161,
    name: 'Arbitrum',
    rpcUrl: process.env.ARBITRUM_RPC_URL || '',
    flashloanProvider: '0x794a61358D6845594F94dc1DB02A252b5b4814aD', // Aave V3
    dexes: [
      {
        name: 'Uniswap V2',
        router: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        factory: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
        isActive: true,
        chainId: 42161,
      },
      {
        name: 'Sushiswap',
        router: '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
        factory: '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
        isActive: true,
        chainId: 42161,
      },
    ],
  },
];

export const POPULAR_TOKENS = {
  1: { // Ethereum
    WETH: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    USDC: '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c',
    USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    WBTC: '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
  },
  137: { // Polygon
    WMATIC: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
    USDC: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
    USDT: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
    DAI: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
    WETH: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
  },
  42161: { // Arbitrum
    WETH: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
    USDC: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
    USDT: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
    DAI: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1',
    ARB: '0x912CE59144191C1204E64559FE8253a0e49E6548',
  },
};

export const MIN_PROFIT_THRESHOLD = parseFloat(process.env.MIN_PROFIT_THRESHOLD || '0.01');
export const MAX_GAS_PRICE = parseFloat(process.env.MAX_GAS_PRICE || '50');
export const SLIPPAGE_TOLERANCE = parseFloat(process.env.SLIPPAGE_TOLERANCE || '0.005');
export const PRICE_UPDATE_INTERVAL = parseInt(process.env.PRICE_UPDATE_INTERVAL || '5000');
export const OPPORTUNITY_CHECK_INTERVAL = parseInt(process.env.OPPORTUNITY_CHECK_INTERVAL || '10000');