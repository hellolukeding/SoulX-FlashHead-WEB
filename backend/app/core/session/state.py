"""
会话状态管理
"""
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class SessionStatus(Enum):
    """会话状态枚举"""
    CREATING = "creating"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class SessionState:
    """
    会话状态数据类

    跟踪会话的所有状态信息
    """

    # 基本信息
    session_id: str
    status: str = SessionStatus.CREATING.value
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    # 模型配置
    model_type: str = "lite"
    reference_image: Optional[str] = None

    # 统计信息
    audio_chunks_received: int = 0
    video_frames_generated: int = 0
    total_audio_duration: float = 0.0

    # 性能指标
    average_latency_ms: float = 0.0
    last_latency_ms: float = 0.0
    fps: float = 0.0

    # 错误信息
    last_error: Optional[str] = None

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = time.time()

    def get_uptime(self) -> float:
        """获取会话运行时长（秒）"""
        return time.time() - self.created_at

    def get_idle_time(self) -> float:
        """获取空闲时长（秒）"""
        return time.time() - self.last_activity

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "uptime": self.get_uptime(),
            "idle_time": self.get_idle_time(),
            "model_type": self.model_type,
            "audio_chunks_received": self.audio_chunks_received,
            "video_frames_generated": self.video_frames_generated,
            "average_latency_ms": self.average_latency_ms,
            "fps": self.fps,
            "last_error": self.last_error
        }


class SessionManager:
    """
    会话管理器

    管理所有会话的创建、删除和状态更新
    """

    def __init__(self):
        self.sessions: dict[str, SessionState] = {}
        self.max_sessions = 5  # 最大并发会话数

    def create_session(self, session_id: str) -> SessionState:
        """
        创建新会话

        Args:
            session_id: 会话 ID

        Returns:
            会话状态
        """
        if len(self.sessions) >= self.max_sessions:
            raise Exception(f"达到最大会话数限制: {self.max_sessions}")

        session = SessionState(session_id=session_id)
        self.sessions[session_id] = session

        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        获取会话

        Args:
            session_id: 会话 ID

        Returns:
            会话状态或 None
        """
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs):
        """
        更新会话状态

        Args:
            session_id: 会话 ID
            **kwargs: 要更新的字段
        """
        session = self.get_session(session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.update_activity()

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否删除成功
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list:
        """
        列出所有会话

        Returns:
            会话列表
        """
        return [session.to_dict() for session in self.sessions.values()]

    def get_active_count(self) -> int:
        """
        获取活跃会话数

        Returns:
            活跃会话数
        """
        return len([
            s for s in self.sessions.values()
            if s.status in [SessionStatus.READY.value, SessionStatus.ACTIVE.value]
        ])

    def cleanup_idle_sessions(self, max_idle_time: float = 300):
        """
        清理空闲会话

        Args:
            max_idle_time: 最大空闲时间（秒）

        Returns:
            清理的会话数
        """
        to_remove = []

        for session_id, session in self.sessions.items():
            if session.get_idle_time() > max_idle_time:
                to_remove.append(session_id)

        for session_id in to_remove:
            self.delete_session(session_id)

        return len(to_remove)
