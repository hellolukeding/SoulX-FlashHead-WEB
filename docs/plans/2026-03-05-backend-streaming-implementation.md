# 后端流式处理实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 完善实时数字人平台后端流式处理功能，实现多格式音频解码、GPU 加速 H.264 编码和 WebSocket 二进制消息传输

**架构:** 流式音频处理 → 固定窗口缓冲 → AI 推理 → GPU 加速编码 → WebSocket 二进制传输

**技术栈:** PyAV (FFmpeg), NVIDIA NVENC, librosa, soundfile, FastAPI WebSocket

---

## 前置准备

### 检查依赖

**步骤 1:** 检查 FFmpeg 是否安装

```bash
ffmpeg -version
```

预期输出：FFmpeg 版本信息

**步骤 2:** 如果未安装，安装 FFmpeg

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg libavcodec-dev libavformat-dev libavutil-dev
```

**步骤 3:** 检查 NVIDIA GPU 和 CUDA

```bash
nvidia-smi
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

预期输出：GPU 信息和 CUDA 可用性

**步骤 4:** 更新 Python 依赖

```bash
cd /opt/digital-human-platform/backend
cat >> requirements.txt << 'EOF'
av>=12.0.0
pillow>=10.0.0
librosa>=0.10.0
soundfile>=0.12.0
psutil>=5.9.0
EOF

pip install -r requirements.txt
```

---

## Task 1: 创建配置文件和目录结构

**文件:**
- 创建: `backend/app/config/stream_config.yaml`
- 创建: `backend/app/core/streaming/__init__.py`
- 创建: `backend/app/core/streaming/audio_decoder.py`
- 创建: `backend/app/core/streaming/image_decoder.py`
- 创建: `backend/app/core/streaming/h264_encoder.py`
- 创建: `backend/app/core/streaming/audio_buffer.py`
- 创建: `backend/app/core/streaming/gpu_manager.py`
- 创建: `backend/app/core/streaming/performance.py`

**步骤 1: 创建目录结构**

```bash
cd /opt/digital-human-platform/backend/app
mkdir -p core/streaming config
touch core/streaming/__init__.py
```

**步骤 2: 创建配置文件**

```yaml
# backend/app/config/stream_config.yaml
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
    cleanup_interval: 300
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

**步骤 3: 创建配置加载类**

```python
# backend/app/core/streaming/__init__.py
import yaml
from dataclasses import dataclass
from typing import Tuple, List
from pathlib import Path

@dataclass
class StreamConfig:
    """流式处理配置"""

    # 音频配置
    audio_window_size: float = 1.0
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_supported_formats: List[str] = None

    # 视频配置
    video_fps: int = 25
    video_resolution: Tuple[int, int] = (512, 512)
    video_codec: str = "h264_nvenc"
    video_bitrate: str = "2M"
    encoder_preset: str = "p6"
    encoder_tune: str = "ll"
    gop_size: int = 25
    codec_fallback: str = "libx264"

    # 并发配置
    max_concurrent_sessions: int = 5

    # GPU 配置
    max_memory_utilization: float = 0.9
    enable_nvenc: bool = True

    # 日志配置
    log_level: str = "DEBUG"
    log_performance: bool = True
    request_log: bool = True

    def __post_init__(self):
        if self.audio_supported_formats is None:
            self.audio_supported_formats = ["wav", "mp3", "ogg"]

    @classmethod
    def from_yaml(cls, path: str) -> "StreamConfig":
        """从 YAML 文件加载配置"""
        config_path = Path(path)
        if not config_path.exists():
            return cls()

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        stream_cfg = data.get("stream", {})

        audio = stream_cfg.get("audio", {})
        video = stream_cfg.get("video", {})
        session = stream_cfg.get("session", {})
        gpu = stream_cfg.get("gpu", {})
        logging = stream_cfg.get("logging", {})

        return cls(
            audio_window_size=audio.get("window_size", 1.0),
            audio_sample_rate=audio.get("sample_rate", 16000),
            audio_channels=audio.get("channels", 1),
            audio_supported_formats=audio.get("supported_formats", ["wav", "mp3", "ogg"]),

            video_fps=video.get("fps", 25),
            video_resolution=tuple(video.get("resolution", [512, 512])),
            video_codec=video.get("codec", "h264_nvenc"),
            video_bitrate=video.get("bitrate", "2M"),
            encoder_preset=video.get("preset", "p6"),
            encoder_tune=video.get("tune", "ll"),
            gop_size=video.get("gop_size", 25),
            codec_fallback=video.get("codec_fallback", "libx264"),

            max_concurrent_sessions=session.get("max_concurrent", 5),

            max_memory_utilization=gpu.get("max_memory_utilization", 0.9),
            enable_nvenc=gpu.get("enable_nvenc", True),

            log_level=logging.get("level", "DEBUG"),
            log_performance=logging.get("performance", True),
            request_log=logging.get("request_log", True),
        )

# 加载默认配置
default_config = StreamConfig.from_yaml(
    Path(__file__).parent.parent / "config" / "stream_config.yaml"
)
```

**步骤 4: 提交**

```bash
git add backend/app/config/stream_config.yaml backend/app/core/streaming/
git commit -m "feat: 添加流式处理配置和目录结构"
```

---

## Task 2: 实现音频解码器

**文件:**
- 创建: `backend/app/core/streaming/audio_decoder.py`
- 创建: `backend/tests/core/streaming/test_audio_decoder.py`

**步骤 1: 创建测试文件**

```python
# backend/tests/core/streaming/test_audio_decoder.py
import pytest
import numpy as np
from app.core.streaming.audio_decoder import AudioDecoder

