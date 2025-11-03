"""
Application Layer Logs (6 types)
Web servers, frameworks, APM, message queues, service mesh, API gateways
"""
from datetime import datetime, timedelta
from typing import Dict, Any
import random
import uuid
from .common import LogCommonData

class ApplicationLogTemplates:
    """Application layer log generators"""
    
    @staticmethod
    def web_server_log(anomaly_score: float) -> Dict[str, Any]:
        """#10 Web Server Access Logs"""
        status = 500 if anomaly_score > 85 else (404 if anomaly_score > 75 else 200)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "web_server_access",
            "client_ip": f"{random.choice(LogCommonData.ISP_RANGES)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "user": f"user{random.randint(1000, 9999)}",
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "url": random.choice(["/api/v1/transfer", "/api/v1/balance", "/dashboard", "/login"]),
            "http_version": "HTTP/1.1",
            "status": status,
            "response_size": random.randint(512, 10240),
            "referrer": "https://bank.com/dashboard",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "response_time": random.uniform(0.5, 5.0) if anomaly_score > 70 else random.uniform(0.05, 0.5),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def application_framework_log(anomaly_score: float) -> Dict[str, Any]:
        """#11 Application Framework Logs"""
        level = "ERROR" if anomaly_score > 75 else ("WARNING" if anomaly_score > 50 else "INFO")
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "application_framework",
            "level": level,
            "logger": "com.bank.api.TransferController",
            "thread": f"http-nio-8080-exec-{random.randint(1, 20)}",
            "request_id": f"req-{uuid.uuid4().hex[:12]}",
            "session_id": f"sess-{uuid.uuid4().hex[:12]}",
            "user_id": f"user-{random.randint(10000, 99999)}",
            "method": "POST",
            "endpoint": "/api/v1/transfer",
            "transaction_id": f"txn-{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}",
            "amount": random.randint(100000, 10000000),
            "currency": "VND",
            "execution_time_ms": random.randint(500, 5000) if anomaly_score > 70 else random.randint(50, 500),
            "message": "Transfer failed" if level == "ERROR" else "Transfer completed successfully",
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def apm_trace_log(anomaly_score: float) -> Dict[str, Any]:
        """#12 Application Performance Monitoring (APM) Logs"""
        duration = random.randint(500, 3000) if anomaly_score > 70 else random.randint(50, 500)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "apm_trace",
            "trace_id": uuid.uuid4().hex,
            "span_id": uuid.uuid4().hex[:16],
            "parent_span_id": None,
            "name": "POST /api/v1/transfer",
            "start_time": datetime.now().isoformat() + "Z",
            "end_time": (datetime.now() + timedelta(milliseconds=duration)).isoformat() + "Z",
            "duration_ms": duration,
            "status": "ERROR" if anomaly_score > 85 else "OK",
            "attributes": {
                "http.method": "POST",
                "http.url": "/api/v1/transfer",
                "http.status_code": 500 if anomaly_score > 85 else 200,
                "user.id": f"user-{random.randint(10000, 99999)}",
                "transaction.id": f"txn-{random.randint(100000, 999999)}"
            },
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def message_queue_log(anomaly_score: float) -> Dict[str, Any]:
        """#13 Message Queue Logs"""
        queue_depth = random.randint(500, 5000) if anomaly_score > 70 else random.randint(10, 200)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "message_queue",
            "queue": "payment-processing",
            "event": random.choice(["message_published", "message_consumed", "message_acknowledged"]),
            "message_id": f"msg-{uuid.uuid4().hex[:12]}",
            "message_size_bytes": random.randint(512, 4096),
            "queue_depth": queue_depth,
            "message_age_seconds": random.randint(0, 300) if anomaly_score > 70 else random.randint(0, 10),
            "producer": "payment-service",
            "consumer": "notification-service",
            "priority": "high" if anomaly_score > 75 else "normal",
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def service_mesh_log(anomaly_score: float) -> Dict[str, Any]:
        """#14 Service Mesh Logs"""
        status = 500 if anomaly_score > 85 else 200
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "service_mesh",
            "source_service": "payment-service",
            "source_pod": f"payment-{uuid.uuid4().hex[:8]}",
            "destination_service": "account-service",
            "destination_pod": f"account-{uuid.uuid4().hex[:8]}",
            "method": "POST",
            "path": "/api/account/debit",
            "status_code": status,
            "duration_ms": random.randint(500, 3000) if anomaly_score > 70 else random.randint(20, 200),
            "bytes_sent": random.randint(256, 2048),
            "bytes_received": random.randint(128, 1024),
            "upstream_cluster": "account-service-cluster",
            "retry_count": random.randint(1, 3) if anomaly_score > 75 else 0,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def api_gateway_log(anomaly_score: float) -> Dict[str, Any]:
        """#15 API Gateway Logs"""
        rate_limit_remaining = 5 if anomaly_score > 80 else random.randint(50, 100)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "api_gateway",
            "api_gateway": "kong-prod",
            "client_ip": f"{random.choice(LogCommonData.ISP_RANGES)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "api_key": f"key-{uuid.uuid4().hex[:12]}",
            "method": "POST",
            "path": "/api/v1/transfer",
            "upstream_service": "payment-service",
            "upstream_url": "http://payment-service:8080/transfer",
            "status_code": 429 if anomaly_score > 85 else 200,
            "latency_ms": random.randint(500, 3000) if anomaly_score > 70 else random.randint(50, 300),
            "rate_limit_remaining": rate_limit_remaining,
            "rate_limit_limit": 100,
            "authentication": "failed" if anomaly_score > 80 else "success",
            "anomaly_score": anomaly_score
        }
