#!/bin/bash

set -e

echo "============================================"
echo "Stopping Stage 01 - Ingestion Layer"
echo "============================================"

echo ""
echo "Stopping LocalStack container..."
docker compose down

echo ""
echo "============================================"
echo "✅ Stage 01 stopped successfully!"
echo "============================================"
echo ""
echo "Note: Data is persisted in Docker volume 'localstack-data'"
echo "To remove data: docker volume rm 01-ingestion_localstack-data"
echo ""
