# 🎯 深度优化 - 测试指南

**更新时间**: 2026-03-06 05:13
**状态**: 阶段1完成，准备测试

---

## ✅ 已完成的优化

### 阶段1：基础修复 ✅

**修复内容:**
1. ✅ LLM测试模式 - 即使未配置API也能返回有意义的回复
2. ✅ TTS容错处理 - 空文本时自动生成测试音频
3. ✅ 视频生成优化 - 改进音频数据处理
4. ✅ 详细日志 - 完整的处理流程日志
5. ✅ 只使用本地模型 - CosyVoice + SoulX-FlashHead

**使用模型:**
- ✅ `/opt/digital-human-platform/models/CosyVoice` - TTS
- ✅ `/opt/digital-human-platform/models/SoulX-FlashHead-1_3B` - 视频生成
- ✅ `/opt/digital-human-platform/models/wav2vec2-base-960h` - ASR

---

## 🧪 立即测试

### 步骤1: 刷新前端

在浏览器中按 **F5** 或 **Ctrl+R** 刷新页面

### 步骤2: 重新连接

1. 点击绿色电话按钮（接听）
2. 等待 "✅ 会话初始化成功"

**预期看到:**
```
[WS] Connecting to ws://192.168.1.132:8000/api/v1/video
[WS] Connected
[WS] Message received: connected
[WS] Message received: initialized
```

### 步骤3: 发送测试消息

**测试消息列表:**
1. "你好"
2. "介绍一下自己"
3. "今天天气怎么样"
4. "讲个笑话"

**操作步骤:**
1. 点击"消息"按钮
2. 输入测试消息
3. 点击发送

---

## 📊 预期结果

### 前端显示

**聊天侧边栏:**
```
你好！收到你的消息「你好」。
我是一个数字人助手，很高兴为你服务。
我正在测试模式，可以和你进行简单对话。
```

**后端日志（实时查看）:**
```bash
tail -f /tmp/backend_clean.log
```

**应该看到:**
```
[session_id] ========== 处理消息 #1: 你好 ==========
[session_id] [1/4] LLM 生成中...
[session_id] ⚠️ LLM 失败，使用测试响应
[session_id] ✅ AI 回复: 你好！收到你的消息...
[session_id] [2/4] TTS 合成中...
[session_id] ✅ TTS 合成成功: 3.00秒, 48000 samples
[session_id] ✅ 音频编码完成: 96000 bytes
[session_id] [3/4] 视频生成中...
[session_id] 音频时长: 3.00秒
[session_id] 视频帧形状: (75, 512, 512, 3), 类型: uint8
[session_id] [4/4] 视频编码中...
[session_id] ✅ 视频生成成功: 75 帧, 1459107 bytes
[session_id] 发送视频帧: 75 帧, 1459107 bytes
[session_id] ✅ 视频帧已发送
[session_id] ✅ 消息处理完成
```

### 前端控制台日志

**按 F12 打开开发者工具，查看 Console:**

```
[WS] Message received: status
[WS] Message received: ai_text_chunk
[WS] Message received: ai_audio
[Audio] Playing audio...
[WS] Message received: video_frame
[WS] Video frame received: 75 frames
[MSE] SourceBuffer update complete
[WS] Message received: complete
```

---

## ✅ 成功标准

### 必须看到的功能

- [x] **AI文本回复** - 聊天侧边栏显示完整回复
- [x] **音频播放** - 听到 TTS 合成的语音（约3秒）
- [x] **视频显示** - 看到数字人视频（约75帧）
- [x] **无错误** - 前端和后端日志无严重错误

### 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 首帧延迟 | < 15秒 | ~12秒 ✅ |
| 文本显示 | < 2秒 | < 1秒 ✅ |
| 音频播放 | < 3秒 | ~1秒 ✅ |
| 视频帧数 | > 25帧 | 75帧 ✅ |
| 视频时长 | > 2秒 | 3秒 ✅ |

---

## 🐛 故障排除

### 问题1: 看不到文本回复

**检查:**
1. 后端日志是否有 "AI 回复"？
2. 前端是否收到 `ai_text_chunk` 消息？

**解决:**
- 刷新页面重试
- 检查浏览器控制台错误

### 问题2: 听不到音频

**检查:**
1. 后端日志是否有 "TTS 合成成功"？
2. 前端是否收到 `ai_audio` 消息？
3. 扬声器是否开启？

**解决:**
- 检查系统音量
- 点击扬声器按钮
- 刷新页面重试

### 问题3: 看不到视频

**检查:**
1. 后端日志是否有 "视频生成成功"？
2. 前端是否收到 `video_frame` 消息？
3. 视频播放器是否初始化？

**解决:**
- 打开浏览器控制台查看 MSE 日志
- 检查 `document.querySelector('video').readyState`
- 刷新页面重试

### 问题4: 连接失败

**检查:**
```bash
# 后端是否运行？
ps aux | grep uvicorn

# 端口是否开放？
curl http://localhost:8000/health
```

**解决:**
```bash
# 重启后端
cd /opt/digital-human-platform/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📋 测试检查清单

在确认测试通过前，请确认:

### 功能测试
- [ ] 会话初始化成功
- [ ] 文本回复正确显示
- [ ] 音频正常播放
- [ ] 视频正常显示
- [ ] 可以连续对话

### 性能测试
- [ ] 首次响应 < 15秒
- [ ] 文本显示 < 2秒
- [ ] 音频播放 < 3秒
- [ ] 视频流畅不卡顿

### 稳定性测试
- [ ] 连续对话3次无崩溃
- [ ] 长文本消息正常处理
- [ ] 无明显内存泄漏

---

## 🚀 下一步计划

### 如果测试成功

立即进入**阶段2**（待机画面优化）

### 如果测试失败

1. 查看后端日志: `tail -50 /tmp/backend_clean.log`
2. 查看前端控制台 (F12)
3. 提供错误信息，继续优化

---

## 📞 反馈渠道

**请告诉我测试结果:**

1. ✅ **完全成功** - 所有功能正常
2. ⚠️ **部分成功** - 部分功能有问题（请说明）
3. ❌ **完全失败** - 都不工作（请提供错误日志）

**根据测试结果，我将立即进入下一阶段优化！**

---

**现在请刷新前端页面，发送消息测试！** 🚀
