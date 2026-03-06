"""
速率限制中间件

防止 API 滥用和 DDoS 攻击
"""
import time
from collections import defaultdict
from functools import wraps
from fastapi import Request, HTTPException
from loguru import logger


class RateLimiter:
    """简单的速率限制器"""

    def __init__(self):
        # 存储每个客户端的请求记录
        # 格式: {client_id: [(timestamp, timestamp, ...), ...]}
        self.requests = defaultdict(list)
        self.window_size = 60  # 时间窗口（秒）
        self.max_requests = 60  # 最大请求数

    def is_allowed(self, client_id: str) -> bool:
        """
        检查客户端是否允许请求

        Args:
            client_id: 客户端标识

        Returns:
            是否允许请求
        """
        current_time = time.time()

        # 清理过期的请求记录
        self._cleanup_expired_requests(client_id, current_time)

        # 检查当前窗口内的请求数
        request_times = self.requests[client_id]
        count = len(request_times)

        if count >= self.max_requests:
            logger.warning(f"速率限制触发: {client_id}")
            return False

        # 记录本次请求
        self.requests[client_id].append(current_time)
        return True

    def _cleanup_expired_requests(self, client_id: str, current_time: float):
        """清理过期的请求记录"""
        cutoff_time = current_time - self.window_size

        # 只保留时间窗口内的请求
        self.requests[client_id] = [
            timestamp for timestamp in self.requests[client_id]
            if timestamp > cutoff_time
        ]

    def get_retry_after(self, client_id: str) -> int:
        """
        获取重试等待时间（秒）

        Args:
            client_id: 客户端标识

        Returns:
            需要等待的秒数
        """
        current_time = time.time()
        request_times = self.requests[client_id]

        if not request_times:
            return 0

        # 找到最早的请求
        oldest_request = min(request_times)
        window_start = oldest_request + self.window_size

        retry_after = int(window_start - current_time)
        return max(0, retry_after)


# 全局速率限制器实例
rate_limiter = RateLimiter()


def rate_limit(request_per_minute: int = 60, request_per_hour: int = 1000):
    """
    速率限制装饰器

    Args:
        request_per_minute: 每分钟最大请求数
        request_per_hour: 每小时最大请求数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中获取客户端标识
            # 对于 WebSocket，使用 session_id
            # 对于 HTTP，使用 IP 地址
            request = kwargs.get('request')
            if request:
                client_id = request.client.host if hasattr(request.client, 'host') else 'unknown'
            else:
                client_id = 'default'

            limiter = RateLimiter()
            limiter.max_requests = request_per_minute

            if not limiter.is_allowed(client_id):
                retry_after = limiter.get_retry_after(client_id)
                raise HTTPException(
                    status_code=429,
                    detail="速率限制",
                    headers={"Retry-After": str(retry_after)}
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


class ConnectionRateLimiter:
    """连接数限制器"""

    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.active_connections = set()

    def can_connect(self, connection_id: str) -> bool:
        """
        检查是否允许新连接

        Args:
            connection_id: 连接标识

        Returns:
            是否允许连接
        """
        # 清理断开的连接
        self.active_connections.discard(connection_id)

        # 检查连接数限制
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"连接数达到上限: {self.max_connections}")
            return False

        self.active_connections.add(connection_id)
        return True

    def disconnect(self, connection_id: str):
        """
        断开连接

        Args:
            connection_id: 连接标识
        """
        self.active_connections.discard(connection_id)


# 全局连接限制器
connection_limiter = ConnectionRateLimiter(max_connections=100)
