resource "aws_lambda_layer_version" "core_libs" {
  s3_bucket  = var.lambda_bucket
  s3_key     = "layers/layer_core.zip"
  layer_name = "vpbank-team36-core-libs"
  compatible_runtimes = ["python3.10"]
  description = "Core libraries for Team 36 (pandas, numpy)"
}

resource "aws_lambda_layer_version" "layer_utils" {
  s3_bucket  = var.lambda_bucket
  s3_key     = "layers/layer_utils.zip"
  layer_name = "vpbank-team36-utils-libs"
  compatible_runtimes = ["python3.10"]
  description = "ML libraries for Team 36 (scikit-learn)"
}


##############################################
# Add public permissions for Lambda Layers
##############################################

resource "null_resource" "core_layer_permission" {
  provisioner "local-exec" {
    command = "aws lambda add-layer-version-permission --layer-name ${aws_lambda_layer_version.core_libs.layer_name} --version-number ${aws_lambda_layer_version.core_libs.version} --statement-id AllowPublicAccessCore --action lambda:GetLayerVersion --principal * --region ${var.region}"
  }

  triggers = {
    layer_version = aws_lambda_layer_version.core_libs.version
  }
}

resource "null_resource" "ml_layer_permission" {
  provisioner "local-exec" {
    command = "aws lambda add-layer-version-permission --layer-name ${aws_lambda_layer_version.layer_utils.layer_name} --version-number ${aws_lambda_layer_version.layer_utils.version} --statement-id AllowPublicAccessML --action lambda:GetLayerVersion --principal * --region ${var.region}"
  }

  triggers = {
    layer_version = aws_lambda_layer_version.layer_utils.version
  }
}
