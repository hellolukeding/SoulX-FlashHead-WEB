"""
WebSocket 对话测试客户端

用于测试完整的对话流程
"""
import asyncio
import websockets
import json
import base64
import argparse
from pathlib import Path


async def test_text_message(ws_url: str, message: str):
    """测试文本消息"""
    print(f"\n{'='*60}")
    print(f"发送文本消息: {message}")
    print(f"{'='*60}\n")

    async with websockets.connect(ws_url) as websocket:
        # 1. 创建会话
        print("[1] 创建会话...")

        # 读取参考图像
        reference_image_path = Path(__file__).parent.parent.parent.parent / "assets" / "reference_image.png"

        if not reference_image_path.exists():
            print(f"⚠️  参考图像不存在: {reference_image_path}")
            print("使用默认测试图像...")

            # 创建一个简单的测试图像（1x1 红色像素 PNG）
            test_image_data = base64.b64encode(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0'
                b'\x00\x00\x00\x03\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            ).decode('utf-8')
        else:
            with open(reference_image_path, "rb") as f:
                test_image_data = base64.b64encode(f.read()).decode('utf-8')

        create_session_msg = {
            "type": "create_session",
            "data": {
                "model_type": "lite",
                "reference_image": test_image_data
            }
        }

        await websocket.send(json.dumps(create_session_msg))

        # 接收确认
        response = json.loads(await websocket.recv())
        print(f"✅ {response['type']}: {response.get('data', {})}")

        # 2. 发送文本消息
        print(f"\n[2] 发送文本消息...")

        text_message = {
            "type": "text_message",
            "data": {
                "text": message
            }
        }

        await websocket.send(json.dumps(text_message))

        # 3. 接收响应（多个消息）
        print(f"\n[3] 接收AI响应...")

        ai_text_chunks = []
        ai_audio_received = False
        video_received = False

        while True:
            try:
                # 设置超时，避免无限等待
                response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10.0))

                msg_type = response.get("type")
                data = response.get("data", {})

                if msg_type == "ai_text_chunk":
                    # 流式文本片段
                    chunk = data.get("text", "")
                    ai_text_chunks.append(chunk)
                    print(chunk, end="", flush=True)

                elif msg_type == "ai_text_complete":
                    # 完整文本
                    ai_text = data.get("text", "")
                    print(f"\n\n✅ 完整文本: {ai_text}")

                elif msg_type == "ai_audio":
                    # AI音频
                    ai_audio_received = True
                    audio_data = data.get("audio_data", "")
                    audio_format = data.get("format", "wav")
                    print(f"\n✅ 收到音频: {len(audio_data)} bytes ({audio_format})")

                elif msg_type == "audio_received":
                    # 音频接收确认
                    print(f"\n✅ 音频已接收: {data.get('status')}")

                elif msg_type == "error":
                    # 错误消息
                    print(f"\n❌ 错误: {data.get('message')}")

                elif msg_type == "pong":
                    # 心跳响应
                    pass

                # 如果收到了所有内容，退出循环
                if ai_text_chunks and ai_audio_received:
                    print(f"\n\n✅ 对话完成")
                    break

            except asyncio.TimeoutError:
                print(f"\n⏱️  接收超时")
                break
            except Exception as e:
                print(f"\n❌ 接收消息错误: {e}")
                break


async def test_audio_message(ws_url: str, audio_file: str):
    """测试音频消息（完整对话流程）"""
    print(f"\n{'='*60}")
    print(f"发送音频消息: {audio_file}")
    print(f"{'='*60}\n")

    async with websockets.connect(ws_url) as websocket:
        # 1. 创建会话
        print("[1] 创建会话...")

        reference_image_path = Path(__file__).parent.parent.parent.parent / "assets" / "reference_image.png"

        if not reference_image_path.exists():
            print(f"⚠️  参考图像不存在，使用默认测试图像...")
            test_image_data = base64.b64encode(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0'
                b'\x00\x00\x00\x03\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            ).decode('utf-8')
        else:
            with open(reference_image_path, "rb") as f:
                test_image_data = base64.b64encode(f.read()).decode('utf-8')

        create_session_msg = {
            "type": "create_session",
            "data": {
                "model_type": "lite",
                "reference_image": test_image_data
            }
        }

        await websocket.send(json.dumps(create_session_msg))

        response = json.loads(await websocket.recv())
        print(f"✅ {response['type']}: {response.get('data', {})}")

        # 2. 读取音频文件
        print(f"\n[2] 读取音频文件...")

        if not Path(audio_file).exists():
            print(f"❌ 音频文件不存在: {audio_file}")
            return

        with open(audio_file, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode('utf-8')

        print(f"✅ 音频大小: {len(audio_data)} bytes")

        # 3. 发送音频消息
        print(f"\n[3] 发送音频消息...")

        audio_message = {
            "type": "user_message",
            "data": {
                "audio_data": audio_data,
                "audio_format": "wav"
            }
        }

        await websocket.send(json.dumps(audio_message))

        # 4. 接收响应
        print(f"\n[4] 接收AI响应...")

        user_text = None
        ai_text_chunks = []
        ai_audio_received = False

        while True:
            try:
                response = json.loads(await asyncio.wait_for(websocket.recv(), timeout=30.0))

                msg_type = response.get("type")
                data = response.get("data", {})

                if msg_type == "user_text":
                    # 用户识别的文本
                    user_text = data.get("text", "")
                    print(f"\n👤 用户: {user_text}")

                elif msg_type == "ai_text_chunk":
                    # AI文本片段
                    chunk = data.get("text", "")
                    ai_text_chunks.append(chunk)
                    print(chunk, end="", flush=True)

                elif msg_type == "ai_text_complete":
                    # 完整文本
                    ai_text = data.get("text", "")
                    print(f"\n\n🤖 AI: {ai_text}")

                elif msg_type == "ai_audio":
                    # AI音频
                    ai_audio_received = True
                    audio_data = data.get("audio_data", "")
                    print(f"\n✅ 收到音频: {len(audio_data)} bytes")

                elif msg_type == "error":
                    print(f"\n❌ 错误: {data.get('message')}")

                # 检查是否完成
                if user_text and ai_text_chunks and ai_audio_received:
                    print(f"\n\n✅ 完整对话流程完成")
                    break

            except asyncio.TimeoutError:
                print(f"\n⏱️  接收超时")
                break
            except Exception as e:
                print(f"\n❌ 接收消息错误: {e}")
                break


async def main():
    parser = argparse.ArgumentParser(description="WebSocket 对话测试客户端")
    parser.add_argument("--url", default="ws://localhost:8000/ws?token=test", help="WebSocket URL")
    parser.add_argument("--mode", choices=["text", "audio"], default="text", help="测试模式")
    parser.add_argument("--message", default="你好，请介绍一下自己", help="文本消息内容")
    parser.add_argument("--audio", help="音频文件路径")

    args = parser.parse_args()

    if args.mode == "text":
        await test_text_message(args.url, args.message)
    elif args.mode == "audio":
        if not args.audio:
            print("❌ 音频模式需要指定 --audio 参数")
            return
        await test_audio_message(args.url, args.audio)


if __name__ == "__main__":
    asyncio.run(main())
