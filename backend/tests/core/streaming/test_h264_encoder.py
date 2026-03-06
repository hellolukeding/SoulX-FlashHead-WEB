import pytest
import numpy as np
from app.core.streaming.h264_encoder import H264Encoder


@pytest.fixture
def encoder():
    return H264Encoder(fps=25, bitrate="2M")


@pytest.fixture
def sample_frame():
    """创建测试视频帧"""
    return np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)


@pytest.mark.skip(reason="H.264 encoder requires full FFmpeg installation")
def test_encode_single_frame(encoder, sample_frame):
    """测试单帧编码"""
    result = encoder.encode_frame(sample_frame)

    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.skip(reason="H.264 encoder requires full FFmpeg installation")
def test_encode_batch_frames(encoder):
    """测试批量编码"""
    frames = [np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
              for _ in range(25)]  # 1 秒 @ 25fps

    result = encoder.encode_frames(frames)

    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.skip(reason="H.264 encoder requires full FFmpeg installation")
def test_cpu_fallback():
    """测试 CPU 编码"""
    encoder = H264Encoder(fps=25, bitrate="2M", force_cpu=True)

    frame = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    result = encoder.encode_frame(frame)

    assert len(result) > 0


def test_encoder_initialization():
    """测试编码器初始化"""
    encoder = H264Encoder(fps=25, bitrate="2M")
    assert encoder.fps == 25
    assert encoder.bitrate == "2M"
    assert encoder.codec in ["h264_nvenc", "libx264"]
