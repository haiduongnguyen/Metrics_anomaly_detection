#!/bin/bash

# This script runs when LocalStack is ready
# It creates initial AWS resources for testing

echo "============================================"
echo "LocalStack Initialization Script"
echo "Stage 01 - Ingestion Layer"
echo "============================================"

# Wait for LocalStack to be fully ready
sleep 5

# Set AWS credentials for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# LocalStack endpoint
ENDPOINT="http://localhost:4566"

echo ""
echo "Creating S3 Raw Buckets..."

# Create S3 buckets for raw data
awslocal s3 mb s3://md-raw-logs --region us-east-1 || true
awslocal s3 mb s3://md-raw-metrics --region us-east-1 || true
awslocal s3 mb s3://md-raw-apm --region us-east-1 || true

echo "✓ S3 raw buckets created"

echo ""
echo "Creating S3 Transformed Buckets (Stage 02)..."

# Create S3 buckets for transformed data
awslocal s3 mb s3://md-transformed-logs --region us-east-1 || true
awslocal s3 mb s3://md-transformed-metrics --region us-east-1 || true
awslocal s3 mb s3://md-transformed-apm --region us-east-1 || true

echo "✓ S3 transformed buckets created"

echo ""
echo "Creating S3 Stage 03 Buckets (Warm/Cold)..."
awslocal s3 mb s3://md-warm-store --region us-east-1 || true
awslocal s3 mb s3://md-cold-store --region us-east-1 || true
echo "✓ S3 Stage 03 buckets created"

echo ""
echo "Creating Kinesis Streams..."

# Create Kinesis streams
awslocal kinesis create-stream \
  --stream-name stage01-logs-stream \
  --shard-count 1 \
  --region us-east-1 || true

awslocal kinesis create-stream \
  --stream-name stage01-metrics-stream \
  --shard-count 1 \
  --region us-east-1 || true

echo "✓ Kinesis streams created"

echo ""
echo "Listing created resources..."

echo ""
echo "S3 Buckets:"
awslocal s3 ls

echo ""
echo "Kinesis Streams:"
awslocal kinesis list-streams --region us-east-1

echo ""
echo "============================================"
echo "✅ LocalStack initialization completed!"
echo "============================================"
