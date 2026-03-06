# 🚀 快速开始指南

欢迎使用实时数字人平台！

## ✅ 项目已创建

项目结构已成功创建，包含：
- ✅ 完整的目录结构
- ✅ 后端基础代码（FastAPI）
- ✅ 前端应用（React + TypeScript + Tauri）
- ✅ 完整的文档（API、架构）
- ✅ 开发脚本

## 📂 项目结构

```
digital-human-platform/
├── docs/              # 📚 文档
├── backend/           # 🔧 后端（Python + FastAPI）
├── desktop_app/       # 🎨 前端（React + TypeScript）
├── deployment/        # 🚀 部署配置
├── scripts/           # 🔧 开发脚本
├── models/            # 🤖 模型文件（软链接）
└── examples/          # 📁 示例文件
```

## 🎯 下一步操作

### 选项 1: 查看文档 📖

```bash
# 查看项目说明
cat README.md

# 查看系统架构
cat docs/architecture.md

# 查看 API 文档
cat docs/api/rest-api.md
cat docs/api/websocket-api.md

# 查看项目总结
cat PROJECT_SUMMARY.md
```

### 选项 2: 启动开发环境 🚀

```bash
# 一键启动（后端 + 前端）
./scripts/dev.sh

# 或者手动启动
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main

# 前端
cd desktop_app
yarn install
yarn dev
```

### 选项 3: 开始开发 💻

#### 后端开发
```bash
cd backend/app/core

# 实现推理引擎
cd inference
# TODO: 封装 SoulX-FlashHead 模型

# 实现 WebSocket 服务
cd ../api/websocket
# TODO: 实现 WebSocket 处理器
```

#### 前端开发
```bash
cd desktop_app/src

# 集成 WebSocket
# 修改 api/client.ts
# 修改 components/VideoChat.tsx

# 添加实时功能
# 修改 utils/audio.ts
```

## 📊 技术栈

### 后端
- FastAPI (Web 框架)
- SoulX-FlashHead (AI 推理)
- WebSocket (实时通信)

### 前端
- React 19 (UI 框架)
- TypeScript (类型安全)
- Ant Design (UI 组件)
- Tauri (桌面应用)

## 🎓 学习资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Tauri 文档](https://tauri.app/)

## 📞 获取帮助

- 查看 `docs/` 目录下的文档
- 查看 `PROJECT_SUMMARY.md` 了解项目状态
- 查看 `README.md` 了解项目概述

## 🎉 准备就绪！

项目已创建完成，你现在可以：
1. 阅读文档了解架构
2. 启动开发环境
3. 开始实现核心功能

**祝开发顺利！** 🚀
