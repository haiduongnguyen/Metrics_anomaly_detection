"""
Log Normalizer
Transforms various log formats into standardized OpenTelemetry LogRecord objects
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import re

from log_record import LogRecordObject, Resource, InstrumentationScope, Severity, SeverityNumber, LogAttribute

class LogNormalizer:
    """
    Normalizes logs from different sources into OpenTelemetry LogRecord format
    """
    
    def __init__(self):
        # Source type mappings for standardization
        self.source_mappings = {
            "log-synthesis": "log-synthesis",
            "scenario-orchestrator": "scenario-orchestrator",
            "pattern-generator": "pattern-generator",
            "state-manager": "state-manager",
            "ingestion-interface": "ingestion-interface"
        }
        
        # Log type category mappings
        self.log_type_categories = {
            "infrastructure": ["server_log", "container_log", "network_log", "storage_log"],
            "application": ["application_log", "api_gateway_log", "microservice_log"],
            "database": ["database_log", "sql_query_log", "nosql_log"],
            "security": ["security_log", "authentication_log", "authorization_log"],
            "transaction": ["transaction_log", "payment_log", "transfer_log"],
            "fraud": ["fraud_detection_log", "aml_log", "kyc_log"],
            "user_behavior": ["user_activity_log", "session_log", "clickstream_log"],
            "compliance": ["audit_log", "regulatory_log", "gdpr_log"],
            "monitoring": ["metrics_log", "trace_log", "alert_log"],
            "integration": ["api_gateway_log", "webhook_log", "third_party_log"]
        }
    
    def normalize(self, raw_log: Dict[str, Any]) -> LogRecordObject:
        """
        Normalize a raw log entry into OpenTelemetry LogRecord
        
        Args:
            raw_log: Raw log entry with source, timestamp, log_type, and data
            
        Returns:
            Normalized LogRecordObject
        """
        try:
            source = raw_log.get("source", "unknown")
            timestamp = raw_log.get("timestamp", datetime.now(timezone.utc).isoformat())
            log_type = raw_log.get("log_type", "unknown")
            data = raw_log.get("data", {})
            metadata = raw_log.get("metadata", {})
        except Exception as e:
            print(f"[v0] ERROR in normalize extraction: {e}")
            print(f"[v0] raw_log type: {type(raw_log)}")
            print(f"[v0] raw_log: {raw_log}")
            raise
        
        # Parse timestamp
        try:
            if isinstance(timestamp, str):
                # Handle various timestamp formats
                if timestamp.endswith('Z'):
                    dt = datetime.fromisoformat(timestamp[:-1] + '+00:00')
                else:
                    dt = datetime.fromisoformat(timestamp)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
        except Exception:
            dt = datetime.now(timezone.utc)
        
        # Extract basic information
        body = self._extract_body(log_type, data)
        severity = self._determine_severity(log_type, data)
        attributes = self._extract_attributes(log_type, data, source, metadata)
        
        # Create resource information
        resource = self._create_resource(source, log_type, data)
        
        # Create instrumentation scope
        instrumentation_scope = self._create_instrumentation_scope(source, log_type)
        
        # Extract trace context if available
        trace_context = self._extract_trace_context(data)
        
        # Create LogRecord
        log_record = LogRecordObject.create_from_timestamp(
            timestamp=dt,
            body=body,
            severity_text=severity,
            severity_number=self._severity_to_number(severity),
            attributes=attributes,
            resource=resource,
            instrumentation_scope=instrumentation_scope,
            **trace_context
        )
        
        # Add observed timestamp (when we processed the log)
        log_record.observed_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        return log_record
    
    def _extract_body(self, log_type: str, data: Dict[str, Any]) -> str:
        """Extract meaningful body content from log data"""
        
        # Different body extraction strategies based on log type
        if log_type == "security_log":
            event_type = data.get("event_type", "unknown")
            user = data.get("account", data.get("user_id", "unknown"))
            ip = data.get("source_ip", data.get("ip_address", "unknown"))
            return f"Security event: {event_type} from user {user} at IP {ip}"
        
        elif log_type == "transaction_log":
            txn_data = data.get("transaction", {})
            txn_id = txn_data.get("id", data.get("transaction_id", "unknown"))
            status = txn_data.get("status", data.get("status", "unknown"))
            amount = data.get("amount", txn_data.get("amount", 0))
            currency = data.get("currency", txn_data.get("currency", "VND"))
            return f"Transaction {txn_id}: {status} - {amount:,} {currency}"
        
        elif log_type == "application_log":
            level = data.get("level", "INFO")
            service = data.get("service", "unknown")
            message = data.get("message", "Application log entry")
            return f"[{level}] {service}: {message}"
        
        elif log_type == "server_log":
            host = data.get("host", "unknown")
            cpu = data.get("cpu_usage_percent", 0)
            memory = data.get("memory_used_gb", 0)
            return f"Server metrics from {host}: CPU {cpu:.1f}%, Memory {memory:.1f}GB"
        
        elif "message" in data:
            return str(data["message"])
        
        elif "error" in data and data["error"]:
            error = data["error"]
            if isinstance(error, dict):
                return f"Error: {error.get('type', 'Unknown')} - {error.get('details', 'No details')}"
            return f"Error: {error}"
        
        else:
            # Fallback: create summary from data
            key_fields = ["level", "status", "event_type", "transaction_id", "user_id"]
            summary_parts = []
            for field in key_fields:
                if field in data:
                    summary_parts.append(f"{field}: {data[field]}")
            
            if summary_parts:
                return f"{log_type}: " + ", ".join(summary_parts)
            
            return f"{log_type} log entry"
    
    def _determine_severity(self, log_type: str, data: Dict[str, Any]) -> Severity:
        """Determine OpenTelemetry severity based on log content"""
        
        # Check for explicit severity indicators
        if "level" in data:
            level = str(data["level"]).upper()
            if level in ["FATAL", "CRITICAL"]:
                return Severity.FATAL
            elif level in ["ERROR", "ERR"]:
                return Severity.ERROR
            elif level in ["WARN", "WARNING"]:
                return Severity.WARN
            elif level in ["INFO"]:
                return Severity.INFO
            elif level in ["DEBUG", "TRACE"]:
                return Severity.DEBUG
        
        # Check for status indicators
        if "status" in data:
            status = str(data["status"]).lower()
            if status in ["failed", "error", "critical", "fatal"]:
                return Severity.ERROR
            elif status in ["warning", "degraded", "slow"]:
                return Severity.WARN
        
        # Check event types for security logs
        if "event_type" in data:
            event_type = str(data["event_type"]).lower()
            if any(word in event_type for word in ["breach", "attack", "intrusion", "malware"]):
                return Severity.FATAL
            elif any(word in event_type for word in ["failure", "blocked", "denied"]):
                return Severity.ERROR
            elif any(word in event_type for word in ["suspicious", "anomaly"]):
                return Severity.WARN
        
        # Check anomaly score
        anomaly_score = data.get("anomaly_score", 0)
        try:
            score = float(anomaly_score)
            if score >= 85:
                return Severity.FATAL
            elif score >= 70:
                return Severity.ERROR
            elif score >= 50:
                return Severity.WARN
        except (ValueError, TypeError):
            pass
        
        # Default severity based on log type
        high_severity_types = ["security_log", "fraud_detection_log", "aml_log"]
        medium_severity_types = ["transaction_log", "database_log", "server_log"]
        
        if log_type in high_severity_types:
            return Severity.WARN
        elif log_type in medium_severity_types:
            return Severity.INFO
        else:
            return Severity.INFO
    
    def _severity_to_number(self, severity: Severity) -> SeverityNumber:
        """Convert severity enum to number"""
        mapping = {
            Severity.TRACE: SeverityNumber.TRACE,
            Severity.DEBUG: SeverityNumber.DEBUG1,
            Severity.INFO: SeverityNumber.INFO,
            Severity.WARN: SeverityNumber.WARN,
            Severity.ERROR: SeverityNumber.ERROR,
            Severity.FATAL: SeverityNumber.FATAL
        }
        return mapping.get(severity, SeverityNumber.INFO)
    
    def _extract_attributes(self, log_type: str, data: Dict[str, Any], source: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and standardize attributes"""
        attributes = {}
        
        # Core attributes
        attributes["source"] = source
        attributes["original_log_type"] = log_type
        attributes["log.category"] = self._map_log_type_to_category(log_type)
        
        # Preserve key data fields as attributes
        key_attributes = [
            "user_id", "username", "account", "transaction_id", "session_id",
            "ip_address", "source_ip", "host", "service", "level", "status",
            "event_type", "error_code", "amount", "currency", "gateway"
        ]
        
        for attr in key_attributes:
            if attr in data:
                attributes[attr] = data[attr]
        
        # Anomaly score if present
        if "anomaly_score" in data:
            attributes["anomaly_score"] = data["anomaly_score"]
            attributes["anomaly.high"] = float(data["anomaly_score"]) > 70
        
        # Performance metrics
        performance_metrics = [
            "cpu_usage_percent", "memory_used_gb", "disk_io_read_mb", "disk_io_write_mb",
            "response_time", "processing_time_ms", "duration_ms", "latency_ms"
        ]
        
        for metric in performance_metrics:
            if metric in data:
                attributes[f"performance.{metric}"] = data[metric]
        
        # Add metadata attributes
        if metadata:
            for key, value in metadata.items():
                attributes[f"meta.{key}"] = value
        
        # Special handling for nested objects
        nested_objects = ["transaction", "authentication", "network", "database"]
        for obj_name in nested_objects:
            if obj_name in data and isinstance(data[obj_name], dict):
                for key, value in data[obj_name].items():
                    attributes[f"{obj_name}.{key}"] = value
        
        # Clean up attribute names (replace spaces with underscores)
        cleaned_attributes = {}
        for key, value in attributes.items():
            clean_key = str(key).replace(" ", "_").replace(".", ".")  # Keep dots for hierarchy
            cleaned_attributes[clean_key] = value
        
        return cleaned_attributes
    
    def _create_resource(self, source: str, log_type: str, data: Dict[str, Any]) -> Resource:
        """Create resource information"""
        attributes = {}
        
        # Service information
        service_name = {
            "log-synthesis": "log-synthesis-service",
            "scenario-orchestrator": "scenario-orchestrator-service", 
            "pattern-generator": "pattern-generator-service",
            "state-manager": "state-manager-service",
            "ingestion-interface": "ingestion-interface-service"
        }.get(source, f"{source}-service")
        
        attributes["service.name"] = service_name
        attributes["service.version"] = "1.0.0"
        
        # Host information
        if "host" in data:
            attributes["host.name"] = data["host"]
        elif "hostname" in data:
            attributes["host.name"] = data["hostname"]
        else:
            attributes["host.name"] = "unknown-host"
        
        # IP/Network information
        ip_fields = ["source_ip", "ip_address", "client_ip"]
        for field in ip_fields:
            if field in data:
                attributes["host.ip"] = data[field]
                break
        
        # Environment information
        attributes["environment"] = "development"
        attributes["deployment.environment"] = "docker"
        
        # Log category
        attributes["log.category"] = self._map_log_type_to_category(log_type)
        
        return Resource(attributes=attributes)
    
    def _create_instrumentation_scope(self, source: str, log_type: str) -> InstrumentationScope:
        """Create instrumentation scope information"""
        scope_name = f"{source}.{log_type.replace('_log', '')}"
        return InstrumentationScope(
            name=scope_name,
            version="1.0.0",
            attributes={}
        )
    
    def _extract_trace_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trace context if available"""
        trace_context = {}
        
        trace_fields = ["trace_id", "span_id", "request_id"]
        for field in trace_fields:
            if field in data:
                if field == "request_id":
                    trace_context["span_id"] = data[field][:16]  # Take first 16 chars as span_id
                else:
                    trace_context[field] = data[field]
        
        return trace_context
    
    def _map_log_type_to_category(self, log_type: str) -> str:
        """Map log type to standardized category"""
        for category, types in self.log_type_categories.items():
            if log_type in types:
                return category
        return "unknown"
    
    def normalize_batch(self, raw_logs: List[Dict[str, Any]]) -> List[LogRecordObject]:
        """Normalize a batch of logs"""
        normalized_logs = []
        
        for raw_log in raw_logs:
            try:
                normalized_log = self.normalize(raw_log)
                normalized_logs.append(normalized_log)
            except Exception as e:
                print(f"Failed to normalize log: {e}")
                # Create a fallback log record
                fallback_log = LogRecordObject.create_from_timestamp(
                    timestamp=datetime.now(timezone.utc),
                    body=f"Failed to normalize log: {str(e)}",
                    severity_text=Severity.ERROR,
                    severity_number=SeverityNumber.ERROR,
                    attributes={
                        "source": raw_log.get("source", "unknown"),
                        "original_log_type": raw_log.get("log_type", "unknown"),
                        "normalization.error": str(e)
                    }
                )
                normalized_logs.append(fallback_log)
        
        return normalized_logs
