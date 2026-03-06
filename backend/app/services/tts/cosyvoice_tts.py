"""
CosyVoice TTS 实现
阿里开源的高质量语音合成服务
GitHub: https://github.com/FunAudioLLM/CosyVoice

使用 Cross-lingual 模式，支持参考音频声音克隆
"""
import asyncio
import sys
import os
from typing import Optional
import numpy as np
from loguru import logger

# 添加 CosyVoice 路径
COSYVOICE_ROOT = "/opt/digital-human-platform/models/CosyVoice"
sys.path.insert(0, COSYVOICE_ROOT)

COSYVOICE_AVAILABLE = False

try:
    from cosyvoice.cli.cosyvoice import AutoModel
    COSYVOICE_AVAILABLE = True
    logger.info(f"[CosyVoice] ✅ 已导入，路径: {COSYVOICE_ROOT}")
except ImportError as e:
    error_msg = str(e)
    if "Qwen2ForCausalLM" in error_msg:
        logger.warning("[CosyVoice] ⚠️  依赖版本不兼容（Qwen2ForCausalLM）")
        logger.info("[CosyVoice] 💡 推荐使用 Edge TTS（已配置在 .env 中）")
        logger.info("[CosyVoice] 💡 如需使用 CosyVoice，请降级 PyTorch 到 2.3.1")
    else:
        logger.warning(f"[CosyVoice] ⚠️  未安装，将回退到 Edge TTS: {e}")

from app.services.tts.base import BaseTTS
from app.services.tts.edge_tts import EdgeTTSEngine


class CosyVoiceEngine(BaseTTS):
    """
    CosyVoice TTS 引擎（Cross-lingual 模式）

    使用 Cross-lingual 模式，支持参考音频的声音克隆
    如果 CosyVoice 不可用，自动回退到 Edge TTS
    """

    # 默认参考音频路径
    DEFAULT_REFERENCE_AUDIO = "/opt/digital-human-platform/assets/simple_voice.mp3"

    def __init__(
        self,
        model_name: str = "CosyVoice-300M",
        voice_name: str = "中文女",
        speaker_reference: Optional[str] = None
    ):
        """
        初始化 CosyVoice 引擎

        Args:
            model_name: 模型名称
            voice_name: 音色名称（用于兼容）
            speaker_reference: 参考音频路径（用于声音克隆）
        """
        super().__init__()
        self.model_name = model_name
        self.voice_name = voice_name
        self.cosyvoice = None
        self.use_fallback = False

        # 设置参考音频
        self.speaker_reference = speaker_reference or self.DEFAULT_REFERENCE_AUDIO

        if not os.path.exists(self.speaker_reference):
            logger.warning(f"[CosyVoice] 参考音频不存在: {self.speaker_reference}")
            # 尝试使用默认参考音频
            if os.path.exists(self.DEFAULT_REFERENCE_AUDIO):
                self.speaker_reference = self.DEFAULT_REFERENCE_AUDIO
                logger.info(f"[CosyVoice] 使用默认参考音频: {self.speaker_reference}")
            else:
                logger.error("[CosyVoice] 无可用参考音频，回退到 Edge TTS")
                self.fallback = EdgeTTSEngine()
                self.use_fallback = True
                return

        if not COSYVOICE_AVAILABLE:
            logger.warning("[CosyVoice] 回退到 Edge TTS")
            self.fallback = EdgeTTSEngine()
            self.use_fallback = True
            return

        try:
            # 尝试加载 CosyVoice 模型
            model_dir = os.path.join(COSYVOICE_ROOT, "pretrained_models", model_name)

            if not os.path.exists(model_dir):
                logger.error(f"[CosyVoice] 模型目录不存在: {model_dir}")
                logger.warning("[CosyVoice] 回退到 Edge TTS")
                self.fallback = EdgeTTSEngine()
                self.use_fallback = True
                return

            # 初始化 CosyVoice
            self.cosyvoice = AutoModel(model_dir=model_dir)
            logger.success(f"[CosyVoice] ✅ 初始化成功: {model_name}")
            logger.info(f"[CosyVoice] 参考音频: {self.speaker_reference}")

        except Exception as e:
            logger.error(f"[CosyVoice] ❌ 初始化失败: {e}")
            logger.warning("[CosyVoice] 回退到 Edge TTS")
            self.fallback = EdgeTTSEngine()
            self.use_fallback = True

    async def synthesize(self, text: str) -> np.ndarray:
        """
        合成语音（Cross-lingual 模式）

        Args:
            text: 要合成的文本

        Returns:
            np.ndarray: 音频数据 (16kHz, float32)
        """
        if self.use_fallback or not self.cosyvoice:
            return await self.fallback.synthesize(text)

        try:
            logger.debug(f"[CosyVoice] 合成: {text[:50]}...")

            # 使用 Cross-lingual 模式合成
            import torch
            import torchaudio

            output_list = list(self.cosyvoice.inference_cross_lingual(
                text,
                self.speaker_reference,
                stream=False
            ))

            if not output_list:
                logger.error("[CosyVoice] 未生成音频")
                return await self.fallback.synthesize(text)

            output = output_list[0]
            audio_tensor = output['tts_speech']

            # 转换为 numpy 数组
            if isinstance(audio_tensor, torch.Tensor):
                audio = audio_tensor.numpy().squeeze()
            else:
                audio = np.array(audio_tensor).squeeze()

            # CosyVoice 默认采样率是 22050 Hz，需要重采样到 16000 Hz
            cosyvoice_sr = 22050
            target_sr = 16000

            if cosyvoice_sr != target_sr:
                import librosa
                audio = librosa.resample(audio, orig_sr=cosyvoice_sr, target_sr=target_sr)

            audio = audio.astype(np.float32)

            duration = len(audio) / target_sr
            logger.debug(f"[CosyVoice] 合成完成: {duration:.2f}秒")

            return audio

        except Exception as e:
            logger.error(f"[CosyVoice] 合成失败: {e}")
            logger.info("[CosyVoice] 回退到 Edge TTS")
            return await self.fallback.synthesize(text)

    def is_available(self) -> bool:
        """检查 CosyVoice 是否可用"""
        return COSYVOICE_AVAILABLE and not self.use_fallback

    def get_voice_name(self) -> str:
        """获取当前使用的音色名称"""
        return f"Cross-lingual ({os.path.basename(self.speaker_reference)})"
