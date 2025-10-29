#!/usr/bin/env python3
"""
Banking API Gateway Mock
Routes requests to microservices and aggregates responses
"""

import json
import time
import random
import logging
import requests
from flask import Flask, jsonify, request, Response
from datetime import datetime
import threading
import queue
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class APIGateway:
    """Mock API Gateway for banking microservices"""
    
    def __init__(self):
        self.config = self._load_config()
        self.services = {
            'transaction-service': {
                'host': 'transaction-service',
                'port': 8081,
                'health': '/health',
                'metrics': '/metrics',
                'events': '/transactions/events'
            },
            'auth-service': {
                'host': 'auth-service',
                'port': 8082,
                'health': '/health',
                'metrics': '/metrics',
                'events': '/auth/events'
            },
            'monitoring-service': {
                'host': 'monitoring-service',
                'port': 8083,
                'health': '/health',
                'metrics': '/metrics',
                'events': '/metrics/events'
            }
        }
        
        # Gateway metrics
        self.metrics = {
            'requests_processed': 0,
            'response_time_sum': 0,
            'error_count': 0,
            'uptime_start': datetime.now()
        }
        
        # Request queue for monitoring
        self.request_queue = queue.Queue()
        
    def _load_config(self):
        """Load gateway configuration"""
        try:
            with open('/app/config/anomaly_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            return {}
    
    def _make_service_request(self, service_name, endpoint, method='GET', data=None):
        """Make request to a microservice"""
        service_config = self.services.get(service_name)
        if not service_config:
            return None, f"Service {service_name} not found"
        
        url = f"http://{service_config['host']}:{service_config['port']}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, timeout=5)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=5)
            else:
                return None, f"Unsupported method: {method}"
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Update metrics
            self.metrics['requests_processed'] += 1
            self.metrics['response_time_sum'] += response_time
            
            if response.status_code >= 400:
                self.metrics['error_count'] += 1
            
            # Log request for monitoring
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'gateway_request': f"{method} {endpoint}",
                'service': service_name,
                'service_url': url,
                'method': method,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'success': response.status_code < 400
            }
            
            self.request_queue.put(log_entry)
            
            return response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text, None
            
        except requests.exceptions.RequestException as e:
            self.metrics['error_count'] += 1
            logger.error(f"Error requesting {service_name}{endpoint}: {e}")
            return None, str(e)
    
    def get_aggregated_events(self):
        """Aggregate events from all services"""
        all_events = []
        
        for service_name in self.services.keys():
            events, error = self._make_service_request(service_name, self.services[service_name]['events'])
            
            if events and 'events' in events:
                for event in events['events']:
                    event['gateway_timestamp'] = datetime.now().isoformat()
                    event['gateway_service'] = service_name
                    all_events.append(event)
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x.get('timestamp', ''))
        
        return {
            'events': all_events[-100:],  # Return last 100 events
            'total_count': len(all_events),
            'services_count': len(self.services)
        }
    
    def get_aggregated_metrics(self):
        """Aggregate metrics from all services"""
        aggregated = {
            'gateway_metrics': {
                'requests_processed': self.metrics['requests_processed'],
                'average_response_time_ms': round(
                    self.metrics['response_time_sum'] / max(1, self.metrics['requests_processed']), 2
                ),
                'error_rate_percent': round(
                    (self.metrics['error_count'] / max(1, self.metrics['requests_processed'])) * 100, 2
                ),
                'uptime_seconds': (datetime.now() - self.metrics['uptime_start']).total_seconds()
            },
            'services': {}
        }
        
        for service_name in self.services.keys():
            metrics, error = self._make_service_request(service_name, self.services[service_name]['metrics'])
            
            if metrics:
                aggregated['services'][service_name] = metrics
            else:
                aggregated['services'][service_name] = {
                    'error': error,
                    'status': 'unavailable'
                }
        
        return aggregated
    
    def get_system_health(self):
        """Get overall system health"""
        health_status = {
            'overall_status': 'healthy',
            'gateway': {
                'status': 'healthy',
                'uptime_seconds': (datetime.now() - self.metrics['uptime_start']).total_seconds()
            },
            'services': {},
            'issues': []
        }
        
        unhealthy_count = 0
        
        for service_name in self.services.keys():
            health, error = self._make_service_request(service_name, self.services[service_name]['health'])
            
            if health and health.get('status') == 'healthy':
                health_status['services'][service_name] = {
                    'status': 'healthy',
                    'uptime_seconds': health.get('uptime_seconds', 0)
                }
            else:
                health_status['services'][service_name] = {
                    'status': 'unhealthy',
                    'error': error or 'Health check failed'
                }
                health_status['issues'].append(f"{service_name} is unhealthy")
                unhealthy_count += 1
        
        # Determine overall status
        if unhealthy_count == 0:
            health_status['overall_status'] = 'healthy'
        elif unhealthy_count == 1:
            health_status['overall_status'] = 'degraded'
        else:
            health_status['overall_status'] = 'critical'
        
        return health_status

