resource "aws_s3_bucket" "ingestion" {
  bucket        = "${var.project}-opstimus"
  force_destroy = false


  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Project = var.project
  }
}


output "s3_cold_bucket_name" {
  value = aws_s3_bucket.ingestion.bucket
}
