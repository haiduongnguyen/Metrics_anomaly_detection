#!/bin/bash

set -e

echo "============================================"
echo "Starting Full Pipeline - Stage 00 & 01"
echo "============================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

echo ""
echo "Building and starting all services..."
docker compose up -d --build

echo ""
echo "Waiting for services to be ready..."
sleep 15

# Check LocalStack health
echo ""
echo "Checking LocalStack status..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
        echo "✅ LocalStack is healthy!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "Waiting for LocalStack... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ LocalStack failed to start"
    exit 1
fi

# Check Stage 00 services
echo ""
echo "Checking Stage 00 services..."
services=("scenario-orchestrator:8000" "pattern-generator:8001" "log-synthesis:8002" "state-manager:8003" "ingestion-interface:8004" "log-consolidation:8005")

for service in "${services[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "⚠️  $name is not responding"
    fi
done

echo ""
echo "============================================"
echo "✅ Full Pipeline Started Successfully!"
echo "============================================"
echo ""
echo "Services:"
echo "  Stage 00 - Mock Servers:"
echo "    - Scenario Orchestrator: http://localhost:8000"
echo "    - Pattern Generator: http://localhost:8001"
echo "    - Log Synthesis: http://localhost:8002"
echo "    - State Manager: http://localhost:8003"
echo "    - Ingestion Interface: http://localhost:8004"
echo "    - Log Consolidation: http://localhost:8005"
echo ""
echo "  Stage 01 - Ingestion:"
echo "    - LocalStack: http://localhost:4566"
echo "    - Kinesis Consumer: Running"
echo ""
echo "Monitoring:"
echo "  docker compose logs -f"
echo "  docker compose logs -f kinesis-consumer"
echo "  docker compose logs -f ingestion-interface"
echo ""
echo "Data Flow:"
echo "  Stage 00 → Kinesis (LocalStack) → Consumer → S3 (LocalStack)"
echo ""
echo "Check S3 data:"
echo "  awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566"
echo ""
