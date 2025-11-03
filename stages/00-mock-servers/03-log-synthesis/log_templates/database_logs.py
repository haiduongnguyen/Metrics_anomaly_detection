"""
Database & Data Store Logs (8 types)
SQL databases, NoSQL, caching, replication, backups
"""
from datetime import datetime, timedelta
from typing import Dict, Any
import random
import uuid

class DatabaseLogTemplates:
    """Database and data store log generators"""
    
    @staticmethod
    def database_query_log(anomaly_score: float) -> Dict[str, Any]:
        """#16 Database Query Logs"""
        query_time = random.uniform(2.0, 10.0) if anomaly_score > 70 else random.uniform(0.01, 0.5)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "database_query",
            "database": "banking_db",
            "user": "app_user",
            "host": f"app-server-{random.randint(1, 10):02d}",
            "query_time": query_time,
            "lock_time": random.uniform(0.0, 1.0) if anomaly_score > 75 else 0.0,
            "rows_sent": random.randint(1, 1000),
            "rows_examined": random.randint(1000, 1000000) if anomaly_score > 70 else random.randint(1, 10000),
            "query": "SELECT * FROM transactions WHERE user_id = ? AND created_at > ?",
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def database_connection_log(anomaly_score: float) -> Dict[str, Any]:
        """#17 Database Connection Logs"""
        active_connections = random.randint(80, 100) if anomaly_score > 70 else random.randint(20, 60)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "database_connection",
            "pool": "main-db-pool",
            "event": random.choice(["connection_acquired", "connection_released", "connection_timeout" if anomaly_score > 80 else "connection_acquired"]),
            "connection_id": f"conn-{random.randint(100, 999)}",
            "active_connections": active_connections,
            "idle_connections": 100 - active_connections,
            "max_connections": 100,
            "wait_time_ms": random.randint(100, 5000) if anomaly_score > 75 else random.randint(0, 50),
            "client": f"app-server-{random.randint(1, 10):02d}",
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def database_transaction_log(anomaly_score: float) -> Dict[str, Any]:
        """#18 Database Transaction Logs"""
        event = "transaction_rollback" if anomaly_score > 85 else "transaction_commit"
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "database_transaction",
            "database": "banking_db",
            "event": event,
            "transaction_id": f"txn-{uuid.uuid4().hex[:12]}",
            "isolation_level": "READ_COMMITTED",
            "duration_ms": random.randint(500, 5000) if anomaly_score > 70 else random.randint(10, 200),
            "queries_executed": random.randint(1, 10),
            "rows_affected": random.randint(1, 100),
            "locks_acquired": random.randint(1, 10),
            "deadlock_detected": anomaly_score > 90,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def database_replication_log(anomaly_score: float) -> Dict[str, Any]:
        """#19 Database Replication Logs"""
        replication_lag = random.randint(30, 300) if anomaly_score > 70 else random.randint(0, 10)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "database_replication",
            "master": "db-master-01",
            "slave": f"db-slave-{random.randint(1, 3):02d}",
            "replication_lag_seconds": replication_lag,
            "master_binlog_file": f"mysql-bin.{random.randint(100, 999):06d}",
            "master_binlog_position": random.randint(100000, 999999),
            "slave_io_running": "No" if anomaly_score > 85 else "Yes",
            "slave_sql_running": "No" if anomaly_score > 85 else "Yes",
            "last_error": "Connection lost" if anomaly_score > 85 else None,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def database_backup_log(anomaly_score: float) -> Dict[str, Any]:
        """#20 Database Backup & Recovery Logs"""
        status = "failed" if anomaly_score > 85 else "success"
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "database_backup",
            "event": "backup_completed",
            "database": "banking_db",
            "backup_type": random.choice(["full", "incremental"]),
            "backup_file": f"/backups/banking_db_{datetime.now().strftime('%Y%m%d')}.sql.gz",
            "backup_size_gb": random.uniform(50.0, 200.0),
            "duration_minutes": random.randint(60, 180) if anomaly_score > 70 else random.randint(20, 60),
            "status": status,
            "verification": "failed" if anomaly_score > 85 else "passed",
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def redis_cache_log(anomaly_score: float) -> Dict[str, Any]:
        """#21 Redis/Cache Logs"""
        result = "MISS" if anomaly_score > 70 else random.choice(["HIT", "HIT", "HIT", "MISS"])
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "redis_cache",
            "cache": "redis-prod",
            "operation": random.choice(["GET", "SET", "DEL"]),
            "key": f"user:{random.randint(10000, 99999)}:session",
            "result": result,
            "execution_time_us": random.randint(500, 5000) if anomaly_score > 75 else random.randint(50, 500),
            "memory_used_mb": random.randint(2048, 3800) if anomaly_score > 70 else random.randint(1024, 2500),
            "memory_max_mb": 4096,
            "evicted_keys": random.randint(100, 1000) if anomaly_score > 75 else 0,
            "hit_rate": 0.50 if anomaly_score > 70 else 0.95,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def mongodb_log(anomaly_score: float) -> Dict[str, Any]:
        """#22 MongoDB Logs"""
        execution_time = random.randint(500, 5000) if anomaly_score > 70 else random.randint(5, 100)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "mongodb",
            "severity": "I",
            "component": "COMMAND",
            "context": f"conn{random.randint(100, 999)}",
            "database": "banking_db",
            "collection": "users",
            "operation": "find",
            "query": {"user_id": random.randint(10000, 99999)},
            "plan_summary": "IXSCAN { user_id: 1 }" if anomaly_score < 70 else "COLLSCAN",
            "keys_examined": 1 if anomaly_score < 70 else random.randint(1000, 10000),
            "docs_examined": 1 if anomaly_score < 70 else random.randint(1000, 10000),
            "n_returned": 1,
            "execution_time_ms": execution_time,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def elasticsearch_log(anomaly_score: float) -> Dict[str, Any]:
        """#23 Elasticsearch Logs"""
        took_time = random.randint(2000, 10000) if anomaly_score > 70 else random.randint(10, 500)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "elasticsearch",
            "type": "index_search_slowlog",
            "cluster_name": "banking-cluster",
            "node_name": f"es-node-{random.randint(1, 5):02d}",
            "index_name": f"transactions-{datetime.now().strftime('%Y-%m')}",
            "shard": random.randint(0, 4),
            "took_ms": took_time,
            "total_shards": 5,
            "search_type": "QUERY_THEN_FETCH",
            "query": {"match": {"user_id": random.randint(10000, 99999)}},
            "anomaly_score": anomaly_score
        }
