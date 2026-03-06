"""
SoulX-FlashHead 推理引擎封装 - 修复版
"""
import sys
import os

# 添加 SoulX-FlashHead 路径
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')

import torch
import numpy as np
import librosa
from typing import Optional, Dict, Any, Tuple
from loguru import logger
from dataclasses import dataclass

from flash_head.inference import (
    get_pipeline,
    get_base_data,
    get_audio_embedding,
    run_pipeline
)


@dataclass
class InferenceConfig:
    """推理配置"""
    model_type: str = "lite"  # lite 或 pro
    audio_sample_rate: int = 16000
    video_fps: int = 25
    video_resolution: Tuple[int, int] = (512, 512)
    use_face_crop: bool = True
    seed: int = 42


class FlashHeadInferenceEngine:
    """
    SoulX-FlashHead 推理引擎

    封装 SoulX-FlashHead 模型，提供简洁的推理接口
    """

    def __init__(self, config: InferenceConfig):
        """
        初始化推理引擎

        Args:
            config: 推理配置
        """
        self.config = config
        self.pipeline = None
        self.is_loaded = False
        self.current_person = None

        logger.info(f"初始化 FlashHead 推理引擎 (模型: {config.model_type})")

    def load_model(self, reference_image: str) -> bool:
        """
        加载模型并准备参考图像

        Args:
            reference_image: 参考图像路径

        Returns:
            是否加载成功
        """
        try:
            # 🔧 修复：切换到 SoulX-FlashHead 目录以解决相对路径问题
            original_dir = os.getcwd()
            os.chdir('/opt/soulx/SoulX-FlashHead')
            
            logger.info("开始加载 SoulX-FlashHead 模型...")

            # 模型路径 - 使用项目的 models 目录
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

            self.is_loaded = True
            self.current_person = reference_image

            logger.success("✅ 模型加载成功")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            return False

    def process_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000
    ) -> Optional[torch.Tensor]:
        """
        处理音频并生成视频帧

        Args:
            audio_data: 音频数据 (numpy array, shape: [samples])
            sample_rate: 采样率

        Returns:
            视频帧 tensor [frames, 3, height, width] 或 None
        """
        if not self.is_loaded:
            logger.error("模型未加载，请先调用 load_model()")
            return None

        try:
            # 重采样音频到 16kHz
            if sample_rate != self.config.audio_sample_rate:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=self.config.audio_sample_rate
                )

            # 🔧 修复音频长度问题
            # SoulX-FlashHead 要求固定的 frame_num = 33
            # 模型内部使用固定的帧数，音频必须对应 33 帧
            #
            # 33 帧对应的音频长度: 33 * 16000 / 25 = 21120 samples (1.32秒)
            #
            FRAME_NUM = 33
            TARGET_AUDIO_SAMPLES = FRAME_NUM * 16000 // 25  # 21120 samples
            
            current_length = len(audio_data)
            
            # 截取或填充到固定长度
            if current_length >= TARGET_AUDIO_SAMPLES:
                # 截取前 33 帧对应的音频
                audio_data = audio_data[:TARGET_AUDIO_SAMPLES]
                logger.info(f"[FlashHead] 音频截取: {current_length} → {len(audio_data)} samples")
            else:
                # 填充到 33 帧
                padding_needed = TARGET_AUDIO_SAMPLES - current_length
                audio_data = np.concatenate([
                    audio_data,
                    np.zeros(padding_needed, dtype=np.float32)
                ])
                logger.info(f"[FlashHead] 音频填充: {current_length} → {len(audio_data)} samples (增加 {padding_needed})")

            # 验证
            video_length = int(len(audio_data) * 25 / 16000)
            logger.info(f"[FlashHead] 音频长度: {len(audio_data)} samples ({len(audio_data)/16000:.2f}秒), video_length: {video_length}")
            logger.info(f"[FlashHead] 验证: video_length == 33 ? {video_length == FRAME_NUM}")

            # 获取音频嵌入
            audio_embedding = get_audio_embedding(self.pipeline, audio_data)

            # 生成视频
            video_frames = run_pipeline(self.pipeline, audio_embedding)

            return video_frames

        except Exception as e:
            logger.error(f"音频处理失败: {e}")
            return None

    def process_audio_file(
        self,
        audio_path: str
    ) -> Optional[torch.Tensor]:
        """
        处理音频文件并生成视频帧

        Args:
            audio_path: 音频文件路径

        Returns:
            视频帧 tensor 或 None
        """
        try:
            # 加载音频
            audio_data, sr = librosa.load(
                audio_path,
                sr=self.config.audio_sample_rate,
                mono=True
            )

            logger.info(f"加载音频: {audio_path} (时长: {len(audio_data)/sr:.2f}秒)")

            # 处理音频
            return self.process_audio(audio_data, sr)

        except Exception as e:
            logger.error(f"音频文件处理失败: {e}")
            return None

    def process_audio_streaming(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        chunk_duration: float = 1.32
    ):
        """
        流式处理音频并生成视频帧（分段生成）

        将长音频分成多个片段，每个片段生成独立的视频。
        这样可以更快地返回第一帧视频。

        Args:
            audio_data: 音频数据 (numpy array, shape: [samples])
            sample_rate: 采样率
            chunk_duration: 每段视频的时长（秒），默认 1.32秒（33帧）

        Yields:
            dict: {
                'chunk_index': int,
                'total_chunks': int,
                'video_frames': torch.Tensor,
                'audio_chunk': np.ndarray,
                'duration': float
            }
        """
        if not self.is_loaded:
            logger.error("模型未加载，请先调用 load_model()")
            return

        try:
            # 重采样音频到 16kHz
            if sample_rate != self.config.audio_sample_rate:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=self.config.audio_sample_rate
                )

            FRAME_NUM = 33
            TARGET_AUDIO_SAMPLES = FRAME_NUM * 16000 // 25  # 21120 samples (1.32秒)

            total_samples = len(audio_data)
            chunk_count = int(np.ceil(total_samples / TARGET_AUDIO_SAMPLES))

            logger.info(f"[FlashHead Streaming] 总音频: {total_samples} samples ({total_samples/16000:.2f}秒)")
            logger.info(f"[FlashHead Streaming] 将生成 {chunk_count} 个视频片段")

            # 分段处理
            for i in range(chunk_count):
                start_idx = i * TARGET_AUDIO_SAMPLES
                end_idx = min(start_idx + TARGET_AUDIO_SAMPLES, total_samples)
                audio_chunk = audio_data[start_idx:end_idx]

                # 如果是最后一段且不足 TARGET_AUDIO_SAMPLES，填充
                if len(audio_chunk) < TARGET_AUDIO_SAMPLES:
                    padding_needed = TARGET_AUDIO_SAMPLES - len(audio_chunk)
                    audio_chunk = np.concatenate([
                        audio_chunk,
                        np.zeros(padding_needed, dtype=np.float32)
                    ])
                    logger.info(f"[FlashHead Streaming] 最后一段填充: {padding_needed} samples")

                logger.info(f"[FlashHead Streaming] 处理片段 {i+1}/{chunk_count}: {len(audio_chunk)} samples")

                # 获取音频嵌入
                audio_embedding = get_audio_embedding(self.pipeline, audio_chunk)

                # 生成视频帧
                video_frames = run_pipeline(self.pipeline, audio_embedding)

                if video_frames is not None:
                    yield {
                        'chunk_index': i,
                        'total_chunks': chunk_count,
                        'video_frames': video_frames,
                        'audio_chunk': audio_chunk,
                        'duration': len(audio_chunk) / 16000
                    }
                else:
                    logger.warning(f"[FlashHead Streaming] 片段 {i+1} 生成失败")

        except Exception as e:
            logger.error(f"[FlashHead Streaming] 流式音频处理失败: {e}")
            raise

    def change_person(self, reference_image: str) -> bool:
        """
        切换参考人物

        Args:
            reference_image: 新的参考图像路径

        Returns:
            是否切换成功
        """
        try:
            get_base_data(
                self.pipeline,
                cond_image_path_or_dir=reference_image,
                base_seed=self.config.seed,
                use_face_crop=self.config.use_face_crop
            )

            self.current_person = reference_image
            logger.info(f"✅ 参考人物已切换: {reference_image}")
            return True

        except Exception as e:
            logger.error(f"❌ 切换人物失败: {e}")
            return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            性能指标字典
        """
        if not self.is_loaded:
            return {}

        try:
            # GPU 内存使用
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_allocated() / 1024**3  # GB
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            else:
                gpu_memory = 0
                gpu_memory_total = 0

            return {
                "model_loaded": self.is_loaded,
                "model_type": self.config.model_type,
                "current_person": self.current_person,
                "gpu_memory_gb": round(gpu_memory, 2),
                "gpu_memory_total_gb": round(gpu_memory_total, 2),
                "gpu_utilization": round(gpu_memory / gpu_memory_total * 100, 1) if gpu_memory_total > 0 else 0
            }

        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {}

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
