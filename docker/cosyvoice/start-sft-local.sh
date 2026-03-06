#!/bin/bash
# CosyVoice SFT 服务 - 本地启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 激活虚拟环境
source "${PROJECT_ROOT}/backend/venv/bin/activate"

# 设置 Python 路径
export PYTHONPATH="${PROJECT_ROOT}/models/CosyVoice/third_party/Matcha-TTS:${PROJECT_ROOT}/models/CosyVoice:${PYTHONPATH}"

# 设置 ModelScope 缓存目录
export MODELSCOPE_CACHE_DIR="${PROJECT_ROOT}/models/CosyVoice/pretrained_models"

cd "${SCRIPT_DIR}"

echo "🎵 启动 CosyVoice-300M-SFT 服务..."
echo "模型: CosyVoice-300M-SFT (7 个预设音色)"
echo "端口: 8003"
echo ""

# 启动服务
exec python3 cosyvoice_sft_server.py
