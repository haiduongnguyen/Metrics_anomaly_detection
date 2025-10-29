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
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Backend configuration for state management
  backend "local" {
    path = "./terraform.tfstate"
  }
}

# Provider configuration based on workspace
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "banking-mock-server"
      Environment = terraform.workspace
      ManagedBy   = "terraform"
    }
  }
}

# LocalStack provider for local workspace
provider "aws" {
  alias  = "localstack"
  region = var.aws_region

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
    iam = "http://localhost:4566"
  }

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  default_tags {
    tags = {
      Project     = "banking-mock-server"
      Environment = "${terraform.workspace}-localstack"
      ManagedBy   = "terraform"
    }
  }
}

# Random resources for unique naming
resource "random_pet" "instance_name" {
  prefix = "banking-mock"
  length = 2
}

# Data sources
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Local variables for workspace-specific configuration
locals {
  is_local_workspace = terraform.workspace == "local"
  is_aws_workspace   = terraform.workspace == "aws"

  instance_type = local.is_local_workspace ? var.local_instance_type : var.aws_instance_type
  provider_name = local.is_local_workspace ? "aws.localstack" : "aws"

  common_tags = {
    Project     = "banking-mock-server"
    Environment = terraform.workspace
    ManagedBy   = "terraform"
    Name        = "${random_pet.instance_name.id}-mock-server"
  }
}

# VPC configuration (only for AWS workspace)
resource "aws_vpc" "main" {
  count = local.is_aws_workspace ? 1 : 0

  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${random_pet.instance_name.id}-vpc"
  })
}

# Internet Gateway (only for AWS workspace)
resource "aws_internet_gateway" "main" {
  count = local.is_aws_workspace ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  tags = merge(local.common_tags, {
    Name = "${random_pet.instance_name.id}-igw"
  })
}

# Public Subnet (only for AWS workspace)
resource "aws_subnet" "public" {
  count = local.is_aws_workspace ? 1 : 0

  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${random_pet.instance_name.id}-public-subnet"
  })
}

# Route Table (only for AWS workspace)
resource "aws_route_table" "public" {
  count = local.is_aws_workspace ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${random_pet.instance_name.id}-rt"
  })
}

# Route Table Association (only for AWS workspace)
resource "aws_route_table_association" "public" {
  count = local.is_aws_workspace ? 1 : 0

  subnet_id      = aws_subnet.public[0].id
  route_table_id = aws_route_table.public[0].id
}

# Security Group
resource "aws_security_group" "mock_server" {
  provider    = local.provider_name
  name_prefix = "${random_pet.instance_name.id}-sg"
  description = "Security group for banking mock server"

  # Allow SSH from specific IP ranges
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr_blocks
    description = "SSH access"
  }

  # Allow HTTP from anywhere
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Mock server API"
  }

  # Allow health checks
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Health check access"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

# EC2 Instance Profile and IAM Role
resource "aws_iam_role" "mock_server_role" {
  provider    = local.provider_name
  name_prefix = "${random_pet.instance_name.id}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  provider   = local.provider_name
  role       = aws_iam_role.mock_server_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "mock_server_profile" {
  provider    = local.provider_name
  name_prefix = "${random_pet.instance_name.id}-profile"
  role        = aws_iam_role.mock_server_role.name
}

# EC2 Key Pair (for AWS workspace)
resource "aws_key_pair" "deployer" {
  count    = local.is_aws_workspace ? 1 : 0
  provider = local.provider_name

  key_name_prefix = "${random_pet.instance_name.id}-key"
  public_key      = var.public_key

  tags = local.common_tags
}

# EC2 Instance
resource "aws_instance" "mock_server" {
  provider                    = local.provider_name
  ami                         = data.aws_ami.amazon_linux_2.id
  instance_type               = local.instance_type
  key_name                    = local.is_aws_workspace ? aws_key_pair.deployer[0].key_name : null
  iam_instance_profile        = aws_iam_instance_profile.mock_server_profile.name
  vpc_security_group_ids      = [aws_security_group.mock_server.id]
  associate_public_ip_address = true

  # User data script to install Docker and run the mock server
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    docker_image   = var.docker_image
    server_port    = var.server_port
    config_content = fileexists("${path.cwd}/00-mock-servers/config.yaml") ? file("${path.cwd}/00-mock-servers/config.yaml") : ""
  }))

  tags = local.common_tags

  # Volume for logs and data
  root_block_device {
    volume_size           = 20
    volume_type           = "gp2"
    delete_on_termination = true
    encrypted             = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Availability Zones data source
data "aws_availability_zones" "available" {
  provider = local.provider_name
  state    = "available"
}


