"""
Fraud Detection & AML Logs
Danh mục VI: 3 loại log về phát hiện gian lận và chống rửa tiền
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from .common import *


class FraudLogs:
    """Generator cho các loại log phát hiện gian lận và AML"""
    
    @staticmethod
    def generate_fraud_detection_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VI.1 - Fraud Detection Logs: Log phát hiện gian lận"""
        
        alert_id = f"FRD{random.randint(100000, 999999)}"
        
        fraud_types = [
            "card_fraud", "identity_theft", "account_takeover",
            "transaction_fraud", "phishing", "social_engineering"
        ]
        
        if anomaly_score > 0.7:
            risk_score = round(random.uniform(70, 100), 2)
            status = random.choice(["confirmed_fraud", "under_investigation", "high_risk"])
            action = random.choice(["account_frozen", "transaction_blocked", "card_blocked"])
        else:
            risk_score = round(random.uniform(0, 40), 2)
            status = "false_positive"
            action = "no_action"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "fraud_detection",
            "category": "fraud",
            "alert_id": alert_id,
            "fraud_type": random.choice(fraud_types),
            "risk_score": risk_score,
            "status": status,
            "action_taken": action,
            "customer_id": f"CUS{random.randint(100000, 999999)}",
            "transaction_id": f"TXN{random.randint(1000000, 9999999)}",
            "amount": round(random.uniform(1000000, 100000000), 2),
            "detection_method": random.choice(["rule_based", "ml_model", "behavioral_analysis", "manual_review"]),
            "indicators": random.sample([
                "unusual_location",
                "high_velocity",
                "unusual_amount",
                "device_mismatch",
                "time_anomaly",
                "merchant_risk"
            ], k=random.randint(1, 3)),
            "model_version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}",
            "assigned_to": random.choice(VIETNAMESE_NAMES),
            "ip_address": random_ip(),
            "location": random.choice(VIETNAMESE_CITIES),
            "anomaly_score": anomaly_score,
            "priority": "P1" if risk_score > 80 else "P2"
        }
    
    @staticmethod
    def generate_aml_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VI.2 - AML (Anti-Money Laundering) Logs: Log chống rửa tiền"""
        
        case_id = f"AML{random.randint(100000, 999999)}"
        
        aml_indicators = [
            "structuring", "rapid_movement", "high_risk_country",
            "cash_intensive", "shell_company", "unusual_pattern"
        ]
        
        if anomaly_score > 0.7:
            risk_level = random.choice(["high", "critical"])
            status = random.choice(["under_review", "sar_filed", "escalated"])
            requires_sar = True
        else:
            risk_level = "low"
            status = "cleared"
            requires_sar = False
        
        total_amount = round(random.uniform(500000000, 5000000000), 2)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "aml_monitoring",
            "category": "fraud",
            "case_id": case_id,
            "customer_id": f"CUS{random.randint(100000, 999999)}",
            "risk_level": risk_level,
            "status": status,
            "indicators": random.sample(aml_indicators, k=random.randint(1, 3)),
            "total_amount": total_amount,
            "transaction_count": random.randint(10, 100),
            "time_period_days": random.randint(1, 30),
            "countries_involved": random.sample(["Vietnam", "Singapore", "USA", "China", "UAE", "Switzerland"], k=random.randint(1, 3)),
            "requires_sar": requires_sar,
            "sar_filed_date": datetime.now().isoformat() if requires_sar else None,
            "compliance_officer": random.choice(VIETNAMESE_NAMES),
            "review_deadline": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
            "related_parties": random.randint(1, 5),
            "source_of_funds": random.choice(["business", "salary", "investment", "unknown"]),
            "anomaly_score": anomaly_score,
            "priority": "urgent" if risk_level == "critical" else "normal"
        }
    
    @staticmethod
    def generate_kyc_log(anomaly_score: float = 0.0) -> Dict[str, Any]:
        """VI.3 - KYC/CDD Logs: Log xác minh danh tính khách hàng"""
        
        kyc_id = f"KYC{random.randint(100000, 999999)}"
        
        verification_types = ["identity", "address", "income", "source_of_funds", "pep_screening"]
        
        if anomaly_score > 0.7:
            status = random.choice(["failed", "pending_documents", "high_risk", "rejected"])
            risk_rating = random.choice(["high", "critical"])
        else:
            status = "approved"
            risk_rating = "low"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "kyc_verification",
            "category": "fraud",
            "kyc_id": kyc_id,
            "customer_id": f"CUS{random.randint(100000, 999999)}",
            "customer_name": random.choice(VIETNAMESE_NAMES),
            "verification_type": random.choice(verification_types),
            "status": status,
            "risk_rating": risk_rating,
            "id_type": random.choice(["cccd", "passport", "driving_license"]),
            "id_number": f"{random.randint(100000000000, 999999999999)}",
            "date_of_birth": f"{random.randint(1960, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "nationality": "Vietnamese",
            "occupation": random.choice([
                "Nhân viên văn phòng",
                "Kinh doanh",
                "Giáo viên",
                "Bác sĩ",
                "Kỹ sư"
            ]),
            "income_range": random.choice(["<10M", "10-20M", "20-50M", "50-100M", ">100M"]),
            "pep_status": random.choice([True, False]) if anomaly_score > 0.5 else False,
            "sanctions_match": random.choice([True, False]) if anomaly_score > 0.7 else False,
            "documents_verified": random.randint(1, 5),
            "verification_method": random.choice(["manual", "automated", "video_call", "biometric"]),
            "verified_by": random.choice(VIETNAMESE_NAMES),
            "branch": random.choice(VIETNAMESE_CITIES),
            "anomaly_score": anomaly_score,
            "requires_enhanced_dd": anomaly_score > 0.7
        }


def get_all_fraud_log_types():
    """Trả về danh sách tất cả các loại log gian lận"""
    return [
        "fraud_detection",
        "aml_monitoring",
        "kyc_verification"
    ]
