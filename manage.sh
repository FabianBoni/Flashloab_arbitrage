#!/bin/bash

# BSC Arbitrage Docker Management Script
# Manages Docker containers and services for Linux/Unix

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emoji support
CHECK="✅"
CROSS="❌"
ROCKET="🚀"
STOP="🛑"
INFO="📊"
LOGS="📋"
BUILD="🔨"
SHELL="🐚"
CLEAN="🧹"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} BSC ARBITRAGE DOCKER MANAGER${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_menu() {
    echo -e "${BLUE}Docker Management Options:${NC}"
    echo -e "${BLUE}-------------------------${NC}"
    echo "1. ${BUILD} Build Image"
    echo "2. ${ROCKET} Start Services"
    echo "3. ${STOP} Stop Services"
    echo "4. 🔄 Restart Services"
    echo "5. ${INFO} Show Status"
    echo "6. ${LOGS} Show Logs"
    echo "7. ${SHELL} Shell Access"
    echo "8. ${CLEAN} Cleanup"
    echo "9. 🔍 Check Docker"
    echo "0. ${CROSS} Exit"
    echo -e "${BLUE}-------------------------${NC}"
}

check_docker() {
    echo -e "${INFO} Checking Docker installation..."
    
    # Check Docker installation
    if ! command -v docker &> /dev/null; then
        echo -e "${CROSS} Docker is not installed"
        echo "💡 Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo -e "${CHECK} Docker found: $(docker --version)"
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        echo -e "${CROSS} Docker daemon is not running"
        echo "💡 Start Docker service: sudo systemctl start docker"
        exit 1
    fi
    
    echo -e "${CHECK} Docker daemon is running"
    
    # Check Docker Compose
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo -e "${CHECK} Docker Compose found: $(docker compose version --short)"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo -e "${CHECK} Docker Compose found: $(docker-compose --version)"
    else
        echo -e "${CROSS} Docker Compose is not available"
        echo "💡 Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

build_image() {
    echo -e "${BUILD} Building Docker image..."
    
    if [ ! -f "Dockerfile" ]; then
        echo -e "${CROSS} Dockerfile not found"
        return 1
    fi
    
    if docker build -t bsc-arbitrage .; then
        echo -e "${CHECK} Docker image built successfully"
    else
        echo -e "${CROSS} Docker image build failed"
        return 1
    fi
}

start_services() {
    echo -e "${ROCKET} Starting Docker services..."
    
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${CROSS} docker-compose.yml not found"
        return 1
    fi
    
    # Stop any existing containers first
    $COMPOSE_CMD down &> /dev/null || true
    
    # Start services
    if $COMPOSE_CMD up -d; then
        echo -e "${CHECK} Docker services started"
        sleep 2
        show_status
    else
        echo -e "${CROSS} Failed to start Docker services"
        return 1
    fi
}

stop_services() {
    echo -e "${STOP} Stopping Docker services..."
    
    if $COMPOSE_CMD down; then
        echo -e "${CHECK} Docker services stopped"
    else
        echo -e "${CROSS} Failed to stop Docker services"
        return 1
    fi
}

restart_services() {
    echo -e "🔄 Restarting Docker services..."
    
    if $COMPOSE_CMD restart; then
        echo -e "${CHECK} Docker services restarted"
        sleep 2
        show_status
    else
        echo -e "${CROSS} Failed to restart Docker services"
        return 1
    fi
}

show_status() {
    echo -e "${INFO} Docker Services Status:"
    echo "------------------------"
    
    # Show running containers
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Show compose services if compose file exists
    if [ -f "docker-compose.yml" ]; then
        echo ""
        echo -e "${LOGS} Compose Services:"
        $COMPOSE_CMD ps
    fi
}

show_logs() {
    echo -e "${LOGS} Docker Logs:"
    echo "Press Ctrl+C to stop following logs..."
    echo "-----------------------------------"
    
    read -p "Enter service name (or press Enter for all): " service
    
    if [ -z "$service" ]; then
        $COMPOSE_CMD logs -f
    else
        $COMPOSE_CMD logs -f "$service"
    fi
}

shell_access() {
    echo -e "${SHELL} Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    echo ""
    
    read -p "Enter container name (or press Enter for 'bsc-arbitrage-scanner'): " container
    if [ -z "$container" ]; then
        container="bsc-arbitrage-scanner"
    fi
    
    echo -e "${SHELL} Accessing $container shell..."
    
    if docker exec -it "$container" /bin/bash 2>/dev/null; then
        echo "Shell session ended"
    elif docker exec -it "$container" /bin/sh 2>/dev/null; then
        echo "Shell session ended"
    else
        echo -e "${CROSS} Failed to access container shell"
        echo "💡 Make sure the container is running"
    fi
}

cleanup() {
    echo -e "${CLEAN} Docker cleanup:"
    echo "This will remove:"
    echo "- Stopped containers"
    echo "- Unused networks"
    echo "- Dangling images"
    echo ""
    
    read -p "Continue? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo "Cleaning up..."
        
        # Remove stopped containers
        docker container prune -f
        
        # Remove unused networks
        docker network prune -f
        
        # Remove dangling images
        docker image prune -f
        
        echo -e "${CHECK} Docker cleanup completed"
    else
        echo -e "${CROSS} Cleanup cancelled"
    fi
}

main() {
    print_header
    
    # Check Docker installation
    check_docker
    echo ""
    
    while true; do
        print_menu
        echo ""
        read -p "👉 Select option (0-9): " choice
        echo ""
        
        case $choice in
            1)
                build_image
                ;;
            2)
                start_services
                ;;
            3)
                stop_services
                ;;
            4)
                restart_services
                ;;
            5)
                show_status
                ;;
            6)
                show_logs
                ;;
            7)
                shell_access
                ;;
            8)
                cleanup
                ;;
            9)
                check_docker
                ;;
            0)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo -e "${CROSS} Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        if [[ $choice != 6 ]]; then  # Don't pause after logs (they're interactive)
            read -p "Press Enter to continue..."
        fi
        echo ""
    done
}

# Run main function
main "$@"
