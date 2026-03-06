#!/bin/bash
# CosyVoice TTS 服务 - 一键部署脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "==================================="
echo "  CosyVoice TTS 服务部署"
echo "==================================="
echo ""

# 检查环境
echo "1️⃣  检查环境..."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi
echo "   ✅ Docker: $(docker --version)"

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi
echo "   ✅ Docker Compose: $(docker compose version 2>/dev/null || docker-compose --version)"

# 检查 GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  nvidia-smi 未找到，请确保已安装 NVIDIA 驱动"
else
    echo "   ✅ GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
fi
echo ""

# 检查模型
echo "2️⃣  检查模型..."
COSYVOICE_MODEL_DIR="${COSYVOICE_ROOT:-/opt/digital-human-platform/models/CosyVoice}"

if [ ! -d "${COSYVOICE_MODEL_DIR}" ]; then
    echo "❌ CosyVoice 模型目录不存在: ${COSYVOICE_MODEL_DIR}"
    exit 1
fi
echo "   ✅ 模型目录: ${COSYVOICE_MODEL_DIR}"

# 检查默认参考音频
DEFAULT_PROMPT="${COSYVOICE_MODEL_DIR}/pretrained_models/CosyVoice-300M/asset/default_prompt.wav"
if [ ! -f "${DEFAULT_PROMPT}" ]; then
    echo "⚠️  默认参考音频不存在: ${DEFAULT_PROMPT}"
    echo "   将创建默认参考音频..."

    source "${PROJECT_ROOT}/backend/venv/bin/activate" || {
        echo "❌ 无法激活 Python 虚拟环境"
        exit 1
    }

    python3 << 'EOF'
import numpy as np
import wave
import os

sample_rate = 22050
duration = 1.0
frequency = 440.0

t = np.linspace(0, duration, int(sample_rate * duration), False)
audio = np.sin(2 * np.pi * frequency * t) * 0.3
audio = (audio * 32767).astype(np.int16)

output_dir = "/opt/digital-human-platform/models/CosyVoice/pretrained_models/CosyVoice-300M/asset"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "default_prompt.wav")

with wave.open(output_path, 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(sample_rate)
    wav.writeframes(audio.tobytes())

print(f"✅ 创建参考音频: {output_path}")
EOF
else
    echo "   ✅ 默认参考音频: ${DEFAULT_PROMPT}"
fi
echo ""

# 创建网络
echo "3️⃣  创建 Docker 网络..."
if ! docker network inspect digital-human-network &> /dev/null; then
    docker network create digital-human-network
    echo "   ✅ 网络已创建: digital-human-network"
else
    echo "   ✅ 网络已存在: digital-human-network"
fi
echo ""

# 构建镜像
echo "4️⃣  构建 Docker 镜像..."
echo "   这可能需要 10-30 分钟..."
echo ""

cd "${SCRIPT_DIR}"
docker build -t cosyvoice-tts:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "   ✅ 镜像构建成功"
else
    echo ""
    echo "   ❌ 镜像构建失败"
    exit 1
fi
echo ""

# 启动服务
echo "5️⃣  启动服务..."
if [ -f .env ]; then
    docker compose up -d
else
    echo "   ⚠️  .env 文件不存在，使用默认配置"
    cp .env.example .env
    docker compose up -d
fi
echo ""

# 等待服务启动
echo "6️⃣  等待服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:${COSYVOICE_PORT:-8002}/health > /dev/null 2>&1; then
        echo "   ✅ 服务已启动"
        break
    fi
    echo "   等待中... ($i/30)"
    sleep 2
done
echo ""

# 显示服务状态
echo "==================================="
echo "  部署完成！"
echo "==================================="
echo ""
docker compose ps
echo ""
echo "服务地址: http://localhost:${COSYVOICE_PORT:-8002}"
echo "健康检查: http://localhost:${COSYVOICE_PORT:-8002}/health"
echo ""
echo "测试服务:"
echo "  ./test.sh"
echo ""
echo "查看日志:"
echo "  docker compose logs -f"
echo ""
echo "停止服务:"
echo "  docker compose down"
