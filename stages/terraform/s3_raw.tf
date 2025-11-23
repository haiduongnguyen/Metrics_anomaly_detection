resource "aws_s3_bucket" "raw_data" {
  bucket        = var.s3_bucket_raw
  force_destroy = true
}
