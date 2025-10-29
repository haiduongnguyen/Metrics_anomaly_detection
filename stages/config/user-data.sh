#!/bin/bash
set -e

# Minimal user data script for EC2 deployment

echo "Starting Banking Mock Server setup at $(date)"

# Install Docker
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Create application directory
mkdir -p /opt/banking-mock-server
chown ec2-user:ec2-user /opt/banking-mock-server

# Copy files from S3 or create minimal setup
cat > /opt/banking-mock-server/config.yaml << 'EOF'
global_anomaly_rate: 0.08
log_generation:
  logs_per_second: 10
service_sources:
  - api-gateway
  - transaction-service
  - auth-service
anomaly_scenarios:
  - id: "BANK-001"
    name: "Login Failure Spike"
    type: "Suspicious Transaction"
    enabled: true
    frequency_weight: 40
    severity: "High"
EOF

# Run the mock server container
docker run -d \
  --name banking-mock-server \
  -p 8000:8000 \
  --restart unless-stopped \
  -v /opt/banking-mock-server/config.yaml:/app/config.yaml:ro \
  banking-mock-server:latest

echo "Setup completed at $(date)"
