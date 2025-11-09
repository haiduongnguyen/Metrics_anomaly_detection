# Stage 01 - Ingestion Layer

## 1. Giới Thiệu

Stage 01 - Ingestion Layer là lớp tiếp nhận và streaming dữ liệu, kết nối giữa Stage 00 (Mock Servers) và các stage xử lý phía sau. Lớp này sử dụng **Amazon Kinesis Data Streams** để streaming real-time và **Amazon S3** để lưu trữ raw data theo cấu trúc partition chuẩn, sẵn sàng cho các công việc ETL và phân tích ở các stage tiếp theo.

### Nối Tiếp Từ Stage 00

Ở Stage 00, chúng ta đã có hệ thống Mock Servers với 6 microservices tạo ra 59 loại log đa dạng, được chuẩn hóa theo OpenTelemetry format và lưu vào file system local. Stage 01 tiếp nối bằng cách:

1. **Nhận logs từ Stage 00** qua Ingestion Interface (port 8004)
2. **Stream vào Kinesis** để xử lý real-time
3. **Lưu vào S3** với partition structure chuẩn AWS
4. **Cung cấp dashboard** để monitor và quản lý

Điều này cho phép logs không chỉ được lưu local mà còn đi vào một data pipeline AWS-compatible, sẵn sàng cho big data processing.

## 2. Kiến Trúc Hệ Thống

```
┌──────────────────────────────────────────────────────┐
│  Stage 00 - Mock Servers                             │
│  ├─ Scenario Orchestrator (8000)                     │
│  ├─ Pattern Generator (8001)                         │
│  ├─ Log Synthesis (8002) - 59 log types             │
│  ├─ State Manager (8003)                             │
│  ├─ Ingestion Interface (8004) ◄── Receives logs    │
│  └─ Log Consolidation (8005)                         │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ Kinesis PutRecords (boto3)
                     │ Partition Key: service name
                     ▼
┌──────────────────────────────────────────────────────┐
│  LocalStack (Port 4566)                              │
│  ├─ Kinesis Data Streams                             │
│  │  ├─ stage01-logs-stream (ACTIVE, 1 shard)        │
│  │  └─ stage01-metrics-stream (ACTIVE, 1 shard)     │
│  │                                                    │
│  └─ S3 Raw Buckets                                   │
│     ├─ md-raw-logs (partitioned storage)            │
│     ├─ md-raw-metrics                                │
│     └─ md-raw-apm                                    │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ GetRecords (polling every 5s)
                     │ Batch size: 100 records
                     ▼
┌──────────────────────────────────────────────────────┐
│  Kinesis Consumer Service                            │
│  ├─ Reads from Kinesis stream                        │
│  ├─ Parses JSON logs                                 │
│  ├─ Groups by partition (service + time)             │
│  └─ Writes to S3 (JSONL format)                      │
└──────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  S3 Partitioned Storage                              │
│  service=<svc>/year=YYYY/month=MM/day=DD/hour=HH/    │
│    part-<uuid>.jsonl                                 │
│                                                       │
│  Example:                                            │
│  service=api-gateway/                                │
│    year=2025/month=11/day=09/hour=13/                │
│      part-abc123.jsonl                               │
└──────────────────────────────────────────────────────┘
```

### Monitoring Dashboard

```
┌──────────────────────────────────────────────────────┐
│  Stage 01 Dashboard (Port 8010)                      │
│  ├─ Real-time Kinesis monitoring                     │
│  ├─ S3 bucket browser                                │
│  ├─ Partition analysis                               │
│  └─ Integrated log viewer                            │
└──────────────────────────────────────────────────────┘
```

## 3. Các Thành Phần Chính

### 3.1. LocalStack - AWS Services Emulator
- **Port**: 4566
- **Services**: S3, Kinesis, Lambda, IAM, CloudWatch
- **Purpose**: Mô phỏng AWS services cho local development
- **Configuration**: 
  - PERSISTENCE=0 (no data persistence để tránh conflicts)
  - LAMBDA_EXECUTOR=local (simplified execution)
  - Tự động khởi tạo resources qua init scripts

