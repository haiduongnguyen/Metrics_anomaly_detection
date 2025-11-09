# Full Pipeline - Metrics Anomaly Detection System

## 1. Tổng Quan

Đây là hệ thống pipeline hoàn chỉnh cho **Metrics Anomaly Detection**, bao gồm 2 stages chính:

- **Stage 00**: Mock Servers - Tạo ra logs và metrics mô phỏng
- **Stage 01**: Ingestion Layer - Stream và lưu trữ data vào data lake

Pipeline được thiết kế theo kiến trúc AWS nhưng chạy hoàn toàn local với LocalStack, cho phép development và testing mà không cần AWS account.

## 2. Kiến Trúc Tổng Thể

```
┌────────────────────────────────────────────────────────┐
│  Stage 00 - Mock Servers (6 services)                  │
│  ├─ Scenario Orchestrator (8000) - Web UI control      │
│  ├─ Pattern Generator (8001) - Math patterns           │
│  ├─ Log Synthesis (8002) - 59 log types               │
│  ├─ State Manager (8003) - Entity states               │
│  ├─ Ingestion Interface (8004) - Log ingestion         │
│  └─ Log Consolidation (8005) - OpenTelemetry std       │
└────────────────────────┬───────────────────────────────┘
                         │
                         │ Kinesis PutRecords (boto3)
                         │ + Local file storage
                         │ + OpenTelemetry consolidation
                         ▼
┌────────────────────────────────────────────────────────┐
│  LocalStack (4566) - AWS Services Emulation            │
│  ├─ Kinesis: stage01-logs-stream, stage01-metrics     │
│  └─ S3: md-raw-logs, md-raw-metrics, md-raw-apm       │
└────────────────────────┬───────────────────────────────┘
                         │
                         │ GetRecords polling (every 5s)
                         ▼
┌────────────────────────────────────────────────────────┐
│  Stage 01 - Ingestion (3 services)                     │
│  ├─ Kinesis Consumer - Stream to S3 writer            │
│  └─ Dashboard (8010) - Visual monitoring UI            │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│  S3 Partitioned Storage (LocalStack)                   │
│  service=<svc>/year=YYYY/month=MM/day=DD/hour=HH/      │
│  ├─ part-uuid1.jsonl                                   │
│  ├─ part-uuid2.jsonl                                   │
│  └─ ...                                                │
│                                                         │
│  Ready for Stage 02 (ETL with AWS Glue)               │
└────────────────────────────────────────────────────────┘
```

## 3. Services Overview

### Stage 00 Services (Ports 8000-8005)

| Service | Port | Purpose |
|---------|------|---------|
| Scenario Orchestrator | 8000 | Điều khiển 200+ scenarios, Web UI |
| Pattern Generator | 8001 | Tạo mathematical patterns |
| Log Synthesis | 8002 | Tạo 59 loại logs |
| State Manager | 8003 | Quản lý entity states |
| Ingestion Interface | 8004 | Nhận logs, gửi Kinesis + local storage |
| Log Consolidation | 8005 | OpenTelemetry standardization |

### Stage 01 Services (Port 8010 + backend)

| Service | Port | Purpose |
|---------|------|---------|
| LocalStack | 4566 | AWS services emulator (Kinesis, S3) |
| Kinesis Consumer | - | Poll Kinesis → Write S3 (partitioned) |
| Dashboard | 8010 | Visual monitoring UI |

**Total**: 9 services running

## 4. Luồng Dữ Liệu Chi Tiết

### Step 1: Log Generation (Stage 00)
```
Scenario Orchestrator triggers scenario
    ↓
Pattern Generator creates data patterns
    ↓
Log Synthesis generates 59 types of logs
    ↓
Ingestion Interface receives logs
```

### Step 2: Multi-Path Storage (Stage 00)
```
Ingestion Interface splits logs to:
    ├─→ Local files (/app/logs/categories/)
    ├─→ Log Consolidation (OpenTelemetry format)
    └─→ Kinesis Stream (boto3 PutRecords) ✨ Stage 01
```

### Step 3: Streaming Pipeline (Stage 01)
```
Kinesis Stream (LocalStack)
    ↓ polling every 5s
Kinesis Consumer
    ├─ Parses JSON logs
    ├─ Groups by partition (service + time)
    └─ Writes to S3
    
S3 Raw Buckets (LocalStack)
    └─ Partitioned JSONL files
       service=<name>/year=YYYY/month=MM/day=DD/hour=HH/
```

