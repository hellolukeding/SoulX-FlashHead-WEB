"""
Edge TTS 实现
免费的微软神经语音合成服务
"""
import asyncio
from io import BytesIO
from typing import Optional
import numpy as np
import edge_tts
import soundfile as sf
import resampy
from loguru import logger

from app.services.tts.base import BaseTTS


class EdgeTTSEngine(BaseTTS):
    """Edge TTS 引擎"""

    def __init__(self, voice_name: str = "zh-CN-YunxiNeural"):
        """
        初始化 Edge TTS

        Args:
            voice_name: 语音名称，如 zh-CN-YunxiNeural, zh-CN-XiaoxiaoNeural
        """
        super().__init__()
        self.voice_name = voice_name
        logger.info(f"[EdgeTTS] 初始化成功，音色: {voice_name}")

    def get_voice_name(self) -> str:
        return self.voice_name

    async def synthesize(self, text: str) -> np.ndarray:
        """
        合成语音

        Args:
            text: 待合成的文本

        Returns:
            np.ndarray: 16kHz 采样率的音频数据 (float32)
        """
        try:
            logger.debug(f"[EdgeTTS] 开始合成: {text[:50]}...")

            # 创建通信对象
            communicate = edge_tts.Communicate(text, self.voice_name)

            # 收集音频数据
            audio_buffer = BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

            # 读取音频
            audio_buffer.seek(0)
            stream, sample_rate = sf.read(audio_buffer)

            logger.debug(f"[EdgeTTS] 原始音频: {sample_rate}Hz, shape={stream.shape}")

            # 转为单声道
            if stream.ndim > 1:
                logger.debug(f"[EdgeTTS] 检测到多声道 ({stream.shape[1]}声道)，使用第一声道")
                stream = stream[:, 0]

            # 转为 float32
            stream = stream.astype(np.float32)

            # 重采样到 16kHz
            if sample_rate != self.sample_rate:
                logger.debug(f"[EdgeTTS] 重采样: {sample_rate}Hz -> {self.sample_rate}Hz")
                stream = resampy.resample(
                    x=stream,
                    sr_orig=sample_rate,
                    sr_new=self.sample_rate
                )

            logger.debug(f"[EdgeTTS] 合成完成: {len(stream)/self.sample_rate:.2f}秒")

            return stream

        except Exception as e:
            logger.error(f"[EdgeTTS] 合成失败: {e}")
            # 返回静音
            return np.zeros(int(self.sample_rate * 0.5), dtype=np.float32)
