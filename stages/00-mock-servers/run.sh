#!/bin/bash
set -e

# Minimal quick start script for Banking Mock Server

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

# Get compose command
if command -v docker compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

case $1 in
    "start"|"")
        print_info "Starting Banking Mock Server..."
        $COMPOSE_CMD up -d
        print_success "Mock server started!"
        echo
        echo "🚀 Server is running at: http://localhost:8000"
        echo "❤️  Health check: http://localhost:8000/health"
        echo
        echo "Control API:"
        echo "  Start: curl -X POST http://localhost:8000/control -H 'Content-Type: application/json' -d '{\"action\":\"start\"}'"
        echo "  Stop:  curl -X POST http://localhost:8000/control -H 'Content-Type: application/json' -d '{\"action\":\"stop\"}'"
        echo
        ;;
    "stop")
        print_info "Stopping mock server..."
        $COMPOSE_CMD down
        print_success "Mock server stopped!"
        ;;
    "logs")
        $COMPOSE_CMD logs -f
        ;;
    "status")
        $COMPOSE_CMD ps
        ;;
    "clean")
        print_info "Cleaning up..."
        $COMPOSE_CMD down -v
        docker system prune -f
        print_success "Cleanup complete!"
        ;;
    *)
        echo "Usage: $0 [start|stop|logs|status|clean]"
        echo
        echo "Commands:"
        echo "  start   Start the mock server (default)"
        echo "  stop    Stop the mock server"
        echo "  logs    Show logs"
        echo "  status  Show service status"
        echo "  clean   Remove containers and volumes"
        exit 1
        ;;
esac
