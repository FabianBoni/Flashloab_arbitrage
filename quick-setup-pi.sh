#!/bin/bash

# 🚀 One-Click Raspberry Pi Setup for BSC Arbitrage Scanner
# This script handles the complete setup process automatically

set -e  # Exit on any error

echo "🚀 BSC Arbitrage Scanner - Raspberry Pi Setup"
echo "=============================================="
echo ""

# Function to check if running on Raspberry Pi
check_raspberry_pi() {
    if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
        echo "   The script will continue but may need adjustments"
        echo ""
    else
        PI_MODEL=$(cat /proc/device-tree/model | tr -d '\0')
        echo "✅ Detected: $PI_MODEL"
        echo ""
    fi
}

# Function to update system
update_system() {
    echo "📦 Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    echo "✅ System updated"
    echo ""
}

# Function to install Docker
install_docker() {
    echo "🐳 Installing Docker..."
    
    if command -v docker &> /dev/null; then
        echo "✅ Docker already installed: $(docker --version)"
    else
        # Install Docker using official script
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        echo "✅ Docker installed successfully"
        echo "⚠️  You may need to log out and back in for Docker permissions"
    fi
    echo ""
}

# Function to install Docker Compose
install_docker_compose() {
    echo "🔧 Installing Docker Compose..."
    
    # Try multiple methods
    if sudo apt install docker-compose-plugin -y; then
        echo "✅ Docker Compose plugin installed via apt"
    elif command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose already available: $(docker-compose --version)"
    else
        echo "📥 Installing Docker Compose binary..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo "✅ Docker Compose binary installed"
    fi
    echo ""
}

# Function to setup project
setup_project() {
    echo "📁 Setting up project..."
    
    # Make scripts executable
    chmod +x *.sh
    
    # Create logs directory with proper permissions
    mkdir -p logs
    chmod 755 logs
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        echo "📝 Creating default .env file..."
        cat > .env << 'EOF'
# BSC Configuration
BSC_RPC_URL=https://bsc-dataseed1.binance.org/
SCAN_INTERVAL=10

# Profit Thresholds
MIN_PROFIT_THRESHOLD=0.008

# Telegram Notifications (optional - replace with your values)
# TELEGRAM_BOT_TOKEN=your_bot_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration (optional - for real trading only)
# PRIVATE_KEY=your_private_key_here

# Logging
LOG_LEVEL=INFO
EOF
        echo "✅ Created default .env file"
        echo "📝 Edit .env to add your Telegram bot token and private key if needed"
    else
        echo "✅ .env file already exists"
    fi
    echo ""
}

# Function to test Docker setup
test_docker() {
    echo "🧪 Testing Docker installation..."
    
    # Test Docker
    if docker run --rm hello-world > /dev/null 2>&1; then
        echo "✅ Docker working correctly"
    else
        echo "❌ Docker test failed"
        echo "💡 Try: sudo usermod -aG docker $USER && sudo reboot"
        return 1
    fi
    
    # Test Docker Compose
    if command -v docker-compose &> /dev/null; then
        echo "✅ docker-compose command available"
    elif docker compose version &> /dev/null 2>&1; then
        echo "✅ docker compose (plugin) available"
    else
        echo "❌ Docker Compose not working"
        return 1
    fi
    echo ""
}

# Function to build and start
build_and_start() {
    echo "🔨 Building and starting BSC Arbitrage Scanner..."
    
    # Build the Docker image
    echo "🏗️  Building Docker image..."
    if command -v docker-compose &> /dev/null; then
        docker-compose build
    else
        docker compose build
    fi
    
    echo "🚀 Starting the scanner..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    echo "✅ Scanner started successfully!"
    echo ""
}

# Function to show status and next steps
show_status() {
    echo "📊 Current Status:"
    echo "=================="
    
    # Show container status
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
    
    echo ""
    echo "🎯 Next Steps:"
    echo "=============="
    echo "1. View logs:    ./manage.sh logs"
    echo "2. Check status: ./manage.sh status"
    echo "3. Stop scanner: ./manage.sh stop"
    echo "4. Edit config:  nano .env"
    echo ""
    echo "📱 To enable Telegram notifications:"
    echo "   - Create a Telegram bot (@BotFather)"
    echo "   - Add TELEGRAM_BOT_TOKEN to .env"
    echo "   - Add TELEGRAM_CHAT_ID to .env"
    echo ""
    echo "💰 To enable trading (ADVANCED):"
    echo "   - Add PRIVATE_KEY to .env"
    echo "   - Ensure sufficient BNB for gas"
    echo "   - Restart: ./manage.sh restart"
    echo ""
    echo "✅ Setup complete! The scanner is monitoring for arbitrage opportunities."
}

# Main execution
main() {
    check_raspberry_pi
    
    echo "🔧 This script will:"
    echo "   1. Update system packages"
    echo "   2. Install Docker and Docker Compose"
    echo "   3. Setup the BSC arbitrage scanner"
    echo "   4. Start monitoring for opportunities"
    echo ""
    
    read -p "Continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    echo ""
    
    update_system
    install_docker
    install_docker_compose
    setup_project
    
    if test_docker; then
        build_and_start
        show_status
    else
        echo "❌ Docker setup failed. Please check the installation and try again."
        echo "💡 You may need to reboot and run this script again."
        exit 1
    fi
}

# Run main function
main "$@"
