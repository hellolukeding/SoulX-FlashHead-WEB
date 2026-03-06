# 🚀 Stage 2 部署和测试指南

**更新时间**: 2026-03-06
**状态**: ✅ 代码已完成，待部署测试

---

## 📦 已完成的改进

### 后端优化

**文件**: `backend/app/api/websocket/video_stream_stage2.py` ✅ **NEW**

**新增功能**:
1. ✅ 实时状态反馈 (`_send_status`方法)
2. ✅ 音频优先播放（立即发送音频，不等待视频）
3. ✅ 三阶段进度指示：
   - `thinking`: 正在理解您的问题... (10-30%)
   - `tts`: 正在合成语音... (30-60%)
   - `generating`: 正在生成视频画面... (60-90%)
   - `playing`: 正在播放... (100%)

**关键改进**:
```python
# 🎯 关键：音频优先策略
if audio_b64:
    await websocket.send_json({
        "type": "ai_audio",
        "data": {
            "audio_data": audio_b64,
            "audio_format": "wav",
            "sample_rate": 16000
        }
    })
    logger.info(f"✅ 音频已发送（音频优先策略）")

# 然后才生成视频（后台进行）
await self._send_status(websocket, "generating", 60, "正在生成视频画面...")
```

### 路由更新

**文件**: `backend/app/api/websocket/websocket.py` ✅ **UPDATED**

**变更**:
```python
# 从
from app.api.websocket import video_stream
router.include_router(video_stream.router, tags=["video_stream"])

# 改为
from app.api.websocket import video_stream_stage2  # 阶段2优化版
router.include_router(video_stream_stage2.router, tags=["video_stream"])
```

### 前端改进（已完成部分）

**文件**: `desktop_app/src/components/VideoChat.tsx`

**已完成**:
1. ✅ 添加 `processingState` 状态管理
2. ✅ 添加 `status` 消息处理
3. ✅ 发送消息时立即显示"思考中"状态
4. ✅ 音频、视频播放时更新进度

**待添加**:
- [ ] 待机动画覆盖层（UI）

---

## 🚀 部署步骤

### Step 1: 重启后端

```bash
cd /opt/digital-human-platform/backend

# 激活虚拟环境
source venv/bin/activate

# 重启后端服务
pkill -f uvicorn  # 停止现有服务

# 启动后端（带日志）
nohup python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > /tmp/backend_stage2.log 2>&1 &

# 查看启动日志
tail -f /tmp/backend_stage2.log
```

### Step 2: 刷新前端

