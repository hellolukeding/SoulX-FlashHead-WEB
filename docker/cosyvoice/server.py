"""
CosyVoice 流式 TTS 服务 - FastAPI 服务器

特性：
- 流式切片输出 (150-200ms)
- 内存级数据传递
- 支持多种音色
- 零磁盘 I/O
"""
import asyncio
import io
import logging
import time
import wave
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import set_seed

from cosyvoice.cli.CosyVoice2 import CosyVoice2
from cosyvoice.utils.file_utils import load_wav

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 请求/响应模型
# ============================================================================

class TTSRequest(BaseModel):
    """TTS 请求"""
    text: str
    speaker: str = "female"
    chunk_size: int = 2400  # 150ms @ 16kHz
    speed: float = 1.0
    seed: int = 0


class StreamingTTSRequest(BaseModel):
    """流式 TTS 请求"""
    text: str
    speaker: str = "female"
    chunk_size: int = 2400
    speed: float = 1.0


# ============================================================================
# 全局模型实例
# ============================================================================

cosyvoice_model: Optional[CosyVoice2] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global cosyvoice_model

    logger.info("🎵 初始化 CosyVoice 模型...")

    # 加载模型
    model_path = "/models/CosyVoice-300M"

    cosyvoice_model = CosyVoice2(
        model_path=model_path,
        load_jit=True,
        load_onnx=False,
        fp16=True,
    )

    logger.info("✅ CosyVoice 模型加载完成")

    # 预热
    logger.info("🔥 预热模型...")
    _ = cosyvoice_model.inference_zero(
        text="你好",
        speaker_embedding="default",
        stream=False,
    )
    logger.info("✅ 预热完成")

    yield

    # 清理
    logger.info("🧹 清理资源...")
    del cosyvoice_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="CosyVoice 流式 TTS 服务",
    description="支持流式切片输出的 TTS 服务",
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================================
# 端点
# ============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "model": "CosyVoice-300M",
        "gpu_available": torch.cuda.is_available(),
    }


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    标准的 TTS 端点（一次性生成完整音频）

    Args:
        request: TTS 请求

    Returns:
        完整的音频数据
    """
    if cosyvoice_model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    start_time = time.time()

    try:
        # 生成音频
        set_seed(request.seed)
        audio = cosyvoice_model.inference_zero(
            text=request.text,
            speaker_embedding=request.speaker,
            stream=False,
        )

        # 转换为 numpy
        if isinstance(audio, (tuple, list)):
            audio = audio[0]

        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()

        # 调整速度
        if request.speed != 1.0:
            # 使用 resampy 或 librosa 调整速度
            import librosa
            audio = librosa.effects.time_stretch(audio, rate=request.speed)

        # 编码为 WAV
        buffer = io.BytesIO()
        sf.write(buffer, audio, 24000, format='WAV')
        buffer.seek(0)

        latency = (time.time() - start_time) * 1000
        logger.info(f"[TTS] 生成完成: {len(audio)/24000:.2f}s, 延迟: {latency:.0f}ms")

        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={
                "X-Latency-ms": str(latency),
                "X-Duration-s": str(len(audio) / 24000),
            }
        )

    except Exception as e:
        logger.error(f"[TTS] 生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/stream")
async def text_to_speech_streaming(request: StreamingTTSRequest):
    """
    流式 TTS 端点 - 切片输出

    将长文本分片处理，每片 150-200ms

    Args:
        request: TTS 请求

    Returns:
        流式音频切片
    """
    if cosyvoice_model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    async def generate_chunks() -> AsyncGenerator[bytes, None]:
        """生成音频切片"""
        try:
            # 使用 CosyVoice 的内置流式功能
            set_seed(0)

            chunk_count = 0
            total_samples = 0

            # 流式生成
            for audio_chunk in cosyvoice_model.inference_zero(
                text=request.text,
                speaker_embedding=request.speaker,
                stream=True,  # 启用流式输出
            ):
                if audio_chunk is None:
                    break

                # 转换为 numpy
                if isinstance(audio_chunk, torch.Tensor):
                    audio_chunk = audio_chunk.cpu().numpy()

                # 分片
                samples_per_chunk = request.chunk_size
                num_chunks = int(np.ceil(len(audio_chunk) / samples_per_chunk))

                for i in range(num_chunks):
                    start = i * samples_per_chunk
                    end = min(start + samples_per_chunk, len(audio_chunk))
                    chunk = audio_chunk[start:end]

                    # 确保是 int16
                    if chunk.dtype != np.int16:
                        if chunk.max() <= 1.0:
                            chunk = (chunk * 32767).astype(np.int16)
                        else:
                            chunk = chunk.astype(np.int16)

                    # 编码为 WAV
                    buffer = io.BytesIO()
                    with wave.open(buffer, 'wb') as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(24000)
                        wav.writeframes(chunk.tobytes())

                    chunk_bytes = buffer.getvalue()
                    total_samples += len(chunk)
                    chunk_count += 1

                    logger.debug(f"[TTS Stream] 发送切片 #{chunk_count}: {len(chunk)/24000*1000:.0f}ms")
                    yield chunk_bytes

            logger.info(f"[TTS Stream] 完成: {chunk_count} 切片, {total_samples/24000:.2f}s")

        except Exception as e:
            logger.error(f"[TTS Stream] 错误: {e}")
            raise

    return StreamingResponse(
        generate_chunks(),
        media_type="audio/wav",
        headers={
            "Transfer-Encoding": "chunked",
            "X-Chunk-Size": str(request.chunk_size),
        }
    )


@app.post("/tts/stream/async")
async def text_to_speech_streaming_async(request: StreamingTTSRequest):
    """
    异步流式 TTS - 真正的实时输出

    在生成音频的同时发送，不等完整音频生成完毕
    """
    if cosyvoice_model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    async def generate_realtime() -> AsyncGenerator[bytes, None]:
        """实时生成音频"""
        try:
            # 启动生成任务
            set_seed(0)

            # 创建异步队列
            audio_queue: asyncio.Queue[Optional[np.ndarray]] = asyncio.Queue(maxsize=10)

            # 生成任务
            async def generate_audio():
                try:
                    for audio_chunk in cosyvoice_model.inference_zero(
                        text=request.text,
                        speaker_embedding=request.speaker,
                        stream=True,
                    ):
                        if audio_chunk is None:
                            break

                        if isinstance(audio_chunk, torch.Tensor):
                            audio_chunk = audio_chunk.cpu().numpy()

                        await audio_queue.put(audio_chunk)

                    await audio_queue.put(None)

                except Exception as e:
                    logger.error(f"[Audio Generator] 错误: {e}")
                    await audio_queue.put(None)

            # 启动生成任务
            asyncio.create_task(generate_audio())

            # 分片发送
            chunk_count = 0
            while True:
                audio = await audio_queue.get()

                if audio is None:
                    break

                # 分片
                samples_per_chunk = request.chunk_size
                num_chunks = int(np.ceil(len(audio) / samples_per_chunk))

                for i in range(num_chunks):
                    start = i * samples_per_chunk
                    end = min(start + samples_per_chunk, len(audio))
                    chunk = audio[start:end]

                    # 转换为 int16
                    if chunk.dtype != np.int16:
                        if chunk.max() <= 1.0:
                            chunk = (chunk * 32767).astype(np.int16)
                        else:
                            chunk = chunk.astype(np.int16)

                    # 编码并发送
                    buffer = io.BytesIO()
                    with wave.open(buffer, 'wb') as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(24000)
                        wav.writeframes(chunk.tobytes())

                    chunk_count += 1
                    yield buffer.getvalue()
                    logger.debug(f"[Realtime TTS] 发送切片 #{chunk_count}")

            logger.info(f"[Realtime TTS] 完成: {chunk_count} 切片")

        except Exception as e:
            logger.error(f"[Realtime TTS] 错误: {e}")
            raise

    return StreamingResponse(
        generate_realtime(),
        media_type="audio/wav",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
