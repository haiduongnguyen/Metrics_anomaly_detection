# AWS Configuration for Production Deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "banking-anomaly-detection-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}

# Configure AWS provider for production
provider "aws" {
  region = var.region
  profile = var.aws_profile
  
  default_tags {
    tags = var.tags
  }
}

# VPC Configuration
resource "aws_vpc" "main" {
  count = var.create_vpc ? 1 : 0
  
  cidr_block = var.vpc_cidr
  
  enable_dns_hostnames = true
  enable_dns_support = true
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-vpc-${var.environment}"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = var.create_vpc ? length(var.public_subnet_cidrs) : 0
  
  vpc_id = aws_vpc.main[0].id
  cidr_block = var.public_subnet_cidrs[count.index]
  
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-public-subnet-${count.index + 1}-${var.environment}"
    Type = "public"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = var.create_vpc ? length(var.private_subnet_cidrs) : 0
  
  vpc_id = aws_vpc.main[0].id
  cidr_block = var.private_subnet_cidrs[count.index]
  
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-private-subnet-${count.index + 1}-${var.environment}"
    Type = "private"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.main[0].id
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-igw-${var.environment}"
  })
}

# Route Tables
resource "aws_route_table" "public" {
  count = var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.main[0].id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-public-rt-${var.environment}"
  })
}

resource "aws_route_table_association" "public" {
  count = var.create_vpc ? length(var.public_subnet_cidrs) : 0
  
  subnet_id = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

# S3 Buckets for AWS
resource "aws_s3_bucket" "raw_logs" {
  count = var.s3_buckets_enabled ? 1 : 0
  
  bucket = "${var.project_name}-raw-logs-${var.environment}"
  
  tags = merge(var.tags, {
    Purpose = "raw-logs"
    Type = "storage"
  })
}

resource "aws_s3_bucket_versioning" "raw_logs" {
  count = var.s3_buckets_enabled && var.encryption_enabled ? 1 : 0
  
  bucket = aws_s3_bucket.raw_logs[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_logs" {
  count = var.s3_buckets_enabled && var.encryption_enabled ? 1 : 0
  
  bucket = aws_s3_bucket.raw_logs[0].id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw_logs" {
  count = var.s3_buckets_enabled ? 1 : 0
  
  bucket = aws_s3_bucket.raw_logs[0].id
  
  rule {
    id = "raw_logs_lifecycle"
    status = "Enabled"
    
    transition {
      days = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days = 60
      storage_class = "GLACIER"
    }
    
    expiration {
      days = var.raw_data_retention_days
    }
  }
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

# Kinesis Streams for AWS
resource "aws_kinesis_stream" "logs_stream" {
  count = var.kinesis_enabled ? 1 : 0
  
  name = "${var.project_name}-logs-stream-${var.environment}"
  shard_count = var.kinesis_shard_count
  
  retention_period = 24
  
  tags = var.tags
}

resource "aws_kinesis_stream" "metrics_stream" {
  count = var.kinesis_enabled ? 1 : 0
  
  name = "${var.project_name}-metrics-stream-${var.environment}"
  shard_count = var.kinesis_shard_count
  
  retention_period = 24
  
  tags = var.tags
}

# ElastiCache Redis for AWS
resource "aws_elasticache_subnet_group" "main" {
  count = var.create_vpc && var.redis_enabled ? 1 : 0
  
  name = "${var.project_name}-subnet-group-${var.environment}"
  description = "ElastiCache subnet group for ${var.project_name}"
  
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "redis" {
  count = var.redis_enabled ? 1 : 0
  
  name = "${var.project_name}-redis-sg-${var.environment}"
  description = "Security group for Redis"
  
  vpc_id = var.create_vpc ? aws_vpc.main[0].id : data.aws_vpc.default.id
  
  ingress {
    from_port = var.redis_port
    to_port = var.redis_port
    protocol = "tcp"
    security_groups = var.lambda_enabled ? [aws_security_group.lambda[0].id] : []
  }
  
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = var.tags
}

resource "aws_elasticache_replication_group" "main" {
  count = var.redis_enabled ? 1 : 0
  
  replication_group_id = "${var.project_name}-redis-${var.environment}"
  description = "Redis cluster for ${var.project_name}"
  
  node_type = var.redis_node_type
  port = var.redis_port
  
  parameter_group_name = "default.redis7"
  
  subnet_group_name = var.create_vpc ? aws_elasticache_subnet_group.main[0].name : null
  security_group_ids = var.redis_enabled ? [aws_security_group.redis[0].id] : []
  
  cluster_mode_enabled = false
  num_cache_clusters = 1
  
  tags = var.tags
}

# Lambda Functions for AWS
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

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  count = var.lambda_enabled && var.s3_buckets_enabled ? 1 : 0
  
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  role = aws_iam_role.lambda_role[0].name
}

resource "aws_iam_role_policy_attachment" "lambda_kinesis" {
  count = var.lambda_enabled && var.kinesis_enabled ? 1 : 0
  
  policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisReadOnlyAccess"
  role = aws_iam_role.lambda_role[0].name
}

resource "aws_security_group" "lambda" {
  count = var.lambda_enabled ? 1 : 0
  
  name = "${var.project_name}-lambda-sg-${var.environment}"
  description = "Security group for Lambda functions"
  
  vpc_id = var.create_vpc ? aws_vpc.main[0].id : data.aws_vpc.default.id
  
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = var.tags
}

# SQS Queues for AWS
resource "aws_sqs_queue" "anomaly_queue" {
  count = var.lambda_enabled ? 1 : 0
  
  name = "${var.project_name}-anomaly-queue-${var.environment}"
  
  visibility_timeout_seconds = 300
  message_retention_period = 1209600  # 14 days
  
  tags = var.tags
}

# CloudWatch for AWS
resource "aws_cloudwatch_log_group" "lambda_logs" {
  count = var.lambda_enabled ? 1 : 0
  
  name = "/aws/lambda/${var.project_name}-${var.environment}"
  
  retention_in_days = 14
  
  tags = var.tags
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_vpc" "default" {
  default = true
}

# Outputs for AWS
output "vpc_id" {
  description = "VPC ID"
  value = var.create_vpc ? aws_vpc.main[0].id : data.aws_vpc.default.id
}

output "subnet_ids" {
  description = "Subnet IDs"
  value = {
    public = var.create_vpc ? aws_subnet.public[*].id : []
    private = var.create_vpc ? aws_subnet.private[*].id : []
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

output "redis_endpoint" {
  description = "Redis endpoint"
  value = var.redis_enabled ? aws_elasticache_replication_group.main[0].primary_endpoint_address : null
}

output "sqs_queues" {
  description = "SQS queue URLs"
  value = {
    anomaly_queue = var.lambda_enabled ? aws_sqs_queue.anomaly_queue[0].id : null
  }
}
