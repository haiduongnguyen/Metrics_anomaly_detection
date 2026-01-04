variable "s3_bucket_raw" {
  type        = string
  description = "Target S3 bucket to upload generated data"
}

variable "data_folder" {
  type        = string
  description = "Local folder that contains generated jsonl data"
}
