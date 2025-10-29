#!/usr/bin/env python3
"""
Banking Authentication Service Mock
Generates realistic authentication events with configurable anomaly rates
"""

import json
import time
import random
import logging
from flask import Flask, jsonify, request
from datetime import datetime
import threading
import queue
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class AuthService:
    """Mock authentication service for banking anomaly detection"""
    
    def __init__(self):
        self.event_queue = queue.Queue()
        self.running = False
        self.config = self._load_config()
        
        # Service metrics
        self.metrics = {
            'auth_attempts': 0,
            'successful_auths': 0,
            'failed_auths': 0,
            'anomalies_detected': 0,
            'average_response_time': 0,
            'uptime_start': datetime.now()
        }
        
        # Failed login tracking for brute force detection
        self.failed_attempts = {}
        
    def _load_config(self):
        """Load service configuration"""
        try:
            with open('/app/config/anomaly_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            return {
                'anomaly_settings': {
                    'auth_service': {
                        'anomaly_rate': 0.025,
                        'failed_login_rate': 0.015,
                        'brute_force_rate': 0.005
                    }
                },
                'banking_metrics': {
                    'response_times': {
                        'normal_mean_ms': 150,
                        'normal_std_ms': 50
                    }
                }
            }
    
    def generate_auth_event(self):
        """Generate a single authentication event"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Determine if this should be an anomaly
        anomaly_rate = self.config['anomaly_settings']['auth_service'].get('anomaly_rate', 0.025)
        is_anomaly = random.random() < anomaly_rate
        
        # Generate customer and session info
        customer_id = f"CUST_{random.randint(100000, 999999)}"
        username = f"user_{customer_id.split('_')[1]}"
        
        # Determine auth result
        if is_anomaly:
            auth_result = self._generate_anomaly_auth_result(customer_id)
        else:
            auth_result = "success"
        
        # Generate response time
        rt_metrics = self.config['banking_metrics']['response_times']
        response_time = max(
            50,
            int(random.gauss(rt_metrics['normal_mean_ms'], rt_metrics['normal_std_ms']))
        )
        
        if is_anomaly:
            response_time = int(response_time * random.uniform(1.5, 2.0))
        
        # Generate location and device info
        location = {
            'country': random.choice(['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'SG', 'IN', 'BR']),
            'city': f"City_{random.randint(1, 100)}",
            'ip_address': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'latitude': random.uniform(-90, 90),
            'longitude': random.uniform(-180, 180)
        }
        
        device_info = {
            'device_id': f"DEV_{random.randint(100000, 999999)}",
            'type': random.choice(['mobile', 'desktop', 'tablet']),
            'os': random.choice(['iOS', 'Android', 'Windows', 'macOS', 'Linux']),
            'browser': random.choice(['Chrome', 'Safari', 'Firefox', 'Edge', 'Opera'])
        }
        
        # Determine anomaly type
        anomaly_type = None
        failure_reason = None
        
        if is_anomaly:
            anomaly_type = self._determine_anomaly_type(auth_result, customer_id)
            if auth_result == "failure":
                failure_reason = random.choice(['invalid_credentials', 'account_locked', 'suspicious_activity', 'rate_limit_exceeded'])
        
        auth_event = {
            'event_id': event_id,
            'timestamp': timestamp,
            'service': 'auth-service',
            'customer_id': customer_id,
            'username': username,
            'ip_address': location['ip_address'],
            'user_agent': f"{device_info['os']}/{device_info['browser']}",
            'device_fingerprint': device_info['device_id'],
            'location': location,
            'auth_method': random.choice(['password', '2fa', 'biometric', 'sso']),
            'result': auth_result,
            'failure_reason': failure_reason,
            'response_time_ms': response_time,
            'anomaly_type': anomaly_type
        }
        
        # Update metrics
        self.metrics['auth_attempts'] += 1
        if auth_result == "success":
            self.metrics['successful_auths'] += 1
        else:
            self.metrics['failed_auths'] += 1
        
        if is_anomaly:
            self.metrics['anomalies_detected'] += 1
        
        return auth_event
    
    def _generate_anomaly_auth_result(self, customer_id):
        """Generate authentication result for anomaly scenarios"""
        service_config = self.config['anomaly_settings']['auth_service']
        rand_val = random.random()
        
        # Track failed attempts for brute force detection
        if customer_id not in self.failed_attempts:
            self.failed_attempts[customer_id] = {'count': 0, 'last_attempt': datetime.now()}
        
        # Check for brute force pattern
        if (self.failed_attempts[customer_id]['count'] >= 5 and 
            (datetime.now() - self.failed_attempts[customer_id]['last_attempt']).total_seconds() < 300):
            return "failure"  # Brute force detected
        
        # Determine result based on anomaly type probabilities
        failed_rate = service_config.get('failed_login_rate', 0.015) / service_config.get('anomaly_rate', 0.025)
        
        if rand_val < failed_rate:
            self.failed_attempts[customer_id]['count'] += 1
            self.failed_attempts[customer_id]['last_attempt'] = datetime.now()
            return "failure"
        else:
            # Reset failed attempts on success
            if self.failed_attempts[customer_id]['count'] > 0:
                self.failed_attempts[customer_id]['count'] = 0
            return "success"
    
    def _determine_anomaly_type(self, auth_result, customer_id):
        """Determine the specific type of anomaly"""
        if auth_result == "failure":
            # Check if it's brute force
            if (self.failed_attempts.get(customer_id, {}).get('count', 0) >= 5):
                return "brute_force"
            else:
                return "failed_login"
        else:
            # Successful but anomalous
            rand_val = random.random()
            if rand_val < 0.3:
                return "unusual_location"
            elif rand_val < 0.6:
                return "new_device"
            else:
                return "impossible_travel"
    
    def start_event_generation(self):
        """Start continuous event generation in background thread"""
        self.running = True
        
        def generate_events():
            while self.running:
                try:
                    # Generate auth event
                    auth_event = self.generate_auth_event()
                    
                    # Add to queue for processing
                    self.event_queue.put(auth_event)
                    
                    # Simulate processing time
                    time.sleep(random.uniform(0.01, 0.05))
                    
                except Exception as e:
                    logger.error(f"Error generating auth event: {e}")
                    time.sleep(1)
        
        # Start background thread
        self.generation_thread = threading.Thread(target=generate_events, daemon=True)
        self.generation_thread.start()
        logger.info("Authentication event generation started")
    
    def stop_event_generation(self):
        """Stop event generation"""
        self.running = False
        logger.info("Authentication event generation stopped")

# Initialize service
auth_service = AuthService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - auth_service.metrics['uptime_start']).total_seconds()
    
    return jsonify({
        'status': 'healthy',
        'service': 'auth-service',
        'uptime_seconds': uptime,
        'metrics': auth_service.metrics
    })

@app.route('/auth', methods=['POST'])
def authenticate():
    """Perform authentication (for testing)"""
    try:
        auth_event = auth_service.generate_auth_event()
        return jsonify(auth_event), 201
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/events', methods=['GET'])
def get_events():
    """Get generated events from queue"""
    events = []
    while not auth_service.event_queue.empty() and len(events) < 100:
        try:
            event = auth_service.event_queue.get_nowait()
            events.append(event)
        except queue.Empty:
            break
    
    return jsonify({
        'events': events,
        'count': len(events)
    })

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    uptime = (datetime.now() - auth_service.metrics['uptime_start']).total_seconds()
    
    # Calculate success rate
    if auth_service.metrics['auth_attempts'] > 0:
        success_rate = (auth_service.metrics['successful_auths'] / 
                       auth_service.metrics['auth_attempts']) * 100
        anomaly_rate = (auth_service.metrics['anomalies_detected'] / 
                        auth_service.metrics['auth_attempts']) * 100
    else:
        success_rate = 0
        anomaly_rate = 0
    
    return jsonify({
        'service': 'auth-service',
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'auth_attempts': auth_service.metrics['auth_attempts'],
            'successful_auths': auth_service.metrics['successful_auths'],
            'failed_auths': auth_service.metrics['failed_auths'],
            'anomalies_detected': auth_service.metrics['anomalies_detected'],
            'success_rate_percent': round(success_rate, 2),
            'anomaly_rate_percent': round(anomaly_rate, 2),
            'average_response_time_ms': auth_service.metrics['average_response_time'],
            'uptime_seconds': uptime,
            'queue_size': auth_service.event_queue.qsize(),
            'tracked_failed_attempts': len(auth_service.failed_attempts)
        }
    })

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'anomaly_rate': auth_service.config['anomaly_settings']['auth_service'].get('anomaly_rate', 0.025),
        'service': 'auth-service'
    })

@app.route('/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.json
        if 'anomaly_rate' in new_config:
            auth_service.config['anomaly_settings']['auth_service']['anomaly_rate'] = new_config['anomaly_rate']
            logger.info(f"Updated anomaly rate to {new_config['anomaly_rate']}")
        
        return jsonify({'status': 'updated', 'config': new_config})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/security/failed-attempts', methods=['GET'])
def get_failed_attempts():
    """Get tracked failed login attempts (for security monitoring)"""
    return jsonify({
        'failed_attempts': auth_service.failed_attempts,
        'total_tracked_ips': len(auth_service.failed_attempts)
    })

if __name__ == '__main__':
    # Start event generation
    auth_service.start_event_generation()
    
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=8082, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down auth service...")
        auth_service.stop_event_generation()
