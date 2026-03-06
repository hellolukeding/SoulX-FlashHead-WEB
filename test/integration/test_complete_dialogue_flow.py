"""
完整对话流程集成测试

测试 ASR → LLM → TTS → 视频生成 的完整流程
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from loguru import logger

# 添加项目路径
import sys
sys.path.insert(0, 'backend')

# Mock FlashHead 相关导入
sys.modules['flash_head'] = MagicMock()
sys.modules['flash_head.inference'] = MagicMock()
sys.modules['xfuser'] = MagicMock()
sys.modules['xfuser.core'] = MagicMock()
sys.modules['xfuser.core.distributed'] = MagicMock()

from app.services.asr.factory import ASRFactory
from app.services.llm.client import LLMClient
from app.services.tts.factory import TTSFactory
from app.core.session.state import SessionState, SessionStatus


class TestCompleteTextDialogueFlow:
    """测试完整文本对话流程"""

    @pytest.mark.asyncio
    async def test_text_in_text_out_flow(self):
        """测试文本输入 → 文本输出流程"""
        # 1. 初始化组件
        llm = LLMClient()

        if not llm.is_available():
            pytest.skip("需要 LLM API key")

        # 2. 用户输入文本
        user_text = "你好，请介绍一下你自己"

        # 3. LLM 生成回复
        ai_response = ""
        async for chunk in llm.chat_stream(user_text):
            ai_response += chunk
            # 测试前几个chunk即可
            if len(ai_response) > 50:
                break

        # 4. 验证流程
        assert len(user_text) > 0
        assert len(ai_response) > 0
        assert isinstance(ai_response, str)

        logger.info(f"用户: {user_text}")
        logger.info(f"AI: {ai_response[:100]}...")

    @pytest.mark.asyncio
    async def test_text_conversation_with_multiple_turns(self):
        """测试多轮文本对话"""
        llm = LLMClient()

        if not llm.is_available():
            pytest.skip("需要 LLM API key")

        # 多轮对话
        conversation = [
            "你好",
            "你叫什么名字？",
            "你能做什么？",
            "谢谢"
        ]

        responses = []
        for user_input in conversation:
            response = await llm.chat(user_input)
            responses.append(response)
            assert len(response) > 0

        assert len(responses) == len(conversation)
        logger.info(f"完成了 {len(conversation)} 轮对话")


class TestCompleteAudioDialogueFlow:
    """测试完整音频对话流程"""

    @pytest.mark.asyncio
    async def test_audio_in_audio_out_flow(self):
        """测试音频输入 → 音频输出流程"""
        # 1. 初始化组件
        asr = ASRFactory.create("mock")
        llm = LLMClient()
        tts = TTSFactory.create("edge")

        # 2. 模拟用户音频输入
        user_audio = np.random.randn(16000).astype(np.float32) * 0.1

        # 3. ASR 识别
        user_text = await asr.recognize(user_audio)
        assert isinstance(user_text, str)
        assert len(user_text) > 0

        # 4. LLM 生成回复
        if llm.is_available():
            ai_text = await llm.chat(user_text)
            assert isinstance(ai_text, str)
            assert len(ai_text) > 0
        else:
            # 如果 LLM 不可用，使用模拟文本
            ai_text = "这是一个测试回复"

        # 5. TTS 合成
        ai_audio = await tts.synthesize(ai_text)
        assert isinstance(ai_audio, np.ndarray)
        assert len(ai_audio) > 0

        # 验证完整流程
        logger.info(f"ASR: {user_text}")
        logger.info(f"LLM: {ai_text[:50]}...")
        logger.info(f"TTS: {len(ai_audio)} 采样")

    @pytest.mark.asyncio
    async def test_audio_conversation_with_multiple_turns(self):
        """测试多轮音频对话"""
        asr = ASRFactory.create("mock")
        llm = LLMClient()
        tts = TTSFactory.create("edge")

        # 多轮对话
        num_turns = 3
        for i in range(num_turns):
            # 1. 用户音频
            user_audio = np.random.randn(16000).astype(np.float32) * 0.1

            # 2. ASR
            user_text = await asr.recognize(user_audio)

            # 3. LLM
            if llm.is_available():
                ai_text = await llm.chat(user_text)
            else:
                ai_text = f"这是第{i+1}轮回复"

            # 4. TTS
            ai_audio = await tts.synthesize(ai_text)

            # 验证
            assert len(user_text) > 0
            assert len(ai_text) > 0
            assert len(ai_audio) > 0

            logger.info(f"第{i+1}轮完成: {len(ai_audio)} 采样")


class TestASRTTSIntegration:
    """测试 ASR + TTS 集成"""

    @pytest.mark.asyncio
    async def test_asr_tts_roundtrip(self):
        """测试 ASR → TTS 循环"""
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 1. 模拟音频输入
        test_audio = np.random.randn(16000).astype(np.float32) * 0.1

        # 2. ASR 识别
        recognized_text = await asr.recognize(test_audio)
        assert len(recognized_text) > 0

        # 3. TTS 合成
        synthesized_audio = await tts.synthesize(recognized_text)
        assert len(synthesized_audio) > 0

        logger.info(f"循环测试: 音频({len(test_audio)}) → 文本({len(recognized_text)}) → 音频({len(synthesized_audio)})")


class TestBusinessWorkflows:
    """测试业务流程"""

    @pytest.mark.asyncio
    async def test_simple_query_workflow(self):
        """测试简单查询流程"""
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 模拟用户查询
        user_query_audio = np.random.randn(16000 * 2).astype(np.float32) * 0.1

        # ASR 识别
        user_query = await asr.recognize(user_query_audio)

        # 模拟回复
        ai_response = "我收到了你的问题"

        # TTS 合成
        ai_response_audio = await tts.synthesize(ai_response)

        # 验证
        assert len(user_query) > 0
        assert len(ai_response) > 0
        assert len(ai_response_audio) > 0

        logger.info("✅ 简单查询流程完成")

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 创建多个并发任务
        async def process_request(request_id: int):
            user_audio = np.random.randn(16000).astype(np.float32) * 0.1
            user_text = await asr.recognize(user_audio)
            ai_audio = await tts.synthesize(f"回复{request_id}")
            return request_id, len(user_text), len(ai_audio)

        # 并发执行
        tasks = [process_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # 验证所有任务都成功
        assert len(results) == 5
        for request_id, text_len, audio_len in results:
            assert text_len > 0
            assert audio_len > 0

        logger.info(f"✅ 并发处理 {len(results)} 个请求")


class TestErrorScenarios:
    """测试错误场景"""

    @pytest.mark.asyncio
    async def test_empty_audio_handling(self):
        """测试空音频处理"""
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 空音频
        empty_audio = np.array([])

        # ASR 应该处理空音频
        result = await asr.recognize(empty_audio)
        assert result is not None

        # TTS 应该处理空文本
        audio_result = await tts.synthesize("")
        assert audio_result is not None

        logger.info("✅ 空音频处理测试通过")

    @pytest.mark.asyncio
    async def test_very_long_audio_handling(self):
        """测试超长音频处理"""
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 超长音频（10秒）
        long_audio = np.random.randn(16000 * 10).astype(np.float32) * 0.1

        # ASR 应该处理长音频
        result = await asr.recognize(long_audio)
        assert result is not None

        # 超长文本
        long_text = "这是一个很长的测试。" * 100

        # TTS 应该处理长文本
        audio_result = await tts.synthesize(long_text)
        assert audio_result is not None

        logger.info("✅ 超长音频处理测试通过")


class TestPerformanceScenarios:
    """测试性能场景"""

    @pytest.mark.asyncio
    async def test_response_time(self):
        """测试响应时间"""
        import time
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        start_time = time.time()

        # 完整流程
        test_audio = np.random.randn(16000).astype(np.float32) * 0.1
        user_text = await asr.recognize(test_audio)
        ai_audio = await tts.synthesize(user_text)

        end_time = time.time()
        duration = end_time - start_time

        # 验证
        assert len(user_text) > 0
        assert len(ai_audio) > 0
        # 响应时间应该在合理范围内（< 10秒）
        assert duration < 10.0

        logger.info(f"✅ 响应时间: {duration:.2f}秒")

    @pytest.mark.asyncio
    async def test_throughput(self):
        """测试吞吐量"""
        import time
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 批量处理
        num_requests = 10
        start_time = time.time()

        for i in range(num_requests):
            test_audio = np.random.randn(16000).astype(np.float32) * 0.1
            user_text = await asr.recognize(test_audio)
            ai_audio = await tts.synthesize(f"测试{i}")

        end_time = time.time()
        duration = end_time - start_time
        throughput = num_requests / duration

        logger.info(f"✅ 吞吐量: {throughput:.2f} 请求/秒")

        # 验证吞吐量合理
        assert throughput > 0.5  # 至少每2秒一个请求


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
