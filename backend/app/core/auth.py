"""
JWT 认证模块

提供 JWT token 验证和用户认证功能
"""
import os
import jwt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from loguru import logger
from passlib.context import CryptContext


class JWTAuth:
    """JWT 认证管理器"""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )

        if not self.secret_key:
            # 生成随机密钥
            import secrets
            self.secret_key = secrets.token_urlsafe(32)
            logger.warning("⚠️  JWT_SECRET_KEY 未配置，使用临时密钥")

        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌

        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量

        Returns:
            JWT token 字符串
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict]:
        """
       验证 JWT token

        Args:
            token: JWT token 字符串

        Returns:
            解码后的 payload，验证失败返回 None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token 已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的 Token: {e}")
            return None

    def decode_token(self, token: str) -> Optional[Dict]:
        """
        解码 token（不验证过期时间）

        Args:
            token: JWT token 字符串

        Returns:
            解码后的 payload
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            return payload
        except jwt.InvalidTokenError as e:
            logger.error(f"Token 解码失败: {e}")
            return None


# 全局实例
jwt_auth = JWTAuth()


def verify_websocket_token(token: str) -> Optional[Dict]:
    """
    验证 WebSocket 连接的 token

    Args:
        token: JWT token 字符串

    Returns:
        验证成功返回用户信息，失败返回 None
    """
    if not token:
        return None

    payload = jwt_auth.verify_token(token)
    if not payload:
        return None

    # 检查是否包含必要的用户信息
    if "sub" not in payload:
        logger.warning("Token 缺少 subject 声明")
        return None

    return payload


def create_user_token(user_id: str, **extra_data) -> str:
    """
    为用户创建 token

    Args:
        user_id: 用户 ID
        **extra_data: 额外的数据

    Returns:
        JWT token 字符串
    """
    data = {"sub": user_id, **extra_data}
    return jwt_auth.create_access_token(data)
