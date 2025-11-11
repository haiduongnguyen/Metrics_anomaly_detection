Write-Host "🚀 Building Lambda packages for Windows..."

$LAMBDA_DIR = "lambda_build"

# Clean old builds
if (Test-Path $LAMBDA_DIR) { Remove-Item -Recurse -Force $LAMBDA_DIR }
New-Item -ItemType Directory -Path $LAMBDA_DIR | Out-Null

# Copy your code
Copy-Item lambda_filter.py $LAMBDA_DIR
Copy-Item lambda_normalization.py $LAMBDA_DIR
Copy-Item config.py $LAMBDA_DIR

# Create ZIPs
Compress-Archive -Path "$LAMBDA_DIR\*" -DestinationPath "lambda_filter.zip" -Force
Compress-Archive -Path "$LAMBDA_DIR\*" -DestinationPath "lambda_normalization.zip" -Force

Write-Host "✅ Lambda ZIPs ready for Terraform!"

