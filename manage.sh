#!/bin/bash

# BSC Arbitrage Scanner - Docker Management Script
# Simple commands to manage your arbitrage scanner

ACTION=${1:-help}

case $ACTION in
    "start")
        echo "🚀 Starting BSC Arbitrage Scanner..."
        docker-compose up -d
        echo "✅ Scanner started!"
        echo "📋 Use './manage.sh logs' to view output"
        ;;
    
    "stop")
        echo "🛑 Stopping BSC Arbitrage Scanner..."
        docker-compose down
        echo "✅ Scanner stopped!"
        ;;
    
    "restart")
        echo "🔄 Restarting BSC Arbitrage Scanner..."
        docker-compose restart
        echo "✅ Scanner restarted!"
        ;;
    
    "logs")
        echo "📋 Showing live logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    
    "status")
        echo "📊 Container Status:"
        docker-compose ps
        echo ""
        echo "💾 Resource Usage:"
        docker stats --no-stream bsc-arbitrage-scanner 2>/dev/null || echo "Container not running"
        ;;
    
    "update")
        echo "⬇️ Updating application..."
        git pull
        echo "🔨 Rebuilding container..."
        docker-compose up -d --build
        echo "✅ Update complete!"
        ;;
    
    "config")
        echo "⚙️ Opening configuration file..."
        nano .env
        echo "🔄 Restart scanner to apply changes: ./manage.sh restart"
        ;;
    
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker-compose down
        docker system prune -f
        echo "✅ Cleanup complete!"
        ;;
    
    "install")
        echo "📦 Installing BSC Arbitrage Scanner..."
        chmod +x setup-pi.sh
        ./setup-pi.sh
        ;;
    
    "backup")
        BACKUP_FILE="arbitrage-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        echo "💾 Creating backup: $BACKUP_FILE"
        tar -czf "$BACKUP_FILE" .env logs/ --exclude='logs/*.log.*'
        echo "✅ Backup created: $BACKUP_FILE"
        ;;
    
    "help"|*)
        echo "🤖 BSC Arbitrage Scanner - Management Commands"
        echo "=============================================="
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
        echo "Setup:"
        echo "  ./manage.sh install   - Full Raspberry Pi setup"
        echo ""
        echo "💡 Default mode: MONITORING (no trading)"
        echo "🔑 Add PRIVATE_KEY to .env to enable trading"
        ;;
esac
