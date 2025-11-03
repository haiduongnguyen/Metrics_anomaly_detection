"""
Business Intelligence & Analytics Logs - 2 loại log
Logs liên quan đến phân tích kinh doanh
"""

import random
from datetime import datetime, timedelta
from .common import *

class BusinessIntelligenceLogs:
    """Generator cho Business Intelligence & Analytics Logs"""
    
    @staticmethod
    def generate_etl_pipeline_log(anomaly_score: float = 0.0) -> dict:
        """
        ETL Pipeline Logs
        Log của các pipeline ETL (Extract, Transform, Load)
        """
        pipelines = [
            "daily_transaction_aggregation",
            "customer_behavior_analysis",
            "fraud_pattern_detection",
            "revenue_reporting",
            "risk_assessment"
        ]
        stages = ["EXTRACT", "TRANSFORM", "LOAD", "VALIDATE"]
        
        is_anomaly = anomaly_score > 0.7
        
        pipeline = random.choice(pipelines)
        stage = random.choice(stages)
        
        if is_anomaly:
            status = "FAILED"
            records_processed = random.randint(0, 10000)
            records_failed = random.randint(1000, 50000)
            error_message = random.choice([
                "Data quality check failed",
                "Schema mismatch detected",
                "Transformation timeout",
                "Target database connection lost",
                "Insufficient memory for processing"
            ])
            duration_seconds = random.randint(3600, 14400)
        else:
            status = "SUCCESS"
            records_processed = random.randint(100000, 10000000)
            records_failed = random.randint(0, 100)
            error_message = None
            duration_seconds = random.randint(300, 3600)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "etl_pipeline",
            "pipeline_name": pipeline,
            "pipeline_id": f"ETL-{random.randint(100000, 999999)}",
            "stage": stage,
            "status": status,
            "records_processed": records_processed,
            "records_failed": records_failed,
            "records_skipped": random.randint(0, 1000),
            "duration_seconds": duration_seconds,
            "data_size_gb": round(random.uniform(0.1, 500.0), 2),
            "source": random.choice(["production_db", "data_warehouse", "external_api", "file_storage"]),
            "destination": random.choice(["data_warehouse", "analytics_db", "reporting_db"]),
            "error_message": error_message,
            "started_at": (datetime.now() - timedelta(seconds=duration_seconds)).isoformat(),
            "completed_at": datetime.now().isoformat(),
            "triggered_by": random.choice(["SCHEDULE", "MANUAL", "EVENT"]),
            "anomaly_score": anomaly_score
        }
    
    @staticmethod
    def generate_report_generation_log(anomaly_score: float = 0.0) -> dict:
        """
        Report Generation Logs
        Log tạo báo cáo kinh doanh và phân tích
        """
        report_types = [
            "DAILY_TRANSACTION_SUMMARY",
            "MONTHLY_REVENUE_REPORT",
            "CUSTOMER_SEGMENTATION",
            "RISK_ASSESSMENT",
            "FRAUD_ANALYSIS",
            "COMPLIANCE_REPORT",
            "EXECUTIVE_DASHBOARD"
        ]
        formats = ["PDF", "EXCEL", "CSV", "JSON", "HTML"]
        
        is_anomaly = anomaly_score > 0.7
        
        report_type = random.choice(report_types)
        format_type = random.choice(formats)
        
        if is_anomaly:
            status = "FAILED"
            generation_time_seconds = random.randint(600, 3600)
            error = random.choice([
                "Query timeout exceeded",
                "Insufficient data for period",
                "Template rendering failed",
                "Export format error",
                "Memory limit exceeded"
            ])
            file_size_mb = 0
        else:
            status = "SUCCESS"
            generation_time_seconds = random.randint(5, 300)
            error = None
            file_size_mb = round(random.uniform(0.1, 50.0), 2)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "log_type": "report_generation",
            "report_type": report_type,
            "report_id": f"RPT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "format": format_type,
            "status": status,
            "generation_time_seconds": generation_time_seconds,
            "file_size_mb": file_size_mb,
            "records_included": random.randint(1000, 1000000) if status == "SUCCESS" else 0,
            "date_range": {
                "from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d")
            },
            "requested_by": random.choice(VIETNAMESE_NAMES),
            "department": random.choice(["Finance", "Risk Management", "Compliance", "Executive"]),
            "delivery_method": random.choice(["EMAIL", "DOWNLOAD", "SFTP", "API"]),
            "error": error,
            "anomaly_score": anomaly_score
        }
