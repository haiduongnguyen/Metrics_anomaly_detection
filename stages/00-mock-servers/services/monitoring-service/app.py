#!/usr/bin/env python3
"""
Banking Monitoring Service Mock
Generates realistic system monitoring events with configurable anomaly rates
"""

import json
import time
import random
import logging
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import threading
import queue
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class MonitoringService:
    """Mock monitoring service for banking anomaly detection"""
    
    def __init__(self):
        self.event_queue = queue.Queue()
        self.running = False
        self.config = self._load_config()
        
        # Service metrics
        self.metrics = {
            'metrics_generated': 0,
            'anomalies_detected': 0,
            'alerts_generated': 0,
            'uptime_start': datetime.now()
        }
        
        # System state tracking
        self.system_state = {
            'cpu_utilization': 45.0,
            'memory_utilization': 60.0,
            'disk_usage': 30.0,
            'network_io': 25.0,
            'response_time_p95': 200.0
        }
        
        # Active anomalies tracking
        self.active_anomalies = {}
        
    def _load_config(self):
        """Load service configuration"""
        try:
            with open('/app/config/anomaly_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            return {
                'anomaly_settings': {
                    'monitoring_service': {
                        'anomaly_rate': 0.03,
                        'high_cpu_rate': 0.01,
                        'memory_leak_rate': 0.008,
                        'network_timeout_rate': 0.007,
                        'disk_space_rate': 0.005
                    }
                }
            }
    
    def generate_monitoring_event(self):
        """Generate a single monitoring event"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Determine if this should be an anomaly
        anomaly_rate = self.config['anomaly_settings']['monitoring_service'].get('anomaly_rate', 0.03)
        is_anomaly = random.random() < anomaly_rate
        
        # Select service and metric
        services = ['transaction-service', 'auth-service', 'api-gateway', 'monitoring-service']
        service = random.choice(services)
        
        # Select metric type
        metrics = ['cpu_utilization', 'memory_utilization', 'disk_usage', 'network_io', 'response_time_p95']
        metric_name = random.choice(metrics)
        
        # Generate metric value
        if is_anomaly:
            metric_value, anomaly_type = self._generate_anomaly_metric(metric_name)
        else:
            metric_value = self._generate_normal_metric(metric_name)
            anomaly_type = None
        
        # Determine alert status
        alert_threshold = 80.0
        status = "alert" if metric_value > alert_threshold else "normal"
        
        monitoring_event = {
            'event_id': event_id,
            'timestamp': timestamp,
            'service': service,
            'metric_name': metric_name,
            'metric_value': metric_value,
            'unit': 'percent',
            'instance_id': f"i-{random.randint(10000000, 99999999)}",
            'environment': 'production',
            'alert_threshold': alert_threshold,
            'status': status,
            'anomaly_type': anomaly_type
        }
        
        # Update metrics
        self.metrics['metrics_generated'] += 1
        if is_anomaly:
            self.metrics['anomalies_detected'] += 1
        if status == "alert":
            self.metrics['alerts_generated'] += 1
        
        # Update system state
        self.system_state[metric_name] = metric_value
        
        return monitoring_event
    
    def _generate_normal_metric(self, metric_name):
        """Generate normal metric value"""
        base_values = {
            'cpu_utilization': 45.0,
            'memory_utilization': 60.0,
            'disk_usage': 30.0,
            'network_io': 25.0,
            'response_time_p95': 200.0
        }
        
        base_value = base_values.get(metric_name, 50.0)
        
        # Add some variance but keep within normal range
        variance = base_value * 0.2
        value = max(10, min(75, random.gauss(base_value, variance)))
        
        return round(value, 2)
    
    def _generate_anomaly_metric(self, metric_name):
        """Generate anomalous metric value"""
        service_config = self.config['anomaly_settings']['monitoring_service']
        
        # Determine anomaly type based on configured rates
        total_rate = service_config['anomaly_rate']
        rand_val = random.random()
        
        if rand_val < service_config['high_cpu_rate'] / total_rate and metric_name == 'cpu_utilization':
            return random.uniform(85, 95), 'high_cpu'
        elif rand_val < (service_config['high_cpu_rate'] + service_config['memory_leak_rate']) / total_rate and metric_name == 'memory_utilization':
            return random.uniform(80, 90), 'memory_leak'
        elif rand_val < (service_config['high_cpu_rate'] + service_config['memory_leak_rate'] + service_config['network_timeout_rate']) / total_rate and metric_name == 'network_io':
            return random.uniform(85, 98), 'network_timeout'
        elif rand_val < (service_config['high_cpu_rate'] + service_config['memory_leak_rate'] + service_config['network_timeout_rate'] + service_config['disk_space_rate']) / total_rate and metric_name == 'disk_usage':
            return random.uniform(92, 98), 'disk_space'
        else:
            # Generic high value anomaly
            return random.uniform(82, 96), 'metric_spike'
    
    def generate_system_health_event(self):
        """Generate a comprehensive system health event"""
        timestamp = datetime.now().isoformat()
        
        # Calculate overall system health
        health_score = 100.0
        
        # Deduct points for each metric above threshold
        for metric, value in self.system_state.items():
            if value > 80:
                health_score -= (value - 80) * 2
        
        health_score = max(0, health_score)
        
        health_event = {
            'event_id': str(uuid.uuid4()),
            'timestamp': timestamp,
            'event_type': 'system_health',
            'service': 'monitoring-service',
            'health_score': round(health_score, 2),
            'overall_status': 'healthy' if health_score > 80 else 'degraded' if health_score > 50 else 'critical',
            'system_metrics': self.system_state.copy(),
            'active_anomalies': len(self.active_anomalies),
            'alerts_count': self.metrics['alerts_generated']
        }
        
        return health_event
    
    def start_event_generation(self):
        """Start continuous event generation in background thread"""
        self.running = True
        
        def generate_events():
            while self.running:
                try:
                    # Generate monitoring event
                    monitoring_event = self.generate_monitoring_event()
                    self.event_queue.put(monitoring_event)
                    
                    # Generate system health event every 30 seconds
                    if random.random() < 0.03:  # ~3% chance = roughly every 30 seconds
                        health_event = self.generate_system_health_event()
                        self.event_queue.put(health_event)
                    
                    # Simulate monitoring interval
                    time.sleep(random.uniform(0.5, 2.0))
                    
                except Exception as e:
                    logger.error(f"Error generating monitoring event: {e}")
                    time.sleep(1)
        
        # Start background thread
        self.generation_thread = threading.Thread(target=generate_events, daemon=True)
        self.generation_thread.start()
        logger.info("Monitoring event generation started")
    
    def stop_event_generation(self):
        """Stop event generation"""
        self.running = False
        logger.info("Monitoring event generation stopped")

# Initialize service
monitoring_service = MonitoringService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - monitoring_service.metrics['uptime_start']).total_seconds()
    
    return jsonify({
        'status': 'healthy',
        'service': 'monitoring-service',
        'uptime_seconds': uptime,
        'metrics': monitoring_service.metrics
    })

@app.route('/metrics', methods=['POST'])
def create_metric():
    """Create a new metric (for testing)"""
    try:
        monitoring_event = monitoring_service.generate_monitoring_event()
        return jsonify(monitoring_event), 201
    except Exception as e:
        logger.error(f"Error creating metric: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/metrics/events', methods=['GET'])
def get_events():
    """Get generated events from queue"""
    events = []
    while not monitoring_service.event_queue.empty() and len(events) < 100:
        try:
            event = monitoring_service.event_queue.get_nowait()
            events.append(event)
        except queue.Empty:
            break
    
    return jsonify({
        'events': events,
        'count': len(events)
    })

@app.route('/system/health', methods=['GET'])
def get_system_health():
    """Get current system health status"""
    health_event = monitoring_service.generate_system_health_event()
    return jsonify(health_event)

@app.route('/system/metrics', methods=['GET'])
def get_system_metrics():
    """Get current system metrics"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'system_state': monitoring_service.system_state,
        'active_anomalies': monitoring_service.active_anomalies
    })

