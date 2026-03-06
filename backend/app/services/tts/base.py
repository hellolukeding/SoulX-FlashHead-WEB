"""
TTS 服务基类
"""
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class BaseTTS(ABC):
    """TTS 基类"""

    def __init__(self):
        """初始化 TTS"""
        self.sample_rate = 16000  # 目标采样率

    @abstractmethod
    async def synthesize(self, text: str) -> np.ndarray:
        """
        合成语音

        Args:
            text: 待合成的文本

        Returns:
            np.ndarray: 16kHz 采样率的音频数据 (float32)
        """
        pass

    @abstractmethod
    def get_voice_name(self) -> str:
        """获取当前使用的音色名称"""
        pass
