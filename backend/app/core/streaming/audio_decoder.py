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
