#!/bin/bash
# CosyVoice TTS 服务部署脚本

set -e

PROJECT_ROOT="/opt/digital-human-platform"
DOCKER_DIR="$PROJECT_ROOT/docker"
MODELS_DIR="$PROJECT_ROOT/models/CosyVoice"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🎵 CosyVoice TTS 服务部署"
echo "========================"
echo ""

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
    if ! docker-compose version &> /dev/null 2>&1 && ! docker compose version &> /dev/null 2>&1; then
        echo -e "${RED}✗ Docker Compose 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC}"
}

# 检查 NVIDIA Docker
check_nvidia() {
    echo -n "检查 NVIDIA Docker..."
    if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 未安装 nvidia-container-toolkit${NC}"
        echo "  GPU 功能可能不可用"
        return 1
    fi
}

# 检查模型
check_model() {
    echo ""
    echo "检查 CosyVoice 模型..."

    if [ ! -d "$MODELS_DIR" ]; then
        echo -e "  ${RED}✗ 模型目录不存在: $MODELS_DIR${NC}"
        echo ""
        echo "请先下载 CosyVoice 模型："
        echo "  git clone https://github.com/FunAudioLLM/CosyVoice.git $MODELS_DIR"
        echo "  cd $MODELS_DIR"
        echo "  # 下载模型文件，参考项目文档"
        echo ""
        return 1
    fi

    echo -e "  ${GREEN}✓${NC} 模型目录存在: $MODELS_DIR"
    return 0
}

# 构建镜像
build() {
    echo ""
    echo "构建 Docker 镜像..."
    cd "$DOCKER_DIR"

    docker-compose -f docker-compose-cosyvoice.yml build cosyvoice

    echo -e "${GREEN}✓ 镜像构建完成${NC}"
}

# 启动服务
start() {
    echo ""
    echo "启动 CosyVoice 服务..."
    cd "$DOCKER_DIR"

    docker-compose -f docker-compose-cosyvoice.yml up -d cosyvoice

    echo ""
    echo -e "${GREEN}✓ CosyVoice 服务已启动${NC}"
    echo ""
    echo "查看日志: docker-compose -f docker-compose-cosyvoice.yml logs -f cosyvoice"
    echo "停止服务: docker-compose -f docker-compose-cosyvoice.yml down"
    echo ""
    echo "服务端点:"
    echo "  - 健康检查:  http://localhost:8002/health"
    echo "  - 标准 TTS:   POST http://localhost:8002/tts"
    echo "  - 流式 TTS:   POST http://localhost:8002/tts/stream"
    echo ""
}

# 测试服务
test() {
    echo ""
    echo "测试 CosyVoice 服务..."

    # 等待服务启动
    echo "等待服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 服务已就绪${NC}"
            break
        fi
        echo "  等待中... ($i/30)"
        sleep 2
    done

    # 健康检查
    echo ""
    echo "健康检查:"
    curl -s http://localhost:8002/health | python3 -m json.tool || true

    # TTS 测试
    echo ""
    echo "TTS 测试 (标准):"
    curl -X POST http://localhost:8002/tts \
        -H "Content-Type: application/json" \
        -d '{"text": "你好，我是数字人助手", "speaker": "default"}' \
        -o /tmp/test_tts.wav \
        -w "\n状态: %{http_code}\n"

    if [ -f /tmp/test_tts.wav ] && [ -s /tmp/test_tts.wav ]; then
        echo -e "${GREEN}✓ 音频生成成功: /tmp/test_tts.wav${NC}"
        echo "  文件大小: $(du -h /tmp/test_tts.wav | cut -f1)"
    else
        echo -e "${YELLOW}⚠ 音频生成失败或模型未加载${NC}"
    fi
}

# 日志
logs() {
    cd "$DOCKER_DIR"
    docker-compose -f docker-compose-cosyvoice.yml logs -f cosyvoice
}

# 停止
stop() {
    echo ""
    echo "停止 CosyVoice 服务..."
    cd "$DOCKER_DIR"

    docker-compose -f docker-compose-cosyvoice.yml down

    echo -e "${GREEN}✓ 服务已停止${NC}"
}

# 重启
restart() {
    stop
    start
}

# 清理
clean() {
    echo ""
    echo "清理容器和镜像..."
    cd "$DOCKER_DIR"

    docker-compose -f docker-compose-cosyvoice.yml down -v
    docker rmi cosyvoice-tts:latest 2>/dev/null || true

    echo -e "${GREEN}✓ 清理完成${NC}"
}

# 帮助
usage() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  build    - 构建 Docker 镜像"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  logs     - 查看日志"
    echo "  test     - 测试服务"
    echo "  clean    - 清理容器和镜像"
    echo "  status   - 查看状态"
    echo ""
    echo "示例:"
    echo "  $0 build     # 构建镜像"
    echo "  $0 start     # 启动服务"
    echo "  $0 test      # 测试服务"
}

# 状态
status() {
    cd "$DOCKER_DIR"
    docker-compose -f docker-compose-cosyvoice.yml ps
}

# 主函数
main() {
    local command="${1:-start}"

    case "$command" in
        build)
            check_docker
            check_docker_compose
            check_model && build
            ;;
        start)
            check_docker
            check_docker_compose
            check_nvidia
            check_model && start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs
            ;;
        test)
            test
            ;;
        clean)
            clean
            ;;
        status)
            status
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            echo "未知命令: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
