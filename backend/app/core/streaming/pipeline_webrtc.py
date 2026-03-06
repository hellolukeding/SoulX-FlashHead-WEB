"""
全链路异步流式 WebRTC 架构

实现极低延迟数字人交互：
- CosyVoice 流式切片 (150-200ms)
- SoulX 时空缓存机制
- 内存级数据传递 (零磁盘 IO)
- WebRTC UDP 推流

目标延迟：
- 首包延迟 (TTFT): < 250ms
- 音画同步误差: < 20ms
"""
import asyncio
import time
import numpy as np
import torch
from collections import deque
from loguru import logger
from typing import AsyncIterator, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from aiortc import MediaStreamTrack
from av import VideoFrame


# ============================================================================
# 配置
# ============================================================================

@dataclass
class StreamingConfig:
    """流式配置"""
    # 音频切片大小 (150-200ms @ 16kHz = 2400-3200 samples)
    audio_chunk_size: int = 2400  # 150ms

    # SoulX 时空缓存配置
    temporal_cache_size: int = 21120  # 33 帧 @ 16kHz/25fps = 1.32秒
    overlap_frames: int = 9  # 重叠帧数
    output_stride: int = 24  # 输出帧步长 (33 - 9)

    # 视频缓冲
    video_buffer_size: int = 60  # 最大缓冲帧数

    # FPS
    fps: int = 25

    # SageAttention
    use_sage_attention: bool = True


# ============================================================================
# WebRTC 视频轨道 - 优化版
# ============================================================================

class StreamingVideoTrack(MediaStreamTrack):
    """
    流式视频轨道 - 支持 WebRTC 实时推流

    特性：
    - 帧队列自动管理
    - 自动丢帧保实时
    - PTS 时间戳自动管理
    """
    KIND = "video"

    def __init__(self, config: StreamingConfig):
        super().__init__()
        self.config = config
        self._frame_queue: asyncio.Queue[Optional[np.ndarray]] = asyncio.Queue(
            maxsize=config.video_buffer_size
        )
        self._current_frame: Optional[np.ndarray] = None
        self._frame_count = 0
        self._running = True
        self._start_time = time.time()

        # 统计
        self._frames_sent = 0
        self._frames_dropped = 0

    async def add_frame(self, frame: np.ndarray) -> bool:
        """
        添加视频帧

        Args:
            frame: RGB 帧 [H, W, 3] uint8

        Returns:
            是否成功添加（False 表示队列满，帧被丢弃）
        """
        if not self._running:
            return False

        try:
            self._frame_queue.put_nowait(frame.copy())
            return True
        except asyncio.QueueFull:
            # 队列满，丢弃最旧的帧
            try:
                self._frame_queue.get_nowait()
                self._frame_queue.put_nowait(frame.copy())
                self._frames_dropped += 1
            except:
                pass
            return False

    async def recv(self) -> VideoFrame:
        """
        接收帧（WebRTC 调用）

        Returns:
            VideoFrame 对象
        """
        if not self._running:
            # 返回黑屏
            return VideoFrame(width=512, height=512)

        # 计算超时（根据 FPS）
        timeout = 1.0 / self.config.fps

        try:
            frame = await asyncio.wait_for(
                self._frame_queue.get(),
                timeout=timeout
            )

            if frame is None:
                # 结束信号
                self._running = False
                return VideoFrame(width=512, height=512)

            self._current_frame = frame
            self._frames_sent += 1

        except asyncio.TimeoutError:
            # 超时，使用上一帧
            pass

        if self._current_frame is None:
            # 还没有帧，返回黑屏
            return VideoFrame(width=512, height=512)

        # 创建 VideoFrame
        video_frame = VideoFrame.from_ndarray(self._current_frame, format="rgb24")
        video_frame.pts = self._frame_count
        video_frame.time_base = f"{self.config.fps}/1"
        self._frame_count += 1

        return video_frame

    def stop(self):
        """停止流"""
        self._running = False
        try:
            self._frame_queue.put_nowait(None)
        except:
            pass

    def get_stats(self) -> dict:
        """获取统计信息"""
        elapsed = time.time() - self._start_time
        return {
            "frames_sent": self._frames_sent,
            "frames_dropped": self._frames_dropped,
            "elapsed": elapsed,
            "fps": self._frames_sent / elapsed if elapsed > 0 else 0
        }


