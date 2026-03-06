#!/usr/bin/env python3
"""快速验证视频流功能"""
import asyncio
import json
import websockets
import base64

async def test():
    uri = "ws://192.168.1.132:8000/api/v1/video"
    print(f"连接到 {uri}...")

    try:
        async with websockets.connect(uri) as ws:
            print("✅ 连接成功")

            # 初始化
            await ws.send(json.dumps({"type": "init", "data": {"reference_image": "default"}}))
            resp = await ws.recv()
            data = json.loads(resp)
            print(f"初始化: {data.get('type')}")

            # 发送消息
            await ws.send(json.dumps({"type": "message", "data": {"text": "你好"}}))
            print("消息已发送，等待响应...")

            audio_ok = False
            video_ok = False

            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=120)
                    data = json.loads(msg)
                    msg_type = data.get("type")

                    if msg_type == "ai_audio":
                        audio_ok = True
                        print(f"✅ 音频接收: {len(data.get('data', {}).get('audio_data', ''))} bytes")

                    elif msg_type == "video_frame":
                        video_ok = True
                        frames = data.get('data', {}).get('video_frames', 0)
                        video_size = len(data.get('data', {}).get('video_data', ''))
                        print(f"✅ 视频接收: {frames} 帧, {video_size} bytes")

                    elif msg_type == "complete":
                        print(f"\n{'='*50}")
                        print(f"音频: {'✅' if audio_ok else '❌'}")
                        print(f"视频: {'✅' if video_ok else '❌'}")
                        print(f"{'='*50}")
                        break

                except asyncio.TimeoutError:
                    print("超时")
                    break

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test())