@pytest.fixture
def decoder():
    return AudioDecoder()

@pytest.fixture
def sample_wav_data():
    """创建测试用的 WAV 音频数据"""
    # 生成 1 秒的正弦波音频 (16kHz)
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0  # A4 音符

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * frequency * t)

    # 归一化到 16 位整数
    audio = (audio * 32767).astype(np.int16)

    return audio.tobytes()

def test_decode_wav_format(decoder, sample_wav_data):
    """测试 WAV 格式解码"""
    import base64
    audio_b64 = base64.b64encode(sample_wav_data).decode()

    result = decoder.decode_base64_audio(audio_b64, "wav")

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert len(result) > 0

def test_decode_invalid_format(decoder):
    """测试无效格式处理"""
    with pytest.raises(ValueError, match="Unsupported audio format"):
        decoder.decode_base64_audio("invalid_data", "flac")

def test_resample_to_16khz(decoder):
    """测试重采样到 16kHz"""
    # 创建 8kHz 音频
    sample_rate = 8000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    result = decoder.resample_audio(audio, 8000, 16000)

    assert len(result) == 32000  # 2 秒 @ 16kHz
```

**步骤 2: 运行测试（预期失败）**

```bash
cd /opt/digital-human-platform/backend
pytest tests/core/streaming/test_audio_decoder.py -v
```

预期输出：`ModuleNotFoundError: No module named 'app.core.streaming.audio_decoder'`

**步骤 3: 实现 AudioDecoder**

```python
# backend/app/core/streaming/audio_decoder.py
import base64
import io
import numpy as np
import librosa
import soundfile as sf
from loguru import logger
from typing import Tuple, Optional