# ============================================================================
# WebRTC 音频轨道
# ============================================================================

class StreamingAudioTrack(MediaStreamTrack):
    """
    流式音频轨道 - 支持 WebRTC 实时推流

    特性：
    - Opus 编码
    - 自动音频缓冲
    """
    KIND = "audio"

    def __init__(self, sample_rate: int = 16000):
        super().__init__()
        self.sample_rate = sample_rate
        self._audio_queue: asyncio.Queue[Optional[np.ndarray]] = asyncio.Queue(maxsize=50)
        self._current_audio: Optional[np.ndarray] = None
        self._audio_position = 0
        self._running = True

    async def add_audio(self, audio: np.ndarray):
        """添加音频数据"""
        if not self._running:
            return

        try:
            self._audio_queue.put_nowait(audio.copy())
        except asyncio.QueueFull:
            logger.warning("音频队列满，丢弃")

    async def recv(self):
        """
        接收音频（WebRTC 调用）

        Returns:
            AudioFrame 对象
        """
        from av import AudioFrame

        frame_size = int(self.sample_rate / 50)  # 20ms 帧

        if not self._running or self._current_audio is None:
            # 返回静音
            return AudioFrame(format='s16', layout='mono', samples=frame_size)

        # 检查是否需要新音频
        if self._audio_position + frame_size > len(self._current_audio):
            # 获取新音频
            try:
                self._current_audio = await asyncio.wait_for(
                    self._audio_queue.get(),
                    timeout=0.1
                )
                if self._current_audio is None:
                    self._running = False
                    return AudioFrame(format='s16', layout='mono', samples=frame_size)
                self._audio_position = 0
            except asyncio.TimeoutError:
                return AudioFrame(format='s16', layout='mono', samples=frame_size)

        # 提取帧
        chunk = self._current_audio[self._audio_position:self._audio_position + frame_size]
        self._audio_position += frame_size

        # 转换为 int16
        if chunk.dtype != np.int16:
            chunk = (chunk * 32767).astype(np.int16)

        # 创建 AudioFrame
        audio_frame = AudioFrame.from_ndarray(
            chunk.reshape(1, -1),
            format='s16',
            layout='mono'
        )
        audio_frame.sample_rate = self.sample_rate

        return audio_frame

    def stop(self):
        """停止流"""
        self._running = False


# ============================================================================
# 流式流水线调度器
# ============================================================================

