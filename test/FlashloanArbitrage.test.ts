import { expect } from 'chai';
import { ethers } from 'hardhat';
import { FlashloanArbitrage } from '../typechain-types';

describe('FlashloanArbitrage', function () {
  let flashloanArbitrage: FlashloanArbitrage;
  let owner: any;
  let addr1: any;

  beforeEach(async function () {
    [owner, addr1] = await ethers.getSigners();

    const FlashloanArbitrage = await ethers.getContractFactory('FlashloanArbitrage');
    flashloanArbitrage = await FlashloanArbitrage.deploy();
    await flashloanArbitrage.waitForDeployment();
  });

  describe('Deployment', function () {
    it('Should set the right owner', async function () {
      expect(await flashloanArbitrage.owner()).to.equal(owner.address);
    });

    it('Should initialize with correct default values', async function () {
      expect(await flashloanArbitrage.minProfitThreshold()).to.equal(ethers.parseEther('0.01'));
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
      ).to.be.revertedWith('Ownable: caller is not the owner');
    });
  });

  describe('Profit Threshold', function () {
    it('Should allow owner to update minimum profit threshold', async function () {
      const newThreshold = ethers.parseEther('0.05');
      await flashloanArbitrage.updateMinProfitThreshold(newThreshold);
      
      expect(await flashloanArbitrage.minProfitThreshold()).to.equal(newThreshold);
    });

    it('Should not allow non-owner to update profit threshold', async function () {
      await expect(
        flashloanArbitrage.connect(addr1).updateMinProfitThreshold(ethers.parseEther('0.05'))
      ).to.be.revertedWith('Ownable: caller is not the owner');
    });
  });

  describe('Emergency Functions', function () {
    it('Should allow owner to emergency withdraw ETH', async function () {
      // Send some ETH to the contract
      await owner.sendTransaction({
        to: await flashloanArbitrage.getAddress(),
        value: ethers.parseEther('1.0'),
      });

      const initialBalance = await ethers.provider.getBalance(owner.address);
      
      // Emergency withdraw
      const tx = await flashloanArbitrage.emergencyWithdraw(
        ethers.ZeroAddress,
        ethers.parseEther('1.0')
      );
      
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice;
      const finalBalance = await ethers.provider.getBalance(owner.address);
      
      expect(finalBalance).to.be.closeTo(
        initialBalance + ethers.parseEther('1.0') - gasUsed,
        ethers.parseEther('0.01') // Allow for gas cost variance
      );
    });

    it('Should not allow non-owner to emergency withdraw', async function () {
      await expect(
        flashloanArbitrage.connect(addr1).emergencyWithdraw(
          ethers.ZeroAddress,
          ethers.parseEther('1.0')
        )
      ).to.be.revertedWith('Ownable: caller is not the owner');
    });
  });

  describe('Access Control', function () {
    it('Should only allow owner to execute arbitrage', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'; // WETH
      const amount = ethers.parseEther('1.0');
      const path = [asset, '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c']; // WETH -> USDC

      await expect(
        flashloanArbitrage.connect(addr1).executeArbitrage(
          asset,
          amount,
          'uniswap',
          'sushiswap',
          path
        )
      ).to.be.revertedWith('Ownable: caller is not the owner');
    });
  });

  describe('Input Validation', function () {
    it('Should revert with invalid path', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
      const amount = ethers.parseEther('1.0');
      const invalidPath = [asset]; // Path too short

      await expect(
        flashloanArbitrage.executeArbitrage(
          asset,
          amount,
          'uniswap',
          'sushiswap',
          invalidPath
        )
      ).to.be.revertedWith('Invalid path');
    });

    it('Should revert with inactive DEX', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
      const amount = ethers.parseEther('1.0');
      const path = [asset, '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c'];

      await expect(
        flashloanArbitrage.executeArbitrage(
          asset,
          amount,
          'nonexistent',
          'sushiswap',
          path
        )
      ).to.be.revertedWith('DEX not active');
    });

    it('Should revert when path does not start with borrowed asset', async function () {
      const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
      const amount = ethers.parseEther('1.0');
      const wrongPath = ['0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c', asset]; // Wrong order

      await expect(
        flashloanArbitrage.executeArbitrage(
          asset,
          amount,
          'uniswap',
          'sushiswap',
          wrongPath
        )
      ).to.be.revertedWith('Path must start with borrowed asset');
    });
  });
});