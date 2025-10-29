#!/usr/bin/env python3
"""
Banking Anomaly Detection Data Generator
Generates realistic banking logs with configurable anomaly rates
"""

import json
import random
import time
import datetime
import uuid
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TransactionEvent:
    """Transaction event structure"""
    timestamp: str
    event_id: str
    service: str
    customer_id: str
    account_id: str
    transaction_type: str
    amount: float
    currency: str
    merchant_id: str
    location: Dict[str, str]
    device_info: Dict[str, str]
    response_time_ms: int
    status: str
    risk_score: float
    anomaly_type: str = None

@dataclass
class AuthEvent:
    """Authentication event structure"""
    timestamp: str
    event_id: str
    service: str
    customer_id: str
    username: str
    ip_address: str
    user_agent: str
    device_fingerprint: str
    location: Dict[str, str]
    auth_method: str
    result: str
    failure_reason: str = None
    response_time_ms: int
    anomaly_type: str = None

@dataclass
class MonitoringEvent:
    """System monitoring event structure"""
    timestamp: str
    event_id: str
    service: str
    metric_name: str
    metric_value: float
    unit: str
    instance_id: str
    environment: str
    alert_threshold: float
    status: str
    anomaly_type: str = None

class BankingDataGenerator:
    """Main data generator class for banking anomaly detection"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "anomaly_config.json"
        self.scenarios_path = Path(__file__).parent.parent / "config" / "banking_scenarios.json"
        
        self.config = self._load_config()
        self.scenarios = self._load_scenarios()
        
        # Initialize data pools
        self.customers = self._generate_customer_pool()
        self.merchants = self._generate_merchant_pool()
        self.locations = self._generate_location_pool()
        self.devices = self._generate_device_pool()
        
        # Anomaly state tracking
        self.anomaly_states = {
            'transaction': {},
            'auth': {},
            'monitoring': {}
        }
        
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _load_scenarios(self) -> Dict:
        """Load anomaly scenarios from JSON file"""
        with open(self.scenarios_path, 'r') as f:
            return json.load(f)
    
    def _generate_customer_pool(self) -> List[Dict]:
        """Generate a pool of customers"""
        customers = []
        segments = self.config['generation_settings']['customer_segments']
        
        for i in range(10000):  # 10K customers
            segment = random.choices(
                list(segments.keys()),
                weights=list(segments.values())
            )[0]
            
            customers.append({
                'customer_id': f"CUST_{i:06d}",
                'segment': segment,
                'accounts': [f"ACC_{i:06d}_{j}" for j in range(random.randint(1, 3))],
                'registration_date': self._random_past_date(days=365*3),
                'risk_level': random.choice(['low', 'medium', 'high'])
            })
        
        return customers
    
    def _generate_merchant_pool(self) -> List[Dict]:
        """Generate a pool of merchants"""
        categories = ['retail', 'restaurant', 'online', 'gas', 'grocery', 'travel', 'entertainment']
        merchants = []
        
        for i in range(5000):  # 5K merchants
            merchants.append({
                'merchant_id': f"MER_{i:06d}",
                'name': f"Merchant {i}",
                'category': random.choice(categories),
                'location': random.choice(self.locations if 'locations' in locals() else self._generate_location_pool()),
                'risk_score': random.uniform(0.1, 0.9)
            })
        
        return merchants
    
    def _generate_location_pool(self) -> List[Dict]:
        """Generate a pool of geographic locations"""
        countries = ['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'SG', 'IN', 'BR']
        cities = {
            'US': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
            'GB': ['London', 'Manchester', 'Birmingham', 'Leeds', 'Glasgow'],
            'CA': ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Ottawa'],
            'AU': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide'],
            'DE': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne'],
            'FR': ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice'],
            'JP': ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya'],
            'SG': ['Singapore'],
            'IN': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata'],
            'BR': ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza']
        }
        
        locations = []
        for country in countries:
            for city in cities.get(country, ['Unknown']):
                locations.append({
                    'country': country,
                    'city': city,
                    'latitude': random.uniform(-90, 90),
                    'longitude': random.uniform(-180, 180)
                })
        
        return locations
    
    def _generate_device_pool(self) -> List[Dict]:
        """Generate a pool of device information"""
        devices = []
        for i in range(2000):
            devices.append({
                'device_id': f"DEV_{i:06d}",
                'type': random.choice(['mobile', 'desktop', 'tablet']),
                'os': random.choice(['iOS', 'Android', 'Windows', 'macOS', 'Linux']),
                'browser': random.choice(['Chrome', 'Safari', 'Firefox', 'Edge', 'Opera'])
            })
        
        return devices
    
    def _random_past_date(self, days: int) -> str:
        """Generate a random past date"""
        past_date = datetime.datetime.now() - datetime.timedelta(
            days=random.randint(1, days)
        )
        return past_date.isoformat()
    
    def _should_generate_anomaly(self, service: str) -> bool:
        """Determine if an anomaly should be generated based on configuration"""
        service_config = self.config['anomaly_settings'].get(f"{service}_service", {})
        anomaly_rate = service_config.get('anomaly_rate', 0.02)
        return random.random() < anomaly_rate
    
    def _generate_transaction_event(self) -> TransactionEvent:
        """Generate a transaction event"""
        customer = random.choice(self.customers)
        merchant = random.choice(self.merchants)
        location = random.choice(self.locations)
        device = random.choice(self.devices)
        
        # Determine if this should be an anomaly
        anomaly_type = None
        risk_score = random.uniform(0.1, 0.8)
        
        if self._should_generate_anomaly('transaction'):
            anomaly_type = self._generate_transaction_anomaly()
            risk_score = random.uniform(0.7, 1.0)
        
        # Generate amount based on anomaly or normal pattern
        amount_metrics = self.config['banking_metrics']['transaction_amounts']
        if anomaly_type == 'suspicious_high_amount':
            amount = random.uniform(amount_metrics['suspicious_threshold'], amount_metrics['max'])
        elif anomaly_type == 'fraud_pattern':
            amount = random.uniform(100, 500)  # Small amounts for fraud
        else:
            # Normal distribution around mean
            amount = max(
                amount_metrics['min'],
                random.gauss(amount_metrics['normal_mean'], amount_metrics['normal_std'])
            )
        
        # Generate response time
        rt_metrics = self.config['banking_metrics']['response_times']
        response_time = max(
            rt_metrics['min_ms'],
            int(random.gauss(rt_metrics['normal_mean_ms'], rt_metrics['normal_std_ms']))
        )
        
        if anomaly_type:
            response_time = int(response_time * random.uniform(1.5, 3.0))
        
        return TransactionEvent(
            timestamp=datetime.datetime.now().isoformat(),
            event_id=str(uuid.uuid4()),
            service="transaction-service",
            customer_id=customer['customer_id'],
            account_id=random.choice(customer['accounts']),
            transaction_type=random.choice(['purchase', 'transfer', 'withdrawal', 'deposit']),
            amount=round(amount, 2),
            currency="USD",
            merchant_id=merchant['merchant_id'],
            location=location,
            device_info={
                'device_id': device['device_id'],
                'type': device['type'],
                'os': device['os']
            },
            response_time_ms=response_time,
            status="completed" if risk_score < 0.9 else "flagged",
            risk_score=risk_score,
            anomaly_type=anomaly_type
        )
    
    def _generate_transaction_anomaly(self) -> str:
        """Generate a specific type of transaction anomaly"""
        service_config = self.config['anomaly_settings']['transaction_service']
        rand_val = random.random()
        
        if rand_val < service_config['suspicious_transaction_rate'] / service_config['anomaly_rate']:
            return 'suspicious_high_amount'
        elif rand_val < (service_config['suspicious_transaction_rate'] + service_config['fraud_pattern_rate']) / service_config['anomaly_rate']:
            return 'fraud_pattern'
        else:
            return 'money_laundering'
    
    def _generate_auth_event(self) -> AuthEvent:
        """Generate an authentication event"""
        customer = random.choice(self.customers)
        location = random.choice(self.locations)
        device = random.choice(self.devices)
        
        # Determine if this should be an anomaly
        anomaly_type = None
        result = "success"
        failure_reason = None
        
        if self._should_generate_anomaly('auth'):
            anomaly_type = self._generate_auth_anomaly()
            if anomaly_type in ['brute_force', 'credential_stuffing']:
                result = "failure"
                failure_reason = "invalid_credentials"
        
        # Generate response time
        rt_metrics = self.config['banking_metrics']['response_times']
        response_time = max(
            rt_metrics['min_ms'],
            int(random.gauss(rt_metrics['normal_mean_ms'], rt_metrics['normal_std_ms']))
        )
        
        if anomaly_type:
            response_time = int(response_time * random.uniform(1.2, 2.0))
        
        return AuthEvent(
            timestamp=datetime.datetime.now().isoformat(),
            event_id=str(uuid.uuid4()),
            service="auth-service",
            customer_id=customer['customer_id'],
            username=f"user_{customer['customer_id'].split('_')[1]}",
            ip_address=f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            user_agent=f"{device['os']}/{device['browser']}",
            device_fingerprint=device['device_id'],
            location=location,
            auth_method=random.choice(['password', '2fa', 'biometric', 'sso']),
            result=result,
            failure_reason=failure_reason,
            response_time_ms=response_time,
            anomaly_type=anomaly_type
        )
    
    def _generate_auth_anomaly(self) -> str:
        """Generate a specific type of authentication anomaly"""
        service_config = self.config['anomaly_settings']['auth_service']
        rand_val = random.random()
        
        if rand_val < service_config['failed_login_rate'] / service_config['anomaly_rate']:
            return 'brute_force'
        elif rand_val < (service_config['failed_login_rate'] + service_config['brute_force_rate']) / service_config['anomaly_rate']:
            return 'credential_stuffing'
        else:
            return 'unusual_location'
    
    def _generate_monitoring_event(self) -> MonitoringEvent:
        """Generate a monitoring/metrics event"""
        services = ['transaction-service', 'auth-service', 'api-gateway', 'monitoring-service']
        metrics = ['cpu_utilization', 'memory_utilization', 'disk_usage', 'network_io', 'response_time_p95']
        
        # Determine if this should be an anomaly
        anomaly_type = None
        metric_value = random.uniform(20, 60)  # Normal range
        
        if self._should_generate_anomaly('monitoring'):
            anomaly_type = self._generate_monitoring_anomaly()
            if anomaly_type == 'high_cpu':
                metric_value = random.uniform(85, 95)
            elif anomaly_type == 'memory_leak':
                metric_value = random.uniform(80, 90)
            elif anomaly_type == 'disk_space':
                metric_value = random.uniform(92, 98)
        
        return MonitoringEvent(
            timestamp=datetime.datetime.now().isoformat(),
            event_id=str(uuid.uuid4()),
            service=random.choice(services),
            metric_name=random.choice(metrics),
            metric_value=metric_value,
            unit="percent",
            instance_id=f"i-{random.randint(10000000, 99999999)}",
            environment="production",
            alert_threshold=80.0,
            status="normal" if metric_value < 80 else "alert",
            anomaly_type=anomaly_type
        )
    
    def _generate_monitoring_anomaly(self) -> str:
        """Generate a specific type of monitoring anomaly"""
        service_config = self.config['anomaly_settings']['monitoring_service']
        rand_val = random.random()
        
        if rand_val < service_config['high_cpu_rate'] / service_config['anomaly_rate']:
            return 'high_cpu'
        elif rand_val < (service_config['high_cpu_rate'] + service_config['memory_leak_rate']) / service_config['anomaly_rate']:
            return 'memory_leak'
        elif rand_val < (service_config['high_cpu_rate'] + service_config['memory_leak_rate'] + service_config['network_timeout_rate']) / service_config['anomaly_rate']:
            return 'network_timeout'
        else:
            return 'disk_space'
    
    def generate_events_batch(self, batch_size: int = 50) -> List[Dict]:
        """Generate a batch of mixed events"""
        events = []
        
        for _ in range(batch_size):
            event_type = random.choices(
                ['transaction', 'auth', 'monitoring'],
                weights=[0.6, 0.3, 0.1]  # 60% transactions, 30% auth, 10% monitoring
            )[0]
            
            if event_type == 'transaction':
                event = self._generate_transaction_event()
            elif event_type == 'auth':
                event = self._generate_auth_event()
            else:
                event = self._generate_monitoring_event()
            
            events.append(asdict(event))
        
        return events
    
    def run_continuous_generation(self, duration_seconds: int = 300):
        """Run continuous event generation for specified duration"""
        logger.info(f"Starting continuous event generation for {duration_seconds} seconds")
        
        start_time = time.time()
        events_per_second = self.config['generation_settings']['events_per_second']
        
        while time.time() - start_time < duration_seconds:
            batch_start = time.time()
            
            # Generate batch of events
            batch = self.generate_events_batch(events_per_second)
            
            # Output events (in real implementation, send to message queue)
            for event in batch:
                print(json.dumps(event))
            
            # Calculate sleep time to maintain rate
            batch_duration = time.time() - batch_start
            target_batch_duration = 1.0  # 1 second per batch
            sleep_time = max(0, target_batch_duration - batch_duration)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logger.info("Event generation completed")

if __name__ == "__main__":
    generator = BankingDataGenerator()
    
    # Run for 5 minutes (300 seconds) for testing
    generator.run_continuous_generation(300)
