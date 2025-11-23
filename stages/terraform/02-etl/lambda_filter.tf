terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

locals {
  lambda_name = "${var.project_name}-lambda-filter"
  lambda_src  = "${path.module}/../../02-etl/lambda_filter"
  lambda_zip  = "${path.module}/lambda_filter.zip"
}

# -----------------------------
# Zip lambda_filter code
# -----------------------------
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = local.lambda_src
  output_path = local.lambda_zip
}

# -----------------------------
# IAM Role
# -----------------------------
data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${local.lambda_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_iam_role_policy_attachment" "basic_logging" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda needs S3 read/write permissions
data "aws_iam_policy_document" "lambda_s3_rw" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.s3_bucket_raw}/*"]
  }
}

resource "aws_iam_policy" "lambda_s3_policy" {
  name   = "${local.lambda_name}-s3-policy"
  policy = data.aws_iam_policy_document.lambda_s3_rw.json
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

# -----------------------------
# Lambda Function
# -----------------------------
resource "aws_lambda_function" "lambda_filter" {
  function_name = local.lambda_name
  description   = "Filter raw logs → filtered logs based on config.json rules"

  runtime = "python3.10"
  handler = "lambda_filter.lambda_handler"
  role    = aws_iam_role.lambda_role.arn

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout      = 60
  memory_size  = 256

  environment {
    variables = {
      RAW_BUCKET = var.s3_bucket_raw
    }
  }
}

# -----------------------------
# S3 Trigger (raw/ prefix)
# -----------------------------
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Trigger"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_filter.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.s3_bucket_raw}"
}

resource "aws_s3_bucket_notification" "raw_events" {
  bucket = var.s3_bucket_raw

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_filter.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}

# -----------------------------
# Output
# -----------------------------
output "lambda_filter_name" {
  value = aws_lambda_function.lambda_filter.function_name
}

output "lambda_filter_arn" {
  value = aws_lambda_function.lambda_filter.arn
}
