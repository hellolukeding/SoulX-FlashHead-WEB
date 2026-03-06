# 后端流式处理实现设计文档

**日期:** 2026-03-05
**版本:** 1.0
**作者:** Claude Code
**状态:** 已批准

---

## 1. 概述

### 1.1 目标

完善实时数字人平台的后端流式处理功能，实现：
- 多格式音频解码（WAV, MP3, OGG）
- GPU 加速 H.264 视频编码
- 固定窗口音频缓冲管理
- WebSocket 二进制消息传输
- 完善的错误处理和性能监控

### 1.2 范围

**包含：**
- 音频/图像解码器
- H.264 编码器（NVENC + CPU fallback）
- 音频缓冲管理
- GPU 资源管理
- WebSocket 二进制协议
- 性能监控和日志

**不包含：**
- 前端实现（独立项目）
- 用户认证（后续功能）
- 数据库集成（后续功能）

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     WebSocket 连接层                         │
│  (ConnectionManager + WebSocketHandler)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     消息处理层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 音频解码器    │  │ 图像解码器    │  │ H.264 编码器  │     │
│  │ AudioDecoder │  │ ImageDecoder │  │  H264Encoder  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     推理引擎层                               │
│  (FlashHeadInferenceEngine)                                 │
│  - 模型加载                                                  │
│  - 音频处理 (librosa + wav2vec2)                            │
│  - 视频生成 (SoulX-FlashHead)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     缓冲管理层                               │
│  - 音频缓冲队列 (固定窗口: 1秒)                              │
│  - 视频帧队列 (25 FPS)                                       │
│  - 同步协调                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流程

```
客户端音频流
    │
    ▼
[1] WebSocket 接收音频块
    │
    ▼
[2] AudioDecoder 解码为 PCM
    │
    ▼
[3] 累积到音频缓冲 (1秒窗口)
    │
    ▼
[4] FlashHeadInferenceEngine 生成视频帧
    │
    ▼
[5] H264Encoder 编码为 H.264 流
    │
    ▼
[6] WebSocket 二进制消息发送
    │
    ▼
客户端播放器
```

---

## 3. 核心组件设计

### 3.1 AudioDecoder（音频解码器）

**职责：** 解码各种格式的音频数据为标准 PCM

**类定义：**
```python
class AudioDecoder:
    def decode_base64_audio(self, audio_data: str, format: str) -> np.ndarray:
        """
        解码 base64 编码的音频数据

        Args:
            audio_data: base64 编码的音频数据
            format: 音频格式 (wav/mp3/ogg)

        Returns:
            16kHz PCM mono numpy array
        """

    def decode_audio_file(self, audio_path: str) -> np.ndarray:
        """
        解码音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            16kHz PCM mono numpy array
        """
```

**技术栈：**
- `librosa` - 音频加载和重采样
- `soundfile` - 音频文件读写
- `io.BytesIO` - 内存中处理

**文件位置：** `backend/app/core/streaming/audio_decoder.py`

---

### 3.2 H264Encoder（H.264 编码器）

**职责：** 将视频帧编码为 H.264 二进制流

**类定义：**
```python
class H264Encoder:
    def __init__(self, fps: int = 25, bitrate: str = "2M"):
        """
        初始化编码器

        Args:
            fps: 帧率
            bitrate: 比特率
        """

    def encode_frame(self, frame: np.ndarray) -> bytes:
        """
        编码单个视频帧

        Args:
            frame: RGB 图像 (H, W, 3)

        Returns:
            H.264 编码数据包
        """

    def encode_frames(self, frames: List[np.ndarray]) -> bytes:
        """
        批量编码视频帧

        Args:
            frames: RGB 图像列表

        Returns:
            拼接的 H.264 数据包
        """
```

**编码参数：**
- 编解码器: `h264_nvenc` (GPU) 或 `libx264` (CPU)
- 预设: `p6` (质量)
- 调优: `ll` (低延迟)
- 比特率: `2M`
- GOP 大小: 25 (1秒关键帧间隔)

**文件位置：** `backend/app/core/streaming/h264_encoder.py`

---

### 3.3 AudioBuffer（音频缓冲管理器）

**职责：** 管理固定窗口的音频缓冲

**类定义：**
```python
class AudioBuffer:
    WINDOW_SIZE = 1.0  # 1秒窗口
    SAMPLE_RATE = 16000
    WINDOW_SAMPLES = 16000  # 1秒 @ 16kHz

    def add_chunk(self, audio_chunk: np.ndarray) -> Optional[np.ndarray]:
        """
        添加音频块到缓冲

        Args:
            audio_chunk: 音频数据块

        Returns:
            当缓冲满时返回完整窗口，否则返回 None
        """

    def clear(self):
        """清空缓冲"""

    def get_buffer_size(self) -> float:
        """获取当前缓冲大小（秒）"""
```

