#!/bin/bash

# BSC Arbitrage Scanner - Docker Management Script
# Compatible with both docker-compose and docker compose

ACTION=${1:-help}

# Function to detect and use correct Docker Compose command
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "❌ Docker Compose not found!"
        echo "Please install Docker Compose first"
        exit 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

case $ACTION in
    "start")
        echo "🚀 Starting BSC Arbitrage Scanner..."
        
        # Setup permissions first
        if [ -f "./setup-permissions.sh" ]; then
            echo "🔧 Setting up permissions..."
            chmod +x ./setup-permissions.sh
            ./setup-permissions.sh
        fi
        
        $COMPOSE_CMD up -d
        echo "✅ Scanner started!"
        echo "📋 Use './manage.sh logs' to view output"
        ;;
    
    "setup")
        echo "🔧 Setting up permissions and directories..."
        chmod +x ./setup-permissions.sh
        ./setup-permissions.sh
        echo "✅ Setup complete!"
        ;;
    
    "stop")
        echo "🛑 Stopping BSC Arbitrage Scanner..."
        $COMPOSE_CMD down
        echo "✅ Scanner stopped!"
        ;;
    
    "restart")
        echo "🔄 Restarting BSC Arbitrage Scanner..."
        $COMPOSE_CMD restart
        echo "✅ Scanner restarted!"
        ;;
    
    "logs")
        echo "📋 Showing live logs (Ctrl+C to exit)..."
        $COMPOSE_CMD logs -f
        ;;
    
    "status")
        echo "📊 Container Status:"
        $COMPOSE_CMD ps
        echo ""
        echo "💾 Resource Usage:"
        docker stats --no-stream bsc-arbitrage-scanner 2>/dev/null || echo "Container not running"
        ;;
    
    "update")
        echo "⬇️ Updating application..."
        git pull
        echo "🔨 Rebuilding container..."
        $COMPOSE_CMD up -d --build
        echo "✅ Update complete!"
        ;;
    
    "config")
        echo "⚙️ Opening configuration file..."
        nano .env
        echo "🔄 Restart scanner to apply changes: ./manage.sh restart"
        ;;
    
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        $COMPOSE_CMD down
        docker system prune -f
        echo "✅ Cleanup complete!"
        ;;
    
    "install")
        echo "📦 Installing BSC Arbitrage Scanner..."
        chmod +x setup-pi-modern.sh
        ./setup-pi-modern.sh
        ;;
    
    "backup")
        BACKUP_FILE="arbitrage-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        echo "💾 Creating backup: $BACKUP_FILE"
        tar -czf "$BACKUP_FILE" .env logs/ --exclude='logs/*.log.*'
        echo "✅ Backup created: $BACKUP_FILE"
        ;;
    
    "compose-test")
        echo "🧪 Testing Docker Compose..."
        echo "Using command: $COMPOSE_CMD"
        $COMPOSE_CMD version
        ;;
    
    "help"|*)
        echo "🤖 BSC Arbitrage Scanner - Management Commands"
        echo "=============================================="
        echo "Using: $COMPOSE_CMD"
        echo ""
        echo "Basic Operations:"
        echo "  ./manage.sh start     - Start the scanner"
        echo "  ./manage.sh stop      - Stop the scanner"
        echo "  ./manage.sh restart   - Restart the scanner"
        echo "  ./manage.sh logs      - View live logs"
        echo "  ./manage.sh status    - Check status and resources"
        echo ""
        echo "Maintenance:"
        echo "  ./manage.sh update    - Update and rebuild"
        echo "  ./manage.sh config    - Edit configuration"
        echo "  ./manage.sh clean     - Clean Docker resources"
        echo "  ./manage.sh backup    - Backup configuration and logs"
        echo ""
        echo "Setup & Testing:"
        echo "  ./manage.sh setup        - Setup permissions and directories"
        echo "  ./manage.sh install      - Full Raspberry Pi setup"
        echo "  ./manage.sh compose-test - Test Docker Compose"
        echo ""
        echo "💡 Default mode: MONITORING (no trading)"
        echo "🔑 Add PRIVATE_KEY to .env to enable trading"
        ;;
esac
