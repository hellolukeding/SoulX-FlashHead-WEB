# 🚀 测试视频流 - 已修复版本

**修复时间:** 2026-03-06 05:03

---

## ✅ 已修复的问题

### 1. **错误处理修复**
- ✅ 修复了 `KeyError: 'audio_format'` 错误
- ✅ 添加了空音频/视频的处理逻辑
- ✅ 改进了错误消息返回

### 2. **LLM 测试模式**
- ✅ 当 LLM 未配置时，自动使用测试响应
- ✅ 测试响应：`"你好！收到你的消息：「{text}」。..."`
- ✅ 保证始终有文本返回

### 3. **TTS 处理**
- ✅ 即使 TTS 失败也不会崩溃
- ✅ 返回空的音频数据而不是错误

---

## 🔄 现在请重新测试

### 步骤 1: 刷新前端页面

在浏览器中按 **F5** 或 **Ctrl+R** 刷新页面

### 步骤 2: 重新连接

1. 点击绿色电话按钮（接听）
2. 等待 "✅ 会话初始化成功"

### 步骤 3: 发送消息

1. 点击"消息"按钮打开聊天侧边栏
2. 输入任何文本，例如："你好"
3. 点击发送

### 步骤 4: 观察结果

**应该看到：**

1. **AI 文本回复**（聊天侧边栏）
   ```
   你好！收到你的消息：「你好」。
   我是一个数字人助手，很高兴为你服务。
   ```

2. **后端日志**（终端）
   ```bash
   tail -f /tmp/backend.log
   ```

   应该看到：
   ```
   [session_id] 处理消息 #1: 你好
   [session_id] LLM 生成失败，使用测试响应
   [session_id] AI: 你好！收到你的消息...
   [session_id] TTS 合成中...
   [session_id] 生成视频中...
   [session_id] ✅ 生成 33 帧视频
   [session_id] 发送视频帧: 33 帧, ~1.4 MB
   [session_id] ✅ 视频帧已发送
   ```

3. **前端日志**（浏览器控制台，F12）
   ```
   [WS] Message received: ai_text_chunk
   [WS] Audio received: wav, 16000Hz
   [Audio] Playing audio...
   [WS] Video frame received: 33 frames
   [MSE] Buffer busy, added to queue
   ```

---

## 🎬 预期结果

### 成功的标志

✅ **文本**: AI 回复显示在聊天侧边栏
✅ **音频**: 听到 AI 语音（Edge TTS 合成）
✅ **视频**: 看到数字人视频（SoulX-FlashHead 生成）

### 如果视频仍然不显示

**检查：**
1. 浏览器控制台是否有 `[MSE]` 相关错误？
2. 视频播放器是否初始化成功？
3. 是否收到 `video_frame` 消息？

**如果一切正常但看不到视频：**
- 可能是 MSE 队列问题
- 尝试刷新页面重新连接

---

## 🐛 已知限制

### 当前测试模式

由于 LLM 未配置 API key，系统使用测试响应：

**优点：**
- ✅ 可以测试完整流程
- ✅ 不需要配置 API key
- ✅ 快速验证功能

**缺点：**
- ❌ AI 回复是固定的
- ❌ 不是真正的对话

### 配置 LLM（可选）

如果需要真正的对话，配置 API key：

```bash
cd /opt/digital-human-platform/backend
nano .env

# 添加：
OPEN_AI_API_KEY=your_api_key_here
```

然后重启后端：
```bash
pkill -f uvicorn
# 重新启动
```

---

## 📊 测试检查清单

测试前确认：

- [ ] 后端服务正在运行（`ps aux | grep uvicorn`）
- [ ] 前端页面已刷新
- [ ] 会话已初始化（看到 "✅ 会话初始化成功"）
- [ ] 已发送消息
- [ ] 浏览器控制台打开（F12）

测试结果：

- [ ] AI 文本回复显示 ✅/❌
- [ ] 音频播放正常 ✅/❌
- [ ] 视频显示正常 ✅/❌
- [ ] 后端日志无错误 ✅/❌

---

## 🔧 故障排除

### 问题：仍然看不到视频

**诊断步骤：**

1. **检查浏览器控制台**
   ```
   [MSE] SourceBuffer created
   [MSE] MediaSource opened
   [WS] Video frame received: 33 frames
   ```

   如果看到这些消息，说明数据已接收。

2. **检查视频元素**
   ```javascript
   // 在浏览器控制台运行
   document.querySelector('video').readyState
   ```

   应该返回 4 (HAVE_ENOUGH_DATA)

3. **检查 MSE 状态**
   ```javascript
   // 在浏览器控制台运行
   const mediaSource = new MediaSource()
   mediaSource.sourceBuffers.length
   ```

### 问题：音频无法播放

**检查：**
- 扬声器是否开启
- 浏览器是否阻止了自动播放
- 尝试手动点击播放

### 问题：后端崩溃

**查看日志：**
```bash
tail -50 /tmp/backend.log
```

**重启后端：**
```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📝 总结

### 修复内容

✅ 错误处理改进
✅ LLM 测试模式
✅ TTS 失容处理
✅ WebSocket 消息格式修复

### 可以测试

✅ 完整对话流程
✅ 音频播放
✅ 视频生成和播放
✅ 聊天历史记录

### 下一步

1. **测试功能** - 验证所有组件正常工作
2. **配置 LLM** - 添加 API key 获得真正的对话
3. **性能优化** - 根据测试结果优化

---

**现在请刷新前端页面，发送消息测试！** 🚀

如有问题，请查看浏览器控制台和后端日志。
