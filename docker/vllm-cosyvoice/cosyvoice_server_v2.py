"""
CosyVoice 流式 TTS 服务 - FastAPI 服务器

特性：
- 流式切片输出 (150-200ms)
- 内存级数据传递
- 支持多种音色
"""
import asyncio
import io
import logging
import time
import wave
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 请求/响应模型
# ============================================================================

class TTSRequest(BaseModel):
    """TTS 请求"""
    text: str
    prompt_text: str = "希望你今天能够开心"
    prompt_audio_url: str = ""


class StreamingTTSRequest(BaseModel):
    """流式 TTS 请求"""
    text: str
    prompt_text: str = "希望你今天能够开心"
    prompt_audio_url: str = ""
    chunk_size_ms: int = 150


# ============================================================================
# 全局模型实例
# ============================================================================

cosyvoice_model = None
model_loaded = False
prompt_wav = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global cosyvoice_model, model_loaded, prompt_wav

    logger.info("🎵 初始化 CosyVoice 模型...")

    try:
        # 导入 CosyVoice
        import sys
        sys.path.insert(0, '/models/CosyVoice/third_party/Matcha-TTS')
        sys.path.insert(0, '/models/CosyVoice')

        from cosyvoice.cli.cosyvoice import CosyVoice

        # 使用 ModelScope 模型 ID
        model_path = 'iic/CosyVoice-300M'

        logger.info(f"正在加载模型: {model_path}")
        cosyvoice_model = CosyVoice(model_path)

        # 加载默认参考音频
        import os
        prompt_audio_path = '/opt/digital-human-platform/models/CosyVoice/pretrained_models/CosyVoice-300M/asset/default_prompt.wav'
        if os.path.exists(prompt_audio_path):
            prompt_wav = prompt_audio_path
            logger.info(f"✅ 加载默认参考音频: {prompt_audio_path}")
        else:
            logger.warning("⚠️ 未找到默认参考音频，需要提供 prompt_audio_url")

        model_loaded = True
        logger.info(f"✅ CosyVoice 模型加载成功 (采样率: {cosyvoice_model.sample_rate}Hz)")

    except Exception as e:
        logger.error(f"❌ 模型加载失败: {e}")
        logger.error("服务将以无模型模式启动，用于测试")
        import traceback
        traceback.print_exc()

    yield

    # 清理
    logger.info("🧹 清理资源...")
    if cosyvoice_model is not None:
        del cosyvoice_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="CosyVoice 流式 TTS 服务",
    description="支持流式切片输出的 TTS 服务",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# 辅助函数
# ============================================================================

def audio_to_wav_bytes(audio: np.ndarray, sample_rate: int = 22050) -> bytes:
    """将音频转换为 WAV 字节"""
    # 确保是 int16
    if audio.dtype != np.int16:
        if audio.max() <= 1.0:
            audio = (audio * 32767).astype(np.int16)
        else:
            audio = audio.astype(np.int16)

    # 编码为 WAV
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio.tobytes())

    return buffer.getvalue()


async def generate_audio_stream(
    text: str,
    prompt_text: str,
    prompt_wav_path: str,
    chunk_size_ms: int = 150,
    sample_rate: int = 22050,
) -> AsyncGenerator[bytes, None]:
    """生成音频流"""
    if cosyvoice_model is None:
        logger.error("模型未加载")
        return

    try:
        chunk_samples = int(sample_rate * chunk_size_ms / 1000)

        # 调用 CosyVoice Zero Shot
        for audio_chunk in cosyvoice_model.inference_zero_shot(
            tts_text=text,
            prompt_text=prompt_text,
            prompt_wav=prompt_wav_path,
            stream=True,
        ):
            if audio_chunk is None:
                break

            # 获取音频数据
            if isinstance(audio_chunk, dict):
                audio_chunk = audio_chunk.get('tts_speech', audio_chunk)

            # 转换为 numpy
            if isinstance(audio_chunk, torch.Tensor):
                audio_chunk = audio_chunk.cpu().numpy()
            elif isinstance(audio_chunk, (list, tuple)):
                audio_chunk = np.array(audio_chunk)

            # 确保是一维数组
            if len(audio_chunk.shape) > 1:
                audio_chunk = audio_chunk.squeeze()

            # 分片
            num_chunks = int(np.ceil(len(audio_chunk) / chunk_samples))

            for i in range(num_chunks):
                start = i * chunk_samples
                end = min(start + chunk_samples, len(audio_chunk))
                chunk = audio_chunk[start:end]

                if len(chunk) > 0:
                    wav_bytes = audio_to_wav_bytes(chunk, sample_rate)
                    yield wav_bytes

                    logger.debug(f"[TTS Stream] 发送切片: {len(chunk)/sample_rate*1000:.0f}ms")

    except Exception as e:
        logger.error(f"[TTS Stream] 生成失败: {e}")
        raise


