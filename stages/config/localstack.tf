# LocalStack Configuration for Local Development

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Configure AWS provider for LocalStack
provider "aws" {
  region = var.region
  
  # LocalStack configuration
  access_key = "test"
  secret_key = "test"
  
  endpoints {
    s3       = "http://${var.localstack_host}:${var.localstack_edge_port}"
    kinesis  = "http://${var.localstack_host}:${var.localstack_edge_port}"
    lambda   = "http://${var.localstack_host}:${var.localstack_edge_port}"
    iam      = "http://${var.localstack_host}:${var.localstack_edge_port}"
    cloudwatch = "http://${var.localstack_host}:${var.localstack_edge_port}"
    sqs      = "http://${var.localstack_host}:${var.localstack_edge_port}"
    sns      = "http://${var.localstack_host}:${var.localstack_edge_port}"
    dynamodb = "http://${var.localstack_host}:${var.localstack_edge_port}"
    events   = "http://${var.localstack_host}:${var.localstack_edge_port}"
    sts      = "http://${var.localstack_host}:${var.localstack_edge_port}"
    
    # Skip credentials validation for LocalStack
    skip_credentials_validation = true
    skip_metadata_api_check = true
    skip_requesting_account_id = true
  }
  
  default_tags {
    tags = var.tags
  }
}

# LocalStack-specific resources
resource "local_file" "localstack_config" {
  content = templatefile("${path.module}/localstack.yml.tpl", {
    project_name = var.project_name
    environment  = var.environment
    region       = var.region
  })
  filename = "${path.root}/../docker/localstack.yml"
}

# S3 Buckets for LocalStack
resource "aws_s3_bucket" "raw_logs" {
  count = var.s3_buckets_enabled ? 1 : 0
  
  bucket = "${var.project_name}-raw-logs-${var.environment}"
  
  tags = merge(var.tags, {
    Purpose = "raw-logs"
    Type = "storage"
  })
}

resource "aws_s3_bucket" "raw_metrics" {
  count = var.s3_buckets_enabled ? 1 : 0
  
  bucket = "${var.project_name}-raw-metrics-${var.environment}"
  
  tags = merge(var.tags, {
    Purpose = "raw-metrics"
    Type = "storage"
  })
}

resource "aws_s3_bucket" "transformed_data" {
  count = var.s3_buckets_enabled ? 1 : 0
  
  bucket = "${var.project_name}-transformed-data-${var.environment}"
  
  tags = merge(var.tags, {
    Purpose = "transformed-data"
    Type = "storage"
  })
}

# Kinesis Streams for LocalStack
resource "aws_kinesis_stream" "logs_stream" {
  count = var.kinesis_enabled ? 1 : 0
  
  name = "${var.project_name}-logs-stream-${var.environment}"
  shard_count = var.kinesis_shard_count
  
  tags = var.tags
}

resource "aws_kinesis_stream" "metrics_stream" {
  count = var.kinesis_enabled ? 1 : 0
  
  name = "${var.project_name}-metrics-stream-${var.environment}"
  shard_count = var.kinesis_shard_count
  
  tags = var.tags
}

# Lambda Functions for LocalStack
resource "aws_iam_role" "lambda_role" {
  count = var.lambda_enabled ? 1 : 0
  
  name = "${var.project_name}-lambda-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  count = var.lambda_enabled ? 1 : 0
  
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role = aws_iam_role.lambda_role[0].name
}

# SQS Queues for LocalStack
resource "aws_sqs_queue" "anomaly_queue" {
  count = var.lambda_enabled ? 1 : 0
  
  name = "${var.project_name}-anomaly-queue-${var.environment}"
  
  tags = var.tags
}

# CloudWatch Log Groups for LocalStack
resource "aws_cloudwatch_log_group" "lambda_logs" {
  count = var.lambda_enabled ? 1 : 0
  
  name = "/aws/lambda/${var.project_name}-${var.environment}"
  
  retention_in_days = 7
  
  tags = var.tags
}

# DynamoDB Tables for LocalStack
resource "aws_dynamodb_table" "anomaly_records" {
  count = var.lambda_enabled ? 1 : 0
  
  name = "${var.project_name}-anomaly-records-${var.environment}"
  
  billing_mode = "PAY_PER_REQUEST"
  
  hash_key = "anomaly_id"
  
  attribute {
    name = "anomaly_id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "S"
  }
  
  global_secondary_index {
    name = "timestamp_index"
    hash_key = "timestamp"
    projection_type = "ALL"
  }
  
  tags = var.tags
}

# Output configuration for LocalStack
output "localstack_endpoints" {
  description = "LocalStack service endpoints"
  value = {
    s3       = "http://${var.localstack_host}:${var.localstack_edge_port}"
    kinesis  = "http://${var.localstack_host}:${var.localstack_edge_port}"
    lambda   = "http://${var.localstack_host}:${var.localstack_edge_port}"
    sqs      = "http://${var.localstack_host}:${var.localstack_edge_port}"
    cloudwatch = "http://${var.localstack_host}:${var.localstack_edge_port}"
  }
}

output "s3_buckets" {
  description = "S3 bucket names"
  value = {
    raw_logs = var.s3_buckets_enabled ? aws_s3_bucket.raw_logs[0].bucket : null
    raw_metrics = var.s3_buckets_enabled ? aws_s3_bucket.raw_metrics[0].bucket : null
    transformed_data = var.s3_buckets_enabled ? aws_s3_bucket.transformed_data[0].bucket : null
  }
}

output "kinesis_streams" {
  description = "Kinesis stream names"
  value = {
    logs_stream = var.kinesis_enabled ? aws_kinesis_stream.logs_stream[0].name : null
    metrics_stream = var.kinesis_enabled ? aws_kinesis_stream.metrics_stream[0].name : null
  }
}

output "sqs_queues" {
  description = "SQS queue URLs"
  value = {
    anomaly_queue = var.lambda_enabled ? aws_sqs_queue.anomaly_queue[0].id : null
  }
}
