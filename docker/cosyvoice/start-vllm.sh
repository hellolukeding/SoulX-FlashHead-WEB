#!/bin/bash
# CosyVoice SFT 服务启动脚本 (vLLM 加速)

set -e

echo "🎵 启动 CosyVoice-300M-SFT 服务 (vLLM 加速)..."

# 设置 Python 路径
export PYTHONPATH="/models/CosyVoice/third_party/Matcha-TTS:/models/CosyVoice:${PYTHONPATH}"

# 设置 ModelScope 缓存目录
export MODELSCOPE_CACHE_DIR="/models/CosyVoice/pretrained_models"

# vLLM 配置
export VLLM_USE_MODELSCOPE=true
export VLLM_TENSOR_PARALLEL_SIZE=1

# 设置日志级别
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# GPU 内存优化
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

# 启动服务
exec uvicorn cosyvoice_sft_server:app \
    --host 0.0.0.0 \
    --port 8002 \
    --log-level ${LOG_LEVEL}
