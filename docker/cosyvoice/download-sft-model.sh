#!/bin/bash
# 下载 CosyVoice-300M-SFT 模型（支持预设音色）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 激活虚拟环境
source "${PROJECT_ROOT}/backend/venv/bin/activate"

# 设置 Python 路径
export PYTHONPATH="/opt/digital-human-platform/models/CosyVoice/third_party/Matcha-TTS:/opt/digital-human-platform/models/CosyVoice:${PYTHONPATH}"

# 模型配置
MODEL_NAME="CosyVoice-300M-SFT"
MODEL_ID="iic/CosyVoice-300M-SFT"
CACHE_DIR="${PROJECT_ROOT}/models/CosyVoice/pretrained_models"

echo "==================================="
echo "  下载 CosyVoice-300M-SFT 模型"
echo "==================================="
echo ""
echo "模型: ${MODEL_NAME}"
echo "大小: 约 1.5 GB"
echo "缓存目录: ${CACHE_DIR}"
echo ""
read -p "确认下载? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消下载"
    exit 0
fi

echo ""
echo "开始下载..."
echo ""

python3 << EOF
import sys
from modelscope import snapshot_download

print(f"正在下载 {MODEL_NAME}...")

cache_path = snapshot_download(
    MODEL_ID,
    cache_dir="${CACHE_DIR}",
)

print()
print("=" * 50)
print("✅ 下载完成!")
print("=" * 50)
print(f"模型路径: {cache_path}")
print()

# 创建符号链接（如果需要）
import os
target_dir = os.path.join("${CACHE_DIR}", "${MODEL_NAME}")
if not os.path.exists(target_dir):
    os.symlink(cache_path, target_dir)
    print(f"创建符号链接: {target_dir}")
EOF

echo ""
echo "==================================="
echo "  测试预设音色"
echo "==================================="
echo ""

python3 << 'PYEOF'
import sys
import time
import torch
import numpy as np
import wave

sys.path.insert(0, '/opt/digital-human-platform/models/CosyVoice/third_party/Matcha-TTS')
sys.path.insert(0, '/opt/digital-human-platform/models/CosyVoice')

from cosyvoice.cli.cosyvoice import CosyVoice

print("正在加载 CosyVoice-300M-SFT 模型...")
model = CosyVoice('iic/CosyVoice-300M-SFT')
print(f"✅ 模型加载成功 (采样率: {model.sample_rate}Hz)")
print()

# 获取预设音色列表
spks = model.list_available_spks()
print(f"预设音色数量: {len(spks)}")
print()
print("可用的预设音色:")
for i, spk in enumerate(spks[:10], 1):
    print(f"  {i}. {spk}")
if len(spks) > 10:
    print(f"  ... 还有 {len(spks) - 10} 个音色")
print()

# 测试第一个音色
if spks:
    test_spk = spks[0]
    tts_text = "你好，我是数字人助手，很高兴认识大家"

    print(f"测试音色: {test_spk}")
    print(f"合成文本: {tts_text}")
    print()
    print("正在生成音频...")

    start_time = time.time()
    audio_list = []

    for audio_chunk in model.inference_sft(
        tts_text=tts_text,
        spk_id=test_spk,
        stream=False,
    ):
        if isinstance(audio_chunk, dict):
            audio_chunk = audio_chunk.get('tts_speech', audio_chunk)

        if isinstance(audio_chunk, torch.Tensor):
            audio_chunk = audio_chunk.cpu().numpy()
        elif isinstance(audio_chunk, (list, tuple)):
            audio_chunk = np.array(audio_chunk)

        audio_list.append(audio_chunk)

    if audio_list:
        audio = np.concatenate(audio_list)
        if len(audio.shape) > 1:
            audio = audio.squeeze()

        latency = (time.time() - start_time) * 1000
        duration = len(audio) / model.sample_rate

        print()
        print("=" * 50)
        print("✅ 预设音色测试成功!")
        print("=" * 50)
        print(f"   音色: {test_spk}")
        print(f"   时长: {duration:.2f}s")
        print(f"   延迟: {latency:.0f}ms")
        print(f"   RTF: {latency/1000/duration:.2f}x")

        # 保存音频
        if audio.dtype != np.int16:
            if audio.max() <= 1.0:
                audio = (audio * 32767).astype(np.int16)

        output_path = "/tmp/cosyvoice_sft_output.wav"
        with wave.open(output_path, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(model.sample_rate)
            wav.writeframes(audio.tobytes())

        print(f"   输出: {output_path}")
PYEOF

echo ""
echo "==================================="
echo "  完成!"
echo "==================================="
echo ""
echo "下一步:"
echo "  1. 使用不同预设音色测试"
echo "  2. 更新 Docker 镜像以支持 SFT 模式"
echo "  3. 更新 API 服务添加预设音色端点"
