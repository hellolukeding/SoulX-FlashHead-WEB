"""
LLM 服务单元测试

测试大语言模型对话服务的核心功能
"""
import pytest
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from loguru import logger

# 添加项目路径
import sys
sys.path.insert(0, 'backend')

from app.services.llm.client import LLMClient, get_llm_client
from app.core.exceptions import LLMError


class TestLLMClient:
    """测试 LLM 客户端"""

    def test_llm_client_init(self):
        """测试 LLM 客户端初始化"""
        client = LLMClient()
        assert client is not None
        assert client.model == "qwen-plus"

    def test_llm_client_init_without_api_key(self):
        """测试没有 API key 的初始化"""
        # 临时移除 API key
        import os
        old_key = os.getenv("OPEN_AI_API_KEY")
        if old_key:
            del os.environ["OPEN_AI_API_KEY"]

        try:
            client = LLMClient()
            assert not client.is_available()
        finally:
            if old_key:
                os.environ["OPEN_AI_API_KEY"] = old_key

    def test_get_system_prompt(self):
        """测试系统提示词"""
        client = LLMClient()
        prompt = client._get_default_system_prompt()

        assert isinstance(prompt, str)
        assert "友好的AI助手" in prompt
        assert "简洁明了" in prompt

    def test_set_system_prompt(self):
        """测试设置自定义提示词"""
        client = LLMClient()
        custom_prompt = "你是一个专业助手"
        client.set_system_prompt(custom_prompt)

        assert client.system_prompt == custom_prompt


class TestLLMChatStream:
    """测试 LLM 流式对话"""

    @pytest.mark.asyncio
    async def test_chat_stream_structure(self):
        """测试流式对话结构"""
        # 需要 API key 才能运行此测试
        client = LLMClient()

        if not client.is_available():
            pytest.skip("需要 LLM API key")

        # 流式生成
        chunks = []
        async for chunk in client.chat_stream("你好"):
            chunks.append(chunk)
            assert isinstance(chunk, str)
            if len(chunks) > 5:  # 测试前几个chunk
                break

        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_chat_stream_with_custom_prompt(self):
        """测试自定义系统提示词"""
        client = LLMClient()
        client.set_system_prompt("你是个数学老师")

        if not client.is_available():
            pytest.skip("需要 LLM API key")

        result_text = ""
        async for chunk in client.chat_stream("1+1等于几？"):
            result_text += chunk
            if "2" in result_text:
                break

        assert "2" in result_text

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("OPEN_AI_API_KEY") is None,
        reason="需要 LLM API key"
    )
    async def test_chat_stream_full_conversation(self):
        """测试完整对话"""
        client = LLMClient()

        if not client.is_available():
            pytest.skip("需要 LLM API key")

        # 发送消息
        full_response = ""
        async for chunk in client.chat_stream("今天天气怎么样？"):
            full_response += chunk

        assert len(full_response) > 0
        assert isinstance(full_response, str)


class TestLLMChatNonStream:
    """测试 LLM 非流式对话"""

    @pytest.mark.asyncio
    async def test_chat_simple(self):
        """测试简单对话"""
        client = LLMClient()

        if not client.is_available():
            pytest.skip("需要 LLM API key")

        result = await client.chat("测试")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self):
        """测试带系统提示的对话"""
        client = LLMClient()
        client.set_system_prompt("你只回答数字")

        if not client.is_available():
            pytest.skip("需要 LLM API key")

        result = await client.chat("一加一等于几？")
        assert "2" in result


class TestLLMBusinessFlow:
    """测试 LLM 业务流程集成"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("OPEN_AI_API_KEY") is None,
        reason="需要 LLM API key"
    )
    async def test_llm_conversation_flow(self):
        """测试 LLM 完整对话流程"""
        client = LLMClient()

        # 模拟用户输入
        user_inputs = [
            "你好",
            "介绍一下你自己",
            "再见"
        ]

        responses = []
        for user_input in user_inputs:
            result = await client.chat(user_input)
            responses.append(result)
            assert len(result) > 0

        assert len(responses) == 3

    @pytest.mark.asyncio
    async def test_llm_streaming_response_quality(self):
        """测试流式响应质量"""
        client = LLMClient()

        if not client.is_available():
            pytest.skip("需要 LLM API key")

        # 收集所有chunks
        chunks = []
        start_time = asyncio.get_event_loop().time()

        async for chunk in client.chat_stream("请用一句话介绍你自己"):
            chunks.append(chunk)

        end_time = asyncio.get_event_loop().time()

        # 验证响应
        full_text = "".join(chunks)
        assert len(full_text) > 10
        assert "数字人" in full_text or "AI" in full_text

        # 验证时效性（应该在5秒内完成）
        duration = end_time - start_time
        assert duration < 5.0


class TestLLMErrorHandling:
    """测试 LLM 错误处理"""

    def test_llm_error_creation(self):
        """测试 LLM 错误异常"""
        error = LLMError("LLM 错误", details={"service": "qwen-plus"})

        assert error.message == "LLM 错误"
        assert error.code == 500
        assert error.details["service"] == "qwen-plus"

    @pytest.mark.asyncio
    async def test_chat_without_api_key(self):
        """测试没有 API key 时的行为"""
        client = LLMClient()

        if client.is_available():
            pytest.skip("API key 已配置")

        result = await client.chat("测试")
        assert "未配置" in result or "错误" in result


class TestLLMGetLLMClient:
    """测试 LLM 客户端单例"""

    def test_get_llm_client_singleton(self):
        """测试获取单例"""
        client1 = get_llm_client()
        client2 = get_llm_client()

        # 应该返回同一个实例
        assert client1 is client2

    def test_get_llm_client_multiple_calls(self):
        """测试多次调用返回同一实例"""
        clients = [get_llm_client() for _ in range(5)]

        # 所有应该是同一个实例
        assert all(c is clients[0] for c in clients)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