### Step 4: Monitoring (Stage 01)
```
Dashboard (Port 8010)
    ├─ Kinesis stream status
    ├─ S3 bucket browser
    ├─ Partition analysis
    └─ Log viewer
```

## 5. Cài Đặt và Chạy

### 5.1. Yêu Cầu

- Docker & Docker Compose v2.0+
- **Minimum 2GB RAM** (đã tối ưu)
- 10GB disk space
- Linux/MacOS/Windows (WSL2)

### 5.2. Quick Start

```bash
cd /home/son/Documents/cursor-projects/Metrics_anomaly_detection/stages

# Start all services
docker compose up -d

# Wait 2-3 minutes for initialization

# Check status
docker compose ps
```

### 5.3. Detailed Start

```bash
# Using helper script
./start.sh

# Or step by step
docker compose up -d           # Start services
docker compose ps              # Check status
docker compose logs -f         # View logs
```

### 5.4. Stop Services

```bash
./stop.sh

# Or
docker compose down

# Remove all data
docker compose down -v
```

## 6. Verification

### 6.1. Check All Services Healthy

```bash
docker compose ps

# Expected: All services show "Up X seconds (healthy)"
```

### 6.2. Check LocalStack

```bash
curl http://localhost:4566/_localstack/health | jq '.services.kinesis, .services.s3'

# Expected: Both "running"
```

### 6.3. Check Stage 00

```bash
curl http://localhost:8000/health  # Scenario Orchestrator
curl http://localhost:8004/health  # Ingestion Interface
curl http://localhost:8005/health  # Log Consolidation

# Expected: All return {"status": "healthy"}
```

### 6.4. Check Stage 01

```bash
# Dashboard
curl http://localhost:8010/health

# Kinesis streams
awslocal kinesis list-streams --endpoint-url http://localhost:4566

# S3 buckets
awslocal s3 ls --endpoint-url http://localhost:4566

# Consumer
docker logs kinesis-consumer | grep "Consuming"
```

## 7. Sử Dụng

### 7.1. Web UIs

**Stage 00 Control Panel**: http://localhost:8000
- Trigger scenarios
- View scenarios status
- Monitor continuous generation

**Stage 01 Dashboard**: http://localhost:8010
- Monitor Kinesis streams
- Browse S3 buckets
- View logs
- Analyze partitions

### 7.2. Generate Test Data

**Via Web UI**:
```
1. Open http://localhost:8000
2. Section "Tạo Log Liên Tục"
3. Click "Bật Tự Động" hoặc "Start Continuous"
4. Set interval: 2s, logs_per_interval: 10, duration: 60s
5. Click Start
```

**Via API**:
```bash
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{
    "interval_seconds": 2,
    "logs_per_interval": 10,
    "duration_seconds": 60
  }'
```

### 7.3. Monitor Data Flow

**Option 1**: Dashboard (Recommended)
```
Open http://localhost:8010
Watch "S3 Objects" count increase
Select bucket and browse files
```

**Option 2**: Terminal
```bash
# Terminal 1: Producer
docker compose logs -f ingestion-interface | grep Kinesis

# Terminal 2: Consumer
docker compose logs -f kinesis-consumer

# Terminal 3: S3 count
watch -n 5 'awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566 | wc -l'
```

### 7.4. Access Data

**Via Dashboard**:
```
1. Open http://localhost:8010
2. Select bucket: md-raw-logs
3. Click "Refresh"
4. Click "View" on any file
5. Log content appears in viewer
```

**Via CLI**:
```bash
# List objects
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566

# Download file
awslocal s3 cp s3://md-raw-logs/<key> sample.jsonl --endpoint-url http://localhost:4566

# View content
cat sample.jsonl | jq '.'
```

### 7.5. Stop Generation

```bash
curl -X POST http://localhost:8000/api/continuous/stop
```

## 8. Testing

### 8.1. Automated Test

```bash
cd /home/son/Documents/cursor-projects/Metrics_anomaly_detection/stages

./test-pipeline.sh
```

Test will:
1. Verify all services healthy
2. Check LocalStack và Kinesis
3. Trigger 30s of log generation
4. Wait for data flow
5. Verify S3 has data
6. Show sample logs

### 8.2. Manual Test Kinesis

```bash
cd stages/01-ingestion
./test-kinesis.sh
```

This sends a test record to Kinesis và verifies it's received.

## 9. Data Format

### Log Format