### 3.2. Kinesis Data Streams
- **stage01-logs-stream**: Stream chính cho logs
  - Retention: 24 hours
  - Shards: 1 (có thể scale)
  - Throughput: 1MB/s write, 2MB/s read
  
- **stage01-metrics-stream**: Stream cho metrics (future use)
  - Same configuration as logs stream

### 3.3. S3 Raw Buckets
- **md-raw-logs**: Lưu trữ raw logs với partition structure
- **md-raw-metrics**: Lưu trữ raw metrics
- **md-raw-apm**: Lưu trữ APM metrics

**Partition Structure** (tương thích Athena/Glue):
```
service=<service_name>/
  year=YYYY/
    month=MM/
      day=DD/
        hour=HH/
          part-<uuid>.jsonl
```

### 3.4. Kinesis Consumer Service
- **Language**: Python 3.11
- **Function**: Continuously polls Kinesis và writes to S3
- **Configuration**:
  - Poll interval: 5 seconds
  - Batch size: 100 records
  - Auto-restart on errors
  
**Why Consumer Service instead of Lambda?**
LocalStack Community Edition has limitations với Lambda (functions stay in Pending state). Consumer service là giải pháp thay thế hoạt động tốt và sẵn sàng migrate lên Lambda khi deploy AWS thật.

### 3.5. Stage 01 Dashboard (Port 8010)
- **Web UI**: Modern, responsive interface
- **Features**:
  - Real-time Kinesis stream monitoring
  - S3 bucket browser với filtering
  - Partition structure analysis
  - Integrated log viewer (dark theme)
  - REST API endpoints
- **Auto-refresh**: Every 10 seconds
- **Technology**: FastAPI + boto3 + vanilla JavaScript

## 4. Tích Hợp với Stage 00

### 4.1. Kinesis Producer Integration

Stage 00 Ingestion Interface (port 8004) đã được tích hợp Kinesis producer:

```python
# File: 00-mock-servers/05-ingestion-interface/kinesis_producer.py
class KinesisProducer:
    - Kết nối đến LocalStack Kinesis
    - Batch logs và gửi qua PutRecords API
    - Partition key: service name
    - Auto-retry on failures
```

**Environment Variables**:
```yaml
KINESIS_ENABLED: true
AWS_ENDPOINT_URL: http://localstack:4566
AWS_DEFAULT_REGION: us-east-1
KINESIS_STREAM_NAME: stage01-logs-stream
```

### 4.2. Data Flow

```
Stage 00: Log Synthesis
    ↓ (POST /api/ingest/batch)
Stage 00: Ingestion Interface
    ├─→ Local file storage (logs/<category>/)
    ├─→ Forward to Consolidation (8005)
    └─→ Send to Kinesis (boto3 PutRecords) ✨ NEW
    
Kinesis Stream
    ↓ (GetRecords polling)
    
Kinesis Consumer
    ├─→ Parse JSON logs
    ├─→ Group by partition
    └─→ Write to S3 (partitioned JSONL)
    
S3 Raw Buckets
    └─→ Ready for Stage 02 (ETL)
```

## 5. Cài Đặt và Chạy

### 5.1. Yêu Cầu Hệ Thống
- Docker & Docker Compose v2.0+
- Minimum 2GB RAM
- 10GB disk space
- Stage 00 đã được setup (xem `stages/00-mock-servers/README.md`)

### 5.2. Khởi Động (Standalone Mode)

Nếu chỉ muốn chạy Stage 01:

```bash
cd stages/01-ingestion
./start.sh
```

Script này sẽ:
1. Detect LocalStack đang chạy hoặc start mới
2. Connect vào `anomaly-network`
3. Initialize Kinesis streams và S3 buckets
4. Start dashboard service

### 5.3. Khởi Động (Full Pipeline Mode)

**Khuyến nghị**: Chạy toàn bộ pipeline từ thư mục stages/:

```bash
cd stages
docker compose up -d
```

Hoặc:

```bash
./start.sh
```

## 6. Sử Dụng

### 6.1. Access Dashboard

**URL**: http://localhost:8010

Dashboard cung cấp:
- 📊 Real-time statistics (Kinesis + S3)
- 📡 Kinesis stream status monitoring
- 🗄️ S3 bucket browser
- 📁 Partition structure analysis
- 📄 Integrated log viewer

