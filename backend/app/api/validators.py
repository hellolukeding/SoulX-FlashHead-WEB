"""
输入验证模型

使用 Pydantic 进行严格的输入验证
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
import re
import base64


class AudioMessage(BaseModel):
    """音频消息验证"""

    audio_data: str = Field(
        ...,
        min_length=1,
        max_length=10 * 1024 * 1024,  # 10MB
        description="Base64 编码的音频数据"
    )

    audio_format: str = Field(
        default="wav",
        regex="^(wav|mp3|ogg|opus|flac)$",
        description="音频格式"
    )

    @validator('audio_data')
    def validate_audio_base64(cls, v):
        """验证 Base64 编码"""
        try:
            # 检查是否为有效的 Base64
            decoded = base64.b64decode(v)
            # 检查解码后是否为空
            if len(decoded) == 0:
                raise ValueError("音频数据为空")
            return v
        except Exception:
            raise ValueError("无效的 Base64 编码")

    @validator('audio_data')
    def validate_audio_size(cls, v):
        """验证音频大小"""
        size_bytes = len(v) * 3 / 4  # Base64 解码后大约大小
        size_mb = size_bytes / (1024 * 1024)

        if size_mb > 10:  # 最大 10MB
            raise ValueError(f"音频过大: {size_mb:.1f}MB，最大允许 10MB")

        return v


class TextMessage(BaseModel):
    """文本消息验证"""

    text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="用户输入的文本"
    )

    @validator('text')
    def validate_text_content(cls, v):
        """验证文本内容"""
        if not v.strip():
            raise ValueError("文本不能为空")

        # 检查是否包含潜在的有害内容
        # 这里可以添加更多的验证规则
        return v


class CreateSessionMessage(BaseModel):
    """创建会话消息验证"""

    model_type: str = Field(
        default="lite",
        regex="^(lite|pro)$",
        description="模型类型"
    )

    reference_image: str = Field(
        ...,
        min_length=100,
        max_length=5 * 1024 * 1024,  # 5MB
        description="Base64 编码的参考图像"
    )

    @validator('reference_image')
    def validate_image_base64(cls, v):
        """验证图像 Base64 编码"""
        try:
            decoded = base64.b64decode(v)
            if len(decoded) < 100:
                raise ValueError("图像数据过小")
            return v
        except Exception:
            raise ValueError("无效的图像 Base64 编码")

    @validator('reference_image')
    def validate_image_format(cls, v):
        """验证图像格式"""
        # 检查是否为常见的图像格式
        # PNG: 89 50 4E 47
        # JPEG: FF D8 FF
        try:
            decoded = base64.b64decode(v)
            header = decoded[:8]

            if header[:4] == b'\x89PNG':
                return v
            elif header[:3] == b'\xFF\xD8\xFF':
                return v
            else:
                raise ValueError("不支持的图像格式，仅支持 PNG 和 JPEG")
        except Exception:
            raise ValueError("无法识别图像格式")


class UserMessage(BaseModel):
    """用户消息验证（音频或文本）"""

    message_type: str = Field(
        ...,
        regex="^(audio_chunk|text_message)$",
        description="消息类型"
    )

    data: dict = Field(..., description="消息数据")

    @validator('data')
    def validate_data_by_type(cls, v, values):
        """根据消息类型验证数据"""
        message_type = values.get('message_type')

        if message_type == "audio_chunk":
            # 验证音频消息
            return AudioMessage(**v).dict()

        elif message_type == "text_message":
            # 验证文本消息
            return TextMessage(**v).dict()

        else:
            raise ValueError(f"不支持的消息类型: {message_type}")


class WebSocketMessage(BaseModel):
    """WebSocket 消息基础验证"""

    type: str = Field(
        ...,
        description="消息类型"
    )

    data: Optional[dict] = Field(default_factory=dict, description="消息数据")

    @validator('type')
    def validate_message_type(cls, v):
        """验证消息类型"""
        valid_types = {
            "create_session",
            "user_message",
            "text_message",
            "audio_chunk",
            "pause_session",
            "resume_session",
            "close_session",
            "ping"
        }

        if v not in valid_types:
            raise ValueError(f"不支持的消息类型: {v}")

        return v