**Input** (từ Stage 00):
```json
{
  "timestamp": "2025-11-09T13:24:33Z",
  "service": "api-gateway",
  "level": "INFO",
  "message": "Request processed",
  "trace_id": "abc123",
  "source": "log-synthesis",
  "log_type": "api_gateway_log",
  "anomaly_score": 5.2
}
```

**Output** (trong S3):
- Format: JSONL (newline-delimited JSON)
- Same structure as input
- One log per line
- UTF-8 encoding

### Partition Structure

```
md-raw-logs/
├── service=api-gateway/
│   └── year=2025/
│       └── month=11/
│           └── day=09/
│               └── hour=13/
│                   ├── part-uuid1.jsonl
│                   └── part-uuid2.jsonl
├── service=auth-service/
│   └── year=2025/...
└── service=payment-service/
    └── year=2025/...
```

**Benefits**:
- AWS Glue Crawler compatible
- Athena query optimization
- Partition pruning for fast queries
- Easy to manage and archive

## 10. Configuration

### Environment Variables

All configuration in `docker-compose.yml`:

**LocalStack**:
```yaml
SERVICES: s3,kinesis,lambda,iam,cloudwatch,sts,logs
DEBUG: 0
PERSISTENCE: 0
AWS_DEFAULT_REGION: us-east-1
```

**Ingestion Interface** (Stage 00 → Stage 01 bridge):
```yaml
KINESIS_ENABLED: true
AWS_ENDPOINT_URL: http://localstack:4566
KINESIS_STREAM_NAME: stage01-logs-stream
```

**Kinesis Consumer**:
```yaml
STREAM_NAME: stage01-logs-stream
TARGET_BUCKET: md-raw-logs
POLL_INTERVAL: 5
BATCH_SIZE: 100
```

**Dashboard**:
```yaml
AWS_ENDPOINT_URL: http://localstack:4566
AWS_DEFAULT_REGION: us-east-1
```

## 11. Performance

### Metrics

- **Throughput**: ~1000 logs/second (configurable)
- **Latency**: 10-15 seconds end-to-end
- **RAM Usage**: ~1.5-2GB total (all services)
- **CPU Usage**: ~20-30% during active generation
- **Storage**: ~1GB per 100K logs (depends on log size)

### Bottlenecks

1. **Consumer polling**: Limited by POLL_INTERVAL (5s)
   - Solution: Reduce to 2-3s
   
2. **Single shard**: Kinesis throughput limited
   - Solution: Add more shards (via awslocal or Terraform)
   
3. **LocalStack limitations**: Not as fast as real AWS
   - Solution: Deploy to real AWS for production

## 12. Troubleshooting

### All Services

```bash
# Check status
docker compose ps

# View logs
docker compose logs -f

# Restart specific service
docker compose restart <service-name>

# Restart all
docker compose restart
```

### LocalStack Issues

```bash
# Check health
curl http://localhost:4566/_localstack/health

# View logs
docker logs localstack-anomaly

# Restart
docker compose restart localstack

# Full reset
docker compose down -v
docker compose up -d
```

### No Data in S3

**Step 1**: Check Stage 00 producing logs
```bash
curl http://localhost:8000/health
docker logs ingestion-interface | grep "total_ingested"
```

**Step 2**: Check Kinesis producer working
```bash
docker logs ingestion-interface | grep Kinesis
# Should show: "✅ [Kinesis Producer] Sent X logs"
```

**Step 3**: Check consumer processing
```bash
docker logs kinesis-consumer | grep "Wrote"
# Should show: "✅ Wrote X logs to s3://..."
```

**Step 4**: Verify S3
```bash
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566
```

### Port Conflicts

```bash
# Check ports in use
lsof -i :4566  # LocalStack
lsof -i :8000  # Scenario Orchestrator
lsof -i :8010  # Dashboard

# Kill processes if needed
kill -9 <PID>
```

## 13. Monitoring

### Health Checks

```bash
# Quick check all
curl http://localhost:8000/health && \
curl http://localhost:8004/health && \
curl http://localhost:8010/health && \
curl http://localhost:4566/_localstack/health

# All should return 200 OK
```

### Real-time Monitoring

**Dashboard** (Recommended): http://localhost:8010
- Visual indicators
- Auto-refresh every 10s
- S3 browser
- Log viewer

**Logs**:
```bash
# All services
docker compose logs -f

# Specific services
docker compose logs -f kinesis-consumer ingestion-interface

# Filter
docker compose logs -f | grep -E "(Kinesis|Wrote|ERROR)"
```

