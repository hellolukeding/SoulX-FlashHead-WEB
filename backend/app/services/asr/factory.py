"""
ASR 工厂类
根据配置创建对应的 ASR 实例
"""
import os
from typing import Optional, Dict, Any
import numpy as np
from loguru import logger

from app.core.config import settings
from app.services.asr.base import BaseASR
from app.services.asr.tencent_asr import TencentASR


class MockASR(BaseASR):
    """模拟 ASR（用于测试）"""

    async def recognize(self, audio: np.ndarray, metadata: Dict[str, Any] = None) -> str:
        """模拟识别"""
        duration = len(audio) / self.sample_rate
        logger.debug(f"[MockASR] 模拟识别: {duration:.2f}秒音频")
        return "这是测试文本"


class ASRFactory:
    """ASR 工厂类"""

    @staticmethod
    def create(asr_type: Optional[str] = None) -> BaseASR:
        """
        创建 ASR 实例

        Args:
            asr_type: ASR 类型，如果为 None 则从配置读取

        Returns:
            BaseASR: ASR 实例
        """
        asr_type = asr_type or settings.asr_type or os.getenv("ASR_TYPE", "mock")

        logger.info(f"[ASR] 创建 ASR 实例: {asr_type}")

        if asr_type == "mock":
            return MockASR()

        elif asr_type == "tencent":
            try:
                tencent_asr = TencentASR()
                if tencent_asr.is_available():
                    logger.success("[ASR] 腾讯 ASR 初始化成功")
                    return tencent_asr
                else:
                    logger.warning("[ASR] 腾讯 ASR 凭证未配置，回退到 MockASR")
                    return MockASR()
            except Exception as e:
                logger.error(f"[ASR] 腾讯 ASR 初始化失败: {e}，回退到 MockASR")
                return MockASR()

        elif asr_type == "funasr":
            # TODO: 实现 FunASR
            logger.warning("[ASR] FunASR 尚未实现，使用 MockASR")
            return MockASR()

        else:
            logger.warning(f"[ASR] 未知的 ASR 类型: {asr_type}，使用 MockASR")
            return MockASR()


# 全局单例
_asr_instance: Optional[BaseASR] = None


def get_asr() -> BaseASR:
    """获取 ASR 单例"""
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = ASRFactory.create()
    return _asr_instance
