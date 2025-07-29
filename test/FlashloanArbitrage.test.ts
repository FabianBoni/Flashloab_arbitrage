import { expect } from 'chai';
import hre from 'hardhat';
import type { FlashloanArbitrage } from '../typechain-types';

describe('FlashloanArbitrage', function () {
  let flashloanArbitrage: FlashloanArbitrage;
  let owner: any;
  let addr1: any;

  beforeEach(async function () {
    [owner, addr1] = await hre.ethers.getSigners();

    const FlashloanArbitrage = await hre.ethers.getContractFactory('FlashloanArbitrage');
    const contract = await FlashloanArbitrage.deploy();
    await contract.waitForDeployment();
    flashloanArbitrage = contract as unknown as FlashloanArbitrage;
  });

  describe('Deployment', function () {
    it('Should set the right owner', async function () {
      expect(await flashloanArbitrage.owner()).to.equal(owner.address);
    });

    it('Should initialize with correct default values', async function () {
      expect(await flashloanArbitrage.minProfitThreshold()).to.equal(hre.ethers.parseEther('0.01'));
      expect(await flashloanArbitrage.maxSlippage()).to.equal(50);
    });

    it('Should have DEX configurations set', async function () {
      const uniswapConfig = await flashloanArbitrage.dexConfigs('uniswap');
      expect(uniswapConfig.isActive).to.be.true;
      expect(uniswapConfig.name).to.equal('Uniswap V2');

      const sushiConfig = await flashloanArbitrage.dexConfigs('sushiswap');
      expect(sushiConfig.isActive).to.be.true;
      expect(sushiConfig.name).to.equal('SushiSwap');
    });
  });

  describe('DEX Configuration', function () {
    it('Should allow owner to update DEX config', async function () {
      await flashloanArbitrage.updateDEXConfig(
        'testdex',
        '0x1234567890123456789012345678901234567890',
        true
      );

      const config = await flashloanArbitrage.dexConfigs('testdex');
      expect(config.router).to.equal('0x1234567890123456789012345678901234567890');
      expect(config.isActive).to.be.true;
    });

    it('Should not allow non-owner to update DEX config', async function () {
      await expect(
        flashloanArbitrage.connect(addr1).updateDEXConfig(
          'testdex',
          '0x1234567890123456789012345678901234567890',
          true
        )
      ).to.be.reverted;
    });
  });

  describe('Profit Threshold', function () {
    it('Should allow owner to update minimum profit threshold', async function () {
      const newThreshold = hre.ethers.parseEther('0.05');
      await flashloanArbitrage.updateMinProfitThreshold(newThreshold);
      
      expect(await flashloanArbitrage.minProfitThreshold()).to.equal(newThreshold);
    });

    it('Should not allow non-owner to update profit threshold', async function () {
      await expect(
        flashloanArbitrage.connect(addr1).updateMinProfitThreshold(hre.ethers.parseEther('0.05'))
      ).to.be.reverted;
    });
  });

  describe('Emergency Functions', function () {
    it('Should allow owner to emergency withdraw ETH', async function () {
      // Send some ETH to the contract
      await owner.sendTransaction({
        to: await flashloanArbitrage.getAddress(),
        value: hre.ethers.parseEther('1.0'),
      });

      const initialBalance = await hre.ethers.provider.getBalance(owner.address);
      
      // Emergency withdraw
      const tx = await flashloanArbitrage.emergencyWithdraw(
        hre.ethers.ZeroAddress,
        hre.ethers.parseEther('1.0')
      );
      
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * BigInt(receipt!.gasPrice || 0);
      const finalBalance = await hre.ethers.provider.getBalance(owner.address);
      
      const expectedBalance = initialBalance + hre.ethers.parseEther('1.0') - gasUsed;
      expect(Number(finalBalance)).to.be.closeTo(
        Number(expectedBalance),
        Number(hre.ethers.parseEther('0.01')) // Allow for gas cost variance
      );
    });

    it('Should not allow non-owner to emergency withdraw', async function () {
      await expect(
        flashloanArbitrage.connect(addr1).emergencyWithdraw(
          hre.ethers.ZeroAddress,
          hre.ethers.parseEther('1.0')
        )
      ).to.be.reverted;
    });
  });

  describe('Access Control', function () {
    it('Should only allow owner to execute arbitrage', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'; // WETH
      const amount = hre.ethers.parseEther('1.0');
      const path = [asset, '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c']; // WETH -> USDC

      await expect(
        flashloanArbitrage.connect(addr1).executeArbitrage(
          asset,
          amount,
          'uniswap',
          'sushiswap',
          path
        )
      ).to.be.reverted;
    });
  });

  describe('Input Validation', function () {
    it('Should revert with invalid path', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
      const amount = hre.ethers.parseEther('1.0');
      const invalidPath = [asset]; // Path too short

      await expect(
        flashloanArbitrage.executeArbitrage(
          asset,
          amount,
          'uniswap',
          'sushiswap',
          invalidPath
        )
      ).to.be.reverted;
    });

    it('Should revert with inactive DEX', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
      const amount = hre.ethers.parseEther('1.0');
      const path = [asset, '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c'];

      await expect(
        flashloanArbitrage.executeArbitrage(
          asset,
          amount,
          'nonexistent',
          'sushiswap',
          path
        )
      ).to.be.reverted;
    });

    it('Should revert when path does not start with borrowed asset', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
      const amount = hre.ethers.parseEther('1.0');
      const wrongPath = ['0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c', asset]; // Wrong order

      await expect(
        flashloanArbitrage.executeArbitrage(
          asset,
          amount,
          'uniswap',
          'sushiswap',
          wrongPath
        )
      ).to.be.reverted;
    });
  });
});
