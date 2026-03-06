# 🎯 完整测试和调试指南

**最后更新**: 2026-03-06 05:55

---

## 已完成的修复

1. ✅ **SoulX-FlashHead 音频长度修复** - 音频填充到 23040 的倍数
2. ✅ **CosyVoice 模型路径修复** - 使用 `CosyVoice-300M`
3. ✅ **工作目录设置** - `main.py` 已设置正确的 `os.chdir()`
4. ✅ **后端重启** - 使用最新代码

---

## 🔍 调试步骤

### 步骤1: 检查后端状态

```bash
# 健康检查
curl http://localhost:8000/health

# 预期输出:
# {
#   "status": "healthy",
#   "gpu_available": true,
#   "video_generation": true
# }
```

### 步骤2: 打开浏览器开发者工具

1. 打开 http://192.168.1.132:1420/
2. 按 **F12** 打开开发者工具
3. 切换到 **Console** 标签

### 步骤3: 清除缓存并刷新

**Windows/Linux**: **Ctrl + Shift + R**
**Mac**: **Cmd + Shift + R**

### 步骤4: 连接并发送消息

1. 点击绿色电话按钮
2. 点击"消息"按钮
3. 输入: `你好，请介绍一下自己`
4. 点击发送

### 步骤5: 查看调试信息

**在开发者工具 Console 中，您应该看到**:

```
[WS] Connecting to ws://192.168.1.132:8000/api/v1/video
[WS] Connected
[WS] Initializing session...
[WS] Session ID: xxx
[WS] Message received: initialized
[WS] Message received: status
[WS] Message received: ai_audio
[WS] Audio received: wav 16000 Hz
[Audio] Playing audio...
[WS] Message received: video_frame
[WS] Video frame received: XXX frames
[MSE] Buffer busy, added to queue. Queue size: 1
```

---

## 🐛 如果仍然看不到视频

### 检查后端日志

```bash
# 实时查看日志
tail -f /tmp/backend_final.log | grep -E "SoulX|FlashHead|视频|video|ERROR|成功|失败"
```

### 预期日志:

```
[session_id] [1/4] LLM 生成中...
[session_id] [2/4] TTS 合成中...
[session_id] ✅ TTS 合成成功: XX.XX秒
[session_id] [3/4] 视频生成中...
[FlashHead] 音频长度: XXXXX samples (XX.XX秒)
[session_id] ✅ 视频生成成功: XXX 帧
[session_id] ✅ 视频帧已发送
```

### 如果看到错误，请复制完整的错误信息

---

## 📊 可能的结果

### ✅ 成功

- **2-3秒**: 音频开始播放
- **5-10秒**: 视频显示
- **视频内容**: SoulX-FlashHead 生成的数字人说话

### ❌ 失败类型1: 音频播放但无视频

**检查**:
1. 后端日志是否显示 "视频生成成功"?
2. 前端 Console 是否显示 "Video frame received"?
3. MSE 是否正确初始化?

### ❌ 失败类型2: 既无音频也无视频

**检查**:
1. 后端日志是否有错误?
2. WebSocket 连接是否成功?
3. 会话是否初始化成功?

---

## 🔧 手动测试视频生成

如果前端测试失败，可以在后端手动测试:

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate

# 运行测试脚本
python test_video_generation.py
```

**预期输出**:
```
✅ 模型加载成功
音频长度: 48000 samples (3.00秒)
开始生成视频...
✅ 视频生成成功: torch.Size([75, 3, 512, 512])
```

---

## 💡 关键信息

### WebSocket 端点
```
ws://192.168.1.132:8000/api/v1/video
```

### 消息格式

**初始化**:
```json
{
  "type": "init",
  "data": {
    "reference_image": "default"
  }
}
```

**发送消息**:
```json
{
  "type": "message",
  "data": {
    "text": "你好"
  }
}
```

### 预期响应

1. `connected` - 连接成功
2. `initialized` - 会话初始化成功
3. `status` - 处理状态（可选）
4. `ai_audio` - TTS 音频
5. `video_frame` - 视频帧
6. `complete` - 处理完成

---

## 📝 请反馈以下信息

1. **音频是否播放？** (是/否)
2. **视频是否显示？** (是/否)
3. **后端日志的最后20行** (复制粘贴)
4. **前端 Console 的最后10行** (复制粘贴)

---

**立即测试并告诉我结果！** 🚀
