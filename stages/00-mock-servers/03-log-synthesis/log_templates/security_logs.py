"""
Security & Authentication Logs
Danh mục IV: 7 loại log về bảo mật và xác thực
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from .common import *


class SecurityLogs:
    """Generator cho các loại log bảo mật và xác thực"""
    
    @staticmethod
    def generate_authentication_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """IV.1 - Authentication Logs: Log xác thực người dùng"""
        user_id = f"USR{random.randint(100000, 999999)}"
        ip = random_ip()
        
        # Xác định trạng thái dựa trên anomaly_score
        if anomaly_score > 0.7:
            status = random.choice(["failed", "blocked", "suspicious"])
            reason = random.choice([
                "Invalid credentials",
                "Account locked",
                "Too many attempts",
                "Suspicious location",
                "Device not recognized"
            ])
        else:
            status = "success"
            reason = "Valid credentials"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "authentication",
            "category": "security",
            "user_id": user_id,
            "username": random.choice(VIETNAMESE_NAMES),
            "auth_method": random.choice(["password", "otp", "biometric", "sso", "token"]),
            "status": status,
            "reason": reason,
            "ip_address": ip,
            "device": random.choice(["mobile", "web", "tablet", "desktop"]),
            "device_id": f"DEV{random.randint(1000, 9999)}",
            "location": random.choice(VIETNAMESE_CITIES),
            "session_id": f"SES{random.randint(100000, 999999)}",
            "anomaly_score": anomaly_score,
            "severity": "high" if anomaly_score > 0.7 else "low"
        }
    
    @staticmethod
    def generate_authorization_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """IV.2 - Authorization Logs: Log phân quyền truy cập"""
        user_id = f"USR{random.randint(100000, 999999)}"
        
        resources = [
            "account_balance", "transaction_history", "user_profile",
            "admin_panel", "reports", "settings", "customer_data"
        ]
        
        actions = ["read", "write", "delete", "update", "execute"]
        
        if anomaly_score > 0.7:
            decision = "denied"
            reason = random.choice([
                "Insufficient permissions",
                "Role not authorized",
                "Resource restricted",
                "Policy violation"
            ])
        else:
            decision = "granted"
            reason = "Policy matched"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "authorization",
            "category": "security",
            "user_id": user_id,
            "resource": random.choice(resources),
            "action": random.choice(actions),
            "decision": decision,
            "reason": reason,
            "role": random.choice(["user", "admin", "manager", "auditor", "operator"]),
            "policy_id": f"POL{random.randint(1000, 9999)}",
            "ip_address": random_ip(),
            "anomaly_score": anomaly_score,
            "severity": "critical" if anomaly_score > 0.8 else "medium"
        }
    
    @staticmethod
    def generate_session_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """IV.3 - Session Management Logs: Log quản lý phiên làm việc"""
        session_id = f"SES{random.randint(100000, 999999)}"
        user_id = f"USR{random.randint(100000, 999999)}"
        
        event_types = ["session_start", "session_end", "session_timeout", "session_refresh"]
        
        if anomaly_score > 0.7:
            event_type = random.choice(["session_hijack", "concurrent_session", "session_anomaly"])
            status = "suspicious"
        else:
            event_type = random.choice(event_types)
            status = "normal"
        
        duration = random.randint(60, 7200)  # 1 phút đến 2 giờ
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "session_management",
            "category": "security",
            "session_id": session_id,
            "user_id": user_id,
            "event_type": event_type,
            "status": status,
            "duration_seconds": duration,
            "ip_address": random_ip(),
            "device": random.choice(["mobile", "web", "tablet"]),
            "location": random.choice(VIETNAMESE_CITIES),
            "idle_time": random.randint(0, 1800),
            "activities_count": random.randint(1, 100),
            "anomaly_score": anomaly_score,
            "severity": "high" if anomaly_score > 0.7 else "low"
        }
    
    @staticmethod
    def generate_encryption_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """IV.4 - Encryption/Decryption Logs: Log mã hóa/giải mã"""
        
        operations = ["encrypt", "decrypt", "key_generation", "key_rotation"]
        algorithms = ["AES-256", "RSA-2048", "SHA-256", "HMAC-SHA256"]
        
        if anomaly_score > 0.7:
            status = "failed"
            error = random.choice([
                "Invalid key",
                "Corrupted data",
                "Algorithm mismatch",
                "Key expired"
            ])
        else:
            status = "success"
            error = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "encryption",
            "category": "security",
            "operation": random.choice(operations),
            "algorithm": random.choice(algorithms),
            "key_id": f"KEY{random.randint(10000, 99999)}",
            "data_size_bytes": random.randint(1024, 1048576),
            "status": status,
            "error": error,
            "processing_time_ms": random.randint(10, 500),
            "user_id": f"USR{random.randint(100000, 999999)}",
            "service": random.choice(["payment", "storage", "communication", "backup"]),
            "anomaly_score": anomaly_score,
            "severity": "critical" if anomaly_score > 0.8 else "low"
        }
    
    @staticmethod
    def generate_intrusion_detection_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """IV.5 - Intrusion Detection Logs: Log phát hiện xâm nhập"""
        
        attack_types = [
            "SQL Injection", "XSS", "CSRF", "DDoS", "Brute Force",
            "Port Scanning", "Malware", "Phishing"
        ]
        
        if anomaly_score > 0.7:
            threat_level = random.choice(["high", "critical"])
            action_taken = random.choice(["blocked", "quarantined", "alerted"])
            detected = True
        else:
            threat_level = "low"
            action_taken = "monitored"
            detected = False
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "intrusion_detection",
            "category": "security",
            "source_ip": random_ip(),
            "destination_ip": random_ip(),
            "attack_type": random.choice(attack_types) if detected else "none",
            "threat_level": threat_level,
            "detected": detected,
            "action_taken": action_taken,
            "signature_id": f"SIG{random.randint(1000, 9999)}",
            "packet_count": random.randint(1, 10000),
            "bytes_transferred": random.randint(1024, 10485760),
            "protocol": random.choice(["TCP", "UDP", "HTTP", "HTTPS"]),
            "port": random.randint(1, 65535),
            "anomaly_score": anomaly_score,
            "severity": "critical" if anomaly_score > 0.8 else "medium"
        }
    
    @staticmethod
    def generate_data_access_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """IV.6 - Data Access Logs: Log truy cập dữ liệu nhạy cảm"""
        
        data_types = [
            "customer_pii", "account_balance", "transaction_history",
            "credit_card", "loan_details", "kyc_documents"
        ]
        
        if anomaly_score > 0.7:
            access_type = random.choice(["unauthorized", "suspicious", "bulk_download"])
            status = "flagged"
        else:
            access_type = "authorized"
            status = "normal"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "data_access",
            "category": "security",
            "user_id": f"USR{random.randint(100000, 999999)}",
            "data_type": random.choice(data_types),
            "access_type": access_type,
            "operation": random.choice(["read", "write", "delete", "export"]),
            "records_accessed": random.randint(1, 1000),
            "status": status,
            "ip_address": random_ip(),
            "location": random.choice(VIETNAMESE_CITIES),
            "purpose": random.choice(["customer_service", "audit", "reporting", "investigation"]),
            "approval_id": f"APR{random.randint(1000, 9999)}" if access_type == "authorized" else None,
            "anomaly_score": anomaly_score,
            "severity": "critical" if anomaly_score > 0.8 else "medium"
        }
    
    @staticmethod
    def generate_security_incident_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """IV.7 - Security Incident Logs: Log sự cố bảo mật"""
        
        incident_types = [
            "data_breach", "account_compromise", "malware_infection",
            "unauthorized_access", "policy_violation", "insider_threat"
        ]
        
        severity_levels = ["low", "medium", "high", "critical"]
        
        if anomaly_score > 0.7:
            severity = random.choice(["high", "critical"])
            status = random.choice(["investigating", "confirmed", "critical"])
        else:
            severity = random.choice(["low", "medium"])
            status = "resolved"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "security_incident",
            "category": "security",
            "incident_id": f"INC{random.randint(100000, 999999)}",
            "incident_type": random.choice(incident_types),
            "severity": severity,
            "status": status,
            "affected_users": random.randint(1, 1000),
            "affected_systems": random.randint(1, 10),
            "detection_method": random.choice(["automated", "manual", "user_report", "third_party"]),
            "response_time_minutes": random.randint(5, 240),
            "assigned_to": random.choice(VIETNAMESE_NAMES),
            "description": f"Security incident detected: {random.choice(incident_types)}",
            "mitigation_steps": random.choice([
                "Password reset enforced",
                "Account locked",
                "System isolated",
                "Investigation ongoing"
            ]),
            "anomaly_score": anomaly_score,
            "priority": "P1" if severity == "critical" else "P2"
        }


def get_all_security_log_types():
    """Trả về danh sách tất cả các loại log bảo mật"""
    return [
        "authentication",
        "authorization",
        "session_management",
        "encryption",
        "intrusion_detection",
        "data_access",
        "security_incident"
    ]
