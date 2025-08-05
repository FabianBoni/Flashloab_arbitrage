# Docker Management Guide

## Quick Start

### Option 1: Linux/Unix Bash Script
```bash
chmod +x manage.sh
./manage.sh
```

### Option 2: Windows Batch Script (Simple)
```bash
manage.bat
```

### Option 3: Python Script (Advanced)
```bash
python manage.py
```

## Manual Docker Commands

### Build Image
```bash
docker build -t bsc-arbitrage .
```

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Status
```bash
docker-compose ps
docker ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f bsc-arbitrage
```

### Restart Services
```bash
docker-compose restart
```

### Shell Access
```bash
docker exec -it bsc-arbitrage-scanner /bin/bash
```

## Environment Configuration

Create a `.env` file with your settings:
```env
# Required for trading
PRIVATE_KEY=your_private_key_here
BSC_RPC_URL=https://bsc-dataseed1.binance.org/

# Optional
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
MIN_PROFIT_THRESHOLD=0.008
SCAN_INTERVAL=10
```

## Docker Compose Services

- **bsc-arbitrage**: Main arbitrage scanner container
- **Resource limits**: Optimized for Raspberry Pi (512M RAM, 1 CPU)
- **Volumes**: Persistent log storage
- **Health checks**: Automatic monitoring
- **Auto-restart**: Unless manually stopped

## Management Features

- ✅ Docker installation check
- ✅ Build automation
- ✅ Service lifecycle management
- ✅ Log monitoring
- ✅ Shell access
- ✅ Resource cleanup
- ✅ Health status monitoring

## Production Deployment

### Linux/Unix:
1. **Make executable**: `chmod +x manage.sh`
2. **Build image**: `./manage.sh` → Option 1
3. **Configure environment**: Edit `.env` file
4. **Start services**: `./manage.sh` → Option 2
5. **Monitor logs**: `./manage.sh` → Option 6
6. **Check status**: `./manage.sh` → Option 5

### Windows:
1. **Build image**: `manage.bat` → Option 1
2. **Configure environment**: Edit `.env` file
3. **Start services**: `manage.bat` → Option 2
4. **Monitor logs**: `manage.bat` → Option 5
5. **Check status**: `manage.bat` → Option 4
