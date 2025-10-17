#!/bin/bash

# Set Hugging Face token
HUGGING_FACE_HUB_TOKEN="your_huggingface_token_here"

docker run -d \
    --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN" \
    -p 8001:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model deepseek-ai/DeepSeek-V3-0324 \
    --tokenizer-mode auto \
    --disable-log-requests \
    --tensor-parallel-size 1 \
    --distributed-executor-backend mp \
    --max-model-len 8192 \
    --max-num-batched-tokens 65536 \
    --kv-cache-dtype=auto \
    --no-enable-prefix-caching \ &
