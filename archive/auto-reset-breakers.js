const { RateLimiter } = require('./dist/src/RateLimiter');

// Auto-reset circuit breakers every 30 seconds
setInterval(() => {
    const rateLimiter = RateLimiter.getInstance();
    const status = rateLimiter.getQueueStatus();
    
    if (status.circuitBreakerOpen) {
        console.log(`🔧 Auto-resetting circuit breaker (${status.consecutiveFailures} failures)`);
        rateLimiter.forceResetCircuitBreaker();
        rateLimiter.clearQueue();
        console.log('✅ Circuit breaker auto-reset completed');
    }
}, 30000); // Check every 30 seconds

console.log('🤖 Auto Circuit Breaker Reset service started (every 30s)');
