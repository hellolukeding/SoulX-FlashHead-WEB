#!/usr/bin/env python3
"""
WebSocket 测试客户端 - 用于调试视频生成流程
"""
import asyncio
import json
import websockets
from loguru import logger

async def test_video_stream():
    """测试视频流"""
    uri = "ws://192.168.1.132:8000/api/v1/video"

    try:
        logger.info(f"连接到 {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.success("✅ 连接成功")

            # 1. 发送初始化消息
            init_msg = {
                "type": "init",
                "data": {
                    "reference_image": "default"
                }
            }
            logger.info(f"发送初始化消息...")
            await websocket.send(json.dumps(init_msg))

            # 2. 接收响应
            logger.info("等待响应...")

            message_count = 0
            audio_received = False
            video_received = False

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=120)
                    message_count += 1
                    data = json.loads(message)
                    msg_type = data.get("type")

                    logger.info(f"[消息 {message_count}] {msg_type}")

                    if msg_type == "connected":
                        logger.info(f"  Session ID: {data.get('session_id')}")

                    elif msg_type == "initialized":
                        logger.success(f"  ✅ 会话初始化成功")

                        # 发送测试消息
                        test_msg = {
                            "type": "message",
                            "data": {
                                "text": "你好，请介绍一下自己"
                            }
                        }
                        logger.info(f"发送测试消息...")
                        await websocket.send(json.dumps(test_msg))

                    elif msg_type == "status":
                        logger.info(f"  状态: {data.get('data', {}).get('message')}")

                    elif msg_type == "ai_audio":
                        audio_received = True
                        audio_size = len(data.get('data', {}).get('audio_data', ''))
                        logger.success(f"  ✅ 音频接收成功: {audio_size} bytes")

                    elif msg_type == "video_frame":
                        video_received = True
                        frames = data.get('data', {}).get('video_frames', 0)
                        video_size = len(data.get('data', {}).get('video_data', ''))
                        logger.success(f"  ✅ 视频接收成功: {frames} 帧, {video_size} bytes")

                    elif msg_type == "complete":
                        success = data.get('data', {}).get('success', False)
                        if success:
                            logger.success(f"  ✅ 处理完成")
                        else:
                            logger.error(f"  ❌ 处理失败")

                        # 总结
                        logger.info("=" * 60)
                        logger.info("测试结果:")
                        logger.info(f"  音频: {'✅ 接收' if audio_received else '❌ 未接收'}")
                        logger.info(f"  视频: {'✅ 接收' if video_received else '❌ 未接收'}")
                        logger.info("=" * 60)

                        # 如果测试完成，退出
                        break

                    elif msg_type == "error":
                        logger.error(f"  ❌ 错误: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    logger.warning("⚠️  30秒内没有收到新消息，可能处理完成")
                    break
                except Exception as e:
                    logger.error(f"❌ 处理消息错误: {e}")
                    break

    except websockets.exceptions.WebSocketException as e:
        logger.error(f"❌ WebSocket 连接错误: {e}")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_video_stream())