**缓冲策略：**
- 固定窗口：1 秒
- 累积到 1 秒后触发处理
- 处理后清空缓冲
- 支持部分填充（会话结束时）

**文件位置：** `backend/app/core/streaming/audio_buffer.py`

---

### 3.4 GPUMemoryManager（GPU 内存管理器）

**职责：** 管理 GPU 资源分配和并发控制

**类定义：**
```python
class GPUMemoryManager:
    def __init__(self, max_sessions: int = 5):
        self.max_sessions = max_sessions
        self.allocated_sessions = set()

    def can_allocate_session(self) -> bool:
        """检查是否可以分配新会话"""

    def allocate_session(self, session_id: str):
        """分配 GPU 资源"""

    def free_session(self, session_id: str):
        """释放 GPU 资源"""
```

**文件位置：** `backend/app/core/streaming/gpu_manager.py`

---

## 4. WebSocket 二进制协议

### 4.1 消息格式

```python
# H.264 视频包
struct BinaryMessage {
    uint8 message_type;  # 0x01 = video_packet
    uint8 frame_type;    # 0x01 = I-frame, 0x02 = P-frame
    uint16 sequence;     # 序列号
    uint32 timestamp;    # 时间戳
    uint16 payload_size; # 数据长度
    uint8[payload_size] payload; # H.264 数据
}
```

### 4.2 发送流程

```python
async def send_h264_packet(self, session_id: str, packet: bytes, is_keyframe: bool):
    # 构建二进制消息头
    header = pack('>BBHIH',
                  0x01,              # message_type
                  1 if is_keyframe else 2,  # frame_type
                  sequence,          # sequence
                  timestamp,         # timestamp
                  len(packet))       # payload_size

    # 发送头 + 数据
    await websocket.send_bytes(header + packet)
```

---

## 5. 配置管理

### 5.1 配置文件

**文件位置：** `backend/app/config/stream_config.yaml`

```yaml
stream:
  audio:
    window_size: 1.0
    sample_rate: 16000
    channels: 1
    supported_formats:
      - wav
      - mp3
      - ogg

  video:
    fps: 25
    resolution: [512, 512]
    codec: h264_nvenc
    bitrate: 2M
    preset: p6
    tune: ll
    gop_size: 25
    codec_fallback: libx264

  session:
    max_concurrent: 5
    cleanup_interval: 300  # 5分钟
    idle_timeout: 300

  gpu:
    max_memory_utilization: 0.9
    enable_nvenc: true

  logging:
    level: DEBUG
    performance: true
    request_log: true
    log_file: logs/streaming.log
```

### 5.2 配置类

```python
@dataclass
class StreamConfig:
    """流式处理配置"""

    # 音频配置
    audio_window_size: float = 1.0
    audio_sample_rate: int = 16000
    audio_channels: int = 1

    # 视频配置
    video_fps: int = 25
    video_resolution: Tuple[int, int] = (512, 512)
    video_codec: str = "h264_nvenc"
    video_bitrate: str = "2M"

    # 编码器配置
    encoder_preset: str = "p6"
    encoder_tune: str = "ll"
    gop_size: int = 25

    # 并发配置
    max_concurrent_sessions: int = 5

    # 日志配置
    log_level: str = "DEBUG"
    log_performance: bool = True
```

---

## 6. 错误处理

### 6.1 错误分级

**Level 1: 可恢复错误**
- 记录日志，继续处理
- 示例：单个音频块解码失败

**Level 2: 会话级错误**
- 重试，然后回退
- 示例：NVENC 编码失败 → CPU fallback

**Level 3: 严重错误**
- 关闭会话，清理资源
- 示例：GPU OOM

### 6.2 错误处理示例

```python
# GPU OOM 错误
if "out of memory" in str(e).lower():
    logger.critical(f"GPU OOM: {e}")
    await send_error(session_id, "gpu_oom", "GPU 内存不足")
    await close_session(session_id, cleanup=True)

    # 尝试恢复
    torch.cuda.empty_cache()
```

---

## 7. 性能监控

### 7.1 性能指标

