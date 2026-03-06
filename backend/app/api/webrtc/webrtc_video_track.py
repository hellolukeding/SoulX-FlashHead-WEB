"""
WebRTC 视频流 Track - 简化版

使用帧缓冲队列实现实时视频流
"""
import asyncio
import numpy as np
import torch
from loguru import logger
from typing import Optional
from av import VideoFrame

from aiortc import MediaStreamTrack


class BufferedVideoStreamTrack(MediaStreamTrack):
    """
    缓冲式视频流 Track

    使用帧缓冲队列，从外部添加视频帧
    """

    KIND = "video"

    def __init__(self, fps: int = 25):
        super().__init__()
        self.fps = fps
        self._frame_queue = asyncio.Queue(maxsize=60)  # 缓冲最多 60 帧
        self._current_frame = None
        self._frame_count = 0
        self._running = True

    async def add_frame(self, frame: np.ndarray):
        """
        添加视频帧到队列

        Args:
            frame: RGB 帧 [H, W, 3] uint8
        """
        try:
            self._frame_queue.put_nowait(frame.copy())
        except asyncio.QueueFull:
            # 队列满，丢弃最旧的帧
            try:
                self._frame_queue.get_nowait()
                self._frame_queue.put_nowait(frame.copy())
            except:
                pass

    async def recv(self) -> VideoFrame:
        """
        接收视频帧（WebRTC 调用）

        Returns:
            VideoFrame 对象
        """
        if not self._running:
            # 返回黑屏
            return VideoFrame(width=512, height=512)

        try:
            # 从队列获取帧，超时则使用上一帧
            frame = await asyncio.wait_for(
                self._frame_queue.get(),
                timeout=1.0 / self.fps
            )
            self._current_frame = frame
        except asyncio.TimeoutError:
            # 使用上一帧
            pass

        if self._current_frame is None:
            # 返回黑屏
            return VideoFrame(width=512, height=512)

        # 创建 VideoFrame
        video_frame = VideoFrame.from_ndarray(self._current_frame, format="rgb24")
        video_frame.pts = self._frame_count
        video_frame.time_base = f"{self.fps}/1"
        self._frame_count += 1

        return video_frame

    def stop(self):
        """停止流"""
        self._running = False


class FlashHeadVideoGenerator:
    """
    SoulX-FlashHead 视频生成器

    将 TTS 音频转换为视频帧并添加到 Track
    """

    def __init__(self, engine, track: BufferedVideoStreamTrack):
        self.engine = engine
        self.track = track
        self._running = False

    async def process_audio(self, audio: np.ndarray):
        """
        处理音频并生成视频帧

        Args:
            audio: 音频数据 (16000 Hz, float32)
        """
        try:
            logger.info(f"处理音频: {len(audio)} samples ({len(audio)/16000:.2f}秒)")

            # 使用完整音频处理
            generated_list = self.engine.process_audio_complete(audio, 16000)

            logger.info(f"生成 {len(generated_list)} 个视频块")

            # 将视频帧添加到 Track
            for video_frames in generated_list:
                # video_frames: [N, 3, H, W]
                frames_np = video_frames.cpu().numpy().astype(np.uint8)

                # 转换为 [N, H, W, 3] RGB
                for i in range(frames_np.shape[0]):
                    frame = np.transpose(frames_np[i], (1, 2, 0))
                    await self.track.add_frame(frame)

            logger.success(f"✅ 添加了 {sum(v.shape[0] for v in generated_list)} 帧到队列")

        except Exception as e:
            logger.error(f"处理音频失败: {e}")
            import traceback
            traceback.print_exc()
