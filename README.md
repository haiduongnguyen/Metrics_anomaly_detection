# Banking Metrics Anomaly Detection & Root Cause Analysis

A comprehensive system for detecting anomalies in banking metrics and performing root cause analysis using AI-powered techniques.

## 🎯 Overview

This project provides a mock log server that generates realistic banking system logs with configurable anomaly scenarios, designed for testing and developing anomaly detection systems.

## 🚀 Quick Start

### Option 1: Local Docker Compose (Recommended)
```bash
cd stages/00-mock-servers

# Start the mock server
./run.sh

# View logs
./run.sh logs

# Stop the server
./run.sh stop
```

### Option 2: Manual Docker Compose
```bash
cd stages/00-mock-servers

# Build and start
docker compose up --build

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Option 3: Direct Python
```bash
cd stages/00-mock-servers

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py --auto-start
```

## 📊 Features

### Mock Server Capabilities
- **16 Anomaly Scenarios**: Realistic banking threats across 4 categories
- **Configurable Rates**: Adjustable anomaly rates (default 8%)
- **Multiple Services**: Logs from 11 different banking services
- **JSON Format**: Structured logs with comprehensive metadata
- **REST API**: Control server behavior via HTTP endpoints
- **Burst Simulation**: Periodic traffic spikes for testing

### Anomaly Categories
1. **Suspicious Transactions** (High Frequency)
   - Login Failure Spike
   - Brute Force Attack
   - Transaction Amount Anomaly
   - Credential Stuffing

2. **Abnormal User Activity** (Medium Frequency)
   - Geographic Traffic Anomaly
   - PII Access Anomaly
   - Session Hijacking
   - VPN Anomalies

3. **Minor System Errors** (Medium Frequency)
   - Request Timeout Spike
   - Database Connection Errors
   - Cache Hit Rate Degradation
   - Database Replication Lag

4. **Severe Anomalies** (Low Frequency)
   - DDoS Attack
   - SQL Injection Attempts
   - Data Exfiltration
   - Ransomware Activity

## 📁 Project Structure

```
Metrics_anomaly_detection/
├── README.md                           # This file
├── .gitignore                          # Git ignore rules
├── stages/
│   ├── 00-mock-servers/               # ✅ Mock server implementation
│   │   ├── app.py                     # Main FastAPI application
│   │   ├── config.yaml               # Configuration file
│   │   ├── docker-compose.yml        # Docker setup
│   │   ├── Dockerfile                # Container definition
│   │   ├── run.sh                    # Quick start script
│   │   └── requirements.txt          # Python dependencies
│   ├── config/                       # Infrastructure configuration
│   │   ├── main.tf                   # Terraform configuration
│   │   ├── user-data.sh              # EC2 setup script
│   │   ├── main-minimal.tf           # Minimal AWS setup
│   │   ├── variables-minimal.tf      # AWS variables
│   │   └── outputs-minimal.tf        # AWS outputs
│   └── MINIMAL_DEPLOYMENT.md         # Deployment guide
└── challenge-documents/              # Original requirements
```

## 🔧 Configuration

### Server Configuration (`config.yaml`)
```yaml
# Global anomaly rate
global_anomaly_rate: 0.08

# Log generation settings
log_generation:
  logs_per_second: 10
  burst_simulation: true

# Service sources
service_sources:
  - api-gateway
  - transaction-service
  - auth-service
  - fraud-detection-service

# Anomaly scenarios (16 total)
anomaly_scenarios:
  - id: "BANK-001"
    name: "Login Failure Spike"
    type: "Suspicious Transaction"
    enabled: true
    frequency_weight: 40
    severity: "High"
```

## 📡 API Endpoints

### Server Control
- **GET `/`** - Server status
- **GET `/health`** - Health check
- **POST `/control`** - Start/stop log generation

### Control Examples
```bash
# Start log generation
curl -X POST http://localhost:8000/control \
  -H 'Content-Type: application/json' \
  -d '{"action":"start"}'

# Stop log generation
curl -X POST http://localhost:8000/control \
  -H 'Content-Type: application/json' \
  -d '{"action":"stop"}'

