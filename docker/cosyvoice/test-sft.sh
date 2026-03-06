#!/bin/bash
# CosyVoice SFT 服务测试脚本

set -e

COSYVOICE_URL=${COSYVOICE_URL:-"http://localhost:8003"}

echo "==================================="
echo "  CosyVoice SFT 服务测试"
echo "==================================="
echo ""

# 1. 健康检查
echo "1️⃣  健康检查..."
curl -s ${COSYVOICE_URL}/health | python3 -m json.tool || echo "❌ 健康检查失败"
echo ""

# 2. 获取音色列表
echo "2️⃣  获取音色列表..."
SPEAKERS=$(curl -s ${COSYVOICE_URL}/speakers)
echo "$SPEAKERS" | python3 -m json.tool || echo "❌ 获取音色列表失败"
echo ""

# 3. 选择第一个音色测试
echo "3️⃣  测试预设音色 TTS..."
FIRST_SPEAKER=$(echo "$SPEAKERS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['speakers'][0])" 2>/dev/null || echo "中性女")

echo "   使用音色: $FIRST_SPEAKER"
echo "   合成文本: '你好，我是数字人助手，很高兴认识大家'"
echo ""

curl -s -X POST ${COSYVOICE_URL}/tts \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"你好，我是数字人助手，很高兴认识大家\",
    \"speaker\": \"$FIRST_SPEAKER\"
  }" \
  -o /tmp/test_cosyvoice_sft.wav

if [ -f /tmp/test_cosyvoice_sft.wav ]; then
    echo "   ✅ 音频文件已生成: $(ls -lh /tmp/test_cosyvoice_sft.wav | awk '{print $5}')"
    echo "   格式: $(file /tmp/test_cosyvoice_sft.wav | cut -d: -f2)"
else
    echo "   ❌ 音频文件生成失败"
fi
echo ""

# 4. 测试不同音色
echo "4️⃣  测试多个音色..."
SPEAKER_LIST=($(echo "$SPEAKERS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join(data['speakers'][:3]))" 2>/dev/null))

for i in {1..2}; do
    if [ ! -z "${SPEAKER_LIST[$i]}" ]; then
        SPEAKER="${SPEAKER_LIST[$i]}"
        echo "   测试音色: $SPEAKER"

        curl -s -X POST ${COSYVOICE_URL}/tts \
          -H "Content-Type: application/json" \
          -d "{
            \"text\": \"这是音色测试\",
            \"speaker\": \"$SPEAKER\"
          }" \
          -o /tmp/test_sft_${i}.wav

        if [ -f /tmp/test_sft_${i}.wav ]; then
            echo "     ✅ 生成成功: $(ls -lh /tmp/test_sft_${i}.wav | awk '{print $5}')"
        fi
    fi
done
echo ""

# 5. 流式 TTS 测试
echo "5️⃣  流式 TTS 测试..."
echo "   使用音色: $FIRST_SPEAKER"

START_TIME=$(date +%s%3N)
curl -s -X POST ${COSYVOICE_URL}/tts/stream \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"今天是个好日子，心想的事儿都能成\",
    \"speaker\": \"$FIRST_SPEAKER\",
    \"chunk_size_ms\": 150
  }" \
  -o /tmp/test_sft_stream.wav
END_TIME=$(date +%s%3N)

if [ -f /tmp/test_sft_stream.wav ]; then
    LATENCY=$((END_TIME - START_TIME))
    echo "   ✅ 流式音频文件已生成: $(ls -lh /tmp/test_sft_stream.wav | awk '{print $5}')"
    echo "   耗时: ${LATENCY}ms"
else
    echo "   ❌ 流式音频文件生成失败"
fi
echo ""

echo "==================================="
echo "  测试完成！"
echo "==================================="
echo ""
echo "生成的音频文件:"
ls -lh /tmp/test_cosyvoice_sft*.wav 2>/dev/null
echo ""
echo "播放测试:"
echo "  aplay /tmp/test_cosyvoice_sft.wav"
echo "  aplay /tmp/test_sft_stream.wav"
