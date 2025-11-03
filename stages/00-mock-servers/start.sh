#!/bin/bash

echo "🚀 Starting Banking Anomaly Log Simulation System..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build and start services
echo "📦 Building and starting services..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

services=("scenario-orchestrator:8000" "pattern-generator:8001" "log-synthesis:8002" "state-manager:8003" "ingestion-interface:8004")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -f http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name is healthy (port $port)"
    else
        echo "⚠️  $name is not responding yet (port $port)"
    fi
done

echo ""
echo "🎉 System is starting up!"
echo ""
echo "📍 Access the services:"
echo "   • Scenario Orchestrator: http://localhost:8000"
echo "   • Pattern Generator:     http://localhost:8001"
echo "   • Log Synthesis Engine:  http://localhost:8002"
echo "   • State Manager:         http://localhost:8003"
echo "   • Ingestion Interface:   http://localhost:8004"
echo ""
echo "📚 API Documentation:"
echo "   • http://localhost:8000/docs"
echo "   • http://localhost:8001/docs"
echo "   • http://localhost:8002/docs"
echo "   • http://localhost:8003/docs"
echo "   • http://localhost:8004/docs"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop system: docker-compose down"
echo ""
