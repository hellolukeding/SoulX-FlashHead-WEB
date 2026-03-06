# SoulX-FlashHead Docker 镜像 - 时空缓存流式视频生成
# 支持 SageAttention 加速

FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip3 install --upgrade pip

# 安装 PyTorch (CUDA 12.1)
RUN pip3 install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121

# 安装 SageAttention (关键优化)
RUN pip3 install SageAttention-2.2.0+torch2.5+cu121 \
    --extra-index-url https://pyproject.org/pre-built/

# 安装 SoulX-FlashHead 依赖
RUN pip3 install \
    transformers==4.45.2 \
    accelerate \
    omegaconf \
    hydra-core \
    einops \
    librosa \
    soundfile \
    av \
    opencv-python \
    pillow \
    pyyaml \
    fastapi \
    uvicorn[standard] \
    websockets \
    aiortc \
    av

# 安装 flash-attn (可选，SageAttention 的替代)
RUN pip3 install flash-attn --no-build-isolation || echo "flash-attn 安装失败，使用 SageAttention"

# 创建模型目录
RUN mkdir -p /models

# 设置工作目录
WORKDIR /app

# 复制启动脚本
COPY start_soulx.sh /app/
RUN chmod +x /app/start_soulx.sh

# 暴露端口
EXPOSE 8003

# 启动 SoulX 服务
CMD ["/app/start_soulx.sh"]
