#!/bin/bash
# CosyVoice SFT 服务启动脚本

set -e

echo "🎵 启动 CosyVoice-300M-SFT 服务..."

# 设置 Python 路径
export PYTHONPATH="/models/CosyVoice/third_party/Matcha-TTS:/models/CosyVoice:${PYTHONPATH}"

# 设置 ModelScope 缓存目录
export MODELSCOPE_CACHE_DIR="/models/CosyVoice/pretrained_models"

# 设置日志级别
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# 启动服务
exec uvicorn cosyvoice_sft_server:app \
    --host 0.0.0.0 \
    --port 8002 \
    --log-level ${LOG_LEVEL}
