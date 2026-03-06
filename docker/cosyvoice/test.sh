#!/bin/bash
# CosyVoice TTS 服务测试脚本

set -e

COSYVOICE_URL=${COSYVOICE_URL:-"http://localhost:8002"}

echo "==================================="
echo "  CosyVoice TTS 服务测试"
echo "==================================="
echo ""

# 1. 健康检查
echo "1️⃣  健康检查..."
curl -s ${COSYVOICE_URL}/health | python3 -m json.tool || echo "❌ 健康检查失败"
echo ""

# 2. 服务信息
echo "2️⃣  服务信息..."
curl -s ${COSYVOICE_URL}/ | python3 -m json.tool
echo ""

# 3. 标准 TTS 测试
echo "3️⃣  标准 TTS 测试..."
echo "   发送请求: '你好，我是数字人助手'"

curl -s -X POST ${COSYVOICE_URL}/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是数字人助手",
    "prompt_text": "希望你今天能够开心"
  }' \
  -o /tmp/test_cosyvoice.wav

if [ -f /tmp/test_cosyvoice.wav ]; then
    echo "   ✅ 音频文件已生成: $(ls -lh /tmp/test_cosyvoice.wav | awk '{print $5}')"
    echo "   格式: $(file /tmp/test_cosyvoice.wav | cut -d: -f2)"
else
    echo "   ❌ 音频文件生成失败"
fi
echo ""

# 4. 流式 TTS 测试
echo "4️⃣  流式 TTS 测试..."
echo "   发送请求: '你好，我是数字人助手，很高兴认识大家'"

START_TIME=$(date +%s%3N)
curl -s -X POST ${COSYVOICE_URL}/tts/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是数字人助手，很高兴认识大家",
    "prompt_text": "希望你今天能够开心",
    "chunk_size_ms": 150
  }' \
  -o /tmp/test_cosyvoice_stream.wav
END_TIME=$(date +%s%3N)

if [ -f /tmp/test_cosyvoice_stream.wav ]; then
    LATENCY=$((END_TIME - START_TIME))
    echo "   ✅ 流式音频文件已生成: $(ls -lh /tmp/test_cosyvoice_stream.wav | awk '{print $5}')"
    echo "   耗时: ${LATENCY}ms"
else
    echo "   ❌ 流式音频文件生成失败"
fi
echo ""

echo "==================================="
echo "  测试完成！"
echo "==================================="
echo ""
echo "音频文件位置:"
echo "  标准 TTS: /tmp/test_cosyvoice.wav"
echo "  流式 TTS: /tmp/test_cosyvoice_stream.wav"
echo ""
echo "播放测试:"
echo "  aplay /tmp/test_cosyvoice.wav"
echo "  aplay /tmp/test_cosyvoice_stream.wav"
