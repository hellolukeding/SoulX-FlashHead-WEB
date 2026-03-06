#!/bin/bash
# CosyVoice-300M-SFT TTS 服务 - 一键部署脚本 (vLLM 加速)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "==================================="
echo "  CosyVoice SFT 服务部署 (vLLM)"
echo "==================================="
echo ""

# 检查环境
echo "1️⃣  检查环境..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi
echo "   ✅ Docker: $(docker --version)"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi
echo "   ✅ Docker Compose: $(docker compose version 2>/dev/null || docker-compose --version)"

if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  nvidia-smi 未找到"
else
    echo "   ✅ GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
    echo "   显存: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)"
fi
echo ""

# 检查 SFT 模型
echo "2️⃣  检查 SFT 模型..."
SFT_MODEL_DIR="${PROJECT_ROOT}/models/CosyVoice/pretrained_models/iic/CosyVoice-300M-SFT"

if [ ! -d "${SFT_MODEL_DIR}" ]; then
    echo "❌ SFT 模型不存在: ${SFT_MODEL_DIR}"
    echo ""
    echo "请先下载 SFT 模型:"
    echo "  cd ${SCRIPT_DIR}"
    echo "  bash download-sft-model.sh"
    exit 1
fi

SFT_MODEL_SIZE=$(du -sh "${SFT_MODEL_DIR}" 2>/dev/null | cut -f1)
echo "   ✅ SFT 模型: ${SFT_MODEL_DIR} (${SFT_MODEL_SIZE})"
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
docker build -f Dockerfile.vllm-sft -t cosyvoice-sft:latest .

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
if [ -f .env-sft ]; then
    docker compose -f docker-compose-sft.yml --env-file .env-sft up -d
else
    echo "   使用默认配置"
    docker compose -f docker-compose-sft.yml up -d
fi
echo ""

# 等待服务启动
echo "6️⃣  等待服务启动..."
for i in {1..45}; do
    if curl -s http://localhost:${COSYVOICE_SFT_PORT:-8003}/health > /dev/null 2>&1; then
        echo "   ✅ 服务已启动"
        break
    fi
    echo "   等待中... ($i/45)"
    sleep 2
done
echo ""

# 显示服务状态和音色列表
echo "==================================="
echo "  部署完成！"
echo "==================================="
echo ""

docker compose -f docker-compose-sft.yml ps
echo ""

echo "服务地址: http://localhost:${COSYVOICE_SFT_PORT:-8003}"
echo ""
echo "🎤 预设音色列表:"
curl -s http://localhost:${COSYVOICE_SFT_PORT:-8003}/speakers | python3 -m json.tool 2>/dev/null || echo "获取音色列表失败"
echo ""
echo "📖 API 端点:"
echo "  健康检查: GET /health"
echo "  音色列表: GET /speakers"
echo "  标准 TTS: POST /tts"
echo "  流式 TTS: POST /tts/stream"
echo ""
echo "📝 请求示例:"
echo "  curl -X POST http://localhost:${COSYVOICE_SFT_PORT:-8003}/tts \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"text\": \"你好\", \"speaker\": \"中性女\"}' \\"
echo "    -o output.wav"
echo ""
echo "查看日志:"
echo "  docker compose -f docker-compose-sft.yml logs -f"
echo ""
echo "停止服务:"
echo "  docker compose -f docker-compose-sft.yml down"
