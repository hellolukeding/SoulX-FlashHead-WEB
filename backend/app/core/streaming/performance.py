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
