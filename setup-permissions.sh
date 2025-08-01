#!/bin/bash

# Setup script for fixing Docker permissions on Raspberry Pi
echo "🔧 Setting up BSC Arbitrage Scanner permissions..."

# Create logs directory on host if it doesn't exist
if [ ! -d "./logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p ./logs
    chmod 755 ./logs
fi

# Create empty log file if it doesn't exist
if [ ! -f "./logs/arbitrage.log" ]; then
    echo "📄 Creating arbitrage.log file..."
    touch ./logs/arbitrage.log
    chmod 666 ./logs/arbitrage.log  # Allow read/write for all users
fi

# Fix ownership if running as root
if [ "$EUID" -eq 0 ]; then
    echo "🔐 Fixing ownership (running as root)..."
    # Get the regular user (not root)
    REAL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
    if [ ! -z "$REAL_USER" ] && [ "$REAL_USER" != "root" ]; then
        chown -R $REAL_USER:$REAL_USER ./logs
        echo "✅ Changed ownership to $REAL_USER"
    fi
fi

echo "✅ Permissions setup complete!"
echo ""
echo "📋 Directory structure:"
ls -la ./logs/ 2>/dev/null || echo "⚠️  Logs directory not accessible"

echo ""
echo "🚀 You can now run:"
echo "   docker-compose up -d"
echo "   ./manage.sh start"