### 6.2. Monitor Data Flow

**Terminal 1 - Ingestion Interface** (Producer):
```bash
docker compose logs -f ingestion-interface | grep Kinesis
```

Expect:
```
✅ [Kinesis Producer] Sent 100 logs to stage01-logs-stream
```

**Terminal 2 - Kinesis Consumer**:
```bash
docker compose logs -f kinesis-consumer
```

Expect:
```
✅ Wrote 100 logs to s3://md-raw-logs/service=api-gateway/...
📊 Batch processed: 100 records, 100 written, 0 failed
📈 Total processed: 300
```

### 6.3. Browse S3 Data

**Via Dashboard** (Recommended):
```
1. Open http://localhost:8010
2. Select bucket: md-raw-logs
3. Click "Refresh"
4. Click "View" on any object
```

**Via CLI**:
```bash
# List all objects
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566

# Download sample
awslocal s3 cp s3://md-raw-logs/<key> sample.jsonl --endpoint-url http://localhost:4566

# View content
cat sample.jsonl | jq '.'
```

### 6.4. Test Pipeline

**Automated Test**:
```bash
cd stages
./test-pipeline.sh
```

**Manual Test**:
```bash
# 1. Trigger log generation từ Stage 00
curl -X POST http://localhost:8000/api/continuous/start \
  -H "Content-Type: application/json" \
  -d '{
    "interval_seconds": 2,
    "logs_per_interval": 10,
    "duration_seconds": 60
  }'

# 2. Monitor qua Dashboard: http://localhost:8010

# 3. Check S3 data
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566

# 4. Stop generation
curl -X POST http://localhost:8000/api/continuous/stop
```

## 7. API Endpoints

### Dashboard APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/stats/summary` | GET | Overall statistics |
| `/api/kinesis/streams` | GET | List Kinesis streams |
| `/api/kinesis/stream/{name}/metrics` | GET | Stream details |
| `/api/s3/buckets` | GET | List S3 buckets |
| `/api/s3/bucket/{name}/objects` | GET | List objects in bucket |
| `/api/s3/bucket/{name}/partitions` | GET | Partition analysis |
| `/api/s3/object/{bucket}/{key}` | GET | View log content |

**Example**:
```bash
# Get summary
curl http://localhost:8010/api/stats/summary | jq

# List streams
curl http://localhost:8010/api/kinesis/streams | jq

# Browse S3
curl http://localhost:8010/api/s3/bucket/md-raw-logs/objects | jq
```

## 8. Cấu Trúc Thư Mục

```
01-ingestion/
├── dashboard/                    # Web UI service
│   ├── app.py                   # FastAPI application
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── kinesis-consumer/            # Consumer service
│   ├── consumer.py              # Kinesis polling & S3 writing
│   ├── requirements.txt
│   └── Dockerfile
│
├── localstack-init/             # LocalStack initialization
│   └── 01-setup-resources.sh   # Auto-create streams & buckets
│
├── docker-compose.yml           # Lightweight config (uses existing LocalStack)
├── docker-compose.standalone.yml # Standalone mode
├── start.sh                     # Smart startup script
├── stop.sh                      # Shutdown script
├── test-kinesis.sh              # Test script
├── plan.md                      # Architecture plan (reference)
├── .gitignore
└── README.md                    # This file
```

## 9. Configuration

### Environment Variables

**Ingestion Interface (Stage 00)**:
```yaml
KINESIS_ENABLED: true                    # Enable Kinesis producer
AWS_ENDPOINT_URL: http://localstack:4566 # LocalStack endpoint
AWS_DEFAULT_REGION: us-east-1
KINESIS_STREAM_NAME: stage01-logs-stream
```

**Kinesis Consumer**:
```yaml
AWS_ENDPOINT_URL: http://localstack:4566
AWS_DEFAULT_REGION: us-east-1
STREAM_NAME: stage01-logs-stream
TARGET_BUCKET: md-raw-logs
POLL_INTERVAL: 5                         # Seconds between polls
BATCH_SIZE: 100                          # Records per batch
```

