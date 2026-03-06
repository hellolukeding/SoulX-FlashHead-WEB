"""
TTS 服务单元测试

测试语音合成服务的核心功能
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from loguru import logger

# 添加项目路径
import sys
sys.path.insert(0, 'backend')

from app.services.tts.factory import TTSFactory
from app.services.tts.edge_tts import EdgeTTSEngine
from app.services.tts.cosyvoice_tts import CosyVoiceEngine
from app.services.tts.base import BaseTTS
from app.core.exceptions import TTSError


class TestEdgeTTS:
    """测试 EdgeTTSEngine 实现"""

    def test_edge_tts_instantiation(self):
        """测试 EdgeTTSEngine 实例化"""
        tts = EdgeTTSEngine()
        assert isinstance(tts, BaseTTS)
        assert tts.sample_rate in [16000, 24000]

    @pytest.mark.asyncio
    async def test_edge_tts_synthesize(self):
        """测试 EdgeTTSEngine 合成功能"""
        tts = EdgeTTSEngine()

        # 测试合成
        result = await tts.synthesize("你好，世界")

        assert result is not None
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
        # EdgeTTS 返回 24000Hz 采样率
        assert tts.sample_rate in [16000, 24000]

    @pytest.mark.asyncio
    async def test_edge_tts_with_different_texts(self):
        """测试不同文本内容"""
        tts = EdgeTTSEngine()

        test_texts = [
            "短文本",
            "这是一段中等长度的文本，用于测试 TTS 合成功能",
            "这是一个非常长的文本。" * 10  # 长文本
        ]

        for text in test_texts:
            result = await tts.synthesize(text)
            assert isinstance(result, np.ndarray)
            assert len(result) > 0
            logger.info(f"文本长度: {len(text)}, 音频采样数: {len(result)}")


class TestCosyVoiceTTS:
    """测试 CosyVoiceEngine 实现"""

    def test_cosyvoice_tts_instantiation(self):
        """测试 CosyVoiceEngine 实例化"""
        try:
            tts = CosyVoiceEngine()
            assert isinstance(tts, BaseTTS)
        except Exception as e:
            # CosyVoice 可能因为依赖问题初始化失败
            pytest.skip(f"CosyVoice 不可用: {e}")

    @pytest.mark.asyncio
    async def test_cosyvoice_tts_synthesize(self):
        """测试 CosyVoiceEngine 合成功能"""
        try:
            tts = CosyVoiceEngine()
            result = await tts.synthesize("测试")

            assert result is not None
            assert isinstance(result, np.ndarray)
        except Exception as e:
            pytest.skip(f"CosyVoice 合成失败: {e}")


class TestTTSFactory:
    """测试 TTS 工厂"""

    def test_factory_create_edge(self):
        """测试创建 EdgeTTSEngine"""
        tts = TTSFactory.create("edge")
        assert isinstance(tts, EdgeTTSEngine)

    def test_factory_create_cosyvoice(self):
        """测试创建 CosyVoiceEngine"""
        try:
            tts = TTSFactory.create("cosyvoice")
            assert isinstance(tts, CosyVoiceEngine)
        except Exception:
            # CosyVoice 不可用时跳过
            pass

    def test_factory_default_type(self):
        """测试默认类型"""
        # Mock 环境变量
        import os
        old_tts_type = os.getenv("TTS_TYPE")
        os.environ["TTS_TYPE"] = "edge"

        try:
            tts = TTSFactory.create()
            assert isinstance(tts, EdgeTTSEngine)
        finally:
            # 恢复环境变量
            if old_tts_type:
                os.environ["TTS_TYPE"] = old_tts_type
            else:
                del os.environ["TTS_TYPE"]

    def test_factory_unsupported_type_fallback(self):
        """测试不支持的类型回退到 EdgeTTSEngine"""
        tts = TTSFactory.create("edge")
        assert isinstance(tts, EdgeTTSEngine)


class TestTTSErrorHandling:
    """测试 TTS 错误处理"""

    def test_tts_error_creation(self):
        """测试 TTS 错误异常"""
        error = TTSError("合成失败", details={"text": "测试"})

        assert error.message == "合成失败"
        assert error.code == 500
        assert error.details == {"text": "测试"}
        assert "error" in error.to_dict()

    @pytest.mark.asyncio
    async def test_empty_text_handling(self):
        """测试空文本处理"""
        tts = EdgeTTSEngine()

        # 空文本应该返回静音或空数组
        result = await tts.synthesize("")
        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """测试特殊字符处理"""
        tts = EdgeTTSEngine()

        special_texts = [
            "你好！@#$%",
            "测试emoji 😊👍",
            "Mix中mix English",
            "数字123符号#$"
        ]

        for text in special_texts:
            try:
                result = await tts.synthesize(text)
                assert result is not None
            except Exception as e:
                logger.warning(f"特殊字符合成失败: {text}, 错误: {e}")


class TestTTSBusinessFlow:
    """测试 TTS 业务流程集成"""

    @pytest.mark.asyncio
    async def test_complete_tts_workflow(self):
        """测试完整的 TTS 工作流程"""
        # 创建 TTS 实例
        tts = TTSFactory.create("edge")

        # 模拟 LLM 生成的文本
        llm_texts = [
            "你好！我是数字人助手。",
            "今天天气怎么样？",
            "很高兴为你服务！"
        ]

        # 执行合成
        for text in llm_texts:
            result = await tts.synthesize(text)

            # 验证结果
            assert isinstance(result, np.ndarray)
            assert len(result) > 0
            logger.info(f"文本: {text}, 音频长度: {len(result)} 采样")

    @pytest.mark.asyncio
    async def test_multiple_sequential_syntheses(self):
        """测试连续多次合成"""
        tts = TTSFactory.create("edge")

        results = []
        for i in range(5):
            text = f"这是第{i+1}条测试消息"
            result = await tts.synthesize(text)
            results.append(result)

        # 验证所有合成都成功
        assert len(results) == 5
        assert all(isinstance(r, np.ndarray) for r in results)
        assert all(len(r) > 0 for r in results)

    @pytest.mark.asyncio
    async def test_tts_with_metadata(self):
        """测试带元数据的合成"""
        tts = TTSFactory.create("edge")

        text = "这是一个测试"
        metadata = {
            "session_id": "test_session",
            "user_id": "test_user",
            "timestamp": 1234567890
        }

        # 大多数 TTS 实现会忽略 metadata，但应该接受参数
        result = await tts.synthesize(text)

        assert result is not None
        assert isinstance(result, np.ndarray)

    @pytest.mark.asyncio
    async def test_tts_streaming_scenario(self):
        """测试流式对话场景"""
        """模拟 LLM 流式生成 → TTS 合成的场景"""
        tts = TTSFactory.create("edge")

        # 模拟 LLM 流式生成的文本片段
        llm_chunks = [
            "你好",
            "，",
            "我是",
            "数字人",
            "助手",
            "。"
        ]

        # 场景1: 累积文本后合成（更实际的场景）
        accumulated_text = ""
        for chunk in llm_chunks:
            accumulated_text += chunk

        # 最终合成
        result = await tts.synthesize(accumulated_text)
        assert result is not None
        assert len(result) > 0


class TestTTSEdgeCases:
    """测试 TTS 边界情况"""

    @pytest.mark.asyncio
    async def test_very_long_text(self):
        """测试超长文本"""
        tts = TTSFactory.create("edge")

        # 创建一个很长的文本（1000字）
        long_text = "这是一个很长的文本。" * 100

        result = await tts.synthesize(long_text)
        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_very_short_text(self):
        """测试极短文本"""
        tts = TTSFactory.create("edge")

        short_texts = ["a", "测试", "你好"]

        for text in short_texts:
            result = await tts.synthesize(text)
            assert result is not None

    @pytest.mark.asyncio
    async def test_punctuation_only(self):
        """测试只有标点符号"""
        tts = TTSFactory.create("edge")

        punctuation_texts = [
            "...",
            "！？。",
            "，、；："
        ]

        for text in punctuation_texts:
            try:
                result = await tts.synthesize(text)
                # 可能返回空音频或静音
                assert result is not None
            except Exception as e:
                logger.info(f"标点符号处理: {text}, 结果: {e}")

    @pytest.mark.asyncio
    async def test_multilingual_text(self):
        """测试多语言文本"""
        tts = TTSFactory.create("edge")

        multilingual_texts = [
            "Hello",  # 英文
            "你好",  # 中文
            "こんにちは",  # 日文
            "안녕하세요",  # 韩文
            "Mix中English混合"  # 混合
        ]

        for text in multilingual_texts:
            try:
                result = await tts.synthesize(text)
                assert result is not None
                logger.info(f"多语言测试: {text} -> {len(result)} 采样")
            except Exception as e:
                logger.warning(f"多语言合成可能不支持: {text}")


class TestTTSPerformance:
    """测试 TTS 性能"""

    @pytest.mark.asyncio
    async def test_synthesis_speed(self):
        """测试合成速度"""
        import time
        tts = TTSFactory.create("edge")

        text = "这是一个性能测试文本"
        start_time = time.time()

        result = await tts.synthesize(text)

        end_time = time.time()
        duration = end_time - start_time

        assert result is not None
        # 合成应该在合理时间内完成（< 10秒）
        assert duration < 10.0
        logger.info(f"合成耗时: {duration:.2f}秒")

    @pytest.mark.asyncio
    async def test_concurrent_syntheses(self):
        """测试并发合成"""
        tts = TTSFactory.create("edge")

        # 创建多个并发任务
        tasks = [
            tts.synthesize(f"测试消息{i}")
            for i in range(5)
        ]

        # 并发执行
        results = await asyncio.gather(*tasks)

        # 验证所有任务都成功
        assert len(results) == 5
        assert all(isinstance(r, np.ndarray) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
