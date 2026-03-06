# 🔄 实时数字人平台 - 完整业务流程

**文档版本:** 2.0
**更新日期:** 2026-03-05
**技术栈:** React + FastAPI + SoulX-FlashHead + WebSocket + ASR + LLM + TTS

---

## ⚠️ 重要说明

**关于 SoulX-FlashHead 模型能力:**

❌ **常见误解:** 数字人模型生成视频和语音
✅ **实际情况:** SoulX-FlashHead **仅生成视频**，不生成音频

**详细验证:** 请参阅 [`docs/verification/MODEL_CAPABILITIES_VERIFICATION.md`](./verification/MODEL_CAPABILITIES_VERIFICATION.md)

---

## 📖 业务概述

**核心功能:** 智能实时数字人对话系统

### 系统定义

我们的数字人平台是一个**智能对话系统**，包含以下核心能力:

1. 👂 **语音识别 (ASR)** - 理解用户说了什么
2. 🧠 **智能对话 (LLM)** - AI 思考并生成回复
3. 🔊 **语音合成 (TTS)** - 生成 AI 的语音
4. 🎬 **视频生成** - 生成口型同步的数字人视频

### 两种业务模式

**模式 A: 智能对话模式 (完整功能)**
```
用户说话 → ASR识别 → LLM思考 → TTS生成 → 数字人视频 → 用户看到AI回复
```

**模式 B: 口型同步模式 (简化版)**
```
用户说话 → 直接生成视频 → 用户看到自己的话由数字人说出
```

📌 **本文档重点描述模式 A（智能对话模式）**，这是用户真正需要的"智能数字人"系统。

**关键特点:**
- ⚡ **低延迟**: 1.5-2.5 秒端到端延迟
- 🎬 **实时生成**: 25 FPS 视频流
- 👥 **多并发**: 支持 4-5 个并发会话
- 🎨 **个性化**: 支持自定义数字人形象

---

## 👤 用户视角的业务流程

### 第一步：选择数字人形象

```
用户操作：
┌─────────────────────────┐
│  1. 打开应用            │
│  2. 上传/选择参考图像   │
│  3. 预览数字人形象      │
│  4. 点击"开始对话"      │
└─────────────────────────┘

系统响应：
┌─────────────────────────┐
│ ✓ 加载参考图像         │
│ ✓ 初始化 AI 模型        │
│ ✓ 显示"准备就绪"        │
│ ✓ 等待用户说话          │
└─────────────────────────┘
```

**预期时间:** 2-5 秒（模型加载）

---

### 第二步：实时对话

```
用户操作：
┌─────────────────────────┐
│  1. 按住"说话"按钮      │
│  2. 对着麦克风说话      │
│  3. 松开按钮           │
│  4. 观看数字人回应      │
└─────────────────────────┘

系统响应：
┌─────────────────────────┐
│ ✓ 实时录制音频         │
│ ✓ 流式发送到服务器     │
│ ✓ AI 生成视频流        │
│ ✓ 数字人"说"出内容     │
└─────────────────────────┘
```

**预期时间:** 1.5-2.5 秒（从说话到看到数字人回应）

---

### 第三步：持续对话

```
用户操作：
┌─────────────────────────┐
│  循环:                 │
│  说话 → 等待 → 观看    │
│  说话 → 等待 → 观看    │
│  ...                  │
└─────────────────────────┘

系统响应：
┌─────────────────────────┐
│  持续接收音频流        │
│  持续生成视频流        │
│  持续播放视频          │
└─────────────────────────┘
```

**体验:** 流畅的对话体验，像真人视频通话一样

---

### 第四步：结束对话

```
用户操作：
┌─────────────────────────┐
│  1. 点击"结束对话"      │
│  2. 确认结束           │
│  3. 查看会话统计        │
└─────────────────────────┘

系统响应：
┌─────────────────────────┐
│ ✓ 停止录制             │
│ ✓ 处理剩余音频         │
│ ✓ 释放资源             │
│ ✓ 显示统计信息         │
│   （时长、帧数等）     │
└─────────────────────────┘
```

---

## 🏗️ 技术架构数据流程

### 方案 A: 智能对话系统（推荐）⭐

