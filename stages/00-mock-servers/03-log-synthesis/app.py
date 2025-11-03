"""
Log Synthesis Engine
Transforms patterns into actual log entries with proper formatting
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import uuid
import random
import httpx

from comprehensive_logs import ComprehensiveLogGenerator

app = FastAPI(title="Log Synthesis Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LogRequest(BaseModel):
    log_type: str  # Any of the 59 comprehensive log types
    scenario_id: str
    count: int = 100
    anomaly_score: float = 0.0

class LogEntry(BaseModel):
    timestamp: str
    log_type: str
    data: Dict[str, Any]

# Log templates
class LogTemplates:
    """Templates for different log types"""
    
    @staticmethod
    def application_log(scenario_id: str, anomaly_score: float) -> Dict[str, Any]:
        """Generate application log entry"""
        severity_map = {
            range(0, 25): "INFO",
            range(25, 50): "WARNING",
            range(50, 75): "ERROR",
            range(75, 101): "CRITICAL"
        }
        
        severity = "INFO"
        for score_range, level in severity_map.items():
            if int(anomaly_score) in score_range:
                severity = level
                break
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "level": severity,
            "service": random.choice(["payment-service", "auth-service", "transfer-service", "account-service"]),
            "trace_id": str(uuid.uuid4()),
            "span_id": uuid.uuid4().hex[:8],
            "user_id": f"USR{random.randint(100000, 999999)}",
            "session_id": f"sess_{uuid.uuid4().hex[:12]}",
            "message": LogTemplates._get_message(severity, scenario_id),
            "error": LogTemplates._get_error(severity) if severity in ["ERROR", "CRITICAL"] else None,
            "context": {
                "transaction_id": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "amount": random.randint(100000, 10000000),
                "currency": "VND"
            },
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def security_log(scenario_id: str, anomaly_score: float) -> Dict[str, Any]:
        """Generate security log entry"""
        event_types = ["authentication_failure", "suspicious_activity", "unauthorized_access", "rate_limit_exceeded"]
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "event_type": random.choice(event_types),
            "severity": "CRITICAL" if anomaly_score > 75 else "WARNING",
            "source_ip": f"113.161.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "authentication": {
                "method": "password",
                "attempts": random.randint(1, 5),
                "account": f"user{random.randint(1000, 9999)}@example.com",
                "reason": "invalid_credentials" if anomaly_score > 50 else "success"
            },
            "risk_score": int(anomaly_score),
            "geo_location": {
                "country": "VN",
                "city": random.choice(["Ho Chi Minh City", "Hanoi", "Da Nang"]),
                "coordinates": [10.8231, 106.6297]
            },
            "anomaly_indicators": {
                "velocity_anomaly": anomaly_score > 60,
                "location_anomaly": anomaly_score > 70,
                "device_anomaly": anomaly_score > 80
            }
        }
    
    @staticmethod
    def transaction_log(scenario_id: str, anomaly_score: float) -> Dict[str, Any]:
        """Generate transaction log entry"""
        status = "failed" if anomaly_score > 70 else "completed"
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "transaction": {
                "id": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}",
                "type": random.choice(["transfer", "payment", "withdrawal", "deposit"]),
                "status": status,
                "amount": random.randint(100000, 50000000),
                "currency": "VND",
                "from_account": f"****{random.randint(1000, 9999)}",
                "to_account": f"****{random.randint(1000, 9999)}",
                "channel": random.choice(["mobile_app", "web", "atm", "branch"])
            },
            "processing": {
                "duration_ms": random.randint(100, 5000),
                "gateway": random.choice(["VNPAY", "MOMO", "ZALOPAY"]),
                "authorization_code": f"AUTH{random.randint(100, 999)}" if status == "completed" else None
            },
            "anomaly_indicators": {
                "velocity_score": anomaly_score / 100,
                "amount_deviation": random.uniform(0, 3),
                "time_deviation": random.uniform(0, 2),
                "pattern_match": "fraud" if anomaly_score > 80 else "normal"
            }
        }
    
    @staticmethod
    def _get_message(severity: str, scenario_id: str) -> str:
        """Generate appropriate message based on severity"""
        messages = {
            "INFO": ["Transaction processed successfully", "User authenticated", "Request completed"],
            "WARNING": ["High latency detected", "Retry attempt", "Resource usage elevated"],
            "ERROR": ["Payment processing failed", "Database connection timeout", "Service unavailable"],
            "CRITICAL": ["System overload detected", "Security breach attempt", "Data corruption detected"]
        }
        return random.choice(messages.get(severity, messages["INFO"]))
    
    @staticmethod
    def _get_error(severity: str) -> Dict[str, Any]:
        """Generate error details"""
        errors = {
            "ERROR": {
                "type": "ProcessingException",
                "code": f"ERR_{random.randint(100, 999)}",
                "details": "Operation failed due to temporary issue"
            },
            "CRITICAL": {
                "type": "SystemException",
                "code": f"CRIT_{random.randint(100, 999)}",
                "details": "Critical system failure detected"
            }
        }
        return errors.get(severity, errors["ERROR"])

# Storage
synthesized_logs: List[Dict[str, Any]] = []

# Continuous generation state and auto-forwarding
continuous_generation_state = {
    "enabled": False,
    "logs_per_second": 0,
    "total_generated": 0
}

INGESTION_URL = "http://ingestion-interface:8004"

comprehensive_generator = ComprehensiveLogGenerator()

@app.on_event("startup")
async def startup_event():
    print("[v0] Log Synthesis Engine started")
    print(f"[v0] Will forward logs to: {INGESTION_URL}")

@app.get("/")
async def root():
    """Serve the web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Synthesis Engine</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #333; border-bottom: 2px solid #FF9800; padding-bottom: 10px; }
            .controls { margin: 20px 0; display: flex; gap: 10px; flex-wrap: wrap; }
            select, input, button { padding: 10px; border-radius: 4px; border: 1px solid #ddd; }
            button { background: #FF9800; color: white; cursor: pointer; border: none; }
            button:hover { background: #F57C00; }
            .log-viewer { background: #263238; color: #aed581; padding: 15px; border-radius: 4px; font-family: monospace; max-height: 500px; overflow-y: auto; font-size: 12px; }
            .log-entry { margin: 10px 0; padding: 10px; background: #37474f; border-left: 3px solid #4CAF50; }
            .log-entry.error { border-left-color: #f44336; }
            .log-entry.warning { border-left-color: #FF9800; }
            .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
            .stat-card { background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center; }
            .stat-value { font-size: 24px; font-weight: bold; color: #F57C00; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Log Synthesis Engine</h1>
            <p>Transform patterns into formatted log entries</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalLogs">0</div>
                    <div>Total Logs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="appLogs">0</div>
                    <div>Application</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="secLogs">0</div>
                    <div>Security</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="txnLogs">0</div>
                    <div>Transaction</div>
                </div>
            </div>
            
            <div class="controls">
                <select id="logType">
                    <option value="application">Application Log</option>
                    <option value="security">Security Log</option>
                    <option value="transaction">Transaction Log</option>
                </select>
                <input type="number" id="count" placeholder="Count" value="10" min="1" max="1000">
                <input type="number" id="anomalyScore" placeholder="Anomaly Score (0-100)" value="50" min="0" max="100">
                <button onclick="generateLogs()">Generate Logs</button>
                <button onclick="clearLogs()">Clear</button>
                <button onclick="exportLogs()">Export JSON</button>
            </div>
            
            <div id="logViewer" class="log-viewer"></div>
        </div>
        
        <script>
            let logs = [];
            
            async function generateLogs() {
                const logType = document.getElementById('logType').value;
                const count = parseInt(document.getElementById('count').value);
                const anomalyScore = parseFloat(document.getElementById('anomalyScore').value);
                
                const response = await fetch('/api/synthesize', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        log_type: logType,
                        scenario_id: 'DEMO_001',
                        count: count,
                        anomaly_score: anomalyScore
                    })
                });
                
                const newLogs = await response.json();
                logs = [...newLogs, ...logs].slice(0, 100); // Keep last 100
                displayLogs();
                updateStats();
            }
            
            function displayLogs() {
                const viewer = document.getElementById('logViewer');
                viewer.innerHTML = logs.map(log => {
                    const severity = log.data.level || log.data.severity || 'INFO';
                    const cssClass = severity === 'ERROR' || severity === 'CRITICAL' ? 'error' : 
                                    severity === 'WARNING' ? 'warning' : '';
                    return `<div class="log-entry ${cssClass}">${JSON.stringify(log.data, null, 2)}</div>`;
                }).join('');
            }
            
            function updateStats() {
                document.getElementById('totalLogs').textContent = logs.length;
                document.getElementById('appLogs').textContent = logs.filter(l => l.log_type === 'application').length;
                document.getElementById('secLogs').textContent = logs.filter(l => l.log_type === 'security').length;
                document.getElementById('txnLogs').textContent = logs.filter(l => l.log_type === 'transaction').length;
            }
            
            function clearLogs() {
                logs = [];
                displayLogs();
                updateStats();
            }
            
            function exportLogs() {
                const dataStr = JSON.stringify(logs, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `logs_${new Date().toISOString()}.json`;
                link.click();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/synthesize", response_model=List[LogEntry])
async def synthesize_logs(request: LogRequest, background_tasks: BackgroundTasks):
    """Synthesize log entries based on request"""
    logs = []
    
    for i in range(request.count):
        # Vary anomaly score slightly for realism
        score = request.anomaly_score + random.uniform(-5, 5)
        score = max(0, min(100, score))
        
        try:
            log_data = comprehensive_generator.generate(request.log_type, score)
        except ValueError as e:
            print(f"[v0] Unknown log type '{request.log_type}', using application log as fallback")
            log_data = LogTemplates.application_log(request.scenario_id, score)
        
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            log_type=request.log_type,
            data=log_data
        )
        logs.append(log_entry)
        synthesized_logs.append(log_entry.dict())
    
    background_tasks.add_task(forward_to_ingestion, [log.dict() for log in logs])
    
    # Keep only last 10000 logs in memory
    if len(synthesized_logs) > 10000:
        synthesized_logs[:] = synthesized_logs[-10000:]
    
    continuous_generation_state["total_generated"] += len(logs)
    
    return logs

# Auto-forwarding function
async def forward_to_ingestion(logs: List[Dict[str, Any]]):
    """Forward synthesized logs to ingestion interface"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{INGESTION_URL}/api/ingest/batch",
                json={
                    "logs": logs,
                    "metadata": {
                        "source": "log-synthesis",
                        "timestamp": datetime.now().isoformat()
                    }
                },
                timeout=5.0
            )
    except Exception as e:
        print(f"[v0] Failed to forward logs to ingestion: {e}")

@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Get recent synthesized logs"""
    return synthesized_logs[-limit:]

@app.get("/api/logs/stats")
async def get_stats():
    """Get log statistics"""
    total = len(synthesized_logs)
    by_type = {}
    
    for log in synthesized_logs:
        log_type = log.get("log_type", "unknown")
        by_type[log_type] = by_type.get(log_type, 0) + 1
    
    return {
        "total_logs": total,
        "by_type": by_type,
        "last_generated": synthesized_logs[-1]["timestamp"] if synthesized_logs else None,
        "continuous_total": continuous_generation_state["total_generated"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "log-synthesis",
        "logs_in_memory": len(synthesized_logs)
    }

@app.get("/api/log-types")
async def get_log_types():
    """Get all available comprehensive log types"""
    return {
        "categories": comprehensive_generator.get_all_categories(),
        "total_types": len(comprehensive_generator.get_all_log_types()),
        "log_types": comprehensive_generator.get_all_log_types()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
