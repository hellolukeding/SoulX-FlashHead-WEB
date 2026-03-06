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
