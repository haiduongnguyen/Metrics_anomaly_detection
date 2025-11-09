"""
Stage 01 - Ingestion Dashboard
Web UI để monitor Kinesis, S3, và Consumer metrics
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import boto3
import os
import json

app = FastAPI(title="Stage 01 Ingestion Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS Configuration
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', 'http://localstack:4566')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

# Initialize boto3 clients
kinesis_client = boto3.client(
    'kinesis',
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

s3_client = boto3.client(
    's3',
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Configuration
KINESIS_STREAMS = ['stage01-logs-stream', 'stage01-metrics-stream']
S3_BUCKETS = ['md-raw-logs', 'md-raw-metrics', 'md-raw-apm']

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "stage01-dashboard",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/kinesis/streams")
async def get_kinesis_streams():
    """Get all Kinesis streams status"""
    try:
        streams_info = []
        
        for stream_name in KINESIS_STREAMS:
            try:
                response = kinesis_client.describe_stream_summary(StreamName=stream_name)
                summary = response['StreamDescriptionSummary']
                
                streams_info.append({
                    'name': stream_name,
                    'status': summary['StreamStatus'],
                    'shard_count': summary['OpenShardCount'],
                    'retention_hours': summary['RetentionPeriodHours'],
                    'created_at': summary['StreamCreationTimestamp'].isoformat() if 'StreamCreationTimestamp' in summary else None,
                    'error': None
                })
            except Exception as e:
                streams_info.append({
                    'name': stream_name,
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        return {
            'streams': streams_info,
            'total': len(streams_info),
            'active': sum(1 for s in streams_info if s['status'] == 'ACTIVE')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kinesis/stream/{stream_name}/metrics")
async def get_stream_metrics(stream_name: str):
    """Get metrics for a specific stream"""
    try:
        response = kinesis_client.describe_stream(StreamName=stream_name)
        stream_desc = response['StreamDescription']
        
        # Get shard details
        shards = []
        for shard in stream_desc['Shards']:
            shards.append({
                'shard_id': shard['ShardId'],
                'hash_range': {
                    'start': shard['HashKeyRange']['StartingHashKey'],
                    'end': shard['HashKeyRange']['EndingHashKey']
                },
                'sequence_range': shard['SequenceNumberRange']
            })
        
        return {
            'stream_name': stream_name,
            'status': stream_desc['StreamStatus'],
            'arn': stream_desc['StreamARN'],
            'retention_hours': stream_desc['RetentionPeriodHours'],
            'shards': shards,
            'shard_count': len(shards),
            'encryption': stream_desc.get('EncryptionType', 'NONE')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/s3/buckets")
async def get_s3_buckets():
    """Get all S3 buckets status"""
    try:
        buckets_info = []
        
        for bucket_name in S3_BUCKETS:
            try:
                # List objects in bucket
                response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
                
                objects = response.get('Contents', [])
                total_size = sum(obj['Size'] for obj in objects)
                
                buckets_info.append({
                    'name': bucket_name,
                    'object_count': len(objects),
                    'total_size': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'error': None
                })
            except Exception as e:
                buckets_info.append({
                    'name': bucket_name,
                    'object_count': 0,
                    'total_size': 0,
                    'error': str(e)
                })
        
        return {
            'buckets': buckets_info,
            'total_buckets': len(buckets_info),
            'total_objects': sum(b['object_count'] for b in buckets_info),
            'total_size_mb': sum(b.get('total_size_mb', 0) for b in buckets_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/s3/bucket/{bucket_name}/objects")
async def get_bucket_objects(
    bucket_name: str,
    prefix: Optional[str] = None,
    max_keys: int = 100
):
    """Get objects in a bucket"""
    try:
        params = {
            'Bucket': bucket_name,
            'MaxKeys': max_keys
        }
        if prefix:
            params['Prefix'] = prefix
        
        response = s3_client.list_objects_v2(**params)
        
        objects = []
        for obj in response.get('Contents', []):
            objects.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'size_kb': round(obj['Size'] / 1024, 2),
                'last_modified': obj['LastModified'].isoformat(),
                'storage_class': obj.get('StorageClass', 'STANDARD')
            })
        
        return {
            'bucket': bucket_name,
            'prefix': prefix,
            'objects': objects,
            'count': len(objects),
            'is_truncated': response.get('IsTruncated', False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/s3/bucket/{bucket_name}/partitions")
async def get_bucket_partitions(bucket_name: str):
    """Get partition structure summary"""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        objects = response.get('Contents', [])
        
        # Analyze partitions
        services = set()
        dates = set()
        
        for obj in objects:
            key = obj['Key']
            parts = key.split('/')
            
            # Extract service
            if parts[0].startswith('service='):
                services.add(parts[0].split('=')[1])
            
            # Extract date
            if len(parts) >= 4:
                year = parts[1].split('=')[1] if parts[1].startswith('year=') else None
                month = parts[2].split('=')[1] if parts[2].startswith('month=') else None
                day = parts[3].split('=')[1] if parts[3].startswith('day=') else None
                
                if year and month and day:
                    dates.add(f"{year}-{month}-{day}")
        
        return {
            'bucket': bucket_name,
            'services': sorted(list(services)),
            'service_count': len(services),
            'dates': sorted(list(dates)),
            'date_count': len(dates),
            'total_objects': len(objects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/s3/object/{bucket_name}/{key:path}")
async def get_object_content(bucket_name: str, key: str, lines: int = 10):
    """Get content of an S3 object"""
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        # Parse JSONL
        log_lines = []
        for line in content.strip().split('\n')[:lines]:
            try:
                log_lines.append(json.loads(line))
            except:
                log_lines.append({"raw": line})
        
        return {
            'bucket': bucket_name,
            'key': key,
            'lines_requested': lines,
            'lines_returned': len(log_lines),
            'logs': log_lines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/summary")
async def get_summary_stats():
    """Get overall summary statistics"""
    try:
        # Kinesis stats
        kinesis_data = await get_kinesis_streams()
        
        # S3 stats
        s3_data = await get_s3_buckets()
        
        # Consumer stats (would come from actual consumer service)
        consumer_stats = {
            'status': 'running',
            'records_processed': 0,  # Placeholder
            'last_poll': None
        }
        
        return {
            'kinesis': {
                'total_streams': kinesis_data['total'],
                'active_streams': kinesis_data['active']
            },
            's3': {
                'total_buckets': s3_data['total_buckets'],
                'total_objects': s3_data['total_objects'],
                'total_size_mb': s3_data['total_size_mb']
            },
            'consumer': consumer_stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard UI"""
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stage 01 - Ingestion Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            
            h1 {
                color: #667eea;
                margin-bottom: 10px;
            }
            
            .subtitle {
                color: #666;
                font-size: 14px;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .card-title {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #667eea;
            }
            
            .metric {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }
            
            .metric:last-child {
                border-bottom: none;
            }
            
            .metric-label {
                color: #666;
            }
            
            .metric-value {
                font-weight: bold;
                color: #333;
            }
            
            .status-badge {
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .status-active {
                background: #d4edda;
                color: #155724;
            }
            
            .status-error {
                background: #f8d7da;
                color: #721c24;
            }
            
            .table-container {
                max-height: 400px;
                overflow-y: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
            }
            
            th {
                background: #667eea;
                color: white;
                padding: 10px;
                text-align: left;
                position: sticky;
                top: 0;
            }
            
            td {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            
            tr:hover {
                background: #f8f9fa;
            }
            
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                margin: 5px;
            }
            
            button:hover {
                background: #5568d3;
            }
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #666;
            }
            
            .actions {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            .log-viewer {
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                max-height: 400px;
                overflow-y: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Stage 01 - Ingestion Dashboard</h1>
                <p class="subtitle">Monitor Kinesis Streams, S3 Buckets, và Consumer Performance</p>
                <p class="subtitle">Last updated: <span id="lastUpdate">Loading...</span></p>
            </div>
            
            <div class="grid">
                <!-- Summary Card -->
                <div class="card">
                    <div class="card-title">📊 Summary Statistics</div>
                    <div id="summaryStats" class="loading">Loading...</div>
                </div>
                
                <!-- Kinesis Streams Card -->
                <div class="card">
                    <div class="card-title">📡 Kinesis Streams</div>
                    <div id="kinesisStreams" class="loading">Loading...</div>
                </div>
                
                <!-- S3 Buckets Card -->
                <div class="card">
                    <div class="card-title">🗄️ S3 Buckets</div>
                    <div id="s3Buckets" class="loading">Loading...</div>
                </div>
            </div>
            
            <!-- S3 Browser -->
            <div class="card">
                <div class="card-title">📁 S3 Object Browser</div>
                <div class="actions">
                    <select id="bucketSelect" onchange="loadBucketObjects()">
                        <option value="">Select bucket...</option>
                        <option value="md-raw-logs">md-raw-logs</option>
                        <option value="md-raw-metrics">md-raw-metrics</option>
                        <option value="md-raw-apm">md-raw-apm</option>
                    </select>
                    <button onclick="loadBucketObjects()">Refresh</button>
                    <button onclick="loadPartitions()">View Partitions</button>
                </div>
                <div id="s3Objects" class="table-container">
                    <p class="loading">Select a bucket to view objects</p>
                </div>
            </div>
            
            <!-- Log Viewer -->
            <div class="card">
                <div class="card-title">📄 Log Viewer</div>
                <div id="logViewer" class="log-viewer">
                    Click on an S3 object to view its content...
                </div>
            </div>
        </div>
        
        <script>
            async function fetchData(url) {
                const response = await fetch(url);
                if (!response.ok) throw new Error('Network error');
                return await response.json();
            }
            
            async function loadSummary() {
                try {
                    const data = await fetchData('/api/stats/summary');
                    document.getElementById('summaryStats').innerHTML = `
                        <div class="metric">
                            <span class="metric-label">Kinesis Streams</span>
                            <span class="metric-value">${data.kinesis.active_streams}/${data.kinesis.total_streams} Active</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">S3 Objects</span>
                            <span class="metric-value">${data.s3.total_objects}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Total Size</span>
                            <span class="metric-value">${data.s3.total_size_mb.toFixed(2)} MB</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Consumer Status</span>
                            <span class="metric-value">${data.consumer.status}</span>
                        </div>
                    `;
                } catch (e) {
                    document.getElementById('summaryStats').innerHTML = '<div class="loading">Error loading data</div>';
                }
            }
            
            async function loadKinesisStreams() {
                try {
                    const data = await fetchData('/api/kinesis/streams');
                    let html = '';
                    data.streams.forEach(stream => {
                        const statusClass = stream.status === 'ACTIVE' ? 'status-active' : 'status-error';
                        html += `
                            <div class="metric">
                                <span class="metric-label">${stream.name}</span>
                                <span class="status-badge ${statusClass}">${stream.status}</span>
                            </div>
                        `;
                    });
                    document.getElementById('kinesisStreams').innerHTML = html;
                } catch (e) {
                    document.getElementById('kinesisStreams').innerHTML = '<div class="loading">Error loading streams</div>';
                }
            }
            
            async function loadS3Buckets() {
                try {
                    const data = await fetchData('/api/s3/buckets');
                    let html = '';
                    data.buckets.forEach(bucket => {
                        html += `
                            <div class="metric">
                                <span class="metric-label">${bucket.name}</span>
                                <span class="metric-value">${bucket.object_count} objects (${bucket.total_size_mb} MB)</span>
                            </div>
                        `;
                    });
                    document.getElementById('s3Buckets').innerHTML = html;
                } catch (e) {
                    document.getElementById('s3Buckets').innerHTML = '<div class="loading">Error loading buckets</div>';
                }
            }
            
            async function loadBucketObjects() {
                const bucket = document.getElementById('bucketSelect').value;
                if (!bucket) return;
                
                try {
                    const data = await fetchData(`/api/s3/bucket/${bucket}/objects?max_keys=50`);
                    let html = '<table><tr><th>Key</th><th>Size (KB)</th><th>Last Modified</th><th>Action</th></tr>';
                    data.objects.forEach(obj => {
                        html += `
                            <tr>
                                <td>${obj.key}</td>
                                <td>${obj.size_kb}</td>
                                <td>${new Date(obj.last_modified).toLocaleString()}</td>
                                <td><button onclick="viewLog('${bucket}', '${obj.key}')">View</button></td>
                            </tr>
                        `;
                    });
                    html += '</table>';
                    document.getElementById('s3Objects').innerHTML = html;
                } catch (e) {
                    document.getElementById('s3Objects').innerHTML = '<div class="loading">Error loading objects</div>';
                }
            }
            
            async function loadPartitions() {
                const bucket = document.getElementById('bucketSelect').value;
                if (!bucket) return;
                
                try {
                    const data = await fetchData(`/api/s3/bucket/${bucket}/partitions`);
                    let html = `
                        <h3>Partition Analysis</h3>
                        <p><strong>Services:</strong> ${data.services.join(', ')}</p>
                        <p><strong>Dates:</strong> ${data.dates.join(', ')}</p>
                        <p><strong>Total Objects:</strong> ${data.total_objects}</p>
                    `;
                    document.getElementById('s3Objects').innerHTML = html;
                } catch (e) {
                    document.getElementById('s3Objects').innerHTML = '<div class="loading">Error loading partitions</div>';
                }
            }
            
            async function viewLog(bucket, key) {
                try {
                    const data = await fetchData(`/api/s3/object/${bucket}/${encodeURIComponent(key)}?lines=10`);
                    document.getElementById('logViewer').textContent = JSON.stringify(data.logs, null, 2);
                } catch (e) {
                    document.getElementById('logViewer').textContent = 'Error loading log content';
                }
            }
            
            function updateTimestamp() {
                document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
            }
            
            function refreshAll() {
                updateTimestamp();
                loadSummary();
                loadKinesisStreams();
                loadS3Buckets();
            }
            
            // Initial load
            refreshAll();
            
            // Auto-refresh every 10 seconds
            setInterval(refreshAll, 10000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
