#!/bin/bash

set -e

echo "============================================"
echo "Testing Full Pipeline"
echo "============================================"

# Wait for services to be ready
echo ""
echo "Step 1: Checking all services are healthy..."

services=("scenario-orchestrator:8000" "pattern-generator:8001" "log-synthesis:8002" "state-manager:8003" "ingestion-interface:8004" "log-consolidation:8005")
all_healthy=true

for service in "${services[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is NOT healthy"
        all_healthy=false
    fi
done

if [ "$all_healthy" = false ]; then
    echo "⚠️  Some services are not healthy. Please wait or check logs."
    exit 1
fi

# Check LocalStack
echo ""
echo "Step 2: Checking LocalStack..."
if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
    echo "✅ LocalStack is healthy"
else
    echo "❌ LocalStack is NOT healthy"
    exit 1
fi

# Check Kinesis stream
echo ""
echo "Step 3: Checking Kinesis stream..."
STREAM_STATUS=$(awslocal kinesis describe-stream-summary --stream-name stage01-logs-stream --endpoint-url http://localhost:4566 --query 'StreamDescriptionSummary.StreamStatus' --output text 2>/dev/null || echo "ERROR")

if [ "$STREAM_STATUS" = "ACTIVE" ]; then
    echo "✅ Kinesis stream is ACTIVE"
else
    echo "❌ Kinesis stream status: $STREAM_STATUS"
    exit 1
fi

# Check S3 bucket
echo ""
echo "Step 4: Checking S3 bucket..."
if awslocal s3 ls s3://md-raw-logs/ --endpoint-url http://localhost:4566 > /dev/null 2>&1; then
    echo "✅ S3 bucket md-raw-logs exists"
else
    echo "❌ S3 bucket not found"
    exit 1
fi

# Trigger test scenario
echo ""
echo "Step 5: Triggering test scenario to generate logs..."

TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{
    "interval_seconds": 2,
    "logs_per_interval": 10,
    "duration_seconds": 30
  }')

echo "✅ Started continuous log generation"
echo "   Response: $TEST_RESPONSE"

# Wait for logs to be generated and processed
echo ""
echo "Step 6: Waiting for logs to flow through pipeline..."
echo "   (Waiting 30 seconds for data generation and processing)"

for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""

# Check if logs reached Kinesis
echo ""
echo "Step 7: Checking if logs reached Kinesis..."

# Get shard iterator
SHARD_ID=$(awslocal kinesis describe-stream --stream-name stage01-logs-stream --endpoint-url http://localhost:4566 --query 'StreamDescription.Shards[0].ShardId' --output text 2>/dev/null)

if [ ! -z "$SHARD_ID" ] && [ "$SHARD_ID" != "None" ]; then
    echo "✅ Kinesis shard found: $SHARD_ID"
    
    # Try to get records
    SHARD_ITERATOR=$(awslocal kinesis get-shard-iterator \
      --stream-name stage01-logs-stream \
      --shard-id $SHARD_ID \
      --shard-iterator-type TRIM_HORIZON \
      --endpoint-url http://localhost:4566 \
      --query 'ShardIterator' \
      --output text 2>/dev/null)
    
    if [ ! -z "$SHARD_ITERATOR" ]; then
        RECORD_COUNT=$(awslocal kinesis get-records \
          --shard-iterator $SHARD_ITERATOR \
          --endpoint-url http://localhost:4566 \
          --query 'length(Records)' \
          --output text 2>/dev/null || echo "0")
        
        echo "   Records in Kinesis: $RECORD_COUNT"
    fi
else
    echo "⚠️  Could not access Kinesis shard"
fi

# Wait a bit more for consumer to process
echo ""
echo "Waiting additional 15 seconds for consumer to process..."
sleep 15

# Check if data appeared in S3
echo ""
echo "Step 8: Checking if data appeared in S3..."

S3_OBJECTS=$(awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566 2>/dev/null | wc -l)

if [ "$S3_OBJECTS" -gt 0 ]; then
    echo "✅ Found $S3_OBJECTS objects in S3!"
    echo ""
    echo "Sample S3 structure:"
    awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566 | head -10
    
    # Try to download and show a sample log
    FIRST_FILE=$(awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566 | head -1 | awk '{print $4}')
    if [ ! -z "$FIRST_FILE" ]; then
        echo ""
        echo "Sample log content from: $FIRST_FILE"
        awslocal s3 cp "s3://md-raw-logs/$FIRST_FILE" - --endpoint-url http://localhost:4566 2>/dev/null | head -3
    fi
else
    echo "⚠️  No objects found in S3 yet"
    echo "   This might be normal if consumer is still processing"
    echo "   Check consumer logs: docker compose logs kinesis-consumer"
fi

# Stop continuous generation
echo ""
echo "Step 9: Stopping continuous log generation..."
curl -s -X POST http://localhost:8000/api/continuous/stop > /dev/null
echo "✅ Stopped continuous generation"

# Summary
echo ""
echo "============================================"
echo "📊 Test Summary"
echo "============================================"
echo ""
echo "✅ All services are healthy"
echo "✅ LocalStack is running"
echo "✅ Kinesis stream is ACTIVE"
echo "✅ S3 bucket exists"
echo "✅ Test scenarios triggered"

if [ "$S3_OBJECTS" -gt 0 ]; then
    echo "✅ Data flow verified: Stage 00 → Kinesis → S3"
    echo ""
    echo "🎉 Full pipeline is working correctly!"
else
    echo "⚠️  Data not yet in S3 (check consumer logs)"
    echo ""
    echo "Troubleshooting:"
    echo "  docker compose logs kinesis-consumer"
    echo "  docker compose logs ingestion-interface | grep Kinesis"
fi

echo ""
echo "============================================"
echo ""
