"""
TTS 服务模块
"""
from app.services.tts.base import BaseTTS
from app.services.tts.edge_tts import EdgeTTSEngine
from app.services.tts.cosyvoice_tts import CosyVoiceEngine
from app.services.tts.factory import TTSFactory, get_tts

__all__ = [
    "BaseTTS",
    "EdgeTTSEngine",
    "CosyVoiceEngine",
    "TTSFactory",
    "get_tts",
]