class AudioDecoder:
    """
    音频解码器

    支持多种音频格式解码为标准 PCM
    """

    SUPPORTED_FORMATS = {
        "wav": True,
        "mp3": True,
        "ogg": True,
        "flac": False,
    }

    def __init__(self, target_sample_rate: int = 16000):
        """
        初始化音频解码器

        Args:
            target_sample_rate: 目标采样率
        """
        self.target_sample_rate = target_sample_rate

    def decode_base64_audio(
        self,
        audio_data: str,
        format: str = "wav"
    ) -> np.ndarray:
        """
        解码 base64 编码的音频数据

        Args:
            audio_data: base64 编码的音频数据
            format: 音频格式 (wav/mp3/ogg)

        Returns:
            16kHz PCM mono numpy array (float32)

        Raises:
            ValueError: 不支持的音频格式
            Exception: 解码失败
        """
        if format.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {format}")

        try:
            # 解码 base64
            audio_bytes = base64.b64decode(audio_data)

            # 读取音频
            audio, sr = self._load_audio_from_bytes(audio_bytes, format)

            # 转换为目标格式
            return self._normalize_audio(audio, sr)

        except Exception as e:
            logger.error(f"Audio decoding failed: {e}")
            raise

    def decode_audio_file(self, audio_path: str) -> np.ndarray:
        """
        解码音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            16kHz PCM mono numpy array (float32)
        """
        try:
            audio, sr = librosa.load(
                audio_path,
                sr=self.target_sample_rate,
                mono=True
            )

            logger.info(f"Loaded audio: {audio_path} "
                       f"(duration: {len(audio)/self.target_sample_rate:.2f}s)")

            return audio.astype(np.float32)

        except Exception as e:
            logger.error(f"Failed to load audio file {audio_path}: {e}")
            raise

    def resample_audio(
        self,
        audio: np.ndarray,
        original_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """
        重采样音频

        Args:
            audio: 音频数据
            original_sr: 原始采样率
            target_sr: 目标采样率

        Returns:
            重采样后的音频
        """
        if original_sr == target_sr:
            return audio

        resampled = librosa.resample(
            audio,
            orig_sr=original_sr,
            target_sr=target_sr
        )

        return resampled.astype(np.float32)

    def _load_audio_from_bytes(
        self,
        audio_bytes: bytes,
        format: str
    ) -> Tuple[np.ndarray, int]:
        """
        从字节加载音频

        Args:
            audio_bytes: 音频字节数据
            format: 音频格式

        Returns:
            (audio_data, sample_rate)
        """
        # 创建临时文件对象
        audio_file = io.BytesIO(audio_bytes)

        # 使用 soundfile 读取
        audio, sr = sf.read(audio_file)

        return audio, sr

    def _normalize_audio(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> np.ndarray:
        """
        标准化音频到目标格式

        Args:
            audio: 音频数据
            sample_rate: 当前采样率

        Returns:
            标准化后的音频 (16kHz, mono, float32)
        """
        # 转为单声道
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # 重采样
        if sample_rate != self.target_sample_rate:
            audio = self.resample_audio(
                audio,
                sample_rate,
                self.target_sample_rate
            )

        return audio.astype(np.float32)
```

**步骤 4: 运行测试（预期通过）**

```bash
pytest tests/core/streaming/test_audio_decoder.py -v
```

**步骤 5: 提交**

```bash
git add backend/app/core/streaming/audio_decoder.py backend/tests/core/streaming/test_audio_decoder.py
git commit -m "feat: 实现音频解码器"
```

---

## Task 3: 实现图像解码器

**文件:**
- 创建: `backend/app/core/streaming/image_decoder.py`
- 创建: `backend/tests/core/streaming/test_image_decoder.py`

**步骤 1: 创建测试文件**

```python
# backend/tests/core/streaming/test_image_decoder.py
import pytest
import base64
from pathlib import Path
from app.core.streaming.image_decoder import ImageDecoder

@pytest.fixture
def decoder():
    return ImageDecoder()

@pytest.fixture
def sample_image_b64():
    """创建测试用的 base64 编码图像"""
    # 创建一个简单的测试图像
    import io
    from PIL import Image
    import numpy as np

    # 创建 512x512 的测试图像
    img = Image.fromarray(np.zeros((512, 512, 3), dtype=np.uint8))

    # 转为 base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    return base64.b64encode(img_bytes).decode()

def test_decode_base64_image(decoder, sample_image_b64, tmp_path):
    """测试解码 base64 图像"""
    output_path = tmp_path / "test_output.png"

    result = decoder.decode_and_save(sample_image_b64, str(output_path))

    assert result == str(output_path)
    assert Path(result).exists()

def test_save_to_temp_dir(decoder, sample_image_b64):
    """测试保存到临时目录"""
    result = decoder.decode_and_save(sample_image_b64)

    assert Path(result).exists()
    assert result.endswith(".png")
```

**步骤 2: 运行测试（预期失败）**

```bash
pytest tests/core/streaming/test_image_decoder.py -v
```

**步骤 3: 实现 ImageDecoder**

```python
# backend/app/core/streaming/image_decoder.py
import base64
import io
import tempfile
from pathlib import Path
from typing import Optional
from PIL import Image
from loguru import logger


class ImageDecoder:
    """
    图像解码器

    解码 base64 编码的图像并保存到文件
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化图像解码器

        Args:
            temp_dir: 临时文件目录，None 则使用系统临时目录
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def decode_and_save(
        self,
        image_b64: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        解码 base64 图像并保存到文件

        Args:
            image_b64: base64 编码的图像数据
            output_path: 输出文件路径，None 则自动生成

        Returns:
            保存的图像文件路径
        """
        try:
            # 解码 base64
            image_bytes = base64.b64decode(image_b64)

            # 从字节加载图像
            image = Image.open(io.BytesIO(image_bytes))

            # 生成输出路径
            if output_path is None:
                output_path = self._generate_temp_path()

            # 确保目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存图像
            image.save(output_path)

            logger.info(f"Image decoded and saved: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Image decoding failed: {e}")
            raise

    def _generate_temp_path(self) -> str:
        """生成临时文件路径"""
        import uuid
        filename = f"ref_image_{uuid.uuid4().hex[:8]}.png"
        return str(Path(self.temp_dir) / filename)

    def cleanup_temp_files(self, older_than_seconds: int = 3600):
        """
        清理旧的临时文件

        Args:
            older_than_seconds: 清理超过此秒数的文件
        """
        import time

        temp_path = Path(self.temp_dir)
        current_time = time.time()

        for file_path in temp_path.glob("ref_image_*.png"):
            if current_time - file_path.stat().st_mtime > older_than_seconds:
                file_path.unlink()
                logger.debug(f"Cleaned up temp file: {file_path}")
```

**步骤 4: 运行测试（预期通过）**

```bash
pytest tests/core/streaming/test_image_decoder.py -v
```

**步骤 5: 提交**

```bash
git add backend/app/core/streaming/image_decoder.py backend/tests/core/streaming/test_image_decoder.py
git commit -m "feat: 实现图像解码器"
```

---

## Task 4: 实现音频缓冲管理器

**文件:**
- 创建: `backend/app/core/streaming/audio_buffer.py`
- 创建: `backend/tests/core/streaming/test_audio_buffer.py`

**步骤 1: 创建测试文件**

```python
# backend/tests/core/streaming/test_audio_buffer.py
import pytest
import numpy as np
from app.core.streaming.audio_buffer import AudioBuffer

@pytest.fixture
def buffer():
    return AudioBuffer(window_size=1.0, sample_rate=16000)

def test_add_chunks_until_full(buffer):
    """测试累积到完整窗口"""
    # 添加 0.5 秒
    chunk = np.zeros(8000, dtype=np.float32)  # 0.5s @ 16kHz
    result = buffer.add_chunk(chunk)
    assert result is None  # 未满

    # 再添加 0.5 秒
    result = buffer.add_chunk(chunk)
    assert result is not None  # 已满
    assert len(result) == 16000  # 1 秒 @ 16kHz

def test_partial_buffer(buffer):
    """测试部分缓冲"""
    chunk = np.zeros(4000, dtype=np.float32)
    result = buffer.add_chunk(chunk)

    assert result is None
    assert buffer.get_buffer_size() == 0.25  # 4000/16000

def test_clear_buffer(buffer):
    """测试清空缓冲"""
    chunk = np.zeros(8000, dtype=np.float32)
    buffer.add_chunk(chunk)
    buffer.clear()

    assert buffer.get_buffer_size() == 0.0

def test_overflow_handling(buffer):
    """测试缓冲溢出处理"""
    # 添加 1.5 秒数据
    chunk = np.zeros(24000, dtype=np.float32)  # 1.5s @ 16kHz
    result = buffer.add_chunk(chunk)

    assert result is not None
    assert len(result) == 16000  # 返回 1 秒
    assert buffer.get_buffer_size() == 0.5  # 剩余 0.5 秒
```

**步骤 2: 运行测试（预期失败）**

```bash
pytest tests/core/streaming/test_audio_buffer.py -v
```

**步骤 3: 实现 AudioBuffer**

```python
# backend/app/core/streaming/audio_buffer.py
import numpy as np
from typing import Optional, List
from loguru import logger


class AudioBuffer:
    """
    音频缓冲管理器

    管理固定窗口的音频缓冲
    """

    def __init__(self, window_size: float = 1.0, sample_rate: int = 16000):
        """
        初始化音频缓冲

        Args:
            window_size: 窗口大小（秒）
            sample_rate: 采样率
        """
        self.window_size = window_size
        self.sample_rate = sample_rate
        self.window_samples = int(window_size * sample_rate)

        self.buffer: List[np.ndarray] = []
        self.current_size = 0

    def add_chunk(self, audio_chunk: np.ndarray) -> Optional[np.ndarray]:
        """
        添加音频块到缓冲

        Args:
            audio_chunk: 音频数据块 (float32)

        Returns:
            当缓冲满时返回完整窗口，否则返回 None
        """
        chunk_size = len(audio_chunk)

        # 添加到缓冲
        self.buffer.append(audio_chunk)
        self.current_size += chunk_size

        # 检查是否达到窗口大小
        if self.current_size >= self.window_samples:
            return self._get_window()

        return None

    def _get_window(self) -> np.ndarray:
        """
        获取完整窗口并清空缓冲

        Returns:
            完整窗口的音频数据
        """
        # 合并所有缓冲块
        full_buffer = np.concatenate(self.buffer)

        # 提取窗口
        window = full_buffer[:self.window_samples]

        # 保留多余部分
        remaining = full_buffer[self.window_samples:]

        # 重置缓冲
        self.buffer = [remaining] if len(remaining) > 0 else []
        self.current_size = len(remaining)

        logger.debug(f"Audio buffer window ready: {len(window)} samples")

        return window

    def clear(self):
        """清空缓冲"""
        self.buffer = []
        self.current_size = 0

    def get_buffer_size(self) -> float:
        """
        获取当前缓冲大小（秒）

        Returns:
            缓冲大小（秒）
        """
        return self.current_size / self.sample_rate

    def get_remaining(self) -> Optional[np.ndarray]:
        """
        获取剩余的音频数据（用于会话结束）

        Returns:
            剩余的音频数据，如果没有则返回 None
        """
        if self.current_size == 0:
            return None

        remaining = np.concatenate(self.buffer)
        self.clear()

        return remaining
```

**步骤 4: 运行测试（预期通过）**

```bash
pytest tests/core/streaming/test_audio_buffer.py -v
```

**步骤 5: 提交**

```bash
git add backend/app/core/streaming/audio_buffer.py backend/tests/core/streaming/test_audio_buffer.py
git commit -m "feat: 实现音频缓冲管理器"
```

---

## Task 5: 实现 GPU 管理器

**文件:**
- 创建: `backend/app/core/streaming/gpu_manager.py`
- 创建: `backend/tests/core/streaming/test_gpu_manager.py`

**步骤 1: 创建测试文件**

```python
# backend/tests/core/streaming/test_gpu_manager.py
import pytest
from app.core.streaming.gpu_manager import GPUMemoryManager

@pytest.fixture
def manager():
    return GPUMemoryManager(max_sessions=5)

def test_can_allocate_session(manager):
    """测试可以分配新会话"""
    assert manager.can_allocate_session() is True

def test_allocate_session(manager):
    """测试分配会话"""
    session_id = "test_session_1"
    manager.allocate_session(session_id)

    assert session_id in manager.allocated_sessions

def test_max_sessions_limit(manager):
    """测试最大会话数限制"""
    # 分配 5 个会话
    for i in range(5):
        manager.allocate_session(f"session_{i}")

    # 第 6 个应该被拒绝
    assert manager.can_allocate_session() is False

def test_free_session(manager):
    """测试释放会话"""
    session_id = "test_session_1"
    manager.allocate_session(session_id)
    manager.free_session(session_id)

    assert session_id not in manager.allocated_sessions
```

**步骤 2: 运行测试（预期失败）**

```bash
pytest tests/core/streaming/test_gpu_manager.py -v
```

**步骤 3: 实现 GPUMemoryManager**

```python
# backend/app/core/streaming/gpu_manager.py
import torch
from typing import Set
from loguru import logger


class GPUMemoryManager:
    """
    GPU 内存管理器

    管理 GPU 资源分配和并发控制
    """

    def __init__(self, max_sessions: int = 5):
        """
        初始化 GPU 管理器

        Args:
            max_sessions: 最大并发会话数
        """
        self.max_sessions = max_sessions
        self.allocated_sessions: Set[str] = set()

    def can_allocate_session(self) -> bool:
        """
        检查是否可以分配新会话

        Returns:
            是否可以分配
        """
        # 检查会话数限制
        if len(self.allocated_sessions) >= self.max_sessions:
            logger.warning(f"Max session limit reached: {self.max_sessions}")
            return False

        # 检查 GPU 内存使用
        if torch.cuda.is_available():
            used = torch.cuda.memory_allocated() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            utilization = used / total

            if utilization > 0.9:  # 90% 阈值
                logger.warning(f"GPU memory usage too high: {utilization:.1%}")
                return False

        return True

    def allocate_session(self, session_id: str):
        """
        分配 GPU 资源

        Args:
            session_id: 会话 ID
        """
        if not self.can_allocate_session():
            raise RuntimeError(f"Cannot allocate session: max limit reached")

        self.allocated_sessions.add(session_id)
        logger.info(f"GPU resources allocated: {session_id}")

    def free_session(self, session_id: str):
        """
        释放 GPU 资源

        Args:
            session_id: 会话 ID
        """
        if session_id in self.allocated_sessions:
            self.allocated_sessions.discard(session_id)

            # 清理 GPU 缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"GPU resources freed: {session_id}")

    def get_memory_info(self) -> dict:
        """
        获取 GPU 内存信息

        Returns:
            内存信息字典
        """
        if not torch.cuda.is_available():
            return {
                "available": False,
                "allocated_sessions": len(self.allocated_sessions)
            }

        used = torch.cuda.memory_allocated() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3

        return {
            "available": True,
            "allocated_sessions": len(self.allocated_sessions),
            "used_gb": round(used, 2),
            "total_gb": round(total, 2),
            "utilization": round(used / total, 2)
        }
```

**步骤 4: 运行测试（预期通过）**

```bash
pytest tests/core/streaming/test_gpu_manager.py -v
```

**步骤 5: 提交**

```bash
git add backend/app/core/streaming/gpu_manager.py backend/tests/core/streaming/test_gpu_manager.py
git commit -m "feat: 实现 GPU 内存管理器"
```

---

## Task 6: 实现 H.264 编码器

**文件:**
- 创建: `backend/app/core/streaming/h264_encoder.py`
- 创建: `backend/tests/core/streaming/test_h264_encoder.py`

**步骤 1: 创建测试文件**

```python
# backend/tests/core/streaming/test_h264_encoder.py
import pytest
import numpy as np
from app.core.streaming.h264_encoder import H264Encoder

@pytest.fixture
def encoder():
    return H264Encoder(fps=25, bitrate="2M")

@pytest.fixture
def sample_frame():
    """创建测试视频帧"""
    return np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)

def test_encode_single_frame(encoder, sample_frame):
    """测试单帧编码"""
    result = encoder.encode_frame(sample_frame)

    assert isinstance(result, bytes)
    assert len(result) > 0

def test_encode_batch_frames(encoder):
    """测试批量编码"""
    frames = [np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
              for _ in range(25)]  # 1 秒 @ 25fps

    result = encoder.encode_frames(frames)

    assert isinstance(result, bytes)
    assert len(result) > 0

def test_nvenc_fallback():
    """测试 NVENC 不可用时的 CPU fallback"""
    encoder = H264Encoder(fps=25, bitrate="2M", force_cpu=True)

    frame = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    result = encoder.encode_frame(frame)

    assert len(result) > 0
```

**步骤 2: 运行测试（预期失败）**

```bash
pytest tests/core/streaming/test_h264_encoder.py -v
```

**步骤 3: 实现 H264Encoder**

```python
# backend/app/core/streaming/h264_encoder.py
import av
import numpy as np
from typing import List, Optional
from loguru import logger


class H264Encoder:
    """
    H.264 视频编码器

    使用 GPU 加速 (NVENC) 或 CPU 编码
    """

    def __init__(
        self,
        fps: int = 25,
        bitrate: str = "2M",
        preset: str = "p6",
        tune: str = "ll",
        gop_size: int = 25,
        force_cpu: bool = False
    ):
        """
        初始化编码器

        Args:
            fps: 帧率
            bitrate: 比特率
            preset: 质量预设
            tune: 调优选项
            gop_size: GOP 大小
            force_cpu: 强制使用 CPU 编码
        """
        self.fps = fps
        self.bitrate = bitrate
        self.preset = preset
        self.tune = tune
        self.gop_size = gop_size
        self.force_cpu = force_cpu

        self.codec = self._select_codec()
        self.encoder: Optional[av.CodecContext] = None

        logger.info(f"H264Encoder initialized: codec={self.codec}, fps={fps}")

    def _select_codec(self) -> str:
        """选择最佳编码器"""
        if self.force_cpu:
            return "libx264"

        # 尝试使用 NVENC
        try:
            codec = av.CodecContext.create("h264_nvenc", "w")
            logger.success("✅ Using NVIDIA NVENC encoder")
            return "h264_nvenc"
        except Exception as e:
            logger.warning(f"⚠️  NVENC not available, using CPU: {e}")
            return "libx264"

    def _create_encoder(self, width: int, height: int):
        """创建编码器实例"""
        if self.encoder is not None:
            return

        codec_context = av.CodecContext.create(self.codec, "w")
        codec_context.width = width
        codec_context.height = height
        codec_context.framerate = self.fps
        codec_context.bit_rate = int(self.bitrate.replace("M", "")) * 1_000_000

        # 设置编码参数
        if self.codec == "h264_nvenc":
            codec_context.options = {
                "preset": self.preset,
                "tune": self.tune,
                "rc": "cbr",
            }
        else:
            codec_context.options = {
                "preset": "medium",
                "tune": "zerolatency",
                "crf": "23",
            }

        codec_context.gop_size = self.gop_size

        self.encoder = codec_context
        self.encoder.open()

    def encode_frame(self, frame: np.ndarray) -> bytes:
        """
        编码单个视频帧

        Args:
            frame: RGB 图像 (H, W, 3) uint8

        Returns:
            H.264 编码数据包
        """
        if self.encoder is None:
            self._create_encoder(frame.shape[1], frame.shape[0])

        # 转换 numpy 为 PyAV 帧
        av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")

        # 编码
        packets = self.encoder.encode(av_frame)

        # 合并所有包
        result = b""
        for packet in packets:
            result += packet.to_bytes()

        return result

    def encode_frames(self, frames: List[np.ndarray]) -> bytes:
        """
        批量编码视频帧

        Args:
            frames: RGB 图像列表

        Returns:
            拼接的 H.264 数据包
        """
        if not frames:
            return b""

        if self.encoder is None:
            self._create_encoder(frames[0].shape[1], frames[0].shape[0])

        result = b""

        for frame in frames:
            av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            packets = self.encoder.encode(av_frame)

            for packet in packets:
                result += packet.to_bytes()

        # 刷新编码器
        packets = self.encoder.encode(None)
        for packet in packets:
            result += packet.to_bytes()

        return result

    def close(self):
        """关闭编码器"""
        if self.encoder is not None:
            self.encoder.close()
            self.encoder = None
```

**步骤 4: 运行测试（预期通过）**

```bash
pytest tests/core/streaming/test_h264_encoder.py -v
```

**步骤 5: 提交**

```bash
git add backend/app/core/streaming/h264_encoder.py backend/tests/core/streaming/test_h264_encoder.py
git commit -m "feat: 实现 H.264 编码器"
```

---

## Task 7: 实现性能监控

**文件:**
- 创建: `backend/app/core/streaming/performance.py`
- 创建: `backend/tests/core/streaming/test_performance.py`

**步骤 1: 创建性能监控类**

```python
# backend/app/core/streaming/performance.py
import time
from dataclasses import dataclass, field
from typing import List
from loguru import logger


@dataclass
class PerformanceMetrics:
    """性能指标"""

    # 音频处理
    audio_decode_time: List[float] = field(default_factory=list)
    audio_buffer_size: List[float] = field(default_factory=list)

    # 推理时间
    inference_time: List[float] = field(default_factory=list)
    inference_fps: List[float] = field(default_factory=list)

    # 编码时间
    encode_time: List[float] = field(default_factory=list)

    # 端到端延迟
    end_to_end_latency: List[float] = field(default_factory=list)

    def add_audio_decode_time(self, duration: float):
        """记录音频解码时间"""
        self.audio_decode_time.append(duration)

    def add_inference_time(self, duration: float, fps: float):
        """记录推理时间和 FPS"""
        self.inference_time.append(duration)
        self.inference_fps.append(fps)

    def add_encode_time(self, duration: float):
        """记录编码时间"""
        self.encode_time.append(duration)

    def add_latency(self, duration: float):
        """记录端到端延迟"""
        self.end_to_end_latency.append(duration)

    def log_summary(self):
        """记录性能摘要"""
        if self.inference_time:
            avg_inf = sum(self.inference_time) / len(self.inference_time)
            logger.info(f"平均推理时间: {avg_inf*1000:.2f}ms")

        if self.inference_fps:
            avg_fps = sum(self.inference_fps) / len(self.inference_fps)
            logger.info(f"平均推理 FPS: {avg_fps:.2f}")

        if self.end_to_end_latency:
            avg_lat = sum(self.end_to_end_latency) / len(self.end_to_end_latency)
            logger.info(f"平均端到端延迟: {avg_lat*1000:.2f}ms")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "audio_decode_avg_ms": self._avg(self.audio_decode_time) * 1000 if self.audio_decode_time else 0,
            "inference_avg_ms": self._avg(self.inference_time) * 1000 if self.inference_time else 0,
            "inference_avg_fps": self._avg(self.inference_fps) if self.inference_fps else 0,
            "encode_avg_ms": self._avg(self.encode_time) * 1000 if self.encode_time else 0,
            "latency_avg_ms": self._avg(self.end_to_end_latency) * 1000 if self.end_to_end_latency else 0,
        }

    def _avg(self, values: List[float]) -> float:
        """计算平均值"""
        return sum(values) / len(values) if values else 0.0


