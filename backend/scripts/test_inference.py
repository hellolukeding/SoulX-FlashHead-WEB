#!/usr/bin/env python3
"""
测试 SoulX-FlashHead 推理引擎
"""
import sys
sys.path.insert(0, '.')

from loguru import logger
from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig


def test_inference_engine():
    """测试推理引擎"""
    logger.add("../logs/test.log", rotation="10 MB")

    logger.info("=== 测试 SoulX-FlashHead 推理引擎 ===")

    # 创建配置
    config = InferenceConfig(
        model_type="lite",
        use_face_crop=True
    )

    # 创建引擎
    engine = FlashHeadInferenceEngine(config)

    # 加载模型
    reference_image = "/opt/soulx/SoulX-FlashHead/examples/girl.png"
    logger.info(f"参考图像: {reference_image}")

    if not engine.load_model(reference_image):
        logger.error("❌ 模型加载失败")
        return False

    logger.success("✅ 模型加载成功")

    # 获取性能指标
    metrics = engine.get_performance_metrics()
    logger.info(f"📊 性能指标: {metrics}")

    # 测试推理
    audio_path = "/opt/soulx/SoulX-FlashHead/examples/podcast_sichuan_16k.wav"
    logger.info(f"测试音频: {audio_path}")

    video_frames = engine.process_audio_file(audio_path)

    if video_frames is not None:
        logger.success(f"✅ 视频生成成功: {video_frames.shape}")

        # 保存第一帧作为测试
        import torch
        import numpy as np
        from PIL import Image

        # 转换第一帧为图像
        frame = video_frames[0].cpu().numpy().transpose(1, 2, 0)
        frame = (frame * 255).astype(np.uint8)
        img = Image.fromarray(frame)
        img.save("../logs/test_frame.png")
        logger.success("✅ 测试帧已保存: logs/test_frame.png")
    else:
        logger.error("❌ 视频生成失败")
        return False

    # 清理
    engine.unload()

    logger.success("✅ 测试完成")
    return True


if __name__ == "__main__":
    success = test_inference_engine()
    sys.exit(0 if success else 1)