**Dashboard**:
```yaml
AWS_ENDPOINT_URL: http://localstack:4566
AWS_DEFAULT_REGION: us-east-1
```

### Resource Limits

**Optimized cho 2GB RAM systems**:
- LocalStack: No persistence, local executor
- Consumer: Minimal memory footprint (~50MB)
- Dashboard: ~50MB
- Total Stage 01: ~500-700MB RAM

## 10. Data Format

### Input (từ Stage 00)

```json
{
  "timestamp": "2025-11-09T13:24:33Z",
  "service": "api-gateway",
  "level": "INFO",
  "message": "Request processed successfully",
  "trace_id": "abc123xyz",
  "source": "log-synthesis",
  "log_type": "api_gateway_log",
  "anomaly_score": 5.2,
  "request_id": "req-456",
  "user_id": "user-789"
}
```

### Output (trong S3)

**File**: `s3://md-raw-logs/service=api-gateway/year=2025/month=11/day=09/hour=13/part-abc123.jsonl`

**Format**: JSONL (newline-delimited JSON), mỗi line là một log entry giống input

**Benefits**:
- Tương thích với AWS Glue Crawlers
- Athena-ready (có thể query ngay)
- Compressed-friendly (GZIP trong production)
- Partition pruning tối ưu query performance

## 11. Performance

### Throughput
- **Ingestion**: ~1000 logs/second (from Stage 00)
- **Kinesis**: 1MB/s per shard (~1000 records/s)
- **Consumer**: ~20 records/second (limited by poll interval)
- **S3 Write**: <1 second per batch

### Latency
- Stage 00 → Kinesis: <1 second
- Kinesis → Consumer: 5-10 seconds (poll interval)
- Consumer → S3: <1 second
- **Total end-to-end**: 10-15 seconds

### Optimization Options
```yaml
# Faster consumption
POLL_INTERVAL: 2          # Reduce from 5s to 2s
BATCH_SIZE: 200           # Increase from 100 to 200

# Higher throughput
# Add more Kinesis shards (requires terraform)
# Deploy multiple consumer instances
```

## 12. Troubleshooting

### LocalStack không khởi động

```bash
# Check logs
docker logs localstack-anomaly

# Verify port not in use
lsof -i :4566

# Restart
docker compose restart localstack
```

### Kinesis Consumer không xử lý records

```bash
# Check consumer logs
docker logs kinesis-consumer

# Verify stream exists
awslocal kinesis list-streams --endpoint-url http://localhost:4566

# Check stream status
awslocal kinesis describe-stream-summary --stream-name stage01-logs-stream --endpoint-url http://localhost:4566
```

### Không có data trong S3

**Bước 1**: Verify Stage 00 đang gửi logs
```bash
docker logs ingestion-interface | grep Kinesis
# Should show: "✅ [Kinesis Producer] Sent X logs"
```

**Bước 2**: Check consumer đang chạy
```bash
docker logs kinesis-consumer | grep "Consuming from shard"
# Should show: "📖 Consuming from shard: shardId-000000000000"
```

**Bước 3**: Manual test
```bash
cd stages/01-ingestion
./test-kinesis.sh
```

**Bước 4**: Check S3 again
```bash
sleep 10
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566
```

### Dashboard không accessible

```bash
# Check container
docker ps | grep stage01-dashboard

# Check logs
docker logs stage01-dashboard

# Restart
docker compose restart stage01-dashboard

# Access
curl http://localhost:8010/health
```

## 13. Testing

### Quick Test

```bash
# From stages directory
cd /home/son/Documents/cursor-projects/Metrics_anomaly_detection/stages

# Run automated test
./test-pipeline.sh
```

Test này sẽ:
1. ✅ Verify all services healthy
2. ✅ Check LocalStack và Kinesis
3. ✅ Trigger test log generation
4. ✅ Wait for data flow
5. ✅ Verify S3 has data
6. ✅ Show sample logs

### Manual Verification

```bash
# 1. Check services
docker compose ps

# 2. Check Kinesis
awslocal kinesis describe-stream-summary --stream-name stage01-logs-stream --endpoint-url http://localhost:4566

# 3. Check S3
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566

# 4. View dashboard
open http://localhost:8010
```

