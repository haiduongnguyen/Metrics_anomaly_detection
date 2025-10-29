#!/bin/bash

# Environment Switching Script
# Switches between LocalStack and AWS configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$CONFIG_DIR")"
ENVIRONMENT_FILE="$CONFIG_DIR/.current_environment"

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

log_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Show current environment
show_current() {
    if [ -f "$ENVIRONMENT_FILE" ]; then
        CURRENT_ENV=$(cat "$ENVIRONMENT_FILE")
        log_info "Current environment: $CURRENT_ENV"
    else
        log_warn "No environment set. Use '$0 <environment>' to set one."
    fi
}

# Validate environment
validate_environment() {
    local env=$1
    case $env in
        local|dev|staging|prod)
            return 0
            ;;
        *)
            log_error "Invalid environment: $env"
            log_info "Valid environments: local, dev, staging, prod"
            return 1
            ;;
    esac
}

# Switch to LocalStack environment
switch_to_local() {
    log_header "Switching to LocalStack Environment"
    
    # Create terraform.tfvars for LocalStack
    cat > "$CONFIG_DIR/terraform.tfvars" << EOF
# LocalStack Configuration
environment = "local"
region = "us-east-1"

localstack_enabled = true
localstack_host = "localhost"
localstack_edge_port = 4566

aws_enabled = false

project_name = "banking-anomaly-detection"
tags = {
    Environment = "local"
    Project = "banking-anomaly-detection"
    Owner = "devops"
}

# Infrastructure Settings
create_vpc = false
s3_buckets_enabled = true
kinesis_enabled = true
lambda_enabled = true
redis_enabled = true
cloudwatch_enabled = true

# Free-tier optimized settings
kinesis_shard_count = 1
lambda_memory_size = 128
lambda_timeout_seconds = 60
redis_node_type = "cache.t3.micro"

# Security
encryption_enabled = true
access_logging_enabled = true
EOF
    
    # Update mock services config for local
    cat > "$PROJECT_ROOT/00-mock-servers/config/anomaly_config.json" << EOF
{
  "anomaly_settings": {
    "global_anomaly_rate": 0.02,
    "transaction_service": {
      "anomaly_rate": 0.015,
      "suspicious_transaction_rate": 0.008,
      "high_amount_transaction_rate": 0.004,
      "fraud_pattern_rate": 0.003,
      "normal_transaction_rate": 0.985
    },
    "auth_service": {
      "anomaly_rate": 0.025,
      "failed_login_rate": 0.015,
      "brute_force_rate": 0.005,
      "unusual_location_rate": 0.005,
      "normal_auth_rate": 0.975
    },
    "monitoring_service": {
      "anomaly_rate": 0.03,
      "high_cpu_rate": 0.01,
      "memory_leak_rate": 0.008,
      "network_timeout_rate": 0.007,
      "disk_space_rate": 0.005,
      "normal_metrics_rate": 0.97
    }
  },
  "banking_metrics": {
    "transaction_amounts": {
      "min": 10.0,
      "max": 50000.0,
      "normal_mean": 250.0,
      "normal_std": 150.0,
      "suspicious_threshold": 10000.0
    },
    "response_times": {
      "min_ms": 50,
      "max_ms": 5000,
      "normal_mean_ms": 200,
      "normal_std_ms": 100,
      "slow_threshold_ms": 1000
    },
    "error_rates": {
      "normal_max": 0.01,
      "warning_threshold": 0.05,
      "critical_threshold": 0.15
    }
  },
  "generation_settings": {
    "events_per_second": 100,
    "batch_size": 50,
    "working_hours_only": false,
    "timezones": ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"],
    "customer_segments": {
      "retail": 0.7,
      "business": 0.25,
      "premium": 0.05
    }
  },
  "infrastructure": {
    "deployment_target": "local",
    "instance_types": {
      "micro": "local",
      "small": "local"
    },
    "use_free_tier": true,
    "max_instances": 1,
    "ports": {
      "transaction_service": 8081,
      "auth_service": 8082,
      "monitoring_service": 8083,
      "api_gateway": 8080
    }
  }
}
EOF
    
    # Save current environment
    echo "local" > "$ENVIRONMENT_FILE"
    
    log_info "LocalStack environment configured successfully!"
    log_info "Next steps:"
    log_info "  1. Start LocalStack: docker run -d -p 4566:4566 localstack/localstack"
    log_info "  2. Initialize Terraform: cd $CONFIG_DIR && terraform init"
    log_info "  3. Apply configuration: terraform apply"
    log_info "  4. Start mock services: cd $PROJECT_ROOT/00-mock-servers && docker-compose up -d"
}

# Switch to AWS environment
switch_to_aws() {
    local env=$1
    log_header "Switching to AWS Environment: $env"
    
    # Create terraform.tfvars for AWS
    cat > "$CONFIG_DIR/terraform.tfvars" << EOF
# AWS Configuration
environment = "$env"
region = "us-east-1"

localstack_enabled = false

aws_enabled = true
aws_profile = "default"
aws_account_id = ""

project_name = "banking-anomaly-detection"
tags = {
    Environment = "$env"
    Project = "banking-anomaly-detection"
    Owner = "devops"
}

# Infrastructure Settings
create_vpc = true
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]

s3_buckets_enabled = true
kinesis_enabled = true
lambda_enabled = true
redis_enabled = true
cloudwatch_enabled = true

