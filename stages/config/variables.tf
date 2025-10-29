variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_instance_type" {
  description = "EC2 instance type for AWS deployment"
  type        = string
  default     = "t3.micro"
}

variable "local_instance_type" {
  description = "Instance type for LocalStack deployment"
  type        = string
  default     = "t2.micro"
}

variable "docker_image" {
  description = "Docker image for the mock server"
  type        = string
  default     = "banking-mock-server:latest"
}

variable "server_port" {
  description = "Port for the mock server API"
  type        = number
  default     = 8000
}

variable "public_key" {
  description = "SSH public key for EC2 access"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "banking-mock-server"
}