class StreamingPipeline:
    """
    全链路异步流式流水线

    架构：
    ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
    │   LLM   │ ──> │ CosyVoice│ ──> │ SoulX    │ ──> │ WebRTC  │
    │Streaming│     │ Chunking │     │ Temporal │     │  UDP    │
    └─────────┘     └──────────┘     └──────────┘     └─────────┘
         │                │                 │
         └────────────────┴─────────────────┘
                     asyncio.Queue (内存共享)
    """

    def __init__(self, config: StreamingConfig):
        self.config = config

        # 内存队列（零拷贝）
        self.audio_queue: asyncio.Queue[Optional[np.ndarray]] = asyncio.Queue(maxsize=10)

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 延迟追踪
        self.start_time: Optional[float] = None
        self.first_audio_time: Optional[float] = None
        self.first_video_time: Optional[float] = None

        # 状态
        self._is_running = False
        self._tasks: list[asyncio.Task] = []

    async def process(
        self,
        text_stream: AsyncIterator[str],
        tts_engine,
        soulx_engine,
        video_track: StreamingVideoTrack,
        audio_track: StreamingAudioTrack,
    ):
        """
        处理流式输入

        Args:
            text_stream: LLM 流式输出
            tts_engine: TTS 引擎 (CosyVoice)
            soulx_engine: 视频引擎 (SoulX)
            video_track: WebRTC 视频轨道
            audio_track: WebRTC 音频轨道
        """
        self._is_running = True
        self.start_time = time.time()

        logger.info("🚀 启动全链路流式流水线")

        try:
            # 并行任务
            tasks = [
                asyncio.create_task(self._tts_worker(text_stream, tts_engine, audio_track)),
                asyncio.create_task(self._video_worker(soulx_engine, video_track))
            ]

            self._tasks = tasks

            # 等待完成
            await asyncio.gather(*tasks)

            # 报告延迟
            self._report_latency()

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self._is_running = False

    async def _tts_worker(
        self,
        text_stream: AsyncIterator[str],
        tts_engine,
        audio_track: StreamingAudioTrack,
    ):
        """
        TTS 工作线程 - 流式切片

        特性：
        - 收到文本立即合成
        - 切片大小 150-200ms
        - 推送到音频轨道和视频队列
        """
        logger.info("[TTS] 启动流式 TTS (Chunk Size: {} samples)".format(
            self.config.audio_chunk_size
        ))

        text_buffer = ""
        chunk_count = 0

        try:
            async for text_chunk in text_stream:
                text_buffer += text_chunk

                # 检查是否有足够文本
                if len(text_buffer) >= 5:  # 至少 5 个字符
                    # 合成音频
                    audio = await self._synthesize_async(tts_engine, text_buffer)

                    if audio is not None and len(audio) > 0:
                        chunk_count += 1

                        if self.first_audio_time is None:
                            self.first_audio_time = time.time()
                            latency = (self.first_audio_time - self.start_time) * 1000
                            logger.success(f"[TTS] 🎵 首包延迟: {latency:.0f}ms")

                        # 推送到音频轨道
                        await audio_track.add_audio(audio)

                        # 推送到视频队列
                        await self.audio_queue.put(audio)

                        logger.debug(f"[TTS] Chunk #{chunk_count}: {len(audio)} samples")

                        text_buffer = ""

            # 处理剩余文本
            if text_buffer:
                audio = await self._synthesize_async(tts_engine, text_buffer)
                if audio is not None:
                    await audio_track.add_audio(audio)
                    await self.audio_queue.put(audio)

            # 发送结束信号
            await self.audio_queue.put(None)

            logger.success(f"[TTS] ✅ 完成，生成 {chunk_count} 个切片")

        except Exception as e:
            logger.error(f"[TTS] 错误: {e}")
            await self.audio_queue.put(None)
            raise

    async def _video_worker(
        self,
        soulx_engine,
        video_track: StreamingVideoTrack,
    ):
        """
        视频工作线程 - 使用 SoulX 流式引擎

        特性：
        - 收到音频立即生成
        - 使用引擎内部 deque 缓存
        - 增量生成，输出 24 帧/块
        """
        logger.info("[Video] 启动流式视频生成 (SoulX Streaming)")

        frame_count = 0
        chunk_count = 0

        # 音频块生成器
        async def audio_chunk_generator():
            """生成音频块"""
            nonlocal chunk_count
            while self._is_running:
                audio_chunk = await self.audio_queue.get()
                if audio_chunk is None:
                    break
                chunk_count += 1
                yield audio_chunk

        try:
            # 使用 SoulX 流式引擎
            if hasattr(soulx_engine, 'process_audio_stream'):
                # 使用流式引擎
                logger.info("[Video] 使用 FlashHeadStreamingEngine 流式模式")

                async for video_frames in soulx_engine.process_audio_stream(
                    audio_chunk_generator()
                ):
                    # video_frames: [N, 3, H, W]
                    frames_np = video_frames.cpu().numpy()

                    # 转换为 [N, H, W, 3] RGB
                    for i in range(frames_np.shape[0]):
                        frame = np.transpose(frames_np[i], (1, 2, 0))

                        # 缩放到 [0, 255]
                        if frame.max() <= 1.0:
                            frame = (frame * 255).astype(np.uint8)
                        else:
                            frame = frame.astype(np.uint8)

                        await video_track.add_frame(frame)
                        frame_count += 1

                        # 记录首帧延迟
                        if self.first_video_time is None:
                            self.first_video_time = time.time()
                            latency = (self.first_video_time - self.start_time) * 1000
                            logger.success(f"[Video] 🎬 首帧延迟: {latency:.0f}ms")

                    logger.debug(f"[Video] 块 {chunk_count}: 生成 {video_frames.shape[0]} 帧")

            else:
                # 使用传统引擎
                logger.warning("[Video] 使用非流式引擎（降级模式）")
                audio_context = deque(maxlen=self.config.temporal_cache_size)

                while self._is_running:
                    audio_chunk = await self.audio_queue.get()
                    if audio_chunk is None:
                        break

                    audio_context.extend(audio_chunk)

                    min_samples = int(16000 / self.config.fps)

                    if len(audio_context) >= min_samples:
                        frames = await self._generate_video_async(
                            soulx_engine,
                            np.array(list(audio_context))
                        )

                        if frames is not None:
                            if self.first_video_time is None:
                                self.first_video_time = time.time()
                                latency = (self.first_video_time - self.start_time) * 1000
                                logger.success(f"[Video] 🎬 首帧延迟: {latency:.0f}ms")

                            for frame in frames:
                                await video_track.add_frame(frame)
                                frame_count += 1

                        overlap_samples = int(16000 / self.config.fps * self.config.overlap_frames)
                        while len(audio_context) > overlap_samples:
                            audio_context.popleft()

            logger.success(f"[Video] ✅ 完成，生成 {frame_count} 帧")

        except Exception as e:
            logger.error(f"[Video] 错误: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def _synthesize_async(self, tts_engine, text: str) -> Optional[np.ndarray]:
        """异步合成音频"""
        loop = asyncio.get_event_loop()

        def _synthesize():
            try:
                return tts_engine.synthesize(text)
            except Exception as e:
                logger.error(f"TTS error: {e}")
                return None

        return await loop.run_in_executor(self.executor, _synthesize)

    async def _generate_video_async(self, soulx_engine, audio: np.ndarray):
        """异步生成视频"""
        loop = asyncio.get_event_loop()

        def _generate():
            try:
                return soulx_engine.process_audio(audio, 16000)
            except Exception as e:
                logger.error(f"Video generation error: {e}")
                return None

        return await loop.run_in_executor(self.executor, _generate)

    def _report_latency(self):
        """报告延迟指标"""
        if self.start_time is None:
            return

        logger.info("")
        logger.info("=" * 50)
        logger.info("📊 延迟报告")
        logger.info("=" * 50)

        if self.first_audio_time:
            audio_latency = (self.first_audio_time - self.start_time) * 1000
            logger.info(f"🎵 首包音频延迟: {audio_latency:.0f}ms")
            status = "✅" if audio_latency < 300 else "⚠️"
            logger.info(f"   状态: {status} (目标: < 300ms)")

        if self.first_video_time:
            video_latency = (self.first_video_time - self.start_time) * 1000
            logger.info(f"🎬 首帧视频延迟: {video_latency:.0f}ms")
            status = "✅" if video_latency < 300 else "⚠️"
            logger.info(f"   状态: {status} (目标: < 300ms)")

        if self.first_audio_time and self.first_video_time:
            sync_delay = abs(self.first_video_time - self.first_audio_time) * 1000
            logger.info(f"🎯 音画同步误差: {sync_delay:.0f}ms")
            status = "✅" if sync_delay < 20 else "⚠️"
            logger.info(f"   状态: {status} (目标: < 20ms)")

        logger.info("=" * 50)
        logger.info("")

    def stop(self):
        """停止流水线"""
        self._is_running = False

        for task in self._tasks:
            if not task.done():
                task.cancel()

        self.executor.shutdown(wait=False)
