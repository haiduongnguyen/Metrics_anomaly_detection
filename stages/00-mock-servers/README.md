# Banking Anomaly Detection Mock Servers

This directory contains mock microservices that simulate realistic banking operations with configurable anomaly rates for testing anomaly detection systems.

## Architecture

The mock system consists of four main microservices:

### 1. Transaction Service (Port 8081)
- Generates realistic banking transactions
- Supports various transaction types: purchase, transfer, withdrawal, deposit
- Configurable anomaly scenarios: suspicious high amounts, fraud patterns, money laundering
- Realistic response times and risk scoring

### 2. Authentication Service (Port 8082)
- Simulates user authentication events
- Tracks failed login attempts for brute force detection
- Anomaly scenarios: brute force attacks, credential stuffing, unusual locations
- Device fingerprinting and geographic tracking

### 3. Monitoring Service (Port 8083)
- Generates system monitoring metrics
- Tracks CPU, memory, disk, and network metrics
- Anomaly scenarios: resource exhaustion, cascade failures, performance degradation
- System health events and alerting

### 4. API Gateway (Port 8080)
- Central entry point for all services
- Aggregates events and metrics from all services
- Provides unified dashboard and health monitoring
- Routes requests to appropriate microservices

## Features

### Realistic Data Generation
- **Imbalanced datasets**: Normal operations (95-98%) vs anomalies (2-5%)
- **Banking-specific metrics**: Transaction amounts, response times, error rates
- **Temporal patterns**: Business hours, seasonal variations, weekend effects
- **Customer segmentation**: Retail, business, premium customers

### Configurable Anomaly Rates
- Adjustable via configuration files
- Per-service anomaly rate configuration
- Real-time configuration updates via API
- Environment-specific settings (local vs AWS)

### Microservices Architecture
- Independent services with own databases
- Inter-service communication via REST APIs
- Service discovery and health monitoring
- Graceful degradation and error handling

### Deployment Options
- **Local development**: Docker Compose with LocalStack
- **EC2 deployment**: Free-tier optimized scripts
- **AWS integration**: Terraform configurations for full AWS deployment

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+ (for local development)
- AWS CLI (for AWS deployment)

### Local Development

1. **Start the services**:
```bash
cd docker
docker-compose up -d
```

2. **Verify services are running**:
```bash
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health
```

3. **View the dashboard**:
```bash
curl http://localhost:8080/dashboard
```

4. **Check generated events**:
```bash
curl http://localhost:8080/events
```

### Configuration

The main configuration file is `config/anomaly_config.json`:

```json
{
  "anomaly_settings": {
    "global_anomaly_rate": 0.02,
    "transaction_service": {
      "anomaly_rate": 0.015,
      "suspicious_transaction_rate": 0.008
    }
  },
  "generation_settings": {
    "events_per_second": 100
  }
}
```

### Real-time Configuration Updates

Update anomaly rates without restarting:

```bash
# Update transaction service anomaly rate
curl -X POST http://localhost:8081/config \
  -H "Content-Type: application/json" \
  -d '{"anomaly_rate": 0.03}'

# Update auth service anomaly rate
curl -X POST http://localhost:8082/config \
  -H "Content-Type: application/json" \
  -d '{"anomaly_rate": 0.04}'
```

## API Endpoints

### API Gateway (Port 8080)
- `GET /health` - Gateway health status
- `GET /dashboard` - Comprehensive dashboard
- `GET /metrics` - Aggregated metrics from all services
- `GET /events` - Recent events from all services
- `GET /system/health` - Overall system health

### Transaction Service (Port 8081)
- `GET /health` - Service health
- `GET /metrics` - Transaction metrics
- `GET /transactions/events` - Generated transaction events
- `POST /transactions` - Create test transaction
- `GET /config` - Current configuration
- `POST /config` - Update configuration

### Authentication Service (Port 8082)
- `GET /health` - Service health
- `GET /metrics` - Authentication metrics
- `GET /auth/events` - Generated auth events
- `POST /auth` - Create test authentication
- `GET /security/failed-attempts` - Failed login tracking
- `GET /config` - Current configuration
- `POST /config` - Update configuration

### Monitoring Service (Port 8083)
- `GET /health` - Service health
- `GET /metrics` - Monitoring metrics
- `GET /metrics/events` - Generated monitoring events
- `GET /system/health` - System health status
- `GET /system/metrics` - Current system metrics
- `GET /dashboard` - Monitoring dashboard
- `GET /config` - Current configuration
- `POST /config` - Update configuration

## Anomaly Scenarios

