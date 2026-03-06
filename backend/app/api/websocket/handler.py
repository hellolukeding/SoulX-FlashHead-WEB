"""
WebSocket 连接处理器
"""
import json
import asyncio
import time
import base64
from typing import Dict, Optional, Set
from struct import pack
from contextlib import nullcontext
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect
import uuid

import numpy as np
from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig
from app.core.session.state import SessionState
from app.core.streaming.audio_decoder import AudioDecoder
from app.core.streaming.image_decoder import ImageDecoder
from app.core.streaming.h264_encoder import H264Encoder
from app.core.streaming.audio_buffer import AudioBuffer
from app.core.streaming.gpu_manager import GPUMemoryManager
from app.core.streaming.performance import PerformanceMetrics, PerformanceTimer
from app.services.llm.client import get_llm_client
from app.services.tts.factory import get_tts
from app.services.asr.factory import get_asr


class ConnectionManager:
    """
    WebSocket 连接管理器

    管理所有 WebSocket 连接和会话
    """

    def __init__(self):
        # 活跃连接: session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # 会话状态: session_id -> SessionState
        self.sessions: Dict[str, SessionState] = {}

        # 会话的推理引擎: session_id -> FlashHeadInferenceEngine
        self.engines: Dict[str, FlashHeadInferenceEngine] = {}

        # 流式处理组件
        self.gpu_manager = GPUMemoryManager(max_sessions=5)
        self.decoders: Dict[str, AudioDecoder] = {}
        self.encoders: Dict[str, H264Encoder] = {}
        self.buffers: Dict[str, AudioBuffer] = {}
        self.metrics: Dict[str, PerformanceMetrics] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """
        接受新的 WebSocket 连接

        Args:
            websocket: WebSocket 连接
            session_id: 会话 ID

        Returns:
            是否连接成功
        """
        try:
            await websocket.accept()
            self.active_connections[session_id] = websocket

            # 创建会话状态
            self.sessions[session_id] = SessionState(
                session_id=session_id,
                created_at=time.time()
            )

            logger.info(f"✅ 新连接: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False

    def disconnect(self, session_id: str):
        """
        断开连接并清理资源

        Args:
            session_id: 会话 ID
        """
        # 关闭编码器
        if session_id in self.encoders:
            try:
                self.encoders[session_id].close()
            except Exception as e:
                logger.warning(f"关闭编码器失败: {e}")
            del self.encoders[session_id]

        # 卸载推理引擎
        if session_id in self.engines:
            self.engines[session_id].unload()
            del self.engines[session_id]

        # 释放 GPU 资源
        self.gpu_manager.free_session(session_id)

        # 删除流式处理组件
        self.buffers.pop(session_id, None)
        self.decoders.pop(session_id, None)
        self.metrics.pop(session_id, None)

        # 删除会话
        if session_id in self.sessions:
            del self.sessions[session_id]

        # 删除连接
        if session_id in self.active_connections:
            del self.active_connections[session_id]

        logger.info(f"❌ 连接断开: {session_id}")

    async def send_message(self, session_id: str, message: dict) -> bool:
        """
        发送消息到指定会话

        Args:
            session_id: 会话 ID
            message: 消息内容

        Returns:
            是否发送成功
        """
        if session_id not in self.active_connections:
            logger.warning(f"会话不存在: {session_id}")
            return False

        try:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
            return True

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.disconnect(session_id)
            return False

    async def send_bytes(self, session_id: str, data: bytes) -> bool:
        """
        发送二进制数据到指定会话

        Args:
            session_id: 会话 ID
            data: 二进制数据

        Returns:
            是否发送成功
        """
        if session_id not in self.active_connections:
            logger.warning(f"会话不存在: {session_id}")
            return False

        try:
            websocket = self.active_connections[session_id]
            await websocket.send_bytes(data)
            return True

        except Exception as e:
            logger.error(f"发送二进制数据失败: {e}")
            self.disconnect(session_id)
            return False

    async def broadcast(self, message: dict):
        """
        广播消息到所有连接

        Args:
            message: 消息内容
        """
        disconnected = []
        for session_id in self.active_connections:
            success = await self.send_message(session_id, message)
            if not success:
                disconnected.append(session_id)

        # 清理断开的连接
        for session_id in disconnected:
            self.disconnect(session_id)

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        获取会话状态

        Args:
            session_id: 会话 ID

        Returns:
            会话状态或 None
        """
        return self.sessions.get(session_id)

    def list_sessions(self) -> list:
        """
        列出所有活跃会话

        Returns:
            会话列表
        """
        return [
            {
                "session_id": session_id,
                "status": self.sessions[session_id].status,
                "created_at": self.sessions[session_id].created_at
            }
            for session_id in self.sessions
        ]

    def get_engine(self, session_id: str) -> Optional[FlashHeadInferenceEngine]:
        """
        获取会话的推理引擎

        Args:
            session_id: 会话 ID

        Returns:
            推理引擎或 None
        """
        return self.engines.get(session_id)


class WebSocketHandler:
    """
    WebSocket 消息处理器

    处理客户端发送的各种消息
    """

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def handle_message(
        self,
        session_id: str,
        message: dict
    ):
        """
        处理接收到的消息

        Args:
            session_id: 会话 ID
            message: 消息内容
        """
        message_type = message.get("type")
        data = message.get("data", {})

        logger.debug(f"收到消息 [{message_type}]: {session_id}")

        try:
            if message_type == "create_session":
                await self._create_session(session_id, data)

            elif message_type == "audio_chunk":
                await self._handle_audio_chunk(session_id, data)

            elif message_type == "pause_session":
                await self._pause_session(session_id)

            elif message_type == "resume_session":
                await self._resume_session(session_id)

            elif message_type == "close_session":
                await self._close_session(session_id)

            elif message_type == "user_message":
                await self._handle_user_message(session_id, data)

            elif message_type == "text_message":
                await self._handle_text_message(session_id, data)

            elif message_type == "ping":
                await self._handle_ping(session_id)

            else:
                await self._send_error(session_id, 400, f"未知消息类型: {message_type}")

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await self._send_error(session_id, 500, str(e))

    async def _create_session(self, session_id: str, data: dict):
        """创建会话并加载模型"""
        try:
            # 检查 GPU 资源
            if not self.manager.gpu_manager.can_allocate_session():
                await self._send_error(session_id, 503, "达到最大并发会话数")
                return

            # 获取参数
            model_type = data.get("model_type", "lite")
            reference_image_b64 = data.get("reference_image")

            if not reference_image_b64:
                await self._send_error(session_id, 400, "缺少 reference_image")
                return

            # 解码参考图像
            image_decoder = ImageDecoder()
            reference_image_path = image_decoder.decode_and_save(reference_image_b64)

            # 创建推理引擎
            config = InferenceConfig(
                model_type=model_type,
                use_face_crop=True
            )

            engine = FlashHeadInferenceEngine(config)

            # 加载模型
            if engine.load_model(reference_image_path):
                # 分配 GPU 资源
                self.manager.gpu_manager.allocate_session(session_id)

                # 保存引擎和流式处理组件
                self.manager.engines[session_id] = engine
                self.manager.decoders[session_id] = AudioDecoder()
                self.manager.encoders[session_id] = H264Encoder()
                self.manager.buffers[session_id] = AudioBuffer()
                self.manager.metrics[session_id] = PerformanceMetrics()

                # 更新会话状态
                session = self.manager.get_session(session_id)
                if session:
                    session.status = "ready"
                    session.model_type = model_type
                    session.reference_image = reference_image_path

                # 发送成功响应
                await self.manager.send_message(session_id, {
                    "type": "session_created",
                    "data": {
                        "session_id": session_id,
                        "status": "ready",
                        "model_type": model_type
                    },
                    "timestamp": self._get_timestamp()
                })

                logger.success(f"✅ 会话创建成功: {session_id}")
            else:
                await self._send_error(session_id, 500, "模型加载失败")

        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            await self._send_error(session_id, 500, str(e))

    async def _handle_audio_chunk(self, session_id: str, data: dict):
        """处理音频块"""
        start_time = time.time()
        metrics = self.manager.metrics.get(session_id)

        try:
            # 获取组件
            engine = self.manager.get_engine(session_id)
            decoder = self.manager.decoders.get(session_id)
            encoder = self.manager.encoders.get(session_id)
            buffer = self.manager.buffers.get(session_id)

            if not all([engine, decoder, encoder, buffer]):
                await self._send_error(session_id, 404, "会话未创建")
                return

            # 解码音频
            with PerformanceTimer(metrics, "audio_decode") if metrics else nullcontext():
                audio_format = data.get("format", "wav")
                audio_b64 = data.get("audio_data")

                audio_data = decoder.decode_base64_audio(audio_b64, audio_format)

            # 添加到缓冲
            audio_window = buffer.add_chunk(audio_data)

            if audio_window is not None:
                logger.info(f"[{session_id}] 音频缓冲满，开始处理: {len(audio_window)} samples")

                # 生成视频帧
                try:
                    video_frames = engine.process_audio(audio_window)

                    if video_frames is not None and metrics:
                        fps = 25.0  # 固定 25 FPS
                        inference_time = time.time() - start_time
                        metrics.add_inference_time(inference_time, fps)

                    if video_frames is not None:
                        # 转换 tensor 为 numpy
                        import torch
                        frames_np = video_frames.cpu().numpy().transpose(0, 2, 3, 1)  # [F, H, W, C]
                        frames_np = (frames_np * 255).astype(np.uint8)

                        # 编码为 H.264
                        with PerformanceTimer(metrics, "encode") if metrics else nullcontext():
                            h264_data = encoder.encode_frames(frames_np)

                        # 发送视频帧
                        await self._send_video_packet(session_id, h264_data, is_keyframe=True)

                        # 更新会话统计
                        session = self.manager.get_session(session_id)
                        if session:
                            session.video_frames_generated += len(frames_np)
                            session.last_activity = time.time()

                        # 记录端到端延迟
                        if metrics:
                            metrics.add_latency(time.time() - start_time)

                except Exception as e:
                    logger.error(f"[{session_id}] 生成视频失败: {e}")
                    await self._send_error(session_id, 500, f"视频生成失败: {str(e)}")
                    return

            # 发送确认
            await self.manager.send_message(session_id, {
                "type": "audio_received",
                "data": {
                    "session_id": session_id,
                    "sequence": data.get("sequence", 0),
                    "status": "processing",
                    "buffer_size": buffer.get_buffer_size()
                },
                "timestamp": self._get_timestamp()
            })

        except Exception as e:
            logger.error(f"[{session_id}] 处理音频块失败: {e}")
            await self._send_error(session_id, 500, str(e))

    async def _send_video_packet(
        self,
        session_id: str,
        packet: bytes,
        is_keyframe: bool
    ):
        """发送 H.264 视频包"""
        # 构建二进制消息头
        header = pack('>BBHIH',
                      0x01,              # message_type: video_packet
                      1 if is_keyframe else 2,  # frame_type
                      0,                 # sequence (todo: increment)
                      int(time.time()),  # timestamp
                      len(packet))       # payload_size

        # 发送二进制消息
        success = await self.manager.send_bytes(session_id, header + packet)

        if success:
            logger.debug(f"[{session_id}] 发送视频包: {len(packet)} bytes, keyframe={is_keyframe}")

    async def _handle_user_message(self, session_id: str, data: dict):
        """
        处理用户消息（完整对话流程）

        流程: ASR识别 → LLM生成 → TTS合成 → 视频生成

        Args:
            session_id: 会话ID
            data: {audio_data, audio_format}
        """
        try:
            # 获取服务组件
            engine = self.manager.get_engine(session_id)
            decoder = self.manager.decoders.get(session_id)
            encoder = self.manager.encoders.get(session_id)

            if not all([engine, decoder, encoder]):
                await self._send_error(session_id, 404, "会话未创建")
                return

            # 获取ASR和TTS服务
            asr = get_asr()
            tts = get_tts()
            llm = get_llm_client()

            # 1. 解码音频
            audio_format = data.get("format", "wav")
            audio_b64 = data.get("audio_data")

            logger.info(f"[{session_id}] 开始处理用户消息...")

            user_audio = decoder.decode_base64_audio(audio_b64, audio_format)

            # 2. ASR识别
            logger.info(f"[{session_id}] ASR识别中...")
            user_text = await asr.recognize(user_audio)
            logger.info(f"[{session_id}] 用户: {user_text}")

            # 发送识别结果
            await self.manager.send_message(session_id, {
                "type": "user_text",
                "data": {
                    "text": user_text
                }
            })

            # 3. LLM生成（流式）
            logger.info(f"[{session_id}] LLM生成中...")

            ai_text_chunks = []
            async for chunk in llm.chat_stream(user_text):
                ai_text_chunks.append(chunk)

                # 流式发送文本
                await self.manager.send_message(session_id, {
                    "type": "ai_text_chunk",
                    "data": {
                        "text": chunk
                    }
                })

            ai_text = "".join(ai_text_chunks)
            logger.info(f"[{session_id}] AI: {ai_text}")

            # 发送完整文本
            await self.manager.send_message(session_id, {
                "type": "ai_text_complete",
                "data": {
                    "text": ai_text
                }
            })

            # 4. TTS合成
            logger.info(f"[{session_id}] TTS合成中...")
            ai_audio = await tts.synthesize(ai_text)

            # 发送音频（Base64编码）
            import io
            audio_buffer = io.BytesIO()
            import soundfile as sf
            sf.write(audio_buffer, ai_audio, 16000, format='WAV')
            audio_buffer.seek(0)
            audio_b64_result = base64.b64encode(audio_buffer.read()).decode('utf-8')

            await self.manager.send_message(session_id, {
                "type": "ai_audio",
                "data": {
                    "audio_data": audio_b64_result,
                    "format": "wav",
                    "sample_rate": 16000
                }
            })

            # 5. 视频生成
            logger.info(f"[{session_id}] 生成视频中...")

            # 重采样音频到16kHz
            if len(ai_audio) / 16000 > 0:
                video_frames = engine.process_audio(ai_audio, 16000)

                if video_frames is not None:
                    # 转换tensor为numpy
                    import torch
                    frames_np = video_frames.cpu().numpy().transpose(0, 2, 3, 1)  # [F, H, W, C]
                    frames_np = (frames_np * 255).astype(np.uint8)

                    # 编码为H.264
                    h264_data = encoder.encode_frames(frames_np)

                    # 发送视频帧
                    await self._send_video_packet(session_id, h264_data, is_keyframe=True)

                    logger.success(f"[{session_id}] ✅ 完整对话流程完成")

                    # 更新会话统计
                    session = self.manager.get_session(session_id)
                    if session:
                        session.video_frames_generated += len(frames_np)
                        session.last_activity = time.time()
                else:
                    logger.error(f"[{session_id}] 视频生成失败")
                    await self._send_error(session_id, 500, "视频生成失败")
            else:
                logger.warning(f"[{session_id}] TTS音频为空")
                await self._send_error(session_id, 500, "TTS音频生成失败")

        except Exception as e:
            logger.error(f"[{session_id}] 处理用户消息失败: {e}")
            import traceback
            traceback.print_exc()
            await self._send_error(session_id, 500, str(e))

    async def _handle_text_message(self, session_id: str, data: dict):
        """
        处理纯文本消息（跳过ASR）

        流程: LLM生成 → TTS合成 → 视频生成

        Args:
            session_id: 会话ID
            data: {text}
        """
        try:
            # 获取服务组件
            engine = self.manager.get_engine(session_id)
            encoder = self.manager.encoders.get(session_id)

            if not all([engine, encoder]):
                await self._send_error(session_id, 404, "会话未创建")
                return

            # 获取TTS和LLM服务
            tts = get_tts()
            llm = get_llm_client()

            # 获取用户文本
            user_text = data.get("text", "")

            logger.info(f"[{session_id}] 用户(文本): {user_text}")

            # 1. LLM生成（流式）
            logger.info(f"[{session_id}] LLM生成中...")

            ai_text_chunks = []
            async for chunk in llm.chat_stream(user_text):
                ai_text_chunks.append(chunk)

                # 流式发送文本
                await self.manager.send_message(session_id, {
                    "type": "ai_text_chunk",
                    "data": {
                        "text": chunk
                    }
                })

            ai_text = "".join(ai_text_chunks)
            logger.info(f"[{session_id}] AI: {ai_text}")

            # 发送完整文本
            await self.manager.send_message(session_id, {
                "type": "ai_text_complete",
                "data": {
                    "text": ai_text
                }
            })

            # 2. TTS合成
            logger.info(f"[{session_id}] TTS合成中...")
            ai_audio = await tts.synthesize(ai_text)

            # 发送音频（Base64编码）
            import io
            audio_buffer = io.BytesIO()
            import soundfile as sf
            sf.write(audio_buffer, ai_audio, 16000, format='WAV')
            audio_buffer.seek(0)
            audio_b64_result = base64.b64encode(audio_buffer.read()).decode('utf-8')

            await self.manager.send_message(session_id, {
                "type": "ai_audio",
                "data": {
                    "audio_data": audio_b64_result,
                    "format": "wav",
                    "sample_rate": 16000
                }
            })

            # 3. 视频生成
            logger.info(f"[{session_id}] 生成视频中...")

            # 重采样音频到16kHz
            if len(ai_audio) / 16000 > 0:
                video_frames = engine.process_audio(ai_audio, 16000)

                if video_frames is not None:
                    # 转换tensor为numpy
                    import torch
                    frames_np = video_frames.cpu().numpy().transpose(0, 2, 3, 1)  # [F, H, W, C]
                    frames_np = (frames_np * 255).astype(np.uint8)

                    # 编码为H.264
                    h264_data = encoder.encode_frames(frames_np)

                    # 发送视频帧
                    await self._send_video_packet(session_id, h264_data, is_keyframe=True)

                    logger.success(f"[{session_id}] ✅ 文本对话流程完成")

                    # 更新会话统计
                    session = self.manager.get_session(session_id)
                    if session:
                        session.video_frames_generated += len(frames_np)
                        session.last_activity = time.time()
                else:
                    logger.error(f"[{session_id}] 视频生成失败")
                    await self._send_error(session_id, 500, "视频生成失败")
            else:
                logger.warning(f"[{session_id}] TTS音频为空")
                await self._send_error(session_id, 500, "TTS音频生成失败")

        except Exception as e:
            logger.error(f"[{session_id}] 处理文本消息失败: {e}")
            import traceback
            traceback.print_exc()
            await self._send_error(session_id, 500, str(e))
    async def _pause_session(self, session_id: str):
        """暂停会话"""
        session = self.manager.get_session(session_id)
        if session:
            session.status = "paused"

        await self.manager.send_message(session_id, {
            "type": "session_paused",
            "data": {
                "session_id": session_id,
                "status": "paused"
            },
            "timestamp": self._get_timestamp()
        })

    async def _resume_session(self, session_id: str):
        """恢复会话"""
        session = self.manager.get_session(session_id)
        if session:
            session.status = "active"

        await self.manager.send_message(session_id, {
            "type": "session_resumed",
            "data": {
                "session_id": session_id,
                "status": "active"
            },
            "timestamp": self._get_timestamp()
        })

    async def _close_session(self, session_id: str):
        """关闭会话"""
        # 获取剩余音频数据
        buffer = self.manager.buffers.get(session_id)
        if buffer:
            remaining = buffer.get_remaining()
            if remaining is not None and len(remaining) > 1000:
                logger.info(f"[{session_id}] 处理剩余音频: {len(remaining)} samples")
                # 可以选择处理剩余的音频

        self.manager.disconnect(session_id)

        await self.manager.send_message(session_id, {
            "type": "session_closed",
            "data": {
                "session_id": session_id,
                "status": "closed"
            },
            "timestamp": self._get_timestamp()
        })

    async def _handle_ping(self, session_id: str):
        """处理心跳"""
        # 获取性能指标
        metrics = self.manager.metrics.get(session_id)
        perf_data = metrics.to_dict() if metrics else {}

        await self.manager.send_message(session_id, {
            "type": "pong",
            "data": {
                "timestamp": self._get_timestamp(),
                "performance": perf_data
            }
        })

    async def _send_error(self, session_id: str, code: int, message: str):
        """发送错误消息"""
        await self.manager.send_message(session_id, {
            "type": "error",
            "data": {
                "code": code,
                "message": message
            },
            "timestamp": self._get_timestamp()
        })

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# 全局连接管理器实例
manager = ConnectionManager()
handler = WebSocketHandler(manager)
