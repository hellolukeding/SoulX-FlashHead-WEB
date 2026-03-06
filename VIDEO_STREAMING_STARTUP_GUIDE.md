# 视频流测试启动指南

## 快速启动

### 1. 启动后端服务

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**预期输出:**
```
🚀 Starting Digital Human Platform Backend...
✅ GPU 可用: NVIDIA GeForce RTX 5090 (31.8 GB)
   CUDA 版本: 12.8
   PyTorch 版本: 2.7.1+cu128
✅ 应用初始化完成
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 验证后端服务

**健康检查:**
```bash
curl http://localhost:8000/health
```

**预期响应:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "cuda_version": "12.8",
  "pytorch_version": "2.7.1+cu128",
  "video_generation": true
}
```

### 3. 打开前端测试页面

**方法 1: 直接打开文件**
```bash
# 在浏览器中打开
file:///opt/digital-human-platform/frontend/video_stream_test.html
```

**方法 2: 使用 HTTP 服务器**
```bash
cd /opt/digital-human-platform/frontend
python -m http.server 8001

# 浏览器访问
http://localhost:8001/video_stream_test.html
```

**方法 3: 使用 Tauri 桌面应用**
```bash
cd /opt/digital-human-platform/desktop_app
npm run dev

# 浏览器访问
http://localhost:1420
```

### 4. 测试视频流

1. 点击"连接并初始化"按钮
2. 等待会话初始化完成（首次加载模型需要时间）
3. 输入文本消息，例如："你好，请介绍一下自己"
4. 点击"发送消息"
5. 观察：
   - AI 文本回复（实时显示）
   - 音频播放（TTS 合成）
   - 视频生成（SoulX-FlashHead）

---

## 预期流程

### 1. 连接阶段
```
[连接] → WebSocket 连接成功
[初始化] → 正在初始化会话...
[初始化] → ✅ 会话初始化成功！现在可以发送消息了
```

### 2. 对话阶段
```
[发送] 用户: 你好，请介绍一下自己
[LLM] AI: 你好！我是数字人助手...
[TTS] 收到音频: wav, 16000Hz
[视频] 生成视频中...
[视频] 收到视频帧: 25 帧
[完成] ✅ 消息处理完成
```

---

## 前端界面说明

### 状态面板
- **连接状态**: 显示 WebSocket 连接状态
- **视频帧数**: 显示接收的视频帧总数
- **聊天消息**: 显示处理的消息数
- **会话ID**: 显示当前会话ID（前8位）

### 控制按钮
- **连接并初始化**: 建立 WebSocket 连接并初始化会话
- **断开连接**: 关闭 WebSocket 连接
- **发送消息**: 发送文本消息到后端

### 日志区域
- 实时显示所有消息和事件
- 不同颜色标识不同类型：
  - 蓝色：信息日志
  - 绿色：成功日志
  - 红色：错误日志

---

## 故障排除

### 问题 1: WebSocket 连接失败
```
错误: 连接错误
```

**解决方案:**
1. 检查后端服务是否启动
   ```bash
   ps aux | grep uvicorn
   ```
2. 检查端口 8000 是否被占用
   ```bash
   lsof -i :8000
   ```
3. 检查防火墙设置
   ```bash
   sudo ufw allow 8000
   ```

### 问题 2: 会话初始化失败
```
错误: 会话初始化失败
```

**解决方案:**
1. 检查 SoulX-FlashHead 模型文件是否存在
   ```bash
   ls -lh /opt/digital-human-platform/models/SoulX-FlashHead-1_3B
   ```
2. 检查 GPU 内存是否足够
   ```bash
   nvidia-smi
   ```
3. 查看后端日志
   ```bash
   tail -f /opt/digital-human-platform/logs/app.log
   ```

### 问题 3: 视频无法播放
```
错误: SourceBuffer 忙碌，跳过此帧
```

**解决方案:**
1. 刷新页面重新连接
2. 检查浏览器是否支持 MSE
3. 尝试使用 Chrome/Edge 浏览器

### 问题 4: 音频无法播放
```
错误: 播放音频失败
```

**解决方案:**
1. 检查浏览器自动播放策略
2. 手动点击播放按钮
3. 调整系统音量

---

## 性能监控

### 后端性能

**查看 GPU 使用情况:**
```bash
watch -n 1 nvidia-smi
```

**查看进程资源使用:**
```bash
htop
```

### 前端性能

**打开浏览器开发者工具 (F12):**
- **Performance 标签**: 查看性能瓶颈
- **Network 标签**: 查看 WebSocket 消息
- **Console 标签**: 查看日志和错误

---

## 日志位置

### 后端日志
```bash
# 应用日志
tail -f /opt/digital-human-platform/logs/app.log

# 错误日志
tail -f /opt/digital-human-platform/logs/error.log

# WebSocket 日志
tail -f /opt/digital-human-platform/logs/websocket.log
```

### 前端日志
- 浏览器开发者工具 Console 标签
- 页面内的日志区域

---

## 配置选项

### 后端配置 (.env)
```bash
# LLM 配置
LLM_MODEL=mimo-v2-flash
OPEN_AI_URL=https://api.xiaomimimo.com/v1
OPEN_AI_API_KEY=your_api_key_here

# TTS 配置
TTS_TYPE=edge
EDGE_TTS_VOICE=zh-CN-YunxiNeural

# ASR 配置
ASR_TYPE=tencent
TENCENT_APPID=your_appid
TENCENT_ASR_SECRET_ID=your_secret_id
TENCENT_ASR_SECRET_KEY=your_secret_key
```

### 前端配置
修改 `video_stream_test.html` 中的 WebSocket URL:
```javascript
const wsUrl = 'ws://192.168.1.132:8000/api/v1/video';
```

---

## 测试消息示例

### 简单问候
```
你好，请介绍一下自己
```

### 提问测试
```
什么是人工智能？
```

### 对话测试
```
今天天气怎么样？
```

### 长文本测试
```
请用3分钟时间详细介绍一下量子计算的原理和应用
```

---

## 下一步

### 如果测试成功
1. ✅ 视频流功能正常
2. ✅ 音视频同步良好
3. ✅ 延迟可接受
4. → 进入性能优化阶段
5. → 开发桌面应用版本

### 如果遇到问题
1. 查看"故障排除"部分
2. 检查后端日志
3. 提交 Issue 到 GitHub

---

## 联系支持

**项目地址:** https://github.com/your-org/digital-human-platform
**文档:** https://github.com/your-org/digital-human-platform/wiki
**Issues:** https://github.com/your-org/digital-human-platform/issues

---

**祝测试顺利！** 🎉