```
┌─────────────────────────────────────────────────────────────────┐
│           完整的智能数字人对话系统 (4节点架构)                    │
└─────────────────────────────────────────────────────────────────┘

用户语音
    ↓
┌──────────────────┐
│   ASR 节点        │ 语音识别 (Whisper/Qwen-Audio)
│   "你说了什么"    │ 输出: 用户文本
└────────┬─────────┘
         │
         ↓ 用户文本 ("你好，请介绍一下自己")
┌──────────────────┐
│   LLM 节点        │ 智能对话 (Qwen2.5/GLM-4/Claude)
│   "该怎么回复"    │ 输出: AI回复文本
└────────┬─────────┘
         │
         ↓ AI回复文本 ("你好！我是SoulX数字人...")
┌──────────────────┐
│   TTS 节点        │ 文字转语音 (CosyVoice/GPT-SoVITS)
│   "用声音说出来"  │ 输出: 16kHz WAV音频
└────────┬─────────┘
         │
         ↓ AI语音 (16kHz WAV, mono)
┌──────────────────────────┐
│ SoulX-FlashHead 模型      │ 视频生成 (已实现)
│ "生成口型同步视频"        │ 输出: H.264视频流
└────────┬─────────────────┘
         │
         ↓ 视频流 (H.264, 25fps)
┌──────────────────┐
│   音视频合成      │ 合并AI音频+视频
│   (可选)         │ 输出: MP4 with audio
└────────┬─────────┘
         │
         ↓ 完整音视频流
┌──────────────────┐
│   WebSocket 推送  │ 实时推送到前端
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│   前端播放        │ 用户看到AI数字人回复
└──────────────────┘
```

**性能分析:**
- ASR: ~500ms
- LLM: ~200ms
- TTS: ~300ms
- 视频生成: ~1500ms
- 编码传输: ~100ms
- **总计: ~2.6秒** (可接受)

**技术栈:**
| 节点 | 推荐方案 | GPU需求 | 状态 |
|------|----------|---------|------|
| ASR | Whisper-Large-v3 | 10GB | 🔴 待开发 |
| LLM | Qwen2.5-7B-Instruct | 16GB | 🔴 待开发 |
| TTS | CosyVoice-v1 | 8GB | 🔴 待开发 |
| 视频生成 | SoulX-FlashHead-1.3B | 24GB | ✅ 已实现 |

---

### 方案 B: 口型同步系统（简化版）

```
┌─────────────────────────────────────────────────────────────────┐
│           简化的口型同步系统 (单节点架构)                         │
└─────────────────────────────────────────────────────────────────┘

用户语音
    ↓
┌─────────────────────┐
│   WebSocket 服务     │ 接收用户音频
└──────┬──────────────┘
       │
       ↓ 音频流 (Base64)
┌─────────────────────┐
│   AudioDecoder       │ 解码音频
└──────┬──────────────┘
       │
       ↓ PCM音频 (16kHz)
┌─────────────────────┐
│   AudioBuffer        │ 缓冲1秒
└──────┬──────────────┘
       │
       ↓ 完整音频窗口
┌──────────────────────────┐
│ SoulX-FlashHead 模型      │ 直接使用用户音频生成视频
│ "生成口型同步视频"        │ (无AI智能对话)
└────────┬─────────────────┘
         │
         ↓ 视频流 (H.264)
┌─────────────────────┐
│   WebSocket 服务     │ 推送视频
└──────┬──────────────┘
       │
       ↓
┌──────────────────┐
│   前端播放        │ 播放用户声音+视频
└──────────────────┘
```

**优点:**
- ✅ 延迟更低 (~1.5秒)
- ✅ 实现简单（已基本完成）
- ✅ 无需额外组件

**缺点:**
- ❌ 没有智能对话能力
- ❌ 数字人只是"重复"用户的话
- ❌ 不满足"智能助手"需求

---

### 当前实现的数据流图 (已完成 - 方案B部分)

---

## 🎬 详细业务流程时序图

### 阶段一：建立连接和初始化