**浏览器操作**:
1. 打开前端页面 (http://192.168.1.132:5173)
2. 按 **F5** 或 **Ctrl+R** 刷新
3. 清除缓存（如果需要）：**Ctrl+Shift+R**

### Step 3: 测试流程

#### 测试步骤

1. **点击绿色电话按钮**（接听）
2. **等待初始化**：
   ```
   预期看到：
   - ✅ "✅ 会话初始化成功！现在可以发送消息了"
   ```

3. **点击"消息"按钮**

4. **输入测试消息**：`你好`

5. **点击发送**

6. **观察改进**：
   ```
   预期看到：
   ✅ 1秒内显示："正在理解您的问题..."
   ✅ 2-3秒内显示："正在合成语音..."
   ✅ 音频开始播放（不等待视频！）
   ✅ 5-8秒内显示："正在生成视频画面..."
   ✅ 视频最终显示
   ```

---

## 📊 预期改进效果

### 优化前（阶段1）

```
用户: 你好
      ↓ 空白 10秒 ❌
      ↓ 音频和视频同时出现
用户感受: 😡 系统卡死了吗？
```

### 优化后（阶段2）

```
用户: 你好
      ↓ 1秒 ✅
      ↓ 显示 "正在理解您的问题..."
      ↓ 2-3秒
      ↓ 显示 "正在合成语音..."
      ↓ 音频立即播放 ✅
      ↓ 5-8秒
      ↓ 显示 "正在生成视频画面..."
      ↓ 视频显示
用户感受: 😊 系统在工作，有反馈
```

---

## 🐛 故障排除

### 问题1: 后端启动失败

**检查**:
```bash
# 检查语法错误
cd /opt/digital-human-platform/backend
python -m py_compile app/api/websocket/video_stream_stage2.py

# 检查导入
python -c "from app.api.websocket import video_stream_stage2"
```

**解决**:
- 查看错误日志: `tail -50 /tmp/backend_stage2.log`
- 修复语法错误
- 确保所有依赖已安装

### 问题2: 前端看不到状态更新

**检查**:
1. 打开浏览器开发者工具 (F12)
2. 查看 Console 标签
3. 查看 WebSocket 消息

**预期看到**:
```javascript
[WS] Message received: status
[WS] Message received: ai_audio
[WS] Audio received: wav 16000 Hz
[WS] Message received: video_frame
```

**解决**:
- 刷新页面 (F5)
- 清除浏览器缓存
- 检查后端是否发送了status消息

### 问题3: 音频仍然延迟

**检查后端日志**:
```bash
tail -f /tmp/backend_stage2.log | grep "音频已发送"
```

**预期看到**:
```
[session_id] ✅ 音频已发送（音频优先策略）
[session_id] [3/4] 视频生成中...
```

**解决**:
- 确认使用的是 `video_stream_stage2.py`
- 检查音频生成时间
- 查看TTS性能

---

## 📋 测试检查清单

### 功能测试

- [ ] 后端启动成功
- [ ] 前端连接成功
- [ ] 会话初始化成功
- [ ] 发送消息后立即看到状态提示
- [ ] 音频在2-3秒内开始播放
- [ ] 视频最终显示
- [ ] 进度条正常更新
- [ ] 状态消息正确显示（思考→语音→视频）

### 性能测试

- [ ] 首次反馈时间 < 2秒 ✅
- [ ] 音频播放时间 < 3秒 ✅
- [ ] 视频显示时间 < 12秒 ✅
- [ ] 无明显空白期 ✅

### 用户体验测试

- [ ] 用户知道系统正在工作 ✅
- [ ] 有明确的进度指示 ✅
- [ ] 音频优先播放改善体验 ✅
- [ ] 整体体验流畅 ✅

---

## 🔍 日志查看

### 后端日志

```bash
# 实时查看
tail -f /tmp/backend_stage2.log

# 查看特定会话
tail -f /tmp/backend_stage2.log | grep "session_id"

# 查看错误
tail -f /tmp/backend_stage2.log | grep -E "ERROR|WARN"
```

### 前端日志

**浏览器开发者工具 (F12)**:
```javascript
// Console标签查看WebSocket消息
[WS] Message received: status
[WS] Message received: ai_audio
[WS] Message received: video_frame
```

---

## 📈 监控指标

### 关键指标

| 指标 | 阶段1 | 阶段2 | 目标 |
|------|-------|-------|------|
| 首次反馈时间 | 12秒 | <2秒 | ✅ |
| 音频播放时间 | 12秒 | <3秒 | ✅ |
| 用户感知延迟 | 12秒 | <2秒 | ✅ |
| 进度可见性 | 无 | 有 | ✅ |

---

## 🎯 下一步

### 如果测试成功 ✅

立即进入**阶段3**：分段视频生成（流式传输）

**准备工作**:
1. 实现视频分段生成（1秒一段）
2. 前端流式播放
3. 进一步降低延迟到 < 3秒

### 如果测试失败 ❌

1. 查看错误日志
2. 修复问题
3. 重新测试
4. 直到成功为止

---

## 📝 总结

**阶段2优势**:
1. ✅ 快速部署（替换一个文件）
2. ✅ 立即改善用户体验
3. ✅ 音频优先策略
4. ✅ 详细进度反馈
5. ✅ 为WebRTC迁移做准备

**虽然架构未变，但体验大幅改善！**

---

## 🚀 立即开始测试

```bash
# 1. 重启后端
cd /opt/digital-human-platform/backend
source venv/bin/activate
pkill -f uvicorn
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend_stage2.log 2>&1 &

# 2. 刷新前端（浏览器按F5）

# 3. 发送消息测试

# 4. 反馈结果
```

---

**准备就绪，开始测试！** 🚀
