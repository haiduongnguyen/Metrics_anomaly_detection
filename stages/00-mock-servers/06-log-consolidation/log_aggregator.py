"""
Log Aggregator
Provides aggregation and analytics functionality for consolidated logs
"""
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import statistics
import math

from log_record import LogRecordObject, Severity, SeverityNumber

class LogAggregator:
    """
    Aggregates and analyzes consolidated logs
    """
    
    def __init__(self):
        self.severity_weights = {
            SeverityNumber.TRACE: 1,
            SeverityNumber.DEBUG1: 2,
            SeverityNumber.INFO: 4,
            SeverityNumber.WARN: 8,
            SeverityNumber.ERROR: 16,
            SeverityNumber.FATAL: 32
        }
    
    def aggregate_stats(self, logs: List[LogRecordObject]) -> Dict[str, Any]:
        """
        Generate comprehensive statistics for a collection of logs
        """
        if not logs:
            return {"message": "No logs available for analysis"}
        
        # Basic counts
        total_logs = len(logs)
        unique_sources = len(set(log.attributes.get('source', 'unknown') for log in logs))
        unique_log_types = len(set(log.attributes.get('original_log_type', 'unknown') for log in logs))
        
        # Severity distribution
        severity_counts = defaultdict(int)
        severity_weights_sum = 0
        
        for log in logs:
            severity = log.severity_text.value if log.severity_text else "UNKNOWN"
            severity_counts[severity] += 1
            
            severity_num = log.severity_number or SeverityNumber.INFO
            severity_weights_sum += self.severity_weights.get(severity_num, 0)
        
        # Source distribution
        source_counts = Counter()
        for log in logs:
            source = log.attributes.get('source', 'unknown')
            source_counts[source] += 1
        
        # Category distribution
        category_counts = Counter()
        for log in logs:
            category = log.attributes.get('log.category', 'unknown')
            category_counts[category] += 1
        
        # Anomaly analysis
        anomaly_scores = []
        high_anomaly_logs = 0
        
        for log in logs:
            anomaly_score = log.attributes.get('anomaly_score')
            if anomaly_score is not None:
                try:
                    score = float(anomaly_score)
                    anomaly_scores.append(score)
                    if score > 70:
                        high_anomaly_logs += 1
                except (ValueError, TypeError):
                    pass
        
        # Time analysis
        timestamps = []
        for log in logs:
            try:
                if log.timestamp.endswith('Z'):
                    ts = datetime.fromisoformat(log.timestamp[:-1] + '+00:00')
                else:
                    ts = datetime.fromisoformat(log.timestamp)
                timestamps.append(ts)
            except ValueError:
                continue
        
        time_analysis = {}
        if timestamps:
            timestamps.sort()
            time_analysis = {
                "start_time": timestamps[0].isoformat(),
                "end_time": timestamps[-1].isoformat(),
                "duration_minutes": (timestamps[-1] - timestamps[0]).total_seconds() / 60,
                "avg_interval_seconds": (timestamps[-1] - timestamps[0]).total_seconds() / max(len(timestamps) - 1, 1)
            }
        
        # Performance metrics analysis
        performance_metrics = self._analyze_performance_metrics(logs)
        
        # Top error patterns
        error_patterns = self._extract_error_patterns(logs)
        
        return {
            "summary": {
                "total_logs": total_logs,
                "unique_sources": unique_sources,
                "unique_log_types": unique_log_types,
                "high_anomaly_logs": high_anomaly_logs,
                "severity_weight_score": severity_weights_sum
            },
            "severity_distribution": dict(severity_counts),
            "top_sources": dict(source_counts.most_common(10)),
            "top_categories": dict(category_counts.most_common(10)),
            "anomaly_analysis": {
                "logs_with_anomaly_score": len(anomaly_scores),
                "avg_anomaly_score": statistics.mean(anomaly_scores) if anomaly_scores else 0,
                "max_anomaly_score": max(anomaly_scores) if anomaly_scores else 0,
                "min_anomaly_score": min(anomaly_scores) if anomaly_scores else 0,
                "high_anomaly_count": high_anomaly_logs,
                "high_anomaly_percentage": (high_anomaly_logs / total_logs * 100) if total_logs > 0 else 0
            },
            "time_analysis": time_analysis,
            "performance_metrics": performance_metrics,
            "error_patterns": error_patterns,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def aggregate_timeline(self, logs: List[LogRecordObject], minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Generate timeline aggregation of logs over specified time period
        """
        if not logs:
            return []
        
        # Calculate time window
        now = datetime.now(timezone.utc)
        end_time = now
        start_time = end_time - timedelta(minutes=minutes)
        
        # Create time buckets (1-minute buckets)
        bucket_size = timedelta(minutes=1)
        buckets = []
        current_time = start_time
        
        while current_time < end_time:
            buckets.append({
                "timestamp": current_time.isoformat(),
                "count": 0,
                "severity_counts": defaultdict(int),
                "source_counts": defaultdict(int),
                "anomaly_scores": [],
                "high_anomaly_count": 0
            })
            current_time += bucket_size
        
        # Assign logs to buckets
        for log in logs:
            try:
                if log.timestamp.endswith('Z'):
                    log_time = datetime.fromisoformat(log.timestamp[:-1] + '+00:00')
                else:
                    log_time = datetime.fromisoformat(log.timestamp)
                
                # Find the right bucket
                for bucket in buckets:
                    bucket_time = datetime.fromisoformat(bucket['timestamp'])
                    if bucket_time <= log_time < bucket_time + bucket_size:
                        bucket["count"] += 1
                        
                        severity = log.severity_text.value if log.severity_text else "UNKNOWN"
                        bucket["severity_counts"][severity] += 1
                        
                        source = log.attributes.get('source', 'unknown')
                        bucket["source_counts"][source] += 1
                        
                        anomaly_score = log.attributes.get('anomaly_score')
                        if anomaly_score is not None:
                            try:
                                score = float(anomaly_score)
                                bucket["anomaly_scores"].append(score)
                                if score > 70:
                                    bucket["high_anomaly_count"] += 1
                            except (ValueError, TypeError):
                                pass
                        break
                        
            except ValueError:
                continue
        
        # Calculate bucket statistics
        for bucket in buckets:
            if bucket["anomaly_scores"]:
                bucket["avg_anomaly_score"] = statistics.mean(bucket["anomaly_scores"])
                bucket["max_anomaly_score"] = max(bucket["anomaly_scores"])
            else:
                bucket["avg_anomaly_score"] = 0
                bucket["max_anomaly_score"] = 0
            
            # Remove raw scores to keep response size manageable
            del bucket["anomaly_scores"]
            
            # Convert defaultdicts to regular dicts
            bucket["severity_counts"] = dict(bucket["severity_counts"])
            bucket["source_counts"] = dict(bucket["source_counts"])
        
        return buckets
    
    def aggregate_by_source(self, logs: List[LogRecordObject]) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate logs by source
        """
        source_stats = defaultdict(list)
        
        for log in logs:
            source = log.attributes.get('source', 'unknown')
            source_stats[source].append(log)
        
        results = {}
        for source, source_logs in source_stats.items():
            results[source] = {
                "count": len(source_logs),
                "severity_distribution": self._get_severity_distribution(source_logs),
                "avg_anomaly_score": self._get_avg_anomaly_score(source_logs),
                "latest_timestamp": self._get_latest_timestamp(source_logs),
                "top_log_types": self._get_top_log_types(source_logs),
                "high_anomaly_count": len([log for log in source_logs if log.has_high_anomaly_score()])
            }
        
        return results
    
    def aggregate_anomaly_patterns(self, logs: List[LogRecordObject], threshold: float = 70.0) -> Dict[str, Any]:
        """
        Analyze anomaly patterns across logs
        """
        high_anomaly_logs = [log for log in logs if log.has_high_anomaly_score(threshold)]
        
        if not high_anomaly_logs:
            return {"message": "No high anomaly logs found"}
        
        # Analyze by source
        anomaly_by_source = defaultdict(int)
        # Analyze by log type
        anomaly_by_type = defaultdict(int)
        # Analyze by category
        anomaly_by_category = defaultdict(int)
        
        for log in high_anomaly_logs:
            source = log.attributes.get('source', 'unknown')
            log_type = log.attributes.get('original_log_type', 'unknown')
            category = log.attributes.get('log.category', 'unknown')
            
            anomaly_by_source[source] += 1
            anomaly_by_type[log_type] += 1
            anomaly_by_category[category] += 1
        
        # Time pattern analysis
        anomaly_timestamps = []
        for log in high_anomaly_logs:
            try:
                if log.timestamp.endswith('Z'):
                    ts = datetime.fromisoformat(log.timestamp[:-1] + '+00:00')
                else:
                    ts = datetime.fromisoformat(log.timestamp)
                anomaly_timestamps.append(ts)
            except ValueError:
                continue
        
        time_pattern = {}
        if anomaly_timestamps:
            # Hour distribution (UTC)
            hour_distribution = defaultdict(int)
            for ts in anomaly_timestamps:
                hour_distribution[ts.hour] += 1
            
            time_pattern = {
                "peak_hour": max(hour_distribution, key=hour_distribution.get),
                "hour_distribution": dict(hour_distribution),
                "duration_minutes": (max(anomaly_timestamps) - min(anomaly_timestamps)).total_seconds() / 60 if len(anomaly_timestamps) > 1 else 0
            }
        
        # Anomaly score distribution
        scores = []
        for log in high_anomaly_logs:
            anomaly_score = log.attributes.get('anomaly_score')
            if anomaly_score is not None:
                try:
                    scores.append(float(anomaly_score))
                except (ValueError, TypeError):
                    pass
        
        return {
            "total_high_anomaly_logs": len(high_anomaly_logs),
            "threshold_used": threshold,
            "anomaly_by_source": dict(anomaly_by_source.most_common(10)),
            "anomaly_by_type": dict(anomaly_by_type.most_common(10)),
            "anomaly_by_category": dict(anomaly_by_category.most_common(10)),
            "time_pattern": time_pattern,
            "score_distribution": {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "avg": statistics.mean(scores) if scores else 0,
                "median": statistics.median(scores) if scores else 0
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _analyze_performance_metrics(self, logs: List[LogRecordObject]) -> Dict[str, Any]:
        """Analyze performance metrics from logs"""
        metrics = {}
        
        # Common performance fields
        performance_fields = [
            "performance.cpu_usage_percent",
            "performance.memory_used_gb",
            "performance.response_time",
            "performance.processing_time_ms",
            "performance.duration_ms",
            "performance.latency_ms"
        ]
        
        for field in performance_fields:
            values = []
            for log in logs:
                value = self._get_nested_attribute(log, field)
                if value is not None and isinstance(value, (int, float)):
                    values.append(value)
            
            if values:
                field_name = field.replace("performance.", "")
                metrics[field_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "median": statistics.median(values)
                }
        
        return metrics
    
    def _extract_error_patterns(self, logs: List[LogRecordObject]) -> Dict[str, Any]:
        """Extract common error patterns from logs"""
        error_logs = [log for log in logs if log.severity_text in [Severity.ERROR, Severity.FATAL]]
        
        if not error_logs:
            return {"message": "No error logs found"}
        
        # Extract error types from body
        error_types = Counter()
        error_sources = Counter()
        
        for log in error_logs:
            body = log.body if isinstance(log.body, str) else str(log.body)
            
            # Common error patterns
            error_patterns = [
                "connection timeout", "database error", "authentication failed",
                "permission denied", "file not found", "server error",
                "network error", "memory error", "disk full", "cpu overload"
            ]
            
            for pattern in error_patterns:
                if pattern.lower() in body.lower():
                    error_types[pattern] += 1
                    break
            
            # Track sources of errors
            source = log.attributes.get('source', 'unknown')
            error_sources[source] += 1
        
        return {
            "total_error_logs": len(error_logs),
            "error_patterns": dict(error_types.most_common(10)),
            "error_by_source": dict(error_sources.most_common(5))
        }
    
    def _get_severity_distribution(self, logs: List[LogRecordObject]) -> Dict[str, int]:
        """Get severity distribution for a set of logs"""
        distribution = Counter()
        for log in logs:
            severity = log.severity_text.value if log.severity_text else "UNKNOWN"
            distribution[severity] += 1
        return dict(distribution)
    
    def _get_avg_anomaly_score(self, logs: List[LogRecordObject]) -> float:
        """Calculate average anomaly score for logs"""
        scores = []
        for log in logs:
            anomaly_score = log.attributes.get('anomaly_score')
            if anomaly_score is not None:
                try:
                    scores.append(float(anomaly_score))
                except (ValueError, TypeError):
                    pass
        return statistics.mean(scores) if scores else 0
    
    def _get_latest_timestamp(self, logs: List[LogRecordObject]) -> Optional[str]:
        """Get latest timestamp from logs"""
        latest_time = None
        for log in logs:
            try:
                if log.timestamp.endswith('Z'):
                    log_time = datetime.fromisoformat(log.timestamp[:-1] + '+00:00')
                else:
                    log_time = datetime.fromisoformat(log.timestamp)
                
                if latest_time is None or log_time > latest_time:
                    latest_time = log_time
            except ValueError:
                continue
        
        return latest_time.isoformat() if latest_time else None
    
    def _get_top_log_types(self, logs: List[LogRecordObject], limit: int = 5) -> Dict[str, int]:
        """Get top log types from logs"""
        log_type_counts = Counter()
        for log in logs:
            log_type = log.attributes.get('original_log_type', 'unknown')
            log_type_counts[log_type] += 1
        return dict(log_type_counts.most_common(limit))
    
    def _get_nested_attribute(self, log: LogRecordObject, attribute_path: str) -> Any:
        """Get nested attribute from log using dot notation"""
        parts = attribute_path.split('.')
        value = log.attributes
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
