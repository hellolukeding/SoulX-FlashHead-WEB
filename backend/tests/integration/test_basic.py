"""基础集成测试"""
import pytest
from fastapi.testclient import TestClient

# 简单的测试，不需要完整模型
def test_basic_imports():
    """测试基本导入"""
    import torch
    from app.core.streaming.audio_decoder import AudioDecoder
    from app.core.streaming.image_decoder import ImageDecoder
    from app.core.streaming.audio_buffer import AudioBuffer
    from app.core.streaming.gpu_manager import GPUMemoryManager
    from app.core.streaming.performance import PerformanceMetrics
    
    assert torch is not None
    assert AudioDecoder is not None
    assert ImageDecoder is not None
    assert AudioBuffer is not None
    assert GPUMemoryManager is not None
    assert PerformanceMetrics is not None


def test_gpu_available():
    """测试 GPU 可用性"""
    import torch
    
    cuda_available = torch.cuda.is_available()
    print(f"\n✅ CUDA Available: {cuda_available}")
    
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"   GPU: {gpu_name}")
        print(f"   Memory: {gpu_memory:.1f} GB")
        print(f"   CUDA Version: {torch.version.cuda}")


def test_streaming_config():
    """测试流式处理配置"""
    from app.core.streaming import StreamConfig
    
    config = StreamConfig()
    
    assert config.audio_sample_rate == 16000
    assert config.video_fps == 25
    assert config.max_concurrent_sessions == 5
    assert config.audio_window_size == 1.0
    
    print(f"\n✅ 流式处理配置加载成功")
    print(f"   音频采样率: {config.audio_sample_rate} Hz")
    print(f"   视频帧率: {config.video_fps} FPS")
    print(f"   最大并发: {config.max_concurrent_sessions}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
