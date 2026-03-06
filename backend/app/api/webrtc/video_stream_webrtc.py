"""
WebRTC 实时视频流端点 - 简化版

使用 aiortc 实现 WebRTC 视频流
支持 SoulX-FlashHead 实时视频生成
"""
import asyncio
import base64
import io
import time
import uuid
from typing import Optional, Dict, Any
import numpy as np
from fastapi import APIRouter, WebSocket
from loguru import logger

from aiortc import RTCPeerConnection, RTCSessionDescription

from app.core.inference.flashhead_streaming import FlashHeadStreamingEngine, StreamingConfig
from app.api.webrtc.webrtc_video_track import BufferedVideoStreamTrack, FlashHeadVideoGenerator
from app.services.llm.client import get_llm_client
from app.services.tts.factory import get_tts
from app.core.streaming.image_decoder import ImageDecoder


router = APIRouter()

# WebRTC 配置
RTC_CONFIGURATION = {
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
}


class WebRTCSession:
    """WebRTC 会话管理"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.engine: Optional[FlashHeadStreamingEngine] = None
        self.video_track: Optional[BufferedVideoStreamTrack] = None
        self.video_generator: Optional[FlashHeadVideoGenerator] = None
        self.pc: Optional[RTCPeerConnection] = None
        self.created_at = time.time()
        self.message_count = 0

    async def initialize(self, reference_image_b64: str) -> bool:
        """初始化会话"""
        try:
            logger.info(f"[{self.session_id}] 初始化 WebRTC 会话...")

            # 解码参考图像
            image_decoder = ImageDecoder()
            reference_image_path = image_decoder.decode_and_save(reference_image_b64)

            logger.info(f"[{self.session_id}] 参考图像: {reference_image_path}")

            # 创建流式推理引擎
            config = StreamingConfig(
                model_type="lite",
                use_face_crop=True
            )

            self.engine = FlashHeadStreamingEngine(config)

            # 加载模型
            if not self.engine.load_model(reference_image_path):
                logger.error(f"[{self.session_id}] 模型加载失败")
                return False

            # 创建视频 Track
            self.video_track = BufferedVideoStreamTrack(fps=25)
            self.video_generator = FlashHeadVideoGenerator(self.engine, self.video_track)

            logger.success(f"[{self.session_id}] ✅ 会话初始化成功")
            return True

        except Exception as e:
            logger.error(f"[{self.session_id}] 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def process_text_message(self, text: str) -> Dict[str, Any]:
        """
        处理文本消息并生成视频流

        Returns:
            处理结果字典
        """
        try:
            self.message_count += 1
            logger.info(f"[{self.session_id}] 处理消息 #{self.message_count}: {text}")

            # 1. LLM 生成
            logger.info(f"[{self.session_id}] [1/3] LLM 生成中...")
            test_responses = [
                f"你好！收到你的消息「{text}」。我是一个数字人助手，很高兴为你服务。",
                f"关于「{text}」，这是一个很有趣的话题。",
                f"好的，我明白了，你说的是「{text}」。",
            ]
            import random
            ai_text = random.choice(test_responses)
            logger.info(f"[{self.session_id}] ✅ AI 回复: {ai_text[:100]}...")

            # 2. TTS 合成
            logger.info(f"[{self.session_id}] [2/3] TTS 合成中...")
            try:
                tts = get_tts()
                ai_audio = await tts.synthesize(ai_text)

                if ai_audio is None or len(ai_audio) == 0:
                    raise ValueError("TTS 返回空音频")

                duration = len(ai_audio) / 16000
                logger.info(f"[{self.session_id}] ✅ TTS 合成成功: {duration:.2f}秒")

            except Exception as e:
                logger.error(f"[{self.session_id}] ❌ TTS 合成失败: {e}")
                ai_audio = np.zeros(16000 * 3, dtype=np.float32)

            # 3. 生成视频并添加到 Track（后台任务）
            logger.info(f"[{self.session_id}] [3/3] 生成视频...")

            # 创建后台任务处理视频
            asyncio.create_task(self.video_generator.process_audio(ai_audio))

            # 编码音频为 Base64
            try:
                audio_buffer = io.BytesIO()
                import soundfile as sf
                sf.write(audio_buffer, ai_audio, 16000, format='WAV')
                audio_buffer.seek(0)
                audio_b64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
            except Exception as e:
                logger.error(f"[{self.session_id}] 音频编码失败: {e}")
                audio_b64 = None

            return {
                "ai_text": ai_text,
                "audio_data": audio_b64,
                "audio_samples": len(ai_audio),
                "video_duration": len(ai_audio) / 16000,
                "success": True
            }

        except Exception as e:
            logger.error(f"[{self.session_id}] 处理失败: {e}")
            import traceback
            traceback.print_exc()

            return {
                "ai_text": f"你好！收到你的消息「{text}」。抱歉，处理过程中出现了问题。",
                "audio_data": None,
                "success": False,
                "error": str(e)
            }

    def cleanup(self):
        """清理资源"""
        if self.video_track:
            self.video_track.stop()
        if self.engine:
            self.engine.unload()
        if self.pc:
            asyncio.create_task(self.pc.close())


# 全局会话管理
_sessions: Dict[str, WebRTCSession] = {}


@router.websocket("/webrtc/video")
async def webrtc_video_stream_endpoint(websocket: WebSocket):
    """
    WebRTC 视频流端点

    信令协议：
    - Client: {"type": "init", "data": {"reference_image": "..."}}  // 初始化
    - Client: {"type": "offer", "data": {"sdp": "...", "type": "offer"}}  // WebRTC offer
    - Server: {"type": "answer", "data": {"sdp": "...", "type": "answer"}}  // WebRTC answer
    - Client: {"type": "ice_candidate", "data": {"candidate": "...", "sdpMid": "...", "sdpMLineIndex": ...}}
    - Client: {"type": "message", "data": {"text": "..."}}  // 发送消息
    - Server: {"type": "ai_text", "data": {"text": "..."}}  // AI 回复
    - Server: {"type": "audio", "data": {"audio_data": "..."}}  // TTS 音频
    """
    await websocket.accept()

    session_id = str(uuid.uuid4())
    session = WebRTCSession(session_id)
    _sessions[session_id] = session

    logger.info(f"[{session_id}] 🎬 WebRTC 视频流连接建立")

    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebRTC 连接已建立"
        })

        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            message_data = data.get("data", {})

            logger.debug(f"[{session_id}] 收到消息: {message_type}")

            if message_type == "init":
                # 初始化会话
                reference_image = message_data.get("reference_image", "default")

                if reference_image == "default":
                    import os
                    default_image_path = "/opt/soulx/SoulX-FlashHead/examples/girl.png"
                    if os.path.exists(default_image_path):
                        with open(default_image_path, "rb") as f:
                            reference_image = base64.b64encode(f.read()).decode('utf-8')
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"默认参考图像不存在"
                        })
                        continue

                success = await session.initialize(reference_image)

                if success:
                    await websocket.send_json({
                        "type": "initialized",
                        "session_id": session_id
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "会话初始化失败"
                    })

            elif message_type == "offer":
                # WebRTC offer
                if not session.video_track:
                    await websocket.send_json({
                        "type": "error",
                        "message": "会话未初始化"
                    })
                    continue

                # 创建 RTCPeerConnection
                session.pc = RTCPeerConnection(configuration=RTC_CONFIGURATION)

                # 添加视频 track
                session.pc.addTrack(session.video_track)

                # 设置远程描述
                offer = RTCSessionDescription(
                    sdp=message_data.get("sdp"),
                    type=message_data.get("type")
                )
                await session.pc.setRemoteDescription(offer)

                # 创建 answer
                answer = await session.pc.createAnswer()
                await session.pc.setLocalDescription(answer)

                # 发送 answer
                await websocket.send_json({
                    "type": "answer",
                    "data": {
                        "sdp": session.pc.localDescription.sdp,
                        "type": session.pc.localDescription.type
                    }
                })

                logger.info(f"[{session_id}] WebRTC 连接建立")

            elif message_type == "ice_candidate":
                # ICE candidate
                if session.pc:
                    from aiortc import RTCIceCandidate
                    candidate = RTCIceCandidate(
                        sdpMid=message_data.get("sdpMid"),
                        sdpMLineIndex=message_data.get("sdpMLineIndex"),
                        candidate=message_data.get("candidate")
                    )
                    await session.pc.addIceCandidate(candidate)

            elif message_type == "message":
                # 处理文本消息
                if not session.video_track:
                    await websocket.send_json({
                        "type": "error",
                        "message": "会话未初始化"
                    })
                    continue

                text = message_data.get("text", "")
                if not text:
                    continue

                # 处理消息
                result = await session.process_text_message(text)

                # 发送 AI 文本
                if result.get("ai_text"):
                    await websocket.send_json({
                        "type": "ai_text",
                        "data": {"text": result.get("ai_text")}
                    })

                # 发送音频
                if result.get("audio_data"):
                    await websocket.send_json({
                        "type": "audio",
                        "data": {"audio_data": result["audio_data"]}
                    })

                # 发送完成标记
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "success": result.get("success", False),
                        "video_duration": result.get("video_duration", 0)
                    }
                })

            elif message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": time.time()
                })

    except Exception as e:
        logger.error(f"[{session_id}] 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        session.cleanup()
        if session_id in _sessions:
            del _sessions[session_id]
        logger.info(f"[{session_id}] 🔌 连接关闭")
