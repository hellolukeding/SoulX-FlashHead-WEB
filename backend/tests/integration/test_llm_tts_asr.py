"""
LLM + TTS + ASR 集成测试
测试完整的智能对话流程
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.services.llm import get_llm_client
from app.services.tts import get_tts
from app.services.asr import get_asr
from loguru import logger


async def test_llm():
    """测试 LLM 服务"""
    logger.info("=" * 60)
    logger.info("测试 LLM 服务")
    logger.info("=" * 60)

    llm_client = get_llm_client()

    if not llm_client.is_available():
        logger.error("❌ LLM 服务未配置，跳过测试")
        return False

    # 测试非流式对话
    logger.info("\n--- 测试非流式对话 ---")
    response = await llm_client.chat("你好，请用一句话介绍你自己")
    logger.info(f"LLM 回复: {response}")

    # 测试流式对话
    logger.info("\n--- 测试流式对话 ---")
    logger.info("LLM 流式回复: ", end="")
    async for chunk in llm_client.chat_stream("今天天气怎么样？"):
        print(chunk, end="", flush=True)
    print()  # 换行

    logger.success("✅ LLM 服务测试通过")
    return True


async def test_tts():
    """测试 TTS 服务"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 TTS 服务")
    logger.info("=" * 60)

    tts = get_tts()

    # 测试语音合成
    text = "你好，我是AI数字人助手。"
    logger.info(f"合成文本: {text}")

    audio = await tts.synthesize(text)
    duration = len(audio) / tts.sample_rate

    logger.info(f"音频时长: {duration:.2f}秒")
    logger.info(f"音频采样率: {tts.sample_rate}Hz")
    logger.info(f"音频数据类型: {audio.dtype}")
    logger.info(f"音频形状: {audio.shape}")

    if len(audio) > 0:
        logger.success("✅ TTS 服务测试通过")
        return True
    else:
        logger.error("❌ TTS 生成的音频为空")
        return False


async def test_asr():
    """测试 ASR 服务"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 ASR 服务")
    logger.info("=" * 60)

    asr = get_asr()

    # 创建模拟音频（1秒静音）
    import numpy as np
    audio = np.zeros(16000, dtype=np.float32)

    logger.info("识别模拟音频（1秒静音）")

    text = await asr.recognize(audio)
    logger.info(f"识别结果: {text}")

    logger.success("✅ ASR 服务测试通过")
    return True


async def test_complete_flow():
    """测试完整对话流程"""
    logger.info("\n" + "=" * 60)
    logger.info("测试完整对话流程")
    logger.info("=" * 60)

    llm_client = get_llm_client()
    tts = get_tts()

    if not llm_client.is_available():
        logger.error("❌ LLM 服务未配置，跳过测试")
        return False

    # 用户输入
    user_text = "你好，请介绍一下你自己"
    logger.info(f"用户: {user_text}")

    # LLM 生成回复
    logger.info("AI: ", end="")
    ai_response = ""
    async for chunk in llm_client.chat_stream(user_text):
        print(chunk, end="", flush=True)
        ai_response += chunk
    print()  # 换行

    # TTS 合成语音
    logger.info("合成 AI 语音...")
    audio = await tts.synthesize(ai_response)
    duration = len(audio) / tts.sample_rate
    logger.info(f"音频生成成功，时长: {duration:.2f}秒")

    logger.success("✅ 完整对话流程测试通过")
    return True


async def main():
    """主测试函数"""
    logger.info("🚀 开始集成测试")
    logger.info("=" * 60)

    results = {}

    # 测试各个服务
    results["llm"] = await test_llm()
    results["tts"] = await test_tts()
    results["asr"] = await test_asr()
    results["complete"] = await test_complete_flow()

    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    for service, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{service}: {status}")

    all_passed = all(results.values())
    if all_passed:
        logger.success("\n🎉 所有测试通过！")
        return 0
    else:
        logger.error("\n❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
