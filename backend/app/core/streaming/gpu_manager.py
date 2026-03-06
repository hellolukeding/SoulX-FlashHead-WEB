import torch
from typing import Set, Dict
from loguru import logger


class GPUMemoryManager:
    """
    GPU 内存管理器

    管理 GPU 资源分配和并发控制
    """

    def __init__(self, max_sessions: int = 5):
        """
        初始化 GPU 管理器

        Args:
            max_sessions: 最大并发会话数
        """
        self.max_sessions = max_sessions
        self.allocated_sessions: Set[str] = set()

    def can_allocate_session(self) -> bool:
        """
        检查是否可以分配新会话

        Returns:
            是否可以分配
        """
        # 检查会话数限制
        if len(self.allocated_sessions) >= self.max_sessions:
            logger.warning(f"Max session limit reached: {self.max_sessions}")
            return False

        # 检查 GPU 内存使用
        if torch.cuda.is_available():
            used = torch.cuda.memory_allocated() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            utilization = used / total

            if utilization > 0.9:  # 90% 阈值
                logger.warning(f"GPU memory usage too high: {utilization:.1%}")
                return False

        return True

    def allocate_session(self, session_id: str):
        """
        分配 GPU 资源

        Args:
            session_id: 会话 ID
        """
        if not self.can_allocate_session():
            raise RuntimeError(f"Cannot allocate session: max limit reached")

        self.allocated_sessions.add(session_id)
        logger.info(f"GPU resources allocated: {session_id}")

    def free_session(self, session_id: str):
        """
        释放 GPU 资源

        Args:
            session_id: 会话 ID
        """
        if session_id in self.allocated_sessions:
            self.allocated_sessions.discard(session_id)

            # 清理 GPU 缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"GPU resources freed: {session_id}")

    def get_memory_info(self) -> Dict:
        """
        获取 GPU 内存信息

        Returns:
            内存信息字典
        """
        if not torch.cuda.is_available():
            return {
                "available": False,
                "allocated_sessions": len(self.allocated_sessions)
            }

        used = torch.cuda.memory_allocated() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3

        return {
            "available": True,
            "allocated_sessions": len(self.allocated_sessions),
            "used_gb": round(used, 2),
            "total_gb": round(total, 2),
            "utilization": round(used / total, 2)
        }
