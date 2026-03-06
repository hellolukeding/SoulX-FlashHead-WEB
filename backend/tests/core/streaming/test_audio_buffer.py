import pytest
import numpy as np
from app.core.streaming.audio_buffer import AudioBuffer


@pytest.fixture
def buffer():
    return AudioBuffer(window_size=1.0, sample_rate=16000)


def test_add_chunks_until_full(buffer):
    """测试累积到完整窗口"""
    # 添加 0.5 秒
    chunk = np.zeros(8000, dtype=np.float32)  # 0.5s @ 16kHz
    result = buffer.add_chunk(chunk)
    assert result is None  # 未满

    # 再添加 0.5 秒
    result = buffer.add_chunk(chunk)
    assert result is not None  # 已满
    assert len(result) == 16000  # 1 秒 @ 16kHz


def test_partial_buffer(buffer):
    """测试部分缓冲"""
    chunk = np.zeros(4000, dtype=np.float32)
    result = buffer.add_chunk(chunk)

    assert result is None
    assert buffer.get_buffer_size() == 0.25  # 4000/16000


def test_clear_buffer(buffer):
    """测试清空缓冲"""
    chunk = np.zeros(8000, dtype=np.float32)
    buffer.add_chunk(chunk)
    buffer.clear()

    assert buffer.get_buffer_size() == 0.0


def test_overflow_handling(buffer):
    """测试缓冲溢出处理"""
    # 添加 1.5 秒数据
    chunk = np.zeros(24000, dtype=np.float32)  # 1.5s @ 16kHz
    result = buffer.add_chunk(chunk)

    assert result is not None
    assert len(result) == 16000  # 返回 1 秒
    assert buffer.get_buffer_size() == 0.5  # 剩余 0.5 秒
