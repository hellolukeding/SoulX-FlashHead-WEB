"""
WebSocket 流式处理集成测试
"""
import pytest
import asyncio
import base64
import numpy as np
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_audio_b64():
    """创建测试音频数据"""
    # 生成 1 秒测试音频
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * 440 * t)
    audio = (audio * 32767).astype(np.int16)

    # 简单的 WAV 头
    import struct
    audio_bytes = audio.tobytes()
    wav_data = b'RIFF' + struct.pack('<I', 36 + len(audio_bytes))
    wav_data += b'WAVEfmt ' + struct.pack('<I', 16)
    wav_data += struct.pack('<H', 1)  # PCM
    wav_data += struct.pack('<H', 1)  # mono
    wav_data += struct.pack('<I', sample_rate)
    wav_data += struct.pack('<I', sample_rate * 2)
    wav_data += struct.pack('<H', 2)
    wav_data += struct.pack('<H', 16)
    wav_data += b'data' + struct.pack('<I', len(audio_bytes))
    wav_data += audio_bytes

    return base64.b64encode(wav_data).decode()


@pytest.fixture
def sample_image_b64():
    """创建测试图像数据"""
    from PIL import Image
    import io

    img = Image.fromarray(np.zeros((512, 512, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    return base64.b64encode(img_bytes).decode()


@pytest.mark.asyncio
@pytest.mark.skip(reason="需要完整的模型环境")
async def test_websocket_connection_flow(client, sample_audio_b64, sample_image_b64):
    """测试完整的 WebSocket 连接流程"""
    # 这个测试需要：
    # 1. 真实的 WebSocket 连接
    # 2. 模型文件存在
    # 3. GPU 可用
    # 因此在 CI/CD 中跳过，仅用于本地开发测试

    with client.websocket_connect("/api/ws") as websocket:
        session_id = "test_session_001"

        # 1. 发送创建会话消息
        websocket.send_json({
            "type": "create_session",
            "data": {
                "model_type": "lite",
                "reference_image": sample_image_b64
            }
        })

        # 2. 接收会话创建响应
        response = websocket.receive_json()
        assert response["type"] == "session_created"
        assert response["data"]["status"] == "ready"

        # 3. 发送音频块
        websocket.send_json({
            "type": "audio_chunk",
            "data": {
                "audio_data": sample_audio_b64,
                "format": "wav",
                "sequence": 0
            }
        })

        # 4. 接收音频确认
        response = websocket.receive_json()
        assert response["type"] == "audio_received"
        assert response["data"]["status"] == "processing"

        # 5. 关闭会话
        websocket.send_json({
            "type": "close_session",
            "data": {}
        })

        # 6. 接收关闭确认
        response = websocket.receive_json()
        assert response["type"] == "session_closed"


def test_health_endpoint(client):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gpu_available" in data


def test_root_endpoint(client):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_ping_pong(client):
    """测试心跳机制"""
    with client.websocket_connect("/api/ws") as websocket:
        # 发送 ping
        websocket.send_json({
            "type": "ping",
            "data": {}
        })

        # 接收 pong
        response = websocket.receive_json()
        assert response["type"] == "pong"
        assert "timestamp" in response["data"]


@pytest.mark.asyncio
async def test_error_handling(client):
    """测试错误处理"""
    with client.websocket_connect("/api/ws") as websocket:
        # 发送未知消息类型
        websocket.send_json({
            "type": "unknown_type",
            "data": {}
        })

        # 应该接收错误响应
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert response["data"]["code"] == 400
