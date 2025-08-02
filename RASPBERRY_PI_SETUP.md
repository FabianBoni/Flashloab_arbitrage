# 🚀 Complete Raspberry Pi Setup Guide for BSC Arbitrage Scanner

## Step 1: Prepare Your Raspberry Pi

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Git
```bash
sudo apt install git -y
```

## Step 2: Install Docker

### Install Docker
```bash
# Add Docker's official GPG key
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Reboot to apply group changes
sudo reboot
```

### After reboot, verify Docker installation:
```bash
docker --version
docker run hello-world
```

### Install Docker Compose
```bash
# Method 1: Try apt package first (modern Pi OS)
sudo apt install docker-compose-plugin -y

# Method 2: If method 1 fails, install binary
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Test installation
docker compose version
# OR if using old version:
docker-compose version
```

## Step 3: Clone and Setup the Project

### Clone the repository
```bash
cd ~
git clone https://github.com/FabianBoni/Flashloab_arbitrage.git
cd Flashloab_arbitrage
```

### Make scripts executable
```bash
chmod +x *.sh
```

### Run the setup script
```bash
./setup-pi.sh
```

If you get permission errors, try the modern setup:
```bash
./setup-pi-modern.sh
```

## Step 4: Configure Environment

### Create .env file
```bash
nano .env
```

Add your configuration:
```env
# BSC Configuration
BSC_RPC_URL=https://bsc-dataseed1.binance.org/
SCAN_INTERVAL=10

# Profit Thresholds
MIN_PROFIT_THRESHOLD=0.008

# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration (optional - for real trading)
# PRIVATE_KEY=your_private_key_here

# Logging
LOG_LEVEL=INFO
```

## Step 5: Build and Start the Scanner

### Setup permissions and build
```bash
# Setup permissions
./manage.sh setup

# Build the Docker image
docker compose build

# Start the scanner
./manage.sh start
```

## Step 6: Monitor the Scanner

### View logs
```bash
./manage.sh logs
```

### Check status
```bash
./manage.sh status
```

### Stop the scanner
```bash
./manage.sh stop
```

## Step 7: Alternative Manual Setup (if scripts fail)

### Manual Docker setup
```bash
# Create logs directory
mkdir -p logs
chmod 755 logs

# Build image manually
docker build -t bsc-arbitrage .

# Run container manually
docker run -d \
  --name bsc-arbitrage-scanner \
  --restart unless-stopped \
  -v $(pwd)/.env:/home/arbitrage/app/.env:ro \
  -e BSC_RPC_URL=https://bsc-dataseed1.binance.org/ \
  -e SCAN_INTERVAL=10 \
  -e MIN_PROFIT_THRESHOLD=0.008 \
  -e LOG_LEVEL=INFO \
  bsc-arbitrage

# View logs
docker logs -f bsc-arbitrage-scanner
```

## Troubleshooting

### If Docker Compose not found:
```bash
# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# OR install binary version
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### If permission errors:
```bash
# Fix ownership
sudo chown -R $USER:$USER .
chmod +x *.sh

# Fix Docker permissions
sudo usermod -aG docker $USER
sudo reboot
```

### If Python environment errors:
```bash
# Install Python packages system-wide (for development only)
sudo apt install python3-pip python3-venv -y
```

### Memory issues on Pi:
```bash
# Increase swap space
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## What the Scanner Does

✅ **Monitoring Mode** (default):
- Scans BSC DEXes for arbitrage opportunities
- Logs all profitable opportunities found
- Sends Telegram notifications (if configured)
- Uses minimal resources (optimized for Pi)

✅ **Trading Mode** (with PRIVATE_KEY):
- Automatically executes profitable trades
- Uses flashloan arbitrage (no capital required)
- Dynamic position sizing based on profit
- Comprehensive risk management

## Commands Reference

```bash
# Basic operations
./manage.sh start      # Start the scanner
./manage.sh stop       # Stop the scanner  
./manage.sh restart    # Restart the scanner
./manage.sh logs       # View live logs
./manage.sh status     # Check status

# Maintenance
./manage.sh update     # Update and rebuild
./manage.sh clean      # Clean Docker resources
./manage.sh backup     # Backup configuration

# Setup & Testing
./manage.sh setup      # Setup permissions
./manage.sh compose-test # Test Docker Compose
```

## Expected Output

The scanner will show:
- Connection to BSC network
- Token prices from multiple DEXes
- Price spreads between exchanges
- Profitable arbitrage opportunities
- Real-time profit calculations
- Memory usage optimizations

🎯 **The scanner is now running and monitoring for profitable arbitrage opportunities!**
