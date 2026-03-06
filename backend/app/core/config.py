"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用设置
    APP_NAME: str = "Digital Human Platform"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:1420",
        "tauri://localhost"
    ]

    # 模型配置
    MODEL_PATH: str = "/opt/digital-human-platform/models"
    FLASHHEAD_MODEL: str = "SoulX-FlashHead-1_3B"
    WAV2VEC_MODEL: str = "wav2vec2-base-960h"
    DEFAULT_MODEL_TYPE: str = "lite"  # lite 或 pro

    # 推理配置
    MAX_CONCURRENT_SESSIONS: int = 5
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    VIDEO_FPS: int = 25
    VIDEO_RESOLUTION: str = "512x512"

    # 缓冲配置
    AUDIO_BUFFER_SIZE: int = 2  # 秒
    VIDEO_BUFFER_SIZE: int = 10  # 帧

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # GPU 配置
    CUDA_VISIBLE_DEVICES: str = "0"

    # ==================== LLM 配置 ====================
    llm_model: str = "qwen-plus"
    openai_url: str = ""
    openai_api_key: str = ""

    # ==================== TTS 配置 ====================
    tts_type: str = "cosyvoice"  # cosyvoice, edge, doubao, tencent, azure
    edge_tts_voice: str = "zh-CN-YunxiNeural"
    cosyvoice_model: str = "CosyVoice-300M-SFT"
    cosyvoice_voice: str = "中文女"

    # ==================== ASR 配置 ====================
    asr_type: str = "mock"  # tencent, funasr, huber, lip, mock
    tencent_appid: str = ""
    tencent_asr_secret_id: str = ""
    tencent_asr_secret_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False  # 允许不区分大小写
        extra = "ignore"  # 忽略额外的字段
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()


# 模型路径
FLASHHEAD_MODEL_PATH = os.path.join(
    settings.MODEL_PATH,
    settings.FLASHHEAD_MODEL
)

WAV2VEC_MODEL_PATH = os.path.join(
    settings.MODEL_PATH,
    settings.WAV2VEC_MODEL
)

# 模型路径更新
COSYVOICE_PATH: str = "/opt/digital-human-platform/models/CosyVoice"
