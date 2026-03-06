"""
SoulX-FlashHead 实时流式推理引擎

基于官方 generate_video.py 的 stream 模式实现
支持实时视频流式生成（类似微信视频通话）

注意: 此模块必须在加载前切换到 SoulX-FlashHead 目录
"""
import sys
import os
import asyncio
from collections import deque
from typing import Optional, AsyncIterator
import numpy as np
import torch
import librosa
from loguru import logger
from dataclasses import dataclass

# 保存当前目录
_ORIGINAL_DIR = os.getcwd()

# 切换到 SoulX-FlashHead 目录
os.chdir('/opt/soulx/SoulX-FlashHead')

# 添加路径
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')

# 现在可以安全导入
from flash_head.inference import (
    get_pipeline,
    get_base_data,
    get_infer_params,
    get_audio_embedding,
    run_pipeline
)

# 恢复原始目录
os.chdir(_ORIGINAL_DIR)


@dataclass
class StreamingConfig:
    """流式推理配置"""
    model_type: str = "lite"
    audio_sample_rate: int = 16000
    video_fps: int = 25
    use_face_crop: bool = True
    seed: int = 42

    # 从官方实现继承的参数
    frame_num: int = 33  # 固定帧数
    motion_frames_num: int = 9  # 重叠帧数


