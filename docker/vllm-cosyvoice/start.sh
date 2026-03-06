#!/bin/bash
set -e

MODEL_PATH=${MODEL_PATH:-"/models/CosyVoice-300M"}
PORT=${PORT:-8002}
HOST=${HOST:-"0.0.0.0"}

echo "🎵 启动 CosyVoice 流式 TTS 服务"
echo "================================"
echo "模型路径: ${MODEL_PATH}"
echo "监听地址: ${HOST}:${PORT}"
echo ""

# 启动 FastAPI 服务器
cd /app

python3 -m uvicorn cosyvoice_server:app \
    --host ${HOST} \
    --port ${PORT} \
    --workers 1 \
    --log-level info \
    --loop uvloop