### Data Metrics

```bash
# Count S3 objects
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566 | wc -l

# Total size
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566 | awk '{sum+=$3} END {print sum/1024/1024 " MB"}'

# Consumer stats
docker logs kinesis-consumer | grep "Total processed"
```

## 14. Advanced Usage

### Custom Scenarios

**Trigger specific anomaly**:
```bash
curl -X POST http://localhost:8000/api/anomaly/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "anomaly_type": "cpu_spike",
    "intensity": 90,
    "duration_seconds": 60
  }'
```

### Query S3 Data

**List partitions**:
```bash
awslocal s3 ls s3://md-raw-logs/ --endpoint-url http://localhost:4566
# Shows service partitions

awslocal s3 ls s3://md-raw-logs/service=api-gateway/ --endpoint-url http://localhost:4566
# Shows year partitions
```

**Download specific partition**:
```bash
awslocal s3 sync s3://md-raw-logs/service=api-gateway/year=2025/month=11/ ./local-data/ --endpoint-url http://localhost:4566
```

### Analyze Logs

```bash
# Download all logs
awslocal s3 sync s3://md-raw-logs/ ./all-logs/ --endpoint-url http://localhost:4566

# Count logs per service
find ./all-logs -name "*.jsonl" -exec wc -l {} \; | awk '{sum+=$1} END {print sum " total logs"}'

# Parse and analyze
cat ./all-logs/service=api-gateway/*/*.jsonl | jq '.anomaly_score' | sort -n | tail -10
```

## 15. Migration to AWS

### Current Setup (LocalStack)
- ✅ Development và testing
- ✅ No AWS costs
- ✅ Fast iteration
- ✅ Same APIs as AWS

### Migration Steps

**1. Environment Variables**:
```yaml
# Remove LocalStack endpoints
AWS_ENDPOINT_URL: ""

# Use real AWS credentials
AWS_ACCESS_KEY_ID: <from-iam>
AWS_SECRET_ACCESS_KEY: <from-iam>
# Or use IAM roles (recommended)
```

**2. Infrastructure**:
- Deploy Kinesis streams (1-5 shards based on throughput)
- Create S3 buckets với encryption (SSE-S3 or SSE-KMS)
- Setup IAM roles and policies
- Optional: Use Terraform (Stage 01 Bước 2)

**3. Replace Consumer with Lambda**:
- Lambda code có sẵn (backup trong git history)
- Deploy via AWS Console or Terraform
- Event source mapping auto-configured
- Auto-scaling built-in

**4. Dashboard**:
- Deploy to ECS/EKS/AppRunner
- Update AWS_ENDPOINT_URL to empty (use default)
- Add authentication (Cognito or ALB auth)

**5. No Changes Needed**:
- Stage 00 services (can run on ECS)
- Log format (JSONL)
- Partition structure
- Kinesis partition key strategy

## 16. Architecture Benefits

### Scalability
- ✅ Kinesis: Add shards for higher throughput
- ✅ Consumer: Deploy multiple instances
- ✅ S3: Unlimited storage, auto-scaling

### Reliability
- ✅ Kinesis: 24h retention, replay capability
- ✅ S3: 99.999999999% durability
- ✅ Consumer: Auto-restart on failures

### Cost Efficiency
- ✅ LocalStack: Free for development
- ✅ S3: Pay per GB stored
- ✅ Kinesis: Pay per shard-hour
- ✅ Lambda: Pay per invocation (when migrated)

### AWS Compatibility
- ✅ Same boto3 APIs
- ✅ Same partition structure
- ✅ Glue/Athena ready
- ✅ Easy migration path

## 17. Files và Structure

### Root Level (`stages/`)
```
├── docker-compose.yml          # Main compose file
├── start.sh                    # Startup script
├── stop.sh                     # Shutdown script
├── test-pipeline.sh            # End-to-end test
├── QUICK_START.md              # Quick reference
└── README.md                   # This file
```

### Stage 00 (`00-mock-servers/`)
```
├── 01-scenario-orchestrator/   # 6 microservices
├── 02-pattern-generator/
├── 03-log-synthesis/
├── 04-state-manager/
├── 05-ingestion-interface/
├── 06-log-consolidation/
├── docker-compose.yml          # Standalone compose
└── README.md                   # Stage 00 docs
```

