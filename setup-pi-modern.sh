#!/bin/bash

# BSC Arbitrage Scanner - Modern Raspberry Pi Setup Script
# Handles externally managed Python environments properly

set -e

echo "🚀 BSC Arbitrage Scanner - Modern Raspberry Pi Setup"
echo "====================================================="

# Check if running on Raspberry Pi
if [[ $(uname -m) == "arm"* ]] || [[ $(uname -m) == "aarch64" ]]; then
    echo "✅ Raspberry Pi detected"
else
    echo "⚠️  Warning: Not running on Raspberry Pi architecture"
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install required system packages
echo "🔧 Installing required packages..."
sudo apt install -y curl git python3-full python3-venv

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed"
    echo "⚠️  Please log out and back in for Docker permissions to take effect"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose using modern methods
echo "🔧 Installing Docker Compose..."

# Method 1: Try Docker Compose plugin (preferred)
if sudo apt install -y docker-compose-plugin 2>/dev/null; then
    echo "✅ Docker Compose plugin installed"
    # Create symlink for compatibility
    if [ ! -f /usr/local/bin/docker-compose ]; then
        sudo ln -sf /usr/bin/docker /usr/local/bin/docker-compose
        echo '#!/bin/bash\ndocker compose "$@"' | sudo tee /usr/local/bin/docker-compose > /dev/null
        sudo chmod +x /usr/local/bin/docker-compose
    fi
elif command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose already available"
else
    # Method 2: Download binary directly
    echo "📥 Downloading Docker Compose binary..."
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4 2>/dev/null || echo "v2.21.0")
    ARCH=$(uname -m)
    if [[ $ARCH == "aarch64" ]]; then
        ARCH="aarch64"
    elif [[ $ARCH == "armv7l" ]]; then
        ARCH="armv7"
    fi
    
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH}" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose binary installed"
fi

# Verify Docker Compose installation
if docker-compose --version &> /dev/null || docker compose version &> /dev/null; then
    echo "✅ Docker Compose working correctly"
else
    echo "❌ Docker Compose installation failed"
    exit 1
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

# Create logs directory with proper permissions
mkdir -p logs
chmod 755 logs

# Make management script executable
chmod +x manage.sh

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Quick Start Commands:"
echo "  Start scanner:  ./manage.sh start"
echo "  View logs:      ./manage.sh logs"
echo "  Stop scanner:   ./manage.sh stop"
echo ""
echo "📝 Configuration:"
echo "  Edit settings:  ./manage.sh config"
echo "  View help:      ./manage.sh help"
echo ""
echo "⚠️  Default mode: MONITORING ONLY (no trading)"
echo "💡 Add PRIVATE_KEY to .env to enable trading"
echo ""

# Check if user is in docker group
if groups $USER | grep -q '\bdocker\b'; then
    echo "✅ Docker permissions configured"
    echo "🔄 Starting scanner in 5 seconds..."
    sleep 5
    ./manage.sh start
    echo ""
    echo "✅ Scanner started! Use './manage.sh logs' to view logs"
else
    echo "⚠️  Docker permissions not yet active"
    echo "📝 Please run: newgrp docker"
    echo "   Then start with: ./manage.sh start"
fi
