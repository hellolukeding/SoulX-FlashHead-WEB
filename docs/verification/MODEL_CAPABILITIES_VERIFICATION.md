# 🔍 SoulX-FlashHead 模型能力验证报告

**验证日期:** 2026-03-05
**验证目的:** 确认数字人模型是否生成音频和视频
**验证结果:** ⚠️ **模型仅生成视频，不生成音频**

---

## 📋 模型能力澄清

### ❌ 用户理解（部分错误）
> "我的理解是数字人会生成视频和语音"

### ✅ 实际情况（已验证）

**SoulX-FlashHead 1.3B 模型功能:**
- ✅ **生成视频** - 基于音频生成口型同步的视频
- ❌ **不生成音频** - 音频是输入，不是输出
- 🎯 **核心能力** - 音频驱动的唇语同步（Audio-driven Lip Sync）

---

## 🔄 完整业务流程

基于模型实际能力，完整的实时数字人对话流程应该是：

```
┌─────────────────────────────────────────────────────────────────┐
│                     完整的实时对话流程                            │
└─────────────────────────────────────────────────────────────────┘

用户语音
    ↓
┌──────────────┐
│   ASR 节点    │ 语音识别 (Whisper/Qwen-Audio)
└──────────────┘
    ↓
用户文本 ("你好，请介绍一下自己")
    ↓
┌──────────────┐
│   LLM 节点    │ 智能对话 (Qwen/GLM-4/Claude)
└──────────────┘
    ↓
AI回复文本 ("你好！我是SoulX数字人...")
    ↓
┌──────────────┐
│   TTS 节点    │ 文字转语音 (CosyVoice/GPT-SoVITS)
└──────────────┘
    ↓
AI语音 (16kHz WAV, mono)
    ↓
┌──────────────────────────┐
│ SoulX-FlashHead 模型      │ 音频驱动视频生成
│ - 输入: 参考图像 + 音频    │
│ - 输出: 口型同步视频       │
└──────────────────────────┘
    ↓
视频流 (H.264, 25fps, 512x512)
    ↓
┌──────────────┐
│   前端播放    │ WebSocket 推送
└──────────────┘
```

---

## 🎯 关键发现

### 1. 模型输入输出

**输入 (2个):**
1. **参考图像** (Reference Image)
   - 格式: PNG/JPG
   - 作用: 定义数字人外观
   - 示例: `human_gemini.png` (1536x2752)

2. **音频文件** (Audio File)
   - 格式: WAV, 16kHz, mono
   - 作用: 驱动唇语同步
   - 来源: TTS 生成 或 用户原始语音

**输出 (1个):**
1. **视频文件** (Video Only)
   - 格式: MP4 (H.264)
   - 参数: 25fps, 512x512
   - 内容: 口型与音频同步的数字人视频
   - ⚠️ **不包含音频轨道**

---

### 2. 代码验证

**从 `/opt/soulx/SoulX-FlashHead/INPUT_OUTPUT_GUIDE.md`:**
```python
# 官方示例代码
from flashhead import FlashHeadPipeline

# 初始化模型
pipeline = FlashHeadPipeline.from_pretrained("soulx-ai/flashhead-1.3b")

# 输入: 参考图像 + 音频文件
reference_image = "path/to/reference.png"  # 数字人外观
audio_file = "path/to/audio.wav"           # 驱动音频

# 生成: 视频文件 (仅视频，无音频)
video_output = pipeline(
    image=reference_image,
    audio=audio_file,
    output_video="output.mp4"  # 25fps, 512x512, H.264
)
```

**从我们的实现 `flashhead_engine.py`:**
```python
def process_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[torch.Tensor]:
    """
    处理音频数据，生成视频帧

    Args:
        audio_data: 音频数据 (输入)
        sample_rate: 采样率 (默认16000Hz)

    Returns:
        torch.Tensor: 视频帧 [frames, 3, height, width]
        注意: 仅返回视频帧，不包含音频
    """
    # 1. 音频重采样
    if sample_rate != 16000:
        audio_data = librosa.resample(audio_data, sample_rate, 16000)

    # 2. 获取音频嵌入 (用于驱动)
    audio_embedding = get_audio_embedding(self.pipeline, audio_data)

    # 3. 生成视频帧 (唇语同步)
    video_frames = run_pipeline(self.pipeline, audio_embedding)

    # 4. 返回视频帧 (不包含音频)
    return video_frames  # [T, C, H, W]
```

---

### 3. 业务含义

**场景A: 使用用户原始语音**
```
用户说话 → ASR → LLM理解 → 回复用户
                              ↓
                         TTS生成AI语音 → SoulX-FlashHead → 视频流
                                                    ↓
                                              合并 AI音频+视频 → 前端
```

**场景B: 用户语音直接驱动**
```
用户说话 → SoulX-FlashHead → 视频流 (仅视频，用户自己的声音)
                              ↓
                        前端播放用户声音+视频
```
⚠️ 这种场景没有AI智能对话，只是口型同步

---

## 🔧 实施建议

### 方案一: 完整智能对话系统 (推荐)

**需要的组件:**

1. **ASR 节点** - 语音识别
   - 推荐: Whisper (OpenAI)
   - 或: Qwen-Audio (阿里)
   - 输出: 用户文本

2. **LLM 节点** - 智能对话
   - 推荐: Qwen2.5 (阿里)
   - 或: GLM-4 (智谱)
   - 或: Claude/GPT-4
   - 输出: AI回复文本

