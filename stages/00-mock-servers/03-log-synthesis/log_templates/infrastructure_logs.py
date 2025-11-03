"""
Infrastructure & System Logs (9 types)
Server metrics, processes, containers, networking, etc.
"""
from datetime import datetime
from typing import Dict, Any
import random
import uuid
from .common import LogCommonData

class InfrastructureLogTemplates:
    """Infrastructure and system-level log generators"""
    
    @staticmethod
    def server_metrics_log(anomaly_score: float) -> Dict[str, Any]:
        """#1 System Performance Metrics"""
        cpu_base = 45 if anomaly_score < 50 else 85
        memory_base = 16 if anomaly_score < 50 else 28
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "server_metrics",
            "host": f"app-server-{random.randint(1, 10):02d}",
            "cpu_usage_percent": cpu_base + random.uniform(-10, 15),
            "memory_used_gb": memory_base + random.uniform(-2, 4),
            "memory_total_gb": 32,
            "disk_io_read_mb": random.uniform(50, 200) * (2 if anomaly_score > 70 else 1),
            "disk_io_write_mb": random.uniform(30, 150) * (2 if anomaly_score > 70 else 1),
            "network_bytes_in": random.randint(500000, 2000000),
            "network_bytes_out": random.randint(300000, 1500000),
            "load_average_1min": random.uniform(1.5, 8.0) if anomaly_score > 60 else random.uniform(0.5, 2.5),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def process_log(anomaly_score: float) -> Dict[str, Any]:
        """#2 Process & Application Logs"""
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "process_metrics",
            "host": f"app-server-{random.randint(1, 10):02d}",
            "process": random.choice(["java", "python", "node", "nginx"]),
            "pid": random.randint(1000, 65535),
            "cpu_percent": random.uniform(20, 95) if anomaly_score > 60 else random.uniform(5, 40),
            "memory_mb": random.randint(512, 4096),
            "threads": random.randint(50, 500) if anomaly_score > 70 else random.randint(10, 100),
            "fd_count": random.randint(100, 1000),
            "state": random.choice(["RUNNABLE", "SLEEPING", "BLOCKED"]) if anomaly_score > 80 else "RUNNABLE",
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def filesystem_log(anomaly_score: float) -> Dict[str, Any]:
        """#3 File System Logs"""
        used_percent = 85 if anomaly_score > 70 else random.randint(40, 70)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "filesystem",
            "host": f"app-server-{random.randint(1, 10):02d}",
            "filesystem": "/dev/sda1",
            "mount_point": "/",
            "total_gb": 500,
            "used_gb": int(500 * used_percent / 100),
            "available_gb": int(500 * (100 - used_percent) / 100),
            "used_percent": used_percent,
            "inodes_used_percent": random.randint(20, 90) if anomaly_score > 75 else random.randint(10, 50),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def container_log(anomaly_score: float) -> Dict[str, Any]:
        """#4 Docker/Container Logs"""
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "container_metrics",
            "container_id": uuid.uuid4().hex[:12],
            "container_name": random.choice(["payment-service", "auth-service", "transfer-service", "account-service"]),
            "image": f"banking/{random.choice(['payment', 'auth', 'transfer'])}:v1.2.3",
            "cpu_percent": random.uniform(20, 90) if anomaly_score > 60 else random.uniform(5, 35),
            "memory_mb": random.randint(256, 1024),
            "memory_limit_mb": 1024,
            "network_rx_mb": random.uniform(5, 50),
            "network_tx_mb": random.uniform(3, 30),
            "restart_count": random.randint(1, 5) if anomaly_score > 80 else 0,
            "status": "running" if anomaly_score < 90 else random.choice(["running", "restarting", "unhealthy"]),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def kubernetes_log(anomaly_score: float) -> Dict[str, Any]:
        """#5 Kubernetes Logs"""
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "kubernetes_pod",
            "cluster": "prod-cluster",
            "namespace": "banking",
            "pod": f"payment-service-{uuid.uuid4().hex[:8]}",
            "node": f"worker-node-{random.randint(1, 5):02d}",
            "cpu_request": "500m",
            "cpu_limit": "1000m",
            "cpu_usage": f"{random.randint(400, 950)}m" if anomaly_score > 60 else f"{random.randint(200, 600)}m",
            "memory_request": "512Mi",
            "memory_limit": "1Gi",
            "memory_usage": f"{random.randint(400, 900)}Mi" if anomaly_score > 60 else f"{random.randint(256, 600)}Mi",
            "restart_count": random.randint(1, 3) if anomaly_score > 80 else 0,
            "phase": "Running" if anomaly_score < 85 else random.choice(["Running", "Pending", "Failed"]),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def load_balancer_log(anomaly_score: float) -> Dict[str, Any]:
        """#6 Load Balancer Logs"""
        response_time = random.randint(500, 3000) if anomaly_score > 70 else random.randint(50, 300)
        status = 500 if anomaly_score > 85 else (503 if anomaly_score > 75 else 200)
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "load_balancer",
            "lb": "prod-lb-01",
            "client_ip": f"{random.choice(LogCommonData.ISP_RANGES)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "backend_server": f"app-{random.randint(1, 5):02d}",
            "backend_ip": f"10.0.1.{random.randint(10, 50)}",
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "url": random.choice(["/api/transfer", "/api/balance", "/api/login", "/api/payment"]),
            "status": status,
            "response_time_ms": response_time,
            "bytes_sent": random.randint(512, 4096),
            "bytes_received": random.randint(256, 2048),
            "backend_connection_time_ms": random.randint(1, 50),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def firewall_log(anomaly_score: float) -> Dict[str, Any]:
        """#7 Firewall & Security Appliance Logs"""
        action = "DENY" if anomaly_score > 75 else "ALLOW"
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "firewall",
            "firewall": "fw-01",
            "src_ip": f"{random.choice(LogCommonData.ISP_RANGES)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "src_port": random.randint(1024, 65535),
            "dst_ip": f"10.0.1.{random.randint(10, 50)}",
            "dst_port": random.choice([80, 443, 8080, 3306, 5432]),
            "protocol": random.choice(["TCP", "UDP"]),
            "action": action,
            "rule_id": random.randint(1000, 9999),
            "bytes": random.randint(512, 8192),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def dns_log(anomaly_score: float) -> Dict[str, Any]:
        """#8 DNS Logs"""
        response_code = "NXDOMAIN" if anomaly_score > 80 else "NOERROR"
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "dns_query",
            "dns_server": "dns-01",
            "client_ip": f"10.0.1.{random.randint(10, 254)}",
            "query_domain": random.choice(["api.bank.com", "auth.bank.com", "payment.bank.com", "malicious-site.com" if anomaly_score > 85 else "cdn.bank.com"]),
            "query_type": random.choice(["A", "AAAA", "MX", "TXT"]),
            "response_code": response_code,
            "resolved_ip": f"203.0.113.{random.randint(1, 254)}" if response_code == "NOERROR" else None,
            "response_time_ms": random.randint(50, 500) if anomaly_score > 70 else random.randint(5, 50),
            "ttl": 300,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def cdn_log(anomaly_score: float) -> Dict[str, Any]:
        """#9 CDN Logs"""
        cache_status = "MISS" if anomaly_score > 70 else random.choice(["HIT", "HIT", "HIT", "MISS"])
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "log_type": "cdn",
            "cdn": "cloudfront",
            "edge_location": random.choice(["SIN", "HKG", "NRT", "SYD"]),
            "client_ip": f"{random.choice(LogCommonData.ISP_RANGES)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "url": random.choice(["/static/app.js", "/static/style.css", "/images/logo.png"]),
            "cache_status": cache_status,
            "bytes_sent": random.randint(10240, 1048576),
            "origin_response_time_ms": random.randint(100, 1000) if cache_status == "MISS" else 0,
            "edge_response_time_ms": random.randint(5, 50),
            "anomaly_score": anomaly_score
        }
