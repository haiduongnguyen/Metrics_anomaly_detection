"""
Comprehensive Log Templates Library
Organized by categories for better maintainability
"""
from .common import LogCommonData
from .infrastructure_logs import InfrastructureLogTemplates
from .application_logs import ApplicationLogTemplates
from .database_logs import DatabaseLogTemplates
from .security_logs import SecurityLogs
from .transaction_logs import TransactionLogs
from .fraud_logs import FraudLogs
from .analytics_logs import AnalyticsLogs
from .compliance_logs import ComplianceLogs
from .integration_logs import IntegrationLogs
from .monitoring_logs import MonitoringLogs
from .business_intelligence_logs import BusinessIntelligenceLogs
from .specialized_logs import SpecializedLogs
from .log_management_logs import LogManagementLogs

__all__ = [
    'LogCommonData',
    'InfrastructureLogTemplates',
    'ApplicationLogTemplates',
    'DatabaseLogTemplates',
    'SecurityLogs',
    'TransactionLogs',
    'FraudLogs',
    'AnalyticsLogs',
    'ComplianceLogs',
    'IntegrationLogs',
    'MonitoringLogs',
    'BusinessIntelligenceLogs',
    'SpecializedLogs',
    'LogManagementLogs'
]
