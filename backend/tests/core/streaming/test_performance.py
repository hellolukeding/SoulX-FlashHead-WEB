import time
from app.core.streaming.performance import PerformanceMetrics, PerformanceTimer


def test_performance_metrics():
    """测试性能指标"""
    metrics = PerformanceMetrics()

    metrics.add_audio_decode_time(0.1)
    metrics.add_inference_time(0.5, 100.0)
    metrics.add_encode_time(0.2)
    metrics.add_latency(1.5)

    summary = metrics.to_dict()

    assert summary["audio_decode_avg_ms"] == 100.0
    assert summary["inference_avg_ms"] == 500.0
    assert summary["inference_avg_fps"] == 100.0


def test_performance_timer():
    """测试性能计时器"""
    metrics = PerformanceMetrics()

    with PerformanceTimer(metrics, "audio_decode"):
        time.sleep(0.01)

    assert len(metrics.audio_decode_time) == 1
    assert metrics.audio_decode_time[0] >= 0.01
