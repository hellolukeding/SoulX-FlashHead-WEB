#!/usr/bin/env python3
"""测试 SoulX-FlashHead 源码中的确切值"""
import sys
import os

os.chdir('/opt/digital-human-platform/backend')
sys.path.insert(0, '/opt/digital-human-platform/backend')
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')

import numpy as np
import torch
from loguru import logger

from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig

def test_exact_values():
    logger.info("=" * 60)
    logger.info("测试 SoulX-FlashHead 源码中的确切值")
    logger.info("=" * 60)

    # 创建引擎
    config = InferenceConfig(model_type="lite", use_face_crop=True)
    engine = FlashHeadInferenceEngine(config)

    # 加载模型
    if not engine.load_model("/opt/soulx/SoulX-FlashHead/examples/girl.png"):
        logger.error("❌ 模型加载失败")
        return False

    logger.success("✅ 模型加载成功")

    # 测试不同的 audio_length 值
    # 根据 video_length = audio_samples * 25 / 16000
    test_cases = [
        # (video_length, audio_samples, description)
        (81, 51840, "源码示例值 (81帧, 51840 samples)"),
        (161, 103040, "2倍左右"),
        (321, 206080, "接近当前失败的值"),
        (41, 26240, "小值测试"),
    ]

    for video_length, audio_samples, desc in test_cases:
        logger.info(f"\n测试: {desc}")
        logger.info(f"  video_length={video_length}, audio_samples={audio_samples}")

        # 检查约束
        constraint1 = (video_length - 1) % 4 == 0
        logger.info(f"  约束1: (video_length - 1) % 4 = {(video_length - 1) % 4} {'✅' if constraint1 else '❌'}")

        constraint2 = video_length % 36 == 0
        logger.info(f"  约束2: video_length % 36 = {video_length % 36} {'✅' if constraint2 else '❌'}")

        # 生成测试音频
        target_audio = np.random.randn(audio_samples).astype(np.float32) * 0.01

        try:
            video_frames = engine.process_audio(target_audio, 16000)
            if video_frames is not None:
                logger.success(f"  ✅ 视频生成成功: {video_frames.shape}")
            else:
                logger.error(f"  ❌ 视频生成失败")
        except Exception as e:
            logger.error(f"  ❌ 错误: {e}")

    return True

if __name__ == "__main__":
    import time
    start = time.time()
    test_exact_values()
    elapsed = time.time() - start
    logger.info(f"\n测试耗时: {elapsed:.2f}秒")
