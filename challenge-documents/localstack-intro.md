# Hướng dẫn Cấu hình Infrastructure as Code với LocalStack và AWS

## Mục lục

1. [Giới thiệu](#giới-thiệu)
2. [Kiến trúc và Nguyên tắc](#kiến-trúc-và-nguyên-tắc)
3. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
4. [Cài đặt môi trường](#cài-đặt-môi-trường)
5. [Cấu trúc dự án](#cấu-trúc-dự-án)
6. [Cấu hình Terraform](#cấu-hình-terraform)
7. [Triển khai trên LocalStack](#triển-khai-trên-localstack)
8. [Phát triển Application](#phát-triển-application)
9. [Triển khai lên AWS Production](#triển-khai-lên-aws-production)
10. [Testing và Debugging](#testing-và-debugging)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Giới thiệu

### LocalStack là gì?

LocalStack là một framework mô phỏng đầy đủ các dịch vụ AWS trên môi trường local của bạn. Nó cho phép phát triển và test các ứng dụng cloud mà không cần kết nối đến AWS thật, giúp tiết kiệm chi phí và tăng tốc độ phát triển.

### Lợi ích của việc sử dụng LocalStack

**Tiết kiệm chi phí:** Không phải trả phí AWS trong quá trình phát triển và test. Điều này đặc biệt quan trọng khi bạn đang thử nghiệm nhiều configurations hoặc chạy automated tests liên tục.

**Phát triển nhanh hơn:** Không cần chờ đợi resources được provision trên AWS. LocalStack khởi tạo resources gần như tức thì, giúp tăng tốc độ iteration trong quá trình phát triển.

**Offline development:** Có thể làm việc mà không cần kết nối internet. Điều này hữu ích khi bạn đang di chuyển hoặc làm việc ở nơi có kết nối internet không ổn định.

**Môi trường nhất quán:** Mọi developer trong team có thể có môi trường giống hệt nhau. Không còn tình trạng "works on my machine" do khác biệt về môi trường AWS.

**Testing dễ dàng:** Có thể reset và tạo lại môi trường test nhanh chóng. Điều này đặc biệt hữu ích cho integration tests và end-to-end tests.

### Mục tiêu của tài liệu

Tài liệu này hướng dẫn bạn cách setup một môi trường Infrastructure as Code (IaC) sử dụng Terraform và LocalStack, với khả năng chuyển đổi liền mạch sang AWS production mà không cần thay đổi code. Bạn sẽ học cách tổ chức code, cấu hình environments, và deploy applications một cách chuyên nghiệp.

---

## Kiến trúc và Nguyên tắc

### Nguyên tắc thiết kế chính

**Environment Agnostic Code:** Toàn bộ code phải được thiết kế để hoạt động trên cả LocalStack và AWS thật mà không cần sửa đổi logic. Sự khác biệt giữa các môi trường chỉ nằm ở configuration.

**Configuration over Code:** Mọi thông số khác biệt giữa môi trường (endpoints, credentials, regions) phải được quản lý thông qua configuration files hoặc environment variables, không hard-code trong source code.

**Infrastructure as Code:** Sử dụng Terraform để định nghĩa toàn bộ infrastructure, đảm bảo môi trường có thể được tái tạo một cách nhất quán và có thể version control.

**Modular Architecture:** Tổ chức code thành các modules độc lập, tái sử dụng được cho các components khác nhau (S3, DynamoDB, Lambda, etc.).

### Sơ đồ kiến trúc

```
┌─────────────────────────────────────────────────────────┐
│                    Developer Machine                     │
│                                                          │
│  ┌────────────────┐         ┌─────────────────────┐    │
│  │   Application  │────────▶│    LocalStack       │    │
│  │      Code      │         │  (Docker Container) │    │
│  └────────────────┘         └─────────────────────┘    │
│         │                             │                 │
│         │                             │                 │
│  ┌──────▼──────────┐         ┌───────▼────────┐       │
│  │    Terraform    │────────▶│  AWS Services  │       │
│  │  Configuration  │         │   Simulation   │       │
│  └─────────────────┘         └────────────────┘       │
└─────────────────────────────────────────────────────────┘
                      │
                      │ Deploy to Production
                      ▼
         ┌────────────────────────────┐
         │      AWS Cloud (Real)      │
         │                            │
         │  ┌──────┐  ┌──────────┐   │
         │  │  S3  │  │ DynamoDB │   │
         │  └──────┘  └──────────┘   │
         │  ┌──────┐  ┌──────────┐   │
         │  │Lambda│  │   API    │   │
         │  └──────┘  └─Gateway──┘   │
         └────────────────────────────┘
```

---

## Yêu cầu hệ thống

### Phần mềm cần thiết

**Docker và Docker Compose:** LocalStack chạy trong Docker container, đảm bảo môi trường nhất quán và dễ dàng cleanup.

- Docker Desktop (Windows/Mac) hoặc Docker Engine (Linux)
- Docker Compose version 1.27.0 trở lên
- Download tại: https://www.docker.com/products/docker-desktop

**Terraform:** Infrastructure as Code tool chính được sử dụng trong hướng dẫn này.

- Terraform version 1.0.0 trở lên
- Download tại: https://www.terraform.io/downloads

**AWS CLI:** Command line tool để tương tác với AWS và LocalStack.

- AWS CLI version 2.x
- Download tại: https://aws.amazon.com/cli/

**Python 3.8+:** Để cài đặt LocalStack CLI và các tools hỗ trợ.

- Python 3.8 hoặc cao hơn
- pip package manager

**Git:** Version control system để quản lý code.

- Git version 2.x trở lên
- Download tại: https://git-scm.com/

### Cài đặt các tools

**Cài đặt Docker:**

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker-compose --version
```

**Cài đặt Terraform:**

```bash
# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# macOS with Homebrew
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify installation
terraform --version
```

**Cài đặt AWS CLI:**

```bash
# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# macOS
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify installation
aws --version
```

**Cài đặt LocalStack CLI và awslocal:**

```bash
# Install LocalStack CLI
pip install localstack

# Install awslocal (AWS CLI wrapper for LocalStack)
pip install awscli-local

# Verify installation
localstack --version
awslocal --version
```

### Kiểm tra môi trường

Chạy các lệnh sau để đảm bảo tất cả tools đã được cài đặt đúng:

```bash
# Check all required tools
docker --version
docker-compose --version
terraform --version
aws --version
python3 --version
localstack --version
awslocal --version
```

Kết quả mong đợi sẽ hiển thị version của từng tool mà không có lỗi.

---

## Cài đặt môi trường

### Khởi tạo LocalStack với Docker Compose

Tạo file `docker-compose.yml` trong thư mục root của project:

```yaml
services:
  localstack:
    container_name: localstack-main
    image: localstack/localstack:latest
    ports:
      - "4566:4566"            # LocalStack Gateway - điểm truy cập chính
      - "4510-4559:4510-4559"  # External services port range
    environment:
      # Danh sách services cần chạy (để trống = chạy tất cả)
      - SERVICES=s3,dynamodb,lambda,apigateway,sqs,sns,cloudformation,iam,ec2,rds,secretsmanager,cloudwatch,logs
      
      # Debug mode - bật để xem logs chi tiết
      - DEBUG=1
      
      # Thư mục lưu trữ data
      - DATA_DIR=/var/lib/localstack/data
      
      # Lambda executor - sử dụng docker để chạy Lambda functions
      - LAMBDA_EXECUTOR=docker
      - LAMBDA_REMOTE_DOCKER=false
      
      # Docker host socket
      - DOCKER_HOST=unix:///var/run/docker.sock
      
      # AWS Region mặc định
      - AWS_DEFAULT_REGION=us-east-1
      
      # Bật persistence để giữ data khi restart
      - PERSISTENCE=1
      
      # Hostname để Lambda có thể gọi các services khác
      - HOSTNAME_EXTERNAL=localhost
      
    volumes:
      # Mount thư mục để persist data
      - "./localstack-data:/var/lib/localstack"
      
      # Mount Docker socket để LocalStack có thể tạo containers cho Lambda
      - "/var/run/docker.sock:/var/run/docker.sock"
      
    networks:
      - localstack-network

networks:
  localstack-network:
    driver: bridge
```

### Giải thích các cấu hình quan trọng

**SERVICES:** Danh sách các AWS services bạn muốn sử dụng. Để trống hoặc không khai báo sẽ chạy tất cả services available. Chỉ định cụ thể giúp LocalStack khởi động nhanh hơn.

**DEBUG:** Khi set là 1, LocalStack sẽ in ra logs chi tiết, giúp bạn debug khi có vấn đề. Nên bật trong quá trình development.

**PERSISTENCE:** Khi bật, LocalStack sẽ lưu state của các resources vào disk. Khi restart container, các resources sẽ được restore lại. Rất hữu ích để không phải recreate resources mỗi lần restart.

**LAMBDA_EXECUTOR:** Có 3 options: docker (recommended), local, và docker-reuse. Docker executor tạo container riêng cho mỗi Lambda invocation, giống với cách AWS Lambda hoạt động.

**HOSTNAME_EXTERNAL:** Hostname mà Lambda functions sử dụng để gọi các services khác. Thường là localhost hoặc localstack nếu chạy trong Docker network.

### Khởi động LocalStack

```bash
# Start LocalStack
docker-compose up -d

# Xem logs để đảm bảo mọi thứ chạy OK
docker-compose logs -f

# Kiểm tra health status
curl http://localhost:4566/_localstack/health | jq
```

Kết quả health check sẽ hiển thị status của các services:

```json
{
  "services": {
    "s3": "available",
    "dynamodb": "available",
    "lambda": "available",
    ...
  }
}
```

### Cấu hình AWS CLI cho LocalStack

Tạo AWS profile cho LocalStack trong file `~/.aws/config`:

```ini
[profile localstack]
region = us-east-1
output = json
```

Tạo credentials trong file `~/.aws/credentials`:

```ini
[localstack]
aws_access_key_id = test
aws_secret_access_key = test
```

**Lưu ý:** LocalStack không validate credentials, bạn có thể dùng bất kỳ giá trị nào. "test/test" là convention phổ biến.

### Test kết nối với LocalStack

```bash
# Sử dụng awslocal (recommended)
awslocal s3 ls

# Hoặc sử dụng AWS CLI với endpoint override
aws --endpoint-url=http://localhost:4566 s3 ls --profile localstack

# Tạo test bucket
awslocal s3 mb s3://test-bucket

# List lại để verify
awslocal s3 ls
```

Nếu thành công, bạn sẽ thấy bucket vừa tạo trong danh sách.

---

## Cấu trúc dự án

### Tổ chức thư mục

Một cấu trúc project tốt giúp code dễ maintain và scale. Dưới đây là cấu trúc được recommend:

```
aws-localstack-project/
├── README.md
├── .gitignore
├── docker-compose.yml
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── backend.tf
│   │
│   ├── environments/
│   │   ├── local.tfvars
│   │   ├── dev.tfvars
│   │   ├── staging.tfvars
│   │   └── prod.tfvars
│   │
│   └── modules/
│       ├── s3/
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       ├── dynamodb/
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       ├── lambda/
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       └── api-gateway/
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
│
├── src/
│   ├── lambda/
│   │   ├── function1/
│   │   │   ├── index.py
│   │   │   ├── requirements.txt
│   │   │   └── tests/
│   │   │
│   │   └── function2/
│   │       ├── index.js
│   │       ├── package.json
│   │       └── tests/
│   │
│   └── application/
│       ├── app.py
│       ├── config.py
│       ├── requirements.txt
│       └── tests/
│
├── scripts/
│   ├── setup-localstack.sh
│   ├── deploy-local.sh
│   ├── deploy-aws.sh
│   ├── test-local.sh
│   └── cleanup.sh
│
├── tests/
│   ├── integration/
│   └── e2e/
│
└── docs/
    ├── architecture.md
    ├── deployment.md
    └── troubleshooting.md
```

### Giải thích cấu trúc

**Thư mục terraform/:** Chứa toàn bộ Infrastructure as Code definitions. Tổ chức theo modules giúp tái sử dụng code và dễ maintain.

**Thư mục environments/:** Chứa các file .tfvars cho từng môi trường. Mỗi môi trường có configuration riêng nhưng sử dụng chung Terraform code.

**Thư mục modules/:** Chứa các Terraform modules có thể tái sử dụng. Mỗi module đại diện cho một AWS service hoặc một nhóm resources liên quan.

**Thư mục src/:** Chứa application code và Lambda functions. Tách biệt giữa infrastructure code và application code giúp dễ quản lý.

**Thư mục scripts/:** Chứa các automation scripts để deploy, test, và cleanup. Giúp standardize các operations và giảm thiểu manual errors.

**Thư mục tests/:** Chứa integration tests và end-to-end tests. Tách biệt với unit tests trong từng component.

**Thư mục docs/:** Documentation cho project. Bao gồm architecture diagrams, deployment guides, và troubleshooting tips.

### Tạo file .gitignore

```gitignore
# Terraform
**/.terraform/*
*.tfstate
*.tfstate.*
*.tfvars.json
crash.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json
.terraformrc
terraform.rc

# LocalStack data
localstack-data/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log
yarn-error.log
package-lock.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local
*.pem
*.key

# Lambda deployment packages
*.zip
lambda-*.zip

# Logs
*.log
logs/
```

### Tạo README.md

```markdown
# AWS LocalStack Project

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Terraform >= 1.0
- AWS CLI v2
- Python 3.8+

### Setup LocalStack
```bash
docker-compose up -d
```

### Deploy Infrastructure
```bash
cd terraform
terraform init
terraform apply -var-file="environments/local.tfvars"
```

### Run Application
```bash
cd src/application
export USE_LOCALSTACK=true
python app.py
```

## Project Structure
See [docs/architecture.md](docs/architecture.md) for detailed information.

## Deployment
See [docs/deployment.md](docs/deployment.md) for deployment guides.
```

---

## Cấu hình Terraform

### File providers.tf

File này định nghĩa AWS provider và cách nó kết nối với LocalStack hoặc AWS thật:

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Credentials - sử dụng dummy values cho LocalStack
  access_key = var.use_localstack ? "test" : var.aws_access_key
  secret_key = var.use_localstack ? "test" : var.aws_secret_key

  # Skip validations cho LocalStack
  skip_credentials_validation = var.use_localstack
  skip_metadata_api_check     = var.use_localstack
  skip_requesting_account_id  = var.use_localstack

  # Override endpoints khi sử dụng LocalStack
  # Dynamic block chỉ tạo endpoints khi use_localstack = true
  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    
    content {
      apigateway     = "http://localhost:4566"
      apigatewayv2   = "http://localhost:4566"
      cloudformation = "http://localhost:4566"
      cloudwatch     = "http://localhost:4566"
      dynamodb       = "http://localhost:4566"
      ec2            = "http://localhost:4566"
      es             = "http://localhost:4566"
      elasticache    = "http://localhost:4566"
      firehose       = "http://localhost:4566"
      iam            = "http://localhost:4566"
      kinesis        = "http://localhost:4566"
      lambda         = "http://localhost:4566"
      rds            = "http://localhost:4566"
      redshift       = "http://localhost:4566"
      route53        = "http://localhost:4566"
      s3             = "http://s3.localhost.localstack.cloud:4566"
      secretsmanager = "http://localhost:4566"
      ses            = "http://localhost:4566"
      sns            = "http://localhost:4566"
      sqs            = "http://localhost:4566"
      ssm            = "http://localhost:4566"
      stepfunctions  = "http://localhost:4566"
      sts            = "http://localhost:4566"
    }
  }

  # S3 specific configurations cho LocalStack
  s3_use_path_style           = var.use_localstack
  skip_region_validation      = var.use_localstack
}
```

**Giải thích chi tiết:**

Dynamic endpoints block chỉ được tạo khi `use_localstack = true`. Điều này cho phép cùng một provider config hoạt động cho cả LocalStack và AWS thật.

S3 endpoint sử dụng subdomain format `s3.localhost.localstack.cloud` để tương thích tốt hơn với S3 path-style và virtual-hosted-style URLs.

`s3_use_path_style = true` bắt buộc cho LocalStack vì nó không support virtual-hosted-style S3 URLs như AWS thật.

### File variables.tf

```hcl
# Environment Configuration
variable "environment" {
  description = "Environment name (local, dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["local", "dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: local, dev, staging, prod."
  }
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

# AWS Configuration
variable "aws_region" {
  description = "AWS Region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "use_localstack" {
  description = "Use LocalStack for local development"
  type        = bool
  default     = false
}

# AWS Credentials (chỉ dùng cho real AWS)
variable "aws_access_key" {
  description = "AWS Access Key ID (not used in LocalStack)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Access Key (not used in LocalStack)"
  type        = string
  default     = ""
  sensitive   = true
}

# Tagging
variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Feature Flags
variable "enable_versioning" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable encryption for resources"
  type        = bool
  default     = true
}

# Application Specific Variables
variable "lambda_runtime" {
  description = "Lambda function runtime"
  type        = string
  default     = "python3.11"
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 256
  
  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
  
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}
```

**Best practices cho variables:**

Luôn thêm description cho mọi variable để người khác hiểu mục đích sử dụng.

Sử dụng validation blocks để đảm bảo input values hợp lệ trước khi apply.

Mark sensitive variables với `sensitive = true` để Terraform không hiển thị giá trị trong logs.

Cung cấp default values hợp lý cho các variables không bắt buộc.

### File main.tf

```hcl
# Local variables để tính toán các giá trị common
locals {
  # Common naming prefix
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Common tags được merge với custom tags
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    },
    var.tags
  )
}

# S3 Bucket cho data storage
module "data_bucket" {
  source = "./modules/s3"
  
  bucket_name       = "${local.name_prefix}-data"
  enable_versioning = var.enable_versioning
  enable_encryption = var.enable_encryption
  
  tags = local.common_tags
}

# S3 Bucket cho Lambda deployment packages
module "lambda_bucket" {
  source = "./modules/s3"
  
  bucket_name       = "${local.name_prefix}-lambda-deployments"
  enable_versioning = false
  enable_encryption = var.enable_encryption
  
  tags = local.common_tags
}

# DynamoDB Table cho application data
module "users_table" {
  source = "./modules/dynamodb"
  
  table_name     = "${local.name_prefix}-users"
  hash_key       = "userId"
  range_key      = "timestamp"
  billing_mode   = "PAY_PER_REQUEST"
  
  attributes = [
    {
      name = "userId"
      type = "S"
    },
    {
      name = "timestamp"
      type = "N"
    },
    {
      name = "email"
      type = "S"
    }
  ]
  
  global_secondary_indexes = [
    {
      name            = "EmailIndex"
      hash_key        = "email"
      projection_type = "ALL"
    }
  ]
  
  tags = local.common_tags
}

# IAM Role cho Lambda functions
resource "aws_iam_role" "lambda_execution_role" {
  name = "${local.name_prefix}-lambda-execution-role"
  
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
  
  tags = local.common_tags
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy cho Lambda để access DynamoDB và S3
resource "aws_iam_role_policy" "lambda_custom_policy" {
  name = "${local.name_prefix}-lambda-custom-policy"
  role = aws_iam_role.lambda_execution_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          module.users_table.table_arn,
          "${module.users_table.table_arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${module.data_bucket.bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          module.data_bucket.bucket_arn
        ]
      }
    ]
  })
}

# Lambda Function
module "processor_lambda" {
  source = "./modules/lambda"
  
  function_name = "${local.name_prefix}-processor"
  handler       = "index.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout
  
  # Source code
  source_dir  = "${path.root}/../src/lambda/processor"
  output_path = "${path.root}/../build/processor.zip"
  
  # IAM
  role_arn = aws_iam_role.lambda_execution_role.arn
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT    = var.environment
    DYNAMODB_TABLE = module.users_table.table_name
    S3_BUCKET      = module.data_bucket.bucket_name
    USE_LOCALSTACK = var.use_localstack ? "true" : "false"
    AWS_ENDPOINT   = var.use_localstack ? "http://host.docker.internal:4566" : ""
  }
  
  tags = local.common_tags
}

# API Gateway
module "api" {
  source = "./modules/api-gateway"
  
  api_name    = "${local.name_prefix}-api"
  description = "API Gateway for ${var.project_name}"
  
  # Lambda integration
  lambda_function_arn  = module.processor_lambda.function_arn
  lambda_function_name = module.processor_lambda.function_name
  
  tags = local.common_tags
}
```

**Lưu ý quan trọng:**

`AWS_ENDPOINT` trong Lambda environment phải dùng `host.docker.internal:4566` thay vì `localhost:4566` vì Lambda chạy trong Docker container riêng và cần access LocalStack container.

Sử dụng `locals` để tính toán các giá trị common như naming prefix và tags, giúp code DRY hơn.

### File outputs.tf

```hcl
# S3 Outputs
output "data_bucket_name" {
  description = "Name of the data S3 bucket"
  value       = module.data_bucket.bucket_name
}

output "data_bucket_arn" {
  description = "ARN of the data S3 bucket"
  value       = module.data_bucket.bucket_arn
}

output "lambda_bucket_name" {
  description = "Name of the Lambda deployment S3 bucket"
  value       = module.lambda_bucket.bucket_name
}

# DynamoDB Outputs
output "users_table_name" {
  description = "Name of the DynamoDB users table"
  value       = module.users_table.table_name
}

output "users_table_arn" {
  description = "ARN of the DynamoDB users table"
  value       = module.users_table.table_arn
}

# Lambda Outputs
output "processor_lambda_arn" {
  description = "ARN of the processor Lambda function"
  value       = module.processor_lambda.function_arn
}

output "processor_lambda_name" {
  description = "Name of the processor Lambda function"
  value       = module.processor_lambda.function_name
}

# API Gateway Outputs
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api.api_endpoint
}

output "api_id" {
  description = "API Gateway ID"
  value       = module.api.api_id
}

# Environment Info
output "environment" {
  description = "Current environment"
  value       = var.environment
}

output "region" {
  description = "AWS Region"
  value       = var.aws_region
}

output "using_localstack" {
  description = "Whether LocalStack is being used"
  value       = var.use_localstack
}

# Connection Information
output "localstack_endpoint" {
  description = "LocalStack endpoint (if applicable)"
  value       = var.use_localstack ? "http://localhost:4566" : "N/A"
}

# Quick Start Commands
output "quick_start_commands" {
  description = "Useful commands for interacting with deployed resources"
  value = var.use_localstack ? {
    list_s3_buckets       = "awslocal s3 ls"
    list_dynamodb_tables  = "awslocal dynamodb list-tables"
    list_lambda_functions = "awslocal lambda list-functions"
    invoke_lambda         = "awslocal lambda invoke --function-name ${module.processor_lambda.function_name} output.json"
  } : {
    list_s3_buckets       = "aws s3 ls --region ${var.aws_region}"
    list_dynamodb_tables  = "aws dynamodb list-tables --region ${var.aws_region}"
    list_lambda_functions = "aws lambda list-functions --region ${var.aws_region}"
    invoke_lambda         = "aws lambda invoke --function-name ${module.processor_lambda.function_name} output.json --region ${var.aws_region}"
  }
}
```

**Best practices cho outputs:**

Outputs giúp bạn dễ dàng lấy thông tin về resources đã tạo mà không cần vào AWS Console.

Cung cấp cả name và ARN của resources để linh hoạt trong việc sử dụng.

Thêm helpful commands trong outputs để người dùng biết cách interact với resources.

### Environment-specific configurations

**File environments/local.tfvars:**

```hcl
# LocalStack Configuration
use_localstack = true
environment    = "local"
project_name   = "myapp"
aws_region     = "us-east-1"

# Feature flags cho local development
enable_versioning = false  # Tắt versioning để tiết kiệm storage
enable_encryption = false  # LocalStack không cần encryption

# Lambda configuration
lambda_runtime     = "python3.11"
lambda_memory_size = 256
lambda_timeout     = 30

# Tags
tags = {
  Developer = "Your Name"
  Purpose   = "Local Development"
}
```

**File environments/dev.tfvars:**

```hcl
# AWS Development Environment
use_localstack = false
environment    = "dev"
project_name   = "myapp"
aws_region     = "ap-southeast-1"

# Feature flags
enable_versioning = true
enable_encryption = true

# Lambda configuration
lambda_runtime     = "python3.11"
lambda_memory_size = 512
lambda_timeout     = 60

# Tags
tags = {
  CostCenter = "Engineering"
  Team       = "Backend"
}
```

**File environments/prod.tfvars:**

```hcl
# AWS Production Environment
use_localstack = false
environment    = "prod"
project_name   = "myapp"
aws_region     = "ap-southeast-1"

# Feature flags
enable_versioning = true
enable_encryption = true

# Lambda configuration - higher resources for production
lambda_runtime     = "python3.11"
lambda_memory_size = 1024
lambda_timeout     = 300

# Tags
tags = {
  CostCenter  = "Engineering"
  Team        = "Backend"
  Criticality = "High"
  Compliance  = "Required"
}
```

---

## Triển khai trên LocalStack

### Tạo Terraform Modules

Trước khi deploy, chúng ta cần tạo các reusable modules. Dưới đây là các modules cơ bản:

**Module S3 - `modules/s3/main.tf`:**

```hcl
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  
  tags = var.tags
}

resource "aws_s3_bucket_versioning" "this" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.this.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.this.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

**Module S3 - `modules/s3/variables.tf`:**

```hcl
variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "enable_versioning" {
  description = "Enable bucket versioning"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable server-side encryption"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to the bucket"
  type        = map(string)
  default     = {}
}
```

**Module S3 - `modules/s3/outputs.tf`:**

```hcl
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.this.bucket_domain_name
}
```

**Module DynamoDB - `modules/dynamodb/main.tf`:**

```hcl
resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = var.billing_mode
  hash_key     = var.hash_key
  range_key    = var.range_key
  
  # Read/Write capacity chỉ cần khi billing_mode = "PROVISIONED"
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null
  
  # Attributes
  dynamic "attribute" {
    for_each = var.attributes
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }
  
  # Global Secondary Indexes
  dynamic "global_secondary_index" {
    for_each = var.global_secondary_indexes
    content {
      name            = global_secondary_index.value.name
      hash_key        = global_secondary_index.value.hash_key
      range_key       = lookup(global_secondary_index.value, "range_key", null)
      projection_type = global_secondary_index.value.projection_type
      
      read_capacity  = var.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "read_capacity", var.read_capacity) : null
      write_capacity = var.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "write_capacity", var.write_capacity) : null
    }
  }
  
  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  # Server-side encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  tags = var.tags
}
```

**Module DynamoDB - `modules/dynamodb/variables.tf`:**

```hcl
variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "billing_mode" {
  description = "Billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "hash_key" {
  description = "Hash key (partition key)"
  type        = string
}

variable "range_key" {
  description = "Range key (sort key)"
  type        = string
  default     = null
}

variable "attributes" {
  description = "List of attributes"
  type = list(object({
    name = string
    type = string
  }))
}

variable "global_secondary_indexes" {
  description = "List of global secondary indexes"
  type = list(object({
    name            = string
    hash_key        = string
    range_key       = optional(string)
    projection_type = string
    read_capacity   = optional(number)
    write_capacity  = optional(number)
  }))
  default = []
}

variable "read_capacity" {
  description = "Read capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "write_capacity" {
  description = "Write capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = false
}

variable "enable_encryption" {
  description = "Enable server-side encryption"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to the table"
  type        = map(string)
  default     = {}
}
```

**Module DynamoDB - `modules/dynamodb/outputs.tf`:**

```hcl
output "table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.this.name
}

output "table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.this.arn
}

output "table_id" {
  description = "ID of the DynamoDB table"
  value       = aws_dynamodb_table.this.id
}
```

**Module Lambda - `modules/lambda/main.tf`:**

```hcl
# Archive Lambda source code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = var.output_path
}

resource "aws_lambda_function" "this" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.function_name
  role            = var.role_arn
  handler         = var.handler
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = var.runtime
  memory_size     = var.memory_size
  timeout         = var.timeout
  
  environment {
    variables = var.environment_variables
  }
  
  tags = var.tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days
  
  tags = var.tags
}
```

**Module Lambda - `modules/lambda/variables.tf`:**

```hcl
variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "handler" {
  description = "Lambda function handler"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
}

variable "memory_size" {
  description = "Memory size in MB"
  type        = number
  default     = 256
}

variable "timeout" {
  description = "Timeout in seconds"
  type        = number
  default     = 30
}

variable "role_arn" {
  description = "IAM role ARN for Lambda execution"
  type        = string
}

variable "source_dir" {
  description = "Directory containing Lambda source code"
  type        = string
}

variable "output_path" {
  description = "Output path for Lambda zip file"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for Lambda"
  type        = map(string)
  default     = {}
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to Lambda function"
  type        = map(string)
  default     = {}
}
```

**Module Lambda - `modules/lambda/outputs.tf`:**

```hcl
output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.this.arn
}

output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.this.function_name
}

output "invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  value       = aws_lambda_function.this.invoke_arn
}
```

### Tạo Lambda Function Code

Tạo một Lambda function đơn giản để test. Tạo file `src/lambda/processor/index.py`:

```python
import json
import os
import boto3
from datetime import datetime

# Đọc config từ environment variables
USE_LOCALSTACK = os.getenv('USE_LOCALSTACK', 'false').lower() == 'true'
AWS_ENDPOINT = os.getenv('AWS_ENDPOINT', '')
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', '')
S3_BUCKET = os.getenv('S3_BUCKET', '')

# Khởi tạo AWS clients
def get_client(service_name):
    """Tạo boto3 client cho LocalStack hoặc AWS"""
    if USE_LOCALSTACK and AWS_ENDPOINT:
        return boto3.client(
            service_name,
            endpoint_url=AWS_ENDPOINT,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )
    return boto3.client(service_name)

dynamodb = get_client('dynamodb')
s3 = get_client('s3')

def handler(event, context):
    """
    Lambda handler function
    """
    print(f"Event: {json.dumps(event)}")
    print(f"Using LocalStack: {USE_LOCALSTACK}")
    print(f"DynamoDB Table: {DYNAMODB_TABLE}")
    print(f"S3 Bucket: {S3_BUCKET}")
    
    try:
        # Parse input
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        user_id = body.get('userId', 'test-user')
        data = body.get('data', {})
        
        # Current timestamp
        timestamp = int(datetime.now().timestamp())
        
        # Save to DynamoDB
        dynamodb.put_item(
            TableName=DYNAMODB_TABLE,
            Item={
                'userId': {'S': user_id},
                'timestamp': {'N': str(timestamp)},
                'data': {'S': json.dumps(data)},
                'processedAt': {'S': datetime.now().isoformat()}
            }
        )
        print(f"Saved to DynamoDB: userId={user_id}, timestamp={timestamp}")
        
        # Save to S3
        s3_key = f"users/{user_id}/{timestamp}.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps({
                'userId': user_id,
                'timestamp': timestamp,
                'data': data,
                'processedAt': datetime.now().isoformat()
            }),
            ContentType='application/json'
        )
        print(f"Saved to S3: s3://{S3_BUCKET}/{s3_key}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Data processed successfully',
                'userId': user_id,
                'timestamp': timestamp,
                's3Key': s3_key
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Error processing data',
                'error': str(e)
            })
        }
```

Tạo file `src/lambda/processor/requirements.txt`:

```
boto3>=1.26.0
```

### Deploy Infrastructure

Bây giờ chúng ta sẵn sàng deploy infrastructure lên LocalStack:

```bash
# Đảm bảo LocalStack đang chạy
docker-compose ps

# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan -var-file="environments/local.tfvars"

# Apply configuration
terraform apply -var-file="environments/local.tfvars" -auto-approve
```

Terraform sẽ tạo các resources sau:
- 2 S3 buckets (data và lambda deployments)
- 1 DynamoDB table với Global Secondary Index
- 1 IAM role với policies
- 1 Lambda function
- CloudWatch Log Groups

### Verify Deployment

Sau khi deploy xong, verify các resources đã được tạo:

```bash
# List S3 buckets
awslocal s3 ls

# Expected output:
# myapp-local-data
# myapp-local-lambda-deployments

# List DynamoDB tables
awslocal dynamodb list-tables

# Expected output:
# {
#     "TableNames": [
#         "myapp-local-users"
#     ]
# }

# Describe DynamoDB table
awslocal dynamodb describe-table --table-name myapp-local-users

# List Lambda functions
awslocal lambda list-functions

# Get Lambda function details
awslocal lambda get-function --function-name myapp-local-processor
```

### Test Lambda Function

Test Lambda function bằng cách invoke trực tiếp:

```bash
# Tạo test event
cat > test-event.json << EOF
{
  "body": "{\"userId\": \"user123\", \"data\": {\"name\": \"John Doe\", \"email\": \"john@example.com\"}}"
}
EOF

# Invoke Lambda function
awslocal lambda invoke \
  --function-name myapp-local-processor \
  --payload file://test-event.json \
  output.json

# View output
cat output.json

# Check CloudWatch logs
awslocal logs tail /aws/lambda/myapp-local-processor --follow
```

### Verify Data in DynamoDB and S3

```bash
# Query DynamoDB table
awslocal dynamodb scan --table-name myapp-local-users

# List S3 objects
awslocal s3 ls s3://myapp-local-data/users/ --recursive

# Download and view S3 object
awslocal s3 cp s3://myapp-local-data/users/user123/[timestamp].json - | jq
```

---

## Phát triển Application

### Cấu hình SDK cho Application

Tạo một application Python có thể chạy trên cả LocalStack và AWS. Tạo file `src/application/config.py`:

```python
import os
from typing import Optional
import boto3
from botocore.config import Config

class AWSConfig:
    """AWS Configuration class that works with both LocalStack and real AWS"""
    
    def __init__(self):
        self.use_localstack = os.getenv('USE_LOCALSTACK', 'false').lower() == 'true'
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.localstack_endpoint = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
        
        # Resource names from Terraform outputs
        self.dynamodb_table = os.getenv('DYNAMODB_TABLE', '')
        self.s3_bucket = os.getenv('S3_BUCKET', '')
        
    def get_client(self, service_name: str, config: Optional[Config] = None):
        """
        Create boto3 client for specified service
        
        Args:
            service_name: AWS service name (s3, dynamodb, lambda, etc.)
            config: Optional botocore Config object
            
        Returns:
            boto3 client object
        """
        if self.use_localstack:
            return boto3.client(
                service_name,
                endpoint_url=self.localstack_endpoint,
                aws_access_key_id='test',
                aws_secret_access_key='test',
                region_name=self.aws_region,
                config=config
            )
        else:
            return boto3.client(
                service_name,
                region_name=self.aws_region,
                config=config
            )
    
    def get_resource(self, service_name: str):
        """
        Create boto3 resource for specified service
        
        Args:
            service_name: AWS service name (s3, dynamodb, etc.)
            
        Returns:
            boto3 resource object
        """
        if self.use_localstack:
            return boto3.resource(
                service_name,
                endpoint_url=self.localstack_endpoint,
                aws_access_key_id='test',
                aws_secret_access_key='test',
                region_name=self.aws_region
            )
        else:
            return boto3.resource(
                service_name,
                region_name=self.aws_region
            )

# Global config instance
aws_config = AWSConfig()
```

### Tạo Application Code

Tạo file `src/application/app.py`:

```python
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from config import aws_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Main application class for processing and storing data"""
    
    def __init__(self):
        self.dynamodb = aws_config.get_client('dynamodb')
        self.s3 = aws_config.get_client('s3')
        self.table_name = aws_config.dynamodb_table
        self.bucket_name = aws_config.s3_bucket
        
        logger.info(f"Initialized DataProcessor")
        logger.info(f"Using LocalStack: {aws_config.use_localstack}")
        logger.info(f"DynamoDB Table: {self.table_name}")
        logger.info(f"S3 Bucket: {self.bucket_name}")
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save user data to DynamoDB and S3
        
        Args:
            user_id: User identifier
            data: User data dictionary
            
        Returns:
            Dictionary with save results
        """
        try:
            timestamp = int(datetime.now().timestamp())
            
            # Prepare item for DynamoDB
            item = {
                'userId': {'S': user_id},
                'timestamp': {'N': str(timestamp)},
                'data': {'S': json.dumps(data)},
                'createdAt': {'S': datetime.now().isoformat()}
            }
            
            # Save to DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            logger.info(f"Saved to DynamoDB: userId={user_id}, timestamp={timestamp}")
            
            # Save to S3
            s3_key = f"users/{user_id}/{timestamp}.json"
            s3_data = {
                'userId': user_id,
                'timestamp': timestamp,
                'data': data,
                'createdAt': datetime.now().isoformat()
            }
            
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(s3_data, indent=2),
                ContentType='application/json'
            )
            logger.info(f"Saved to S3: s3://{self.bucket_name}/{s3_key}")
            
            return {
                'success': True,
                'userId': user_id,
                'timestamp': timestamp,
                's3Key': s3_key
            }
            
        except Exception as e:
            logger.error(f"Error saving user data: {str(e)}")
            raise
    
    def get_user_data(self, user_id: str, timestamp: int = None) -> Dict[str, Any]:
        """
        Retrieve user data from DynamoDB
        
        Args:
            user_id: User identifier
            timestamp: Optional specific timestamp
            
        Returns:
            User data dictionary
        """
        try:
            if timestamp:
                # Get specific item
                response = self.dynamodb.get_item(
                    TableName=self.table_name,
                    Key={
                        'userId': {'S': user_id},
                        'timestamp': {'N': str(timestamp)}
                    }
                )
                
                if 'Item' not in response:
                    return None
                
                item = response['Item']
                return {
                    'userId': item['userId']['S'],
                    'timestamp': int(item['timestamp']['N']),
                    'data': json.loads(item['data']['S']),
                    'createdAt': item.get('createdAt', {}).get('S', '')
                }
            else:
                # Query all items for user
                response = self.dynamodb.query(
                    TableName=self.table_name,
                    KeyConditionExpression='userId = :userId',
                    ExpressionAttributeValues={
                        ':userId': {'S': user_id}
                    }
                )
                
                items = []
                for item in response.get('Items', []):
                    items.append({
                        'userId': item['userId']['S'],
                        'timestamp': int(item['timestamp']['N']),
                        'data': json.loads(item['data']['S']),
                        'createdAt': item.get('createdAt', {}).get('S', '')
                    })
                
                return items
                
        except Exception as e:
            logger.error(f"Error retrieving user data: {str(e)}")
            raise
    
    def list_users(self) -> List[str]:
        """
        List all unique user IDs
        
        Returns:
            List of user IDs
        """
        try:
            response = self.dynamodb.scan(
                TableName=self.table_name,
                ProjectionExpression='userId'
            )
            
            user_ids = set()
            for item in response.get('Items', []):
                user_ids.add(item['userId']['S'])
            
            return sorted(list(user_ids))
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            raise
    
    def get_s3_file(self, s3_key: str) -> Dict[str, Any]:
        """
        Retrieve file from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File content as dictionary
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error retrieving S3 file: {str(e)}")
            raise

def main():
    """Main application entry point"""
    
    # Initialize processor
    processor = DataProcessor()
    
    # Example usage
    print("\n=== Saving User Data ===")
    result = processor.save_user_data(
        user_id='user456',
        data={
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'age': 28,
            'city': 'San Francisco'
        }
    )
    print(f"Save result: {json.dumps(result, indent=2)}")
    
    print("\n=== Retrieving User Data ===")
    user_data = processor.get_user_data('user456')
    print(f"User data: {json.dumps(user_data, indent=2)}")
    
    print("\n=== Listing All Users ===")
    users = processor.list_users()
    print(f"Users: {users}")
    
    print("\n=== Retrieving S3 File ===")
    if result.get('s3Key'):
        s3_data = processor.get_s3_file(result['s3Key'])
        print(f"S3 data: {json.dumps(s3_data, indent=2)}")

if __name__ == '__main__':
    main()
```

### Tạo Requirements File

Tạo file `src/application/requirements.txt`:

```
boto3>=1.26.0
python-dotenv>=0.19.0
```

### Tạo Environment File

Tạo file `src/application/.env.local`:

```bash
# LocalStack Configuration
USE_LOCALSTACK=true
AWS_REGION=us-east-1
LOCALSTACK_ENDPOINT=http://localhost:4566

# Resource Names (từ Terraform outputs)
DYNAMODB_TABLE=myapp-local-users
S3_BUCKET=myapp-local-data
```

Tạo file `src/application/.env.aws`:

```bash
# AWS Configuration
USE_LOCALSTACK=false
AWS_REGION=ap-southeast-1

# Resource Names (từ Terraform outputs)
DYNAMODB_TABLE=myapp-prod-users
S3_BUCKET=myapp-prod-data
```

### Chạy Application

```bash
# Install dependencies
cd src/application
pip install -r requirements.txt

# Run với LocalStack
export $(cat .env.local | xargs)
python app.py

# Hoặc run với AWS (sau khi deploy lên production)
export $(cat .env.aws | xargs)
python app.py
```

### Tạo Script Automation

Tạo file `scripts/deploy-local.sh`:

```bash
#!/bin/bash
set -e

echo "=== Deploying to LocalStack ==="

# Check if LocalStack is running
if ! docker ps | grep -q localstack; then
    echo "Starting LocalStack..."
    docker-compose up -d
    echo "Waiting for LocalStack to be ready..."
    sleep 10
fi

# Deploy infrastructure
echo "Deploying infrastructure with Terraform..."
cd terraform
terraform init
terraform apply -var-file="environments/local.tfvars" -auto-approve

# Get outputs
echo "Getting Terraform outputs..."
export DYNAMODB_TABLE=$(terraform output -raw users_table_name)
export S3_BUCKET=$(terraform output -raw data_bucket_name)

echo "Deployment completed!"
echo "DynamoDB Table: $DYNAMODB_TABLE"
echo "S3 Bucket: $S3_BUCKET"

# Save outputs to .env file
cd ../src/application
cat > .env.local << EOF
USE_LOCALSTACK=true
AWS_REGION=us-east-1
LOCALSTACK_ENDPOINT=http://localhost:4566
DYNAMODB_TABLE=$DYNAMODB_TABLE
S3_BUCKET=$S3_BUCKET
EOF

echo "Environment file created at src/application/.env.local"
```

Tạo file `scripts/test-local.sh`:

```bash
#!/bin/bash
set -e

echo "=== Testing LocalStack Deployment ==="

# Load environment
export $(cat src/application/.env.local | xargs)

# Test S3
echo "Testing S3..."
awslocal s3 ls

# Test DynamoDB
echo "Testing DynamoDB..."
awslocal dynamodb list-tables

# Test Lambda
echo "Testing Lambda..."
awslocal lambda list-functions

# Run application tests
echo "Running application..."
cd src/application
python app.py

echo "Tests completed!"
```

Tạo file `scripts/cleanup.sh`:

```bash
#!/bin/bash
set -e

echo "=== Cleaning up LocalStack ==="

# Destroy Terraform resources
cd terraform
terraform destroy -var-file="environments/local.tfvars" -auto-approve

# Stop LocalStack
cd ..
docker-compose down -v

echo "Cleanup completed!"
```

Chmod các scripts:

```bash
chmod +x scripts/*.sh
```

---

## Triển khai lên AWS Production

### Chuẩn bị AWS Credentials

Trước khi deploy lên AWS thật, bạn cần configure AWS credentials:

```bash
# Configure AWS CLI
aws configure

# Hoặc export credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="ap-southeast-1"
```

### Review Production Configuration

Kiểm tra file `terraform/environments/prod.tfvars` và đảm bảo các giá trị phù hợp:

```hcl
use_localstack = false
environment    = "prod"
project_name   = "myapp"
aws_region     = "ap-southeast-1"  # Chọn region phù hợp

enable_versioning = true
enable_encryption = true

lambda_runtime     = "python3.11"
lambda_memory_size = 1024
lambda_timeout     = 300

tags = {
  CostCenter  = "Engineering"
  Team        = "Backend"
  Criticality = "High"
}
```

### Setup Terraform Backend cho Production

Để quản lý Terraform state an toàn cho production, nên sử dụng remote backend. Tạo file `terraform/backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "myapp-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-southeast-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

Tạo S3 bucket và DynamoDB table cho state management:

```bash
# Tạo S3 bucket cho Terraform state
aws s3 mb s3://myapp-terraform-state --region ap-southeast-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket myapp-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket myapp-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Tạo DynamoDB table cho state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-1
```

### Deploy lên AWS Production

```bash
# Navigate to terraform directory
cd terraform

# Initialize with new backend
terraform init -reconfigure

# Review plan carefully
terraform plan -var-file="environments/prod.tfvars"

# Apply if everything looks good
terraform apply -var-file="environments/prod.tfvars"
```

**Lưu ý quan trọng:** Khi deploy lên production, review kỹ Terraform plan trước khi apply. Đảm bảo không có resources nào bị destroy hoặc recreate không mong muốn.

### Verify Production Deployment

```bash
# List S3 buckets
aws s3 ls

# List DynamoDB tables
aws dynamodb list-tables --region ap-southeast-1

# List Lambda functions
aws lambda list-functions --region ap-southeast-1

# Get Lambda function details
aws lambda get-function \
  --function-name myapp-prod-processor \
  --region ap-southeast-1
```

### Test Production Application

```bash
# Update environment file
cd src/application

# Get resource names from Terraform outputs
export DYNAMODB_TABLE=$(cd ../../terraform && terraform output -raw users_table_name)
export S3_BUCKET=$(cd ../../terraform && terraform output -raw data_bucket_name)

# Create production environment file
cat > .env.aws << EOF
USE_LOCALSTACK=false
AWS_REGION=ap-southeast-1
DYNAMODB_TABLE=$DYNAMODB_TABLE
S3_BUCKET=$S3_BUCKET
EOF

# Load environment and run
export $(cat .env.aws | xargs)
python app.py
```

### Test Production Lambda

```bash
# Invoke Lambda function
aws lambda invoke \
  --function-name myapp-prod-processor \
  --payload '{"body": "{\"userId\": \"prod-user-001\", \"data\": {\"name\": \"Production User\", \"email\": \"prod@example.com\"}}"}' \
  --region ap-southeast-1 \
  output.json

# View output
cat output.json

# Check CloudWatch logs
aws logs tail /aws/lambda/myapp-prod-processor \
  --region ap-southeast-1 \
  --follow
```

### Monitoring và Logging

Setup CloudWatch alarms cho production:

```hcl
# Add to terraform/main.tf

# Lambda Error Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.environment == "prod" ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function errors exceeded threshold"
  
  dimensions = {
    FunctionName = module.processor_lambda.function_name
  }
  
  alarm_actions = [aws_sns_topic.alerts[0].arn]
  
  tags = local.common_tags
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  count = var.environment == "prod" ? 1 : 0
  
  name = "${local.name_prefix}-alerts"
  
  tags = local.common_tags
}

# SNS Topic Subscription
resource "aws_sns_topic_subscription" "alerts_email" {
  count = var.environment == "prod" ? 1 : 0
  
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = "your-email@example.com"
}
```

---

## Testing và Debugging

### Unit Testing

Tạo file `src/application/tests/test_app.py`:

```python
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import DataProcessor

class TestDataProcessor(unittest.TestCase):
    
    def setUp(self):
        """Setup test fixtures"""
        # Mock AWS config
        with patch('app.aws_config') as mock_config:
            mock_config.use_localstack = True
            mock_config.dynamodb_table = 'test-table'
            mock_config.s3_bucket = 'test-bucket'
            mock_config.get_client = Mock()
            
            self.processor = DataProcessor()
            self.mock_dynamodb = Mock()
            self.mock_s3 = Mock()
            self.processor.dynamodb = self.mock_dynamodb
            self.processor.s3 = self.mock_s3
    
    def test_save_user_data(self):
        """Test saving user data"""
        # Setup
        user_id = 'test-user'
        data = {'name': 'Test User', 'email': 'test@example.com'}
        
        # Execute
        result = self.processor.save_user_data(user_id, data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['userId'], user_id)
        self.assertIn('timestamp', result)
        self.assertIn('s3Key', result)
        
        # Verify DynamoDB was called
        self.mock_dynamodb.put_item.assert_called_once()
        
        # Verify S3 was called
        self.mock_s3.put_object.assert_called_once()
    
    def test_get_user_data(self):
        """Test retrieving user data"""
        # Setup
        user_id = 'test-user'
        timestamp = 1234567890
        
        self.mock_dynamodb.get_item.return_value = {
            'Item': {
                'userId': {'S': user_id},
                'timestamp': {'N': str(timestamp)},
                'data': {'S': json.dumps({'name': 'Test User'})},
                'createdAt': {'S': '2024-01-01T00:00:00'}
            }
        }
        
        # Execute
        result = self.processor.get_user_data(user_id, timestamp)
        
        # Assert
        self.assertEqual(result['userId'], user_id)
        self.assertEqual(result['timestamp'], timestamp)
        self.assertIn('data', result)
        
        # Verify DynamoDB was called
        self.mock_dynamodb.get_item.assert_called_once()

if __name__ == '__main__':
    unittest.main()
```

Chạy tests:

```bash
cd src/application
python -m pytest tests/ -v
```

### Integration Testing

Tạo file `tests/integration/test_integration.py`:

```python
import unittest
import boto3
import json
import os
from datetime import datetime

class TestLocalStackIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Setup test environment"""
        cls.endpoint_url = 'http://localhost:4566'
        cls.region = 'us-east-1'
        
        # Create clients
        cls.s3 = boto3.client(
            's3',
            endpoint_url=cls.endpoint_url,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name=cls.region
        )
        
        cls.dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=cls.endpoint_url,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name=cls.region
        )
        
        cls.lambda_client = boto3.client(
            'lambda',
            endpoint_url=cls.endpoint_url,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name=cls.region
        )
        
        # Resource names
        cls.table_name = os.getenv('DYNAMODB_TABLE', 'myapp-local-users')
        cls.bucket_name = os.getenv('S3_BUCKET', 'myapp-local-data')
        cls.function_name = os.getenv('LAMBDA_FUNCTION', 'myapp-local-processor')
    
    def test_s3_operations(self):
        """Test S3 bucket operations"""
        # Test upload
        test_key = f'test/{datetime.now().timestamp()}.json'
        test_data = {'test': 'data'}
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=test_key,
            Body=json.dumps(test_data)
        )
        
        # Test download
        response = self.s3.get_object(
            Bucket=self.bucket_name,
            Key=test_key
        )
        
        content = json.loads(response['Body'].read())
        self.assertEqual(content, test_data)
        
        # Cleanup
        self.s3.delete_object(
            Bucket=self.bucket_name,
            Key=test_key
        )
    
    def test_dynamodb_operations(self):
        """Test DynamoDB operations"""
        # Test put item
        user_id = f'test-user-{datetime.now().timestamp()}'
        timestamp = int(datetime.now().timestamp())
        
        self.dynamodb.put_item(
            TableName=self.table_name,
            Item={
                'userId': {'S': user_id},
                'timestamp': {'N': str(timestamp)},
                'data': {'S': json.dumps({'test': 'data'})}
            }
        )
        
        # Test get item
        response = self.dynamodb.get_item(
            TableName=self.table_name,
            Key={
                'userId': {'S': user_id},
                'timestamp': {'N': str(timestamp)}
            }
        )
        
        self.assertIn('Item', response)
        self.assertEqual(response['Item']['userId']['S'], user_id)
        
        # Cleanup
        self.dynamodb.delete_item(
            TableName=self.table_name,
            Key={
                'userId': {'S': user_id},
                'timestamp': {'N': str(timestamp)}
            }
        )
    
    def test_lambda_invocation(self):
        """Test Lambda function invocation"""
        payload = {
            'body': json.dumps({
                'userId': f'test-user-{datetime.now().timestamp()}',
                'data': {'test': 'data'}
            })
        }
        
        response = self.lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        self.assertEqual(response['StatusCode'], 200)
        
        result = json.loads(response['Payload'].read())
        self.assertEqual(result['statusCode'], 200)

if __name__ == '__main__':
    unittest.main()
```

Chạy integration tests:

```bash
# Đảm bảo LocalStack đang chạy
docker-compose up -d

# Run tests
python -m pytest tests/integration/ -v
```

### Debugging Tips

**Check LocalStack logs:**

```bash
docker-compose logs -f localstack
```

**Check Lambda logs trong LocalStack:**

```bash
awslocal logs tail /aws/lambda/myapp-local-processor --follow
```

**Debug Terraform:**

```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform apply -var-file="environments/local.tfvars"
```

**Test AWS connectivity:**

```bash
# Test với LocalStack
awslocal s3 ls --debug

# Test với AWS thật
aws s3 ls --debug --region ap-southeast-1
```

**Validate Terraform configuration:**

```bash
cd terraform
terraform fmt -check
terraform validate
terraform plan -var-file="environments/local.tfvars"
```

---

## Best Practices

### Infrastructure as Code Best Practices

**Version Control:** Luôn commit Terraform code vào Git. Sử dụng `.gitignore` để exclude sensitive files như `.tfstate`, `.tfvars` chứa credentials, và `.terraform/` directory.

**Module Organization:** Tổ chức code thành modules nhỏ, tái sử dụng được. Mỗi module nên có một trách nhiệm cụ thể và được document đầy đủ.

**State Management:** Sử dụng remote backend (S3 + DynamoDB) cho production. Enable state locking để tránh conflicts khi nhiều người cùng apply.

**Environment Separation:** Sử dụng workspaces hoặc separate state files cho mỗi environment. Không bao giờ share state giữa các environments.

**Plan Before Apply:** Luôn review Terraform plan kỹ trước khi apply, đặc biệt là trong production. Chú ý các resources bị destroy hoặc recreate.

### Security Best Practices

**Credentials Management:** Không hard-code credentials trong code. Sử dụng environment variables, AWS SSM Parameter Store, hoặc AWS Secrets Manager.

**IAM Least Privilege:** Chỉ cấp permissions tối thiểu cần thiết cho mỗi resource. Thường xuyên review và audit IAM policies.

**Encryption:** Enable encryption cho tất cả data at rest (S3, DynamoDB, RDS) và in transit (HTTPS, TLS).

**Network Security:** Sử dụng VPC, Security Groups, và NACLs để control network access. Không expose resources ra internet nếu không cần thiết.

**Secrets Rotation:** Implement automatic rotation cho credentials và API keys. Sử dụng AWS Secrets Manager hoặc tương đương.

### Development Workflow Best Practices

**Local Development First:** Luôn test trên LocalStack trước khi deploy lên AWS. Điều này giúp phát hiện lỗi sớm và tiết kiệm chi phí.

**Automated Testing:** Implement unit tests, integration tests, và end-to-end tests. Run tests automatically trong CI/CD pipeline.

**Code Review:** Tất cả changes phải được review trước khi merge vào main branch. Sử dụng pull requests và enforce approval requirements.

**Documentation:** Document architecture, deployment procedures, và troubleshooting guides. Keep documentation up-to-date với code changes.

**Monitoring và Alerting:** Setup CloudWatch alarms, dashboards, và logging. Monitor key metrics như error rates, latency, và costs.

### Cost Optimization

**Right-sizing:** Chọn instance types và resource sizes phù hợp với workload. Không over-provision resources.

**Auto-scaling:** Implement auto-scaling cho resources có variable load. Scale down khi không cần thiết.

**Reserved Capacity:** Sử dụng Reserved Instances hoặc Savings Plans cho workloads predictable và long-running.

**Cleanup Unused Resources:** Thường xuyên audit và cleanup resources không sử dụng. Setup automated cleanup cho temporary resources.

**Cost Monitoring:** Enable AWS Cost Explorer và setup budget alerts. Review costs regularly và optimize accordingly.

### Disaster Recovery

**Backup Strategy:** Implement regular backups cho critical data. Test restore procedures periodically.

**Multi-Region Deployment:** Cho production critical applications, consider deploying across multiple regions.

**Disaster Recovery Plan:** Document và test disaster recovery procedures. Define RTO (Recovery Time Objective) và RPO (Recovery Point Objective).

**Infrastructure Versioning:** Tag infrastructure với version numbers. Maintain ability to rollback to previous versions.

---

## Troubleshooting

### Common Issues và Solutions

**Issue: LocalStack container không start được**

Triệu chứng: Docker container exits ngay sau khi start hoặc không respond.

Giải pháp:

```bash
# Check logs
docker-compose logs localstack

# Restart với clean state
docker-compose down -v
docker-compose up -d

# Check if port 4566 is already in use
lsof -i :4566
# Kill process if needed
kill -9 <PID>
```

**Issue: Terraform không connect được với LocalStack**

Triệu chứng: Terraform timeout hoặc connection refused errors.

Giải pháp:

```bash
# Verify LocalStack is running
curl http://localhost:4566/_localstack/health

# Check if endpoints are configured correctly in providers.tf
# Ensure use_localstack = true in tfvars

# Test connection với AWS CLI
awslocal s3 ls
```

**Issue: Lambda function không access được DynamoDB/S3**

Triệu chứng: Lambda returns errors về permissions hoặc không tìm thấy resources.

Giải pháp:

```python
# Kiểm tra AWS_ENDPOINT trong Lambda environment
# Phải dùng host.docker.internal thay vì localhost

# Trong Lambda code:
AWS_ENDPOINT = os.getenv('AWS_ENDPOINT', '')
if AWS_ENDPOINT:
    # Use host.docker.internal for LocalStack
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url='http://host.docker.internal:4566'
    )
```

**Issue: S3 bucket operations fail với LocalStack**

Triệu chứng: S3 operations return 404 hoặc access denied errors.

Giải pháp:

```bash
# Sử dụng path-style URLs cho LocalStack
# Trong Terraform providers.tf:
s3_use_path_style = true

# Test với awslocal
awslocal s3 ls
awslocal s3 mb s3://test-bucket
awslocal s3 ls s3://test-bucket
```

**Issue: Terraform state bị corrupt**

Triệu chứng: Terraform apply fails với state-related errors.

Giải pháp:

```bash
# Backup current state
cp terraform.tfstate terraform.tfstate.backup

# Try to refresh state
terraform refresh -var-file="environments/local.tfvars"

# If still broken, remove and reimport
terraform state rm <resource>
terraform import <resource> <resource_id>

# Last resort: destroy and recreate
terraform destroy -var-file="environments/local.tfvars"
terraform apply -var-file="environments/local.tfvars"
```

**Issue: Application không connect được với AWS services**

Triệu chứng: boto3 client returns connection errors hoặc credential errors.

Giải pháp:

```python
# Check environment variables
import os
print(f"USE_LOCALSTACK: {os.getenv('USE_LOCALSTACK')}")
print(f"AWS_ENDPOINT: {os.getenv('AWS_ENDPOINT')}")
print(f"AWS_REGION: {os.getenv('AWS_REGION')}")

# Verify credentials
import boto3
sts = boto3.client('sts')
print(sts.get_caller_identity())

# Test connection
s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
print(s3.list_buckets())
```

### Debug Commands

**Check LocalStack services status:**

```bash
curl http://localhost:4566/_localstack/health | jq
```

**List all resources trong LocalStack:**

```bash
# S3
awslocal s3 ls

# DynamoDB
awslocal dynamodb list-tables

# Lambda
awslocal lambda list-functions

# IAM
awslocal iam list-roles

# CloudWatch Logs
awslocal logs describe-log-groups
```

**Test Lambda function locally:**

```bash
# Invoke với test payload
awslocal lambda invoke \
  --function-name myapp-local-processor \
  --payload '{"body": "{\"userId\": \"test\", \"data\": {}}"}' \
  --log-type Tail \
  output.json

# View output
cat output.json | jq

# View logs
awslocal logs tail /aws/lambda/myapp-local-processor
```

**Debug Terraform:**

```bash
# Show current state
terraform show

# List resources in state
terraform state list

# Show specific resource
terraform state show aws_s3_bucket.data_bucket

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive
```

### Performance Optimization

**LocalStack startup time:**

```yaml
# Trong docker-compose.yml, chỉ enable services cần thiết
environment:
  - SERVICES=s3,dynamodb,lambda  # Thay vì all services
```

**Lambda cold start:**

```python
# Keep Lambda warm với CloudWatch Events
# Tạo rule invoke Lambda mỗi 5 phút
resource "aws_cloudwatch_event_rule" "keep_warm" {
  name                = "${local.name_prefix}-keep-lambda-warm"
  description         = "Keep Lambda warm"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.keep_warm.name
  target_id = "KeepWarm"
  arn       = module.processor_lambda.function_arn
  
  input = jsonencode({
    "warmup": true
  })
}
```

**DynamoDB query optimization:**

```python
# Sử dụng Query thay vì Scan khi có thể
# Query với KeyConditionExpression
response = dynamodb.query(
    TableName=table_name,
    KeyConditionExpression='userId = :userId',
    ExpressionAttributeValues={
        ':userId': {'S': user_id}
    }
)

# Thêm GSI cho frequent query patterns
# Limit số items returned
response = dynamodb.query(
    TableName=table_name,
    KeyConditionExpression='userId = :userId',
    Limit=10,
    ExpressionAttributeValues={
        ':userId': {'S': user_id}
    }
)
```

---

## Kết luận

Tài liệu này đã hướng dẫn bạn cách setup một môi trường Infrastructure as Code hoàn chỉnh với LocalStack và AWS, cho phép phát triển và test locally trước khi deploy lên production. Những điểm chính cần nhớ:

**Environment Agnostic Design:** Code được thiết kế để chạy trên cả LocalStack và AWS thật mà không cần thay đổi logic, chỉ thay đổi configuration.

**Automation:** Sử dụng Terraform cho infrastructure provisioning và scripts cho deployment automation giúp giảm thiểu manual errors và tăng tốc độ deployment.

**Testing:** Implement comprehensive testing strategy từ unit tests đến integration tests đảm bảo code quality và reliability.

**Security và Best Practices:** Follow AWS và security best practices để build một hệ thống secure, scalable, và maintainable.

**Documentation:** Maintain up-to-date documentation giúp team members hiểu và contribute vào project dễ dàng hơn.

### Next Steps

Sau khi hoàn thành setup cơ bản này, bạn có thể mở rộng hệ thống với:

- API Gateway với custom authorizers
- Step Functions cho complex workflows
- SQS/SNS cho message queuing
- RDS/Aurora cho relational databases
- ElastiCache cho caching layer
- CloudFront cho CDN
- Cognito cho user authentication
- CI/CD pipeline với GitHub Actions hoặc GitLab CI

### Resources

- LocalStack Documentation: https://docs.localstack.cloud
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws
- AWS CLI Reference: https://docs.aws.amazon.com/cli
- Boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

Chúc bạn thành công với việc xây dựng AWS infrastructure!