# Initialize gateway
gateway = APIGateway()

@app.route('/health', methods=['GET'])
def health_check():
    """Gateway health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'api-gateway',
        'uptime_seconds': (datetime.now() - gateway.metrics['uptime_start']).total_seconds(),
        'metrics': gateway.metrics
    })

@app.route('/services/<service_name>/health', methods=['GET'])
def service_health(service_name):
    """Get health of specific service"""
    health, error = gateway._make_service_request(service_name, '/health')
    
    if health:
        return jsonify(health)
    else:
        return jsonify({'error': error}), 503

@app.route('/services/<service_name>/metrics', methods=['GET'])
def service_metrics(service_name):
    """Get metrics of specific service"""
    metrics, error = gateway._make_service_request(service_name, '/metrics')
    
    if metrics:
        return jsonify(metrics)
    else:
        return jsonify({'error': error}), 503

@app.route('/events', methods=['GET'])
def aggregated_events():
    """Get aggregated events from all services"""
    events = gateway.get_aggregated_events()
    return jsonify(events)

@app.route('/metrics', methods=['GET'])
def aggregated_metrics():
    """Get aggregated metrics from all services"""
    metrics = gateway.get_aggregated_metrics()
    return jsonify(metrics)

@app.route('/system/health', methods=['GET'])
def system_health():
    """Get overall system health"""
    health = gateway.get_system_health()
    return jsonify(health)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Get comprehensive dashboard data"""
    dashboard_data = {
        'timestamp': datetime.now().isoformat(),
        'system_health': gateway.get_system_health(),
        'aggregated_metrics': gateway.get_aggregated_metrics(),
        'recent_events': gateway.get_aggregated_events(),
        'gateway_metrics': gateway.metrics
    }
    
    return jsonify(dashboard_data)

@app.route('/config', methods=['GET'])
def get_config():
    """Get gateway configuration"""
    return jsonify({
        'services': list(gateway.services.keys()),
        'config': gateway.config
    })

@app.route('/services/<service_name>/config', methods=['POST'])
def update_service_config(service_name):
    """Update configuration for a specific service"""
    try:
        new_config = request.json
        response, error = gateway._make_service_request(service_name, '/config', 'POST', new_config)
        
        if response:
            return jsonify(response)
        else:
            return jsonify({'error': error}), 503
            
    except Exception as e:
        logger.error(f"Error updating config for {service_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/services/<service_name>/events', methods=['GET'])
def service_events(service_name):
    """Get events from specific service"""
    events, error = gateway._make_service_request(service_name, gateway.services[service_name]['events'])
    
    if events:
        return jsonify(events)
    else:
        return jsonify({'error': error}), 503

# Proxy endpoints for direct service access
@app.route('/proxy/<service_name>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_request(service_name, endpoint):
    """Proxy requests to microservices"""
    method = request.method
    
    if method == 'GET':
        response, error = gateway._make_service_request(service_name, f'/{endpoint}', method)
    elif method in ['POST', 'PUT', 'DELETE']:
        data = request.get_json() if request.is_json else request.form.to_dict()
        response, error = gateway._make_service_request(service_name, f'/{endpoint}', method, data)
    else:
        return jsonify({'error': 'Method not allowed'}), 405
    
    if response:
        return jsonify(response)
    else:
        return jsonify({'error': error}), 503

@app.route('/gateway/logs', methods=['GET'])
def gateway_logs():
    """Get gateway request logs"""
    logs = []
    while not gateway.request_queue.empty() and len(logs) < 50:
        try:
            log_entry = gateway.request_queue.get_nowait()
            logs.append(log_entry)
        except queue.Empty:
            break
    
    return jsonify({
        'logs': logs,
        'count': len(logs)
    })

if __name__ == '__main__':
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down API Gateway...")
