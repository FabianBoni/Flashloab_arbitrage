import 'dotenv/config';
import { ArbitrageDashboardServer } from './dashboard-server.js';

async function main() {
  console.log('🚀 Starting Flashloan Arbitrage Dashboard...');
  
  const port = parseInt(process.env.WEB_PORT || '3000');
  const server = new ArbitrageDashboardServer(port);
  
  server.start();
  
  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n📴 Shutting down dashboard server...');
    process.exit(0);
  });
  
  process.on('SIGTERM', () => {
    console.log('\n📴 Shutting down dashboard server...');
    process.exit(0);
  });
}

main().catch(console.error);
