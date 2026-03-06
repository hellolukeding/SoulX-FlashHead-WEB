"""
WebSocket 视频流端点
通过 WebSocket 发送 SoulX-FlashHead 生成的视频帧到前端
"""
import asyncio
import json
import base64
import io
import time
import numpy as np
from fastapi import APIRouter, WebSocket
from loguru import logger
from typing import Optional

from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig
from app.core.streaming.h264_encoder import H264Encoder
from app.services.llm.client import get_llm_client
from app.services.tts.factory import get_tts
from app.core.streaming.image_decoder import ImageDecoder
import soundfile as sf


router = APIRouter()

# 全局会话管理
_sessions = {}


class VideoStreamSession:
    """视频流会话"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.engine: Optional[FlashHeadInferenceEngine] = None
        self.encoder: Optional[H264Encoder] = None
        self.created_at = time.time()
        self.message_count = 0

    async def initialize(self, reference_image_b64: str) -> bool:
        """初始化会话，加载模型"""
        try:
            # 解码参考图像
            image_decoder = ImageDecoder()
            reference_image_path = image_decoder.decode_and_save(reference_image_b64)

            # 创建推理引擎
            config = InferenceConfig(
                model_type="lite",
                use_face_crop=True
            )

            self.engine = FlashHeadInferenceEngine(config)

            # 加载模型
            if not self.engine.load_model(reference_image_path):
                logger.error(f"[{self.session_id}] 模型加载失败")
                return False

            # 创建 H.264 编码器
            self.encoder = H264Encoder(force_cpu=True)

            logger.success(f"[{self.session_id}] ✅ 会话初始化成功")
            return True

        except Exception as e:
            logger.error(f"[{self.session_id}] 初始化失败: {e}")
            return False

    async def process_text_message(self, text: str) -> dict:
        """处理文本消息，生成视频"""
        try:
            self.message_count += 1
            logger.info(f"[{self.session_id}] 处理消息 #{self.message_count}: {text}")

            # 1. LLM 生成
            logger.info(f"[{self.session_id}] LLM 生成中...")
            llm = get_llm_client()

            ai_text_chunks = []
            try:
                async for chunk in llm.chat_stream(text):
                    ai_text_chunks.append(chunk)
                ai_text = "".join(ai_text_chunks)
            except Exception as e:
                logger.warning(f"[{self.session_id}] LLM 生成失败，使用测试响应: {e}")
                # 测试响应
                ai_text = f"你好！收到你的消息：「{text}」。我是一个数字人助手，很高兴为你服务。目前我正在测试模式，会使用预设回复。"
            
            logger.info(f"[{self.session_id}] AI: {ai_text}")

            # 2. TTS 合成
            logger.info(f"[{self.session_id}] TTS 合成中...")
            tts = get_tts()
            ai_audio = await tts.synthesize(ai_text)

            # 编码音频为 Base64
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, ai_audio, 16000, format='WAV')
            audio_buffer.seek(0)
            audio_b64 = base64.b64encode(audio_buffer.read()).decode('utf-8')

            # 3. 视频生成
            logger.info(f"[{self.session_id}] 生成视频中...")

            if len(ai_audio) / 16000 > 0:
                video_frames = self.engine.process_audio(ai_audio, 16000)

                if video_frames is not None:
                    # 转换 tensor 为 numpy
                    import torch
                    frames_np = video_frames.cpu().numpy()  # [F, H, W, C]
                    frames_np = (frames_np * 255).astype(np.uint8)

                    # 编码为 H.264
                    h264_data = self.encoder.encode_frames(frames_np)

                    logger.success(f"[{self.session_id}] ✅ 生成 {len(frames_np)} 帧视频")

                    return {
                        "ai_text": ai_text,
                        "audio_data": audio_b64,
                        "audio_format": "wav",
                        "sample_rate": 16000,
                        "video_frames": len(frames_np),
                        "video_data": base64.b64encode(h264_data).decode('utf-8'),
                        "success": True
                    }
                else:
                    logger.error(f"[{self.session_id}] 视频生成失败")
                    return {
                        "ai_text": ai_text,
                        "audio_data": audio_b64,
                        "error": "视频生成失败",
                        "success": False
                    }
            else:
                logger.warning(f"[{self.session_id}] TTS 音频为空")
                # 即使没有音频，也返回文本和空音频
                return {
                    "ai_text": ai_text if ai_text else "(AI 文本为空)",
                    "audio_data": None,
                    "audio_format": "wav",
                    "sample_rate": 16000,
                    "video_frames": 0,
                    "video_data": None,
                    "success": True  # 标记为成功，即使没有音频
                }

        except Exception as e:
            logger.error(f"[{self.session_id}] 处理消息失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "success": False
            }

    def cleanup(self):
        """清理资源"""
        if self.engine:
            self.engine.unload()
        if self.encoder:
            self.encoder.close()


@router.websocket("/video")
async def video_stream_endpoint(websocket: WebSocket):
    """
    WebSocket 视频流端点

    接收文本消息，返回 LLM + TTS + SoulX-FlashHead 视频

    消息格式:
    {
        "type": "init" | "message",
        "data": {
            "reference_image": "<base64>"  // 仅 init 时需要
            "text": "<user text>"          // 仅 message 时需要
        }
    }
    """
    await websocket.accept()

    # 生成会话 ID
    import uuid
    session_id = str(uuid.uuid4())
    session = VideoStreamSession(session_id)
    _sessions[session_id] = session

    logger.info(f"[{session_id}] 🎬 视频流连接建立")

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "视频流已连接，请先发送 init 消息初始化"
        })

        # 消息循环
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get("type")
            message_data = data.get("data", {})

            logger.debug(f"[{session_id}] 收到消息: {message_type}")

            if message_type == "init":
                # 初始化会话
                reference_image = message_data.get("reference_image")

                if not reference_image:
                    await websocket.send_json({
                        "type": "error",
                        "message": "缺少 reference_image"
                    })
                    continue

                # 使用默认参考图像（如果没有提供）
                if reference_image == "default":
                    # 读取默认参考图像
                    default_image_path = "/opt/soulx/SoulX-FlashHead/examples/girl.png"
                    if os.path.exists(default_image_path):
                        with open(default_image_path, "rb") as f:
                            reference_image = base64.b64encode(f.read()).decode('utf-8')
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"默认参考图像不存在: {default_image_path}"
                        })
                        continue

                # 初始化
                success = await session.initialize(reference_image)

                if success:
                    await websocket.send_json({
                        "type": "initialized",
                        "session_id": session_id,
                        "message": "会话初始化成功，可以发送消息了"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "会话初始化失败"
                    })

            elif message_type == "message":
                # 处理文本消息
                if not session.engine:
                    await websocket.send_json({
                        "type": "error",
                        "message": "会话未初始化，请先发送 init 消息"
                    })
                    continue

                text = message_data.get("text", "")
                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "缺少 text 字段"
                    })
                    continue

                # 处理消息
                result = await session.process_text_message(text)

                # 发送 AI 文本（流式）
                await websocket.send_json({
                    "type": "ai_text_chunk",
                    "data": {
                        "text": result.get("ai_text", "")
                    }
                })

                # 发送音频
                if "audio_data" in result and result.get("success"):
                    await websocket.send_json({
                        "type": "ai_audio",
                        "data": {
                            "audio_data": result["audio_data"],
                            "audio_format": result.get("audio_format", "wav"),
                            "sample_rate": result.get("sample_rate", 16000)
                        }
                    })

                # 发送视频
                if "video_data" in result:
                    logger.info(f"[{self.session_id}] 发送视频帧: {result['video_frames']} 帧, {len(result['video_data'])} bytes")
                    await websocket.send_json({
                        "type": "video_frame",
                        "data": {
                            "frame_number": session.message_count,
                            "video_data": result["video_data"],
                            "video_frames": result["video_frames"]
                        }
                    })
                    logger.info(f"[{self.session_id}] ✅ 视频帧已发送")

                # 发送完成标记
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "success": result.get("success", False),
                        "message": "消息处理完成"
                    }
                })

            elif message_type == "ping":
                # 心跳
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": time.time()
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"未知消息类型: {message_type}"
                })

    except Exception as e:
        logger.error(f"[{session_id}] 错误: {e}")
        import traceback
        traceback.print_exc()

        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass

    finally:
        # 清理会话
        session.cleanup()
        if session_id in _sessions:
            del _sessions[session_id]

        logger.info(f"[{session_id}] 🔌 连接关闭")


# 需要导入 os
import os