class PerformanceTimer:
    """性能计时器上下文管理器"""

    def __init__(self, metrics: PerformanceMetrics, metric_name: str):
        self.metrics = metrics
        self.metric_name = metric_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if self.metric_name == "audio_decode":
            self.metrics.add_audio_decode_time(duration)
        elif self.metric_name == "encode":
            self.metrics.add_encode_time(duration)
        elif self.metric_name == "latency":
            self.metrics.add_latency(duration)
```

**步骤 2: 创建简单测试**

```python
# backend/tests/core/streaming/test_performance.py
import time
from app.core.streaming.performance import PerformanceMetrics, PerformanceTimer

def test_performance_metrics():
    """测试性能指标"""
    metrics = PerformanceMetrics()

    metrics.add_audio_decode_time(0.1)
    metrics.add_inference_time(0.5, 100.0)
    metrics.add_encode_time(0.2)
    metrics.add_latency(1.5)

    summary = metrics.to_dict()

    assert summary["audio_decode_avg_ms"] == 100.0
    assert summary["inference_avg_ms"] == 500.0
    assert summary["inference_avg_fps"] == 100.0

def test_performance_timer():
    """测试性能计时器"""
    metrics = PerformanceMetrics()

    with PerformanceTimer(metrics, "audio_decode"):
        time.sleep(0.01)

    assert len(metrics.audio_decode_time) == 1
    assert metrics.audio_decode_time[0] >= 0.01
