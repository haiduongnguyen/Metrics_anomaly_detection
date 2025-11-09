#!/bin/bash

set -e

echo "============================================"
echo "Stopping Full Pipeline"
echo "============================================"

echo ""
echo "Stopping all services..."
docker compose down

echo ""
echo "============================================"
echo "✅ Full Pipeline Stopped!"
echo "============================================"
echo ""
echo "Note: Data is persisted in Docker volumes"
echo "To remove all data: docker compose down -v"
echo ""
