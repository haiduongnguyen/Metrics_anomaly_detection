# Stage 01 Dashboard - Ingestion Monitoring UI

## Tổng Quan

Web dashboard trực quan để monitor và quản lý Stage 01 - Ingestion Layer với:
- Real-time Kinesis stream statistics
- S3 bucket browser với partition analysis
- Log viewer tích hợp
- Consumer metrics monitoring

## Features

### 1. Summary Statistics
- Tổng quan về Kinesis streams (active/total)
- S3 objects count và total size
- Consumer status

### 2. Kinesis Stream Monitoring
- Stream status (ACTIVE/ERROR)
- Shard count
- Retention period
- Detailed metrics per stream

### 3. S3 Bucket Browser
- List objects trong bucket
- Partition structure analysis
- Object size và last modified
- Integrated log viewer

### 4. Log Viewer
- View JSONL content từ S3
- Pretty-print JSON formatting
- Support multi-line logs

## Access

**URL**: http://localhost:8010

```bash
# Direct access
open http://localhost:8010

# Or via browser
xdg-open http://localhost:8010
```

## API Endpoints

### Health Check
```
GET /health
```

### Summary Statistics
```
GET /api/stats/summary

Response:
{
  "kinesis": {
    "total_streams": 2,
    "active_streams": 2
  },
  "s3": {
    "total_buckets": 3,
    "total_objects": 15,
    "total_size_mb": 2.5
  },
  "consumer": {
    "status": "running"
  }
}
```

### Kinesis Streams
```
GET /api/kinesis/streams

Response:
{
  "streams": [
    {
      "name": "stage01-logs-stream",
      "status": "ACTIVE",
      "shard_count": 1,
      "retention_hours": 24
    }
  ],
  "total": 2,
  "active": 2
}
```

### Stream Metrics
```
GET /api/kinesis/stream/{stream_name}/metrics

Example:
GET /api/kinesis/stream/stage01-logs-stream/metrics
```

### S3 Buckets
```
GET /api/s3/buckets

Response:
{
  "buckets": [
    {
      "name": "md-raw-logs",
      "object_count": 10,
      "total_size": 1048576,
      "total_size_mb": 1.0
    }
  ],
  "total_buckets": 3,
  "total_objects": 15,
  "total_size_mb": 2.5
}
```

### Bucket Objects
```
GET /api/s3/bucket/{bucket_name}/objects?max_keys=100&prefix=service=api-gateway

Example:
GET /api/s3/bucket/md-raw-logs/objects?max_keys=50

Response:
{
  "bucket": "md-raw-logs",
  "objects": [
    {
      "key": "service=api-gateway/year=2025/month=11/day=09/hour=13/part-xxx.jsonl",
      "size": 58427,
      "size_kb": 57.05,
      "last_modified": "2025-11-09T13:24:33",
      "storage_class": "STANDARD"
    }
  ],
  "count": 10
}
```

### Partition Analysis
```
GET /api/s3/bucket/{bucket_name}/partitions

Example:
GET /api/s3/bucket/md-raw-logs/partitions

Response:
{
  "bucket": "md-raw-logs",
  "services": ["api-gateway", "auth-service", "payment-service"],
  "service_count": 3,
  "dates": ["2025-11-09"],
  "date_count": 1,
  "total_objects": 10
}
```

### Object Content
```
GET /api/s3/object/{bucket_name}/{key}?lines=10

Example:
GET /api/s3/object/md-raw-logs/service=api-gateway/year=2025/month=11/day=09/hour=13/part-xxx.jsonl?lines=10

Response:
{
  "bucket": "md-raw-logs",
  "key": "service=api-gateway/...",
  "lines_requested": 10,
  "lines_returned": 10,
  "logs": [
    {
      "timestamp": "2025-11-09T13:24:33Z",
      "service": "api-gateway",
      "level": "INFO",
      "message": "Request processed"
    }
  ]
}
```

## Usage

### Start Dashboard

