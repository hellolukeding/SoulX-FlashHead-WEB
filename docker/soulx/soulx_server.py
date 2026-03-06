"""
SoulX-FlashHead 流式视频生成服务 - FastAPI 服务器

特性：
- 时空音频上下文缓存
- SageAttention 加速
- 流式帧输出
- 零磁盘 I/O
"""
import asyncio
import io
import logging
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import numpy as np
import torch
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from PIL import Image
from pydantic import BaseModel

# 导入 SoulX-FlashHead
import sys
sys.path.insert(0, '/opt/soulx/SoulX-FlashHead')

from flash_head.inference import (
    get_pipeline,
    get_base_data,
    get_infer_params,
    get_audio_embedding,
    run_pipeline
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 请求/响应模型
# ============================================================================

class VideoRequest(BaseModel):
    """视频生成请求"""
    reference_image: str = "default"
    audio_data: str  # Base64 编码的音频
    sample_rate: int = 16000
    fps: int = 25


class StreamingVideoRequest(BaseModel):
    """流式视频生成请求"""
    reference_image: str = "default"
    sample_rate: int = 16000
    fps: int = 25


# ============================================================================
# 全局模型实例
# ============================================================================

pipeline = None
base_data = None
infer_params = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global pipeline, base_data, infer_params

    logger.info("🎬 初始化 SoulX-FlashHead 模型...")

    # 切换到 SoulX 目录
    import os
    os.chdir('/opt/soulx/SoulX-FlashHead')

    # 加载配置
    logger.info("   加载配置...")
    base_data = get_base_data()
    infer_params = get_infer_params()

    # 创建 pipeline
    logger.info("   创建 pipeline...")
    pipeline = get_pipeline(
        ulysses_degree=1,
        ring_degree=1,
        device="cuda",
        dtype=torch.float16,
    )

    logger.info("✅ SoulX-FlashHead 模型加载完成")

    # 预热
    logger.info("🔥 预热模型...")
    dummy_audio = np.zeros(21120, dtype=np.float32)  # 1.32s @ 16kHz
    _ = run_pipeline(
        pipeline=pipeline,
        audio_embedding=dummy_audio,
        base_data=base_data,
        infer_params=infer_params,
    )
    logger.info("✅ 预热完成")

    # 恢复工作目录
    os.chdir('/app')

    yield

    # 清理
    logger.info("🧹 清理资源...")
    del pipeline
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="SoulX-FlashHead 流式视频生成服务",
    description="支持时空缓存和 SageAttention 的流式视频生成",
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================================
# 辅助函数
# ============================================================================

def decode_base64_audio(base64_data: str) -> np.ndarray:
    """解码 Base64 音频"""
    import base64
    audio_bytes = base64.b64decode(base64_data)

    # 使用 soundfile 解码
    import soundfile as sf
    audio, sr = sf.read(io.BytesIO(audio_bytes))

    # 转换为 16kHz
    if sr != 16000:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

    return audio.astype(np.float32)


def frame_to_base64(frame: np.ndarray) -> str:
    """将视频帧转换为 Base64 JPEG"""
    # 转换为 uint8
    if frame.max() <= 1.0:
        frame = (frame * 255).astype(np.uint8)
    else:
        frame = frame.astype(np.uint8)

    # 转换为 PIL Image
    img = Image.fromarray(frame)

    # 编码为 JPEG
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)

    # Base64 编码
    import base64
    return base64.b64encode(buffer.read()).decode('utf-8')


# ============================================================================
# 端点
# ============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "model": "SoulX-FlashHead-1_3B",
        "gpu_available": torch.cuda.is_available(),
        "sage_attention": os.getenv('USE_SAGEATTENTION', '0') == '1',
    }


