#!/usr/bin/env python3
"""
测试视频生成流程
"""
import sys
import os
import numpy as np

# 添加路径
sys.path.insert(0, '/opt/digital-human-platform/backend')
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')

os.chdir('/opt/digital-human-platform/backend')

from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig
from loguru import logger

def test_video_generation():
    """测试视频生成"""
    logger.info("=" * 60)
    logger.info("开始测试 SoulX-FlashHead 视频生成")
    logger.info("=" * 60)

    # 1. 创建推理引擎
    config = InferenceConfig(
        model_type="lite",
        use_face_crop=True
    )
    engine = FlashHeadInferenceEngine(config)

    # 2. 加载模型
    reference_image = "/opt/soulx/SoulX-FlashHead/examples/girl.png"
    if not engine.load_model(reference_image):
        logger.error("❌ 模型加载失败")
        return False
    logger.success("✅ 模型加载成功")

    # 3. 生成测试音频（3秒）
    logger.info("生成测试音频...")
    test_audio = np.random.randn(16000 * 3).astype(np.float32) * 0.1
    logger.info(f"音频长度: {len(test_audio)} samples ({len(test_audio)/16000:.2f}秒)")

    # 4. 生成视频
    logger.info("开始生成视频...")
    video_frames = engine.process_audio(test_audio, 16000)

    if video_frames is not None:
        logger.success(f"✅ 视频生成成功: {video_frames.shape}")
        logger.info(f"   - 帧数: {video_frames.shape[0]}")
        logger.info(f"   - 分辨率: {video_frames.shape[2]}x{video_frames.shape[3]}")
        return True
    else:
        logger.error("❌ 视频生成失败")
        return False

if __name__ == "__main__":
    try:
        success = test_video_generation()
        if success:
            logger.success("✅ 测试通过")
            sys.exit(0)
        else:
            logger.error("❌ 测试失败")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
