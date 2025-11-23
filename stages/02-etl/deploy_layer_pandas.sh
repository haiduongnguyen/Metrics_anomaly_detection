#!/bin/bash

set -e
LAYER_PANDAS_FOLDER="layer_pandas"
LAYER_NAME="layer_pandas_numpy"
ZIP_FILE="$LAYER_PANDAS_FOLDER/layer_pandas_numpy.zip"

echo "🚀 Publishing Lambda Layer: $LAYER_NAME (Python 3.10)"

aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --zip-file fileb://$ZIP_FILE \
    --compatible-runtimes python3.10

echo "✅ Layer published!"
