"""
Log Consolidation Service
Consolidates all logs from different sources into a unified OpenTelemetry LogRecord format
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import json
import uuid
import asyncio
from enum import Enum
import re
import os
from pathlib import Path

from log_record import LogRecordObject, Severity, LogAttribute
from log_normalizer import LogNormalizer
from log_aggregator import LogAggregator

app = FastAPI(title="Log Consolidation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class RawLogEntry(BaseModel):
    """Raw log entry from any source"""
    source: str  # log-synthesis, scenario-orchestrator, etc.
    timestamp: str
    log_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ConsolidatedLogRequest(BaseModel):
    logs: List[RawLogEntry]
    batch_id: Optional[str] = None

class ConsolidatedLogResponse(BaseModel):
    batch_id: str
    processed_count: int
    log_records: List[LogRecordObject]
    errors: List[str] = []

# Core components
log_normalizer = LogNormalizer()
log_aggregator = LogAggregator()

# Configuration - Default to disabled RAM storage to save memory
ENABLE_RAM_STORAGE = os.getenv("ENABLE_RAM_STORAGE", "false").lower() == "true"
ENABLE_FILE_STORAGE = os.getenv("ENABLE_FILE_STORAGE", "true").lower() == "true"
MAX_RAM_LOGS = int(os.getenv("MAX_RAM_LOGS", "1000"))  # Reduced from 10000 to save RAM

# In-memory storage for recent logs (configurable)
consolidated_logs: List[LogRecordObject] = []
logs_by_source: Dict[str, List[LogRecordObject]] = {}

# File storage configuration
LOGS_DIR = Path("/app/logs/consolidated")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_log_file_path() -> Path:
    """Get current day's log file path"""
    today = datetime.now().strftime("%Y%m%d")
    return LOGS_DIR / f"consolidated_logs_{today}.jsonl"

def write_log_to_file(log_record: LogRecordObject) -> None:
    """Write a single log record to file"""
    if not ENABLE_FILE_STORAGE:
        return
        
    try:
        # Convert to dict for JSON serialization
        log_dict = {
            "timestamp": log_record.timestamp,
            "body": log_record.body,
            "observed_timestamp": log_record.observed_timestamp,
            "severity_text": log_record.severity_text,
            "severity_number": log_record.severity_number,
            "trace_id": log_record.trace_id,
            "span_id": log_record.span_id,
            "attributes": log_record.attributes,
            "resource": {
                "attributes": log_record.resource.attributes
            } if log_record.resource else {},
            "instrumentation_scope": {
                "name": log_record.instrumentation_scope.name,
                "version": log_record.instrumentation_scope.version
            } if log_record.instrumentation_scope else {}
        }
        
        log_file = get_log_file_path()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_dict, ensure_ascii=False) + "\n")
            
    except Exception as e:
        print(f"[v0] Error writing log to file: {e}")

@app.on_event("startup")
async def startup_event():
    print("[v0] Log Consolidation Service started")
    print(f"[v0] RAM Storage: {'ENABLED' if ENABLE_RAM_STORAGE else 'DISABLED'}")
    print(f"[v0] File Storage: {'ENABLED' if ENABLE_FILE_STORAGE else 'DISABLED'}")
    if ENABLE_FILE_STORAGE:
        print(f"[v0] Log files directory: {LOGS_DIR}")
        print(f"[v0] Today's log file: {get_log_file_path()}")
    print("[v0] Ready to normalize logs to OpenTelemetry LogRecord format")

