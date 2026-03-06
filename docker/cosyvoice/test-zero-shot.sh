#!/bin/bash
# CosyVoice Zero-shot TTS 测试脚本
# 使用自定义参考音频进行音色克隆

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 激活虚拟环境
source "${PROJECT_ROOT}/backend/venv/bin/activate"

# 设置 Python 路径
export PYTHONPATH="/opt/digital-human-platform/models/CosyVoice/third_party/Matcha-TTS:/opt/digital-human-platform/models/CosyVoice:${PYTHONPATH}"

# 默认参数
REF_AUDIO="${1:-${PROJECT_ROOT}/assets/simple_voice.mp3}"
PROMPT_TEXT="${2:-今天的天气真不错，适合出去散步}"
TTS_TEXT="${3:-你好，我是数字人助手，很高兴认识大家}"

echo "==================================="
echo "  CosyVoice Zero-shot TTS 测试"
echo "==================================="
echo ""

# 检查参考音频
if [ ! -f "${REF_AUDIO}" ]; then
    echo "❌ 参考音频不存在: ${REF_AUDIO}"
    exit 1
fi

echo "📝 测试参数:"
echo "   参考音频: ${REF_AUDIO}"
echo "   参考文本: ${PROMPT_TEXT}"
echo "   合成文本: ${TTS_TEXT}"
echo ""

# 转换参考音频为 WAV (如果需要)
REF_WAV="/tmp/cosyvoice_ref.wav"
if [ "${REF_AUDIO##*.}" != "wav" ]; then
    echo "🔄 转换参考音频为 WAV..."
    ffmpeg -i "${REF_AUDIO}" -ar 22050 -ac 1 -y "${REF_WAV}" 2>&1 | grep -E "(Duration|Output)"
    echo "   ✅ 转换完成: ${REF_WAV}"
else
    cp "${REF_AUDIO}" "${REF_WAV}"
fi
echo ""

# 运行 Zero-shot TTS
echo "🎵 生成音频..."
python3 << EOF
import sys
import time
import torch
import numpy as np
import wave

sys.path.insert(0, '/opt/digital-human-platform/models/CosyVoice/third_party/Matcha-TTS')
sys.path.insert(0, '/opt/digital-human-platform/models/CosyVoice')

from cosyvoice.cli.cosyvoice import CosyVoice

# 加载模型
print("正在加载 CosyVoice 模型...")
model = CosyVoice('iic/CosyVoice-300M')
print(f"✅ 模型加载成功 (采样率: {model.sample_rate}Hz)")
print()

# 生成音频
ref_wav = "${REF_WAV}"
prompt_text = "${PROMPT_TEXT}"
tts_text = "${TTS_TEXT}"

print(f"参考文本: {prompt_text}")
print(f"合成文本: {tts_text}")
print()
print("正在生成音频...")

start_time = time.time()
audio_list = []

for i, audio_chunk in enumerate(model.inference_zero_shot(
    tts_text=tts_text,
    prompt_text=prompt_text,
    prompt_wav=ref_wav,
    stream=False,
)):
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
    print("✅ 音频生成成功!")
    print("=" * 50)
    print(f"   时长: {duration:.2f}s")
    print(f"   延迟: {latency:.0f}ms")
    print(f"   RTF: {latency/1000/duration:.2f}x")

    # 保存为 WAV
    if audio.dtype != np.int16:
        if audio.max() <= 1.0:
            audio = (audio * 32767).astype(np.int16)
        else:
            audio = audio.astype(np.int16)

    output_path = "/tmp/cosyvoice_zero_shot_output.wav"
    with wave.open(output_path, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(model.sample_rate)
        wav.writeframes(audio.tobytes())

    print(f"   输出: {output_path}")
    print(f"   大小: {len(audio.tobytes())} bytes")
else:
    print("❌ 未能生成音频")
    sys.exit(1)
EOF

echo ""
echo "==================================="
echo "  测试完成!"
echo "==================================="
echo ""
echo "输出文件: /tmp/cosyvoice_zero_shot_output.wav"
echo ""
echo "播放测试:"
echo "  aplay /tmp/cosyvoice_zero_shot_output.wav"
echo ""
echo "使用方法:"
echo "  $0 [参考音频] [参考文本] [合成文本]"
echo ""
echo "示例:"
echo "  $0 assets/simple_voice.mp3"
echo "  $0 assets/simple_voice.mp3 \"你好\" \"测试音频\""
