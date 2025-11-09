#!/bin/bash

set -e

echo "============================================"
echo "Starting Stage 01 - Ingestion Layer"
echo "============================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if LocalStack is already running
if docker ps --filter "name=localstack" --filter "status=running" | grep -q localstack; then
    LOCALSTACK_CONTAINER=$(docker ps --filter "name=localstack" --filter "status=running" --format "{{.Names}}" | head -1)
    echo "✅ Found running LocalStack container: $LOCALSTACK_CONTAINER"
    echo "   Using existing LocalStack on port 4566"
    USE_EXISTING=true
else
    echo "⚠️  No running LocalStack found"
    echo "   Will start dedicated LocalStack for stage 01"
    USE_EXISTING=false
fi

# Check if anomaly-network exists
if ! docker network inspect anomaly-network > /dev/null 2>&1; then
    echo "⚠️  Network 'anomaly-network' not found"
    echo "   Creating network..."
    docker network create anomaly-network
    echo "✅ Network created"
fi

echo ""
if [ "$USE_EXISTING" = true ]; then
    echo "Using existing LocalStack - no new containers to start"
    
    # Connect existing LocalStack to anomaly-network if not already connected
    if ! docker inspect $LOCALSTACK_CONTAINER --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' | grep -q anomaly-network; then
        echo "Connecting $LOCALSTACK_CONTAINER to anomaly-network..."
        docker network connect anomaly-network $LOCALSTACK_CONTAINER 2>/dev/null || echo "Already connected"
    fi
else
    echo "Starting dedicated LocalStack container..."
    docker compose -f docker-compose.standalone.yml up -d
    sleep 10
fi

# Wait for LocalStack health check
echo ""
echo "Waiting for LocalStack to be ready..."
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
    echo "❌ LocalStack failed to respond"
    echo "Check if LocalStack is running: docker ps | grep localstack"
    exit 1
fi

# Initialize AWS resources
echo ""
echo "Initializing AWS resources in LocalStack..."
if [ -f "./localstack-init/01-setup-resources.sh" ]; then
    bash ./localstack-init/01-setup-resources.sh
fi

echo ""
echo "============================================"
echo "✅ Stage 01 started successfully!"
echo "============================================"
echo ""
echo "Services:"
if [ "$USE_EXISTING" = true ]; then
    echo "  - LocalStack: http://localhost:4566 (using existing: $LOCALSTACK_CONTAINER)"
else
    echo "  - LocalStack: http://localhost:4566 (dedicated: localstack-stage01)"
fi
echo ""
echo "Health Check:"
echo "  curl http://localhost:4566/_localstack/health"
echo ""
echo "AWS Resources:"
echo "  awslocal s3 ls"
echo "  awslocal kinesis list-streams"
echo ""
echo "Next Steps:"
echo "  1. Run Terraform to provision infrastructure"
echo "  2. Configure Stage 00 to send data to Kinesis"
echo ""