@app.get("/")
async def root():
    """Serve the web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Consolidation Service</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #333; border-bottom: 2px solid #FF5722; padding-bottom: 10px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
            .stat-card { background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stat-value { font-size: 28px; font-weight: bold; color: #FF5722; }
            .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
            .controls { margin: 20px 0; display: flex; gap: 10px; flex-wrap: wrap; }
            select, input, button { padding: 10px; border-radius: 4px; border: 1px solid #ddd; }
            button { background: #FF5722; color: white; cursor: pointer; border: none; }
            button:hover { background: #E64A19; }
            .log-viewer { background: #f5f5f5; padding: 15px; border-radius: 8px; max-height: 600px; overflow-y: auto; }
            .log-record { background: white; margin: 10px 0; padding: 15px; border-left: 4px solid #FF5722; border-radius: 4px; }
            .log-header { font-weight: bold; color: #333; margin-bottom: 10px; }
            .log-severity { padding: 2px 8px; border-radius: 12px; font-size: 11px; color: white; }
            .severity-low { background: #4CAF50; }
            .severity-medium { background: #FF9800; }
            .severity-high { background: #F44336; }
            .severity-critical { background: #9C27B0; }
            .log-attributes { background: #fafafa; padding: 10px; margin-top: 10px; border-radius: 4px; }
            .attribute { display: inline-block; background: #e0e0e0; padding: 4px 8px; margin: 2px; border-radius: 4px; font-size: 12px; }
            .filters { background: #f9f9f9; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 Log Consolidation Service</h1>
            <p>Chuẩn hóa tất cả log về định dạng OpenTelemetry LogRecord</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalLogs">0</div>
                    <div class="stat-label">Tổng Log</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="uniqueSources">0</div>
                    <div class="stat-label">Nguồn</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="severityHigh">0</div>
                    <div class="stat-label">Nguy cơ Cao</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="avgAnomaly">0.0</div>
                    <div class="stat-label">Trung bình Anomaly</div>
                </div>
            </div>
            
            <div class="filters">
                <h3>🔍 Bộ lọc</h3>
                <div class="controls">
                    <select id="sourceFilter">
                        <option value="">Tất cả nguồn</option>
                    </select>
                    <select id="severityFilter">
                        <option value="">Tất cả mức độ</option>
                        <option value="1">Thấp</option>
                        <option value="2">Trung bình</option>
                        <option value="3">Cao</option>
                        <option value="4">Nghiêm trọng</option>
                    </select>
                    <input type="text" id="searchFilter" placeholder="Tìm kiếm...">
                    <button onclick="applyFilters()">Áp dụng</button>
                    <button onclick="clearFilters()">Xóa lọc</button>
                </div>
            </div>
            
            <div class="controls">
                <button onclick="loadLogs()">🔄 Tải lại</button>
                <button onclick="exportLogs()">📥 Xuất JSON</button>
                <button onclick="simulateIngestion()">📦 Mô phỏng ingestion</button>
            </div>
            
            <div id="logViewer" class="log-viewer"></div>
        </div>
        
        <script>
            let logs = [];
            let filteredLogs = [];
            
            async function loadLogs() {
                try {
                    const response = await fetch('/api/consolidated-logs');
                    const result = await response.json();
                    logs = result.logs;
                    filteredLogs = logs;
                    displayLogs();
                    updateStats();
                    updateSourceFilter();
                } catch (error) {
                    console.error('Failed to load logs:', error);
                }
            }
            
            function updateSourceFilter() {
                const sourceFilter = document.getElementById('sourceFilter');
                const sources = [...new Set(logs.map(log => log.resource.attributes['service.name']))];
                
                sourceFilter.innerHTML = '<option value="">Tất cả nguồn</option>';
                sources.forEach(source => {
                    sourceFilter.innerHTML += `<option value="${source}">${source}</option>`;
                });
            }
            
            function displayLogs() {
                const viewer = document.getElementById('logViewer');
                
                if (filteredLogs.length === 0) {
                    viewer.innerHTML = '<p>Không có log nào để hiển thị</p>';
                    return;
                }
                
                viewer.innerHTML = filteredLogs.map(log => {
                    const severity = log.severity_number;
                    const severityClass = severity <= 9 ? 'low' : 
                                        severity <= 13 ? 'medium' : 
                                        severity <= 17 ? 'high' : 'critical';
                    
                    return `
                        <div class="log-record">
                            <div class="log-header">
                                <span class="log-severity severity-${severityClass}">
                                    ${log.severity_text}
                                </span>
                                <span style="margin-left: 10px;">
                                    ${new Date(log.timestamp).toLocaleString('vi-VN')}
                                </span>
                                <span style="margin-left: 10px; color: #666;">
                                    ${log.resource.attributes['service.name'] || 'unknown'}
                                </span>
                            </div>
                            <div><strong>Body:</strong> ${log.body}</div>
                            <div class="log-attributes">
                                <strong>Attributes:</strong><br>
                                ${Object.entries(log.attributes).map(([key, value]) => 
                                    `<span class="attribute">${key}: ${value}</span>`
                                ).join('')}
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            function updateStats() {
                document.getElementById('totalLogs').textContent = logs.length;
                
                const sources = new Set(logs.map(log => log.resource.attributes['service.name']));
                document.getElementById('uniqueSources').textContent = sources.size;
                
                const highSeverity = logs.filter(log => log.severity_number >= 17).length;
                document.getElementById('severityHigh').textContent = highSeverity;
                
                const anomalyScores = logs
                    .filter(log => log.attributes['anomaly_score'])
                    .map(log => parseFloat(log.attributes['anomaly_score']));
                const avgAnomaly = anomalyScores.length > 0 ? 
                    anomalyScores.reduce((a, b) => a + b, 0) / anomalyScores.length : 0;
                document.getElementById('avgAnomaly').textContent = avgAnomaly.toFixed(1);
            }
            
            function applyFilters() {
                const sourceFilter = document.getElementById('sourceFilter').value;
                const severityFilter = document.getElementById('severityFilter').value;
                const searchFilter = document.getElementById('searchFilter').value.toLowerCase();
                
                filteredLogs = logs.filter(log => {
                    // Source filter
                    if (sourceFilter && log.resource.attributes['service.name'] !== sourceFilter) {
                        return false;
                    }
                    
                    // Severity filter
                    if (severityFilter) {
                        const severityLevel = parseInt(severityFilter);
                        if (severityLevel === 1 && log.severity_number > 9) return false;
                        if (severityLevel === 2 && (log.severity_number <= 9 || log.severity_number > 13)) return false;
                        if (severityLevel === 3 && (log.severity_number <= 13 || log.severity_number > 17)) return false;
                        if (severityLevel === 4 && log.severity_number <= 17) return false;
                    }
                    
                    // Search filter
                    if (searchFilter) {
                        const searchText = (log.body + ' ' + JSON.stringify(log.attributes)).toLowerCase();
                        if (!searchText.includes(searchFilter)) {
                            return false;
                        }
                    }
                    
                    return true;
                });
                
                displayLogs();
            }
            
            function clearFilters() {
                document.getElementById('sourceFilter').value = '';
                document.getElementById('severityFilter').value = '';
                document.getElementById('searchFilter').value = '';
                filteredLogs = logs;
                displayLogs();
            }
            
            function exportLogs() {
                const dataStr = JSON.stringify(filteredLogs, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `consolidated_logs_${new Date().toISOString()}.json`;
                link.click();
            }
            
            async function simulateIngestion() {
                try {
                    const response = await fetch('/api/simulate/ingestion', {method: 'POST'});
                    const result = await response.json();
                    alert(`Đã mô phỏng ingestion: ${result.processed_count} logs processed`);
                    await loadLogs();
                } catch (error) {
                    console.error('Failed to simulate ingestion:', error);
                }
            }
            
            loadLogs();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/consolidate", response_model=ConsolidatedLogResponse)
async def consolidate_logs(request: ConsolidatedLogRequest):
    """Consolidate raw logs into standardized OpenTelemetry LogRecord format"""
    batch_id = request.batch_id or str(uuid.uuid4())
    processed_count = 0
    log_records = []
    errors = []
    
    try:
        for raw_log in request.logs:
            try:
                # Convert Pydantic model to dict for normalization
                raw_log_dict = raw_log.model_dump()
                
                # Normalize raw log to LogRecord
                log_record = log_normalizer.normalize(raw_log_dict)
                log_records.append(log_record)
                processed_count += 1
                
                # Write to file (enabled by default)
                write_log_to_file(log_record)
                
                # Store in memory only if enabled
                if ENABLE_RAM_STORAGE:
                    consolidated_logs.append(log_record)
                    if len(consolidated_logs) > MAX_RAM_LOGS:
                        consolidated_logs[:0] = []
                    
                    # Store by source in memory
                    source = raw_log_dict["source"]
                    if source not in logs_by_source:
                        logs_by_source[source] = []
                    logs_by_source[source].append(log_record)
                    if len(logs_by_source[source]) > MAX_RAM_LOGS:
                        logs_by_source[source][:0] = []
                    
            except Exception as e:
                error_source = raw_log.source if hasattr(raw_log, 'source') else raw_log_dict.get('source', 'unknown') if 'raw_log_dict' in locals() else 'unknown'
                errors.append(f"Failed to normalize log from {error_source}: {str(e)}")
                print(f"[v0] Debug - Error normalizing log: {e}")
                print(f"[v0] Raw log type: {type(raw_log)}")
                print(f"[v0] Raw log: {raw_log}")
                continue
        
        return ConsolidatedLogResponse(
            batch_id=batch_id,
            processed_count=processed_count,
            log_records=log_records,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {str(e)}")

@app.get("/api/consolidated-logs")
async def get_consolidated_logs():
    """Get all consolidated logs"""
    if ENABLE_RAM_STORAGE:
        return {
            "logs": consolidated_logs[-MAX_RAM_LOGS:],  # Return last RAM logs
            "total_count": len(consolidated_logs),
            "sources": list(logs_by_source.keys()),
            "storage_type": "ram"
        }
    else:
        # Read from file if RAM storage is disabled
        if not ENABLE_FILE_STORAGE:
            return {
                "logs": [],
                "total_count": 0,
                "sources": [],
                "storage_type": "none",
                "message": "Both RAM and file storage are disabled"
            }
        
        try:
            log_file = get_log_file_path()
            if not log_file.exists():
                return {
                    "logs": [],
                    "total_count": 0,
                    "sources": [],
                    "storage_type": "file",
                    "message": "No log files found"
                }
            
            logs = []
            sources = set()
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        log_data = json.loads(line)
                        logs.append(log_data)
                        if "resource" in log_data and "attributes" in log_data["resource"]:
                            service_name = log_data["resource"]["attributes"].get("service.name", "unknown")
                            sources.add(service_name)
            
            # Return last 1000 logs from file
            return {
                "logs": logs[-1000:],
                "total_count": len(logs),
                "sources": list(sources),
                "storage_type": "file"
            }
            
        except Exception as e:
            return {
                "logs": [],
                "total_count": 0,
                "sources": [],
                "storage_type": "file",
                "error": f"Failed to read logs from file: {str(e)}"
            }

@app.get("/api/consolidated-logs/by-source/{source}")
async def get_logs_by_source(source: str):
    """Get logs from specific source"""
    if ENABLE_RAM_STORAGE:
        return {
            "source": source,
            "logs": logs_by_source.get(source, []),
            "count": len(logs_by_source.get(source, [])),
            "storage_type": "ram"
        }
    else:
        # Read from file if RAM storage is disabled
        if not ENABLE_FILE_STORAGE:
            return {
                "source": source,
                "logs": [],
                "count": 0,
                "storage_type": "none",
                "message": "Both RAM and file storage are disabled"
            }
        
        try:
            log_file = get_log_file_path()
            if not log_file.exists():
                return {
                    "source": source,
                    "logs": [],
                    "count": 0,
                    "storage_type": "file",
                    "message": "No log files found"
                }
            
            logs = []
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        log_data = json.loads(line)
                        if "resource" in log_data and "attributes" in log_data["resource"]:
                            service_name = log_data["resource"]["attributes"].get("service.name", "unknown")
                            if service_name == source:
                                logs.append(log_data)
            
            return {
                "source": source,
                "logs": logs[-1000:],  # Return last 1000 logs
                "count": len(logs),
                "storage_type": "file"
            }
            
        except Exception as e:
            return {
                "source": source,
                "logs": [],
                "count": 0,
                "storage_type": "file",
                "error": f"Failed to read logs from file: {str(e)}"
            }

@app.post("/api/simulate/ingestion")
async def simulate_ingestion():
    """Simulate log ingestion from log-synthesis service"""
    try:
        # Simulate receiving logs from log-synthesis
        sample_logs = [
            {
                "source": "log-synthesis",
                "timestamp": datetime.now().isoformat(),
                "log_type": "security_log",
                "data": {
                    "event_type": "authentication_failure",
                    "user_id": "USR123456",
                    "ip_address": "113.161.1.1",
                    "anomaly_score": 85.5
                }
            },
            {
                "source": "log-synthesis",
                "timestamp": datetime.now().isoformat(),
                "log_type": "transaction_log",
                "data": {
                    "transaction_id": "TXN20250102103045789",
                    "amount": 5000000,
                    "currency": "VND",
                    "status": "completed",
                    "anomaly_score": 15.5
                }
            },
            {
                "source": "scenario-orchestrator",
                "timestamp": datetime.now().isoformat(),
                "log_type": "infrastructure_log",
                "data": {
                    "cpu_usage": 95.2,
                    "memory_usage": 28.5,
                    "server": "app-server-01",
                    "anomaly_score": 92.0
                }
            }
        ]
        
        request = ConsolidatedLogRequest(logs=sample_logs)
        result = await consolidate_logs(request)
        
        return {
            "message": "Ingestion simulation completed",
            "processed_count": result.processed_count,
            "batch_id": result.batch_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@app.get("/api/aggregation/stats")
async def get_aggregated_stats():
    """Get aggregated statistics across all logs"""
    if ENABLE_RAM_STORAGE:
        logs_to_analyze = consolidated_logs
        if not logs_to_analyze:
            return {"message": "No logs available"}
        stats = log_aggregator.aggregate_stats(logs_to_analyze)
        return stats
    elif ENABLE_FILE_STORAGE:
        # Read from file for analysis - return basic stats since aggregator expects LogRecordObject
        # For file storage mode, we'll skip detailed analysis to avoid memory issues
        total_logs = 0
        try:
            log_file = get_log_file_path()
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    total_logs = sum(1 for line in f if line.strip())
        except Exception:
            pass
            
        return {
            "message": "File storage mode - basic statistics only",
            "file_stats": {
                "total_logs": total_logs,
                "storage_type": "file",
                "ram_storage_disabled": True
            }
        }
    else:
        return {"message": "Both RAM and file storage are disabled"}

@app.get("/api/aggregation/timeline")
async def get_aggregated_timeline(minutes: int = 60):
    """Get aggregated timeline of logs"""
    logs_to_analyze = []
    
    if ENABLE_RAM_STORAGE:
        logs_to_analyze = consolidated_logs
    elif ENABLE_FILE_STORAGE:
        # Read from file for timeline - return empty since aggregator expects LogRecordObject
        return {
            "timeline": [],
            "message": "File storage mode - timeline analysis disabled to save memory",
            "storage_type": "file",
            "ram_storage_disabled": True
        }
    
    if not logs_to_analyze:
        return {"timeline": []}
    
    timeline = log_aggregator.aggregate_timeline(logs_to_analyze, minutes)
    return {"timeline": timeline}

@app.get("/health")
async def health_check():
    total_logs = 0
    
    if ENABLE_RAM_STORAGE:
        total_logs = len(consolidated_logs)
    elif ENABLE_FILE_STORAGE:
        try:
            log_file = get_log_file_path()
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    total_logs = sum(1 for line in f if line.strip())
        except Exception:
            pass
    
    return {
        "status": "healthy",
        "service": "log-consolidation",
        "total_logs": total_logs,
        "sources_count": len(logs_by_source) if ENABLE_RAM_STORAGE else 0,
        "ram_storage": ENABLE_RAM_STORAGE,
        "file_storage": ENABLE_FILE_STORAGE,
        "storage_type": "ram" if ENABLE_RAM_STORAGE else "file" if ENABLE_FILE_STORAGE else "none"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