```

**步骤 3: 运行测试**

```bash
pytest tests/core/streaming/test_performance.py -v
```

**步骤 4: 提交**

```bash
git add backend/app/core/streaming/performance.py backend/tests/core/streaming/test_performance.py
git commit -m "feat: 实现性能监控"
```

---

## Task 8: 集成到 WebSocket Handler

**文件:**
- 修改: `backend/app/api/websocket/handler.py`

**步骤 1: 修改 WebSocketHandler 以使用新组件**

```python
# 在 handler.py 开头添加导入
from app.core.streaming.audio_decoder import AudioDecoder
from app.core.streaming.image_decoder import ImageDecoder
from app.core.streaming.h264_encoder import H264Encoder
from app.core.streaming.audio_buffer import AudioBuffer
from app.core.streaming.gpu_manager import GPUMemoryManager
from app.core.streaming.performance import PerformanceMetrics, PerformanceTimer

# 在 ConnectionManager 中添加
class ConnectionManager:
    def __init__(self):
        # ... 现有代码 ...

        # 新增：资源管理
        self.gpu_manager = GPUMemoryManager()

        # 新增：会话组件
        self.decoders: Dict[str, AudioDecoder] = {}
        self.encoders: Dict[str, H264Encoder] = {}
        self.buffers: Dict[str, AudioBuffer] = {}
        self.metrics: Dict[str, PerformanceMetrics] = {}

    def disconnect(self, session_id: str):
        """断开连接并清理资源"""
        # 清理编码器
        if session_id in self.encoders:
            self.encoders[session_id].close()
            del self.encoders[session_id]

        # 清理其他组件
        self.buffers.pop(session_id, None)
        self.decoders.pop(session_id, None)
        self.metrics.pop(session_id, None)

        # 释放 GPU 资源
        self.gpu_manager.free_session(session_id)

        # ... 现有清理代码 ...

