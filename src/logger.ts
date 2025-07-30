import fs from 'fs';
import path from 'path';

export class Logger {
  private logDir: string;
  private logFile: string;
  private errorLogFile: string;
  private maxFileSize: number = 512 * 1024; // 512KB max size (kleiner!)
  private maxFiles: number = 3; // Nur 3 alte Dateien
  private lastLogTime: number = 0;
  private logThrottleMs: number = 5000; // Nur alle 5 Sekunden OPPORTUNITY logs

  constructor() {
    this.logDir = path.join(process.cwd(), 'logs');
    this.logFile = path.join(this.logDir, 'arbitrage-bot.log');
    this.errorLogFile = path.join(this.logDir, 'arbitrage-errors.log');
    this.ensureLogDir();
  }

  private ensureLogDir(): void {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  private formatMessage(level: string, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level.toUpperCase()}] ${message}\n`;
  }

  private writeToFile(filePath: string, content: string): void {
    try {
      // Check file size and rotate if needed
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        if (stats.size > this.maxFileSize) {
          this.rotateLogFile(filePath);
        }
      }
      
      fs.appendFileSync(filePath, content);
    } catch (error) {
      console.error('Failed to write to log file:', error);
    }
  }

  private rotateLogFile(filePath: string): void {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const rotatedFile = filePath.replace('.log', `-${timestamp}.log`);
      
      // Move current log to timestamped file
      fs.renameSync(filePath, rotatedFile);
      
      // Clean up old files
      this.cleanupOldLogs(path.dirname(filePath));
    } catch (error) {
      console.error('Failed to rotate log file:', error);
    }
  }

  private cleanupOldLogs(logDir: string): void {
    try {
      const files = fs.readdirSync(logDir)
        .filter(file => file.startsWith('arbitrage-bot-') && file.endsWith('.log'))
        .map(file => ({
          name: file,
          path: path.join(logDir, file),
          mtime: fs.statSync(path.join(logDir, file)).mtime
        }))
        .sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

      // Keep only maxFiles, delete the rest
      if (files.length > this.maxFiles) {
        files.slice(this.maxFiles).forEach(file => {
          fs.unlinkSync(file.path);
        });
      }
    } catch (error) {
      console.error('Failed to cleanup old logs:', error);
    }
  }

  info(message: string): void {
    const formatted = this.formatMessage('INFO', message);
    console.log(message);
    this.writeToFile(this.logFile, formatted);
  }

  success(message: string): void {
    const formatted = this.formatMessage('SUCCESS', message);
    console.log(`✅ ${message}`);
    this.writeToFile(this.logFile, formatted);
  }

  warning(message: string): void {
    const formatted = this.formatMessage('WARNING', message);
    console.log(`⚠️  ${message}`);
    this.writeToFile(this.logFile, formatted);
  }

  error(message: string, error?: any): void {
    const errorDetails = error ? ` - ${error.message || error}` : '';
    const fullMessage = `${message}${errorDetails}`;
    const formatted = this.formatMessage('ERROR', fullMessage);
    
    console.error(`❌ ${message}`);
    if (error) {
      console.error(error);
    }
    
    this.writeToFile(this.logFile, formatted);
    this.writeToFile(this.errorLogFile, formatted);
  }

  opportunity(message: string): void {
    // Throttle opportunity logs - only log every 5 seconds
    const now = Date.now();
    if (now - this.lastLogTime < this.logThrottleMs) {
      return; // Skip this log
    }
    this.lastLogTime = now;
    
    const formatted = this.formatMessage('OPPORTUNITY', message);
    console.log(`💰 ${message}`);
    this.writeToFile(this.logFile, formatted);
  }

  trade(message: string): void {
    const formatted = this.formatMessage('TRADE', message);
    console.log(`🚀 ${message}`);
    this.writeToFile(this.logFile, formatted);
  }

  stats(message: string): void {
    const formatted = this.formatMessage('STATS', message);
    console.log(`📊 ${message}`);
    this.writeToFile(this.logFile, formatted);
  }
}

export const logger = new Logger();
