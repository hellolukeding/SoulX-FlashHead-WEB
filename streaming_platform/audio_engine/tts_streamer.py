"""
CosyVoice 流式 TTS 引擎

特性：
- 流式切片输出 (150ms)
- 内存级数据传递（零磁盘 I/O）
- 异步生成器接口
"""
import asyncio
import time
from typing import AsyncGenerator
import numpy as np
from loguru import logger


class CosyVoiceStreamer:
    """
    CosyVoice 流式 TTS 引擎

    使用现有的 CosyVoice 实现，封装为流式接口
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size_ms: int = 150,
    ):
        """
        初始化流式 TTS 引擎

        Args:
            sample_rate: 采样率 (Hz)
            chunk_size_ms: 切片大小 (毫秒)
        """
        self.sample_rate = sample_rate
        self.chunk_size_ms = chunk_size_ms
        self.chunk_size_samples = int(sample_rate * chunk_size_ms / 1000)

        # 引入现有的 TTS 引擎
        self._tts_engine = None
        self._initialized = False

    async def initialize(self):
        """初始化 TTS 引擎"""
        if self._initialized:
            return

        try:
            # 使用现有的 TTS 工厂
            import sys
            sys.path.insert(0, '/opt/digital-human-platform/backend')

            from app.services.tts.factory import get_tts
            from app.services.tts.cosyvoice_tts import CosyVoiceEngine

            # 获取 CosyVoice 引擎
            self._tts_engine = get_tts()
            self._initialized = True

            logger.info("[TTS Streamer] CosyVoice 引擎已初始化")

        except Exception as e:
            logger.warning(f"[TTS Streamer] CosyVoice 初始化失败: {e}")
            logger.info("[TTS Streamer] 使用模拟模式")

    async def generate_audio_stream(
        self,
        text: str,
    ) -> AsyncGenerator[np.ndarray, None]:
        """
        生成音频流

        Args:
            text: 输入文本

        Yields:
            音频切片 numpy array (shape: [chunk_size_samples], dtype: float32)
        """
        if not self._initialized:
            await self.initialize()

        try:
            # 生成完整音频
            start_time = time.time()

            # 调用 TTS 合成
            if hasattr(self._tts_engine, 'synthesize'):
                # 同步调用
                result = self._tts_engine.synthesize(text)

                # 如果返回的是 coroutine，需要 await
                if asyncio.iscoroutine(result):
                    audio = await result
                else:
                    audio = result
            else:
                raise RuntimeError("TTS 引擎不支持 synthesize 方法")

            # 转换为 numpy array
            if audio is None:
                logger.warning("[TTS Streamer] 音频生成返回 None")
                return

            if not isinstance(audio, np.ndarray):
                audio = np.array(audio)

            # 确保是 float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # 重采样到目标采样率（如果需要）
            if len(audio.shape) > 1:
                audio = audio.squeeze()

            # 如果采样率不是 16kHz，进行重采样
            current_sample_rate = getattr(self._tts_engine, 'sample_rate', 24000)
            if current_sample_rate != self.sample_rate:
                import librosa
                audio = librosa.resample(
                    audio,
                    orig_sr=current_sample_rate,
                    target_sr=self.sample_rate
                )

            latency = (time.time() - start_time) * 1000
            duration = len(audio) / self.sample_rate

            logger.info(f"[TTS Streamer] 生成完成: {duration:.2f}s, 延迟: {latency:.0f}ms")

            # 分片输出
            num_chunks = int(np.ceil(len(audio) / self.chunk_size_samples))

            for i in range(num_chunks):
                start = i * self.chunk_size_samples
                end = min(start + self.chunk_size_samples, len(audio))
                chunk = audio[start:end]

                yield chunk

                logger.debug(f"[TTS Streamer] 发送切片 {i+1}/{num_chunks}: {len(chunk)/self.sample_rate*1000:.0f}ms")

                # 模拟流式延迟（实际应用中 TTS 应该是真正的流式）
                await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"[TTS Streamer] 生成失败: {e}")
            raise

    async def generate_mock_stream(
        self,
        text: str,
    ) -> AsyncGenerator[np.ndarray, None]:
        """
        生成模拟音频流（用于测试）

        Args:
            text: 输入文本

        Yields:
            模拟音频切片
        """
        # 计算需要的音频时长（假设每个字符 0.2 秒）
        duration = len(text) * 0.2
        total_samples = int(duration * self.sample_rate)
        num_chunks = int(np.ceil(total_samples / self.chunk_size_samples))

        logger.info(f"[TTS Streamer] 模拟模式: {len(text)} 字符, {duration:.2f}s, {num_chunks} 切片")

        for i in range(num_chunks):
            # 生成随机音频（模拟真实音频）
            chunk = np.random.randn(self.chunk_size_samples).astype(np.float32) * 0.1

            # 添加简单的正弦波（让人声更明显）
            t = np.linspace(0, self.chunk_size_ms / 1000, self.chunk_size_samples)
            chunk += 0.05 * np.sin(2 * np.pi * 440 * t)  # A4 音

            yield chunk

            logger.debug(f"[TTS Streamer] 模拟切片 {i+1}/{num_chunks}")

            # 模拟处理延迟
            await asyncio.sleep(0.1)


class MockTTSStreamer:
    """
    模拟 TTS 流式引擎（用于测试）
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size_ms: int = 150,
    ):
        self.sample_rate = sample_rate
        self.chunk_size_ms = chunk_size_ms
        self.chunk_size_samples = int(sample_rate * chunk_size_ms / 1000)

    async def generate_audio_stream(
        self,
        text: str,
    ) -> AsyncGenerator[np.ndarray, None]:
        """
        生成模拟音频流
        """
        duration = len(text) * 0.15  # 每字符 150ms
        total_samples = int(duration * self.sample_rate)
        num_chunks = int(np.ceil(total_samples / self.chunk_size_samples))

        logger.info(f"[Mock TTS] 生成 {num_chunks} 切片: '{text}'")

        for i in range(num_chunks):
            # 生成模拟音频
            chunk = np.random.randn(self.chunk_size_samples).astype(np.float32) * 0.05

            # 添加正弦波
            t = np.linspace(0, self.chunk_size_ms / 1000, self.chunk_size_samples)
            frequency = 220 + (i % 4) * 110  # 变化频率
            chunk += 0.1 * np.sin(2 * np.pi * frequency * t)

            yield chunk

            logger.debug(f"[Mock TTS] 切片 {i+1}/{num_chunks}: {len(chunk)/self.sample_rate*1000:.0f}ms")

            # 模拟生成延迟
            await asyncio.sleep(self.chunk_size_ms / 1000 * 0.5)