# 在 WebSocketHandler 中修改 _create_session
async def _create_session(self, session_id: str, data: dict):
    """创建会话并加载模型"""
    try:
        # 检查 GPU 资源
        if not self.manager.gpu_manager.can_allocate_session():
            await self._send_error(session_id, 503, "达到最大并发会话数")
            return

        # 获取参数
        model_type = data.get("model_type", "lite")
        reference_image_b64 = data.get("reference_image")

        if not reference_image_b64:
            await self._send_error(session_id, 400, "缺少 reference_image")
            return

        # 解码参考图像
        image_decoder = ImageDecoder()
        reference_image_path = image_decoder.decode_and_save(reference_image_b64)

        # 创建推理引擎
        config = InferenceConfig(
            model_type=model_type,
            use_face_crop=True
        )

        engine = FlashHeadInferenceEngine(config)

        # 加载模型
        if engine.load_model(reference_image_path):
            # 分配 GPU 资源
            self.manager.gpu_manager.allocate_session(session_id)

            # 保存引擎和组件
            self.manager.engines[session_id] = engine
            self.manager.decoders[session_id] = AudioDecoder()
            self.manager.encoders[session_id] = H264Encoder()
            self.manager.buffers[session_id] = AudioBuffer()
            self.manager.metrics[session_id] = PerformanceMetrics()

            # 更新会话状态
            session = self.manager.get_session(session_id)
            if session:
                session.status = "ready"
                session.model_type = model_type
                session.reference_image = reference_image_path

            # 发送成功响应
            await self.manager.send_message(session_id, {
                "type": "session_created",
                "data": {
                    "session_id": session_id,
                    "status": "ready",
                    "model_type": model_type
                },
                "timestamp": self._get_timestamp()
            })

            logger.success(f"✅ 会话创建成功: {session_id}")
        else:
            await self._send_error(session_id, 500, "模型加载失败")

    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        await self._send_error(session_id, 500, str(e))

