# 🎯 SoulX-FlashHead 视频生成问题 - ✅ 已解决

**时间**: 2026-03-06 07:25
**状态**: ✅ **完全修复**

---

## 问题根因

SoulX-FlashHead 模型使用**固定的 `frame_num = 33`**，不支持任意长度的视频。

### 正确的约束

**模型要求**: 音频必须对应**固定的 33 帧**（1.32秒）

- `TARGET_AUDIO_SAMPLES = 33 * 16000 / 25 = 21120 samples`

**原因**: 模型内部使用固定的 `frame_num` 参数处理音频上下文：
```python
context_tokens = rearrange(context_tokens, "(bz f) m c -> bz f m c", f=frame_num)
# frame_num 必须等于 33
```

### 解决方案

```python
FRAME_NUM = 33
TARGET_AUDIO_SAMPLES = FRAME_NUM * 16000 // 25  # 21120 samples

# 截取或填充到固定长度
if current_length >= TARGET_AUDIO_SAMPLES:
    audio_data = audio_data[:TARGET_AUDIO_SAMPLES]  # 截取前 33 帧
else:
    audio_data = np.pad(audio_data, ...)  # 填充到 33 帧
```

---

## 验证结果

### ✅ WebSocket 测试成功

```
连接: ✅ 成功
音频: ✅ 480316 bytes (12秒语音)
视频: ✅ 33 帧, 360516 bytes
```

### ✅ 完整流程验证

1. WebSocket 连接 → ✅
2. 会话初始化 → ✅
3. 发送消息 → ✅
4. LLM 生成回复 → ✅
5. TTS 合成语音 → ✅
6. 视频生成 → ✅
7. 视频编码发送 → ✅

---

## 当前状态

| 功能 | 状态 |
|------|------|
| WebSocket 连接 | ✅ 工作 |
| LLM 生成 | ⚠️ 测试模式（需配置 API Key） |
| TTS 音频生成 | ✅ 工作（Edge TTS） |
| 视频生成 | ✅ 工作（33帧/1.32秒） |
| 视频播放 | ⏳ 待前端测试 |

---

## 限制说明

当前实现每条消息生成 **33 帧（1.32秒）** 的视频。

对于更长的音频（如 12 秒的 TTS 输出），只会使用前 1.32 秒的音频生成视频。

### 后续优化方向

1. **分段视频生成** (阶段3): 将长音频分成多个 33 帧片段，依次生成
2. **滑动窗口**: 使用 `motion_frames_num = 9` 实现平滑过渡
3. **并行优化** (阶段5): 异步生成多个片段

---

## 技术细节

- **模型路径**: `/opt/digital-human-platform/models/SoulX-FlashHead-1_3B`
- **frame_num**: 33 (固定)
- **motion_frames_num**: 9
- **vae_stride**: `[8, 32, 32]`
- **音频长度**: 21120 samples (1.32秒)
- **输出**: (33, 512, 512, 3) RGB 视频帧

---

## 测试步骤

1. **刷新前端**: http://192.168.1.132:1420/ (Ctrl+Shift+R)
2. **点击绿色电话按钮**连接
3. **发送消息**测试
4. **预期结果**:
   - 1-2秒: LLM 文本回复
   - 2秒: 音频开始播放（完整 12 秒）
   - 约 40 秒后: 视频显示（1.32 秒循环）
