"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const chai_1 = require("chai");
const hardhat_1 = require("hardhat");
describe('FlashloanArbitrage', function () {
    let flashloanArbitrage;
    let owner;
    let addr1;
    beforeEach(async function () {
        [owner, addr1] = await hardhat_1.ethers.getSigners();
        const FlashloanArbitrage = await hardhat_1.ethers.getContractFactory('FlashloanArbitrage');
        flashloanArbitrage = await FlashloanArbitrage.deploy();
        await flashloanArbitrage.waitForDeployment();
    });
    describe('Deployment', function () {
        it('Should set the right owner', async function () {
            (0, chai_1.expect)(await flashloanArbitrage.owner()).to.equal(owner.address);
        });
        it('Should initialize with correct default values', async function () {
            (0, chai_1.expect)(await flashloanArbitrage.minProfitThreshold()).to.equal(hardhat_1.ethers.parseEther('0.01'));
            (0, chai_1.expect)(await flashloanArbitrage.maxSlippage()).to.equal(50);
        });
        it('Should have DEX configurations set', async function () {
            const uniswapConfig = await flashloanArbitrage.dexConfigs('uniswap');
            (0, chai_1.expect)(uniswapConfig.isActive).to.be.true;
            (0, chai_1.expect)(uniswapConfig.name).to.equal('Uniswap V2');
            const sushiConfig = await flashloanArbitrage.dexConfigs('sushiswap');
            (0, chai_1.expect)(sushiConfig.isActive).to.be.true;
            (0, chai_1.expect)(sushiConfig.name).to.equal('SushiSwap');
        });
    });
    describe('DEX Configuration', function () {
        it('Should allow owner to update DEX config', async function () {
            await flashloanArbitrage.updateDEXConfig('testdex', '0x1234567890123456789012345678901234567890', true);
            const config = await flashloanArbitrage.dexConfigs('testdex');
            (0, chai_1.expect)(config.router).to.equal('0x1234567890123456789012345678901234567890');
            (0, chai_1.expect)(config.isActive).to.be.true;
        });
        it('Should not allow non-owner to update DEX config', async function () {
            await (0, chai_1.expect)(flashloanArbitrage.connect(addr1).updateDEXConfig('testdex', '0x1234567890123456789012345678901234567890', true)).to.be.revertedWith('Ownable: caller is not the owner');
        });
    });
    describe('Profit Threshold', function () {
        it('Should allow owner to update minimum profit threshold', async function () {
            const newThreshold = hardhat_1.ethers.parseEther('0.05');
            await flashloanArbitrage.updateMinProfitThreshold(newThreshold);
            (0, chai_1.expect)(await flashloanArbitrage.minProfitThreshold()).to.equal(newThreshold);
        });
        it('Should not allow non-owner to update profit threshold', async function () {
            await (0, chai_1.expect)(flashloanArbitrage.connect(addr1).updateMinProfitThreshold(hardhat_1.ethers.parseEther('0.05'))).to.be.revertedWith('Ownable: caller is not the owner');
        });
    });
    describe('Emergency Functions', function () {
        it('Should allow owner to emergency withdraw ETH', async function () {
            // Send some ETH to the contract
            await owner.sendTransaction({
                to: await flashloanArbitrage.getAddress(),
                value: hardhat_1.ethers.parseEther('1.0'),
            });
            const initialBalance = await hardhat_1.ethers.provider.getBalance(owner.address);
            // Emergency withdraw
            const tx = await flashloanArbitrage.emergencyWithdraw(hardhat_1.ethers.ZeroAddress, hardhat_1.ethers.parseEther('1.0'));
            const receipt = await tx.wait();
            const gasUsed = receipt.gasUsed * receipt.gasPrice;
            const finalBalance = await hardhat_1.ethers.provider.getBalance(owner.address);
            (0, chai_1.expect)(finalBalance).to.be.closeTo(initialBalance + hardhat_1.ethers.parseEther('1.0') - gasUsed, hardhat_1.ethers.parseEther('0.01') // Allow for gas cost variance
            );
        });
        it('Should not allow non-owner to emergency withdraw', async function () {
            await (0, chai_1.expect)(flashloanArbitrage.connect(addr1).emergencyWithdraw(hardhat_1.ethers.ZeroAddress, hardhat_1.ethers.parseEther('1.0'))).to.be.revertedWith('Ownable: caller is not the owner');
        });
    });
    describe('Access Control', function () {
        it('Should only allow owner to execute arbitrage', async function () {
            const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'; // WETH
            const amount = hardhat_1.ethers.parseEther('1.0');
            const path = [asset, '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c']; // WETH -> USDC
            await (0, chai_1.expect)(flashloanArbitrage.connect(addr1).executeArbitrage(asset, amount, 'uniswap', 'sushiswap', path)).to.be.revertedWith('Ownable: caller is not the owner');
        });
    });
    describe('Input Validation', function () {
        it('Should revert with invalid path', async function () {
            const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
            const amount = hardhat_1.ethers.parseEther('1.0');
            const invalidPath = [asset]; // Path too short
            await (0, chai_1.expect)(flashloanArbitrage.executeArbitrage(asset, amount, 'uniswap', 'sushiswap', invalidPath)).to.be.revertedWith('Invalid path');
        });
        it('Should revert with inactive DEX', async function () {
            const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
            const amount = hardhat_1.ethers.parseEther('1.0');
            const path = [asset, '0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c'];
            await (0, chai_1.expect)(flashloanArbitrage.executeArbitrage(asset, amount, 'nonexistent', 'sushiswap', path)).to.be.revertedWith('DEX not active');
        });
        it('Should revert when path does not start with borrowed asset', async function () {
            const asset = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
            const amount = hardhat_1.ethers.parseEther('1.0');
            const wrongPath = ['0xA0b86a33E6417efF4e8edC958E5577E6a5C8a06c', asset]; // Wrong order
            await (0, chai_1.expect)(flashloanArbitrage.executeArbitrage(asset, amount, 'uniswap', 'sushiswap', wrongPath)).to.be.revertedWith('Path must start with borrowed asset');
        });
    });
});
//# sourceMappingURL=FlashloanArbitrage.test.js.map