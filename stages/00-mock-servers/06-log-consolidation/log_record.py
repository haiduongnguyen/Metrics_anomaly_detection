"""
OpenTelemetry LogRecord Object Implementation
Defines the standardized LogRecord structure based on OpenTelemetry specification
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timezone
from enum import Enum
import uuid

class Severity(str, Enum):
    """OpenTelemetry LogRecord severity levels"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

class SeverityNumber(int, Enum):
    """OpenTelemetry severity number mapping"""
    # Trace/Debug: 1-8
    TRACE = 1
    DEBUG1 = 2
    DEBUG2 = 3
    DEBUG3 = 4
    DEBUG4 = 5
    DEBUG5 = 6
    DEBUG6 = 7
    DEBUG7 = 8
    DEBUG8 = 9
    
    # Info: 9-12
    INFO = 9
    INFO2 = 10
    INFO3 = 11
    INFO4 = 12
    
    # Warn: 13-16
    WARN = 13
    WARN2 = 14
    WARN3 = 15
    WARN4 = 16
    
    # Error: 17-20
    ERROR = 17
    ERROR2 = 18
    ERROR3 = 19
    ERROR4 = 20
    
    # Fatal: 21-24
    FATAL = 21
    FATAL2 = 22
    FATAL3 = 23
    FATAL4 = 24

class LogAttribute(BaseModel):
    """Individual log attribute with type checking"""
    key: str
    value: Union[str, int, float, bool, list, dict]

class Resource(BaseModel):
    """Resource that generated the log"""
    attributes: Dict[str, str] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Ensure standard resource attributes
        default_attributes = {
            "service.name": "unknown-service",
            "service.version": "1.0.0",
            "host.name": "unknown-host",
            "host.ip": "127.0.0.1",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
            "telemetry.sdk.version": "1.0.0"
        }
        
        # Update with provided attributes, preserving defaults
        for key, value in {**default_attributes, **self.attributes}.items():
            self.attributes[key] = str(value)

class InstrumentationScope(BaseModel):
    """Instrumentation scope information"""
    name: str
    version: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)

