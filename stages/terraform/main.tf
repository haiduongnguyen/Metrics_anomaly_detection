module "upload_generated_data" {
  source        = "./01-generate"

  s3_bucket_raw = var.s3_bucket_raw
  data_folder   = var.data_generate_folder

  depends_on = [
    aws_s3_bucket.raw_data
  ]
}

module "etl" {
  source = "./02-etl"

  project_name         = var.project_name
  s3_bucket_raw        = var.s3_bucket_raw
  data_generate_folder = var.data_generate_folder
  
  depends_on = [
    aws_s3_bucket.raw_data
  ]
}