# Environment-specific settings
kinesis_shard_count = $([ "$env" = "prod" ] && echo "3" || echo "1")
lambda_memory_size = $([ "$env" = "prod" ] && echo "256" || echo "128")
lambda_timeout_seconds = $([ "$env" = "prod" ] && echo "300" || echo "60")
redis_node_type = $([ "$env" = "prod" ] && echo "cache.t3.small" || echo "cache.t3.micro")

# Data retention
raw_data_retention_days = $([ "$env" = "prod" ] && echo "365" || echo "90")
transformed_data_retention_days = $([ "$env" = "prod" ] && echo "2555" || echo "365")

# Security
encryption_enabled = true
access_logging_enabled = true
EOF
    
    # Update mock services config for AWS
    cat > "$PROJECT_ROOT/00-mock-servers/config/anomaly_config.json" << EOF
{
  "anomaly_settings": {
    "global_anomaly_rate": $([ "$env" = "prod" ] && echo "0.01" || echo "0.02"),
    "transaction_service": {
      "anomaly_rate": $([ "$env" = "prod" ] && echo "0.008" || echo "0.015"),
      "suspicious_transaction_rate": $([ "$env" = "prod" ] && echo "0.004" || echo "0.008"),
      "high_amount_transaction_rate": $([ "$env" = "prod" ] && echo "0.002" || echo "0.004"),
      "fraud_pattern_rate": $([ "$env" = "prod" ] && echo "0.002" || echo "0.003"),
      "normal_transaction_rate": $([ "$env" = "prod" ] && echo "0.992" || echo "0.985")
    },
    "auth_service": {
      "anomaly_rate": $([ "$env" = "prod" ] && echo "0.015" || echo "0.025"),
      "failed_login_rate": $([ "$env" = "prod" ] && echo "0.008" || echo "0.015"),
      "brute_force_rate": $([ "$env" = "prod" ] && echo "0.003" || echo "0.005"),
      "unusual_location_rate": $([ "$env" = "prod" ] && echo "0.004" || echo "0.005"),
      "normal_auth_rate": $([ "$env" = "prod" ] && echo "0.985" || echo "0.975")
    },
    "monitoring_service": {
      "anomaly_rate": $([ "$env" = "prod" ] && echo "0.02" || echo "0.03"),
      "high_cpu_rate": $([ "$env" = "prod" ] && echo "0.008" || echo "0.01"),
      "memory_leak_rate": $([ "$env" = "prod" ] && echo "0.006" || echo "0.008"),
      "network_timeout_rate": $([ "$env" = "prod" ] && echo "0.004" || echo "0.007"),
      "disk_space_rate": $([ "$env" = "prod" ] && echo "0.002" || echo "0.005"),
      "normal_metrics_rate": $([ "$env" = "prod" ] && echo "0.98" || echo "0.97")
    }
  },
  "banking_metrics": {
    "transaction_amounts": {
      "min": 10.0,
      "max": 50000.0,
      "normal_mean": 250.0,
      "normal_std": 150.0,
      "suspicious_threshold": 10000.0
    },
    "response_times": {
      "min_ms": 50,
      "max_ms": 5000,
      "normal_mean_ms": 200,
      "normal_std_ms": 100,
      "slow_threshold_ms": 1000
    },
    "error_rates": {
      "normal_max": 0.01,
      "warning_threshold": 0.05,
      "critical_threshold": 0.15
    }
  },
  "generation_settings": {
    "events_per_second": $([ "$env" = "prod" ] && echo "500" || echo "100"),
    "batch_size": 50,
    "working_hours_only": false,
    "timezones": ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"],
    "customer_segments": {
      "retail": 0.7,
      "business": 0.25,
      "premium": 0.05
    }
  },
  "infrastructure": {
    "deployment_target": "aws",
    "instance_types": {
      "micro": "t2.micro",
      "small": "t2.small"
    },
    "use_free_tier": $([ "$env" = "prod" ] && echo "false" || echo "true"),
    "max_instances": $([ "$env" = "prod" ] && echo "5" || echo "2"),
    "ports": {
      "transaction_service": 8081,
      "auth_service": 8082,
      "monitoring_service": 8083,
      "api_gateway": 8080
    }
  }
}
EOF
    
    # Save current environment
    echo "$env" > "$ENVIRONMENT_FILE"
    
    log_info "AWS $env environment configured successfully!"
    log_info "Next steps:"
    log_info "  1. Configure AWS credentials: aws configure"
    log_info "  2. Initialize Terraform: cd $CONFIG_DIR && terraform init"
    log_info "  3. Plan deployment: terraform plan"
    log_info "  4. Apply configuration: terraform apply"
    log_info "  5. Deploy mock services: cd $PROJECT_ROOT/00-mock-servers/scripts && ./deploy_ec2.sh"
}

# Show help
show_help() {
    echo "Usage: $0 <command> [environment]"
    echo ""
    echo "Commands:"
    echo "  show              Show current environment"
    echo "  local             Switch to LocalStack environment"
    echo "  dev               Switch to AWS development environment"
    echo "  staging           Switch to AWS staging environment"
    echo "  prod              Switch to AWS production environment"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local          Switch to LocalStack"
    echo "  $0 dev            Switch to AWS dev"
    echo "  $0 show           Show current environment"
}

# Main function
main() {
    local command=${1:-show}
    
    case $command in
        show)
            show_current
            ;;
        local)
            switch_to_local
            ;;
        dev|staging|prod)
            validate_environment "$command"
            switch_to_aws "$command"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
