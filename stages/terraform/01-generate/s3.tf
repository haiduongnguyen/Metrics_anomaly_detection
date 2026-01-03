locals {
  files = fileset(var.data_folder, "*.jsonl")
}

resource "aws_s3_object" "upload_data" {
  for_each = local.files

  bucket = var.s3_bucket_raw
  key    = "raw/${each.key}"
  source = "${var.data_folder}/${each.key}"
}
