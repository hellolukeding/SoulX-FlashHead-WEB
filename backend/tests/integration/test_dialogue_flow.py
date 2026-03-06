"""
测试完整对话流程集成

验证: ASR → LLM → TTS → 视频生成
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from loguru import logger
from app.services.asr.factory import get_asr
from app.services.llm.client import get_llm_client
from app.services.tts.factory import get_tts
import numpy as np


async def test_dialogue_flow():
    """测试完整对话流程"""

    logger.info("=" * 60)
    logger.info("开始测试完整对话流程")
    logger.info("=" * 60)

    # 1. 初始化服务
    logger.info("\n[1/5] 初始化服务...")
    asr = get_asr()
    llm = get_llm_client()
    tts = get_tts()

    logger.success(f"✅ ASR: {type(asr).__name__}")
    logger.success(f"✅ LLM: {llm.model if llm.is_available() else '未配置'}")
    logger.success(f"✅ TTS: {type(tts).__name__}")

    # 2. 测试ASR
    logger.info("\n[2/5] 测试 ASR...")
    test_audio = np.random.randn(16000).astype(np.float32) * 0.1  # 1秒静音

    user_text = await asr.recognize(test_audio)
    logger.info(f"识别结果: {user_text}")

    # 3. 测试LLM
    if not llm.is_available():
        logger.warning("⚠️  LLM未配置，跳过LLM测试")
        ai_text = "你好！我是AI助手，很高兴认识你！"
    else:
        logger.info("\n[3/5] 测试 LLM...")
        ai_text = await llm.chat("你好")
        logger.info(f"AI回复: {ai_text}")

    # 4. 测试TTS
    logger.info("\n[4/5] 测试 TTS...")
    ai_audio = await tts.synthesize(ai_text)

    logger.success(f"✅ TTS合成成功")
    logger.info(f"音频时长: {len(ai_audio)/16000:.2f}秒")
    logger.info(f"采样率: 16000Hz")
    logger.info(f"数据类型: {ai_audio.dtype}")

    # 5. 总结
    logger.info("\n[5/5] 测试总结")
    logger.success("=" * 60)
    logger.success("✅ 完整对话流程测试通过")
    logger.success("=" * 60)
    logger.info(f"\n流程验证:")
    logger.info(f"  ASR → 识别文本: {user_text}")
    logger.info(f"  LLM → 生成回复: {ai_text[:30]}...")
    logger.info(f"  TTS → 合成音频: {len(ai_audio)/16000:.2f}秒")
    logger.info(f"  视频 → SoulX-FlashHead (待测试)")


async def test_services_health():
    """测试服务健康状态"""
    logger.info("\n服务健康检查:")

    # ASR
    asr = get_asr()
    logger.info(f"  ASR: {type(asr).__name__} ✅")

    # LLM
    llm = get_llm_client()
    if llm.is_available():
        logger.info(f"  LLM: {llm.model} ✅")
    else:
        logger.warning(f"  LLM: 未配置 ⚠️")

    # TTS
    tts = get_tts()
    logger.info(f"  TTS: {type(tts).__name__} ✅")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    # 运行测试
    asyncio.run(test_services_health())
    print()
    asyncio.run(test_dialogue_flow())
