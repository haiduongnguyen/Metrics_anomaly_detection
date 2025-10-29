#!/usr/bin/env python3
"""
Mock Log Server for Banking Anomaly Detection
Generates realistic logs with configurable anomaly scenarios
"""

import asyncio
import json
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yaml
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Banking Log Server", version="1.0.0")

class LogGenerator:
    """Main log generation engine"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.running = False
        self.generation_task = None
        self.correlation_chains = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _generate_uuid(self) -> str:
        """Generate a UUID string"""
        return str(uuid.uuid4())
    
    def _generate_timestamp(self) -> str:
        """Generate ISO 8601 timestamp with milliseconds"""
        return datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
    
    def _generate_user_id(self) -> str:
        """Generate realistic user ID"""
        return f"USR-{random.randint(10000, 99999)}"
    
    def _generate_ip_address(self, country_code: Optional[str] = None) -> str:
        """Generate realistic IP address with optional geographic hint"""
        if country_code == "VN":
            return f"203.{random.randint(160, 191)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        elif country_code == "US":
            return f"52.{random.randint(0, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        elif country_code == "SG":
            return f"52.{random.randint(0, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        else:
            return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    def _get_random_country(self) -> Dict[str, str]:
        """Get random country based on geographic distribution"""
        countries = self.config.get('geographic_distribution', {}).get('countries', [])
        if not countries:
            return {"code": "US", "name": "United States"}
        
        weights = [c.get('weight', 1.0) for c in countries]
        country = random.choices(countries, weights=weights)[0]
        return {"code": country.get('code', 'US'), "name": country.get('name', 'Unknown')}
    
    def _select_service_source(self, anomaly_scenario: Optional[Dict] = None) -> str:
        """Select service source for log generation"""
        if anomaly_scenario and 'source_services' in anomaly_scenario:
            return random.choice(anomaly_scenario['source_services'])
        
        services = self.config.get('service_sources', ['api-gateway'])
        return random.choice(services)
    
    def _select_log_level(self, anomaly_scenario: Optional[Dict] = None) -> str:
        """Select log level based on anomaly scenario or global distribution"""
        if anomaly_scenario and 'log_level' in anomaly_scenario:
            return anomaly_scenario['log_level']
        
        levels = self.config.get('log_levels', {'INFO': 0.60})
        level_names = list(levels.keys())
        weights = list(levels.values())
        return random.choices(level_names, weights=weights)[0]
    
    def _generate_normal_log(self) -> Dict[str, Any]:
        """Generate a normal (non-anomaly) log entry"""
        templates = self.config.get('normal_log_templates', [])
        if not templates:
            template = "Normal system operation"
        else:
            template = random.choice(templates)['template']
        
        service = self._select_service_source()
        level = self._select_log_level()
        
        # Fill template placeholders
        message = template.format(
            user_id=self._generate_user_id(),
            transaction_id=f"TXN-{random.randint(100000, 999999)}",
            amount=f"{random.uniform(10, 1000):.2f}",
            endpoint=f"/api/v1/{random.choice(['users', 'transactions', 'accounts', 'payments'])}",
            response_time=random.randint(50, 500),
            query_time=random.randint(1, 100),
            cache_key=f"cache:{random.choice(['user', 'transaction', 'account'])}:{random.randint(1, 9999)}",
            session_id=f"sess_{self._generate_uuid()[:8]}",
            order_id=f"ORD-{random.randint(10000, 99999)}",
            channel=random.choice(['email', 'sms', 'push']),
            service_name=service,
            action=random.choice(['login', 'logout', 'create', 'update', 'delete'])
        )
        
        return {
            "timestamp": self._generate_timestamp(),
            "source_service": service,
            "log_level": level,
            "event_id": self._generate_uuid(),
            "user_id": self._generate_user_id(),
            "ip_address": self._generate_ip_address(),
            "message": message,
            "anomaly_details": {
                "is_anomaly": False
            }
        }
    
    def _generate_anomaly_log(self, anomaly_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an anomaly log entry based on scenario configuration"""
        service = self._select_service_source(anomaly_scenario)
        level = self._select_log_level(anomaly_scenario)
        country = self._get_random_country()
        
        # Generate scenario-specific message
        message = self._generate_anomaly_message(anomaly_scenario, country)
        
        # Create correlation chain if specified
        correlation_id = self._generate_uuid()
        if 'correlation_chain' in anomaly_scenario:
            self.correlation_chains[correlation_id] = anomaly_scenario['correlation_chain']
        
        log_entry = {
            "timestamp": self._generate_timestamp(),
            "source_service": service,
            "log_level": level,
            "event_id": self._generate_uuid(),
            "correlation_id": correlation_id,
            "user_id": self._generate_user_id(),
            "ip_address": self._generate_ip_address(country['code']),
            "geo_location": f"{country['code']}-{country['name'][:2].upper()}",
            "message": message,
            "anomaly_details": {
                "is_anomaly": True,
                "anomaly_id": anomaly_scenario['id'],
                "anomaly_type": anomaly_scenario['type'],
                "anomaly_name": anomaly_scenario['name'],
                "category": anomaly_scenario.get('category', 'unknown'),
                "severity": anomaly_scenario['severity'],
                "confidence": round(random.uniform(0.7, 0.98), 2)
            }
        }
        
        # Add scenario-specific metrics
        log_entry.update(self._generate_anomaly_metrics(anomaly_scenario))
        
        return log_entry
    
    def _generate_anomaly_message(self, scenario: Dict[str, Any], country: Dict[str, str]) -> str:
        """Generate scenario-specific anomaly message"""
        scenario_id = scenario['id']
        intensity = scenario.get('intensity', {})
        
        messages = {
            "BANK-001": f"Multiple failed login attempts detected for user. {intensity.get('min_attempts', 5)}-{intensity.get('max_attempts', 15)} attempts in {intensity.get('time_window_minutes', 5)} minutes",
            "BANK-002": f"Brute force attack detected from {intensity.get('unique_ips', 10)} unique IP addresses. {intensity.get('attempts_per_minute', 50)} attempts per minute",
            "BANK-003": f"Transaction amount anomaly detected: ${random.uniform(intensity.get('normal_amount_range', [100, 5000])[1] * intensity.get('amount_multiplier', 10), 50000):.2f} exceeds normal pattern",
            "BANK-004": f"Credential stuffing attack detected: {intensity.get('total_attempts', 1000)} total attempts with {intensity.get('success_rate', 0.02)*100:.1f}% success rate",
            "BANK-005": f"Geographic traffic anomaly: User login from unusual location {country['name']} (IP: {self._generate_ip_address(country['code'])})",
            "BANK-006": f"PII access anomaly: User accessed {intensity.get('accounts_accessed', 50)} accounts in {intensity.get('time_window_minutes', 10)} minutes",
            "BANK-007": f"Session hijacking detected: {intensity.get('concurrent_sessions', 3)} concurrent sessions from geographic distance >{intensity.get('geographic_distance_km', 1000)}km",
            "BANK-008": f"VPN anomaly detected: Suspicious activity from VPN in {country['name']}. Connection frequency: {intensity.get('connection_frequency', 10)}/hour",
            "BANK-009": f"Request timeout spike: {intensity.get('timeout_rate', 0.15)*100:.1f}% timeout rate (normal: {intensity.get('normal_timeout_rate', 0.01)*100:.1f}%)",
            "BANK-010": f"Database connection errors: {intensity.get('active_connections', 95)}/{intensity.get('max_connections', 100)} connections active, {intensity.get('error_rate', 0.10)*100:.1f}% error rate",
            "BANK-011": f"Cache hit rate degradation: {intensity.get('cache_hit_rate', 0.60)*100:.1f}% hit rate (normally 95%+)",
            "BANK-012": f"Database replication lag: {intensity.get('lag_seconds', 30)}s lag (normal: {intensity.get('normal_lag_seconds', 1)}s)",
            "BANK-013": f"DDoS attack detected: {intensity.get('requests_per_second', 10000)} RPS from {intensity.get('source_ip_count', 1000)} unique IPs",
            "BANK-014": f"SQL injection attempt detected: Payload '{random.choice(intensity.get('payloads', ['OR 1=1']))}' blocked",
            "BANK-015": f"Data exfiltration detected: {intensity.get('records_exported', 10000)} records exported in {intensity.get('time_window_minutes', 30)} minutes",
            "BANK-016": f"Ransomware activity detected: {intensity.get('encrypted_files', 1000)} files encrypted, backup systems compromised"
        }
        
        return messages.get(scenario_id, f"Anomaly detected: {scenario['name']}")
    
    def _generate_anomaly_metrics(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scenario-specific metrics"""
        scenario_id = scenario['id']
        intensity = scenario.get('intensity', {})
        
        metrics = {}
        
        if scenario_id in ["BANK-001", "BANK-002", "BANK-004"]:
            metrics.update({
                "failed_attempts": random.randint(intensity.get('min_attempts', 5), intensity.get('max_attempts', 15)),
                "unique_ips": intensity.get('unique_ips', random.randint(1, 20)),
                "success_rate": intensity.get('success_rate', random.uniform(0.01, 0.05))
            })
        
        elif scenario_id == "BANK-003":
            normal_range = intensity.get('normal_amount_range', [100, 5000])
            metrics.update({
                "transaction_amount": random.uniform(normal_range[1] * intensity.get('amount_multiplier', 10), 100000),
                "normal_amount_max": normal_range[1],
                "amount_multiplier": intensity.get('amount_multiplier', 10)
            })
        
        elif scenario_id in ["BANK-009", "BANK-010", "BANK-011", "BANK-012"]:
            metrics.update({
                "error_rate": intensity.get('error_rate', random.uniform(0.05, 0.20)),
                "response_time_ms": random.randint(1000, 10000),
                "cpu_utilization_pct": random.uniform(70, 95),
                "memory_utilization_pct": random.uniform(60, 90)
            })
        
        elif scenario_id == "BANK-013":
            metrics.update({
                "requests_per_second": intensity.get('requests_per_second', 10000),
                "normal_rps": intensity.get('normal_rps', 100),
                "attack_duration_minutes": intensity.get('attack_duration_minutes', 15),
                "source_ip_count": intensity.get('source_ip_count', 1000)
            })
        
        elif scenario_id in ["BANK-015", "BANK-016"]:
            metrics.update({
                "records_affected": intensity.get('records_exported', random.randint(1000, 50000)),
                "time_window_minutes": intensity.get('time_window_minutes', 30),
                "data_size_mb": random.uniform(100, 1000)
            })
        
        return {"metrics": metrics}
    
    def _select_anomaly_scenario(self) -> Optional[Dict[str, Any]]:
        """Select an anomaly scenario based on frequency weights"""
        scenarios = [s for s in self.config.get('anomaly_scenarios', []) if s.get('enabled', True)]
        
        if not scenarios:
            return None
        
        weights = [s.get('frequency_weight', 1) for s in scenarios]
        return random.choices(scenarios, weights=weights)[0]
    
    def _generate_correlation_logs(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Generate correlated logs for correlation chains"""
        if correlation_id not in self.correlation_chains:
            return []
        
        chain = self.correlation_chains[correlation_id]
        logs = []
        
        for chain_event in chain[:2]:  # Limit to prevent infinite loops
            # Generate follow-up log for correlation chain event
            log_entry = {
                "timestamp": self._generate_timestamp(),
                "source_service": random.choice(self.config.get('service_sources', ['api-gateway'])),
                "log_level": "INFO",
                "event_id": self._generate_uuid(),
                "correlation_id": correlation_id,
                "user_id": self._generate_user_id(),
                "ip_address": self._generate_ip_address(),
                "message": f"Correlation event: {chain_event}",
                "anomaly_details": {
                    "is_anomaly": False,
                    "correlation_event": chain_event
                }
            }
            logs.append(log_entry)
        
        # Remove correlation chain after processing
        del self.correlation_chains[correlation_id]
        return logs
    
    async def generate_logs(self):
        """Main log generation loop"""
        logs_per_second = self.config.get('log_generation', {}).get('logs_per_second', 100)
        global_anomaly_rate = self.config.get('global_anomaly_rate', 0.08)
        burst_config = self.config.get('log_generation', {}).get('burst_simulation', True)
        
        last_burst_time = time.time()
        burst_active = False
        burst_end_time = 0
        
        logger.info(f"Starting log generation: {logs_per_second} logs/sec, {global_anomaly_rate*100:.1f}% anomaly rate")
        
        while self.running:
            current_time = time.time()
            current_logs_per_second = logs_per_second
            
            # Handle burst simulation
            if burst_config and not burst_active:
                burst_frequency = self.config.get('log_generation', {}).get('burst_frequency_seconds', 300)
                if current_time - last_burst_time > burst_frequency:
                    burst_active = True
                    burst_end_time = current_time + self.config.get('log_generation', {}).get('burst_duration_seconds', 30)
                    burst_multiplier = self.config.get('log_generation', {}).get('burst_multiplier', 3.0)
                    current_logs_per_second = int(logs_per_second * burst_multiplier)
                    logger.info(f"Burst mode activated: {current_logs_per_second} logs/sec")
            
            if burst_active and current_time > burst_end_time:
                burst_active = False
                last_burst_time = current_time
                logger.info(f"Burst mode ended: {logs_per_second} logs/sec")
            
            # Generate logs for this second
            logs_to_generate = current_logs_per_second
            anomaly_logs_to_generate = int(logs_to_generate * global_anomaly_rate)
            normal_logs_to_generate = logs_to_generate - anomaly_logs_to_generate
            
            # Generate normal logs
            for _ in range(normal_logs_to_generate):
                log_entry = self._generate_normal_log()
                print(json.dumps(log_entry, separators=(',', ':')), flush=True)
                await asyncio.sleep(1.0 / normal_logs_to_generate)
            
            # Generate anomaly logs
            for _ in range(anomaly_logs_to_generate):
                scenario = self._select_anomaly_scenario()
                if scenario:
                    log_entry = self._generate_anomaly_log(scenario)
                    print(json.dumps(log_entry, separators=(',', ':')), flush=True)
                    
                    # Generate correlation logs if applicable
                    if 'correlation_id' in log_entry:
                        correlation_logs = self._generate_correlation_logs(log_entry['correlation_id'])
                        for corr_log in correlation_logs:
                            await asyncio.sleep(0.01)  # Small delay between correlation logs
                            print(json.dumps(corr_log, separators=(',', ':')), flush=True)
                
                await asyncio.sleep(1.0 / max(anomaly_logs_to_generate, 1))
            
            # Sleep for remaining time in this second
            elapsed = time.time() - current_time
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
    
    async def start_generation(self):
        """Start the log generation process"""
        if self.running:
            logger.warning("Log generation already running")
            return
        
        self.running = True
        self.generation_task = asyncio.create_task(self.generate_logs())
        logger.info("Log generation started")
    
    async def stop_generation(self):
        """Stop the log generation process"""
        if not self.running:
            logger.warning("Log generation not running")
            return
        
        self.running = False
        if self.generation_task:
            self.generation_task.cancel()
            try:
                await self.generation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Log generation stopped")

# Global log generator instance
log_generator = LogGenerator()

# API Models
class StatusResponse(BaseModel):
    status: str
    running: bool
    config_loaded: bool

class ControlRequest(BaseModel):
    action: str  # "start" or "stop"

# API Endpoints
@app.get("/", response_model=StatusResponse)
async def get_status():
    """Get server status"""
    return StatusResponse(
        status="running",
        running=log_generator.running,
        config_loaded=True
    )

@app.post("/control")
async def control_generation(request: ControlRequest):
    """Start or stop log generation"""
    if request.action == "start":
        await log_generator.start_generation()
        return {"status": "started", "message": "Log generation started"}
    elif request.action == "stop":
        await log_generator.stop_generation()
        return {"status": "stopped", "message": "Log generation stopped"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Main execution
async def main():
    """Main function to run the server"""
    parser = argparse.ArgumentParser(description="Mock Banking Log Server")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")
    parser.add_argument("--auto-start", action="store_true", help="Auto-start log generation")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    # Initialize log generator with config
    global log_generator
    log_generator = LogGenerator(args.config)
    
    # Auto-start if requested
    if args.auto_start:
        await log_generator.start_generation()
    
    # Run server
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=args.port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