```python
@dataclass
class PerformanceMetrics:
    """性能指标"""

    # 音频处理
    audio_decode_time: List[float] = field(default_factory=list)

    # 推理时间
    inference_time: List[float] = field(default_factory=list)
    inference_fps: List[float] = field(default_factory=list)

    # 编码时间
    encode_time: List[float] = field(default_factory=list)

    # 端到端延迟
    end_to_end_latency: List[float] = field(default_factory=list)

    def log_summary(self):
        """记录性能摘要"""
```

### 7.2 日志记录

**请求日志：**
```python
logger.info(f"[{session_id}] 收到音频块: "
            f"seq={sequence}, "
            f"size={len(data)} bytes")
```

**处理日志：**
```python
logger.info(f"[{session_id}] 生成视频帧: "
            f"frames={len(frames)}, "
            f"inference={inference_time*1000:.2f}ms, "
            f"encode={encode_time*1000:.2f}ms")
```

---

## 8. 测试策略

### 8.1 单元测试

- AudioDecoder 测试
- H264Encoder 测试
- AudioBuffer 测试
- GPUMemoryManager 测试

### 8.2 集成测试

- 完整流式处理流程
- 并发会话测试
- 错误恢复测试

### 8.3 性能测试

- 推理速度: > 100 FPS
- 编码速度: > 25 FPS
- 端到端延迟: < 2.5 秒
- 并发会话: 4-5 个

---

## 9. 实施计划

### Phase 1: 基础组件实现（Day 1）

**上午：**
1. 创建配置文件
2. 实现 AudioDecoder
3. 实现 ImageDecoder
4. 编写单元测试

**下午：**
1. 实现 AudioBuffer
2. 实现 GPUMemoryManager
3. 集成到 WebSocketHandler
4. 本地测试

### Phase 2: H.264 编码器实现（Day 2）

**上午：**
1. 实现 H264Encoder（NVENC + CPU fallback）
2. 实现二进制 WebSocket 协议
3. 性能优化
4. 编写单元测试

**下午：**
1. 集成到 WebSocketHandler
2. 实现视频流发送逻辑
3. 错误处理和日志
4. 本地测试

### Phase 3: 端到端集成和测试（Day 3）

**上午：**
1. 完整流程集成
2. 编写集成测试
3. 性能基准测试
4. 并发测试

**下午：**
1. 优化性能
2. 完善文档
3. 代码审查
4. 提交代码

---

## 10. 依赖清单

### Python 依赖

```txt
av>=12.0.0              # PyAV (FFmpeg)
pillow>=10.0.0          # 图像处理
librosa>=0.10.0         # 音频处理
soundfile>=0.12.0       # 音频文件IO
psutil>=5.9.0           # 系统监控
```

### 系统依赖

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libavcodec-dev libavformat-dev libavutil-dev
```

---

## 11. 文件结构

```
backend/app/
├── core/
│   ├── streaming/                    # 新增流处理模块
│   │   ├── __init__.py
│   │   ├── audio_decoder.py          # 音频解码器
│   │   ├── image_decoder.py          # 图像解码器
│   │   ├── h264_encoder.py           # H.264 编码器
│   │   ├── audio_buffer.py           # 音频缓冲
│   │   ├── gpu_manager.py            # GPU 管理
│   │   └── performance.py            # 性能监控
│   │
│   └── config.py                      # 需扩展
│
├── api/
│   └── websocket/
│       └── handler.py                # 需完善
│
└── config/
    ├── stream_config.yaml            # 新增流配置
    └── model_config.yaml             # 新增模型配置
```

---

## 12. 成功标准

### 功能性
- ✅ 支持多种音频格式（WAV, MP3, OGG）
- ✅ 实时流式处理（延迟 < 2.5 秒）
- ✅ H.264 视频编码
- ✅ 并发会话支持（4-5 个）
- ✅ GPU 加速编码

### 性能
- ✅ 推理速度 > 100 FPS
- ✅ 编码速度 > 25 FPS
- ✅ 端到端延迟 < 2.5 秒
- ✅ GPU 内存使用 < 4GB/会话

### 质量
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试全部通过
- ✅ 错误处理完善
- ✅ 日志记录详细

---

## 13. 附录

### 13.1 参考资料

- [SoulX-FlashHead](https://github.com/Soul-AILab/SoulX-FlashHead)
- [PyAV Documentation](https://pyav.org/docs/stable/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [NVIDIA NVENC API](https://developer.nvidia.com/nvidia-video-codec-sdk)

### 13.2 相关文档

- [系统架构](../architecture.md)
- [WebSocket API](../api/websocket-api.md)
- [开发计划](../development/development-plan.md)

---

**文档版本历史：**
- v1.0 (2026-03-05) - 初始设计
