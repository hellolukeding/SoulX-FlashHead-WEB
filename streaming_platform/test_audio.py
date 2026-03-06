"""
测试 CosyVoice 流式 TTS
"""
import asyncio
import sys

sys.path.insert(0, '/opt/digital-human-platform/streaming_platform')

from audio_engine.tts_streamer import MockTTSStreamer, CosyVoiceStreamer


async def test_mock_tts():
    """测试模拟 TTS"""
    print("\n" + "="*50)
    print("测试 Mock TTS 流式输出")
    print("="*50 + "\n")

    streamer = MockTTSStreamer(
        sample_rate=16000,
        chunk_size_ms=150,
    )

    text = "你好，我是数字人助手"

    chunk_count = 0
    total_samples = 0

    async for chunk in streamer.generate_audio_stream(text):
        chunk_count += 1
        total_samples += len(chunk)

        print(f"收到切片 #{chunk_count}:")
        print(f"  Shape: {chunk.shape}")
        print(f"  Dtype: {chunk.dtype}")
        print(f"  Range: [{chunk.min():.3f}, {chunk.max():.3f}]")
        print(f"  Duration: {len(chunk)/16000*1000:.0f}ms")
        print()

    duration = total_samples / 16000
    print(f"✅ 测试完成:")
    print(f"   总切片数: {chunk_count}")
    print(f"   总时长: {duration:.2f}s")
    print(f"   文本: '{text}'")


async def test_cosyvoice_tts():
    """测试 CosyVoice TTS"""
    print("\n" + "="*50)
    print("测试 CosyVoice 流式输出")
    print("="*50 + "\n")

    streamer = CosyVoiceStreamer(
        sample_rate=16000,
        chunk_size_ms=150,
    )

    text = "你好，我是数字人助手"

    chunk_count = 0
    total_samples = 0

    async for chunk in streamer.generate_audio_stream(text):
        chunk_count += 1
        total_samples += len(chunk)

        print(f"收到切片 #{chunk_count}:")
        print(f"  Shape: {chunk.shape}")
        print(f"  Dtype: {chunk.dtype}")
        print(f"  Range: [{chunk.min():.3f}, {chunk.max():.3f}]")
        print(f"  Duration: {len(chunk)/16000*1000:.0f}ms")
        print()

    duration = total_samples / 16000
    print(f"✅ 测试完成:")
    print(f"   总切片数: {chunk_count}")
    print(f"   总时长: {duration:.2f}s")


async def main():
    """主测试函数"""
    await test_mock_tts()

    # 测试 CosyVoice（可选）
    # await test_cosyvoice_tts()


if __name__ == "__main__":
    asyncio.run(main())
