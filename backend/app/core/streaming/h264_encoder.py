import av
import numpy as np
from typing import List, Optional
from loguru import logger


class H264Encoder:
    """
    H.264 视频编码器

    使用 GPU 加速 (NVENC) 或 CPU 编码
    """

    def __init__(
        self,
        fps: int = 25,
        bitrate: str = "2M",
        preset: str = "medium",
        tune: str = "zerolatency",
        gop_size: int = 25,
        force_cpu: bool = False
    ):
        """
        初始化编码器

        Args:
            fps: 帧率
            bitrate: 比特率
            preset: 质量预设
            tune: 调优选项
            gop_size: GOP 大小
            force_cpu: 强制使用 CPU 编码
        """
        self.fps = fps
        self.bitrate = bitrate
        self.preset = preset
        self.tune = tune
        self.gop_size = gop_size
        self.force_cpu = force_cpu

        self.codec = self._select_codec()
        self.encoder: Optional[av.CodecContext] = None
        self.width: Optional[int] = None
        self.height: Optional[int] = None

        logger.info(f"H264Encoder initialized: codec={self.codec}, fps={fps}")

    def _select_codec(self) -> str:
        """选择最佳编码器"""
        if self.force_cpu:
            return "libx264"

        # 尝试使用 NVENC
        try:
            codec = av.CodecContext.create("h264_nvenc", "w")
            logger.info("✅ NVIDIA NVENC available")
            return "h264_nvenc"
        except Exception as e:
            logger.warning(f"⚠️  NVENC not available, using CPU: {e}")
            return "libx264"

    def _create_encoder(self, width: int, height: int):
        """创建编码器实例"""
        if self.encoder is not None:
            if self.width == width and self.height == height:
                return  # 编码器已创建且尺寸匹配

        self.width = width
        self.height = height

        codec_context = av.CodecContext.create(self.codec, "w")
        codec_context.width = width
        codec_context.height = height
        codec_context.framerate = self.fps

        # 设置像素格式
        codec_context.pix_fmt = "yuv420p"

        # 简化比特率设置
        bitrate_value = int(float(self.bitrate.replace("M", "")) * 1_000_000)
        codec_context.bit_rate = bitrate_value

        # 设置 GOP
        codec_context.gop_size = self.gop_size

        # 根据编码器类型设置选项
        if self.codec == "h264_nvenc":
            # NVENC 使用更简单的参数
            codec_context.options = {
                "preset": "p1",  # 最快速度
                "tune": "ll",    # 低延迟
            }
        else:
            # libx264 使用标准参数
            codec_context.options = {
                "preset": "ultrafast",  # 最快速度
                "tune": "zerolatency",   # 零延迟
                "crf": "23",             # 恒定质量
            }

        try:
            codec_context.open()
            self.encoder = codec_context
        except Exception as e:
            logger.error(f"Failed to open encoder: {e}")
            # 如果 NVENC 失败，尝试 CPU fallback
            if self.codec == "h264_nvenc" and not self.force_cpu:
                logger.info("Falling back to CPU encoder")
                self.codec = "libx264"
                self.force_cpu = True
                self._create_encoder(width, height)
            else:
                raise

    def encode_frame(self, frame: np.ndarray) -> bytes:
        """
        编码单个视频帧

        Args:
            frame: RGB 图像 (H, W, 3) uint8

        Returns:
            H.264 编码数据包
        """
        self._create_encoder(frame.shape[1], frame.shape[0])

        # 转换 numpy 为 PyAV 帧
        av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")

        # 编码
        packets = self.encoder.encode(av_frame)

        # 合并所有包
        result = b""
        for packet in packets:
            result += bytes(packet)

        return result

    def encode_frames(self, frames: List[np.ndarray]) -> bytes:
        """
        批量编码视频帧

        Args:
            frames: RGB 图像列表

        Returns:
            拼接的 H.264 数据包
        """
        if len(frames) == 0:
            return b""

        self._create_encoder(frames[0].shape[1], frames[0].shape[0])

        result = b""

        for frame in frames:
            av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            packets = self.encoder.encode(av_frame)

            for packet in packets:
                result += bytes(packet)

        # 刷新编码器
        packets = self.encoder.encode(None)
        for packet in packets:
            result += bytes(packet)

        return result

    def encode_frames_with_keyframe(self, frames: List[np.ndarray]) -> bytes:
        """
        批量编码视频帧，确保第一个帧是关键帧

        用于流式视频生成，确保每个片段可以独立解码。

        Args:
            frames: RGB 图像列表

        Returns:
            拼接的 H.264 数据包（首帧为关键帧）
        """
        if len(frames) == 0:
            return b""

        # 强制重新创建编码器以确保首帧是关键帧
        if self.encoder is not None:
            self.encoder.close()
            self.encoder = None

        self._create_encoder(frames[0].shape[1], frames[0].shape[0])

        result = b""

        for i, frame in enumerate(frames):
            av_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")

            # 强制第一帧为关键帧
            if i == 0:
                av_frame.pict_type = av.VideoPictureType.I

            packets = self.encoder.encode(av_frame)

            for packet in packets:
                result += bytes(packet)

        # 刷新编码器
        packets = self.encoder.encode(None)
        for packet in packets:
            result += bytes(packet)

        return result

    def close(self):
        """关闭编码器"""
        if self.encoder is not None:
            self.encoder.close()
            self.encoder = None
            self.width = None
            self.height = None
