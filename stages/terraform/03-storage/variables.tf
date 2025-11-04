variable "project" {
  default = "vpbank-anomaly-storage"
}

variable "aws_region" {
  default = "ap-southeast-1"
}

variable "hot_cache_node_type" {
  default = "cache.t3.micro"
}

variable "s3_retention_days" {
  default = 30
}

# 🔒 No default password!  Load from AWS Secrets Manager instead
variable "redis_auth_token_secret_name" {
  description = "Secrets Manager name containing Redis AUTH token"
  type        = string
}

variable "redis_auth_token" {
  description = "Auth token (password) for ElastiCache Redis. Must be 16–128 characters."
  type        = string
  sensitive   = true
}