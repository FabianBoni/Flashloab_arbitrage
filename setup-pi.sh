#!/bin/bash

# BSC Arbitrage Scanner - Raspberry Pi Setup Script
# This script sets up everything needed to run the arbitrage scanner

set -e

echo "🚀 BSC Arbitrage Scanner - Raspberry Pi Setup"
echo "=============================================="

# Check if running on Raspberry Pi
if [[ $(uname -m) == "arm"* ]] || [[ $(uname -m) == "aarch64" ]]; then
    echo "✅ Raspberry Pi detected"
else
    echo "⚠️  Warning: Not running on Raspberry Pi architecture"
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    sudo pip3 install docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo "✅ Configuration file created (.env)"
    echo "📝 Edit .env file to customize settings"
else
    echo "✅ Configuration file already exists"
fi

# Create logs directory
mkdir -p logs
chmod 755 logs

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Quick Start Commands:"
echo "  Start scanner:  docker-compose up -d"
echo "  View logs:      docker-compose logs -f"
echo "  Stop scanner:   docker-compose down"
echo ""
echo "📝 Configuration:"
echo "  Edit settings:  nano .env"
echo "  View readme:    cat README-Docker.md"
echo ""
echo "⚠️  Default mode: MONITORING ONLY (no trading)"
echo "💡 Add PRIVATE_KEY to .env to enable trading"
echo ""
echo "🔄 Starting scanner in 5 seconds..."
sleep 5

# Start the scanner
docker-compose up -d

echo "✅ Scanner started! Use 'docker-compose logs -f' to view logs"
