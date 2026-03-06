#!/bin/bash
# vLLM 启动脚本 - CosyVoice LLM 服务

set -e

MODEL_NAME=${MODEL_NAME:-"deepseek-chat-1.5b"}
TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE:-1}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.3}
PORT=${PORT:-8001}

echo "🚀 启动 vLLM 服务..."
echo "   模型: ${MODEL_NAME}"
echo "   GPU 显存利用率: ${GPU_MEMORY_UTILIZATION}"
echo "   端口: ${PORT}"

# 启动 vLLM OpenAI 兼容 API
python3 -m vllm.entrypoints.openai.api_server \
    --model /models/${MODEL_NAME} \
    --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
    --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION} \
    --max-model-len 4096 \
    --dtype half \
    --port ${PORT} \
    --host 0.0.0.0 \
    --disable-log-requests \
    --trust-remote-code \
    --enable-prefix-caching
