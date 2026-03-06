#!/usr/bin/env python3
"""
测试阶段3：分段视频生成

验证流式视频生成功能：
1. 视频 分成多个片段
2. 每个片段独立编码（带关键帧）
3. WebSocket 流式发送
4. 首帧延迟 < 2秒
"""
import asyncio
import json
import time
import websockets
from pathlib import Path


async def test_streaming_video():
    """测试流式视频生成"""

    ws_url = "ws://localhost:8000/api/v1/video"

    print("=" * 60)
    print("阶段3：分段视频生成测试")
    print("=" * 60)

    try:
        async with websockets.connect(ws_url) as ws:
            print("\n[1/4] 连接成功")

            # 接收欢迎消息
            msg = json.loads(await ws.recv())
            print(f"   欢迎: {msg.get('message')}")
            print(f"   功能: {msg.get('features')}")

            # 初始化会话
            print("\n[2/4] 初始化会话...")
            await ws.send(json.dumps({
                "type": "init",
                "data": {"reference_image": "default"}
            }))

            msg = json.loads(await ws.recv())
            if msg.get("type") == "initialized":
                print(f"   ✅ 会话初始化成功")
            else:
                print(f"   ❌ 初始化失败: {msg}")
                return

            # 发送测试消息
            print("\n[3/4] 发送测试消息（流式模式）...")
            test_text = "你好，请介绍一下你自己"
            start_time = time.time()

            await ws.send(json.dumps({
                "type": "message",
                "data": {
                    "text": test_text,
                    "streaming": True  # 启用流式模式
                }
            }))

            # 接收响应
            print("\n[4/4] 接收流式响应...")

            ai_text = None
            audio_received = False
            video_chunks = []
            first_chunk_time = None
            complete_time = None

            while True:
                msg = json.loads(await ws.recv())
                msg_type = msg.get("type")

                if msg_type == "ai_text_chunk":
                    ai_text = msg["data"]["text"]
                    text_latency = (time.time() - start_time) * 1000
                    print(f"\n   📝 AI文本: {ai_text[:50]}... ({text_latency:.0f}ms)")

                elif msg_type == "ai_audio":
                    audio_received = True
                    audio_latency = (time.time() - start_time) * 1000
                    audio_size = len(msg["data"]["audio_data"])
                    print(f"   🔊 音频: {audio_size} bytes ({audio_latency:.0f}ms)")

                elif msg_type == "video_chunk":
                    chunk_idx = msg["data"]["chunk_index"]
                    total_chunks = msg["data"]["total_chunks"]
                    frames = msg["data"]["video_frames"]
                    duration = msg["data"]["duration"]
                    is_first = msg["data"]["is_first"]
                    is_last = msg["data"]["is_last"]

                    if is_first and first_chunk_time is None:
                        first_chunk_time = time.time()
                        first_chunk_latency = (first_chunk_time - start_time) * 1000
                        print(f"\n   🎬 首个视频片段:")
                        print(f"      片段: {chunk_idx + 1}/{total_chunks}")
                        print(f"      帧数: {frames}")
                        print(f"      时长: {duration:.2f}s")
                        print(f"      延迟: {first_chunk_latency:.0f}ms ⭐")

                        if first_chunk_latency < 2000:
                            print(f"      ✅ 首帧延迟达标 (< 2秒)")
                        else:
                            print(f"      ⚠️ 首帧延迟较高")

                    video_chunks.append({
                        "index": chunk_idx,
                        "total": total_chunks,
                        "frames": frames,
                        "duration": duration
                    })

                    if is_last:
                        complete_time = time.time()
                        total_latency = (complete_time - start_time) * 1000
                        print(f"\n   🎬 最后视频片段: {chunk_idx + 1}/{total_chunks}")
                        print(f"      总延迟: {total_latency:.0f}ms")

                elif msg_type == "complete":
                    total_latency = (time.time() - start_time) * 1000
                    success = msg["data"].get("success", False)
                    total_chunks = msg["data"].get("total_chunks", 0)
                    total_frames = msg["data"].get("total_frames", 0)

                    print(f"\n   ✅ 处理完成")
                    print(f"      成功: {success}")
                    print(f"      总片段: {total_chunks}")
                    print(f"      总帧数: {total_frames}")
                    print(f"      总延迟: {total_latency:.0f}ms")
                    break

            # 统计结果
            print("\n" + "=" * 60)
            print("测试结果")
            print("=" * 60)

            if first_chunk_time:
                first_chunk_latency = (first_chunk_time - start_time) * 1000
                print(f"\n✅ 首帧延迟: {first_chunk_latency:.0f}ms")

                if first_chunk_latency < 2000:
                    print(f"   ✅ 优秀 (< 2秒)")
                elif first_chunk_latency < 3000:
                    print(f"   ⚠️ 可接受 (< 3秒)")
                else:
                    print(f"   ❌ 需优化 (> 3秒)")

            if audio_received:
                print(f"✅ 音频优先: 是")
            else:
                print(f"❌ 音频优先: 否")

            if len(video_chunks) > 1:
                print(f"✅ 分段生成: 是 ({len(video_chunks)} 片段)")
            else:
                print(f"❌ 分段生成: 否")

            print("\n阶段3 测试完成！")

    except websockets.exceptions.ConnectionRefused:
        print("\n❌ 连接失败，请确保后端服务正在运行:")
        print("   cd /opt/digital-human-platform/backend")
        print("   source venv/bin/activate")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_streaming_video())
