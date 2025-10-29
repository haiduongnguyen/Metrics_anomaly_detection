#!/bin/bash

# Banking Mock Services EC2 Deployment Script
# Deploys mock banking services on EC2 free-tier instances

set -e

# Configuration
REGION="us-east-1"
INSTANCE_TYPE="t2.micro"
AMI_ID="ami-0c02fb55956c7d316"  # Amazon Linux 2
KEY_NAME="banking-mock-key"
SECURITY_GROUP_NAME="banking-mock-sg"
INSTANCE_PROFILE_NAME="banking-mock-profile"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    log_info "Dependencies check passed."
}

# Create SSH key pair
create_key_pair() {
    log_info "Creating SSH key pair..."
    
    if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
        log_warn "Key pair $KEY_NAME already exists. Skipping creation."
    else
        aws ec2 create-key-pair \
            --key-name "$KEY_NAME" \
            --region "$REGION" \
            --query 'KeyMaterial' \
            --output text > "${KEY_NAME}.pem"
        
        chmod 400 "${KEY_NAME}.pem"
        log_info "Key pair created and saved as ${KEY_NAME}.pem"
    fi
}

# Create security group
create_security_group() {
    log_info "Creating security group..."
    
    # Check if security group already exists
    SG_ID=$(aws ec2 describe-security-groups \
        --group-names "$SECURITY_GROUP_NAME" \
        --region "$REGION" \
        --query 'SecurityGroups[0].GroupId' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$SG_ID" ]; then
        log_warn "Security group $SECURITY_GROUP_NAME already exists (ID: $SG_ID)."
    else
        SG_ID=$(aws ec2 create-security-group \
            --group-name "$SECURITY_GROUP_NAME" \
            --description "Security group for banking mock services" \
            --region "$REGION" \
            --query 'GroupId' \
            --output text)
        
        log_info "Security group created with ID: $SG_ID"
        
        # Add inbound rules
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 22 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"
        
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 8080 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"
        
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 8081 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"
        
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 8082 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"
        
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port 8083 \
            --cidr 0.0.0.0/0 \
            --region "$REGION"
        
        log_info "Security group rules added."
    fi
    
    echo "$SG_ID"
}

# Create IAM role for EC2
create_iam_role() {
    log_info "Creating IAM role for EC2..."
    
    # Check if role already exists
    if aws iam get-role --role-name "$INSTANCE_PROFILE_NAME" &>/dev/null; then
        log_warn "IAM role $INSTANCE_PROFILE_NAME already exists."
    else
        # Create trust policy
        cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
        
        # Create role
        aws iam create-role \
            --role-name "$INSTANCE_PROFILE_NAME" \
            --assume-role-policy-document file://trust-policy.json \
            --description "Role for banking mock services EC2 instances"
        
        # Attach CloudWatch agent policy (for monitoring)
        aws iam attach-role-policy \
            --role-name "$INSTANCE_PROFILE_NAME" \
            --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
        
        # Create instance profile
        aws iam create-instance-profile --instance-profile-name "$INSTANCE_PROFILE_NAME"
        
        # Add role to instance profile
        aws iam add-role-to-instance-profile \
            --instance-profile-name "$INSTANCE_PROFILE_NAME" \
            --role-name "$INSTANCE_PROFILE_NAME"
        
        log_info "IAM role and instance profile created."
        
        # Clean up
        rm -f trust-policy.json
    fi
}

# Launch EC2 instances
launch_instances() {
    local SG_ID=$1
    log_info "Launching EC2 instances..."
    
    # User data script to install Docker and run services
    cat > user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y docker git
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /home/ec2-user/banking-mock
cd /home/ec2-user/banking-mock

# Clone or copy the application (in real scenario, this would be from Git)
# For now, we'll create a simple docker-compose.yml
cat > docker-compose.yml << 'DOCKERFILE'
version: '3.8'

services:
  transaction-service:
    image: python:3.11-slim
    command: |
      sh -c "
      pip install flask requests numpy &&
      cat > app.py << 'APP'
import json, random, time, uuid
from flask import Flask, jsonify
from datetime import datetime
import threading

app = Flask(__name__)

class TransactionService:
    def __init__(self):
        self.metrics = {'transactions_processed': 0, 'anomalies_detected': 0}
        self.running = True
        
    def generate_transaction(self):
        return {
            'transaction_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'service': 'transaction-service',
            'amount': round(random.gauss(250, 150), 2),
            'anomaly_type': 'suspicious' if random.random() < 0.02 else None
        }

service = TransactionService()

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'metrics': service.metrics})

