#!/bin/bash

set -e

FUNCTION_NAME="lambda_test_pandas"
ZIP_FILE="lambda_test.zip"
LAYER_NAME="layer_pandas_numpy"
ACCOUNT_ID="291418341479"

echo "🔍 Getting latest Layer ARN..."
LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name $LAYER_NAME \
    --query 'LayerVersions[0].LayerVersionArn' \
    --output text)

echo "🧪 Using Layer ARN: $LAYER_ARN"

aws lambda create-function \
    --function-name $FUNCTION_NAME \
    --runtime python3.10 \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://$ZIP_FILE \
    --role arn:aws:iam::291418341479:role/lambda_run \
    --layers "$LAYER_ARN"

echo "🎉 Lambda deployed successfully!"