```
用户          前端应用          后端服务          AI模型
 │              │                 │                │
 │  1. 打开应用  │                 │                │
 │──────────────>│                 │                │
 │              │  2. WebSocket 连接  │                │
 │              │──────────────────>│                │
 │              │                 │                │
 │              │  3. 连接成功       │                │
 │              │<──────────────────│                │
 │              │                 │                │
 │  4. 选择图像  │                 │                │
 │──────────────>│                 │                │
 │              │  5. 上传图像       │                │
 │              │──────────────────>│                │
 │              │                 │  6. 保存图像     │
 │              │                 │───────────────>│
 │              │                 │                │
 │              │                 │  7. 加载模型     │
 │              │                 │<───────────────│
 │              │                 │                │
 │              │  8. 会话创建成功  │                │
 │              │<──────────────────│                │
 │  9. 显示就绪  │                 │                │
 │<──────────────│                 │                │
```

**时间消耗:** 2-5 秒

---

### 阶段二：实时音频处理（循环）

```
用户          前端应用          后端服务        音频缓冲      AI模型      视频编码
 │              │                 │               │           │         │
 │  1. 开始说话  │                 │               │           │         │
 │──────────────>│                 │               │           │         │
 │              │  2. 录制音频       │               │           │         │
 │              │  (每 100ms)       │               │           │         │
 │              │                 │               │           │         │
 │              │  3. Base64 编码   │               │           │         │
 │              │──────────────────>│               │           │         │
 │              │                 │  4. 解码音频   │           │         │
 │              │                 │───────────────>│           │         │
 │              │                 │  5. 添加到缓冲 │           │         │
 │              │                 │───────────────>│           │         │
 │              │                 │               │           │         │
 │              │                 │  6. 缓冲满?    │           │         │
 │              │                 │<──────────────│           │         │
 │              │                 │    (1秒后)    │           │         │
 │              │                 │               │           │         │
 │              │                 │  7. 提取窗口   │           │         │
 │              │                 │───────────────>│           │         │
 │              │                 │               │           │         │
 │              │                 │               │  8. 推理  │         │
 │              │                 │               │──────────>│         │
 │              │                 │               │           │         │
 │              │                 │               │  9. 视频帧│         │
 │              │                 │               │<──────────│         │
 │              │                 │               │           │         │
 │              │                 │               │ 10. 编码 │         │
 │              │                 │               │──────────>│         │
 │              │                 │               │           │         │
 │              │                 │               │ 11. H.264│         │
 │              │                 │               │<──────────│         │
 │              │                 │  12. 发送视频   │           │         │
 │              │<──────────────────│               │           │         │
 │              │                 │               │           │         │
 │ 13. 观看回应  │                 │               │           │         │
 │<──────────────│                 │               │           │         │
```

**时间消耗:** 1.5-2.5 秒（端到端延迟）

---

### 阶段三：结束对话和清理

```
用户          前端应用          后端服务        AI模型      GPU管理
 │              │                 │               │         │
 │  1. 点击结束  │                 │               │         │
 │──────────────>│                 │               │         │
 │              │  2. 停止录制       │               │         │
 │              │                 │               │         │
 │              │  3. 发送关闭请求  │               │         │
 │              │──────────────────>│               │         │
 │              │                 │               │         │
 │              │                 │  4. 处理剩余音频│           │         │
 │              │                 │───────────────>│         │
 │              │                 │               │ 10. 生成│         │
 │              │                 │               │───┐     │         │
 │              │                 │               │ 11. 释放│         │
 │              │                 │───────────────>│         │
 │              │                 │               │         │         │
 │              │                 │  5. 关闭编码器  │         │
 │              │                 │──────────────────>│         │
 │              │                 │               │         │
 │              │  6. 会话关闭确认  │               │         │
 │              │<──────────────────│               │         │
 │  7. 显示统计  │                 │               │         │
 │<──────────────│                 │               │         │
```

---

## 🔍 关键技术环节详解

### 1. 音频采集和编码（前端）

```typescript
// 1. 获取麦克风权限
navigator.mediaDevices.getUserMedia({ audio: true })

// 2. 创建录音器
const mediaRecorder = new MediaRecorder(stream, {
  audioBitsPerSecond: 128000
})

// 3. 开始录音（每100ms一个数据块）
mediaRecorder.start(100)

// 4. 接收音频数据
mediaRecorder.ondataavailable = (event) => {
  const audioData = event.data  // Blob 格式

  // 5. 转换为 Base64
  const reader = new FileReader()
  reader.onload = () => {
    const base64Audio = reader.result.split(',')[1]

    // 6. 发送到后端
    sendAudioChunk(base64Audio)
  }
  reader.readAsDataURL(audioData)
}
```

