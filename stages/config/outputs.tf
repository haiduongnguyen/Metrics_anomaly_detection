# Terraform Outputs Configuration

# Environment Information
output "environment_info" {
  description = "Environment configuration information"
  value = {
    environment = var.environment
    region = var.region
    project_name = var.project_name
    localstack_enabled = var.localstack_enabled
    aws_enabled = var.aws_enabled
  }
}

# Service Endpoints
output "service_endpoints" {
  description = "Service endpoints and URLs"
  value = {
    # LocalStack endpoints (if enabled)
    localstack = var.localstack_enabled ? {
      s3 = "http://${var.localstack_host}:${var.localstack_edge_port}"
      kinesis = "http://${var.localstack_host}:${var.localstack_edge_port}"
      lambda = "http://${var.localstack_host}:${var.localstack_edge_port}"
      sqs = "http://${var.localstack_host}:${var.localstack_edge_port}"
      cloudwatch = "http://${var.localstack_host}:${var.localstack_edge_port}"
    } : null
    
    # Mock service endpoints
    mock_services = {
      api_gateway = "http://localhost:8080"
      transaction_service = "http://localhost:8081"
      auth_service = "http://localhost:8082"
      monitoring_service = "http://localhost:8083"
    }
  }
}

# Storage Information
output "storage_info" {
  description = "Storage buckets and filesystem information"
  value = {
    # S3 buckets (if enabled)
    s3_buckets = var.s3_buckets_enabled ? {
      raw_logs = var.localstack_enabled ? "${var.project_name}-raw-logs-${var.environment}" : null
      raw_metrics = var.localstack_enabled ? "${var.project_name}-raw-metrics-${var.environment}" : null
      transformed_data = var.localstack_enabled ? "${var.project_name}-transformed-data-${var.environment}" : null
    } : null
    
    # Local storage paths
    local_storage = {
      config_path = "${path.root}/../00-mock-servers/config"
      logs_path = "${path.root}/../logs"
      data_path = "${path.root}/../data"
    }
  }
}

# Streaming Information
output "streaming_info" {
  description = "Streaming and messaging information"
  value = {
    # Kinesis streams (if enabled)
    kinesis_streams = var.kinesis_enabled && var.localstack_enabled ? {
      logs_stream = "${var.project_name}-logs-stream-${var.environment}"
      metrics_stream = "${var.project_name}-metrics-stream-${var.environment}"
    } : null
    
    # SQS queues (if enabled)
    sqs_queues = var.lambda_enabled && var.localstack_enabled ? {
      anomaly_queue = "${var.project_name}-anomaly-queue-${var.environment}"
    } : null
  }
}

# Compute Information
output "compute_info" {
  description = "Compute and processing information"
  value = {
    # Lambda functions (if enabled)
    lambda_functions = var.lambda_enabled ? {
      role_name = var.localstack_enabled ? "${var.project_name}-lambda-role-${var.environment}" : null
      log_group = var.localstack_enabled ? "/aws/lambda/${var.project_name}-${var.environment}" : null
    } : null
    
    # Mock services
    mock_services = {
      transaction_service = {
        port = 8081
        health_endpoint = "/health"
        metrics_endpoint = "/metrics"
      }
      auth_service = {
        port = 8082
        health_endpoint = "/health"
        metrics_endpoint = "/metrics"
      }
      monitoring_service = {
        port = 8083
        health_endpoint = "/health"
        metrics_endpoint = "/metrics"
      }
      api_gateway = {
        port = 8080
        health_endpoint = "/health"
        dashboard_endpoint = "/dashboard"
      }
    }
  }
}

# Database Information
output "database_info" {
  description = "Database and cache information"
  value = {
    # Redis/ElastiCache (if enabled)
    redis = var.redis_enabled ? {
      endpoint = var.localstack_enabled ? "localhost:6379" : null
      port = var.redis_port
      node_type = var.redis_node_type
    } : null
  }
}

# Monitoring Information
output "monitoring_info" {
  description = "Monitoring and observability information"
  value = {
    # CloudWatch (if enabled)
    cloudwatch = var.cloudwatch_enabled && var.localstack_enabled ? {
      log_group = "/aws/lambda/${var.project_name}-${var.environment}"
      region = var.region
    } : null
    
    # Grafana (if using Docker)
    grafana = {
      url = "http://localhost:3000"
      username = "admin"
      password = "admin"
    }
  }
}

# Networking Information
output "networking_info" {
  description = "Networking and connectivity information"
  value = {
    # VPC information (AWS only)
    vpc = var.create_vpc && var.aws_enabled ? {
      vpc_id = aws_vpc.main.id
      public_subnet_ids = aws_subnet.public[*].id
      private_subnet_ids = aws_subnet.private[*].id
      internet_gateway_id = aws_internet_gateway.main.id
    } : null
    
    # Security groups
    security_groups = var.aws_enabled ? {
      lambda_sg = var.lambda_enabled ? aws_security_group.lambda[0].id : null
      redis_sg = var.redis_enabled ? aws_security_group.redis[0].id : null
    } : null
  }
}

# Configuration Files
output "config_files" {
  description = "Paths to important configuration files"
  value = {
    anomaly_config = "${path.root}/../00-mock-servers/config/anomaly_config.json"
    banking_scenarios = "${path.root}/../00-mock-servers/config/banking_scenarios.json"
    docker_compose = "${path.root}/../00-mock-servers/docker/docker-compose.yml"
    terraform_vars = "${path.root}/terraform.tfvars"
  }
}

# Deployment Commands
output "deployment_commands" {
  description = "Useful commands for deployment and management"
  value = {
    # Local development commands
    local_development = {
      start_services = "cd ../00-mock-servers && docker-compose up -d"
      stop_services = "cd ../00-mock-servers && docker-compose down"
      view_logs = "cd ../00-mock-servers && docker-compose logs -f"
      deploy_localstack = "docker run -d -p 4566:4566 localstack/localstack"
    }
    
    # Terraform commands
    terraform = {
      init = "terraform init"
      plan = "terraform plan"
      apply = "terraform apply"
      destroy = "terraform destroy"
      output = "terraform output"
    }
    
    # Testing commands
    testing = {
      health_check = "curl http://localhost:8080/health"
      get_metrics = "curl http://localhost:8080/metrics"
      get_events = "curl http://localhost:8080/events"
      dashboard = "curl http://localhost:8080/dashboard"
    }
  }
}
