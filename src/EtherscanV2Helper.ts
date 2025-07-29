import axios from 'axios';

/**
 * Etherscan V2 API Helper
 * Uses the new unified API that works across all supported chains with a single API key
 */
export class EtherscanV2Helper {
  private apiKey: string;
  private baseUrl = 'https://api.etherscan.io/v2/api';

  // Chain ID mapping for Etherscan V2
  private static readonly SUPPORTED_CHAINS = {
    ETHEREUM: 1,
    POLYGON: 137,
    ARBITRUM: 42161,
    BSC: 56,
    OPTIMISM: 10,
    BASE: 8453,
    SCROLL: 534352,
    BLAST: 81457,
  };

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  /**
   * Get account balance for any supported chain
   */
  async getBalance(address: string, chainId: number): Promise<string> {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          chainid: chainId,
          module: 'account',
          action: 'balance',
          address: address,
          tag: 'latest',
          apikey: this.apiKey
        }
      });

      if (response.data.status === '1') {
        return response.data.result;
      } else {
        throw new Error(response.data.message || 'Failed to get balance');
      }
    } catch (error: any) {
      console.error(`Error getting balance for ${address} on chain ${chainId}:`, error.message);
      throw error;
    }
  }

  /**
   * Get transaction list for an address on any supported chain
   */
  async getTransactions(
    address: string,
    chainId: number,
    startBlock: number = 0,
    endBlock: number = 99999999,
    page: number = 1,
    offset: number = 10
  ): Promise<any[]> {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          chainid: chainId,
          module: 'account',
          action: 'txlist',
          address: address,
          startblock: startBlock,
          endblock: endBlock,
          page: page,
          offset: offset,
          sort: 'desc',
          apikey: this.apiKey
        }
      });

      if (response.data.status === '1') {
        return response.data.result;
      } else {
        throw new Error(response.data.message || 'Failed to get transactions');
      }
    } catch (error: any) {
      console.error(`Error getting transactions for ${address} on chain ${chainId}:`, error.message);
      throw error;
    }
  }

  /**
   * Get contract verification status
   */
  async getContractVerificationStatus(contractAddress: string, chainId: number): Promise<any> {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          chainid: chainId,
          module: 'contract',
          action: 'getsourcecode',
          address: contractAddress,
          apikey: this.apiKey
        }
      });

      if (response.data.status === '1') {
        return response.data.result[0];
      } else {
        throw new Error(response.data.message || 'Failed to get contract info');
      }
    } catch (error: any) {
      console.error(`Error getting contract info for ${contractAddress} on chain ${chainId}:`, error.message);
      throw error;
    }
  }

  /**
   * Verify and publish contract source code
   */
  async verifyContract(params: {
    contractAddress: string;
    chainId: number;
    sourceCode: string;
    contractName: string;
    compilerVersion: string;
    optimizationUsed: boolean;
    runs?: number;
    constructorArguments?: string;
    libraryName1?: string;
    libraryAddress1?: string;
  }): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('chainid', params.chainId.toString());
      formData.append('module', 'contract');
      formData.append('action', 'verifysourcecode');
      formData.append('contractaddress', params.contractAddress);
      formData.append('sourceCode', params.sourceCode);
      formData.append('contractname', params.contractName);
      formData.append('compilerversion', params.compilerVersion);
      formData.append('optimizationUsed', params.optimizationUsed ? '1' : '0');
      if (params.runs) formData.append('runs', params.runs.toString());
      if (params.constructorArguments) formData.append('constructorArguements', params.constructorArguments);
      if (params.libraryName1) formData.append('libraryname1', params.libraryName1);
      if (params.libraryAddress1) formData.append('libraryaddress1', params.libraryAddress1);
      formData.append('apikey', this.apiKey);

      const response = await axios.post(this.baseUrl, formData);

      if (response.data.status === '1') {
        return response.data.result; // Returns GUID for verification tracking
      } else {
        throw new Error(response.data.message || 'Failed to submit for verification');
      }
    } catch (error: any) {
      console.error(`Error verifying contract ${params.contractAddress} on chain ${params.chainId}:`, error.message);
      throw error;
    }
  }

  /**
   * Check contract verification status using GUID
   */
  async checkVerificationStatus(guid: string, chainId: number): Promise<any> {
    try {
      const response = await axios.get(this.baseUrl, {
        params: {
          chainid: chainId,
          module: 'contract',
          action: 'checkverifystatus',
          guid: guid,
          apikey: this.apiKey
        }
      });

      return response.data;
    } catch (error: any) {
      console.error(`Error checking verification status for GUID ${guid}:`, error.message);
      throw error;
    }
  }

  /**
   * Get supported chains list
   */
  static getSupportedChains(): Record<string, number> {
    return { ...this.SUPPORTED_CHAINS };
  }

  /**
   * Check if a chain ID is supported by Etherscan V2
   */
  static isChainSupported(chainId: number): boolean {
    return Object.values(this.SUPPORTED_CHAINS).includes(chainId);
  }

  /**
   * Get chain name by chain ID
   */
  static getChainName(chainId: number): string {
    const chains: Record<number, string> = {
      1: 'Ethereum',
      137: 'Polygon',
      42161: 'Arbitrum',
      56: 'BSC',
      10: 'Optimism',
      8453: 'Base',
      534352: 'Scroll',
      81457: 'Blast',
    };
    return chains[chainId] || `Chain ${chainId}`;
  }
}

// Usage example
export const createEtherscanV2Helper = (apiKey?: string): EtherscanV2Helper => {
  const key = apiKey || process.env.ETHERSCAN_API_KEY;
  if (!key) {
    throw new Error('Etherscan API key is required. Set ETHERSCAN_API_KEY environment variable.');
  }
  return new EtherscanV2Helper(key);
};