**关键参数:**
- 采样率: 16kHz（系统要求）
- 比特率: 128kbps
- 分块大小: 100ms（可配置）
- 编码: Base64

---

### 2. 音频解码（后端）

```python
class AudioDecoder:
    def decode_base64_audio(self, audio_data: str, format: str) -> np.ndarray:
        # 1. 解码 Base64
        audio_bytes = base64.b64decode(audio_data)

        # 2. 读取音频
        audio, sr = sf.read(io.BytesIO(audio_bytes))

        # 3. 转为单声道
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # 4. 重采样到 16kHz
        if sr != 16000:
            audio = librosa.resample(audio, sr, 16000)

        return audio.astype(np.float32)
```

**处理步骤:**
1. Base64 → Bytes
2. Bytes → NumPy Array
3. 多声道 → 单声道
4. 任意采样率 → 16kHz

---

### 3. 音频缓冲管理

```python
class AudioBuffer:
    WINDOW_SIZE = 1.0  # 1秒
    SAMPLE_RATE = 16000
    WINDOW_SAMPLES = 16000  # 1秒 @ 16kHz

    def add_chunk(self, audio_chunk: np.ndarray) -> Optional[np.ndarray]:
        # 1. 累积音频块
        self.buffer.append(audio_chunk)
        self.current_size += len(audio_chunk)

        # 2. 检查是否达到窗口大小
        if self.current_size >= self.WINDOW_SAMPLES:
            # 3. 返回完整窗口
            return self._get_window()

        return None  # 未满，继续累积
```

**为什么需要缓冲？**
- ⚠️ AI 模型需要固定时长的音频
- ⚠️ 流式输入是分块的，大小不固定
- ✅ 缓冲确保每次处理完整的 1 秒音频
- ✅ 提供更稳定的推理质量

---

### 4. AI 推理生成

```python
class FlashHeadInferenceEngine:
    def process_audio(self, audio_data: np.ndarray) -> torch.Tensor:
        # 1. 音频预处理
        #    - 提取 MFCC 特征
        #    - 归一化
        audio_features = self._preprocess_audio(audio_data)

        # 2. 提取音频语义特征
        #    使用 wav2vec2 模型
        audio_embedding = self.wav2vec2(audio_features)

        # 3. 生成视频帧
        #    使用 SoulX-FlashHead 模型
        video_frames = self.flashhead_model(
            audio_embedding=audio_embedding,
            reference_image=self.reference_image,
            num_frames=25  # 1秒 @ 25fps
        )

        return video_frames  # [25, 3, 512, 512]
```

**模型流程:**
1. 音频特征提取 (librosa)
2. 语义编码 (wav2vec2)
3. 视频生成 (SoulX-FlashHead)
4. 后处理 (Tensor → Image)

**性能:**
- RTX 5090: ~126 FPS（5倍实时速度）
- 生成 1 秒视频 (~200ms)

---

### 5. 视频编码

```python
class H264Encoder:
    def encode_frames(self, frames: List[np.ndarray]) -> bytes:
        # 1. 转换为 PyAV 格式
        for frame in frames:
            av_frame = av.VideoFrame.from_ndarray(frame, 'rgb24')

            # 2. H.264 编码（GPU加速）
            packets = self.encoder.encode(av_frame)

            # 3. 拼接数据包
            for packet in packets:
                result += packet.to_bytes()

        return result  # H.264 视频流
```

**编码参数:**
- 编解码器: h264_nvenc（GPU）或 libx264（CPU）
- 帧率: 25 FPS
- 比特率: 2 Mbps
- GOP: 25 帧一个关键帧

---

### 6. 视频传输和播放

```typescript
// 1. 接收二进制数据
ws.onmessage = (event) => {
  if (event.data instanceof Blob) {
    // 2. 解析二进制消息头
    const header = event.data.slice(0, 12)
    const payload = event.data.slice(12)

    // 3. 解码 H.264
    const videoData = new Uint8Array(payload)

    // 4. 添加到视频队列
    videoQueue.push(videoData)

    // 5. 播放视频
    if (videoQueue.length >= 5) {
      playVideoQueue()
    }
  }
}

// 6. 使用 MediaSource 播放
function playVideoQueue() {
  const sourceBuffer = mediaSource.addSourceBuffer(
    'video/mp4; codecs="avc1.42E01E, mp4a.40.2"'
  )

  sourceBuffer.appendBuffer(videoQueue.shift())
}
```

