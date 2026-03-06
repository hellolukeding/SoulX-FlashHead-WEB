# vLLM Docker 镜像 - 用于 CosyVoice LLM 加速
# 基于 vLLM 0.6.x 支持流式输出和音频模型

FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV VLLM_WORKER_MULTIPROC_METHOD=spawn

# 安装依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip3 install --upgrade pip

# 安装 vLLM (支持音频模型)
RUN pip3 install vllm==0.6.3 \
    torch==2.5.1 \
    torchaudio==2.5.1 \
    transformers==4.45.2 \
    accelerate \
    sentencepiece \
    protobuf

# 创建模型目录
RUN mkdir -p /models

# 设置工作目录
WORKDIR /app

# 复制启动脚本
COPY start_vllm.sh /app/
RUN chmod +x /app/start_vllm.sh

# 暴露端口
EXPOSE 8000

# 启动 vLLM 服务
CMD ["/app/start_vllm.sh"]
