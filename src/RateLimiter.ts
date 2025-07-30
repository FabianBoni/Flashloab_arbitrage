import { logger } from './logger.js';

export class RateLimiter {
    private static instance: RateLimiter;
    private requestQueue: Array<() => Promise<any>> = [];
    private processing = false;
    private readonly maxConcurrent = 1; // Keep at 1 for maximum stability
    private readonly delayBetweenRequests = 1200; // Erhöhe auf 1200ms für extreme Ratenbegrenzung
    private readonly retryDelay = 7000; // Increase retry delay to 7 seconds
    private activeRequests = 0;
    private lastRequestTime = 0;
    private isCircuitBreakerOpen = false;
    private circuitBreakerResetTime = 0;
    private readonly circuitBreakerTimeout = 30000; // 30 seconds circuit breaker timeout
    private consecutiveFailures = 0;
    private readonly maxConsecutiveFailures = 3;

    private constructor() {
        // Using the exported logger instance
    }

    public static getInstance(): RateLimiter {
        if (!RateLimiter.instance) {
            RateLimiter.instance = new RateLimiter();
        }
        return RateLimiter.instance;
    }

    public async executeWithRateLimit<T>(
        requestFn: () => Promise<T>,
        context: string = 'Unknown'
    ): Promise<T | null> {
        // Check circuit breaker
        if (this.isCircuitBreakerOpen) {
            const now = Date.now();
            if (now < this.circuitBreakerResetTime) {
                // Circuit breaker is still open, reject immediately
                logger.warning(`Circuit breaker open for ${context}, skipping request`);
                return null;
            } else {
                // Reset circuit breaker
                this.isCircuitBreakerOpen = false;
                this.consecutiveFailures = 0;
                logger.info('Circuit breaker reset, resuming requests');
            }
        }

        return new Promise((resolve) => {
            this.requestQueue.push(async () => {
                try {
                    // Ensure minimum delay between requests
                    const now = Date.now();
                    const timeSinceLastRequest = now - this.lastRequestTime;
                    if (timeSinceLastRequest < this.delayBetweenRequests) {
                        await this.sleep(this.delayBetweenRequests - timeSinceLastRequest);
                    }

                    this.activeRequests++;
                    this.lastRequestTime = Date.now();
                    
                    const result = await this.executeWithRetry(requestFn, context);
                    this.activeRequests--;
                    
                    // Reset consecutive failures on success
                    if (result !== null) {
                        this.consecutiveFailures = 0;
                    }
                    
                    resolve(result);
                } catch (error) {
                    this.activeRequests--;
                    this.handleRequestError(error, context);
                    resolve(null);
                }
            });

            this.processQueue();
        });
    }

    private async executeWithRetry<T>(
        requestFn: () => Promise<T>,
        context: string,
        maxRetries = 3
    ): Promise<T | null> {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const result = await requestFn();
                return result;
            } catch (error: any) {
                const isRateLimit = this.isRateLimitError(error);

                if (isRateLimit) {
                    this.consecutiveFailures++;
                    
                    // Open circuit breaker if too many consecutive failures
                    if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
                        this.openCircuitBreaker();
                        throw error; // Don't retry when circuit breaker opens
                    }

                    if (attempt < maxRetries) {
                        // Only log on first retry attempt to reduce spam
                        if (attempt === 1) {
                            logger.warning(`⚠️  Rate limit detected for ${context}, retrying with backoff...`);
                        }
                        const backoffDelay = this.retryDelay * attempt * (1 + Math.random() * 0.5); // Add jitter
                        await this.sleep(backoffDelay);
                        continue;
                    } else {
                        // All retries exhausted
                        logger.error(`❌ Rate limited request failed for ${context}:`, error);
                    }
                }

                // If it's not a rate limit error or we've exhausted retries, throw
                throw error;
            }
        }
        return null;
    }

    private isRateLimitError(error: any): boolean {
        if (!error) return false;
        
        const errorString = JSON.stringify(error);
        const hasRateLimitIndicators = 
            error?.code === 'BAD_DATA' || 
            errorString.includes('rate limit') ||
            errorString.includes('too many requests') ||
            errorString.includes('429') ||
            (error?.info?.payload && errorString.includes('-32005'));
            
        return hasRateLimitIndicators;
    }

    private openCircuitBreaker(): void {
        this.isCircuitBreakerOpen = true;
        this.circuitBreakerResetTime = Date.now() + this.circuitBreakerTimeout;
        logger.warning(`🚫 Circuit breaker OPENED due to ${this.consecutiveFailures} consecutive rate limit failures. Pausing requests for ${this.circuitBreakerTimeout/1000}s`);
    }

    private handleRequestError(error: any, context: string): void {
        const isRateLimit = this.isRateLimitError(error);
        
        if (isRateLimit) {
            logger.error(`❌ Rate limited request failed for ${context}:`, error);
        }
        // Silently handle require(false) and other contract execution errors for non-rate-limit errors
    }

    private async processQueue(): Promise<void> {
        if (this.processing || this.requestQueue.length === 0) {
            return;
        }

        this.processing = true;

        while (this.requestQueue.length > 0 && this.activeRequests < this.maxConcurrent) {
            const request = this.requestQueue.shift();
            if (request) {
                // Don't await here - allow concurrent execution up to maxConcurrent
                request().catch(() => {}); // Errors are handled in executeWithRateLimit
            }
        }

        this.processing = false;

        // Continue processing if there are more requests
        if (this.requestQueue.length > 0) {
            setTimeout(() => this.processQueue(), this.delayBetweenRequests);
        }
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    public getQueueStatus(): { queueLength: number; activeRequests: number; circuitBreakerOpen: boolean; consecutiveFailures: number } {
        return {
            queueLength: this.requestQueue.length,
            activeRequests: this.activeRequests,
            circuitBreakerOpen: this.isCircuitBreakerOpen,
            consecutiveFailures: this.consecutiveFailures
        };
    }

    public clearQueue(): void {
        this.requestQueue = [];
        this.isCircuitBreakerOpen = false;
        this.consecutiveFailures = 0;
        logger.info('Rate limiter queue cleared and circuit breaker reset');
    }

    public forceResetCircuitBreaker(): void {
        this.isCircuitBreakerOpen = false;
        this.consecutiveFailures = 0;
        this.circuitBreakerResetTime = 0;
        logger.info('Circuit breaker manually reset');
    }
}
