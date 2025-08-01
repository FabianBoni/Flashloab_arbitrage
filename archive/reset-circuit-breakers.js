#!/usr/bin/env node
/**
 * Reset script to clear all circuit breakers and restart the system
 * Run with: node reset-circuit-breakers.js
 */

require('dotenv').config();
const { RateLimiter } = require('./dist/src/RateLimiter');

console.log('🔄 Resetting all circuit breakers...');

// Reset the main rate limiter
const rateLimiter = RateLimiter.getInstance();
rateLimiter.forceResetCircuitBreaker();
rateLimiter.clearQueue();

console.log('✅ Circuit breakers reset successfully!');
console.log('💡 You can now restart the arbitrage bot with: npm start');