## 14. Sự Khác Biệt với Stage 00

| Aspect | Stage 00 | Stage 01 |
|--------|----------|----------|
| **Purpose** | Generate mock logs | Stream & store logs |
| **Storage** | Local files only | Kinesis + S3 (AWS-compatible) |
| **Format** | Category-based folders | Time-partitioned S3 structure |
| **Processing** | OpenTelemetry consolidation | Real-time streaming pipeline |
| **Scalability** | Limited to single host | Horizontally scalable (shards) |
| **Query** | File-based grep/jq | Athena/Glue-ready |
| **Use Case** | Development, testing | Production data lake |

## 15. Migration to AWS

Stage 01 được thiết kế để dễ dàng migrate lên AWS thật:

### Changes Needed

**1. Environment Variables**:
```yaml
# Remove LocalStack endpoints
AWS_ENDPOINT_URL: ""  # Use default AWS

# Use real credentials (IAM roles)
# AWS_ACCESS_KEY_ID: <from IAM>
# AWS_SECRET_ACCESS_KEY: <from IAM>
```

**2. Switch to Lambda**:
- Lambda code đã có sẵn trong `lambda-consumer/` (backup)
- Deploy với AWS Lambda console hoặc Terraform
- Event source mapping tự động setup

**3. Infrastructure as Code** (Future - Bước 2):
- Terraform modules trong `infra/` directory
- One command deploy: `terraform apply`
- Support for multiple environments (dev, staging, prod)

**4. Không cần thay đổi**:
- ✅ Stage 00 services (có thể chạy trên ECS/EKS)
- ✅ S3 partition structure
- ✅ Kinesis partition key strategy
- ✅ Log format (JSONL)
- ✅ Dashboard code (chỉ đổi endpoint)

## 16. Next Steps

### Stage 01 - Bước 2 (Future Work)
- [ ] Terraform IaC structure (`infra/` directory)
- [ ] Terraform modules (s3_raw, kinesis, lambda, iam)
- [ ] Multiple environment support (localstack.tfvars, aws-dev.tfvars)
- [ ] State management (S3 backend)

### Stage 02 - ETL & Processing
- [ ] AWS Glue Crawlers scan S3 raw buckets
- [ ] Glue Data Catalog registration
- [ ] ETL Jobs: data cleaning, normalization, transformation
- [ ] Write to S3 transformed buckets

### Stage 03 - Hot & Cold Storage
- [ ] Redis/ElastiCache cho hot storage
- [ ] S3 lifecycle policies
- [ ] Athena query engine
- [ ] Data retention policies

## 17. Security & Best Practices

### Local Development
- ✅ Using test credentials (safe for local)
- ✅ Network isolation (Docker bridge)
- ✅ No external exposure (localhost only)

### Production Recommendations
- 🔒 Enable S3 encryption (SSE-S3 or SSE-KMS)
- 🔒 Use IAM roles instead of credentials
- 🔒 Enable VPC endpoints
- 🔒 CloudTrail audit logging
- 🔒 KMS key management
- 🔒 Bucket policies and access controls

## 18. Monitoring

### Health Checks

```bash
# All services
docker compose ps

# Individual checks
curl http://localhost:4566/_localstack/health      # LocalStack
curl http://localhost:8004/health                  # Ingestion Interface
curl http://localhost:8010/health                  # Dashboard
docker logs kinesis-consumer | grep "Consuming"    # Consumer
```

### Metrics

**Via Dashboard**: http://localhost:8010
- Kinesis stream status
- S3 object counts
- Data sizes
- Partition distribution

**Via CLI**:
```bash
# Kinesis metrics
awslocal kinesis describe-stream-summary --stream-name stage01-logs-stream --endpoint-url http://localhost:4566

# S3 metrics
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566 | wc -l
```

## 19. Performance Tuning

### For Higher Throughput

**Option 1**: Increase consumer speed
```yaml
# In docker-compose.yml
kinesis-consumer:
  environment:
    - POLL_INTERVAL=2    # From 5s to 2s
    - BATCH_SIZE=200     # From 100 to 200
```