### Stage 01 (`01-ingestion/`)
```
├── dashboard/                  # Web UI (port 8010)
│   ├── app.py
│   ├── Dockerfile
│   └── README.md
├── kinesis-consumer/           # Consumer service
│   ├── consumer.py
│   ├── Dockerfile
│   └── requirements.txt
├── localstack-init/            # Auto-init scripts
│   └── 01-setup-resources.sh
├── docker-compose.yml          # Uses existing LocalStack
├── docker-compose.standalone.yml
├── start.sh
├── stop.sh
├── test-kinesis.sh
├── plan.md                     # Architecture plan
└── README.md                   # Stage 01 docs
```

## 18. Common Commands

### Management
```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# Rebuild
docker compose build
docker compose up -d

# Remove all
docker compose down -v
```

### Monitoring
```bash
# Status
docker compose ps

# Logs
docker compose logs -f
docker compose logs -f <service>

# Stats
docker stats
```

### Testing
```bash
# Full pipeline test
./test-pipeline.sh

# Kinesis test
cd 01-ingestion && ./test-kinesis.sh

# Manual verification
curl http://localhost:8000/health
curl http://localhost:8010/health
```

### Data Access
```bash
# List streams
awslocal kinesis list-streams --endpoint-url http://localhost:4566

# List buckets
awslocal s3 ls --endpoint-url http://localhost:4566

# List objects
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566

# Download
awslocal s3 cp s3://md-raw-logs/<key> . --endpoint-url http://localhost:4566
```

## 19. Next Stages

### Stage 02 - ETL & Processing (Planned)
- AWS Glue Crawlers scan S3 raw buckets
- Glue Data Catalog registration
- ETL Jobs: cleaning, normalization, transformation
- Write to S3 transformed buckets

### Stage 03 - Hot & Cold Storage (Planned)
- Redis/ElastiCache for hot data (1-24 hours)
- S3 lifecycle policies for cold storage
- Athena query engine
- Redshift Spectrum for analytics

### Stage 04 - Detection Engine (Planned)
- Statistical methods (STL, IQR, Z-Score)
- ML models (Random Cut Forest, SR-CNN, Clustering)
- Rule-based detection
- Decision engine với voting

### Stage 05 - Root Cause Analysis (Planned)
- AWS Bedrock integration
- Vector database for knowledge base
- Confluence integration
- Causal inference

### Stage 06 - Alerting (Planned)
- SQS queues for alerts
- Slack/PagerDuty/Jira integration
- CloudWatch dashboards
- Feedback loop

## 20. Documentation

### Quick Links
- **Quick Start**: [QUICK_START.md](./QUICK_START.md)
- **Stage 00 README**: [00-mock-servers/README.md](./00-mock-servers/README.md)
- **Stage 01 README**: [01-ingestion/README.md](./01-ingestion/README.md)
- **Dashboard README**: [01-ingestion/dashboard/README.md](./01-ingestion/dashboard/README.md)
- **Architecture**: [../challenge-documents/architecture.md](../challenge-documents/architecture.md)
- **Stage 01 Plan**: [01-ingestion/plan.md](./01-ingestion/plan.md)

### API Documentation
- Stage 00 Control: http://localhost:8000
- Stage 01 Dashboard: http://localhost:8010
- FastAPI Swagger: http://localhost:8010/docs

## 21. Support

### Issues?

1. Check container status: `docker compose ps`
2. Check logs: `docker compose logs <service>`
3. Check health: `curl http://localhost:<port>/health`
4. View dashboard: http://localhost:8010
5. Run test: `./test-pipeline.sh`

### Common Solutions

**Services unhealthy**: `docker compose restart`
**No data in S3**: Verify Stage 00 generating logs
**LocalStack errors**: `docker compose restart localstack`
**Port conflicts**: Check `lsof -i :<port>`

---

## 22. Summary

✅ **Stage 00 - Mock Servers**: 6 services, 59 log types, 200+ scenarios
✅ **Stage 01 - Ingestion**: Kinesis streaming, S3 storage, Visual dashboard

**Total Services**: 9 running containers
**Web UIs**: 2 dashboards (ports 8000, 8010)
**Status**: Fully operational

**Quick Access**:
- Stage 00 Control: http://localhost:8000
- Stage 01 Dashboard: http://localhost:8010

**Quick Commands**:
```bash
cd stages
docker compose up -d        # Start
./test-pipeline.sh          # Test
docker compose down         # Stop
```

**Pipeline is ready for testing and development!** 🚀
