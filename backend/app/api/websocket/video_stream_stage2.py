"""
阶段2优化版视频流端点 - 带状态反馈和音频优先
改进用户体验，消除空白期
"""
import asyncio
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
    """视频流会话 - 阶段2优化版（带状态反馈）"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.engine: Optional[FlashHeadInferenceEngine] = None
        self.encoder: Optional[H264Encoder] = None
        self.created_at = time.time()
        self.message_count = 0

    async def initialize(self, reference_image_b64: str) -> bool:
        """初始化会话，加载模型"""
        try:
            logger.info(f"[{self.session_id}] 开始初始化会话...")

            # 解码参考图像
            image_decoder = ImageDecoder()
            reference_image_path = image_decoder.decode_and_save(reference_image_b64)

            logger.info(f"[{self.session_id}] 参考图像已保存: {reference_image_path}")

            # 创建推理引擎
            config = InferenceConfig(
                model_type="lite",
                use_face_crop=True
            )

            self.engine = FlashHeadInferenceEngine(config)

            # 加载模型
            logger.info(f"[{self.session_id}] 正在加载 SoulX-FlashHead 模型...")
            if not self.engine.load_model(reference_image_path):
                logger.error(f"[{self.session_id}] 模型加载失败")
                return False

            # 创建 H.264 编码器
            self.encoder = H264Encoder(force_cpu=True)

            logger.success(f"[{self.session_id}] ✅ 会话初始化成功")
            return True

        except Exception as e:
            logger.error(f"[{self.session_id}] 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def process_text_message(self, text: str, websocket: WebSocket) -> dict:
        """处理文本消息，生成视频 - 阶段2优化版（带状态反馈）"""
        try:
            self.message_count += 1
            logger.info(f"[{self.session_id}] ========== 处理消息 #{self.message_count}: {text} ==========")

            # 发送状态：开始处理
            await self._send_status(websocket, "thinking", 10, "正在理解您的问题...")

            # 1. LLM 生成（带测试模式）
            logger.info(f"[{self.session_id}] [1/4] LLM 生成中...")
            ai_text = None

            try:
                llm = get_llm_client()
                ai_text_chunks = []

                # 流式生成
                async for chunk in llm.chat_stream(text):
                    ai_text_chunks.append(chunk)

                ai_text = "".join(ai_text_chunks)

                if ai_text and len(ai_text.strip()) > 0:
                    logger.info(f"[{self.session_id}] ✅ LLM 生成成功: {ai_text[:50]}...")
                else:
                    raise ValueError("LLM 返回空文本")

            except Exception as e:
                logger.warning(f"[{self.session_id}] ⚠️ LLM 失败，使用测试响应: {e}")
                # 使用测试响应
                ai_text = f"你好！收到你的消息「{text}」。我是一个数字人助手，很高兴为你服务。我正在测试模式，可以和你进行简单对话。"

            # 确保有文本
            if not ai_text or len(ai_text.strip()) == 0:
                ai_text = f"你好！收到你的消息「{text}」。"

            logger.info(f"[{self.session_id}] ✅ AI 回复: {ai_text[:100]}...")

            # 发送状态：开始TTS
            await self._send_status(websocket, "tts", 30, "正在合成语音...")

            # 2. TTS 合成（使用 CosyVoice）
            logger.info(f"[{self.session_id}] [2/4] TTS 合成中...")
            try:
                tts = get_tts()
                ai_audio = await tts.synthesize(ai_text)

                if ai_audio is None or len(ai_audio) == 0:
                    raise ValueError("TTS 返回空音频")

                # 检查音频数据
                if isinstance(ai_audio, np.ndarray):
                    duration = len(ai_audio) / 16000
                    logger.info(f"[{self.session_id}] ✅ TTS 合成成功: {duration:.2f}秒, {len(ai_audio)} samples")
                else:
                    logger.warning(f"[{self.session_id}] ⚠️ TTS 返回格式异常: {type(ai_audio)}")
                    # 生成静音音频
                    ai_audio = np.zeros(16000 * 3, dtype=np.float32)  # 3秒静音

            except Exception as e:
                logger.error(f"[{self.session_id}] ❌ TTS 合成失败: {e}")
                # 生成静音音频
                ai_audio = np.zeros(16000 * 3, dtype=np.float32)  # 3秒静音

            # 编码音频为 Base64
            try:
                audio_buffer = io.BytesIO()
                sf.write(audio_buffer, ai_audio, 16000, format='WAV')
                audio_buffer.seek(0)
                audio_b64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
                logger.info(f"[{self.session_id}] ✅ 音频编码完成: {len(audio_b64)} bytes")
            except Exception as e:
                logger.error(f"[{self.session_id}] ❌ 音频编码失败: {e}")
                audio_b64 = None

            # 🎯 关键改进：立即发送音频，不等待视频
            if audio_b64:
                await websocket.send_json({
                    "type": "ai_audio",
                    "data": {
                        "audio_data": audio_b64,
                        "audio_format": "wav",
                        "sample_rate": 16000
                    }
                })
                logger.info(f"[{self.session_id}] ✅ 音频已发送（音频优先策略）")

            # 发送状态：开始视频生成
            await self._send_status(websocket, "generating", 60, "正在生成视频画面...")

            # 3. 视频生成（后台进行）
            logger.info(f"[{self.session_id}] [3/4] 视频生成中...")

            video_data = None
            video_frames_count = 0

            try:
                # 确保音频是 numpy array
                if not isinstance(ai_audio, np.ndarray):
                    ai_audio = np.array(ai_audio)

                # 确保是 float32
                if ai_audio.dtype != np.float32:
                    ai_audio = ai_audio.astype(np.float32)

                # 确保是单声道
                if len(ai_audio.shape) > 1:
                    ai_audio = ai_audio[:, 0]

                # 检查音频长度
                audio_duration = len(ai_audio) / 16000
                logger.info(f"[{self.session_id}] 音频时长: {audio_duration:.2f}秒")

                if audio_duration < 0.5:
                    logger.warning(f"[{self.session_id}] ⚠️ 音频太短，生成3秒静音视频")
                    ai_audio = np.concatenate([
                        ai_audio,
                        np.zeros(16000 * 3, dtype=np.float32)
                    ])

                # 生成视频
                video_frames = self.engine.process_audio(ai_audio, 16000)

                if video_frames is not None:
                    # 转换 tensor 为 numpy
                    import torch
                    frames_np = video_frames.cpu().numpy()

                    logger.info(f"[{self.session_id}] 视频帧形状: {frames_np.shape}, 类型: {frames_np.dtype}")

                    # 缩放到 [0, 255]
                    if frames_np.max() <= 1.0:
                        frames_np = (frames_np * 255).astype(np.uint8)
                    else:
                        frames_np = frames_np.astype(np.uint8)

                    # 编码为 H.264
                    logger.info(f"[{self.session_id}] [4/4] 视频编码中...")
                    h264_data = self.encoder.encode_frames(frames_np)

                    if h264_data and len(h264_data) > 0:
                        video_data = base64.b64encode(h264_data).decode('utf-8')
                        video_frames_count = len(frames_np)
                        logger.success(f"[{self.session_id}] ✅ 视频生成成功: {video_frames_count} 帧, {len(video_data)} bytes")
                    else:
                        logger.error(f"[{self.session_id}] ❌ 视频编码失败")

                else:
                    logger.error(f"[{self.session_id}] ❌ 视频生成失败")

            except Exception as e:
                logger.error(f"[{self.session_id}] ❌ 视频生成失败: {e}")
                import traceback
                traceback.print_exc()

            # 发送视频（如果生成成功）
            if video_data:
                await websocket.send_json({
                    "type": "video_frame",
                    "data": {
                        "frame_number": self.message_count,
                        "video_data": video_data,
                        "video_frames": video_frames_count
                    }
                })
                logger.info(f"[{self.session_id}] ✅ 视频帧已发送")

            # 返回结果
            result = {
                "ai_text": ai_text,
                "audio_data": audio_b64,
                "audio_format": "wav",
                "sample_rate": 16000,
                "video_frames": video_frames_count,
                "video_data": video_data,
                "success": True
            }

            logger.success(f"[{self.session_id}] ✅ 消息处理完成")
            return result

        except Exception as e:
            logger.error(f"[{self.session_id}] ❌ 处理消息失败: {e}")
            import traceback
            traceback.print_exc()

            # 返回错误但至少返回文本
            return {
                "ai_text": f"你好！收到你的消息「{text}」。抱歉，处理过程中出现了问题。",
                "audio_data": None,
                "audio_format": "wav",
                "sample_rate": 16000,
                "video_frames": 0,
                "video_data": None,
                "success": False,
                "error": str(e)
            }

    async def _send_status(self, websocket: WebSocket, stage: str, progress: int, message: str):
        """发送状态消息"""
        try:
            await websocket.send_json({
                "type": "status",
                "data": {
                    "stage": stage,
                    "progress": progress,
                    "message": message
                }
            })
        except Exception as e:
            logger.warning(f"[{self.session_id}] 发送状态失败: {e}")

    def cleanup(self):
        """清理资源"""
        if self.engine:
            try:
                self.engine.unload()
            except:
                pass
        if self.encoder:
            try:
                self.encoder.close()
            except:
                pass


@router.websocket("/video")
async def video_stream_endpoint(websocket: WebSocket):
    """
    WebSocket 视频流端点 - 阶段2优化版（带状态反馈）

    优化内容：
    1. 实时状态反馈
    2. 音频优先播放
    3. 进度指示
    4. 消除空白期

    只使用 models 文件夹中的模型：
    - CosyVoice (TTS)
    - SoulX-FlashHead-1_3B (视频生成)
    - wav2vec2-base-960h (ASR)
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
                    import os
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

                # 处理消息（带websocket参数以发送状态）
                result = await session.process_text_message(text, websocket)

                # 发送 AI 文本
                if result.get("ai_text"):
                    await websocket.send_json({
                        "type": "ai_text_chunk",
                        "data": {
                            "text": result.get("ai_text", "")
                        }
                    })

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