@app.post("/generate")
async def generate_video(request: VideoRequest):
    """
    标准的视频生成端点（一次性生成完整视频）

    Args:
        request: 视频生成请求

    Returns:
        完整的视频帧序列
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    start_time = time.time()

    try:
        # 解码音频
        audio = decode_base64_audio(request.audio_data)

        # 获取音频嵌入
        audio_embedding = get_audio_embedding(
            pipeline,
            audio,
            base_data,
            infer_params,
        )

        # 生成视频
        frames = run_pipeline(
            pipeline=pipeline,
            audio_embedding=audio_embedding,
            base_data=base_data,
            infer_params=infer_params,
        )

        # 转换为 numpy
        if isinstance(frames, torch.Tensor):
            frames = frames.cpu().numpy()

        # 转换帧为 Base64
        frame_list = []
        for i in range(len(frames)):
            frame = frames[i].transpose(1, 2, 0)  # [H, W, 3]
            frame_list.append(frame_to_base64(frame))

        latency = (time.time() - start_time) * 1000
        logger.info(f"[Video] 生成完成: {len(frames)} 帧, 延迟: {latency:.0f}ms")

        return {
            "frames": frame_list,
            "frame_count": len(frames),
            "fps": request.fps,
            "latency_ms": latency,
        }

    except Exception as e:
        logger.error(f"[Video] 生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/stream")
async def websocket_stream_video(websocket: WebSocket):
    """
    WebSocket 流式视频生成端点

    使用时空音频上下文缓存，实时生成视频帧
    """
    await websocket.accept()

    # 音频上下文队列（时空缓存）
    audio_context = deque(maxlen=21120)  # 1.32s @ 16kHz

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "audio_chunk":
                # 收到音频切片
                import base64
                audio_bytes = base64.b64decode(data["audio_data"])

                # 解码音频
                import soundfile as sf
                audio, sr = sf.read(io.BytesIO(audio_bytes))
                if sr != 16000:
                    import librosa
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                audio = audio.astype(np.float32)

                # 更新音频上下文
                audio_context.extend(audio)

                # 检查是否有足够音频生成视频
                min_samples = int(16000 / 25)  # 每帧 640 samples

                if len(audio_context) >= min_samples:
                    # 生成视频帧
                    audio_array = np.array(list(audio_context))

                    audio_embedding = get_audio_embedding(
                        pipeline,
                        audio_array,
                        base_data,
                        infer_params,
                    )

                    frames = run_pipeline(
                        pipeline=pipeline,
                        audio_embedding=audio_embedding,
                        base_data=base_data,
                        infer_params=infer_params,
                    )

                    if isinstance(frames, torch.Tensor):
                        frames = frames.cpu().numpy()

                    # 只返回新增的帧（去掉重叠帧）
                    new_frames = frames[9:]  # 去掉前 9 帧重叠

                    for frame in new_frames:
                        frame_rgb = frame.transpose(1, 2, 0)  # [H, W, 3]
                        frame_b64 = frame_to_base64(frame_rgb)

                        await websocket.send_json({
                            "type": "video_frame",
                            "frame_data": frame_b64,
                        })

                    # 移除已处理的音频（保留 9 帧重叠）
                    overlap_samples = int(16000 / 25 * 9)
                    while len(audio_context) > overlap_samples:
                        audio_context.popleft()

            elif message_type == "end":
                # 流结束，生成剩余帧
                if len(audio_context) > 0:
                    audio_array = np.array(list(audio_context))

                    audio_embedding = get_audio_embedding(
                        pipeline,
                        audio_array,
                        base_data,
                        infer_params,
                    )

                    frames = run_pipeline(
                        pipeline=pipeline,
                        audio_embedding=audio_embedding,
                        base_data=base_data,
                        infer_params=infer_params,
                    )

                    if isinstance(frames, torch.Tensor):
                        frames = frames.cpu().numpy()

                    for frame in frames:
                        frame_rgb = frame.transpose(1, 2, 0)
                        frame_b64 = frame_to_base64(frame_rgb)

                        await websocket.send_json({
                            "type": "video_frame",
                            "frame_data": frame_b64,
                        })

                await websocket.send_json({"type": "complete"})
                break

    except Exception as e:
        logger.error(f"[WebSocket] 错误: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        audio_context.clear()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
