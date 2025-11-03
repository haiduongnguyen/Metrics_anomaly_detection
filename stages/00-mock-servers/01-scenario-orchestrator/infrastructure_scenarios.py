"""
Infrastructure & System Performance Scenarios
20 predefined anomaly cases with detailed metrics and detection logic
"""
from typing import Dict, List, Any
from enum import Enum

class InfraScenarioType(str, Enum):
    CPU_SPIKE = "cpu_spike"
    MEMORY_LEAK = "memory_leak"
    DB_POOL_EXHAUSTION = "db_pool_exhaustion"
    DISK_IO_BOTTLENECK = "disk_io_bottleneck"
    NETWORK_LATENCY = "network_latency"
    API_DEGRADATION = "api_degradation"
    THREAD_POOL_SATURATION = "thread_pool_saturation"
    CACHE_INVALIDATION = "cache_invalidation"
    LOAD_BALANCER_UNEVEN = "load_balancer_uneven"
    MESSAGE_QUEUE_BACKLOG = "message_queue_backlog"
    DATABASE_DEADLOCK = "database_deadlock"
    CONNECTION_TIMEOUT = "connection_timeout"
    GC_PRESSURE = "gc_pressure"
    CONTAINER_OOM = "container_oom"
    SERVICE_MESH_FAILURE = "service_mesh_failure"
    DNS_RESOLUTION_SLOW = "dns_resolution_slow"
    SSL_HANDSHAKE_FAILURE = "ssl_handshake_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    REPLICA_LAG = "replica_lag"

