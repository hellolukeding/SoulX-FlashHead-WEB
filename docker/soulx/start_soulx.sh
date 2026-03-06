#!/bin/bash
# SoulX-FlashHead 流式视频生成服务启动脚本

set -e

MODEL_PATH=${MODEL_PATH:-"/models/SoulX-FlashHead-1_3B"}
PORT=${PORT:-8003}
FPS=${FPS:-25}
USE_SAGE_ATTN=${USE_SAGE_ATTN:-"true"}

echo "🎬 启动 SoulX-FlashHead 流式视频生成服务..."
echo "   模型路径: ${MODEL_PATH}"
echo "   FPS: ${FPS}"
echo "   SageAttention: ${USE_SAGE_ATTN}"
echo "   端口: ${PORT}"

# 设置 SageAttention 环境变量
if [ "$USE_SAGE_ATTN" = "true" ]; then
    export USE_SAGEATTENTION=1
    echo "   ✅ SageAttention 已启用"
fi

# 启动 FastAPI 服务
cd /app

python3 -m uvicorn soulx_server:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --log-level info