```bash
# From stages directory
cd /home/son/Documents/cursor-projects/Metrics_anomaly_detection/stages

# Start dashboard (if not running)
docker compose up -d stage01-dashboard

# Check status
docker compose ps stage01-dashboard

# Check logs
docker compose logs -f stage01-dashboard
```

### Browse S3 Data

1. Open dashboard: http://localhost:8010
2. Select a bucket from dropdown (md-raw-logs, md-raw-metrics, md-raw-apm)
3. Click "Refresh" to load objects
4. Click "View Partitions" to see partition structure
5. Click "View" button on any object to see log content

### Monitor Kinesis

Dashboard automatically shows:
- Stream status (ACTIVE/ERROR)
- Number of shards
- Retention period
- Auto-refreshes every 10 seconds

### View Logs

1. Click on any S3 object in the browser
2. Log content will appear in the Log Viewer section
3. JSON is pretty-printed for easy reading
4. Shows up to 10 lines by default

## Auto-Refresh

Dashboard auto-refreshes every 10 seconds:
- Summary statistics
- Kinesis stream status
- S3 bucket counts

To disable auto-refresh, comment out this line in the HTML:
```javascript
// setInterval(refreshAll, 10000);
```

## Troubleshooting

### Dashboard not accessible

```bash
# Check if container is running
docker ps | grep stage01-dashboard

# Check logs
docker logs stage01-dashboard

# Restart
docker compose restart stage01-dashboard
```

### Can't see Kinesis streams

Verify LocalStack is healthy:
```bash
curl http://localhost:4566/_localstack/health
```

### Can't see S3 objects

```bash
# Check if buckets exist
awslocal s3 ls --endpoint-url http://localhost:4566

# Check if objects exist
awslocal s3 ls s3://md-raw-logs/ --recursive --endpoint-url http://localhost:4566
```

### API errors

Check dashboard logs:
```bash
docker logs stage01-dashboard | grep ERROR
```

## Screenshots

### Dashboard Main View
- Summary cards với key metrics
- Kinesis streams status
- S3 buckets overview

### S3 Browser
- Sortable table của objects
- File sizes và timestamps
- Quick view actions

### Log Viewer
- Dark theme code viewer
- Syntax-highlighted JSON
- Scrollable content

## Development

### Local Development

```bash
cd stages/01-ingestion/dashboard

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Access at http://localhost:8010
```

### Environment Variables

```yaml
AWS_ENDPOINT_URL: http://localstack:4566
AWS_DEFAULT_REGION: us-east-1
```

### Customization

Edit `app.py` to:
- Add more API endpoints
- Customize metrics
- Add new visualizations
- Integrate with consumer service

## Architecture

```
┌─────────────────────────────────────┐
│  Browser                            │
│  http://localhost:8010              │
└────────────┬────────────────────────┘
             │ HTTP
             ▼
┌─────────────────────────────────────┐
│  Stage 01 Dashboard (FastAPI)      │
│  Port: 8010                         │
└────────┬─────────────┬──────────────┘
         │             │
         │ boto3       │ boto3
         ▼             ▼
┌──────────────┐  ┌──────────────┐
│   Kinesis    │  │      S3      │
│  LocalStack  │  │  LocalStack  │
└──────────────┘  └──────────────┘
```

## Integration with Pipeline

Dashboard integrates seamlessly với full pipeline:

```
Stage 00 (Mock Servers)
    ↓
Ingestion Interface
    ↓
Kinesis Stream ◄─── [Dashboard monitors]
    ↓
Consumer
    ↓
S3 Raw Buckets ◄─── [Dashboard browses]
```

## Future Enhancements

- [ ] Consumer metrics integration
- [ ] Real-time log streaming (WebSocket)
- [ ] Alert notifications
- [ ] Download logs functionality
- [ ] Advanced filtering và search
- [ ] Performance charts (throughput, latency)
- [ ] Custom dashboards
- [ ] Export reports

## Support

- Main README: [../README.md](../README.md)
- Stage 01 Plan: [../plan.md](../plan.md)
- Full Pipeline: [../../README.md](../../README.md)

---

**Dashboard is now live at http://localhost:8010!** 🎉