# 修改 _handle_audio_chunk
async def _handle_audio_chunk(self, session_id: str, data: dict):
    """处理音频块"""
    start_time = time.time()
    metrics = self.manager.metrics.get(session_id)

    try:
        # 获取组件
        engine = self.manager.get_engine(session_id)
        decoder = self.manager.decoders.get(session_id)
        encoder = self.manager.encoders.get(session_id)
        buffer = self.manager.buffers.get(session_id)

        if not all([engine, decoder, encoder, buffer]):
            await self._send_error(session_id, 404, "会话未创建")
            return

        # 解码音频
        with PerformanceTimer(metrics, "audio_decode") if metrics else nullcontext():
            audio_format = data.get("format", "wav")
            audio_b64 = data.get("audio_data")

            audio_data = decoder.decode_base64_audio(audio_b64, audio_format)

        # 添加到缓冲
        audio_window = buffer.add_chunk(audio_data)

        if audio_window is not None:
            # 生成视频帧
            with PerformanceTimer(metrics, "inference") if metrics else nullcontext():
                video_frames = engine.process_audio(audio_window)

                if metrics and video_frames is not None:
                    fps = 25.0  # 固定 25 FPS
                    metrics.add_inference_time(
                        time.time() - start_time,
                        fps
                    )

            if video_frames is not None:
                # 编码为 H.264
                with PerformanceTimer(metrics, "encode") if metrics else nullcontext():
                    # 转换 tensor 为 numpy
                    frames_np = video_frames.cpu().numpy().transpose(0, 2, 3, 1)  # [F, H, W, C]
                    frames_np = (frames_np * 255).astype(np.uint8)

                    h264_data = encoder.encode_frames(frames_np)

                # 发送视频帧
                await self._send_video_packet(session_id, h264_data, is_keyframe=True)

                # 更新会话统计
                session = self.manager.get_session(session_id)
                if session:
                    session.video_frames_generated += len(frames_np)

                # 记录端到端延迟
                if metrics:
                    metrics.add_latency(time.time() - start_time)

        # 发送确认
        await self.manager.send_message(session_id, {
            "type": "audio_received",
            "data": {
                "session_id": session_id,
                "sequence": data.get("sequence", 0),
                "status": "processing"
            },
            "timestamp": self._get_timestamp()
        })

    except Exception as e:
        logger.error(f"处理音频块失败: {e}")
        await self._send_error(session_id, 500, str(e))

