<#
.SYNOPSIS
    Build and publish Lambda Layers for Team36 (core + utils).
.DESCRIPTION
    - Installs dependencies from requirements_core_2.txt and requirements_utils.txt
    - Packages each into proper Lambda layer structure (python/)
    - Uploads to S3 and publishes new layer versions
    - Prints resulting ARNs for Terraform usage
#>

# --- CONFIG ---
$BucketName = "vpbank-hackathon-team36-lambda-artifacts"
$Region = "ap-southeast-1"
$LayerCore = "vpbank-team36-core-libs"
$LayerUtils = "vpbank-team36-utils-libs"

# --- CLEAN PREVIOUS BUILDS ---
Write-Host "🧹 Cleaning previous build directories..."
Remove-Item -Recurse -Force layer_core, layer_utils, layer_zips -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path layer_core\python | Out-Null
New-Item -ItemType Directory -Path layer_utils\python | Out-Null
New-Item -ItemType Directory -Path layer_zips | Out-Null

# --- INSTALL DEPENDENCIES FROM REQUIREMENTS FILES ---
if (Test-Path "requirements_core_2.txt") {
    Write-Host "📦 Installing core dependencies from requirements_core_2.txt..."
    pip install -r requirements_core.txt --no-cache-dir -t layer_core\python
} else {
    Write-Host "⚠️  requirements_core_2.txt not found, skipping core layer install."
}

if (Test-Path "requirements_utils.txt") {
    Write-Host "📦 Installing utils dependencies from requirements_utils.txt..."
    pip install -r requirements_utils.txt --no-cache-dir -t layer_utils\python
} else {
    Write-Host "⚠️  requirements_utils.txt not found, skipping utils layer install."
}

# --- REMOVE CACHE FILES TO REDUCE SIZE ---
Write-Host "🧽 Cleaning __pycache__ and .dist-info folders..."
Get-ChildItem -Path layer_core\python -Include *.dist-info,__pycache__ -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path layer_utils\python -Include *.dist-info,__pycache__ -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# --- ZIP LAYERS ---
Write-Host "🗜️  Creating ZIP archives for layers..."
Compress-Archive -Path layer_core\* -DestinationPath layer_zips\layer_core.zip -Force
Compress-Archive -Path layer_utils\* -DestinationPath layer_zips\layer_utils.zip -Force

# --- UPLOAD TO S3 ---
Write-Host "☁️  Uploading layer ZIPs to S3..."
aws s3 cp "layer_zips\layer_core.zip" "s3://$BucketName/layers/layer_core.zip" --region $Region
aws s3 cp "layer_zips\layer_utils.zip" "s3://$BucketName/layers/layer_utils.zip" --region $Region

# --- PUBLISH NEW LAYERS ---
Write-Host "🚀  Publishing new layer versions to AWS Lambda..."
$coreResult = aws lambda publish-layer-version `
    --layer-name $LayerCore `
    --content S3Bucket=$BucketName,S3Key=layers/layer_core.zip `
    --compatible-runtimes python3.11 `
    --region $Region | ConvertFrom-Json

$utilsResult = aws lambda publish-layer-version `
    --layer-name $LayerUtils `
    --content S3Bucket=$BucketName,S3Key=layers/layer_utils.zip `
    --compatible-runtimes python3.11 `
    --region $Region | ConvertFrom-Json

# --- PRINT RESULTS ---
Write-Host ""
Write-Host "✅ Layers built and published successfully!"
Write-Host "--------------------------------------------"
Write-Host ("Core Layer ARN :  {0}" -f $coreResult.LayerVersionArn)
Write-Host ("Utils Layer ARN:  {0}" -f $utilsResult.LayerVersionArn)
Write-Host "--------------------------------------------"
Write-Host "Use these ARNs in Terraform under your Lambda 'layers' = [...]"
