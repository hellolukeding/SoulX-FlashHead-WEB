#!/bin/bash
# CosyVoice TTS 服务测试脚本

BASE_URL="http://localhost:8002"

echo "🧪 CosyVoice TTS 服务测试"
echo "========================"
echo ""

# 测试 1: 健康检查
echo "测试 1: 健康检查"
echo "----------------"
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo ""

# 测试 2: 标准 TTS
echo "测试 2: 标准 TTS"
echo "----------------"
echo "生成音频: 你好，我是数字人助手"
echo ""

RESPONSE=$(curl -s -X POST "${BASE_URL}/tts" \
    -H "Content-Type: application/json" \
    -d '{"text": "你好，我是数字人助手", "speaker": "default"}' \
    -o /tmp/tts_test.wav \
    -w "HTTP_STATUS:%{http_code}|SIZE:%{size_download}|LATENCY:%{time_total}s")

HTTP_CODE=$(echo $RESPONSE | cut -d'|' -f1 | cut -d':' -f2)
SIZE=$(echo $RESPONSE | cut -d'|' -f2 | cut -d':' -f2)
LATENCY=$(echo $RESPONSE | cut -d'|' -f3 | cut -d':' -f2)

if [ "$HTTP_CODE" = "200" ] && [ -f /tmp/tts_test.wav ] && [ -s /tmp/tts_test.wav ]; then
    echo "✓ 音频生成成功"
    echo "  文件: /tmp/tts_test.wav"
    echo "  大小: $SIZE bytes"
    echo "  延迟: $LATENCY"

    # 播放音频（如果安装了播放器）
    if command -v ffplay &> /dev/null; then
        echo "  播放中..."
        ffplay -autoexit -nodisp /tmp/tts_test.wav 2>/dev/null
    elif command -v aplay &> /dev/null; then
        echo "  播放中..."
        aplay -q /tmp/tts_test.wav
    else
        echo "  (未安装音频播放器)"
    fi
else
    echo "✗ 音频生成失败 (HTTP $HTTP_CODE)"
fi
echo ""

# 测试 3: 流式 TTS
echo "测试 3: 流式 TTS"
echo "----------------"
echo "生成音频: 今天天气真不错，适合出去走走"
echo ""

curl -s -X POST "${BASE_URL}/tts/stream" \
    -H "Content-Type: application/json" \
    -d '{"text": "今天天气真不错，适合出去走走", "speaker": "default", "chunk_size_ms": 150}' \
    -o /tmp/tts_stream.wav \
    -w "\n状态: %{http_code} | 大小: %{size_download} bytes\n"

if [ -f /tmp/tts_stream.wav ] && [ -s /tmp/tts_stream.wav ]; then
    echo "✓ 流式音频生成成功"
    echo "  文件: /tmp/tts_stream.wav"
else
    echo "✗ 流式音频生成失败"
fi
echo ""

# 测试 4: 不同说话人
echo "测试 4: 不同说话人"
echo "----------------"
echo "可用说话人: default, female, male (取决于模型配置)"
echo ""

for speaker in default female male; do
    echo "说话人: $speaker"
    curl -s -X POST "${BASE_URL}/tts" \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"我是${speaker}号说话人\", \"speaker\": \"$speaker\"}" \
        -o "/tmp/tts_${speaker}.wav" \
        -w "  状态: %{http_code}\n"
done
echo ""

echo "测试完成！"
echo "生成的音频文件:"
ls -lh /tmp/tts_*.wav 2>/dev/null || echo "  (无文件生成)"
