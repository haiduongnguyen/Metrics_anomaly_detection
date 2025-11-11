##############################################
# 1️⃣ Create S3 bucket (always managed by Terraform)
##############################################
resource "aws_s3_bucket" "lambda_bucket" {
  bucket = var.lambda_bucket
  force_destroy = true

  tags = {
    Name    = var.lambda_bucket
    Project = var.project
  }

  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_s3_bucket_versioning" "lambda_versioning" {
  bucket = aws_s3_bucket.lambda_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

##############################################
# 2️⃣ Package Lambda ZIPs
##############################################
#data "archive_file" "lambda_filter_zip" {
#  type        = "zip"
#  source_file = "../../02-etl/lambda_filter.py"
##  output_path = "../../02-etl/lambda_filter.zip"
#  depends_on = [aws_s3_bucket.lambda_bucket]
#}

#data "archive_file" "lambda_normalization_zip" {
#  type        = "zip"
#  source_file = "../../02-etl/lambda_normalization.py"
#  output_path = "../../02-etl/lambda_normalization.zip"
#  depends_on = [aws_s3_bucket.lambda_bucket]
#}

##############################################
# 3️⃣ Upload Lambda ZIPs to S3 (after bucket)
##############################################
resource "aws_s3_object" "lambda_filter_obj" {
  bucket = aws_s3_bucket.lambda_bucket.bucket
  key    = "lambda_filter.zip"
  # source = data.archive_file.lambda_filter_zip.output_path
  source = var.lambda_filter_zip
  # etag   = filemd5(data.archive_file.lambda_filter_zip.output_path)
  etag   = filemd5(var.lambda_filter_zip)

  depends_on = [aws_s3_bucket.lambda_bucket]
}

resource "aws_s3_object" "lambda_normalization_obj" {
  bucket = aws_s3_bucket.lambda_bucket.bucket
  key    = "lambda_normalization.zip"
  # source = data.archive_file.lambda_normalization_zip.output_path
  source = var.lambda_normalization_zip
  # etag   = filemd5(data.archive_file.lambda_normalization_zip.output_path)
  etag   = filemd5(var.lambda_normalization_zip)

  depends_on = [aws_s3_bucket.lambda_bucket]
}


data "aws_lambda_layer_version" "core_latest" {
  layer_name = "vpbank-team36-core-libs"
}

##############################################
# 4️⃣ IAM role for Lambda (you already have)
##############################################
# Ensure you already defined in iam.tf:
# resource "aws_iam_role" "lambda_role" { ... }

##############################################
# 5️⃣ Lambda Functions
##############################################
resource "aws_lambda_function" "lambda_filter" {
  function_name = "vpbank_lambda_filter"
  s3_bucket     = aws_s3_bucket.lambda_bucket.bucket
  s3_key        = aws_s3_object.lambda_filter_obj.key
  handler       = "lambda_filter.lambda_handler"
  runtime       = "python3.10"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 60

  source_code_hash = filebase64sha256(var.lambda_filter_zip)

  depends_on = [aws_s3_object.lambda_filter_obj]
  layers = [data.aws_lambda_layer_version.core_latest.arn]
}

resource "aws_lambda_function" "lambda_normalization" {
  function_name = "vpbank_lambda_normalization"
  s3_bucket     = aws_s3_bucket.lambda_bucket.bucket
  s3_key        = aws_s3_object.lambda_normalization_obj.key
  handler       = "lambda_normalization.lambda_handler"
  runtime       = "python3.10"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 60

  source_code_hash = filebase64sha256(var.lambda_normalization_zip)

  depends_on = [aws_s3_object.lambda_normalization_obj]
  layers = [data.aws_lambda_layer_version.core_latest.arn]
}
