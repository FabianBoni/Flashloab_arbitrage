#!/usr/bin/env node

/**
 * Rate Limiting Test Script
 * 
 * This script helps test the rate limiting improvements and RPC configuration.
 * Run with: node test-rate-limiting.js
 */

const { PriceMonitor } = require('./dist/src/PriceMonitor');
const { RateLimiter } = require('./dist/src/RateLimiter');
const { SUPPORTED_CHAINS } = require('./dist/src/config');

async function testRateLimiting() {
    console.log('🧪 Testing Rate Limiting Configuration\n');
    
    // Test 1: RateLimiter functionality
    console.log('1️⃣ Testing RateLimiter...');
    const rateLimiter = RateLimiter.getInstance();
    
    let requestCount = 0;
    const testRequest = () => {
        requestCount++;
        console.log(`   Request ${requestCount} executed`);
        return Promise.resolve(`Result ${requestCount}`);
    };
    
    // Execute multiple requests to test queuing
    const promises = [];
    for (let i = 0; i < 5; i++) {
        promises.push(rateLimiter.executeWithRateLimit(testRequest, `test-${i}`));
    }
    
    await Promise.all(promises);
    console.log(`   ✅ Processed ${requestCount} requests with rate limiting\n`);
    
    // Test 2: Configuration validation
    console.log('2️⃣ Testing Configuration...');
    SUPPORTED_CHAINS.forEach(chain => {
        console.log(`   Chain ${chain.chainId} (${chain.name}):`);
        console.log(`     Primary RPC: ${chain.rpcUrl ? '✅' : '❌'}`);
        
        if (chain.rpcUrls) {
            console.log(`     Additional RPCs: ${chain.rpcUrls.length} configured`);
            chain.rpcUrls.forEach((url, index) => {
                console.log(`       ${index + 1}. ${url ? '✅' : '❌'} ${url}`);
            });
        } else {
            console.log(`     Additional RPCs: ⚠️  None configured (recommended to add more)`);
        }
        
        console.log(`     DEXes: ${chain.dexes.length} configured`);
    });
    console.log();
    
    // Test 3: PriceMonitor in demo mode
    console.log('3️⃣ Testing PriceMonitor (Demo Mode)...');
    const priceMonitor = new PriceMonitor(SUPPORTED_CHAINS, true); // Demo mode
    
    // Test a few price fetches
    const testPairs = [
        { dex: 'PancakeSwap V2', tokenA: 'WBNB', tokenB: 'USDT' },
        { dex: 'Biswap', tokenA: 'WBNB', tokenB: 'BUSD' },
        { dex: 'ApeSwap', tokenA: 'USDT', tokenB: 'USDC' }
    ];
    
    for (const pair of testPairs) {
        const price = await priceMonitor.getTokenPrice(
            56, // BSC
            pair.dex,
            '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', // Mock token A
            '0x55d398326f99059fF775485246999027B3197955', // Mock token B
            BigInt('1000000000000000000')
        );
        console.log(`   ${pair.dex}: ${pair.tokenA}->${pair.tokenB} = ${price.toString()}`);
    }
    console.log();
    
    // Test 4: Circuit breaker status
    console.log('4️⃣ Circuit Breaker Status...');
    const status = rateLimiter.getQueueStatus();
    console.log(`   Queue length: ${status.queueLength}`);
    console.log(`   Active requests: ${status.activeRequests}`);
    console.log(`   Circuit breaker open: ${status.circuitBreakerOpen ? '🚫' : '✅'}`);
    console.log(`   Consecutive failures: ${status.consecutiveFailures}`);
    console.log();
    
    console.log('✅ Rate limiting test completed!');
    console.log();
    console.log('💡 Tips:');
    console.log('   - Configure multiple RPC URLs in .env for better rate limiting');
    console.log('   - Monitor logs for circuit breaker activations');
    console.log('   - Test with real RPCs by setting DEMO_MODE=false');
}

// Environment check
if (!process.env.NODE_ENV) {
    console.log('⚠️  NODE_ENV not set, using development defaults');
}

if (process.env.DEMO_MODE !== 'false') {
    console.log('ℹ️  Running in demo mode (set DEMO_MODE=false for real RPC testing)');
}

testRateLimiting().catch(error => {
    console.error('❌ Test failed:', error);
    process.exit(1);
});