3. **TTS 节点** - 文字转语音
   - 推荐: CosyVoice (阿里)
   - 或: GPT-SoVITS
   - 或: Edge-TTS (微软)
   - 输出: 16kHz WAV 音频

4. **视频生成节点** - SoulX-FlashHead
   - 输入: TTS音频 + 参考图像
   - 输出: 口型同步视频

5. **音视频合成** - 合并输出
   - 输入: TTS音频 + 视频流
   - 输出: MP4 with audio track
   - 或: 分别发送 WebSocket tracks

**后端架构:**
```
FastAPI Backend
├── /api/v1/ws/websocket          (WebSocket连接)
├── /api/v1/audio/asr             (ASR服务)
├── /api/v1/chat/completions      (LLM服务)
├── /api/v1/audio/tts             (TTS服务)
└── /api/v1/video/generate        (视频生成)
```

---

### 方案二: 简化版本 (MVP)

**仅实现口型同步，无智能对话**

```
用户音频 → SoulX-FlashHead → 视频流
                              ↓
                        前端播放原始音频+视频
```

**优点:**
- 实现简单
- 延迟低
- 无需额外组件

**缺点:**
- ❌ 无AI智能对话
- ❌ 只是用户语音的口型同步
- ❌ 不满足"智能数字人"需求

---

## 📊 技术栈对比

### 完整方案推荐配置

| 组件 | 技术选型 | 硬件需求 | 延迟 |
|------|----------|----------|------|
| **ASR** | Whisper-Large-v3 | GPU (10GB) | ~500ms |
| **LLM** | Qwen2.5-7B-Instruct | GPU (16GB) | ~200ms |
| **TTS** | CosyVoice-v1 | GPU (8GB) | ~300ms |
| **视频生成** | SoulX-FlashHead-1.3B | GPU (24GB) | ~1500ms |
| **总计** | - | **GPU (32GB+)** | **~2.5s** |

### 我们的硬件

```
✅ GPU: NVIDIA GeForce RTX 5090
✅ 内存: 31.4 GB
✅ 理论上可以运行所有组件
```

**建议部署方式:**
- 方式1: 所有节点在同一GPU (需要精细内存管理)
- 方式2: 微服务架构，不同节点部署在不同服务器
- 方式3: 使用云服务API (ASR/LLM/TTS)

---

## 🎯 当前项目状态

### 已完成 ✅
1. ✅ SoulX-FlashHead 视频生成引擎
2. ✅ WebSocket 流式传输
3. ✅ H.264 视频编码
4. ✅ 音频解码和处理
5. ✅ GPU 内存管理

### 待开发 🔴
1. 🔴 **ASR 节点** - 语音识别
2. 🔴 **LLM 节点** - 智能对话
3. 🔴 **TTS 节点** - 文字转语音
4. 🔴 **音视频合成** - 合并音频和视频
5. 🔴 **前端 WebSocket 客户端**

---

## 📝 结论

### 直接回答用户问题

> **问题:** "tts数字人模型是否提供，我的理解是数字人会生成视频和语音"

**答案:**
1. ❌ **SoulX-FlashHead 不提供 TTS** - 它不生成音频
2. ✅ **模型生成视频** - 基于输入音频生成口型同步视频
3. ⚠️ **需要额外 TTS 组件** - 实现完整智能对话系统

### 正确的理解

**数字人系统 = 4个核心组件:**
1. **ASR** - 听懂用户说什么
2. **LLM** - 智能思考回复
3. **TTS** - 生成AI语音
4. **视频生成** (SoulX-FlashHead) - 生成口型视频

**SoulX-FlashHead 只负责第4步**，前面3步需要额外组件。

---

## 🚀 下一步行动

### 立即行动 (高优先级)

1. **技术选型**
   - 确定 ASR 方案 (Whisper/Qwen-Audio)
   - 确定 LLM 方案 (Qwen2.5/GLM-4)
   - 确定 TTS 方案 (CosyVoice/GPT-SoVITS)

2. **架构设计**
   - 设计微服务架构
   - 定义节点间通信协议
   - 规划 GPU 资源分配

3. **实施计划**
   - Phase 1: 集成 TTS (最小可用系统)
   - Phase 2: 集成 LLM (简单对话)
   - Phase 3: 集成 ASR (完整闭环)

### 技术验证

```bash
# 验证 TTS 集成
# 1. 安装 CosyVoice
pip install cosyvoice

# 2. 测试 TTS 生成
from cosyvoice import CosyVoice
cosy = CosyVoice('your-model')
audio = cosy.inference('你好，我是数字人', '中文女声')

# 3. 传递给 SoulX-FlashHead
engine = FlashHeadInferenceEngine(config)
video_frames = engine.process_audio(audio)

# 4. 合并音视频
ffmpeg -i audio.wav -i video.mp4 -c:v copy -c:a aac output.mp4
```

---

**验证完成时间:** 2026-03-05
**验证状态:** ✅ 完成
**关键结论:** SoulX-FlashHead 仅生成视频，需要额外 TTS 组件实现完整智能对话

---

## 📚 参考文档

- [SoulX-FlashHead 官方文档](/opt/soulx/SoulX-FlashHead/README.md)
- [模型输入输出指南](/opt/soulx/SoulX-FlashHead/INPUT_OUTPUT_GUIDE.md)
- [业务流程文档](/opt/digital-human-platform/docs/complete-business-flow.md)
- [开发计划](/opt/digital-human-platform/docs/development/development-plan.md)
