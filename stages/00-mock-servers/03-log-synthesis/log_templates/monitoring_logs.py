"""
Monitoring & Observability Logs - 3 loại log
Logs liên quan đến giám sát và quan sát hệ thống
"""

import random
from datetime import datetime
from .common import *

class MonitoringLogs:
    """Generator cho Monitoring & Observability Logs"""
    
    @staticmethod
    def generate_metrics_log(anomaly_score: float = 0.0) -> dict:
        """
        Metrics & Performance Logs
        Log các chỉ số hiệu suất hệ thống
        """
        metric_types = [
            "CPU_USAGE",
            "MEMORY_USAGE",
            "DISK_IO",
            "NETWORK_THROUGHPUT",
            "REQUEST_RATE",
            "ERROR_RATE",
            "RESPONSE_TIME"
        ]
        
        is_anomaly = anomaly_score > 0.7
        
        metric_type = random.choice(metric_types)
        
        if metric_type == "CPU_USAGE":
            value = random.uniform(85, 99) if is_anomaly else random.uniform(10, 70)
            unit = "percent"
            threshold = 80
        elif metric_type == "MEMORY_USAGE":
            value = random.uniform(85, 98) if is_anomaly else random.uniform(20, 75)
            unit = "percent"
            threshold = 85
        elif metric_type == "DISK_IO":
            value = random.uniform(800, 1000) if is_anomaly else random.uniform(50, 500)
            unit = "MB/s"
            threshold = 700
        elif metric_type == "NETWORK_THROUGHPUT":
            value = random.uniform(900, 1000) if is_anomaly else random.uniform(100, 700)
            unit = "Mbps"
            threshold = 850
        elif metric_type == "REQUEST_RATE":
            value = random.uniform(10000, 50000) if is_anomaly else random.uniform(100, 5000)
            unit = "req/s"
            threshold = 8000
        elif metric_type == "ERROR_RATE":
            value = random.uniform(5, 20) if is_anomaly else random.uniform(0, 2)
            unit = "percent"
            threshold = 3
        else:  # RESPONSE_TIME
            value = random.uniform(2000, 10000) if is_anomaly else random.uniform(50, 500)
            unit = "ms"
            threshold = 1000
        
        alert_triggered = value > threshold
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "metrics",
            "metric_name": metric_type,
            "value": round(value, 2),
            "unit": unit,
            "threshold": threshold,
            "alert_triggered": alert_triggered,
            "severity": "CRITICAL" if alert_triggered and is_anomaly else "WARNING" if alert_triggered else "INFO",
            "host": f"server-{random.randint(1, 20)}.banking.local",
            "service": random.choice(["api-gateway", "transaction-service", "auth-service", "database"]),
            "tags": {
                "environment": "production",
                "region": random.choice(["hanoi", "hochiminh", "danang"]),
                "cluster": f"cluster-{random.randint(1, 5)}"
            },
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_distributed_tracing_log(anomaly_score: float = 0.0) -> dict:
        """
        Distributed Tracing Logs (Jaeger, Zipkin)
        Log theo dõi request qua nhiều microservices
        """
        services = ["api-gateway", "auth-service", "account-service", "transaction-service", "notification-service"]
        operations = ["http.request", "db.query", "cache.get", "queue.publish", "external.api"]
        
        is_anomaly = anomaly_score > 0.7
        
        trace_id = f"TRACE-{random.randint(100000000000, 999999999999)}"
        span_id = f"SPAN-{random.randint(100000000, 999999999)}"
        
        service = random.choice(services)
        operation = random.choice(operations)
        
        if is_anomaly:
            duration_ms = random.randint(5000, 30000)
            status = "ERROR"
            error_message = random.choice([
                "Service timeout",
                "Connection refused",
                "Circuit breaker open",
                "Dependency failure"
            ])
        else:
            duration_ms = random.randint(10, 500)
            status = "OK"
            error_message = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "distributed_tracing",
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": f"SPAN-{random.randint(100000000, 999999999)}" if random.random() > 0.3 else None,
            "service_name": service,
            "operation_name": operation,
            "duration_ms": duration_ms,
            "status": status,
            "error_message": error_message,
            "tags": {
                "http.method": random.choice(["GET", "POST", "PUT"]),
                "http.status_code": 500 if status == "ERROR" else 200,
                "db.type": "postgresql" if operation == "db.query" else None,
                "peer.service": random.choice(services) if operation == "external.api" else None
            },
            "logs": [
                {"event": "request_started", "timestamp": datetime.now().isoformat()},
                {"event": "processing", "timestamp": datetime.now().isoformat()},
                {"event": "request_completed", "timestamp": datetime.now().isoformat()}
            ],
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_health_check_log(anomaly_score: float = 0.0) -> dict:
        """
        Health Check & Heartbeat Logs
        Log kiểm tra sức khỏe các services
        """
        services = [
            "api-gateway",
            "auth-service",
            "transaction-service",
            "database-primary",
            "database-replica",
            "redis-cache",
            "message-queue",
            "payment-gateway"
        ]
        
        is_anomaly = anomaly_score > 0.7
        
        service = random.choice(services)
        
        if is_anomaly:
            status = random.choice(["UNHEALTHY", "DEGRADED", "DOWN"])
            response_time_ms = random.randint(5000, 30000) if status != "DOWN" else None
            checks_failed = random.randint(1, 5)
            error_details = random.choice([
                "Database connection pool exhausted",
                "Memory usage above threshold",
                "Disk space critically low",
                "Service not responding",
                "Too many open connections"
            ])
        else:
            status = "HEALTHY"
            response_time_ms = random.randint(5, 100)
            checks_failed = 0
            error_details = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "health_check",
            "service_name": service,
            "status": status,
            "response_time_ms": response_time_ms,
            "checks_passed": 5 - checks_failed if status != "DOWN" else 0,
            "checks_failed": checks_failed,
            "total_checks": 5,
            "endpoint": f"http://{service}:8080/health",
            "host": f"{service}-{random.randint(1, 10)}.banking.local",
            "uptime_seconds": random.randint(0, 2592000),  # 0-30 days
            "error_details": error_details,
            "dependencies": {
                "database": "HEALTHY" if status == "HEALTHY" else random.choice(["HEALTHY", "UNHEALTHY"]),
                "cache": "HEALTHY" if status == "HEALTHY" else random.choice(["HEALTHY", "UNHEALTHY"]),
                "queue": "HEALTHY" if status == "HEALTHY" else random.choice(["HEALTHY", "UNHEALTHY"])
            },
            "anomaly_score": anomaly_score
        }
