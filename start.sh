#!/bin/bash

# 数字人平台启动脚本
# Digital Human Platform Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/opt/digital-human-platform"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_FILE="$PROJECT_DIR/frontend/test_client.html"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🤖 数字人平台启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查虚拟环境
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在，请先创建:${NC}"
    echo "cd $BACKEND_DIR && python -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo -e "${GREEN}[1/3]${NC} 激活虚拟环境..."
cd "$BACKEND_DIR"
source venv/bin/activate

# 检查依赖
echo -e "${GREEN}[2/3]${NC} 检查依赖..."
python -c "import fastapi" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  依赖未安装，正在安装...${NC}"
    pip install -r requirements.txt
}

# 启动后端服务
echo -e "${GREEN}[3/3]${NC} 启动后端服务..."
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 后端服务启动中...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "📍 服务地址:"
echo -e "   - API 文档: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "   - WebSocket: ${GREEN}ws://localhost:8000/ws?token=test${NC}"
echo -e "   - 测试页面: ${GREEN}file://$FRONTEND_FILE${NC}"
echo ""
echo -e "${YELLOW}💡 提示:${NC}"
echo -e "   1. 在浏览器中打开测试页面: ${GREEN}file://$FRONTEND_FILE${NC}"
echo -e "   2. 点击 \"连接服务器\" 按钮"
echo -e "   3. 点击 \"创建会话\" 按钮"
echo -e "   4. 输入文本并点击 \"发送文本\" 或使用 \"录音\" 功能"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo ""

# 启动 FastAPI 服务
python -m app.main
