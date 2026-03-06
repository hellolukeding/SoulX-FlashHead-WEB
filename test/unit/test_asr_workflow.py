"""
ASR 服务单元测试

测试语音识别服务的核心功能
"""
import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from loguru import logger

# 添加项目路径
import sys
sys.path.insert(0, 'backend')

from app.services.asr.factory import ASRFactory, MockASR
from app.services.asr.base import BaseASR
from app.core.exceptions import ASRError


class TestMockASR:
    """测试 MockASR 实现"""

    def test_mock_asr_instantiation(self):
        """测试 MockASR 实例化"""
        asr = MockASR()
        assert isinstance(asr, BaseASR)
        assert asr.sample_rate == 16000

    def test_mock_asr_recognize(self):
        """测试 MockASR 识别功能"""
        asr = MockASR()

        # 创建测试音频数据 (1秒静音)
        test_audio = np.random.randn(16000).astype(np.float32) * 0.1

        # 测试识别
        result = asyncio.run(asr.recognize(test_audio))

        assert isinstance(result, str)
        assert result == "这是测试文本"

    def test_mock_asr_with_different_duration(self):
        """测试不同音频时长"""
        asr = MockASR()

        # 测试不同时长
        for duration in [0.5, 1.0, 2.0, 5.0]:
            samples = int(duration * 16000)
            audio = np.random.randn(samples).astype(np.float32) * 0.1
            result = asyncio.run(asr.recognize(audio))

            assert isinstance(result, str)
            assert len(result) > 0


class TestASRFactory:
    """测试 ASR 工厂"""

    def test_factory_create_mock(self):
        """测试创建 MockASR"""
        asr = ASRFactory.create("mock")
        assert isinstance(asr, MockASR)

    def test_factory_default_type(self):
        """测试默认类型"""
        # Mock 环境变量
        import os
        old_asr_type = os.getenv("ASR_TYPE")
        os.environ["ASR_TYPE"] = "mock"

        try:
            asr = ASRFactory.create()
            assert isinstance(asr, MockASR)
        finally:
            # 恢复环境变量
            if old_asr_type:
                os.environ["ASR_TYPE"] = old_asr_type
            else:
                del os.environ["ASR_TYPE"]

    def test_factory_unsupported_type_fallback(self):
        """测试不支持的类型回退到 MockASR"""
        asr = ASRFactory.create("unsupported_type")
        assert isinstance(asr, MockASR)


class TestASRErrorHandling:
    """测试 ASR 错误处理"""

    def test_asr_error_creation(self):
        """测试 ASR 错误异常"""
        error = ASRError("测试错误", details={"info": "测试详情"})

        assert error.message == "测试错误"
        assert error.code == 400
        assert error.details == {"info": "测试详情"}
        assert "error" in error.to_dict()

    def test_asr_error_to_dict(self):
        """测试异常转字典"""
        error = ASRError("转换错误")
        error_dict = error.to_dict()

        assert error_dict["error"] == "转换错误"
        assert error_dict["code"] == 400


class TestASRBusinessFlow:
    """测试 ASR 业务流程集成"""

    @pytest.mark.asyncio
    async def test_complete_asr_workflow(self):
        """测试完整的 ASR 工作流程"""
        # 创建 ASR 实例
        asr = ASRFactory.create("mock")

        # 模拟用户音频
        user_audio = np.random.randn(16000 * 3).astype(np.float32) * 0.1  # 3秒

        # 执行识别
        result = await asr.recognize(user_audio)

        # 验证结果
        assert isinstance(result, str)
        assert len(result) > 0
        logger.info(f"ASR 识别结果: {result}")

    @pytest.mark.asyncio
    async def test_multiple_sequential_requests(self):
        """测试连续多次识别"""
        asr = ASRFactory.create("mock")

        results = []
        for i in range(5):
            audio = np.random.randn(16000).astype(np.float32) * 0.1
            result = await asr.recognize(audio)
            results.append(result)

        # 验证所有识别都成功
        assert len(results) == 5
        assert all(isinstance(r, str) for r in results)

    @pytest.mark.asyncio
    async def test_asr_with_metadata(self):
        """测试带元数据的识别"""
        asr = ASRFactory.create("mock")

        audio = np.random.randn(16000).astype(np) * 0.1
        metadata = {
            "user_id": "test_user",
            "timestamp": 1234567890,
            "duration": 1.0
        }

        result = await asr.recognize(audio, metadata)

        assert result == "这是测试文本"

    @pytest.mark.asyncio
    async def test_asr_error_handling(self):
        """测试 ASR 错误处理"""
        asr = ASRFactory.create("mock")

        # MockASR 不会抛出异常，所以这里测试其他场景
        audio = np.random.randn(16000).astype(np.float32) * 0.1

        # 应该正常工作
        result = await asr.recognize(audio)
        assert result is not None


class TestASREdgeCases:
    """测试 ASR 边界情况"""

    @pytest.mark.asyncio
    async def test_empty_audio(self):
        """测试空音频"""
        asr = ASRFactory.create("mock")

        # 创建空音频
        empty_audio = np.array([], dtype=np.float32)

        # 应该仍然返回结果（MockASR 行为）
        result = await asr.recognize(empty_audio)
        assert result == "这是测试文本"

    @pytest.mark.asyncio
    async def test_very_long_audio(self):
        """测试超长音频"""
        asr = ASRFactory.create("mock")

        # 创建 10 秒音频
        long_audio = np.random.randn(16000 * 10).astype(np.float32) * 0.1

        result = await asr.recognize(long_audio)
        assert result == "这是测试文本"

    @pytest.mark.asyncio
    async def test_stereo_audio_converted(self):
        """测试立体声转单声道"""
        asr = ASRFactory.create("mock")

        # 创建立体声音频 (2 声道)
        stereo_audio = np.random.randn(16000, 2).astype(np.float32) * 0.1

        # 应该仍然工作（MockASR 不检查格式）
        result = await asr.recognize(stereo_audio)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
