# Rate Limiting Improvements

This document describes the improvements made to address the rate limiting issues that were causing `eth_call in batch triggered rate limit` errors.

## Issues Resolved

The arbitrage bot was experiencing frequent rate limiting errors:
- ❌ `method eth_call in batch triggered rate limit` with error code `-32005`
- ❌ Multiple DEXes failing simultaneously (PancakeSwap V2/V3, Biswap, ApeSwap, etc.)
- ❌ Excessive retry attempts causing spam in logs

## Improvements Implemented

### 1. Enhanced Rate Limiter (`RateLimiter.ts`)

**More Conservative Timing:**
- Increased delay between requests: `800ms → 1500ms`
- Increased retry delay: `3000ms → 5000ms`
- Added jitter to retry delays to prevent thundering herd

**Circuit Breaker Pattern:**
- Opens after 3 consecutive rate limit failures
- Stays open for 30 seconds to allow recovery
- Automatically resets when timeout expires
- Prevents cascading failures

**Better Error Detection:**
- Improved pattern matching for rate limit errors
- Detects multiple error codes: `BAD_DATA`, `-32005`, `429`
- Handles various rate limit message formats

### 2. RPC Endpoint Rotation (`PriceMonitor.ts`)

**Load Distribution:**
- Support for multiple RPC endpoints per chain
- Round-robin rotation between providers
- Distributes load to reduce rate limiting

**Reduced Logging Spam:**
- Only logs actual rate limit errors
- Silences contract execution failures
- Maintains visibility of important issues

### 3. Configuration Improvements (`config.ts`)

**Multiple RPC Support:**
```typescript
rpcUrls: [
  'https://bsc-dataseed.binance.org/',
  'https://bsc-dataseed1.binance.org/',
  'https://bsc-dataseed2.binance.org/',
  'https://bsc-dataseed3.binance.org/'
]
```

**Environment Variables:**
```bash
BSC_RPC_URL=https://your-primary-rpc.com/
BSC_RPC_URL_2=https://your-backup-rpc.com/
BSC_RPC_URL_3=https://your-tertiary-rpc.com/
```

## Usage Examples

### Basic Setup
```javascript
const priceMonitor = new PriceMonitor(SUPPORTED_CHAINS);
// Automatically uses rate limiting and RPC rotation
```

### Manual Rate Limiting
```javascript
const rateLimiter = RateLimiter.getInstance();
const result = await rateLimiter.executeWithRateLimit(
  () => contract.getAmountsOut(amount, path),
  'PancakeSwap-V2-getAmountsOut'
);
```

### Circuit Breaker Status
```javascript
const status = rateLimiter.getQueueStatus();
console.log('Circuit breaker open:', status.circuitBreakerOpen);
console.log('Consecutive failures:', status.consecutiveFailures);
```

## Testing

The improvements have been tested with:
- ✅ Mock rate limit scenarios
- ✅ Circuit breaker functionality  
- ✅ RPC endpoint rotation
- ✅ Multi-DEX price fetching simulation

## Expected Results

With these improvements, you should see:
- 🚫 **Elimination** of `eth_call in batch triggered rate limit` errors
- ⚡ **Faster recovery** from temporary rate limits
- 📊 **Better load distribution** across RPC providers
- 🔇 **Reduced log spam** from rate limit retries
- 🛡️ **Automatic protection** via circuit breaker

## Configuration Tips

1. **Use Multiple RPC Endpoints**: Configure 3-4 RPC URLs per chain for best results
2. **Monitor Circuit Breaker**: Check logs for circuit breaker activations
3. **Adjust Timing**: Increase delays if rate limits persist
4. **Use Paid RPCs**: Consider premium RPC providers for higher limits

## Monitoring

Watch for these log messages:
- ⚠️ `Rate limit detected for X, retrying with backoff...`
- 🚫 `Circuit breaker OPENED due to X consecutive failures`
- ✅ `Circuit breaker reset, resuming requests`

The circuit breaker will automatically handle rate limit bursts and prevent cascading failures.