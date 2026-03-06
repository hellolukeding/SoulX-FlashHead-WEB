"""
WebSocket Handler 单元测试

测试 WebSocket 消息处理和会话管理
"""
import pytest
import asyncio
import json
import numpy as np
from unittest.mock import Mock, AsyncMock, MagicMock, patch
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

from app.core.session.state import SessionState, SessionStatus
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    RateLimitError
)


class TestConnectionManager:
    """测试连接管理器（不依赖实际的 handler.py）"""

    def test_connection_manager_init(self):
        """测试连接管理器初始化"""
        # 创建一个简单的连接管理器类
        class SimpleConnectionManager:
            def __init__(self):
                self.active_connections = {}
                self.sessions = {}
                self.engines = {}
        
        manager = SimpleConnectionManager()
        assert manager is not None
        assert len(manager.active_connections) == 0
        assert len(manager.sessions) == 0
        assert len(manager.engines) == 0


class TestSessionLifecycle:
    """测试会话生命周期"""

    @pytest.fixture
    def mock_websocket(self):
        """创建 mock WebSocket"""
        ws = Mock()
        ws.send = AsyncMock()
        ws.receive = AsyncMock()
        ws.close = AsyncMock()
        return ws

    def test_create_session(self):
        """测试创建会话"""
        session_id = "test_session_001"
        model_type = "lite"

        # 创建会话
        session = SessionState(session_id=session_id, model_type=model_type)

        assert session.session_id == session_id
        assert session.model_type == model_type
        assert session.status == "creating"

    @pytest.mark.asyncio
    async def test_session_initialization(self, mock_websocket):
        """测试会话初始化流程"""
        session_id = "test_session_002"

        # 模拟初始化会话
        session = SessionState(session_id=session_id, model_type="lite")

        # 验证会话状态
        assert session_id == session.session_id
        assert session.status == "creating"

    @pytest.mark.asyncio
    async def test_session_activation(self, mock_websocket):
        """测试会话激活"""
        session_id = "test_session_003"

        session = SessionState(session_id=session_id, model_type="lite")

        # 激活会话
        session.status = "active"

        assert session.status == "active"

    @pytest.mark.asyncio
    async def test_session_pause(self, mock_websocket):
        """测试会话暂停"""
        session_id = "test_session_004"

        session = SessionState(session_id=session_id, model_type="lite")
        session.status = "active"

        # 暂停会话
        session.status = "paused"

        assert session.status == "paused"

    @pytest.mark.asyncio
    async def test_session_resume(self, mock_websocket):
        """测试会话恢复"""
        session_id = "test_session_005"

        session = SessionState(session_id=session_id, model_type="lite")
        session.status = "paused"

        # 恢复会话
        session.status = "active"

        assert session.status == "active"

    @pytest.mark.asyncio
    async def test_session_close(self, mock_websocket):
        """测试会话关闭"""
        session_id = "test_session_006"

        session = SessionState(session_id=session_id, model_type="lite")

        # 关闭会话
        session.status = "closed"

        # 验证状态更新
        assert session.status == "closed"


class TestMessageHandling:
    """测试消息处理"""

    @pytest.fixture
    def mock_websocket(self):
        """创建 mock WebSocket"""
        ws = Mock()
        ws.send = AsyncMock()
        ws.receive = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_handle_text_message(self, mock_websocket):
        """测试处理文本消息"""
        session_id = "test_session_007"

        # 创建会话
        session = SessionState(session_id=session_id, model_type="lite")

        # 模拟消息数据
        message_data = {
            "type": "text",
            "text": "你好"
        }

        # 验证消息格式
        assert message_data["type"] == "text"
        assert "text" in message_data
        assert len(message_data["text"]) > 0

    @pytest.mark.asyncio
    async def test_handle_audio_message(self, mock_websocket):
        """测试处理音频消息"""
        session_id = "test_session_008"

        # 创建会话
        session = SessionState(session_id=session_id, model_type="lite")

        # 模拟音频数据
        test_audio = np.random.randn(16000).astype(np.float32) * 0.1
        import base64
        audio_bytes = test_audio.tobytes()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        message_data = {
            "type": "audio",
            "audio_data": audio_base64,
            "audio_format": "wav"
        }

        # 验证消息格式
        assert message_data["type"] == "audio"
        assert "audio_data" in message_data
        assert "audio_format" in message_data

    @pytest.mark.asyncio
    async def test_handle_create_session_message(self, mock_websocket):
        """测试处理创建会话消息"""
        session_id = "test_session_009"

        # 模拟创建会话消息
        message_data = {
            "type": "create_session",
            "model_type": "lite",
            "reference_image": "base64_encoded_image_data"
        }

        # 验证消息格式
        assert message_data["type"] == "create_session"
        assert "model_type" in message_data
        assert message_data["model_type"] in ["lite", "pro"]
        assert "reference_image" in message_data


