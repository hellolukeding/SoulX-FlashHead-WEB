"""
REST API 路由
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    """REST API 根路径"""
    return {
        "message": "REST API",
        "version": "1.0.0"
    }


@router.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy"
    }
