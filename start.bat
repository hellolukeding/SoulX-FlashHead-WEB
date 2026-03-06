@echo off
REM 数字人平台启动脚本 (Windows)
REM Digital Human Platform Startup Script

setlocal

echo ========================================
echo 🤖 数字人平台启动脚本
echo ========================================
echo.

REM 项目路径
set PROJECT_DIR=%~dp0
set BACKEND_DIR=%PROJECT_DIR%backend
set FRONTEND_FILE=%PROJECT_DIR%frontend\test_client.html

REM 检查虚拟环境
if not exist "%BACKEND_DIR%\venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先创建:
    echo cd %BACKEND_DIR% && python -m venv venv
    pause
    exit /b 1
)

REM 激活虚拟环境
echo [1/3] 激活虚拟环境...
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat

REM 检查依赖
echo [2/3] 检查依赖...
python -c "import fastapi" 2>nul || (
    echo ⚠️  依赖未安装，正在安装...
    pip install -r requirements.txt
)

REM 启动后端服务
echo [3/3] 启动后端服务...
echo.
echo ========================================
echo ✅ 后端服务启动中...
echo ========================================
echo.
echo 📍 服务地址:
echo    - API 文档: http://localhost:8000/docs
echo    - WebSocket: ws://localhost:8000/ws?token=test
echo    - 测试页面: %FRONTEND_FILE%
echo.
echo 💡 提示:
echo    1. 在浏览器中打开测试页面: %FRONTEND_FILE%
echo    2. 点击 "连接服务器" 按钮
echo    3. 点击 "创建会话" 按钮
echo    4. 输入文本并点击 "发送文本" 或使用 "录音" 功能
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 启动 FastAPI 服务
python -m app.main

pause
