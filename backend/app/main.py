"""
FastAPI 应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.api.rest.routes import router as rest_router
from app.api.websocket.websocket import router as websocket_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Starting Digital Human Platform Backend...")

    # 检查 GPU 可用性
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.success(f"✅ GPU 可用: {gpu_name} ({gpu_memory:.1f} GB)")
        logger.info(f"   CUDA 版本: {torch.version.cuda}")
    else:
        logger.warning("⚠️  GPU 不可用，将使用 CPU（性能较差）")

    # 启动时初始化
    logger.success("✅ 应用初始化完成")

    yield

    # 关闭时清理
    logger.info("🛑 Shutting down Digital Human Platform Backend...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Digital Human Platform API",
    description="Real-time digital human video generation service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(rest_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Digital Human Platform",
        "version": "1.0.0",
        "status": "running",
        "message": "Real-time digital human platform backend"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    import torch
    return {
        "status": "healthy",
        "gpu_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🌐 Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