# Check status
curl http://localhost:8000/
```

## 📋 Log Format

All logs are structured in JSON format:
```json
{
  "timestamp": "2025-10-29T14:23:45.123Z",
  "source_service": "auth-service",
  "log_level": "WARN",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "USR-12345",
  "ip_address": "203.0.113.42",
  "geo_location": "US-CA",
  "message": "Multiple failed login attempts detected",
  "anomaly_details": {
    "is_anomaly": true,
    "anomaly_id": "BANK-001",
    "anomaly_type": "Suspicious Transaction",
    "anomaly_name": "Login Failure Spike (#61)",
    "category": "security_authentication",
    "severity": "High",
    "confidence": 0.95
  },
  "metrics": {
    "failed_attempts": 12,
    "unique_ips": 3,
    "success_rate": 0.02
  }
}
```

## 🌐 Deployment Options

### Local Development
- **Docker Compose**: Easiest method for local testing
- **Direct Python**: For development and debugging
- **Configuration**: Edit `config.yaml` to customize behavior

### Cloud Deployment (AWS)
- **EC2 Instance**: Deploy to AWS using Terraform
- **Docker Container**: Runs in Docker on EC2
- **Auto-scaling**: Configurable for production workloads

#### AWS Deployment Commands
```bash
cd stages/config

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply

# Get server URL
terraform output server_url
```

## 🧪 Testing and Validation

### Health Checks
```bash
# Check server health
curl http://localhost:8000/health

# Verify log generation
curl http://localhost:8000/
```

### Log Monitoring
```bash
# View real-time logs
./run.sh logs

# Filter for anomalies
docker compose logs -f banking-mock-server | grep "is_anomaly.*true"

# Check log rate
docker compose logs banking-mock-server | wc -l
```

### Configuration Testing
```bash
# Test configuration loading
python3 -c "
import yaml
config = yaml.safe_load(open('config.yaml'))
print(f'Anomaly scenarios: {len(config.get(\"anomaly_scenarios\", []))}')
print(f'Anomaly rate: {config.get(\"global_anomaly_rate\", 0)}')
print(f'Log rate: {config.get(\"log_generation\", {}).get(\"logs_per_second\", 0)}')
"
```

## 🔍 Troubleshooting

### Common Issues

#### Server Not Starting
```bash
# Check Docker status
docker --version
docker compose version

# Check port availability
lsof -i :8000

# View container logs
docker logs banking-mock-server
```

#### No Logs Visible
```bash
# Check if log generation is active
curl -X POST http://localhost:8000/control \
  -H 'Content-Type: application/json' \
  -d '{"action":"start"}'

# Verify configuration
./run.sh status
```

#### Performance Issues
```bash
# Reduce log generation rate
# Edit config.yaml: logs_per_second: 5

# Monitor resource usage
docker stats banking-mock-server
```

### Debug Mode
```bash
# Run with debug logging
docker compose up --build

# Check container internals
docker exec -it banking-mock-server /bin/bash
```

## 📈 Performance Metrics

### Default Configuration
- **Log Generation**: 10 logs/second (configurable)
- **Anomaly Rate**: 8% of logs (configurable)
- **Memory Usage**: ~100MB (container)
- **CPU Usage**: ~5% (container)
- **Storage**: Minimal (logs in memory)

### Scaling Considerations
- **Horizontal Scale**: Multiple containers via Docker Swarm/Kubernetes
- **Vertical Scale**: Increase `logs_per_second` in config
- **Cloud Deployment**: AWS EC2 with auto-scaling groups

## 🛠️ Development

### Adding New Anomalies
1. Edit `config.yaml` to add new scenario
2. Update `app.py` if custom logic needed
3. Restart server to apply changes

### Custom Configuration
```yaml
# Add new anomaly scenario
anomaly_scenarios:
  - id: "BANK-017"
    name: "Custom Anomaly"
    type: "Custom Category"
    enabled: true
    frequency_weight: 10
    severity: "Medium"
    source_services: ["api-gateway"]
```

### Testing Changes
```bash
# Rebuild and restart
docker compose up --build

# Validate configuration
curl http://localhost:8000/health
```

## 📚 Documentation

- **[MINIMAL_DEPLOYMENT.md](stages/MINIMAL_DEPLOYMENT.md)**: Deployment guide
- **[Architecture](challenge-documents/)**: Original requirements
- **[API Documentation](http://localhost:8000/docs)**: Interactive API docs (when server running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Banking Anomaly Detection system. See the main project license for details.

## 🆘 Support

For issues and questions:
1. Check the logs for error messages
2. Verify configuration syntax
3. Test with minimal config first
4. Check AWS console for deployment issues

## 🔄 Version History

- **v2.0.0**: Minimal mock server with Docker Compose
- **v1.0.0**: Original multi-service architecture

---

**Current Status**: ✅ Working mock server with 16 anomaly scenarios, Docker Compose deployment, and AWS EC2 support.
