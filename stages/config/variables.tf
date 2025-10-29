# Terraform Variables Configuration

variable "environment" {
  description = "Environment name (local, dev, staging, prod)"
  type        = string
  default     = "local"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "banking-anomaly-detection"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "local"
    Project = "banking-anomaly-detection"
    Owner = "devops"
  }
}

# LocalStack Configuration
variable "localstack_enabled" {
  description = "Enable LocalStack for local development"
  type        = bool
  default     = true
}

variable "localstack_host" {
  description = "LocalStack host"
  type        = string
  default     = "localhost"
}

variable "localstack_edge_port" {
  description = "LocalStack edge port"
  type        = number
  default     = 4566
}

# AWS Configuration
variable "aws_enabled" {
  description = "Enable AWS deployment"
  type        = bool
  default     = false
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
  default     = ""
}

variable "aws_profile" {
  description = "AWS CLI profile name"
  type        = string
  default     = "default"
}

# VPC Configuration
variable "create_vpc" {
  description = "Create new VPC (set to false to use default VPC)"
  type        = bool
  default     = true
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# S3 Configuration
variable "s3_buckets_enabled" {
  description = "Enable S3 buckets creation"
  type        = bool
  default     = true
}

variable "raw_data_retention_days" {
  description = "Retention period for raw data in days"
  type        = number
  default     = 90
}

variable "transformed_data_retention_days" {
  description = "Retention period for transformed data in days"
  type        = number
  default     = 365
}

# Kinesis Configuration
variable "kinesis_enabled" {
  description = "Enable Kinesis streams"
  type        = bool
  default     = true
}

variable "kinesis_shard_count" {
  description = "Number of shards for Kinesis streams"
  type        = number
  default     = 1
}

# Lambda Configuration
variable "lambda_enabled" {
  description = "Enable Lambda functions"
  type        = bool
  default     = true
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions (MB)"
  type        = number
  default     = 128
}

variable "lambda_timeout_seconds" {
  description = "Timeout for Lambda functions (seconds)"
  type        = number
  default     = 60
}

# Redis Configuration
variable "redis_enabled" {
  description = "Enable Redis/ElastiCache"
  type        = bool
  default     = true
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

# Monitoring Configuration
variable "cloudwatch_enabled" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "monitoring_interval_seconds" {
  description = "Monitoring interval in seconds"
  type        = number
  default     = 60
}

# Security Configuration
variable "encryption_enabled" {
  description = "Enable encryption for supported services"
  type        = bool
  default     = true
}

variable "access_logging_enabled" {
  description = "Enable access logging"
  type        = bool
  default     = true
}
