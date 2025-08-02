#!/bin/bash

# 📋 Log Management Script for BSC Arbitrage Scanner

echo "📋 BSC Arbitrage Scanner - Log Management"
echo "========================================"
echo ""

# Function to detect Docker Compose command
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "❌ Docker Compose not found!"
        exit 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

case ${1:-status} in
    "live"|"follow"|"tail")
        echo "📺 Showing live logs (Ctrl+C to exit)..."
        echo ""
        $COMPOSE_CMD logs -f bsc-arbitrage
        ;;
    
    "last"|"recent")
        echo "📄 Showing last 100 log lines..."
        echo ""
        $COMPOSE_CMD logs --tail=100 bsc-arbitrage
        ;;
    
    "file")
        echo "📁 Checking for log files..."
        echo ""
        
        # Check host logs directory
        if [ -d "./logs" ]; then
            echo "✅ Host logs directory exists:"
            ls -la ./logs/
            echo ""
            
            if [ -f "./logs/arbitrage.log" ]; then
                echo "📄 Content of arbitrage.log (last 20 lines):"
                tail -20 ./logs/arbitrage.log
            else
                echo "❌ No arbitrage.log file found in host directory"
            fi
        else
            echo "❌ Host logs directory doesn't exist"
        fi
        
        # Check container logs
        echo ""
        echo "🐳 Checking container for log files..."
        if docker ps --format "table {{.Names}}" | grep -q "bsc-arbitrage-scanner"; then
            echo "✅ Container is running"
            
            # Check if logs directory exists in container
            docker exec bsc-arbitrage-scanner ls -la logs/ 2>/dev/null || echo "❌ No logs directory in container"
            
            # Check if log file exists in container
            if docker exec bsc-arbitrage-scanner test -f logs/arbitrage.log 2>/dev/null; then
                echo "✅ Log file exists in container"
                echo "📄 Last 10 lines from container log file:"
                docker exec bsc-arbitrage-scanner tail -10 logs/arbitrage.log
            else
                echo "❌ No log file in container (probably permission issues - using console only)"
            fi
        else
            echo "❌ Container is not running"
        fi
        ;;
    
    "export")
        timestamp=$(date +"%Y%m%d_%H%M%S")
        log_file="arbitrage_logs_${timestamp}.txt"
        
        echo "💾 Exporting all logs to: $log_file"
        echo ""
        
        # Export Docker container logs
        $COMPOSE_CMD logs bsc-arbitrage > "$log_file"
        
        echo "✅ Logs exported to: $log_file"
        echo "📊 File size: $(du -h "$log_file" | cut -f1)"
        ;;
    
    "clear")
        echo "🧹 Clearing Docker container logs..."
        echo ""
        
        read -p "Are you sure you want to clear all container logs? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Stop and recreate container to clear logs
            $COMPOSE_CMD stop bsc-arbitrage
            docker container rm bsc-arbitrage-scanner 2>/dev/null || true
            $COMPOSE_CMD up -d bsc-arbitrage
            echo "✅ Logs cleared and container restarted"
        else
            echo "❌ Operation cancelled"
        fi
        ;;
    
    "size")
        echo "📊 Log size information..."
        echo ""
        
        # Docker container logs
        if docker ps --format "table {{.Names}}" | grep -q "bsc-arbitrage-scanner"; then
            container_log_path=$(docker inspect bsc-arbitrage-scanner --format='{{.LogPath}}' 2>/dev/null)
            if [ -n "$container_log_path" ] && [ -f "$container_log_path" ]; then
                echo "🐳 Docker container logs: $(du -h "$container_log_path" | cut -f1)"
            else
                echo "🐳 Docker container logs: Not accessible"
            fi
        else
            echo "🐳 Container not running"
        fi
        
        # Host log files
        if [ -d "./logs" ]; then
            echo "📁 Host logs directory: $(du -sh ./logs | cut -f1)"
            if [ -f "./logs/arbitrage.log" ]; then
                echo "📄 arbitrage.log: $(du -h ./logs/arbitrage.log | cut -f1)"
            fi
        fi
        ;;
    
    "status"|*)
        echo "📊 Log Status Overview"
        echo "====================="
        echo ""
        
        # Container status
        if docker ps --format "table {{.Names}}" | grep -q "bsc-arbitrage-scanner"; then
            echo "✅ Container: Running"
            
            # Check last log entry time
            last_log=$(docker logs --tail=1 bsc-arbitrage-scanner 2>/dev/null | head -1)
            if [ -n "$last_log" ]; then
                echo "📅 Last log entry: $(echo "$last_log" | cut -d' ' -f1-2)"
            fi
        else
            echo "❌ Container: Not running"
        fi
        
        # Host logs
        if [ -d "./logs" ]; then
            echo "✅ Host logs directory: Exists"
            if [ -f "./logs/arbitrage.log" ]; then
                echo "✅ Log file: Exists ($(du -h ./logs/arbitrage.log | cut -f1))"
                echo "📅 Last modified: $(stat -c %y ./logs/arbitrage.log)"
            else
                echo "❌ Log file: Not found (using console logs only)"
            fi
        else
            echo "❌ Host logs directory: Not found"
        fi
        
        echo ""
        echo "🔧 Available commands:"
        echo "  ./logs.sh live     - View live logs (follow mode)"
        echo "  ./logs.sh last     - Show last 100 lines"
        echo "  ./logs.sh file     - Check log files"
        echo "  ./logs.sh export   - Export logs to file"
        echo "  ./logs.sh size     - Show log sizes"
        echo "  ./logs.sh clear    - Clear logs"
        ;;
esac
