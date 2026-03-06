"""
WebRTC 流式端点 - 全链路异步流式架构

特性：
- LLM 流式输出 → CosyVoice 流式切片 (150ms)
- SoulX 时空缓存 (deque 上下文)
- WebRTC UDP 推流
- 极低延迟目标: < 250ms

架构:
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
│   LLM   │ ──> │ CosyVoice│ ──> │ SoulX    │ ──> │ WebRTC  │
│Streaming│     │ Chunking │     │ Temporal │     │  UDP    │
└─────────┘     └──────────┘     └──────────┘     └─────────┘
     │                │                 │
     └────────────────┴─────────────────┘
                 asyncio.Queue (内存共享)
"""
import asyncio
import json
import time
import uuid
from typing import Optional, AsyncIterator
from loguru import logger

from fastapi import APIRouter

from aiortc import RTCPeerConnection, RTCSessionDescription

from app.core.streaming.pipeline_webrtc import (
    StreamingPipeline,
    StreamingConfig,
    StreamingVideoTrack,
    StreamingAudioTrack,
)
from app.core.inference.flashhead_streaming import FlashHeadStreamingEngine, StreamingConfig as SoulXConfig
from app.services.tts.factory import get_tts
from app.services.llm.client import get_llm_client


router = APIRouter()


# ============================================================================
# 配置
# ============================================================================

STREAMING_CONFIG = StreamingConfig(
    audio_chunk_size=2400,  # 150ms @ 16kHz
    temporal_cache_size=21120,  # SoulX 时空缓存
    overlap_frames=9,
    output_stride=24,
    fps=25,
    use_sage_attention=True,
)

# SoulX 流式配置
SOULX_CONFIG = SoulXConfig(
    model_type="lite",
    use_face_crop=True,
)


# ============================================================================
# WebRTC 端点
# ============================================================================

class WebRTCStreamingSession:
    """WebRTC 流式会话 - 全链路异步架构"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.pc: Optional[RTCPeerConnection] = None
        self.video_track: Optional[StreamingVideoTrack] = None
        self.audio_track: Optional[StreamingAudioTrack] = None
        self.pipeline: Optional[StreamingPipeline] = None

        # 引擎
        self.tts_engine = None
        self.soulx_engine: Optional[FlashHeadStreamingEngine] = None  # ✅ 使用流式引擎
        self.llm_client = None

        # 状态
        self.is_initialized = False

    async def initialize(self):
        """初始化会话"""
        logger.info(f"[{self.session_id}] 初始化 WebRTC 流式会话")

        try:
            # 1. 初始化 TTS (CosyVoice)
            logger.info(f"[{self.session_id}] [1/3] 初始化 CosyVoice...")
            self.tts_engine = get_tts()
            logger.success(f"[{self.session_id}] ✅ CosyVoice 已初始化")

            # 2. 初始化 SoulX 流式引擎
            logger.info(f"[{self.session_id}] [2/3] 初始化 SoulX-FlashHead 流式引擎...")
            self.soulx_engine = FlashHeadStreamingEngine(SOULX_CONFIG)

            # 加载模型（使用默认参考图像）
            import os
            default_image = "/opt/soulx/SoulX-FlashHead/examples/girl.png"
            if os.path.exists(default_image):
                self.soulx_engine.load_model(default_image)
                logger.success(f"[{self.session_id}] ✅ SoulX 流式引擎已加载")
                logger.info(f"[{self.session_id}]    frame_num: {self.soulx_engine.frame_num}")
                logger.info(f"[{self.session_id}]    motion_frames_num: {self.soulx_engine.motion_frames_num}")
                logger.info(f"[{self.session_id}]    slice_len: {self.soulx_engine.slice_len}")
            else:
                logger.warning(f"[{self.session_id}] ⚠️ 默认参考图像不存在，跳过")

            # 3. 初始化 LLM
            logger.info(f"[{self.session_id}] [3/3] 初始化 LLM...")
            self.llm_client = get_llm_client()
            logger.success(f"[{self.session_id}] ✅ LLM 已初始化")

            # 4. 创建 WebRTC Track
            self.video_track = StreamingVideoTrack(STREAMING_CONFIG)
            self.audio_track = StreamingAudioTrack(sample_rate=16000)

            self.is_initialized = True
            logger.success(f"[{self.session_id}] ✅ 会话初始化完成")

        except Exception as e:
            logger.error(f"[{self.session_id}] ❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def process_message(self, text: str) -> dict:
        """处理用户消息 - 流式并行架构"""
        logger.info(f"[{self.session_id}] 📨 处理消息: {text}")

        if not self.is_initialized:
            raise RuntimeError("会话未初始化")

        # 创建文本流（模拟 LLM 流式输出）
        async def text_stream():
            # TODO: 替换为真实的 LLM 流式输出
            response = f"你好！收到你的消息「{text}」。我是数字人助手，很高兴为你服务。"
            for char in response:
                yield char
                await asyncio.sleep(0.01)  # 模拟流式输出

        # 创建流水线
        self.pipeline = StreamingPipeline(STREAMING_CONFIG)

        # 运行流水线
        await self.pipeline.process(
            text_stream=text_stream(),
            tts_engine=self.tts_engine,
            soulx_engine=self.soulx_engine,
            video_track=self.video_track,
            audio_track=self.audio_track,
        )

        return {"success": True}

    def cleanup(self):
        """清理资源"""
        if self.soulx_engine:
            self.soulx_engine.unload()
        if self.pipeline:
            self.pipeline.stop()
        if self.video_track:
            self.video_track.stop()
        if self.audio_track:
            self.audio_track.stop()


# ============================================================================
# 全局会话管理
# ============================================================================

_sessions: dict[str, WebRTCStreamingSession] = {}


@router.post("/offer")
async def webrtc_offer(offer: dict):
    """
    WebRTC SDP Offer 端点

    接收客户端的 SDP Offer，返回 SDP Answer
    """
    try:
        # 解析 Offer
        offer_sdp = RTCSessionDescription(
            sdp=offer.get("sdp"),
            type=offer.get("type", "offer")
        )

        # 创建会话
        session_id = str(uuid.uuid4())
        session = WebRTCStreamingSession(session_id)

        # 初始化
        await session.initialize()

        # 创建 PeerConnection
        pc = RTCPeerConnection()
        session.pc = pc

        # 添加轨道
        if session.video_track:
            pc.addTrack(session.video_track)
        if session.audio_track:
            pc.addTrack(session.audio_track)

        # 设置远程描述
        await pc.setRemoteDescription(offer_sdp)

        # 创建 Answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        # 保存会话
        _sessions[session_id] = session

        # 返回 Answer
        return {
            "sdp": pc.localDescription.sdp,
            "type": "answer",
            "session_id": session_id,
        }

    except Exception as e:
        logger.error(f"WebRTC Offer 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@router.post("/message")
async def webrtc_message(message: dict):
    """
    WebRTC 消息端点

    处理客户端发送的消息（文本输入）
    """
    session_id = message.get("session_id")
    text = message.get("text", "")

    if not session_id or session_id not in _sessions:
        return {"error": "Invalid session"}

    session = _sessions[session_id]

    try:
        # 处理消息（流式）
        result = await session.process_message(text)
        return result

    except Exception as e:
        logger.error(f"消息处理失败: {e}")
        return {"error": str(e)}


@router.post("/cleanup")
async def webrtc_cleanup(request: dict):
    """清理会话"""
    session_id = request.get("session_id")
    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        session.cleanup()
        del _sessions[session_id]
        return {"success": True}
    return {"error": "Invalid session"}
