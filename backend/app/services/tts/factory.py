"""
TTS 工厂类
根据配置创建对应的 TTS 实例
"""
import os
from typing import Optional
from loguru import logger

from app.core.config import settings
from app.services.tts.base import BaseTTS
from app.services.tts.edge_tts import EdgeTTSEngine
from app.services.tts.cosyvoice_tts import CosyVoiceEngine


class TTSFactory:
    """TTS 工厂类"""

    @staticmethod
    def create(tts_type: Optional[str] = None) -> BaseTTS:
        """
        创建 TTS 实例

        Args:
            tts_type: TTS 类型，如果为 None 则从配置读取

        Returns:
            BaseTTS: TTS 实例
        """
        tts_type = tts_type or settings.tts_type or os.getenv("TTS_TYPE", "cosyvoice")

        logger.info(f"[TTS] 创建 TTS 实例: {tts_type}")

        if tts_type == "cosyvoice":
            model_name = settings.cosyvoice_model or os.getenv("COSYVOICE_MODEL", "CosyVoice-300M-SFT")
            voice_name = settings.cosyvoice_voice or os.getenv("COSYVOICE_VOICE", "中文女")
            return CosyVoiceEngine(model_name=model_name, voice_name=voice_name)

        elif tts_type == "edge":
            voice_name = settings.edge_tts_voice or os.getenv("EDGE_TTS_VOICE", "zh-CN-YunxiNeural")
            return EdgeTTSEngine(voice_name=voice_name)

        elif tts_type == "doubao":
            # TODO: 实现豆包 TTS
            raise NotImplementedError(f"TTS 类型 '{tts_type}' 尚未实现")

        elif tts_type == "tencent":
            # TODO: 实现腾讯 TTS
            raise NotImplementedError(f"TTS 类型 '{tts_type}' 尚未实现")

        elif tts_type == "azure":
            # TODO: 实现 Azure TTS
            raise NotImplementedError(f"TTS 类型 '{tts_type}' 尚未实现")

        else:
            logger.warning(f"[TTS] 未知的 TTS 类型: {tts_type}，使用 CosyVoice")
            return CosyVoiceEngine()


# 全局单例
_tts_instance: Optional[BaseTTS] = None


def get_tts() -> BaseTTS:
    """获取 TTS 单例"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSFactory.create()
    return _tts_instance