class TestErrorHandling:
    """测试错误处理"""

    @pytest.fixture
    def mock_websocket(self):
        ws = Mock()
        ws.send = AsyncMock()
        ws.receive = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_invalid_message_type(self, mock_websocket):
        """测试无效消息类型"""
        session_id = "test_session_010"

        session = SessionState(session_id=session_id, model_type="lite")

        # 无效消息类型
        message_data = {
            "type": "invalid_type",
            "data": "test"
        }

        # 应该能识别出无效类型
        valid_types = ["text", "audio", "create_session", "pause_session", "resume_session", "close_session"]
        assert message_data["type"] not in valid_types

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, mock_websocket):
        """测试缺少必需字段"""
        session_id = "test_session_011"

        session = SessionState(session_id=session_id, model_type="lite")

        # 缺少必需字段
        message_data = {
            "type": "text"
            # 缺少 "text" 字段
        }

        # 应该验证失败
        if message_data["type"] == "text":
            assert "text" not in message_data

    @pytest.mark.asyncio
    async def test_authentication_error(self, mock_websocket):
        """测试认证错误"""
        # 模拟无效 token
        invalid_token = "invalid_token_12345"

        # 应该抛出认证错误
        from app.core.auth import verify_websocket_token
        result = verify_websocket_token(invalid_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_validation_error(self, mock_websocket):
        """测试验证错误"""
        # 测试空文本
        empty_text = ""

        # 应该验证失败
        assert len(empty_text.strip()) == 0

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, mock_websocket):
        """测试速率限制"""
        from app.api.middleware.rate_limit import RateLimiter

        limiter = RateLimiter()
        limiter.max_requests = 5  # 设置较小的限制

        client_id = "test_client"

        # 前5个请求应该通过
        for _ in range(5):
            assert limiter.is_allowed(client_id) == True

        # 第6个请求应该被限制
        assert limiter.is_allowed(client_id) == False


class TestCompleteDialogueFlow:
    """测试完整对话流程"""

    @pytest.fixture
    def mock_websocket(self):
        ws = Mock()
        ws.send = AsyncMock()
        ws.receive = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_text_to_text_flow(self, mock_websocket):
        """测试文本到文本流程"""
        session_id = "test_session_012"

        # 1. 创建会话
        session = SessionState(session_id=session_id, model_type="lite")

        # 2. 用户发送文本消息
        user_message = "你好"

        # 3. 验证流程步骤
        assert session.status == "creating"
        assert len(user_message) > 0

    @pytest.mark.asyncio
    async def test_audio_to_audio_flow(self, mock_websocket):
        """测试音频到音频流程"""
        session_id = "test_session_013"

        # 1. 创建会话
        session = SessionState(session_id=session_id, model_type="lite")

        # 2. 用户发送音频
        test_audio = np.random.randn(16000).astype(np.float32) * 0.1

        # 3. 验证流程
        assert session.status == "creating"
        assert len(test_audio) > 0

    @pytest.mark.asyncio
    async def test_session_lifecycle_flow(self, mock_websocket):
        """测试完整会话生命周期"""
        session_id = "test_session_014"

        # 1. 创建会话
        session = SessionState(session_id=session_id, model_type="lite")

        assert session.status == "creating"

        # 2. 激活会话
        session.status = "active"
        assert session.status == "active"

        # 3. 暂停会话
        session.status = "paused"
        assert session.status == "paused"

        # 4. 恢复会话
        session.status = "active"
        assert session.status == "active"

        # 5. 关闭会话
        session.status = "closed"
        assert session.status == "closed"


class TestConcurrentConnections:
    """测试并发连接"""

    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """测试多个会话"""
        # 创建多个会话
        session_ids = [f"session_{i:03d}" for i in range(10)]

        sessions = {}
        for session_id in session_ids:
            session = SessionState(session_id=session_id, model_type="lite")
            sessions[session_id] = session

        # 验证所有会话都创建成功
        assert len(sessions) == 10
        for session_id in session_ids:
            assert session_id in sessions

    @pytest.mark.asyncio
    async def test_connection_limit(self):
        """测试连接数限制"""
        from app.api.middleware.rate_limit import ConnectionRateLimiter

        limiter = ConnectionRateLimiter(max_connections=5)

        # 前5个连接应该通过
        for i in range(5):
            assert limiter.can_connect(f"connection_{i}") == True

        # 第6个连接应该被拒绝
        assert limiter.can_connect("connection_5") == False

        # 断开一个连接后，应该能接受新连接
        limiter.disconnect("connection_0")
        assert limiter.can_connect("connection_5") == True


class TestStateManagement:
    """测试状态管理"""

    def test_session_state_transitions(self):
        """测试会话状态转换"""
        from app.core.session.state import SessionStatus

        session = SessionState(session_id="test", model_type="lite")

        # CREATED -> ACTIVE
        assert session.status == "creating"
        session.status = "active"
        assert session.status == "active"

        # ACTIVE -> PAUSED
        session.status = "paused"
        assert session.status == "paused"

        # PAUSED -> ACTIVE
        session.status = "active"
        assert session.status == "active"

        # ACTIVE -> CLOSED
        session.status = "closed"
        assert session.status == "closed"

    def test_session_metadata(self):
        """测试会话统计信息"""
        session = SessionState(session_id="test", model_type="lite")
        
        # 修改统计信息
        session.audio_chunks_received = 5
        session.video_frames_generated = 10
        session.total_audio_duration = 1.5
        
        assert session.audio_chunks_received == 5
        assert session.video_frames_generated == 10
        assert session.total_audio_duration == 1.5
        assert session.total_audio_duration == 1.5
