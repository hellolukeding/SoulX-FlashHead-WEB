#!/bin/bash

# 开发环境启动脚本

set -e

echo "=== Digital Human Platform - 开发环境启动 ==="
echo ""

# 检查依赖
echo "1. 检查系统依赖..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 未安装"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js 未安装"; exit 1; }
echo "✅ 系统依赖检查通过"
echo ""

# 检查模型
echo "2. 检查模型文件..."
if [ ! -L "models/SoulX-FlashHead-1_3B" ]; then
    echo "⚠️  SoulX-FlashHead 模型软链接不存在"
    echo "创建软链接..."
    ln -s /opt/soulx/SoulX-FlashHead/models/Soul-AILab/SoulX-FlashHead-1_3B models/SoulX-FlashHead-1_3B
    echo "✅ SoulX-FlashHead 软链接已创建"
fi

if [ ! -L "models/wav2vec2-base-960h" ]; then
    echo "⚠️  wav2vec2 模型软链接不存在"
    echo "创建软链接..."
    ln -s /opt/soulx/SoulX-FlashHead/models/facebook/wav2vec2-base-960h models/wav2vec2-base-960h
    echo "✅ wav2vec2 软链接已创建"
fi
echo "✅ 模型文件检查完成"
echo ""

# 启动后端
echo "3. 启动后端服务..."
cd backend

if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
else
    source venv/bin/activate
fi

# 后台启动后端
nohup python -m app.main > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
cd ..

echo ""

# 启动前端
echo "4. 启动前端开发服务器..."
cd desktop_app

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    yarn install
fi

# 前台启动前端
echo "✅ 前端服务启动中..."
echo "   访问: http://localhost:5173"
echo "   API: http://localhost:8000"
echo "   WebSocket: ws://localhost:8000/ws"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    echo "✅ 服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 启动前端
yarn dev

# 清理
cleanup
