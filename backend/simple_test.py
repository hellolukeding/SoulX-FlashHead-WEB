"""
简单视频编码测试
"""
import sys
import os
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')
sys.path.insert(0, '/opt/digital-human-platform/backend')
os.chdir('/opt/soulx/SoulX-FlashHead')

import numpy as np
from app.core.streaming.h264_encoder import H264Encoder

print("测试 H.264 编码...")

# 1. 测试简单帧编码
print("\n1. 测试简单帧编码...")
test_frames = np.random.randint(0, 255, (10, 512, 512, 3), dtype=np.uint8)
print(f"   测试帧形状: {test_frames.shape}")
print(f"   测试帧类型: {test_frames.dtype}")

encoder = H264Encoder(force_cpu=True)

try:
    result = encoder.encode_frames(test_frames)
    print(f"   ✅ 编码成功: {len(result)} bytes")

    if len(result) > 0:
        print(f"   前16字节: {result[:16].hex()}")
except Exception as e:
    print(f"   ❌ 编码失败: {e}")
    import traceback
    traceback.print_exc()
