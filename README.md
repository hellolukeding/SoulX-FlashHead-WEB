# SoulX-FlashHead-WEB

实时数字人 Web 平台 - 基于 SoulX-FlashHead 的实时音频驱动数字人视频生成系统

## 🌟 特性

- ✅ **实时生成**：基于 SoulX-FlashHead 1.3B 模型，支持实时视频生成
- ⚡ **高性能**：RTX 5090 可达 126 FPS，5 倍实时速度
- 🔄 **流式处理**：支持音频流式输入，视频流式输出
- 👥 **多并发**：单卡支持 4-5 个并发会话
- 🎨 **现代架构**：前后端分离，REST API + WebSocket
- 💻 **桌面应用**：基于 Tauri 的跨平台桌面应用

## 🏗️ 技术栈

### 后端
- **框架**：FastAPI
- **AI 模型**：SoulX-FlashHead 1.3B + wav2vec2-base-960h
- **通信**：WebSocket + REST API
- **Python**：3.10+

### 前端
- **框架**：React 19 + TypeScript
- **UI 库**：Ant Design + TailwindCSS
- **桌面**：Tauri 2.0
- **构建**：Vite

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 22+
- CUDA 12.8
- RTX 4090/5090 GPU

### 安装

```bash
# 克隆仓库
git clone https://github.com/hellolukeding/SoulX-FlashHead-WEB.git
cd SoulX-FlashHead-WEB

# 启动开发环境
./scripts/dev.sh
```

详细说明请查看 [START_HERE.md](START_HERE.md)

## 📊 性能数据

| 指标 | 数据 |
|------|------|
| 生成速度 | 126 FPS (RTX 5090) |
| 实时倍数 | 5 倍实时 |
| 并发会话 | 4-5 个 |
| 端到端延迟 | 1.5-2.5 秒 |

## 📖 文档

### 快速开始
- [🚀 快速开始指南](QUICK_START.md) - 新手入门
- [📁 项目结构](PROJECT_STRUCTURE.md) - 目录组织说明
- [📋 开发方案](docs/development/development-plan.md) - 完整开发计划
- [📊 项目总结](docs/reports/PROJECT_COMPLETION_SUMMARY.md) - 项目结构和状态

### 技术文档
- [🏗️ 系统架构](docs/architecture.md) - 系统设计文档
- [🔌 REST API](docs/api/rest-api.md) - REST 接口文档
- [🔌 WebSocket API](docs/api/websocket-api.md) - WebSocket 接口文档

### 测试文档
- [🧪 测试报告](docs/testing/TESTING_SUMMARY.md) - 测试总结
- [📊 测试仪表板](docs/testing/TEST_DASHBOARD.md) - 测试状态

### 项目报告
- [🎉 CosyVoice 测试成功](docs/reports/COSYVOICE_TEST_SUCCESS.md) - 最新测试结果
- [✅ 完整测试报告](docs/testing/FINAL_TESTING_REPORT.md) - 测试框架完成

### 运维文档
- [🔑 多账户配置](docs/operations/multi-account-guide.md) - Git 多账户设置
- [📤 推送指南](docs/operations/push-guide.md) - 代码推送指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 许可证

MIT License

## 🙏 致谢

- [SoulX-FlashHead](https://github.com/Soul-AILab/SoulX-FlashHead) - 核心模型
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://react.dev/) - UI 框架
- [Tauri](https://tauri.app/) - 桌面应用框架
