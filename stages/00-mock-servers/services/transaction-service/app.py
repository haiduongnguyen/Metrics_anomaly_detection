#!/usr/bin/env python3
"""
Banking Transaction Service Mock
Generates realistic transaction events with configurable anomaly rates
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

class TransactionService:
    """Mock transaction service for banking anomaly detection"""
    
    def __init__(self):
        self.event_queue = queue.Queue()
        self.running = False
        self.config = self._load_config()
        
        # Service metrics
        self.metrics = {
            'transactions_processed': 0,
            'anomalies_detected': 0,
            'average_response_time': 0,
            'error_rate': 0,
            'uptime_start': datetime.now()
        }
        
    def _load_config(self):
        """Load service configuration"""
        try:
            with open('/app/config/anomaly_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            return {
                'anomaly_settings': {
                    'transaction_service': {
                        'anomaly_rate': 0.02
                    }
                },
                'banking_metrics': {
                    'transaction_amounts': {
                        'min': 10.0,
                        'max': 50000.0,
                        'normal_mean': 250.0,
                        'normal_std': 150.0
                    },
                    'response_times': {
                        'normal_mean_ms': 200,
                        'normal_std_ms': 100
                    }
                }
            }
    
    def generate_transaction(self):
        """Generate a single transaction event"""
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Determine if this should be an anomaly
        anomaly_rate = self.config['anomaly_settings']['transaction_service'].get('anomaly_rate', 0.02)
        is_anomaly = random.random() < anomaly_rate
        
        # Generate transaction details
        if is_anomaly:
            amount = random.uniform(10000, 50000)  # High-value suspicious transaction
            risk_score = random.uniform(0.7, 1.0)
            status = "flagged"
            anomaly_type = random.choice(['suspicious_amount', 'unusual_location', 'rapid_succession'])
        else:
            amount_metrics = self.config['banking_metrics']['transaction_amounts']
            amount = max(
                amount_metrics['min'],
                random.gauss(amount_metrics['normal_mean'], amount_metrics['normal_std'])
            )
            risk_score = random.uniform(0.1, 0.6)
            status = "completed"
            anomaly_type = None
        
        # Generate response time
        rt_metrics = self.config['banking_metrics']['response_times']
        response_time = max(
            50,
            int(random.gauss(rt_metrics['normal_mean_ms'], rt_metrics['normal_std_ms']))
        )
        
        if is_anomaly:
            response_time = int(response_time * random.uniform(1.5, 2.5))
        
        transaction = {
            'transaction_id': transaction_id,
            'timestamp': timestamp,
            'service': 'transaction-service',
            'customer_id': f"CUST_{random.randint(100000, 999999)}",
            'account_id': f"ACC_{random.randint(100000, 999999)}",
            'transaction_type': random.choice(['purchase', 'transfer', 'withdrawal', 'deposit']),
            'amount': round(amount, 2),
            'currency': 'USD',
            'merchant_id': f"MER_{random.randint(100000, 999999)}",
            'location': {
                'country': random.choice(['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP']),
                'city': f"City_{random.randint(1, 100)}",
                'ip_address': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            },
            'device_info': {
                'device_id': f"DEV_{random.randint(100000, 999999)}",
                'type': random.choice(['mobile', 'desktop', 'tablet']),
                'os': random.choice(['iOS', 'Android', 'Windows', 'macOS'])
            },
            'response_time_ms': response_time,
            'status': status,
            'risk_score': risk_score,
            'anomaly_type': anomaly_type
        }
        
        # Update metrics
        self.metrics['transactions_processed'] += 1
        if is_anomaly:
            self.metrics['anomalies_detected'] += 1
        
        return transaction
    
    def start_event_generation(self):
        """Start continuous event generation in background thread"""
        self.running = True
        
        def generate_events():
            while self.running:
                try:
                    # Generate transaction
                    transaction = self.generate_transaction()
                    
                    # Add to queue for processing
                    self.event_queue.put(transaction)
                    
                    # Simulate processing time
                    time.sleep(random.uniform(0.01, 0.1))
                    
                except Exception as e:
                    logger.error(f"Error generating transaction: {e}")
                    time.sleep(1)
        
        # Start background thread
        self.generation_thread = threading.Thread(target=generate_events, daemon=True)
        self.generation_thread.start()
        logger.info("Transaction event generation started")
    
    def stop_event_generation(self):
        """Stop event generation"""
        self.running = False
        logger.info("Transaction event generation stopped")

# Initialize service
transaction_service = TransactionService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - transaction_service.metrics['uptime_start']).total_seconds()
    
    return jsonify({
        'status': 'healthy',
        'service': 'transaction-service',
        'uptime_seconds': uptime,
        'metrics': transaction_service.metrics
    })

@app.route('/transactions', methods=['POST'])
def create_transaction():
    """Create a new transaction (for testing)"""
    try:
        transaction = transaction_service.generate_transaction()
        return jsonify(transaction), 201
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/transactions/events', methods=['GET'])
def get_events():
    """Get generated events from queue"""
    events = []
    while not transaction_service.event_queue.empty() and len(events) < 100:
        try:
            event = transaction_service.event_queue.get_nowait()
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
    uptime = (datetime.now() - transaction_service.metrics['uptime_start']).total_seconds()
    
    # Calculate average response time
    if transaction_service.metrics['transactions_processed'] > 0:
        avg_response_time = transaction_service.metrics['average_response_time']
    else:
        avg_response_time = 0
    
    # Calculate error rate
    if transaction_service.metrics['transactions_processed'] > 0:
        error_rate = (transaction_service.metrics['anomalies_detected'] / 
                     transaction_service.metrics['transactions_processed']) * 100
    else:
        error_rate = 0
    
    return jsonify({
        'service': 'transaction-service',
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'transactions_processed': transaction_service.metrics['transactions_processed'],
            'anomalies_detected': transaction_service.metrics['anomalies_detected'],
            'anomaly_rate_percent': round(error_rate, 2),
            'average_response_time_ms': avg_response_time,
            'uptime_seconds': uptime,
            'queue_size': transaction_service.event_queue.qsize()
        }
    })

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'anomaly_rate': transaction_service.config['anomaly_settings']['transaction_service'].get('anomaly_rate', 0.02),
        'service': 'transaction-service'
    })

@app.route('/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        new_config = request.json
        if 'anomaly_rate' in new_config:
            transaction_service.config['anomaly_settings']['transaction_service']['anomaly_rate'] = new_config['anomaly_rate']
            logger.info(f"Updated anomaly rate to {new_config['anomaly_rate']}")
        
        return jsonify({'status': 'updated', 'config': new_config})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Start event generation
    transaction_service.start_event_generation()
    
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=8081, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down transaction service...")
        transaction_service.stop_event_generation()