class FlashHeadStreamingEngine:
    """
    SoulX-FlashHead 实时流式推理引擎

    使用滑动窗口算法实现实时视频生成：
    - Lite 模型: 24 帧步长 (frame_num - motion_frames_num = 33 - 9)
    - 每次生成 33 帧，移除前 9 帧重叠，输出 24 帧
    - 使用 deque 缓冲音频数据
    """

    def __init__(self, config: StreamingConfig):
        self.config = config
        self.pipeline = None
        self.is_loaded = False
        self.current_person = None
        self.original_dir = os.getcwd()  # 保存原始目录

        # 从官方实现获取参数
        self.infer_params = None
        self.slice_len = None
        self.cached_audio_duration = None

        # 音频缓冲队列
        self.audio_dq = None
        self.cached_audio_length_sum = None

        # 音频索引范围
        self.audio_start_idx = None
        self.audio_end_idx = None

        logger.info(f"初始化 FlashHead 流式引擎 (模型: {config.model_type})")

    def load_model(self, reference_image: str) -> bool:
        """
        加载模型并准备参考图像

        Args:
            reference_image: 参考图像路径

        Returns:
            是否加载成功
        """
        try:
            self.original_dir = os.getcwd()
            os.chdir('/opt/soulx/SoulX-FlashHead')

            logger.info("开始加载 SoulX-FlashHead 模型...")

            # 模型路径
            ckpt_dir = "/opt/digital-human-platform/models/SoulX-FlashHead-1_3B"
            wav2vec_dir = "/opt/digital-human-platform/models/wav2vec2-base-960h"

            logger.info(f"SoulX-FlashHead 模型路径: {ckpt_dir}")
            logger.info(f"wav2vec2 模型路径: {wav2vec_dir}")

            # 获取 pipeline
            self.pipeline = get_pipeline(
                world_size=1,
                ckpt_dir=ckpt_dir,
                model_type=self.config.model_type,
                wav2vec_dir=wav2vec_dir
            )

            # 准备参考图像
            get_base_data(
                self.pipeline,
                cond_image_path_or_dir=reference_image,
                base_seed=self.config.seed,
                use_face_crop=self.config.use_face_crop
            )

            # 获取推理参数
            self.infer_params = get_infer_params()
            self.frame_num = self.infer_params['frame_num']
            self.motion_frames_num = self.infer_params['motion_frames_num']
            self.slice_len = self.frame_num - self.motion_frames_num
            self.cached_audio_duration = self.infer_params['cached_audio_duration']
            tgt_fps = self.infer_params['tgt_fps']
            sample_rate = self.infer_params['sample_rate']

            logger.info(f"推理参数:")
            logger.info(f"  frame_num: {self.frame_num}")
            logger.info(f"  motion_frames_num: {self.motion_frames_num}")
            logger.info(f"  slice_len: {self.slice_len}")
            logger.info(f"  cached_audio_duration: {self.cached_audio_duration}")
            logger.info(f"  tgt_fps: {tgt_fps}")
            logger.info(f"  sample_rate: {sample_rate}")

            # 初始化音频缓冲队列
            self.cached_audio_length_sum = int(sample_rate * self.cached_audio_duration)
            self.audio_dq = deque([0.0] * self.cached_audio_length_sum,
                                  maxlen=self.cached_audio_length_sum)

            # 音频索引范围
            self.audio_end_idx = int(self.cached_audio_duration * tgt_fps)
            self.audio_start_idx = self.audio_end_idx - self.frame_num

            self.is_loaded = True
            self.current_person = reference_image

            logger.success("✅ 模型加载成功")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def process_audio_stream(
        self,
        audio_chunks: AsyncIterator[np.ndarray]
    ) -> AsyncIterator[torch.Tensor]:
        """
        流式处理音频并生成视频帧

        Args:
            audio_chunks: 音频块异步迭代器

        Yields:
            视频帧 tensor [frames, 3, height, width]
            每次输出 (frame_num - motion_frames_num) 帧
        """
        if not self.is_loaded:
            logger.error("模型未加载，请先调用 load_model()")
            return

        sample_rate = self.infer_params['sample_rate']
        slice_len_samples = self.slice_len * sample_rate // self.config.video_fps

        chunk_idx = 0
        async for audio_chunk in audio_chunks:
            # 确保音频是 float32
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)

            # 重采样到目标采样率
            if sample_rate != self.config.audio_sample_rate:
                audio_chunk = librosa.resample(
                    audio_chunk,
                    orig_sr=self.config.audio_sample_rate,
                    target_sr=sample_rate
                )

            # 添加到音频缓冲队列
            self.audio_dq.extend(audio_chunk.tolist())

            # 检查是否有足够的音频数据
            if len(self.audio_dq) < self.cached_audio_length_sum:
                logger.debug(f"[Stream-{chunk_idx}] 音频缓冲不足，等待更多数据...")
                continue

            # 将 deque 转换为 numpy array
            audio_array = np.array(self.audio_dq)

            # 获取音频嵌入
            audio_embedding = get_audio_embedding(
                self.pipeline,
                audio_array,
                self.audio_start_idx,
                self.audio_end_idx
            )

            # 生成视频
            video = run_pipeline(self.pipeline, audio_embedding)

            # 移除重叠帧
            video = video[self.motion_frames_num:]

            chunk_idx += 1
            logger.debug(f"[Stream-{chunk_idx}] 生成 {video.shape[0]} 帧")

            yield video

    def process_audio_complete(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000
    ) -> list:
        """
        处理完整音频并生成视频（用于测试）

        Args:
            audio_data: 音频数据
            sample_rate: 采样率

        Returns:
            视频帧列表
        """
        if not self.is_loaded:
            logger.error("模型未加载")
            return []

        try:
            # 重采样
            if sample_rate != self.infer_params['sample_rate']:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=self.infer_params['sample_rate']
                )

            tgt_fps = self.infer_params['tgt_fps']
            slice_len_samples = self.slice_len * self.infer_params['sample_rate'] // tgt_fps

            # 填充音频以避免最后一个块被截断
            remainder = len(audio_data) % slice_len_samples
            if remainder > 0:
                pad_length = slice_len_samples - remainder
                audio_data = np.concatenate([
                    audio_data,
                    np.zeros(pad_length, dtype=audio_data.dtype)
                ])

            # 分割音频
            human_speech_array_slices = audio_data.reshape(-1, slice_len_samples)

            logger.info(f"音频分为 {len(human_speech_array_slices)} 个块")

            generated_list = []

            for chunk_idx, human_speech_array in enumerate(human_speech_array_slices):
                # 流式编码音频块
                self.audio_dq.extend(human_speech_array.tolist())
                audio_array = np.array(self.audio_dq)

                audio_embedding = get_audio_embedding(
                    self.pipeline,
                    audio_array,
                    self.audio_start_idx,
                    self.audio_end_idx
                )

                # 推理
                video = run_pipeline(self.pipeline, audio_embedding)
                video = video[self.motion_frames_num:]

                generated_list.append(video.cpu())

                logger.info(f"块-{chunk_idx} 完成: {video.shape[0]} 帧")

            return generated_list

        except Exception as e:
            logger.error(f"音频处理失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def reset_buffer(self):
        """重置音频缓冲队列"""
        self.audio_dq = deque([0.0] * self.cached_audio_length_sum,
                              maxlen=self.cached_audio_length_sum)
        logger.info("音频缓冲队列已重置")

    def get_buffer_duration(self) -> float:
        """获取当前缓冲的音频时长（秒）"""
        return len(self.audio_dq) / self.infer_params['sample_rate']

    def unload(self):
        """卸载模型，释放内存"""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        self.is_loaded = False

        # 恢复工作目录
        try:
            os.chdir(original_dir)
        except:
            pass

        logger.info("模型已卸载")
