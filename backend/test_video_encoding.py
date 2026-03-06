"""
测试视频编码
"""
import sys
import os
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')
sys.path.insert(0, '/opt/digital-human-platform/backend')
os.chdir('/opt/soulx/SoulX-FlashHead')

import numpy as np
import torch
from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig
from app.core.streaming.h264_encoder import H264Encoder

print("测试视频编码...")

# 1. 生成测试视频帧
print("\n1. 生成测试视频帧...")
test_frames = np.random.randint(0, 255, (10, 512, 512, 3), dtype=np.uint8)
print(f"   测试帧形状: {test_frames.shape}")
print(f"   测试帧类型: {test_frames.dtype}")

# 2. 测试编码器
print("\n2. 测试 H264Encoder...")
encoder = H264Encoder(force_cpu=True)

# 3. 尝试编码
print("\n3. 尝试编码...")
try:
    result = encoder.encode_frames(test_frames)
    print(f"   ✅ 编码成功: {len(result)} bytes")
except Exception as e:
    print(f"   ❌ 编码失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试单个帧
print("\n4. 测试单个帧编码...")
try:
    single_frame = test_frames[0]
    print(f"   单帧形状: {single_frame.shape}")
    result = encoder.encode_frame(single_frame)
    print(f"   ✅ 单帧编码成功: {len(result)} bytes")
except Exception as e:
    print(f"   ❌ 单帧编码失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试实际 SoulX-FlashHead 生成的帧
print("\n5. 测试 SoulX-FlashHead 生成的帧...")
try:
    import asyncio

    async def test_soulx():
        config = InferenceConfig(model_type="lite", use_face_crop=True)
        engine = FlashHeadInferenceEngine(config)

        default_image = "/opt/soulx/SoulX-FlashHead/examples/girl.png"
        if not engine.load_model(default_image):
            print("   ❌ 模型加载失败")
            return

        print("   ✅ 模型加载成功")

        # 生成测试音频（1秒静音）
        test_audio = np.zeros(16000, dtype=np.float32)

        # 生成视频
        print("   ⏳ 生成视频中...")
        video_frames = engine.process_audio(test_audio, 16000)

        if video_frames is not None:
            print(f"   ✅ 视频生成成功: {video_frames.shape}")
            print(f"   视频帧类型: {video_frames.dtype}")

            # 转换为 numpy
            frames_np = video_frames.cpu().numpy()

            print(f"   转换前形状: {frames_np.shape}")
            print(f"   转换前类型: {frames_np.dtype}")
            print(f"   转换前值范围: [{frames_np.min()}, {frames_np.max()}]")

            # 尝试不同的转换方式
            print("\n   方式1: transpose(0, 2, 3, 1)")
            frames1 = frames_np.transpose(0, 2, 3, 1)
            print(f"   转换后形状: {frames1.shape}")
            frames1 = (frames1 * 255).astype(np.uint8)
            print(f"   缩放后类型: {frames1.dtype}")
            print(f"   缩放后值范围: [{frames1.min()}, {frames1.max()}]")

            # 编码
            encoder2 = H264Encoder(force_cpu=True)
            result = encoder2.encode_frames(frames1)
            print(f"   ✅ 编码成功: {len(result)} bytes")

            engine.unload()
        else:
            print("   ❌ 视频生成失败")

    asyncio.run(test_soulx())

except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
