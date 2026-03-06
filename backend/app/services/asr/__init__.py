"""
ASR 服务模块
"""
from app.services.asr.base import BaseASR
from app.services.asr.factory import ASRFactory, get_asr

__all__ = [
    "BaseASR",
    "ASRFactory",
    "get_asr",
]
