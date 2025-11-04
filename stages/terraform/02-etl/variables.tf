variable "region" {
  description = "AWS region"
  default     = "ap-southeast-1"
}

variable "lambda_bucket" {
  description = "Name of S3 bucket to store Lambda deployment artifacts"
  default     = "vpbank-hackathon-team36-lambda-artifacts"
}

variable "project" {
  description = "Project name for tagging"
  default     = "VPBank Hackathon 2025"
}

provider "aws" {
  region = var.region
}