**Option 2**: Multiple consumer instances
```yaml
# Add more consumers (requires different shard assignment)
kinesis-consumer-1:
  ...
kinesis-consumer-2:
  ...
```

**Option 3**: Increase Kinesis shards
```bash
# Via awslocal
awslocal kinesis update-shard-count --stream-name stage01-logs-stream --target-shard-count 2 --endpoint-url http://localhost:4566
```

### For Lower Resource Usage

```yaml
# Reduce poll frequency
POLL_INTERVAL: 10           # From 5s to 10s

# Smaller batches
BATCH_SIZE: 50              # From 100 to 50
```

## 20. Troubleshooting Common Issues

### Issue: "Device or resource busy: /tmp/localstack"

**Cause**: Old LocalStack container holding volume

**Solution**:
```bash
docker compose down -v
docker compose up -d
```

### Issue: "Kinesis producer not available"

**Cause**: kinesis_producer.py not copied to container

**Solution**:
```bash
# Rebuild ingestion-interface
docker compose build ingestion-interface
docker compose up -d ingestion-interface
```

### Issue: Consumer shows "Error parsing record"

**Cause**: Base64 encoding mismatch

**Status**: ✅ FIXED in current version

**Verification**:
```bash
docker logs kinesis-consumer | grep "Wrote.*logs"
# Should show successful writes
```

## 21. Documentation

### Detailed Guides
- **[dashboard/README.md](./dashboard/README.md)** - Dashboard API documentation
- **[plan.md](./plan.md)** - Architecture plan và design decisions
- **[../README.md](../README.md)** - Full pipeline documentation
- **[../00-mock-servers/README.md](../00-mock-servers/README.md)** - Stage 00 documentation

### Quick Reference
- Dashboard: http://localhost:8010
- LocalStack: http://localhost:4566
- Test script: `./test-kinesis.sh`
- Start script: `./start.sh`

## 22. FAQ

**Q: Tại sao dùng Consumer service thay vì Lambda?**
A: LocalStack Community Edition có limitations với Lambda (Pending state). Consumer service hoạt động tốt và code Lambda vẫn có sẵn để deploy AWS thật.

**Q: Data có persist khi restart không?**
A: Không với LocalStack (PERSISTENCE=0). Để persist, set PERSISTENCE=1 nhưng có thể gặp volume conflicts.

**Q: Có thể scale Kinesis consumer không?**
A: Có, deploy multiple consumers với shard assignment khác nhau. Hoặc migrate lên Lambda với auto-scaling.

**Q: Partition structure có thể thay đổi không?**
A: Có, sửa `generate_s3_key()` function trong `kinesis-consumer/consumer.py`.

**Q: Dashboard có real-time streaming không?**
A: Hiện tại auto-refresh mỗi 10s. WebSocket real-time streaming là feature future.

## 23. Roadmap

### Completed ✅
- [x] LocalStack setup với Kinesis + S3
- [x] Kinesis consumer service
- [x] S3 partitioned storage
- [x] Integration với Stage 00
- [x] Visual dashboard với monitoring
- [x] REST API endpoints

### In Progress 🔄
- [ ] Terraform IaC structure (Bước 2)
- [ ] Lambda function for AWS deployment
- [ ] Consumer metrics integration in dashboard

### Planned 📋
- [ ] WebSocket real-time log streaming
- [ ] Advanced filtering và search
- [ ] Performance charts
- [ ] Alert notifications
- [ ] Download logs functionality
- [ ] Terraform modules (s3, kinesis, lambda, iam)
- [ ] CI/CD pipeline
- [ ] Multi-environment support

## 24. Support

**Issues?** Check:
1. Container status: `docker compose ps`
2. Container logs: `docker logs <container-name>`
3. Dashboard: http://localhost:8010
4. Test script: `./test-kinesis.sh`

**Questions?** See:
- [Full Pipeline README](../README.md)
- [Stage 00 README](../00-mock-servers/README.md)
- [Architecture docs](../../challenge-documents/architecture.md)

---

**Stage 01 Status**: ✅ Operational (Bước 1 Complete - 100%)

**Next**: Stage 01 Bước 2 (Terraform IaC) hoặc Stage 02 (ETL with AWS Glue)
