#!/bin/bash

# Quick fix for Docker Compose installation on modern Raspberry Pi OS
# Run this to resolve the externally-managed-environment error

echo "🔧 Fixing Docker Compose installation..."

# Method 1: Install Docker Compose plugin (recommended)
echo "📦 Installing Docker Compose plugin..."
if sudo apt install -y docker-compose-plugin; then
    echo "✅ Docker Compose plugin installed successfully"
    
    # Create compatibility wrapper for docker-compose command
    if [ ! -f /usr/local/bin/docker-compose ]; then
        echo "🔗 Creating compatibility wrapper..."
        sudo tee /usr/local/bin/docker-compose > /dev/null << 'EOF'
#!/bin/bash
# Docker Compose compatibility wrapper
docker compose "$@"
EOF
        sudo chmod +x /usr/local/bin/docker-compose
        echo "✅ Compatibility wrapper created"
    fi
    
    # Test installation
    if docker-compose --version &> /dev/null; then
        echo "✅ Docker Compose working correctly"
        docker-compose --version
    else
        echo "⚠️  Using 'docker compose' command instead"
        docker compose version
    fi
    
    echo ""
    echo "🎉 Docker Compose fixed!"
    echo "You can now run: ./manage.sh start"
    
else
    echo "❌ Plugin installation failed, trying binary method..."
    
    # Method 2: Download binary
    echo "📥 Downloading Docker Compose binary..."
    COMPOSE_VERSION="v2.21.0"  # Known working version
    ARCH=$(uname -m)
    
    if [[ $ARCH == "aarch64" ]]; then
        BINARY_ARCH="aarch64"
    elif [[ $ARCH == "armv7l" ]]; then
        BINARY_ARCH="armv7"
    else
        BINARY_ARCH="aarch64"  # Default for Pi
    fi
    
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${BINARY_ARCH}" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    if docker-compose --version &> /dev/null; then
        echo "✅ Docker Compose binary installed successfully"
        docker-compose --version
    else
        echo "❌ Binary installation also failed"
        exit 1
    fi
fi

echo ""
echo "🚀 Ready to start your arbitrage scanner!"
echo "Run: ./manage.sh start"