# 添加新方法：发送 H.264 视频包
async def _send_video_packet(
    self,
    session_id: str,
    packet: bytes,
    is_keyframe: bool
):
    """发送 H.264 视频包"""
    from struct import pack

    # 构建二进制消息头
    header = pack('>BBHIH',
                  0x01,              # message_type: video_packet
                  1 if is_keyframe else 2,  # frame_type
                  0,                 # sequence (todo: increment)
                  int(time.time()),  # timestamp
                  len(packet))       # payload_size

    # 发送二进制消息
    websocket = self.manager.active_connections.get(session_id)
    if websocket:
        await websocket.send_bytes(header + packet)
```

**步骤 2: 添加导入语句**

在文件顶部添加：

```python
from contextlib import nullcontext
from struct import pack
```

**步骤 3: 提交**

```bash
git add backend/app/api/websocket/handler.py
git commit -m "feat: 集成流式处理组件到 WebSocket Handler"
```

---

## Task 9: 创建集成测试

**文件:**
- 创建: `backend/tests/integration/test_websocket_streaming.py`

**步骤 1: 创建集成测试**

```python
# backend/tests/integration/test_websocket_streaming.py
import pytest
import asyncio
import base64
import numpy as np
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_audio_b64():
    """创建测试音频数据"""
    # 生成 1 秒测试音频
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * 440 * t)
    audio = (audio * 32767).astype(np.int16)

    # 简单的 WAV 头
    audio_bytes = audio.tobytes()
    return base64.b64encode(audio_bytes).decode()

@pytest.fixture
def sample_image_b64():
    """创建测试图像数据"""
    from PIL import Image
    import io

    img = Image.fromarray(np.zeros((512, 512, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    return base64.b64encode(img_bytes).decode()

@pytest.mark.asyncio
async def test_websocket_connection_flow(client, sample_audio_b64, sample_image_b64):
    """测试完整的 WebSocket 连接流程"""
    # 这里需要实际的 WebSocket 测试
    # 由于测试复杂度，先创建框架

    # 1. 建立 WebSocket 连接
    # 2. 创建会话
    # 3. 发送音频
    # 4. 接收视频
    # 5. 关闭会话

    pass
```

**步骤 2: 提交**

```bash
git add backend/tests/integration/test_websocket_streaming.py
git commit -m "test: 添加 WebSocket 流式处理集成测试框架"
```

---

## Task 10: 更新主应用

**文件:**
- 修改: `backend/app/main.py`

**步骤 1: 更新 main.py 以导出 WebSocket 路由**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.websocket.websocket import router as websocket_router

# 创建 FastAPI 应用
app = FastAPI(
    title="实时数字人平台 API",
    description="基于 SoulX-FlashHead 的实时音频驱动数字人视频生成系统",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(websocket_router, prefix="/api/ws")

@app.get("/")
async def root():
    return {
        "message": "实时数字人平台 API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gpu_available": __import__("torch").cuda.is_available()
    }

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 实时数字人平台启动")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 实时数字人平台关闭")
```

**步骤 2: 提交**

```bash
git add backend/app/main.py
git commit -m "feat: 更新主应用配置"
```

---

## Task 11: 创建部署文档

**文件:**
- 创建: `backend/deployment/STREAMING_SETUP.md`

**步骤 1: 创建部署文档**

```markdown
# 流式处理功能部署指南

## 系统要求

- Python 3.10+
- CUDA 12.8
- NVIDIA GPU (RTX 4090/5090 推荐)
- FFmpeg

## 安装步骤

### 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg libavcodec-dev libavformat-dev libavutil-dev
```

### 2. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 验证 GPU

```bash
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 4. 启动服务

```bash
python -m app.main
```

## 配置

编辑 `backend/app/config/stream_config.yaml` 修改配置。

## 监控

查看日志：`tail -f backend/logs/streaming.log`

性能指标：访问 `http://localhost:8000/metrics`
```

**步骤 2: 提交**

```bash
git add backend/deployment/STREAMING_SETUP.md
git commit -m "docs: 添加流式处理部署指南"
```

---

## Task 12: 最终测试和验证

**步骤 1: 运行所有测试**

```bash
cd /opt/digital-human-platform/backend
pytest tests/ -v --cov=app
```

**步骤 2: 启动服务器**

```bash
python -m app.main
```

**步骤 3: 验证健康检查**

```bash
curl http://localhost:8000/health
```

预期输出：
```json
{
  "status": "healthy",
  "gpu_available": true
}
```

**步骤 4: 提交最终代码**

```bash
git add .
git commit -m "feat: 完成流式处理功能实现"
```

---

## 完成标准

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
- ✅ 集成测试通过
- ✅ 错误处理完善
- ✅ 日志记录详细

---

## 预计时间

- **Day 1:** Tasks 1-5（配置 + 基础组件）
- **Day 2:** Tasks 6-8（H.264 编码器 + 集成）
- **Day 3:** Tasks 9-12（测试 + 部署）

---

**下一步:** 选择执行方式开始实施
