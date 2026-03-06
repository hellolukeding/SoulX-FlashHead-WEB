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