@app.route('/metrics')
def metrics():
    return jsonify({'service': 'transaction-service', 'metrics': service.metrics})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
APP
      python app.py
      "
    ports:
      - "8081:8081"
    restart: unless-stopped

  auth-service:
    image: python:3.11-slim
    command: |
      sh -c "
      pip install flask requests numpy &&
      cat > app.py << 'APP'
import json, random, time, uuid
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

class AuthService:
    def __init__(self):
        self.metrics = {'auth_attempts': 0, 'anomalies_detected': 0}

service = AuthService()

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'metrics': service.metrics})

@app.route('/metrics')
def metrics():
    return jsonify({'service': 'auth-service', 'metrics': service.metrics})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
APP
      python app.py
      "
    ports:
      - "8082:8082"
    restart: unless-stopped

  monitoring-service:
    image: python:3.11-slim
    command: |
      sh -c "
      pip install flask requests numpy &&
      cat > app.py << 'APP'
import json, random, time, uuid
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

class MonitoringService:
    def __init__(self):
        self.metrics = {'metrics_generated': 0, 'anomalies_detected': 0}

service = MonitoringService()

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'metrics': service.metrics})

@app.route('/metrics')
def metrics():
    return jsonify({'service': 'monitoring-service', 'metrics': service.metrics})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083)
APP
      python app.py
      "
    ports:
      - "8083:8083"
    restart: unless-stopped

  api-gateway:
    image: python:3.11-slim
    command: |
      sh -c "
      pip install flask requests numpy &&
      cat > app.py << 'APP'
import json, requests
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'api-gateway'})

@app.route('/dashboard')
def dashboard():
    return jsonify({'timestamp': datetime.now().isoformat(), 'status': 'running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
APP
      python app.py
      "
    ports:
      - "8080:8080"
    restart: unless-stopped
DOCKERFILE

# Start services
docker-compose up -d

echo "Banking mock services deployed successfully!"
EOF
        
        # Launch instances
        INSTANCE_IDS=$(aws ec2 run-instances \
            --image-id "$AMI_ID" \
            --instance-type "$INSTANCE_TYPE" \
            --key-name "$KEY_NAME" \
            --security-group-ids "$SG_ID" \
            --iam-instance-profile Name="$INSTANCE_PROFILE_NAME" \
            --user-data file://user-data.sh \
            --count 2 \
            --region "$REGION" \
            --query 'Instances[*].InstanceId' \
            --output text)
        
        log_info "EC2 instances launched: $INSTANCE_IDS"
        
        # Wait for instances to be running
        log_info "Waiting for instances to be in running state..."
        for INSTANCE_ID in $INSTANCE_IDS; do
            aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
            log_info "Instance $INSTANCE_ID is now running."
        done
        
        # Get public IPs
        log_info "Getting instance public IPs..."
        PUBLIC_IPS=$(aws ec2 describe-instances \
            --instance-ids $INSTANCE_IDS \
            --region "$REGION" \
            --query 'Reservations[*].Instances[*].PublicIpAddress' \
            --output text)
        
        log_info "Instances deployed with public IPs: $PUBLIC_IPS"
        
        # Clean up
        rm -f user-data.sh
        
        echo "$PUBLIC_IPS"
    fi
}

# Main deployment function
main() {
    log_info "Starting Banking Mock Services EC2 Deployment..."
    
    check_dependencies
    create_key_pair
    SG_ID=$(create_security_group)
    create_iam_role
    PUBLIC_IPS=$(launch_instances "$SG_ID")
    
    log_info "Deployment completed successfully!"
    log_info "API Gateway is accessible at:"
    for IP in $PUBLIC_IPS; do
        log_info "  http://$IP:8080/dashboard"
    done
    
    log_info "To connect to instances via SSH:"
    log_info "  ssh -i ${KEY_NAME}.pem ec2-user@<IP_ADDRESS>"
    
    log_info "To stop instances, run:"
    log_info "  aws ec2 terminate-instances --instance-ids <INSTANCE_IDS> --region $REGION"
}

# Run main function
main "$@"
