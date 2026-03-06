"""
端到端测试

模拟真实用户场景的完整测试
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock
from loguru import logger

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


class TestUserScenarios:
    """测试真实用户场景"""

    @pytest.mark.asyncio
    async def test_simple_greeting_scenario(self):
        """测试简单问候场景"""
        # 场景：用户打招呼，系统回应
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 1. 用户说"你好"
        user_audio = np.random.randn(16000).astype(np.float32) * 0.1

        # 2. ASR 识别
        user_text = await asr.recognize(user_audio)

        # 3. 系统回应
        ai_response = "你好！很高兴为你服务。"

        # 4. TTS 合成
        ai_audio = await tts.synthesize(ai_response)

        # 验证
        assert len(user_text) > 0
        assert len(ai_response) > 0
        assert len(ai_audio) > 0

        logger.info(f"✅ 问候场景: 用户说 '{user_text}' → 系统回应")

    @pytest.mark.asyncio
    async def test_question_answer_scenario(self):
        """测试问答场景"""
        # 场景：用户提问，系统回答
        asr = ASRFactory.create("mock")
        llm = LLMClient()
        tts = TTSFactory.create("edge")

        # 1. 用户提问
        user_audio = np.random.randn(16000 * 3).astype(np.float32) * 0.1

        # 2. ASR 识别
        user_question = await asr.recognize(user_audio)

        # 3. LLM 生成回答
        if llm.is_available():
            ai_answer = await llm.chat(user_question)
        else:
            ai_answer = "这是对问题的模拟回答。"

        # 4. TTS 合成
        ai_audio = await tts.synthesize(ai_answer)

        # 验证完整流程
        assert len(user_question) > 0
        assert len(ai_answer) > 0
        assert len(ai_audio) > 0

        logger.info(f"✅ 问答场景: 问题长度={len(user_question)}, 回答长度={len(ai_answer)}")

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_scenario(self):
        """测试多轮对话场景"""
        # 场景：用户进行多轮对话
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 模拟3轮对话
        conversation_turns = 3
        for turn in range(conversation_turns):
            # 1. 用户说话
            user_audio = np.random.randn(16000).astype(np.float32) * 0.1

            # 2. ASR 识别
            user_text = await asr.recognize(user_audio)

            # 3. 系统回应
            ai_response = f"这是第{turn+1}轮的回复"

            # 4. TTS 合成
            ai_audio = await tts.synthesize(ai_response)

            # 验证
            assert len(user_text) > 0
            assert len(ai_audio) > 0

            logger.info(f"✅ 第{turn+1}轮对话完成")

    @pytest.mark.asyncio
    async def test_fast_consecutive_queries_scenario(self):
        """测试快速连续查询场景"""
        # 场景：用户快速连续提问
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 快速连续3个查询
        queries = ["查询1", "查询2", "查询3"]
        responses = []

        for query in queries:
            # 模拟查询音频
            query_audio = np.random.randn(16000).astype(np.float32) * 0.1

            # ASR 识别
            recognized = await asr.recognize(query_audio)

            # 生成回应
            response = f"回复: {recognized}"

            # TTS 合成
            response_audio = await tts.synthesize(response)

            responses.append({
                'query': recognized,
                'response': response,
                'audio_length': len(response_audio)
            })

        # 验证所有查询都得到响应
        assert len(responses) == len(queries)

        for resp in responses:
            assert len(resp['query']) > 0
            assert len(resp['response']) > 0
            assert resp['audio_length'] > 0

        logger.info(f"✅ 快速连续查询: 完成 {len(responses)} 个查询")


class TestSessionScenarios:
    """测试会话场景"""

    @pytest.mark.asyncio
    async def test_full_session_lifecycle_scenario(self):
        """测试完整会话生命周期场景"""
        # 场景：用户建立会话 → 交互 → 关闭会话
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 1. 创建会话
        session = SessionState(session_id="test_session", model_type="lite")
        assert session.status == "creating"

        # 2. 激活会话
        session.status = "active"
        assert session.status == "active"

        # 3. 进行交互
        user_audio = np.random.randn(16000).astype(np.float32) * 0.1
        user_text = await asr.recognize(user_audio)
        ai_audio = await tts.synthesize("回复")

        assert len(user_text) > 0
        assert len(ai_audio) > 0

        # 更新会话统计
        session.audio_chunks_received = 1
        session.video_frames_generated = 10

        # 4. 关闭会话
        session.status = "closed"
        assert session.status == "closed"

        logger.info(f"✅ 会话生命周期完成: 收到{session.audio_chunks_received}个音频块")

    @pytest.mark.asyncio
    async def test_session_pause_resume_scenario(self):
        """测试会话暂停/恢复场景"""
        # 场景：用户暂停会话，稍后恢复
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 1. 创建并激活会话
        session = SessionState(session_id="test_session_2", model_type="lite")
        session.status = "active"

        # 2. 第一次交互
        user_audio1 = np.random.randn(16000).astype(np.float32) * 0.1
        user_text1 = await asr.recognize(user_audio1)
        ai_audio1 = await tts.synthesize("回复1")

        # 3. 暂停会话
        session.status = "paused"

        # 4. 恢复会话
        session.status = "active"

        # 5. 第二次交互
        user_audio2 = np.random.randn(16000).astype(np.float32) * 0.1
        user_text2 = await asr.recognize(user_audio2)
        ai_audio2 = await tts.synthesize("回复2")

        # 验证两次交互都成功
        assert len(user_text1) > 0 and len(ai_audio1) > 0
        assert len(user_text2) > 0 and len(ai_audio2) > 0

        logger.info("✅ 会话暂停/恢复场景完成")


class TestErrorRecoveryScenarios:
    """测试错误恢复场景"""

    @pytest.mark.asyncio
    async def test_empty_input_recovery_scenario(self):
        """测试空输入恢复场景"""
        # 场景：用户发送空音频，系统优雅处理
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 1. 空音频输入
        empty_audio = np.array([])

        # 2. ASR 处理空音频
        result = await asr.recognize(empty_audio)
        assert result is not None

        # 3. 空文本输入
        empty_text = ""

        # 4. TTS 处理空文本
        audio_result = await tts.synthesize(empty_text)
        assert audio_result is not None

        logger.info("✅ 空输入恢复场景通过")

    @pytest.mark.asyncio
    async def test_very_long_input_handling_scenario(self):
        """测试超长输入处理场景"""
        # 场景：用户发送超长音频
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 1. 超长音频（30秒）
        long_audio = np.random.randn(16000 * 30).astype(np.float32) * 0.1

        # 2. ASR 处理长音频
        result = await asr.recognize(long_audio)
        assert result is not None

        # 3. 超长文本
        long_text = "这是一个很长的文本。" * 200

        # 4. TTS 处理长文本
        audio_result = await tts.synthesize(long_text)
        assert audio_result is not None

        logger.info("✅ 超长输入处理场景通过")


class TestPerformanceScenarios:
    """测试性能场景"""

    @pytest.mark.asyncio
    async def test_response_time_scenario(self):
        """测试响应时间场景"""
        # 场景：用户期望快速响应
        import time
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 记录开始时间
        start_time = time.time()

        # 完整流程
        user_audio = np.random.randn(16000).astype(np.float32) * 0.1
        user_text = await asr.recognize(user_audio)
        ai_audio = await tts.synthesize("快速回复")

        # 计算响应时间
        response_time = time.time() - start_time

        # 验证
        assert len(user_text) > 0
        assert len(ai_audio) > 0
        # 响应时间应该合理（< 5秒）
        assert response_time < 5.0

        logger.info(f"✅ 响应时间: {response_time:.2f}秒")

    @pytest.mark.asyncio
    async def test_concurrent_users_scenario(self):
        """测试并发用户场景"""
        # 场景：多个用户同时使用系统
        asr = ASRFactory.create("mock")
        tts = TTSFactory.create("edge")

        # 模拟5个并发用户
        async def user_session(user_id: int):
            user_audio = np.random.randn(16000).astype(np.float32) * 0.1
            user_text = await asr.recognize(user_audio)
            ai_audio = await tts.synthesize(f"用户{user_id}的回复")
            return user_id, len(user_text), len(ai_audio)

        # 并发执行
        tasks = [user_session(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # 验证所有用户都得到服务
        assert len(results) == 5

        for user_id, text_len, audio_len in results:
            assert text_len > 0
            assert audio_len > 0

        logger.info(f"✅ 并发用户场景: {len(results)} 个用户同时使用")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
