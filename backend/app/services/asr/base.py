"""
ASR 服务基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np


class BaseASR(ABC):
    """ASR 基类"""

    def __init__(self):
        """初始化 ASR"""
        self.sample_rate = 16000  # 目标采样率

    @abstractmethod
    async def recognize(self, audio: np.ndarray, metadata: Dict[str, Any] = None) -> str:
        """
        识别语音

        Args:
            audio: 音频数据 (16kHz, float32)
            metadata: 可选的元数据

        Returns:
            str: 识别的文本
        """
        pass
