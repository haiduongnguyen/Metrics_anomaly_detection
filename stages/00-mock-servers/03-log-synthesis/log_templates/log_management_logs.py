"""
Log Management Infrastructure - 2 loại log
Logs về hạ tầng quản lý log
"""

import random
from datetime import datetime, timedelta
from .common import *

class LogManagementLogs:
    """Generator cho Log Management Infrastructure Logs"""
    
    @staticmethod
    def generate_log_aggregation_log(anomaly_score: float = 0.0) -> dict:
        """
        Log Aggregation & Forwarding Logs
        Log của hệ thống tổng hợp và chuyển tiếp log
        """
        sources = ["application-servers", "database-servers", "api-gateways", "load-balancers", "firewalls"]
        destinations = ["Elasticsearch", "Splunk", "CloudWatch", "DataDog", "Local Storage"]
        
        is_anomaly = anomaly_score > 0.7
        
        source = random.choice(sources)
        destination = random.choice(destinations)
        
        if is_anomaly:
            status = "FAILED"
            logs_processed = random.randint(0, 10000)
            logs_dropped = random.randint(10000, 100000)
            error = random.choice([
                "Destination unreachable",
                "Buffer overflow",
                "Rate limit exceeded",
                "Authentication failed",
                "Parsing error"
            ])
        else:
            status = "SUCCESS"
            logs_processed = random.randint(100000, 10000000)
            logs_dropped = random.randint(0, 100)
            error = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "log_aggregation",
            "source": source,
            "destination": destination,
            "status": status,
            "logs_received": logs_processed + logs_dropped,
            "logs_processed": logs_processed,
            "logs_dropped": logs_dropped,
            "logs_filtered": random.randint(0, 1000),
            "throughput_logs_per_second": random.randint(100, 50000),
            "data_volume_mb": round(random.uniform(10, 10000), 2),
            "processing_latency_ms": random.randint(10, 5000),
            "buffer_usage_percent": random.randint(10, 95),
            "error": error,
            "pipeline": f"pipeline-{random.randint(1, 10)}",
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_log_storage_log(anomaly_score: float = 0.0) -> dict:
        """
        Log Storage & Indexing Logs
        Log về lưu trữ và đánh index log
        """
        storage_types = ["Hot Storage", "Warm Storage", "Cold Storage", "Archive"]
        operations = ["WRITE", "READ", "INDEX", "COMPRESS", "ARCHIVE", "DELETE"]
        
        is_anomaly = anomaly_score > 0.7
        
        storage_type = random.choice(storage_types)
        operation = random.choice(operations)
        
        if is_anomaly:
            status = "FAILED"
            operation = random.choice(["WRITE", "INDEX"])
            error = random.choice([
                "Disk space full",
                "Index corruption detected",
                "Write timeout",
                "Replication lag too high",
                "Shard allocation failed"
            ])
            disk_usage_percent = random.randint(90, 99)
        else:
            status = "SUCCESS"
            error = None
            disk_usage_percent = random.randint(30, 85)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "log_storage",
            "storage_type": storage_type,
            "operation": operation,
            "status": status,
            "documents_affected": random.randint(1000, 1000000),
            "data_size_gb": round(random.uniform(0.1, 1000.0), 2),
            "operation_duration_ms": random.randint(100, 30000),
            "disk_usage_percent": disk_usage_percent,
            "disk_available_gb": round(random.uniform(10, 5000), 2),
            "index_name": f"logs-{datetime.now().strftime('%Y.%m.%d')}",
            "shard_count": random.randint(1, 20),
            "replica_count": random.randint(1, 3),
            "compression_ratio": round(random.uniform(2.0, 10.0), 2),
            "retention_days": random.choice([7, 30, 90, 365]),
            "error": error,
            "cluster": f"log-cluster-{random.randint(1, 5)}",
            "anomaly_score": anomaly_score
        }
