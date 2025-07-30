import { logger } from './logger.js';

export class RateLimiter {
    private static instance: RateLimiter;
    private requestQueue: Array<() => Promise<any>> = [];
    private processing = false;
    private readonly maxConcurrent = 1; // Zurück zu 1 concurrent request für Stabilität
    private readonly delayBetweenRequests = 800; // Erhöhe auf 800ms für bessere Rate Limit Kontrolle
    private readonly retryDelay = 3000; // Erhöhe Retry Delay auf 3 Sekunden
    private activeRequests = 0;
    private lastRequestTime = 0;

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
                    resolve(result);
                } catch (error) {
                    this.activeRequests--;
                    // Only log actual rate limiting errors, not contract execution failures
                    const isRateLimit = (error as any)?.code === 'BAD_DATA' && 
                        (error as any)?.info?.payload && 
                        JSON.stringify(error).includes('rate limit');
                    
                    if (isRateLimit) {
                        logger.error(`Rate limited request failed for ${context}:`, error);
                    }
                    // Silently handle require(false) and other contract execution errors
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
                const isRateLimit = error?.code === 'BAD_DATA' && 
                    error?.info?.payload && 
                    JSON.stringify(error).includes('rate limit');

                if (isRateLimit && attempt < maxRetries) {
                    // Only log on first retry attempt to reduce spam
                    if (attempt === 1) {
                        logger.warning(`Rate limit detected for ${context}, retrying with backoff...`);
                    }
                    await this.sleep(this.retryDelay * attempt); // Exponential backoff
                    continue;
                }

                // If it's not a rate limit error or we've exhausted retries, throw
                throw error;
            }
        }
        return null;
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

    public getQueueStatus(): { queueLength: number; activeRequests: number } {
        return {
            queueLength: this.requestQueue.length,
            activeRequests: this.activeRequests
        };
    }

    public clearQueue(): void {
        this.requestQueue = [];
        logger.info('Rate limiter queue cleared');
    }
}
