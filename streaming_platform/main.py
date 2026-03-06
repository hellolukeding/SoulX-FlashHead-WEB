"""
数字人平台 - 全链路异步流式 WebRTC 架构

主入口文件
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# 创建 FastAPI 应用
app = FastAPI(
    title="Digital Human Streaming Platform",
    description="全链路异步流式 WebRTC 架构",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Digital Human Streaming Platform",
        "version": "1.0.0",
        "status": "running",
        "architecture": "Full-Stack Streaming with WebRTC",
        "components": {
            "audio_engine": "CosyVoice Streaming TTS",
            "video_engine": "SoulX-FlashHead Streaming",
            "transport": "WebRTC (UDP)",
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    logger.info("🚀 启动数字人流式平台...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
        log_level="info"
    )
