#!/bin/sh

export OUTPUT_DIR="python"

rm -rf ${OUTPUT_DIR} && mkdir -p ${OUTPUT_DIR}

docker run --rm -v $(pwd):/var/task -w /var/task lambci/lambda:build-python3.7 \
    pip install -r requirements.txt -t ${OUTPUT_DIR} 