# --- VPC setup ---
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "${var.project}-vpc"
  }
}

resource "aws_subnet" "subnet_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  tags = {
    Name = "${var.project}-subnet-a"
  }
}

# Redis subnet group & SG
resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "${var.project}-subnet-group"
  subnet_ids = [aws_subnet.subnet_a.id]
}

# Security group — restrict to internal VPC
resource "aws_security_group" "redis_sg" {
  name   = "${var.project}-redis-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]  # restrict to VPC only
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project
  }
}
