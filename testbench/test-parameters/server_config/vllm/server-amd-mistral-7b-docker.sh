#!/bin/bash

# Set Hugging Face token
HUGGING_FACE_HUB_TOKEN="your_huggingface_token_here"

docker run -d \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN" \
    -p 8001:8000 \
    --ipc=host \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    rocm/vllm:latest \
    python3 -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.3 \
    --tokenizer-mode mistral \
    --disable-log-requests \
    --tensor-parallel-size 1 \
    --distributed-executor-backend mp \
    --max-model-len 8192 \
    --max-num-batched-tokens 65536 \
    --kv-cache-dtype=auto \
    --no-enable-prefix-caching &
