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
            # SoulX-FlashHead 要求编码后的序列长度必须是 36 的倍数
            # seq_len = audio_length * fps / sr = audio_length * 25 / 16000
            # 需要 seq_len % 36 == 0
            # 因此 audio_length = n * 36 * 16000 / 25 = n * 23040
            #
            # 计算当前音频长度
            current_length = len(audio_data)
            target_chunk_size = 23040  # 36 * 16000 / 25

            # 计算需要填充的长度
            remainder = current_length % target_chunk_size
            if remainder != 0:
                padding_needed = target_chunk_size - remainder
                audio_data = np.concatenate([
                    audio_data,
                    np.zeros(padding_needed, dtype=np.float32)
                ])
                logger.info(f"[FlashHead] 音频填充: {current_length} → {len(audio_data)} samples (增加 {padding_needed})")

            logger.info(f"[FlashHead] 音频长度: {len(audio_data)} samples ({len(audio_data)/16000:.2f}秒)")

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
        logger.info("模型已卸载")
