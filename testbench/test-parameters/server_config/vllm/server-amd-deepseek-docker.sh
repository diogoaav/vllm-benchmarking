#!/bin/bash

# Set Hugging Face token
HUGGING_FACE_HUB_TOKEN="your_huggingface_token_here"

docker run -d \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN" \
    --env "VLLM_DISABLE_DYNAMO=1" \
    --env "VLLM_USE_V1=0" \
    -p 8001:8000 \
    --ipc=host \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    rocm/vllm:latest \
    python3 -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-V3-0324 \
    --tokenizer-mode auto \
    --disable-log-requests \
    --tensor-parallel-size 8 \
    --enable-expert-parallel \
    --gpu-memory-utilization=0.95 \
    --distributed-executor-backend mp \
    --no-enable-prefix-caching &