class LogRecordObject(BaseModel):
    """
    OpenTelemetry LogRecord implementation
    Based on https://opentelemetry.io/docs/specs/otel/logs/data-model/
    """
    
    # Required fields
    timestamp: str = Field(description="Time when the event occurred", 
                          example="2025-01-02T10:30:45.123456789Z")
    body: Union[str, dict, list] = Field(description="Log body content")
    
    # Optional core fields
    observed_timestamp: Optional[str] = Field(
        default=None,
        description="Time when the log was observed/collected"
    )
    severity_text: Optional[Severity] = Field(
        default=Severity.INFO,
        description="Textual severity level"
    )
    severity_number: Optional[SeverityNumber] = Field(
        default=SeverityNumber.INFO,
        description="Numeric severity level (1-24)"
    )
    
    # Optional fields for correlation
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for correlation with traces"
    )
    span_id: Optional[str] = Field(
        default=None,
        description="Span ID for correlation with traces"
    )
    trace_flags: Optional[int] = Field(
        default=None,
        description="Trace flags"
    )
    
    # Structured data
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value attributes providing context"
    )
    
    # Resource and instrumentation
    resource: Resource = Field(default_factory=Resource)
    instrumentation_scope: Optional[InstrumentationScope] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }
    
    @classmethod
    def create_from_timestamp(cls, timestamp: datetime, **kwargs):
        """Create LogRecord with timestamp from datetime object"""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        return cls(
            timestamp=timestamp.isoformat().replace('+00:00', 'Z'),
            **kwargs
        )
    
    def with_timestamp(self, timestamp: Union[str, datetime]) -> 'LogRecordObject':
        """Create new LogRecord with updated timestamp"""
        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            timestamp = timestamp.isoformat().replace('+00:00', 'Z')
        
        return self.copy(update={"timestamp": timestamp})
    
    def with_severity(self, severity: Union[str, int, Severity, SeverityNumber]) -> 'LogRecordObject':
        """Create new LogRecord with updated severity"""
        if isinstance(severity, str):
            severity_text = Severity(severity.upper())
            severity_number = self._severity_text_to_number(severity_text)
        elif isinstance(severity, int):
            severity_number = SeverityNumber(severity)
            severity_text = self._severity_number_to_text(severity_number)
        elif isinstance(severity, Severity):
            severity_text = severity
            severity_number = self._severity_text_to_number(severity_text)
        elif isinstance(severity, SeverityNumber):
            severity_number = severity
            severity_text = self._severity_number_to_text(severity_number)
        else:
            raise ValueError(f"Invalid severity type: {type(severity)}")
        
        return self.copy(update={
            "severity_text": severity_text,
            "severity_number": severity_number
        })
    
    def with_trace_context(self, trace_id: str, span_id: str, trace_flags: int = 0) -> 'LogRecordObject':
        """Create new LogRecord with trace context"""
        return self.copy(update={
            "trace_id": trace_id,
            "span_id": span_id,
            "trace_flags": trace_flags
        })
    
    def add_attribute(self, key: str, value: Any) -> 'LogRecordObject':
        """Add or update an attribute"""
        new_attributes = self.attributes.copy()
        new_attributes[key] = value
        return self.copy(update={"attributes": new_attributes})
    
    def remove_attribute(self, key: str) -> 'LogRecordObject':
        """Remove an attribute"""
        new_attributes = self.attributes.copy()
        new_attributes.pop(key, None)
        return self.copy(update={"attributes": new_attributes})
    
    def has_high_anomaly_score(self, threshold: float = 70.0) -> bool:
        """Check if log has high anomaly score"""
        anomaly_score = self.attributes.get('anomaly_score', 0)
        try:
            return float(anomaly_score) > threshold
        except (ValueError, TypeError):
            return False
    
    def is_from_source(self, source: str) -> bool:
        """Check if log is from specific source"""
        return self.attributes.get('source') == source
    
    def get_log_type(self) -> str:
        """Get the original log type"""
        return self.attributes.get('original_log_type', 'unknown')
    
    def _severity_text_to_number(self, severity_text: Severity) -> SeverityNumber:
        """Convert severity text to number"""
        mapping = {
            Severity.TRACE: SeverityNumber.TRACE,
            Severity.DEBUG: SeverityNumber.DEBUG,
            Severity.INFO: SeverityNumber.INFO,
            Severity.WARN: SeverityNumber.WARN,
            Severity.ERROR: SeverityNumber.ERROR,
            Severity.FATAL: SeverityNumber.FATAL
        }
        return mapping.get(severity_text, SeverityNumber.INFO)
    
    def _severity_number_to_text(self, severity_number: SeverityNumber) -> Severity:
        """Convert severity number to text"""
        if severity_number <= SeverityNumber.DEBUG8:
            return Severity.DEBUG if severity_number >= SeverityNumber.DEBUG1 else Severity.TRACE
        elif severity_number <= SeverityNumber.INFO4:
            return Severity.INFO
        elif severity_number <= SeverityNumber.WARN4:
            return Severity.WARN
        elif severity_number <= SeverityNumber.ERROR4:
            return Severity.ERROR
        else:
            return Severity.FATAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogRecordObject':
        """Create LogRecord from dictionary"""
        return cls(**data)

class LogRecordBatch(BaseModel):
    """Batch of LogRecord objects for efficient processing"""
    logs: List[LogRecordObject]
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    batch_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def count_by_severity(self) -> Dict[str, int]:
        """Count logs by severity level"""
        counts = {}
        for log in self.logs:
            severity = log.severity_text.value if log.severity_text else "UNKNOWN"
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def count_by_source(self) -> Dict[str, int]:
        """Count logs by source"""
        counts = {}
        for log in self.logs:
            source = log.attributes.get('source', 'unknown')
            counts[source] = counts.get(source, 0) + 1
        return counts
    
    def get_high_anomaly_logs(self, threshold: float = 70.0) -> List['LogRecordObject']:
        """Get logs with high anomaly scores"""
        return [log for log in self.logs if log.has_high_anomaly_score(threshold)]
    
    def to_json_lines(self) -> str:
        """Convert batch to JSON lines format"""
        return '\n'.join(log.model_dump_json(exclude_none=True) for log in self.logs)