### Transaction Anomalies
1. **Suspicious High Amount**: Transactions > $10,000
2. **Fraud Patterns**: Multiple small transactions to same merchant
3. **Money Laundering**: Round amounts across multiple accounts

### Authentication Anomalies
1. **Brute Force**: Multiple failed attempts for same username
2. **Credential Stuffing**: Low success rate with many attempts
3. **Unusual Location**: Login from impossible geographic locations

### Monitoring Anomalies
1. **Resource Exhaustion**: CPU/Memory/Disk > 90%
2. **Cascade Failures**: Multiple services failing simultaneously
3. **Performance Degradation**: Gradual increase in response times

## Deployment

### Local Development with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### EC2 Deployment

Use the provided deployment script:

```bash
cd scripts
./deploy_ec2.sh
```

This script:
- Creates EC2 security groups
- Launches t2.micro instances (free tier)
- Installs Docker and dependencies
- Deploys all mock services
- Configures monitoring and logging

### AWS Deployment with Terraform

1. **Switch to AWS environment**:
```bash
cd ../config
./switch_environment.sh dev
```

2. **Initialize and apply Terraform**:
```bash
terraform init
terraform plan
terraform apply
```

3. **Deploy services to EC2**:
```bash
cd ../00-mock-servers/scripts
./deploy_ec2.sh
```

## Environment Switching

Use the environment switcher to toggle between LocalStack and AWS:

```bash
# Switch to LocalStack (local development)
./switch_environment.sh local

# Switch to AWS development
./switch_environment.sh dev

# Switch to AWS staging
./switch_environment.sh staging

# Switch to AWS production
./switch_environment.sh prod

# Show current environment
./switch_environment.sh show
```

## Monitoring and Observability

### Health Monitoring
All services expose `/health` endpoints with:
- Service status
- Uptime metrics
- Error rates
- Performance metrics

### Metrics Collection
- Response times and error rates
- Anomaly detection rates
- Event generation statistics
- Resource utilization

### Logging
- Structured JSON logging
- Request/response tracking
- Error logging with stack traces
- Performance metrics

## Testing

### Unit Testing
```bash
cd services/transaction-service
python -m pytest tests/
```

### Integration Testing
```bash
# Test service communication
curl http://localhost:8080/services/transaction-service/health

# Test event aggregation
curl http://localhost:8080/events | jq '.events | length'
```

### Load Testing
```bash
# Increase event generation rate
curl -X POST http://localhost:8081/config \
  -H "Content-Type: application/json" \
  -d '{"anomaly_rate": 0.1}'

# Monitor system performance
watch -n 5 'curl http://localhost:8080/dashboard'
```

## Data Schema

### Transaction Event
```json
{
  "transaction_id": "uuid",
  "timestamp": "ISO datetime",
  "customer_id": "CUST_123456",
  "amount": 250.50,
  "currency": "USD",
  "transaction_type": "purchase",
  "risk_score": 0.15,
  "anomaly_type": "suspicious_high_amount"
}
```

### Authentication Event
```json
{
  "event_id": "uuid",
  "timestamp": "ISO datetime",
  "customer_id": "CUST_123456",
  "result": "success|failure",
  "ip_address": "192.168.1.1",
  "location": {"country": "US", "city": "New York"},
  "anomaly_type": "brute_force"
}
```

### Monitoring Event
```json
{
  "event_id": "uuid",
  "timestamp": "ISO datetime",
  "service": "transaction-service",
  "metric_name": "cpu_utilization",
  "metric_value": 85.5,
  "unit": "percent",
  "anomaly_type": "high_cpu"
}
```

## Troubleshooting

### Common Issues

1. **Services not starting**:
   - Check port conflicts: `netstat -tulpn | grep :808`
   - Verify Docker: `docker ps`
   - Check logs: `docker-compose logs service-name`

2. **High memory usage**:
   - Reduce event generation rate
   - Increase batch processing size
   - Monitor with: `docker stats`

3. **Network connectivity**:
   - Verify service discovery: `curl http://localhost:8080/system/health`
   - Check inter-service communication
   - Review security group settings (AWS)

### Performance Tuning

1. **Event Generation Rate**:
   - Adjust `events_per_second` in config
   - Monitor system resources
   - Scale horizontally with more instances

2. **Anomaly Detection**:
   - Fine-tune anomaly rates per service
   - Monitor false positive rates
   - Adjust thresholds based on feedback

3. **Resource Optimization**:
   - Use appropriate instance types
   - Enable auto-scaling in production
   - Monitor CloudWatch metrics

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Join the discussion forums
