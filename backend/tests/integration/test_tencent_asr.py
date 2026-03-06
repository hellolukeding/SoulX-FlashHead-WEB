"""
测试腾讯 ASR 集成

验证腾讯云语音识别服务
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from loguru import logger
from app.services.asr.factory import get_asr
import numpy as np


async def test_tencent_asr():
    """测试腾讯 ASR"""

    logger.info("=" * 60)
    logger.info("测试腾讯云 ASR")
    logger.info("=" * 60)

    # 检查环境变量
    secret_id = os.getenv("TENCENT_ASR_SECRET_ID") or os.getenv("TENCENT_SECRET_ID")
    secret_key = os.getenv("TENCENT_ASR_SECRET_KEY") or os.getenv("TENCENT_SECRET_KEY")

    if not secret_id or not secret_key:
        logger.warning("⚠️  腾讯 ASR 凭证未配置")
        logger.warning("请设置环境变量:")
        logger.warning("  export TENCENT_ASR_SECRET_ID=your_secret_id")
        logger.warning("  export TENCENT_ASR_SECRET_KEY=your_secret_key")
        logger.info("\n将使用 MockASR 进行测试...")
    else:
        logger.success(f"✅ 腾讯 ASR 凭证已配置: {secret_id[:8]}...")

    # 创建 ASR 实例
    asr = get_asr()
    logger.info(f"\nASR 类型: {type(asr).__name__}")

    # 测试音频（1秒静音）
    test_audio = np.random.randn(16000).astype(np.float32) * 0.1

    logger.info("\n开始识别测试...")
    logger.info(f"音频时长: {len(test_audio)/16000:.2f}秒")
    logger.info(f"采样率: 16000Hz")
    logger.info(f"数据类型: {test_audio.dtype}")

    try:
        # 识别音频
        result = await asr.recognize(test_audio)

        logger.success(f"\n✅ 识别成功")
        logger.info(f"识别结果: {result}")

        return result

    except Exception as e:
        logger.error(f"\n❌ 识别失败: {e}")
        return None


async def test_asr_health():
    """测试 ASR 健康状态"""
    logger.info("\nASR 健康检查:")

    asr = get_asr()
    logger.info(f"  ASR 类型: {type(asr).__name__}")

    if hasattr(asr, 'is_available'):
        available = asr.is_available()
        if available:
            logger.success(f"  状态: ✅ 可用")
        else:
            logger.warning(f"  状态: ⚠️  凭证未配置")
    else:
        logger.info(f"  状态: ✅ MockASR")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    # 运行测试
    asyncio.run(test_asr_health())
    print()
    asyncio.run(test_tencent_asr())
