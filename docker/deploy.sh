#!/bin/bash
# 数字人平台一键部署脚本

set -e

PROJECT_ROOT="/opt/digital-human-platform"
DOCKER_DIR="$PROJECT_ROOT/docker"
MODELS_DIR="$PROJECT_ROOT/models"

echo "🚀 数字人平台一键部署脚本"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker
check_docker() {
    echo -n "检查 Docker..."
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC}"
}

# 检查 Docker Compose
check_docker_compose() {
    echo -n "检查 Docker Compose..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}✗ Docker Compose 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC}"
}

# 检查 NVIDIA Docker
check_nvidia_docker() {
    echo -n "检查 NVIDIA Docker..."
    if ! docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo -e "${YELLOW}⚠ NVIDIA Docker 运行时未安装${NC}"
        echo "   请安装 nvidia-container-toolkit:"
        echo "   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        return 1
    fi
    echo -e "${GREEN}✓${NC}"
    return 0
}

# 检查模型
check_models() {
    echo ""
    echo "检查模型文件..."

    MODELS=(
        "$MODELS_DIR/CosyVoice-300M"
        "$MODELS_DIR/SoulX-FlashHead-1_3B"
    )

    MISSING=0
    for model in "${MODELS[@]}"; do
        if [ ! -d "$model" ]; then
            echo -e "  ${RED}✗${NC} 缺少: $model"
            MISSING=1
        else
            echo -e "  ${GREEN}✓${NC} 找到: $model"
        fi
    done

    if [ $MISSING -eq 1 ]; then
        echo ""
        echo -e "${YELLOW}⚠ 部分模型未下载，请先下载模型${NC}"
        echo "  模型下载地址："
        echo "  - CosyVoice: https://github.com/FunAudioLLM/CosyVoice"
        echo "  - SoulX-FlashHead: https://github.com/FlagAlpha/FlashHead"
        echo ""
        read -p "是否继续？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 构建镜像
build_images() {
    echo ""
    echo "构建 Docker 镜像..."
    cd "$DOCKER_DIR"

    echo -e "${YELLOW}构建 vLLM 镜像...${NC}"
    docker-compose build vllm

    echo -e "${YELLOW}构建 CosyVoice 镜像...${NC}"
    docker-compose build cosyvoice

    echo -e "${YELLOW}构建 SoulX 镜像...${NC}"
    docker-compose build soulx

    echo -e "${YELLOW}构建后端镜像...${NC}"
    docker-compose build backend

    echo -e "${YELLOW}构建 Nginx 镜像...${NC}"
    docker-compose build nginx

    echo -e "${GREEN}✓ 所有镜像构建完成${NC}"
}

# 启动服务
start_services() {
    echo ""
    echo "启动服务..."
    cd "$DOCKER_DIR"

    docker-compose up -d

    echo ""
    echo -e "${GREEN}✓ 服务已启动${NC}"
}

# 显示状态
show_status() {
    echo ""
    echo "服务状态："
    docker-compose ps

    echo ""
    echo "查看日志："
    echo "  docker-compose logs -f [service]"
    echo ""
    echo "服务端点："
    echo "  - 后端 API:  http://localhost:8000"
    echo "  - CosyVoice: http://localhost:8002"
    echo "  - SoulX:      http://localhost:8003"
    echo "  - WebRTC:     ws://localhost:8000/api/v1/webrtc"
}

# 主函数
main() {
    echo "1. 检查环境..."
    check_docker
    check_docker_compose
    check_nvidia_docker || echo -e "${YELLOW}⚠ 警告: GPU 功能可能不可用${NC}"

    echo ""
    echo "2. 检查模型..."
    check_models

    echo ""
    read -p "是否构建镜像？(Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        build_images
    fi

    echo ""
    read -p "是否启动服务？(Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        start_services
        show_status
    fi

    echo ""
    echo -e "${GREEN}部署完成！${NC}"
}

# 运行
main "$@"
