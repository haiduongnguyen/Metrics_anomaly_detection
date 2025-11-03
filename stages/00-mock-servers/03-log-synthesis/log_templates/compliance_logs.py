"""
Compliance & Audit Logs - 3 loại log
Logs liên quan đến tuân thủ quy định và kiểm toán
"""

import random
from datetime import datetime, timedelta
from .common import *

class ComplianceLogs:
    """Generator cho Compliance & Audit Logs"""
    
    @staticmethod
    def generate_regulatory_compliance_log(anomaly_score: float = 0.0) -> dict:
        """
        Regulatory Compliance Logs
        Log tuân thủ các quy định của NHNN, Basel, FATCA
        """
        regulations = ["NHNN Circular 39/2016", "Basel III", "FATCA", "CRS", "AML/CFT", "GDPR Vietnam"]
        compliance_types = ["KYC_CHECK", "TRANSACTION_LIMIT", "REPORTING", "DATA_PROTECTION", "CAPITAL_ADEQUACY"]
        statuses = ["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW", "REMEDIATED"]
        
        is_anomaly = anomaly_score > 0.7
        
        regulation = random.choice(regulations)
        compliance_type = random.choice(compliance_types)
        
        if is_anomaly:
            status = "NON_COMPLIANT"
            risk_level = random.choice(["HIGH", "CRITICAL"])
            findings = random.choice([
                "Vượt quá hạn mức giao dịch cho phép",
                "Thiếu tài liệu KYC bắt buộc",
                "Chậm báo cáo giao dịch đáng ngờ",
                "Vi phạm quy định về tỷ lệ an toàn vốn"
            ])
        else:
            status = random.choice(["COMPLIANT", "COMPLIANT", "PENDING_REVIEW"])
            risk_level = random.choice(["LOW", "MEDIUM"])
            findings = "Tuân thủ đầy đủ các quy định"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "regulatory_compliance",
            "regulation": regulation,
            "compliance_type": compliance_type,
            "status": status,
            "risk_level": risk_level,
            "findings": findings,
            "checked_by": random.choice(VIETNAMESE_NAMES),
            "department": "Compliance & Risk Management",
            "remediation_deadline": (datetime.now() + timedelta(days=random.randint(7, 30))).isoformat() if status == "NON_COMPLIANT" else None,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_audit_trail_log(anomaly_score: float = 0.0) -> dict:
        """
        Audit Trail Logs
        Log theo dõi mọi thay đổi quan trọng trong hệ thống
        """
        actions = ["CREATE", "UPDATE", "DELETE", "APPROVE", "REJECT", "EXPORT", "IMPORT"]
        entities = ["USER_ACCOUNT", "TRANSACTION", "CONFIGURATION", "PERMISSION", "REPORT", "CUSTOMER_DATA"]
        
        is_anomaly = anomaly_score > 0.7
        
        action = random.choice(actions)
        entity = random.choice(entities)
        user = random.choice(VIETNAMESE_NAMES)
        
        if is_anomaly:
            action = random.choice(["DELETE", "EXPORT"])
            entity = random.choice(["CUSTOMER_DATA", "TRANSACTION", "CONFIGURATION"])
            reason = "Không có lý do hợp lệ"
            approval_status = "UNAPPROVED"
            risk_flag = True
        else:
            reason = random.choice([
                "Cập nhật thông tin theo yêu cầu khách hàng",
                "Thay đổi cấu hình hệ thống theo kế hoạch",
                "Tạo báo cáo định kỳ",
                "Phê duyệt giao dịch theo quy trình"
            ])
            approval_status = "APPROVED" if action in ["DELETE", "EXPORT"] else "NOT_REQUIRED"
            risk_flag = False
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "audit_trail",
            "action": action,
            "entity_type": entity,
            "entity_id": f"{entity}_{random.randint(100000, 999999)}",
            "performed_by": user,
            "user_role": random.choice(["ADMIN", "MANAGER", "OPERATOR", "AUDITOR"]),
            "ip_address": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "reason": reason,
            "approval_status": approval_status,
            "approved_by": random.choice(VIETNAMESE_NAMES) if approval_status == "APPROVED" else None,
            "risk_flag": risk_flag,
            "before_value": f"{{...}}" if action == "UPDATE" else None,
            "after_value": f"{{...}}" if action in ["UPDATE", "CREATE"] else None,
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_data_retention_log(anomaly_score: float = 0.0) -> dict:
        """
        Data Retention & Archival Logs
        Log quản lý lưu trữ và xóa dữ liệu theo quy định
        """
        data_types = ["TRANSACTION_RECORDS", "CUSTOMER_DATA", "AUDIT_LOGS", "COMMUNICATION_RECORDS", "REPORTS"]
        actions = ["ARCHIVE", "DELETE", "RESTORE", "MIGRATE", "BACKUP"]
        
        is_anomaly = anomaly_score > 0.7
        
        data_type = random.choice(data_types)
        action = random.choice(actions)
        
        retention_period_days = random.choice([1825, 2555, 3650])  # 5, 7, 10 năm
        
        if is_anomaly:
            action = "DELETE"
            status = "FAILED"
            reason = random.choice([
                "Xóa dữ liệu trước thời hạn lưu trữ quy định",
                "Không có phê duyệt từ cấp quản lý",
                "Vi phạm chính sách lưu trữ dữ liệu"
            ])
            compliance_status = "NON_COMPLIANT"
        else:
            status = "SUCCESS"
            reason = f"Thực hiện {action.lower()} theo chính sách lưu trữ {retention_period_days} ngày"
            compliance_status = "COMPLIANT"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "data_retention",
            "data_type": data_type,
            "action": action,
            "status": status,
            "records_affected": random.randint(100, 100000) if status == "SUCCESS" else 0,
            "retention_period_days": retention_period_days,
            "storage_location": random.choice(["PRIMARY_DB", "ARCHIVE_STORAGE", "COLD_STORAGE", "BACKUP_SITE"]),
            "initiated_by": random.choice(VIETNAMESE_NAMES),
            "reason": reason,
            "compliance_status": compliance_status,
            "data_size_gb": round(random.uniform(0.1, 1000.0), 2),
            "anomaly_score": anomaly_score
        }