@app.route('/service/metrics', methods=['GET'])
def get_service_metrics():
    """Get service metrics"""
    uptime = (datetime.now() - monitoring_service.metrics['uptime_start']).total_seconds()
    
    # Calculate anomaly rate
    if monitoring_service.metrics['metrics_generated'] > 0:
        anomaly_rate = (monitoring_service.metrics['anomalies_detected'] / 
                        monitoring_service.metrics['metrics_generated']) * 100
        alert_rate = (monitoring_service.metrics['alerts_generated'] / 
                     monitoring_service.metrics['metrics_generated']) * 100
    else:
        anomaly_rate = 0
        alert_rate = 0
    
    return jsonify({
        'service': 'monitoring-service',
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'metrics_generated': monitoring_service.metrics['metrics_generated'],
            'anomalies_detected': monitoring_service.metrics['anomalies_detected'],
            'alerts_generated': monitoring_service.metrics['alerts_generated'],
            'anomaly_rate_percent': round(anomaly_rate, 2),
            'alert_rate_percent': round(alert_rate, 2),
            'uptime_seconds': uptime,
            'queue_size': monitoring_service.event_queue.qsize()
        }
    })

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'anomaly_rate': monitoring_service.config['anomaly_settings']['monitoring_service'].get('anomaly_rate', 0.03),
        'service': 'monitoring-service'
    })

@app.route('/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.json
        if 'anomaly_rate' in new_config:
            monitoring_service.config['anomaly_settings']['monitoring_service']['anomaly_rate'] = new_config['anomaly_rate']
            logger.info(f"Updated anomaly rate to {new_config['anomaly_rate']}")
        
        return jsonify({'status': 'updated', 'config': new_config})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get dashboard data with all metrics"""
    dashboard_data = {
        'timestamp': datetime.now().isoformat(),
        'system_health': monitoring_service.generate_system_health_event(),
        'service_metrics': monitoring_service.metrics,
        'system_state': monitoring_service.system_state,
        'recent_events': []
    }
    
    # Get recent events
    while not monitoring_service.event_queue.empty() and len(dashboard_data['recent_events']) < 10:
        try:
            event = monitoring_service.event_queue.get_nowait()
            dashboard_data['recent_events'].append(event)
        except queue.Empty:
            break
    
    return jsonify(dashboard_data)

if __name__ == '__main__':
    # Start event generation
    monitoring_service.start_event_generation()
    
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=8083, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring service...")
        monitoring_service.stop_event_generation()
