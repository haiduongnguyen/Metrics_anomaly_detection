#!/bin/bash

set -e

ZIP_FILE="lambda_test.zip"

echo "📦 Packaging Lambda test..."

rm -f $ZIP_FILE

cd lambda_test
zip -r ../$ZIP_FILE .
cd ..

echo "✅ Lambda packaged: $ZIP_FILE"