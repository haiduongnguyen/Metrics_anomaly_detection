"""
Ingestion Interface Service
Handles log injection to target systems with rate control
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json
from collections import deque
import os
from pathlib import Path
import httpx

# Import Kinesis producer
try:
    from kinesis_producer import KinesisProducer
    kinesis_producer = KinesisProducer()
except ImportError:
    kinesis_producer = None
    print("[Warning] Kinesis producer not available")

app = FastAPI(title="Ingestion Interface Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class IngestionConfig(BaseModel):
    target_type: str  # kafka, http, file, database
    target_url: Optional[str] = None
    rate_limit: int = 1000  # logs per second
    batch_size: int = 100

class LogBatch(BaseModel):
    logs: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class IngestionJob(BaseModel):
    job_id: str
    config: IngestionConfig
    status: str
    logs_sent: int = 0
    errors: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Storage
ingestion_jobs: Dict[str, IngestionJob] = {}
ingestion_queue: deque = deque(maxlen=10000)
metrics_history: List[Dict[str, Any]] = []

LOG_CATEGORIES = [
    "infrastructure",
    "application",
    "database",
    "security",
    "transaction",
    "fraud",
    "user_behavior",
    "compliance",
    "integration",
    "monitoring",
    "business_intelligence",
    "specialized",
    "anomaly"
]

LOGS_BASE_DIR = Path("/app/logs")
LOGS_BASE_DIR.mkdir(parents=True, exist_ok=True)

for category in LOG_CATEGORIES:
    (LOGS_BASE_DIR / category).mkdir(exist_ok=True)

print(f"[v0] Logs will be written to: {LOGS_BASE_DIR}")
print(f"[v0] Created {len(LOG_CATEGORIES)} log category directories")

# Rate limiter
class RateLimiter:
    def __init__(self, rate: int):
        self.rate = rate
        self.tokens = rate
        self.last_update = datetime.now()
    
    async def acquire(self, count: int = 1):
        """Acquire tokens for rate limiting"""
        now = datetime.now()
        elapsed = (now - self.last_update).total_seconds()
        
        # Refill tokens
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        if self.tokens >= count:
            self.tokens -= count
            return True
        
        # Wait for tokens
        wait_time = (count - self.tokens) / self.rate
        await asyncio.sleep(wait_time)
        self.tokens = 0
        return True

rate_limiter = RateLimiter(1000)

# Auto-ingestion mode for continuous operation
auto_ingestion_state = {
    "enabled": True,  # Auto-enabled by default
    "rate_limit": 1000,
    "total_ingested": 0,
    "last_minute_count": 0
}

# Log consolidation integration
CONSOLIDATION_URL = os.getenv("CONSOLIDATION_URL", "http://log-consolidation:8005")

async def forward_to_consolidation(logs: List[Dict[str, Any]]):
    """Forward logs to consolidation service for OpenTelemetry standardization"""
    try:
        # Prepare raw logs for consolidation
        raw_logs = []
        for log_item in logs:
            if log_item.get("log"):
                log_data = log_item["log"]
                raw_logs.append({
                    "source": log_data.get("source", "ingestion-interface"),
                    "timestamp": log_data.get("timestamp", datetime.now().isoformat()),
                    "log_type": log_data.get("log_type", "unknown"),
                    "data": log_data.get("data", {}),
                    "metadata": log_item.get("metadata", {})
                })
        
        if raw_logs:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{CONSOLIDATION_URL}/api/consolidate",
                    json={"logs": raw_logs},
                    timeout=5.0
                )
            print(f"[v0] Forwarded {len(raw_logs)} logs to consolidation service")
    
    except Exception as e:
        print(f"[v0] Failed to forward logs to consolidation: {e}")

@app.get("/")
async def root():
    """Serve the web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ingestion Interface</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #333; border-bottom: 2px solid #9C27B0; padding-bottom: 10px; }
            .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
            .metric-card { background: #f3e5f5; padding: 15px; border-radius: 8px; text-align: center; }
            .metric-value { font-size: 28px; font-weight: bold; color: #7B1FA2; }
            .metric-label { font-size: 12px; color: #666; margin-top: 5px; }
            .controls { margin: 20px 0; display: flex; gap: 10px; flex-wrap: wrap; }
            select, input, button { padding: 10px; border-radius: 4px; border: 1px solid #ddd; }
            button { background: #9C27B0; color: white; cursor: pointer; border: none; }
            button:hover { background: #7B1FA2; }
            .jobs { margin-top: 20px; }
            .job-card { background: #fafafa; padding: 15px; margin: 10px 0; border-left: 4px solid #9C27B0; border-radius: 4px; }
            .chart { background: #263238; color: #aed581; padding: 15px; border-radius: 4px; font-family: monospace; height: 200px; overflow-y: auto; }
            .status-running { color: #2196F3; }
            .status-completed { color: #4CAF50; }
            .status-failed { color: #f44336; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📤 Ingestion Interface Service</h1>
            <p>Manage log injection to target systems with rate control</p>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value" id="throughput">0</div>
                    <div class="metric-label">Logs/Second</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="totalSent">0</div>
                    <div class="metric-label">Total Sent</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="queueSize">0</div>
                    <div class="metric-label">Queue Size</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="errorRate">0%</div>
                    <div class="metric-label">Error Rate</div>
                </div>
            </div>
            
            <div class="controls">
                <select id="targetType">
                    <option value="kafka">Kafka</option>
                    <option value="http">HTTP Endpoint</option>
                    <option value="file">File System</option>
                    <option value="database">Database</option>
                </select>
                <input type="text" id="targetUrl" placeholder="Target URL (optional)">
                <input type="number" id="rateLimit" placeholder="Rate Limit" value="1000">
                <input type="number" id="batchSize" placeholder="Batch Size" value="100">
                <button onclick="startIngestion()">Start Ingestion</button>
                <button onclick="testConnection()">Test Connection</button>
            </div>
            
            <div class="jobs">
                <h2>Active Jobs</h2>
                <div id="jobs"></div>
            </div>
            
            <div style="margin-top: 20px;">
                <h2>Throughput Monitor</h2>
                <div id="chart" class="chart"></div>
            </div>
        </div>
        
        <script>
            let chartData = [];
            
            async function startIngestion() {
                const config = {
                    target_type: document.getElementById('targetType').value,
                    target_url: document.getElementById('targetUrl').value || null,
                    rate_limit: parseInt(document.getElementById('rateLimit').value),
                    batch_size: parseInt(document.getElementById('batchSize').value)
                };
                
                const response = await fetch('/api/ingest/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                alert(`Ingestion job started: ${result.job_id}`);
                loadJobs();
            }
            
            async function testConnection() {
                const targetType = document.getElementById('targetType').value;
                const response = await fetch(`/api/test/${targetType}`);
                const result = await response.json();
                alert(result.message);
            }
            
            async function loadJobs() {
                const response = await fetch('/api/jobs');
                const jobs = await response.json();
                
                const container = document.getElementById('jobs');
                container.innerHTML = jobs.map(j => `
                    <div class="job-card">
                        <strong>Job ${j.job_id}</strong>
                        <span class="status-${j.status}"> [${j.status.toUpperCase()}]</span>
                        <br>Target: ${j.config.target_type} | Rate: ${j.config.rate_limit}/s | Sent: ${j.logs_sent}
                        ${j.errors > 0 ? `<br><span style="color: #f44336;">Errors: ${j.errors}</span>` : ''}
                    </div>
                `).join('');
            }
            
            async function updateMetrics() {
                const response = await fetch('/api/metrics');
                const metrics = await response.json();
                
                document.getElementById('throughput').textContent = metrics.current_throughput;
                document.getElementById('totalSent').textContent = metrics.total_sent.toLocaleString();
                document.getElementById('queueSize').textContent = metrics.queue_size;
                document.getElementById('errorRate').textContent = metrics.error_rate.toFixed(2) + '%';
                
                // Update chart
                chartData.push({
                    time: new Date().toLocaleTimeString(),
                    throughput: metrics.current_throughput
                });
                if (chartData.length > 20) chartData.shift();
                
                const chart = document.getElementById('chart');
                chart.textContent = chartData.map(d => 
                    `${d.time}: ${'█'.repeat(Math.floor(d.throughput / 50))} ${d.throughput}/s`
                ).join('\n');
                chart.scrollTop = chart.scrollHeight;
            }
            
            loadJobs();
            updateMetrics();
            setInterval(() => { loadJobs(); updateMetrics(); }, 2000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/ingest/start")
async def start_ingestion(config: IngestionConfig, background_tasks: BackgroundTasks):
    """Start a new ingestion job"""
    import uuid
    job_id = str(uuid.uuid4())[:8]
    
    job = IngestionJob(
        job_id=job_id,
        config=config,
        status="running",
        started_at=datetime.now()
    )
    ingestion_jobs[job_id] = job
    
    # Start background ingestion
    background_tasks.add_task(run_ingestion, job_id)
    
    return {"job_id": job_id, "message": "Ingestion started"}

@app.post("/api/ingest/batch")
async def ingest_batch(batch: LogBatch, background_tasks: BackgroundTasks):
    """Ingest a batch of logs"""
    for log in batch.logs:
        ingestion_queue.append({
            "log": log,
            "timestamp": datetime.now().isoformat(),
            "metadata": batch.metadata
        })
    
    if auto_ingestion_state["enabled"]:
        background_tasks.add_task(process_queue_batch, len(batch.logs))
    
    return {
        "message": "Batch queued and processing",
        "count": len(batch.logs),
        "queue_size": len(ingestion_queue)
    }

def write_log_to_file(log_data: Dict[str, Any]):
    """Write log entry to appropriate file"""
    try:
        # Determine log type and file path
        log_type = log_data.get("log_type", "application")
        # Check anomaly score in the data field
        data = log_data.get("data", {})
        anomaly_score = data.get("anomaly_score", 0)
        is_anomaly = anomaly_score > 70  # Changed threshold to 70 for clearer anomaly detection
        
        category = determine_log_category(log_type)
        
        # Choose directory - anomalies go to anomaly folder
        if is_anomaly:
            log_dir = LOGS_BASE_DIR / "anomaly"
        else:
            log_dir = LOGS_BASE_DIR / category
        
        # Create filename with date
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"{log_type}_{date_str}.log"
        
        # Write log entry
        with open(log_file, "a", encoding="utf-8") as f:
            log_line = json.dumps(log_data, ensure_ascii=False)
            f.write(log_line + "\n")
        
        return True
    except Exception as e:
        print(f"[v0] Error writing log to file: {e}")
        return False

# Auto-processing function
async def process_queue_batch(count: int):
    """Process a batch from the queue automatically"""
    rate_limiter_local = RateLimiter(auto_ingestion_state["rate_limit"])
    
    try:
        await rate_limiter_local.acquire(count)
        
        processed = 0
        written = 0
        processed_logs = []
        
        while processed < count and ingestion_queue:
            log_item = ingestion_queue.popleft()
            
            if write_log_to_file(log_item["log"]):
                written += 1
            
            # Collect logs for forwarding to consolidation
            processed_logs.append(log_item)
            
            auto_ingestion_state["total_ingested"] += 1
            auto_ingestion_state["last_minute_count"] += 1
            processed += 1
        
        # Forward logs to consolidation service
        if processed_logs:
            await forward_to_consolidation(processed_logs)
        
        # Send logs to Kinesis (Stage 01 integration)
        if processed_logs and kinesis_producer:
            logs_data = [item.get("log") for item in processed_logs if item.get("log")]
            if logs_data:
                result = kinesis_producer.send_logs(logs_data)
                if result.get("success", 0) > 0:
                    print(f"[Kinesis] Sent {result['success']} logs to Kinesis stream")
        
        if auto_ingestion_state["total_ingested"] % 1000 == 0:
            print(f"[v0] Ingested {auto_ingestion_state['total_ingested']} logs, written {written} to files")
        
        # Record metrics
        metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "throughput": count,
            "job_id": "auto"
        })
        
    except Exception as e:
        print(f"[v0] Auto-ingestion error: {e}")

@app.get("/api/jobs", response_model=List[IngestionJob])
async def list_jobs():
    """List all ingestion jobs"""
    return list(ingestion_jobs.values())

@app.get("/api/metrics")
async def get_metrics():
    """Get current ingestion metrics"""
    total_sent = sum(job.logs_sent for job in ingestion_jobs.values()) + auto_ingestion_state["total_ingested"]
    total_errors = sum(job.errors for job in ingestion_jobs.values())
    
    # Calculate current throughput from recent history
    recent_metrics = metrics_history[-10:] if metrics_history else []
    current_throughput = sum(m.get("throughput", 0) for m in recent_metrics) // max(len(recent_metrics), 1)
    
    error_rate = (total_errors / max(total_sent, 1)) * 100 if total_sent > 0 else 0
    
    return {
        "current_throughput": current_throughput,
        "total_sent": total_sent,
        "queue_size": len(ingestion_queue),
        "error_rate": error_rate,
        "active_jobs": len([j for j in ingestion_jobs.values() if j.status == "running"]),
        "auto_ingestion_enabled": auto_ingestion_state["enabled"]
    }

@app.get("/api/test/{target_type}")
async def test_connection(target_type: str):
    """Test connection to target system"""
    # Simulate connection test
    await asyncio.sleep(0.5)
    
    return {
        "target_type": target_type,
        "status": "success",
        "message": f"Connection to {target_type} successful (simulated)",
        "latency_ms": 45
    }

async def run_ingestion(job_id: str):
    """Background task to run ingestion"""
    job = ingestion_jobs[job_id]
    rate_limiter_local = RateLimiter(job.config.rate_limit)
    
    try:
        # Simulate ingestion for 60 seconds
        for _ in range(60):
            if job.status != "running":
                break
            
            # Process batch
            batch_size = min(job.config.batch_size, len(ingestion_queue))
            
            if batch_size > 0:
                await rate_limiter_local.acquire(batch_size)
                
                # Simulate sending logs
                for _ in range(batch_size):
                    if ingestion_queue:
                        ingestion_queue.popleft()
                        job.logs_sent += 1
                
                # Record metrics
                metrics_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "throughput": batch_size,
                    "job_id": job_id
                })
            
            await asyncio.sleep(1)
        
        job.status = "completed"
        job.completed_at = datetime.now()
        
    except Exception as e:
        job.status = "failed"
        job.errors += 1
        job.completed_at = datetime.now()

@app.get("/api/logs/stats")
async def get_log_stats():
    """Get statistics about stored logs"""
    stats = {
        "base_directory": str(LOGS_BASE_DIR),
        "log_categories": {}
    }
    
    for category in LOG_CATEGORIES:
        log_dir = LOGS_BASE_DIR / category
        files = list(log_dir.glob("*.log"))
        
        total_lines = 0
        total_size = 0
        
        for file in files:
            try:
                total_size += file.stat().st_size
                with open(file, "r") as f:
                    total_lines += sum(1 for _ in f)
            except:
                pass
        
        stats["log_categories"][category] = {
            "files": len(files),
            "total_lines": total_lines,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    return stats

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ingestion-interface",
        "queue_size": len(ingestion_queue),
        "active_jobs": len([j for j in ingestion_jobs.values() if j.status == "running"])
    }

# Function to determine log category from log type
def determine_log_category(log_type: str) -> str:
    """Determine which category directory a log type belongs to"""
    category_mapping = {
        "infrastructure": [
            "server_log", "container_log", "network_log", "storage_log", 
            "cdn_log", "dns_log", "load_balancer_log", "firewall_log", "vpn_log"
        ],
        "application": [
            "application_log", "api_gateway_log", "microservice_log", 
            "middleware_log", "cache_log", "message_queue_log"
        ],
        "database": [
            "database_query_log", "database_connection_log", "database_transaction_log",
            "database_replication_log", "database_backup_log", "redis_cache_log",
            "mongodb_log", "elasticsearch_log"
        ],
        "security": [
            "authentication_log", "authorization_log", "waf_log", 
            "ids_ips_log", "dlp_log", "encryption_log", "certificate_log"
        ],
        "transaction": [
            "payment_transaction_log", "fund_transfer_log", "settlement_log", 
            "reconciliation_log", "clearing_log"
        ],
        "fraud": [
            "fraud_detection_log", "aml_screening_log", "risk_assessment_log"
        ],
        "user_behavior": [
            "user_session_log", "clickstream_log", "user_navigation_log", 
            "search_log", "conversion_log", "ab_test_log"
        ],
        "compliance": [
            "audit_trail_log", "regulatory_report_log", "compliance_check_log"
        ],
        "integration": [
            "third_party_api_log", "webhook_log", "partner_integration_log"
        ],
        "monitoring": [
            "metrics_log", "distributed_trace_log", "alert_log"
        ],
        "business_intelligence": [
            "bi_report_log", "data_warehouse_log"
        ],
        "specialized": [
            "ml_model_log", "blockchain_log"
        ]
    }
    
    log_type_lower = log_type.lower()
    
    # Direct match
    for category, log_types in category_mapping.items():
        if log_type_lower in log_types:
            return category
    
    # Fallback: keyword matching
    for category, log_types in category_mapping.items():
        for lt in log_types:
            if lt.replace("_log", "") in log_type_lower:
                return category
    
    return "application"  # Default category

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
