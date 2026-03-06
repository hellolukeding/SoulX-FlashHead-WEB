"""
自定义异常类

定义项目中使用的所有自定义异常
"""
from typing import Optional


class DigitalHumanException(Exception):
    """数字人平台基础异常类"""

    def __init__(self, message: str, code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error": self.message,
            "code": self.code,
            "details": self.details
        }


class ASRError(DigitalHumanException):
    """ASR 语音识别相关错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code=400, details=details)


class LLMError(DigitalHumanException):
    """LLM 大模型相关错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code=500, details=details)


class TTSError(DigitalHumanException):
    """TTS 语音合成相关错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code=500, details=details)


class VideoGenerationError(DigitalHumanException):
    """视频生成相关错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code=500, details=details)


class AuthenticationError(DigitalHumanException):
    """认证相关错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code=401, details=details)


class ValidationError(DigitalHumanException):
    """输入验证错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code=400, details=details)


class RateLimitError(DigitalHumanException):
    """速率限制错误"""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, code=429, details=details)


class ResourceExhaustedError(DigitalHumanException):
    """资源耗尽错误"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code=503, details=details)