---

## 🎯 性能指标和优化目标

### 性能要求

| 指标 | 目标值 | 当前状态 |
|------|--------|----------|
| 端到端延迟 | < 2.5 秒 | ⚠️ 待测试 |
| 视频帧率 | 25 FPS | ✅ 已配置 |
| 推理速度 | > 100 FPS | ✅ 已实现 |
| 并发会话 | 4-5 个 | ✅ 已实现 |
| GPU 内存 | < 4GB/会话 | ✅ 已管理 |

### 优化策略

1. **音频缓冲**: 固定 1 秒窗口，避免阻塞
2. **GPU 管理**: 智能分配，避免 OOM
3. **编码优化**: NVENC 加速，CPU fallback
4. **传输优化**: 二进制协议，减少开销

---

## 🔐 安全和认证

### 当前状态

⚠️ **注意**: 当前版本未实现认证机制

### 计划实现

```typescript
// JWT Token 认证
const ws = new WebSocket(
  `ws://localhost:8000/ws?token=${jwtToken}`
)

// 会话授权
{
  "type": "create_session",
  "data": {
    "token": jwtToken,
    "reference_image": base64Image
  }
}
```

---

## 📊 监控和日志

### 性能监控

```python
@dataclass
class PerformanceMetrics:
    audio_decode_time: List[float]    # 音频解码时间
    inference_time: List[float]       # AI 推理时间
    encode_time: List[float]           # H.264 编码时间
    end_to_end_latency: List[float]    # 端到端延迟
    inference_fps: List[float]          # 推理 FPS
```

### 日志记录

```python
# 请求日志
logger.info(f"[{session_id}] 收到音频块: seq={sequence}")

# 处理日志
logger.info(f"[{session_id}] 生成视频帧: frames={len(frames)}, inference={inference_time*1000:.2f}ms")

# 错误日志
logger.error(f"[{session_id}] 处理失败: {error}")
```

---

## 🚨 错误处理和恢复

### 常见错误场景

#### 1. 网络断线

```typescript
ws.onclose = () => {
  // 自动重连
  setTimeout(() => {
    reconnect()
  }, 1000)
}
```

#### 2. GPU OOM

```python
try:
    video_frames = engine.process_audio(audio_data)
except RuntimeError as e:
    if "out of memory" in str(e):
        # 释放资源
        torch.cuda.empty_cache()
        # 降级处理
        return error_response
```

#### 3. 编码失败

```python
try:
    h264_data = encoder.encode_frames(frames)
except Exception:
    # CPU fallback
    encoder = H264Encoder(force_cpu=True)
    h264_data = encoder.encode_frames(frames)
```

---

## 📈 使用场景

### 场景一：个人助手

```
用户: "今天天气怎么样？"
  ↓ (录音)
  ↓ (流式传输)
  ↓ (AI 处理)
  ↓ (视频生成)
数字人: "今天天气晴朗..."
```

### 场景二：在线客服

```
客户: "我想查询订单"
  ↓ (实时传输)
  ↓ (自动回复)
  ↓ (生成视频)
数字人客服: "请问您的订单号是？"
```

### 场景三：教育培训

```
老师: "今天我们学习数学"
  ↓ (实时生成)
  ↓ (虚拟形象)
虚拟老师: "让我们开始吧..."
```

---

## 🎓 技术要点总结

### 核心技术

1. **WebSocket 双向通信** - 实时数据传输
2. **音频流式处理** - 低延迟音频处理
3. **AI 视频生成** - SoulX-FlashHead 模型
4. **GPU 加速编码** - NVIDIA NVENC
5. **实时音视频同步** - 时间戳对齐

### 关键挑战

1. ⚠️ **延迟控制** - 需要在 2.5 秒内完成
2. ⚠️ **并发管理** - 4-5 个会话同时进行
3. ⚠️ **GPU 内存** - 避免内存溢出
4. ⚠️ **网络稳定性** - 处理断线重连
5. ⚠️ **音视频同步** - 确保流畅体验

---

**文档位置**: `docs/complete-business-flow.md`

**最后更新**: 2026-03-05
