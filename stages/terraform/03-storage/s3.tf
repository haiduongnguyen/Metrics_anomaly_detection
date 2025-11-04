resource "aws_s3_bucket" "cold_storage" {
  bucket        = "${var.project}-cold-storage"
  force_destroy = false

  # ✅ Enable server-side encryption by default
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Project = var.project
    Layer   = "storage-cold"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket                  = aws_s3_bucket.cold_storage.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "lifecycle" {
  bucket = aws_s3_bucket.cold_storage.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    filter {}

    transition {
      days          = var.s3_retention_days
      storage_class = "GLACIER"
    }
  }
}


output "s3_cold_bucket_name" {
  value = aws_s3_bucket.cold_storage.bucket
}
