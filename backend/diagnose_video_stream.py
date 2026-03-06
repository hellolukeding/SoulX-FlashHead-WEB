"""
诊断视频流问题
"""
import sys
import os

# 添加路径
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')
sys.path.insert(0, '/opt/digital-human-platform/backend')

# 切换到 SoulX 目录
os.chdir('/opt/soulx/SoulX-FlashHead')

print("=" * 60)
print("视频流诊断工具")
print("=" * 60)

# 1. 检查参考图像
print("\n1. 检查参考图像...")
default_image = "/opt/soulx/SoulX-FlashHead/examples/girl.png"
if os.path.exists(default_image):
    size = os.path.getsize(default_image)
    print(f"   ✅ 默认参考图像存在: {default_image} ({size} bytes)")
else:
    print(f"   ❌ 默认参考图像不存在: {default_image}")
    sys.exit(1)

# 2. 检查模型目录
print("\n2. 检查模型目录...")
model_dir = "/opt/digital-human-platform/models/SoulX-FlashHead-1_3B"
if os.path.exists(model_dir):
    files = os.listdir(model_dir)
    print(f"   ✅ 模型目录存在: {model_dir}")
    print(f"   包含文件: {len(files)} 个")
else:
    print(f"   ❌ 模型目录不存在: {model_dir}")
    sys.exit(1)

# 3. 检查 wav2vec 模型
print("\n3. 检查 wav2vec 模型...")
wav2vec_dir = "/opt/digital-human-platform/models/wav2vec2-base-960h"
if os.path.exists(wav2vec_dir):
    files = os.listdir(wav2vec_dir)
    print(f"   ✅ wav2vec 模型存在: {wav2vec_dir}")
    print(f"   包含文件: {len(files)} 个")
else:
    print(f"   ❌ wav2vec 模型不存在: {wav2vec_dir}")

# 4. 测试 FlashHeadEngine 导入
print("\n4. 测试 FlashHeadEngine 导入...")
try:
    from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig
    print("   ✅ FlashHeadEngine 导入成功")
except Exception as e:
    print(f"   ❌ FlashHeadEngine 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 测试 H264Encoder 导入
print("\n5. 测试 H264Encoder 导入...")
try:
    from app.core.streaming.h264_encoder import H264Encoder
    print("   ✅ H264Encoder 导入成功")
except Exception as e:
    print(f"   ❌ H264Encoder 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. 测试 ImageDecoder 导入
print("\n6. 测试 ImageDecoder 导入...")
try:
    from app.core.streaming.image_decoder import ImageDecoder
    print("   ✅ ImageDecoder 导入成功")
except Exception as e:
    print(f"   ❌ ImageDecoder 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 7. 测试 LLM 客户端
print("\n7. 测试 LLM 客户端...")
try:
    from app.services.llm.client import get_llm_client
    llm = get_llm_client()
    print("   ✅ LLM 客户端初始化成功")
except Exception as e:
    print(f"   ❌ LLM 客户端初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 8. 测试 TTS
print("\n8. 测试 TTS...")
try:
    from app.services.tts.factory import get_tts
    tts = get_tts()
    print(f"   ✅ TTS 初始化成功: {type(tts).__name__}")
except Exception as e:
    print(f"   ❌ TTS 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 9. 测试完整的视频生成流程（简化版）
print("\n9. 测试视频生成流程...")
print("   ⏳ 正在初始化 FlashHeadInferenceEngine...")
try:
    import asyncio

    async def test_video_generation():
        # 创建配置
        config = InferenceConfig(
            model_type="lite",
            use_face_crop=True
        )

        # 创建引擎
        engine = FlashHeadInferenceEngine(config)

        # 加载模型
        print("   ⏳ 正在加载 SoulX-FlashHead 模型（可能需要 10-30 秒）...")
        if not engine.load_model(default_image):
            print("   ❌ 模型加载失败")
            return False

        print("   ✅ 模型加载成功")

        # 创建测试音频（1秒静音）
        import numpy as np
        test_audio = np.zeros(16000, dtype=np.float32)

        # 生成视频
        print("   ⏳ 正在生成测试视频...")
        video_frames = engine.process_audio(test_audio, 16000)

        if video_frames is not None:
            print(f"   ✅ 视频生成成功: {video_frames.shape}")

            # 测试 H.264 编码
            print("   ⏳ 正在编码为 H.264...")
            encoder = H264Encoder()
            import torch
            frames_np = video_frames.cpu().numpy().transpose(0, 2, 3, 1)
            frames_np = (frames_np * 255).astype(np.uint8)
            h264_data = encoder.encode_frames(frames_np)

            print(f"   ✅ H.264 编码成功: {len(h264_data)} bytes")

            # 清理
            engine.unload()
            encoder.close()

            return True
        else:
            print("   ❌ 视频生成失败")
            engine.unload()
            return False

    # 运行测试
    result = asyncio.run(test_video_generation())

    if result:
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！视频流功能正常")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 视频生成测试失败")
        print("=" * 60)
        sys.exit(1)

except Exception as e:
    print(f"   ❌ 视频生成测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
