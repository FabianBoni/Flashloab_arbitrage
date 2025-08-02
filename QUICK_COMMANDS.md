# 🚀 Copy & Paste Commands for Raspberry Pi Setup

## Method 1: One-Click Setup (Recommended)

# 1. Clone the repository
cd ~
git clone https://github.com/FabianBoni/Flashloab_arbitrage.git
cd Flashloab_arbitrage

# 2. Run the one-click setup
chmod +x quick-setup-pi.sh
./quick-setup-pi.sh

# 3. View logs
./manage.sh logs

## Method 2: Manual Setup (if one-click fails)

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Install Docker Compose
sudo apt install docker-compose-plugin -y

# 4. Reboot (important for Docker permissions)
sudo reboot

# 5. After reboot, clone and setup
cd ~
git clone https://github.com/FabianBoni/Flashloab_arbitrage.git
cd Flashloab_arbitrage
chmod +x *.sh

# 6. Setup and start
./manage.sh setup
docker compose build
./manage.sh start

# 7. View logs
./manage.sh logs

## Useful Commands

# View live logs
./manage.sh logs

# Check status
./manage.sh status

# Stop scanner
./manage.sh stop

# Restart scanner
./manage.sh restart

# Edit configuration
nano .env

# Clean and rebuild
./manage.sh clean
docker compose build
./manage.sh start

## Expected Output
You should see:
- Connection to BSC network
- Token prices from DEXes
- Price spreads between exchanges
- Arbitrage opportunities (if any)
- Memory optimizations for Pi

## Troubleshooting

# If "docker-compose: command not found"
sudo apt install docker-compose-plugin -y

# If permission errors
sudo chown -R $USER:$USER .
chmod +x *.sh

# If Docker permission denied
sudo usermod -aG docker $USER
sudo reboot

# Check Docker status
docker --version
docker compose version
docker ps

# Manual container start if needed
docker run -d --name bsc-arbitrage-scanner --restart unless-stopped -v $(pwd)/.env:/home/arbitrage/app/.env:ro bsc-arbitrage
