# CosyVoice 流式 TTS 服务 - 修复版

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# 安装 Python、ffmpeg 和依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip3 install --upgrade pip

# 安装 PyTorch (CUDA 12.1)
RUN pip3 install --no-cache-dir torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

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
    uvicorn \
    websockets \
    pydantic \
    pyyaml \
    aiofiles \
    hyperpyyaml \
    modelscope \
    tqdm

# 创建模型目录
RUN mkdir -p /models

# 设置工作目录
WORKDIR /app

# 复制文件
COPY cosyvoice_server_v2.py /app/cosyvoice_server.py

# 暴露端口
EXPOSE 8002

# 启动命令
CMD ["uvicorn", "cosyvoice_server:app", "--host", "0.0.0.0", "--port", "8002"]
