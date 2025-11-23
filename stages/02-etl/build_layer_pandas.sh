#!/bin/bash
set -e

LAYER_NAME="layer_pandas_numpy"
OUTPUT_ZIP="layer_pandas_numpy.zip"

echo "📦 Building Lambda Layer for Python 3.10..."

# Cleanup
rm -rf python
rm -f $OUTPUT_ZIP

docker run --rm \
    --entrypoint /bin/bash \
    -v "$PWD/layer_pandas":/var/task \
    -w /var/task \
    amazon/aws-lambda-python:3.10 \
    -c "
        yum install -y zip >/dev/null 2>&1 && \
        pip install -r requirements.txt -t python/ && \
        zip -r layer_pandas_numpy.zip python
    "

echo "✅ Layer built successfully: $OUTPUT_ZIP"