# Comprehensive scenario definitions
INFRASTRUCTURE_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "cpu_spike": {
        "id": "INFRA_001",
        "name": "CPU Spike đột ngột trên Application Server",
        "description": "Mô phỏng tăng đột ngột CPU usage do batch job, query không tối ưu, hoặc DDoS",
        "severity": "HIGH",
        "metrics": {
            "cpu_utilization": {"baseline": 45, "spike": 95, "unit": "%"},
            "process_cpu_time": {"baseline": 30, "spike": 85, "unit": "%"},
            "thread_count": {"baseline": 150, "spike": 450, "unit": "threads"},
            "context_switches": {"baseline": 5000, "spike": 25000, "unit": "switches/sec"}
        },
        "root_causes": [
            "Batch job chạy không đúng giờ",
            "Query không tối ưu gây full table scan",
            "Memory leak dẫn đến GC liên tục",
            "Infinite loop trong code",
            "DDoS attack"
        ],
        "detection_logic": {
            "z_score_threshold": 3.0,
            "spike_percentage": 40,
            "spike_duration_seconds": 300,
            "baseline_window_minutes": 15
        },
        "correlation": ["increased_response_time", "user_timeout", "retry_requests"],
        "log_patterns": [
            "server_log", "application_log", "container_log", "metrics_log"
        ]
    },
    
    "memory_leak": {
        "id": "INFRA_002",
        "name": "Memory Leak trên Java Application",
        "description": "Mô phỏng memory leak với heap tăng dần, GC frequency tăng, dẫn đến OOM",
        "severity": "CRITICAL",
        "metrics": {
            "heap_memory_usage": {"baseline": 2048, "leak": 7680, "unit": "MB"},
            "gc_frequency": {"baseline": 1, "leak": 15, "unit": "times/hour"},
            "gc_pause_time": {"baseline": 50, "leak": 2000, "unit": "ms"},
            "old_gen_occupancy": {"baseline": 60, "leak": 98, "unit": "%"}
        },
        "root_causes": [
            "Unclosed connections/streams",
            "Collection objects tăng không kiểm soát",
            "Static collection giữ reference",
            "ThreadLocal không cleanup",
            "Cache không có eviction policy"
        ],
        "detection_logic": {
            "memory_growth_rate": 10,  # MB/minute
            "gc_frequency_increase": 5,  # times
            "duration_hours": 2
        },
        "correlation": ["gc_pressure", "application_freeze", "service_unavailable"],
        "log_patterns": [
            "application_log", "container_log", "metrics_log"
        ]
    },
    
    "db_pool_exhaustion": {
        "id": "INFRA_003",
        "name": "Database Connection Pool Exhaustion",
        "description": "Mô phỏng connection pool đầy do connection leak hoặc slow query",
        "severity": "CRITICAL",
        "metrics": {
            "active_connections": {"baseline": 45, "exhaustion": 100, "unit": "connections"},
            "connection_wait_time": {"baseline": 50, "exhaustion": 5000, "unit": "ms"},
            "connection_timeout_errors": {"baseline": 0, "exhaustion": 50, "unit": "errors/min"},
            "pool_utilization": {"baseline": 45, "exhaustion": 100, "unit": "%"}
        },
        "root_causes": [
            "Connection leak (không close)",
            "Connection timeout quá thấp",
            "Traffic spike vượt pool capacity",
            "Slow query giữ connection lâu",
            "Database deadlock"
        ],
        "detection_logic": {
            "pool_full_duration_seconds": 120,
            "wait_time_threshold_ms": 5000,
            "connection_age_threshold_minutes": 10
        },
        "correlation": ["database_slow_query", "transaction_timeout", "service_degradation"],
        "log_patterns": [
            "database_query_log", "application_log", "database_transaction_log"
        ]
    },
    
    "disk_io_bottleneck": {
        "id": "INFRA_004",
        "name": "Disk I/O Bottleneck",
        "description": "Mô phỏng disk I/O quá tải do index không tối ưu hoặc backup job",
        "severity": "HIGH",
        "metrics": {
            "disk_read_iops": {"baseline": 500, "bottleneck": 8000, "unit": "IOPS"},
            "disk_write_iops": {"baseline": 300, "bottleneck": 5000, "unit": "IOPS"},
            "disk_latency": {"baseline": 5, "bottleneck": 50, "unit": "ms"},
            "disk_queue_length": {"baseline": 0.5, "bottleneck": 5, "unit": "requests"}
        },
        "root_causes": [
            "Database index không tối ưu",
            "Log file tăng trưởng nhanh",
            "Backup job chạy giờ peak",
            "RAID controller cache full",
            "Disk failure trong RAID array"
        ],
        "detection_logic": {
            "latency_threshold_ms": 20,
            "queue_length_threshold": 2,
            "duration_minutes": 5
        },
        "correlation": ["database_slow_query", "slow_api_response", "user_timeout"],
        "log_patterns": [
            "storage_log", "database_query_log", "server_log"
        ]
    },
    
    "network_latency": {
        "id": "INFRA_005",
        "name": "Network Latency Spike giữa Services",
        "description": "Mô phỏng network latency tăng do congestion hoặc routing issue",
        "severity": "HIGH",
        "metrics": {
            "round_trip_time": {"baseline": 3, "spike": 50, "unit": "ms"},
            "packet_loss_rate": {"baseline": 0.01, "spike": 1.5, "unit": "%"},
            "jitter": {"baseline": 2, "spike": 15, "unit": "ms"},
            "tcp_retransmission": {"baseline": 0.1, "spike": 5, "unit": "%"}
        },
        "root_causes": [
            "Network congestion",
            "Routing issue",
            "Switch/router degradation",
            "DNS resolution delay",
            "Firewall inspection overhead"
        ],
        "detection_logic": {
            "rtt_threshold_ms": 20,
            "packet_loss_threshold": 0.1,
            "duration_minutes": 1
        },
        "correlation": ["api_timeout", "retry_storm", "cascade_failure"],
        "log_patterns": [
            "network_log", "api_gateway_log", "microservice_log"
        ]
    },
    
    "api_degradation": {
        "id": "INFRA_006",
        "name": "API Response Time Degradation",
        "description": "Mô phỏng API response time tăng do database slow query hoặc dependency timeout",
        "severity": "HIGH",
        "metrics": {
            "avg_response_time": {"baseline": 150, "degradation": 2000, "unit": "ms"},
            "p95_latency": {"baseline": 300, "degradation": 3500, "unit": "ms"},
            "p99_latency": {"baseline": 500, "degradation": 5000, "unit": "ms"},
            "error_rate": {"baseline": 0.1, "degradation": 5, "unit": "%"}
        },
        "root_causes": [
            "Database slow query",
            "External API timeout",
            "Insufficient resources",
            "Code inefficiency",
            "Cache miss rate cao"
        ],
        "detection_logic": {
            "p95_threshold_ms": 500,
            "p99_threshold_ms": 1000,
            "increase_percentage": 50,
            "duration_minutes": 5
        },
        "correlation": ["user_frustration", "abandonment_rate", "revenue_loss"],
        "log_patterns": [
            "api_gateway_log", "application_log", "database_query_log"
        ]
    },
    
    "thread_pool_saturation": {
        "id": "INFRA_007",
        "name": "Thread Pool Saturation",
        "description": "Mô phỏng thread pool đầy do long-running tasks hoặc deadlock",
        "severity": "HIGH",
        "metrics": {
            "active_threads": {"baseline": 50, "saturation": 200, "unit": "threads"},
            "queue_size": {"baseline": 10, "saturation": 1000, "unit": "tasks"},
            "rejected_tasks": {"baseline": 0, "saturation": 50, "unit": "tasks/min"},
            "thread_wait_time": {"baseline": 10, "saturation": 5000, "unit": "ms"}
        },
        "root_causes": [
            "Long-running tasks block threads",
            "Thread pool size không đủ",
            "Thread deadlock",
            "Blocking I/O operations",
            "Synchronization contention"
        ],
        "detection_logic": {
            "pool_full_duration_seconds": 60,
            "rejection_threshold": 1,
            "blocked_threads_percentage": 30
        },
        "correlation": ["request_queuing", "timeout", "user_retry"],
        "log_patterns": [
            "application_log", "container_log", "metrics_log"
        ]
    },
    
    "cache_invalidation": {
        "id": "INFRA_008",
        "name": "Cache Invalidation Storm",
        "description": "Mô phỏng cache invalidation đồng loạt gây thundering herd",
        "severity": "MEDIUM",
        "metrics": {
            "cache_hit_rate": {"baseline": 95, "storm": 30, "unit": "%"},
            "cache_miss_rate": {"baseline": 5, "storm": 70, "unit": "%"},
            "cache_eviction_rate": {"baseline": 10, "storm": 1000, "unit": "evictions/sec"},
            "database_query_rate": {"baseline": 100, "storm": 2000, "unit": "queries/sec"}
        },
        "root_causes": [
            "Cache expiration đồng loạt",
            "Deployment clear cache",
            "Cache key collision",
            "Memory pressure eviction",
            "Cache warming thiếu"
        ],
        "detection_logic": {
            "hit_rate_drop_percentage": 50,
            "duration_minutes": 2,
            "miss_spike_threshold": 1000
        },
        "correlation": ["database_overload", "slow_response", "cascade_failure"],
        "log_patterns": [
            "cache_log", "database_query_log", "application_log"
        ]
    },
    
    "load_balancer_uneven": {
        "id": "INFRA_009",
        "name": "Load Balancer Uneven Distribution",
        "description": "Mô phỏng phân phối traffic không đều giữa các backend",
        "severity": "MEDIUM",
        "metrics": {
            "backend_1_traffic": {"baseline": 20, "uneven": 60, "unit": "%"},
            "backend_2_traffic": {"baseline": 20, "uneven": 15, "unit": "%"},
            "backend_3_traffic": {"baseline": 20, "uneven": 10, "unit": "%"},
            "response_time_variance": {"baseline": 50, "uneven": 500, "unit": "ms"}
        },
        "root_causes": [
            "Sticky session configuration",
            "Backend capacity không đồng nhất",
            "Health check delay",
            "Routing algorithm không phù hợp",
            "Một backend xử lý slow requests"
        ],
        "detection_logic": {
            "coefficient_of_variation": 0.3,
            "max_backend_percentage": 40,
            "duration_minutes": 5
        },
        "correlation": ["backend_overload", "increased_response_time", "health_check_fail"],
        "log_patterns": [
            "load_balancer_log", "server_log", "metrics_log"
        ]
    },
    
    "message_queue_backlog": {
        "id": "INFRA_010",
        "name": "Message Queue Backlog",
        "description": "Mô phỏng message queue tích tụ do consumer chậm hơn producer",
        "severity": "HIGH",
        "metrics": {
            "queue_depth": {"baseline": 500, "backlog": 50000, "unit": "messages"},
            "message_age": {"baseline": 2, "backlog": 300, "unit": "seconds"},
            "consumer_lag": {"baseline": 100, "backlog": 10000, "unit": "messages"},
            "processing_rate": {"baseline": 1000, "backlog": 200, "unit": "msg/sec"}
        },
        "root_causes": [
            "Consumer xử lý chậm",
            "Consumer crash/restart",
            "Message processing error",
            "Consumer scaling không đủ",
            "Poison message block queue"
        ],
        "detection_logic": {
            "depth_threshold": 5000,
            "age_threshold_seconds": 300,
            "lag_threshold": 10000,
            "duration_minutes": 30
        },
        "correlation": ["data_processing_delay", "sla_violation", "business_impact"],
        "log_patterns": [
            "message_queue_log", "application_log", "metrics_log"
        ]
    },
    
    "database_deadlock": {
        "id": "INFRA_011",
        "name": "Database Deadlock",
        "description": "Mô phỏng database deadlock gây transaction rollback",
        "severity": "HIGH",
        "metrics": {
            "deadlock_count": {"baseline": 0, "issue": 10, "unit": "deadlocks/min"},
            "transaction_rollback": {"baseline": 1, "issue": 50, "unit": "rollbacks/min"},
            "lock_wait_time": {"baseline": 10, "issue": 5000, "unit": "ms"},
            "blocked_sessions": {"baseline": 2, "issue": 20, "unit": "sessions"}
        },
        "root_causes": [
            "Transaction order không nhất quán",
            "Lock escalation",
            "Long-running transactions",
            "Index locking",
            "Concurrent updates"
        ],
        "detection_logic": {
            "deadlock_threshold": 5,
            "rollback_threshold": 20,
            "duration_minutes": 5
        },
        "correlation": ["transaction_failure", "data_inconsistency", "user_error"],
        "log_patterns": [
            "database_transaction_log", "database_query_log", "application_log"
        ]
    },
    
    "connection_timeout": {
        "id": "INFRA_012",
        "name": "Connection Timeout Spike",
        "description": "Mô phỏng connection timeout tăng đột ngột",
        "severity": "HIGH",
        "metrics": {
            "timeout_count": {"baseline": 1, "spike": 100, "unit": "timeouts/min"},
            "connection_time": {"baseline": 50, "spike": 10000, "unit": "ms"},
            "retry_attempts": {"baseline": 5, "spike": 50, "unit": "retries/min"},
            "success_rate": {"baseline": 99.9, "spike": 85, "unit": "%"}
        },
        "root_causes": [
            "Network congestion",
            "Server overload",
            "Firewall rules",
            "DNS issues",
            "Connection pool exhaustion"
        ],
        "detection_logic": {
            "timeout_threshold": 50,
            "connection_time_threshold_ms": 5000,
            "duration_minutes": 3
        },
        "correlation": ["service_unavailable", "user_frustration", "retry_storm"],
        "log_patterns": [
            "network_log", "application_log", "api_gateway_log"
        ]
    },
    
    "gc_pressure": {
        "id": "INFRA_013",
        "name": "Garbage Collection Pressure",
        "description": "Mô phỏng GC pressure cao gây application pause",
        "severity": "HIGH",
        "metrics": {
            "gc_time_percentage": {"baseline": 2, "pressure": 30, "unit": "%"},
            "full_gc_frequency": {"baseline": 1, "pressure": 10, "unit": "times/hour"},
            "gc_pause_time": {"baseline": 100, "pressure": 3000, "unit": "ms"},
            "heap_after_gc": {"baseline": 40, "pressure": 85, "unit": "%"}
        },
        "root_causes": [
            "Memory leak",
            "Heap size không đủ",
            "Object allocation rate cao",
            "Large object allocation",
            "Weak reference accumulation"
        ],
        "detection_logic": {
            "gc_time_threshold": 10,
            "pause_time_threshold_ms": 1000,
            "frequency_threshold": 5,
            "duration_minutes": 10
        },
        "correlation": ["application_freeze", "slow_response", "timeout"],
        "log_patterns": [
            "application_log", "container_log", "metrics_log"
        ]
    },
    
    "container_oom": {
        "id": "INFRA_014",
        "name": "Container Out of Memory",
        "description": "Mô phỏng container OOM kill do memory limit",
        "severity": "CRITICAL",
        "metrics": {
            "memory_usage": {"baseline": 1024, "oom": 2048, "unit": "MB"},
            "memory_limit": {"value": 2048, "unit": "MB"},
            "oom_kill_count": {"baseline": 0, "issue": 5, "unit": "kills/hour"},
            "restart_count": {"baseline": 0, "issue": 10, "unit": "restarts/hour"}
        },
        "root_causes": [
            "Memory leak",
            "Memory limit quá thấp",
            "Traffic spike",
            "Large data processing",
            "Cache size không kiểm soát"
        ],
        "detection_logic": {
            "memory_threshold_percentage": 95,
            "oom_kill_threshold": 1,
            "duration_minutes": 5
        },
        "correlation": ["service_restart", "data_loss", "service_unavailable"],
        "log_patterns": [
            "container_log", "server_log", "metrics_log"
        ]
    },
    
    "service_mesh_failure": {
        "id": "INFRA_015",
        "name": "Service Mesh Communication Failure",
        "description": "Mô phỏng service mesh failure gây microservices không communicate",
        "severity": "CRITICAL",
        "metrics": {
            "mesh_error_rate": {"baseline": 0.1, "failure": 50, "unit": "%"},
            "sidecar_cpu": {"baseline": 5, "failure": 80, "unit": "%"},
            "connection_refused": {"baseline": 0, "failure": 100, "unit": "errors/min"},
            "circuit_breaker_open": {"baseline": 0, "failure": 10, "unit": "services"}
        },
        "root_causes": [
            "Sidecar proxy crash",
            "Control plane failure",
            "Certificate expiration",
            "Configuration error",
            "Resource exhaustion"
        ],
        "detection_logic": {
            "error_rate_threshold": 10,
            "connection_refused_threshold": 50,
            "duration_minutes": 2
        },
        "correlation": ["cascade_failure", "service_unavailable", "data_loss"],
        "log_patterns": [
            "microservice_log", "network_log", "container_log"
        ]
    },
    
    "dns_resolution_slow": {
        "id": "INFRA_016",
        "name": "DNS Resolution Slow",
        "description": "Mô phỏng DNS resolution chậm gây connection delay",
        "severity": "MEDIUM",
        "metrics": {
            "dns_query_time": {"baseline": 10, "slow": 500, "unit": "ms"},
            "dns_timeout_rate": {"baseline": 0, "slow": 5, "unit": "%"},
            "dns_cache_hit_rate": {"baseline": 95, "slow": 30, "unit": "%"},
            "connection_delay": {"baseline": 50, "slow": 1000, "unit": "ms"}
        },
        "root_causes": [
            "DNS server overload",
            "Network latency to DNS",
            "DNS cache invalidation",
            "DNS query storm",
            "DNS server failure"
        ],
        "detection_logic": {
            "query_time_threshold_ms": 100,
            "timeout_rate_threshold": 1,
            "duration_minutes": 5
        },
        "correlation": ["connection_timeout", "slow_api_response", "user_timeout"],
        "log_patterns": [
            "dns_log", "network_log", "application_log"
        ]
    },
    
    "ssl_handshake_failure": {
        "id": "INFRA_017",
        "name": "SSL/TLS Handshake Failure",
        "description": "Mô phỏng SSL handshake failure do certificate hoặc cipher issue",
        "severity": "HIGH",
        "metrics": {
            "handshake_failure_rate": {"baseline": 0, "failure": 20, "unit": "%"},
            "handshake_time": {"baseline": 50, "failure": 5000, "unit": "ms"},
            "certificate_errors": {"baseline": 0, "failure": 50, "unit": "errors/min"},
            "connection_refused": {"baseline": 0, "failure": 100, "unit": "errors/min"}
        },
        "root_causes": [
            "Certificate expiration",
            "Certificate mismatch",
            "Cipher suite incompatibility",
            "TLS version mismatch",
            "Certificate chain incomplete"
        ],
        "detection_logic": {
            "failure_rate_threshold": 5,
            "handshake_time_threshold_ms": 1000,
            "duration_minutes": 3
        },
        "correlation": ["connection_failure", "security_alert", "service_unavailable"],
        "log_patterns": [
            "network_log", "security_log", "certificate_log"
        ]
    },
    
    "rate_limit_exceeded": {
        "id": "INFRA_018",
        "name": "Rate Limit Exceeded",
        "description": "Mô phỏng rate limit exceeded do traffic spike hoặc abuse",
        "severity": "MEDIUM",
        "metrics": {
            "rate_limit_hits": {"baseline": 10, "exceeded": 500, "unit": "hits/min"},
            "rejected_requests": {"baseline": 5, "exceeded": 1000, "unit": "requests/min"},
            "request_rate": {"baseline": 1000, "exceeded": 10000, "unit": "req/sec"},
            "throttle_percentage": {"baseline": 0.5, "exceeded": 50, "unit": "%"}
        },
        "root_causes": [
            "Traffic spike",
            "Bot/scraper activity",
            "Retry storm",
            "Rate limit too low",
            "DDoS attack"
        ],
        "detection_logic": {
            "rate_limit_threshold": 100,
            "rejection_threshold": 500,
            "duration_minutes": 5
        },
        "correlation": ["user_frustration", "service_degradation", "revenue_loss"],
        "log_patterns": [
            "api_gateway_log", "waf_log", "application_log"
        ]
    },
    
    "circuit_breaker_open": {
        "id": "INFRA_019",
        "name": "Circuit Breaker Open",
        "description": "Mô phỏng circuit breaker open do downstream service failure",
        "severity": "HIGH",
        "metrics": {
            "circuit_breaker_state": {"baseline": "closed", "issue": "open", "unit": "state"},
            "failure_rate": {"baseline": 0.5, "issue": 60, "unit": "%"},
            "fallback_invocations": {"baseline": 5, "issue": 500, "unit": "calls/min"},
            "downstream_errors": {"baseline": 1, "issue": 100, "unit": "errors/min"}
        },
        "root_causes": [
            "Downstream service failure",
            "Network partition",
            "Timeout threshold too low",
            "Resource exhaustion",
            "Deployment issue"
        ],
        "detection_logic": {
            "failure_rate_threshold": 50,
            "error_threshold": 50,
            "duration_minutes": 2
        },
        "correlation": ["service_degradation", "fallback_mode", "data_staleness"],
        "log_patterns": [
            "microservice_log", "api_gateway_log", "application_log"
        ]
    },
    
    "replica_lag": {
        "id": "INFRA_020",
        "name": "Database Replica Lag",
        "description": "Mô phỏng database replica lag gây data inconsistency",
        "severity": "HIGH",
        "metrics": {
            "replication_lag": {"baseline": 0.5, "lag": 300, "unit": "seconds"},
            "replica_behind_master": {"baseline": 100, "lag": 50000, "unit": "transactions"},
            "read_stale_rate": {"baseline": 0, "lag": 30, "unit": "%"},
            "replication_errors": {"baseline": 0, "lag": 10, "unit": "errors/min"}
        },
        "root_causes": [
            "Master write load cao",
            "Replica resource insufficient",
            "Network latency",
            "Long-running transactions",
            "Replication thread bottleneck"
        ],
        "detection_logic": {
            "lag_threshold_seconds": 60,
            "transaction_behind_threshold": 10000,
            "duration_minutes": 10
        },
        "correlation": ["data_inconsistency", "stale_reads", "business_logic_error"],
        "log_patterns": [
            "database_replication_log", "database_query_log", "application_log"
        ]
    }
}

def get_scenario_by_id(scenario_id: str) -> Dict[str, Any]:
    """Get scenario configuration by ID"""
    for scenario_type, config in INFRASTRUCTURE_SCENARIOS.items():
        if config["id"] == scenario_id:
            return config
    return None

def get_all_infrastructure_scenarios() -> List[Dict[str, Any]]:
    """Get all infrastructure scenarios"""
    return list(INFRASTRUCTURE_SCENARIOS.values())

def get_scenarios_by_severity(severity: str) -> List[Dict[str, Any]]:
    """Get scenarios filtered by severity"""
    return [s for s in INFRASTRUCTURE_SCENARIOS.values() if s["severity"] == severity]
