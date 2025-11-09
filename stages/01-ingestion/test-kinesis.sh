#!/bin/bash

echo "============================================"
echo "Testing Kinesis Integration"
echo "============================================"

# Test record
TEST_RECORD='{
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
  "service": "api-gateway",
  "level": "INFO",
  "message": "Test log from Stage 01 setup",
  "trace_id": "test-'$(date +%s)'",
  "source": "test-script"
}'

echo ""
echo "Sending test record to Kinesis stream: stage01-logs-stream"
echo "Record: $TEST_RECORD"
echo ""

# Base64 encode the record
DATA_BASE64=$(echo -n "$TEST_RECORD" | base64 -w 0)

# Send to Kinesis
awslocal kinesis put-record \
  --stream-name stage01-logs-stream \
  --partition-key "api-gateway" \
  --data "$DATA_BASE64" \
  --region us-east-1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully sent record to Kinesis!"
    echo ""
    echo "Verifying stream..."
    awslocal kinesis describe-stream-summary \
      --stream-name stage01-logs-stream \
      --region us-east-1
    echo ""
    echo "Note: To consume this record, you'll need to implement Lambda consumer (next step)"
else
    echo "❌ Failed to send record"
    exit 1
fi