# ============================================================================
# 端点
# ============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "CosyVoice TTS",
        "model_loaded": model_loaded,
        "gpu_available": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """标准 TTS 端点"""
    if cosyvoice_model is None:
        raise HTTPException(
            status_code=503,
            detail="模型未加载，请检查模型路径"
        )

    start_time = time.time()

    try:
        logger.info(f"[TTS] 收到请求: {request.text[:50]}...")

        # 确定使用的参考音频
        ref_wav = request.prompt_audio_url if request.prompt_audio_url else prompt_wav
        if not ref_wav:
            raise HTTPException(
                status_code=400,
                detail="请提供 prompt_audio_url 或确保服务器已加载默认参考音频"
            )

        # 生成音频 - 使用 zero shot 模式
        audio_list = []
        for audio_chunk in cosyvoice_model.inference_zero_shot(
            tts_text=request.text,
            prompt_text=request.prompt_text,
            prompt_wav=ref_wav,
            stream=False,
        ):
            # 处理字典格式
            if isinstance(audio_chunk, dict):
                audio_chunk = audio_chunk.get('tts_speech', audio_chunk)

            # 转换为 numpy
            if isinstance(audio_chunk, torch.Tensor):
                audio_chunk = audio_chunk.cpu().numpy()
            elif isinstance(audio_chunk, (list, tuple)):
                audio_chunk = np.array(audio_chunk)

            audio_list.append(audio_chunk)

        # 拼接所有音频片段
        if audio_list:
            audio = np.concatenate(audio_list)
        else:
            raise ValueError("未能生成音频")

        # 确保是一维数组
        if len(audio.shape) > 1:
            audio = audio.squeeze()

        # 转换为 WAV
        wav_bytes = audio_to_wav_bytes(audio, sample_rate=cosyvoice_model.sample_rate)

        latency = (time.time() - start_time) * 1000
        duration = len(audio) / cosyvoice_model.sample_rate

        logger.info(f"[TTS] 生成完成: {duration:.2f}s, 延迟: {latency:.0f}ms")

        return StreamingResponse(
            io.BytesIO(wav_bytes),
            media_type="audio/wav",
            headers={
                "X-Latency-ms": str(latency),
                "X-Duration-s": str(duration),
            }
        )

    except Exception as e:
        logger.error(f"[TTS] 生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/stream")
async def text_to_speech_streaming(request: StreamingTTSRequest):
    """流式 TTS 端点"""
    if cosyvoice_model is None:
        raise HTTPException(
            status_code=503,
            detail="模型未加载"
        )

    logger.info(f"[TTS Stream] 收到请求: {request.text[:50]}...")

    start_time = time.time()
    chunk_count = 0

    # 确定使用的参考音频
    ref_wav = request.prompt_audio_url if request.prompt_audio_url else prompt_wav
    if not ref_wav:
        raise HTTPException(
            status_code=400,
            detail="请提供 prompt_audio_url 或确保服务器已加载默认参考音频"
        )

    async def generate() -> AsyncGenerator[bytes, None]:
        nonlocal chunk_count

        try:
            async for wav_bytes in generate_audio_stream(
                text=request.text,
                prompt_text=request.prompt_text,
                prompt_wav_path=ref_wav,
                chunk_size_ms=request.chunk_size_ms,
                sample_rate=cosyvoice_model.sample_rate,
            ):
                chunk_count += 1
                yield wav_bytes

            latency = (time.time() - start_time) * 1000
            logger.info(f"[TTS Stream] 完成: {chunk_count} 切片, 首包延迟: {latency:.0f}ms")

        except Exception as e:
            logger.error(f"[TTS Stream] 生成失败: {e}")
            raise

    return StreamingResponse(
        generate(),
        media_type="audio/wav",
        headers={
            "Transfer-Encoding": "chunked",
            "X-Chunk-Size-ms": str(request.chunk_size_ms),
        }
    )


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "CosyVoice 流式 TTS 服务",
        "version": "1.0.0",
        "mode": "zero-shot",
        "endpoints": {
            "health": "GET /health",
            "tts": "POST /tts",
            "tts_stream": "POST /tts/stream",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
