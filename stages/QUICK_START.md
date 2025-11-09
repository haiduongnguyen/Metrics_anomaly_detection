# Quick Start Guide - Full Pipeline

## TL;DR

```bash
cd /home/son/Documents/cursor-projects/Metrics_anomaly_detection/stages
docker compose up -d --build
```

Đợi 2-3 phút, sau đó test:

```bash
./test-pipeline.sh
```

## Đầy Đủ

### 1. Khởi động

```bash
cd stages
./start.sh
```

### 2. Kiểm tra services

```bash
# All services
docker compose ps

# Health checks
curl http://localhost:8000/health  # Scenario Orchestrator
curl http://localhost:8004/health  # Ingestion Interface
curl http://localhost:4566/_localstack/health  # LocalStack
```

### 3. Trigger logs

Mở browser: http://localhost:8000

Hoặc API:

```bash
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{
    "interval_seconds": 2,
    "logs_per_interval": 10,
    "duration_seconds": 60
  }'
```

### 4. Verify data flow

```bash
# Check Kinesis
awslocal kinesis describe-stream-summary --stream-name stage01-logs-stream --endpoint-url http://localhost:4566

# Check S3
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566

# Download sample
awslocal s3 cp s3://md-raw-logs/service=api-gateway/year=2025/month=11/day=08/hour=10/part-xxx.jsonl . --endpoint-url http://localhost:4566
```

### 5. Monitor

```bash
# All logs
docker compose logs -f

# Specific services
docker compose logs -f kinesis-consumer
docker compose logs -f ingestion-interface
```

### 6. Dừng

```bash
./stop.sh
```

## Luồng Dữ Liệu

```
Mock Servers → Ingestion Interface → Kinesis Stream → Consumer → S3 Raw Buckets
(Stage 00)                            (LocalStack)                (LocalStack)
```

## Troubleshooting

### Services không start

```bash
docker compose logs <service-name>
docker compose restart <service-name>
```

### Không có data trong S3

1. Check ingestion sending to Kinesis:
   ```bash
   docker compose logs ingestion-interface | grep Kinesis
   ```

2. Check consumer processing:
   ```bash
   docker compose logs kinesis-consumer
   ```

3. Manually test:
   ```bash
   cd 01-ingestion
   ./test-kinesis.sh
   ```

### LocalStack issues

```bash
# Restart LocalStack
docker compose restart localstack

# Wait for healthy
curl http://localhost:4566/_localstack/health
```

## Next Steps

- [Full README](./README.md)
- [Stage 01 Plan](./01-ingestion/plan.md)
- [Architecture](../challenge-documents/architecture.md)
