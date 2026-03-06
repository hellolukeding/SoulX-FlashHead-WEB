#!/usr/bin/env python3
"""直接测试 SoulX-FlashHead 视频生成"""
import sys
import os

os.chdir('/opt/digital-human-platform/backend')
sys.path.insert(0, '/opt/digital-human-platform/backend')
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')

import numpy as np
import torch
from loguru import logger

from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig

def test_generation():
    logger.info("=" * 60)
    logger.info("直接测试 SoulX-FlashHead")
    logger.info("=" * 60)

    # 创建引擎
    config = InferenceConfig(model_type="lite", use_face_crop=True)
    engine = FlashHeadInferenceEngine(config)

    # 加载模型
    if not engine.load_model("/opt/soulx/SoulX-FlashHead/examples/girl.png"):
        logger.error("❌ 模型加载失败")
        return False

    logger.success("✅ 模型加载成功")

    # 测试不同的音频长度
    # 根据分析，L=360 应该同时满足两个约束
    # audio = 360 * 16000 / 25 = 230400 samples
    target_audio = np.random.randn(230400).astype(np.float32) * 0.01

    logger.info(f"测试音频: {len(target_audio)} samples ({len(target_audio)/16000:.2f}秒)")
    logger.info(f"预期 video_length: {len(target_audio) * 25 / 16000}")

    try:
        video_frames = engine.process_audio(target_audio, 16000)
        if video_frames is not None:
            logger.success(f"✅ 视频生成成功: {video_frames.shape}")
            return True
        else:
            logger.error("❌ 视频生成失败")
            return False
    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    start = time.time()
    success = test_generation()
    elapsed = time.time() - start

    logger.info(f"测试耗时: {elapsed:.2f}秒")
    logger.success("✅ 测试完成" if success else "❌ 测试失败")
