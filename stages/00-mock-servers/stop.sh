#!/bin/bash

echo "🛑 Stopping Banking Anomaly Log Simulation System..."
echo ""

# Stop all services
docker-compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "💾 Data volumes preserved. To remove volumes, run:"
echo "   docker-compose down -v"
echo ""
