#!/bin/bash
# CosyVoice 本地服务启动脚本

source /opt/digital-human-platform/backend/venv/bin/activate

# 设置 Python 路径
export PYTHONPATH="/opt/digital-human-platform/models/CosyVoice/third_party/Matcha-TTS:/opt/digital-human-platform/models/CosyVoice:/opt/digital-human-platform/backend:$PYTHONPATH"
export MODELSCOPE_CACHE_DIR="/opt/digital-human-platform/models/CosyVoice/pretrained_models"

cd /opt/digital-human-platform/docker/vllm-cosyvoice

echo "🎵 启动 CosyVoice TTS 服务..."
python3 cosyvoice_server_v2.py
