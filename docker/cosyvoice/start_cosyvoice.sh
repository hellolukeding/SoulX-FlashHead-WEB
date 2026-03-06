#!/bin/bash
# CosyVoice 流式 TTS 服务启动脚本

set -e

MODEL_PATH=${MODEL_PATH:-"/models/CosyVoice-300M"}
PORT=${PORT:-8002}
CHUNK_SIZE=${CHUNK_SIZE:-2400}  # 150ms @ 16kHz

echo "🎵 启动 CosyVoice 流式 TTS 服务..."
echo "   模型路径: ${MODEL_PATH}"
echo "   切片大小: ${CHUNK_SIZE} samples (${CHUNK_SIZE/16000}s)"
echo "   端口: ${PORT}"

# 启动 FastAPI 服务
cd /app/CosyVoice

python3 -m uvicorn server:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --log-level info
