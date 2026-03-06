# CosyVoice 流式 TTS 服务 - Docker 镜像
# 基于 CosyVoice-300M Zero-shot 模型
# 验证日期: 2026-03-06

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    NVIDIA_VISIBLE_DEVICES=all

# 安装 Python 和系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip3 install --no-cache-dir --upgrade pip

# 安装 PyTorch (CUDA 12.1)
RUN pip3 install --no-cache-dir \
    torch==2.5.1 \
    torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu121

# 安装 CosyVoice 依赖
RUN pip3 install --no-cache-dir \
    transformers==4.45.2 \
    accelerate \
    omegaconf==2.3.0 \
    hydra-core==1.3.2 \
    einops \
    librosa \
    soundfile \
    fastapi \
    uvicorn[standard] \
    websockets \
    pydantic \
    pyyaml \
    aiofiles \
    hyperpyyaml \
    modelscope \
    tqdm

# 创建工作目录
RUN mkdir -p /app /models
WORKDIR /app

# 复制服务文件
COPY cosyvoice_server.py /app/
COPY start.sh /app/
RUN chmod +x /app/start.sh

# 暴露端口
EXPOSE 8002

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# 启动命令
CMD ["/app/start.sh"]
