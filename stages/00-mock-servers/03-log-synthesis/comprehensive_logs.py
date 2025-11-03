"""
Comprehensive Log Templates Library - Main Interface
Supports 59 different log types across 13 major categories for banking system simulation
"""
from typing import Dict, Any, List
from log_templates.infrastructure_logs import InfrastructureLogTemplates
from log_templates.application_logs import ApplicationLogTemplates
from log_templates.database_logs import DatabaseLogTemplates
from log_templates.security_logs import SecurityLogs
from log_templates.transaction_logs import TransactionLogs
from log_templates.fraud_logs import FraudLogs
from log_templates.analytics_logs import AnalyticsLogs
from log_templates.compliance_logs import ComplianceLogs
from log_templates.integration_logs import IntegrationLogs
from log_templates.monitoring_logs import MonitoringLogs
from log_templates.business_intelligence_logs import BusinessIntelligenceLogs
from log_templates.specialized_logs import SpecializedLogs
from log_templates.log_management_logs import LogManagementLogs

class ComprehensiveLogTemplates:
    """
    Complete library of 59 log types for banking system anomaly detection
    Organized by 13 categories - this is the main interface
    """
    
    # I. Infrastructure & System Logs (9 types)
    generate_server_metrics_log = InfrastructureLogTemplates.server_metrics_log
    generate_process_log = InfrastructureLogTemplates.process_log
    generate_filesystem_log = InfrastructureLogTemplates.filesystem_log
    generate_container_log = InfrastructureLogTemplates.container_log
    generate_kubernetes_log = InfrastructureLogTemplates.kubernetes_log
    generate_load_balancer_log = InfrastructureLogTemplates.load_balancer_log
    generate_firewall_log = InfrastructureLogTemplates.firewall_log
    generate_dns_log = InfrastructureLogTemplates.dns_log
    generate_cdn_log = InfrastructureLogTemplates.cdn_log
    
    # II. Application Layer Logs (6 types) - removed non-existent methods
    generate_web_server_log = ApplicationLogTemplates.web_server_log
    generate_application_framework_log = ApplicationLogTemplates.application_framework_log
    generate_apm_trace_log = ApplicationLogTemplates.apm_trace_log
    generate_message_queue_log = ApplicationLogTemplates.message_queue_log
    generate_service_mesh_log = ApplicationLogTemplates.service_mesh_log
    generate_api_gateway_log = ApplicationLogTemplates.api_gateway_log
    
    # III. Database & Data Store Logs (8 types) - removed generate_ prefix
    generate_database_query_log = DatabaseLogTemplates.database_query_log
    generate_database_connection_log = DatabaseLogTemplates.database_connection_log
    generate_database_transaction_log = DatabaseLogTemplates.database_transaction_log
    generate_database_replication_log = DatabaseLogTemplates.database_replication_log
    generate_database_backup_log = DatabaseLogTemplates.database_backup_log
    generate_redis_cache_log = DatabaseLogTemplates.redis_cache_log
    generate_mongodb_log = DatabaseLogTemplates.mongodb_log
    generate_elasticsearch_log = DatabaseLogTemplates.elasticsearch_log
    
    # IV. Security & Authentication Logs (7 types) - added generate_ prefix
    generate_authentication_log = SecurityLogs.generate_authentication_log
    generate_authorization_log = SecurityLogs.generate_authorization_log
    generate_session_log = SecurityLogs.generate_session_log
    generate_encryption_log = SecurityLogs.generate_encryption_log
    generate_data_access_log = SecurityLogs.generate_data_access_log
    generate_intrusion_detection_log = SecurityLogs.generate_intrusion_detection_log
    generate_security_incident_log = SecurityLogs.generate_security_incident_log
    
    # V. Business Transaction Logs (5 types) - added generate_ prefix
    generate_payment_log = TransactionLogs.generate_payment_log
    generate_transfer_log = TransactionLogs.generate_transfer_log
    generate_withdrawal_log = TransactionLogs.generate_withdrawal_log
    generate_loan_log = TransactionLogs.generate_loan_log
    generate_forex_log = TransactionLogs.generate_forex_log
    
    # VI. Fraud Detection & AML Logs (3 types)
    generate_fraud_detection_log = FraudLogs.generate_fraud_detection_log
    generate_aml_screening_log = FraudLogs.generate_aml_log
    generate_risk_scoring_log = FraudLogs.generate_kyc_log
    
    # VII. User Behavior & Analytics Logs (6 types)
    generate_user_activity_log = AnalyticsLogs.generate_user_activity_log
    generate_clickstream_log = AnalyticsLogs.generate_clickstream_log
    generate_session_analytics_log = AnalyticsLogs.generate_customer_journey_log
    generate_feature_usage_log = AnalyticsLogs.generate_feature_usage_log
    generate_ab_test_log = AnalyticsLogs.generate_ab_test_log
    generate_conversion_log = AnalyticsLogs.generate_conversion_log
    
    # VIII. Compliance & Audit Logs (3 types)
    generate_regulatory_compliance_log = ComplianceLogs.generate_regulatory_compliance_log
    generate_audit_trail_log = ComplianceLogs.generate_audit_trail_log
    generate_data_retention_log = ComplianceLogs.generate_data_retention_log
    
    # IX. External Integration Logs (3 types)
    generate_third_party_api_log = IntegrationLogs.generate_third_party_service_log
    generate_webhook_log = IntegrationLogs.generate_message_queue_log
    generate_integration_error_log = IntegrationLogs.generate_api_gateway_log
    
    # X. Monitoring & Observability Logs (3 types)
    generate_metrics_log = MonitoringLogs.generate_metrics_log
    generate_distributed_tracing_log = MonitoringLogs.generate_distributed_tracing_log
    generate_health_check_log = MonitoringLogs.generate_health_check_log
    
    # XI. Business Intelligence & Analytics Logs (2 types)
    generate_etl_pipeline_log = BusinessIntelligenceLogs.generate_etl_pipeline_log
    generate_report_generation_log = BusinessIntelligenceLogs.generate_report_generation_log
    
    # XII. Specialized Logs (2 types)
    generate_blockchain_log = SpecializedLogs.generate_blockchain_log
    generate_iot_device_log = SpecializedLogs.generate_iot_device_log
    
    # XIII. Log Management Infrastructure (2 types)
    generate_log_aggregation_log = LogManagementLogs.generate_log_aggregation_log
    generate_log_storage_log = LogManagementLogs.generate_log_storage_log
    
    @staticmethod
    def get_all_log_types() -> List[str]:
        """Get list of all available log types"""
        return [
            # I. Infrastructure & System (9 types)
            "server_metrics", "process", "filesystem", "container", "kubernetes",
            "load_balancer", "firewall", "dns", "cdn",
            
            # II. Application Layer (6 types)
            "web_server", "application_framework", "apm_trace", "message_queue",
            "service_mesh", "api_gateway",
            
            # III. Database & Data Store (8 types)
            "database_query", "database_connection", "database_transaction",
            "database_replication", "database_backup", "redis_cache", "mongodb", "elasticsearch",
            
            # IV. Security & Authentication (7 types)
            "authentication", "authorization", "session", "encryption",
            "data_access", "intrusion_detection", "security_incident",
            
            # V. Business Transaction (5 types)
            "payment", "transfer", "withdrawal", "loan", "forex",
            
            # VI. Fraud Detection & AML (3 types)
            "fraud_detection", "aml_screening", "risk_scoring",
            
            # VII. User Behavior & Analytics (6 types)
            "user_activity", "clickstream", "session_analytics", "feature_usage",
            "ab_test", "conversion",
            
            # VIII. Compliance & Audit (3 types)
            "regulatory_compliance", "audit_trail", "data_retention",
            
            # IX. External Integration (3 types)
            "third_party_api", "webhook", "integration_error",
            
            # X. Monitoring & Observability (3 types)
            "metrics", "distributed_tracing", "health_check",
            
            # XI. Business Intelligence & Analytics (2 types)
            "etl_pipeline", "report_generation",
            
            # XII. Specialized (2 types)
            "blockchain", "iot_device",
            
            # XIII. Log Management Infrastructure (2 types)
            "log_aggregation", "log_storage"
        ]
    
    @staticmethod
    def get_log_categories() -> Dict[str, List[str]]:
        """Get log types organized by categories"""
        return {
            "infrastructure": ["server_metrics", "process", "filesystem", "container", "kubernetes",
                             "load_balancer", "firewall", "dns", "cdn"],
            "application": ["web_server", "application_framework", "apm_trace", "message_queue",
                          "service_mesh", "api_gateway"],
            "database": ["database_query", "database_connection", "database_transaction",
                        "database_replication", "database_backup", "redis_cache", "mongodb", "elasticsearch"],
            "security": ["authentication", "authorization", "session", "encryption",
                        "data_access", "intrusion_detection", "security_incident"],
            "transaction": ["payment", "transfer", "withdrawal", "loan", "forex"],
            "fraud": ["fraud_detection", "aml_screening", "risk_scoring"],
            "analytics": ["user_activity", "clickstream", "session_analytics", "feature_usage",
                         "ab_test", "conversion"],
            "compliance": ["regulatory_compliance", "audit_trail", "data_retention"],
            "integration": ["third_party_api", "webhook", "integration_error"],
            "monitoring": ["metrics", "distributed_tracing", "health_check"],
            "business_intelligence": ["etl_pipeline", "report_generation"],
            "specialized": ["blockchain", "iot_device"],
            "log_management": ["log_aggregation", "log_storage"]
        }
    
    @staticmethod
    def get_log_by_type(log_type: str, anomaly_score: float = 0.0) -> Dict[str, Any]:
        """Get log entry by type name with anomaly score"""
        log_generators = {
            # Infrastructure & System
            "server_metrics": ComprehensiveLogTemplates.generate_server_metrics_log,
            "process": ComprehensiveLogTemplates.generate_process_log,
            "filesystem": ComprehensiveLogTemplates.generate_filesystem_log,
            "container": ComprehensiveLogTemplates.generate_container_log,
            "kubernetes": ComprehensiveLogTemplates.generate_kubernetes_log,
            "load_balancer": ComprehensiveLogTemplates.generate_load_balancer_log,
            "firewall": ComprehensiveLogTemplates.generate_firewall_log,
            "dns": ComprehensiveLogTemplates.generate_dns_log,
            "cdn": ComprehensiveLogTemplates.generate_cdn_log,
            
            # Application Layer
            "web_server": ComprehensiveLogTemplates.generate_web_server_log,
            "application_framework": ComprehensiveLogTemplates.generate_application_framework_log,
            "apm_trace": ComprehensiveLogTemplates.generate_apm_trace_log,
            "message_queue": ComprehensiveLogTemplates.generate_message_queue_log,
            "service_mesh": ComprehensiveLogTemplates.generate_service_mesh_log,
            "api_gateway": ComprehensiveLogTemplates.generate_api_gateway_log,
            
            # Database & Data Store
            "database_query": ComprehensiveLogTemplates.generate_database_query_log,
            "database_connection": ComprehensiveLogTemplates.generate_database_connection_log,
            "database_transaction": ComprehensiveLogTemplates.generate_database_transaction_log,
            "database_replication": ComprehensiveLogTemplates.generate_database_replication_log,
            "database_backup": ComprehensiveLogTemplates.generate_database_backup_log,
            "redis_cache": ComprehensiveLogTemplates.generate_redis_cache_log,
            "mongodb": ComprehensiveLogTemplates.generate_mongodb_log,
            "elasticsearch": ComprehensiveLogTemplates.generate_elasticsearch_log,
            
            # Security & Authentication
            "authentication": ComprehensiveLogTemplates.generate_authentication_log,
            "authorization": ComprehensiveLogTemplates.generate_authorization_log,
            "session": ComprehensiveLogTemplates.generate_session_log,
            "encryption": ComprehensiveLogTemplates.generate_encryption_log,
            "data_access": ComprehensiveLogTemplates.generate_data_access_log,
            "intrusion_detection": ComprehensiveLogTemplates.generate_intrusion_detection_log,
            "security_incident": ComprehensiveLogTemplates.generate_security_incident_log,
            
            # Business Transaction
            "payment": ComprehensiveLogTemplates.generate_payment_log,
            "transfer": ComprehensiveLogTemplates.generate_transfer_log,
            "withdrawal": ComprehensiveLogTemplates.generate_withdrawal_log,
            "loan": ComprehensiveLogTemplates.generate_loan_log,
            "forex": ComprehensiveLogTemplates.generate_forex_log,
            
            # Fraud Detection & AML
            "fraud_detection": ComprehensiveLogTemplates.generate_fraud_detection_log,
            "aml_screening": ComprehensiveLogTemplates.generate_aml_screening_log,
            "risk_scoring": ComprehensiveLogTemplates.generate_risk_scoring_log,
            
            # User Behavior & Analytics
            "user_activity": ComprehensiveLogTemplates.generate_user_activity_log,
            "clickstream": ComprehensiveLogTemplates.generate_clickstream_log,
            "session_analytics": ComprehensiveLogTemplates.generate_session_analytics_log,
            "feature_usage": ComprehensiveLogTemplates.generate_feature_usage_log,
            "ab_test": ComprehensiveLogTemplates.generate_ab_test_log,
            "conversion": ComprehensiveLogTemplates.generate_conversion_log,
            
            # Compliance & Audit
            "regulatory_compliance": ComprehensiveLogTemplates.generate_regulatory_compliance_log,
            "audit_trail": ComprehensiveLogTemplates.generate_audit_trail_log,
            "data_retention": ComprehensiveLogTemplates.generate_data_retention_log,
            
            # External Integration
            "third_party_api": ComprehensiveLogTemplates.generate_third_party_api_log,
            "webhook": ComprehensiveLogTemplates.generate_webhook_log,
            "integration_error": ComprehensiveLogTemplates.generate_integration_error_log,
            
            # Monitoring & Observability
            "metrics": ComprehensiveLogTemplates.generate_metrics_log,
            "distributed_tracing": ComprehensiveLogTemplates.generate_distributed_tracing_log,
            "health_check": ComprehensiveLogTemplates.generate_health_check_log,
            
            # Business Intelligence & Analytics
            "etl_pipeline": ComprehensiveLogTemplates.generate_etl_pipeline_log,
            "report_generation": ComprehensiveLogTemplates.generate_report_generation_log,
            
            # Specialized
            "blockchain": ComprehensiveLogTemplates.generate_blockchain_log,
            "iot_device": ComprehensiveLogTemplates.generate_iot_device_log,
            
            # Log Management Infrastructure
            "log_aggregation": ComprehensiveLogTemplates.generate_log_aggregation_log,
            "log_storage": ComprehensiveLogTemplates.generate_log_storage_log,
        }
        
        generator = log_generators.get(log_type)
        if generator:
            return generator(anomaly_score)
        else:
            # Fallback to basic application log
            return ComprehensiveLogTemplates.generate_application_framework_log(anomaly_score)


class ComprehensiveLogGenerator:
    """Convenience wrapper for generating logs"""
    
    def __init__(self):
        self.templates = ComprehensiveLogTemplates()
    
    def generate(self, log_type: str, anomaly_score: float = 0.0) -> Dict[str, Any]:
        """Generate a log of the specified type"""
        return ComprehensiveLogTemplates.get_log_by_type(log_type, anomaly_score)
    
    def get_available_types(self) -> List[str]:
        """Get list of all available log types"""
        return ComprehensiveLogTemplates.get_all_log_types()
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get log types organized by categories"""
        return ComprehensiveLogTemplates.get_log_categories()
