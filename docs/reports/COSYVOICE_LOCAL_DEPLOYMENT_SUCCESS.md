# CosyVoice TTS 本地部署验证报告

**日期**: 2026-03-06
**状态**: ✅ 部署成功

## 部署方式

由于 Docker 构建时间过长（超过 30 分钟），采用了**本地部署方式**。

## 服务配置

- **服务文件**: `/opt/digital-human-platform/docker/vllm-cosyvoice/cosyvoice_server_v2.py`
- **启动脚本**: `/opt/digital-human-platform/docker/run-cosyvoice-local.sh`
- **模型**: CosyVoice-300M (Zero-shot)
- **采样率**: 22050 Hz
- **GPU**: NVIDIA GeForce RTX 5090

## API 端点

### 1. 健康检查
```
GET /health
```

**响应**:
```json
{
    "status": "healthy",
    "service": "CosyVoice TTS",
    "model_loaded": true,
    "gpu_available": true,
    "device": "NVIDIA GeForce RTX 5090"
}
```

### 2. 标准 TTS
```
POST /tts
Content-Type: application/json

{
    "text": "你好，我是数字人助手",
    "prompt_text": "希望你今天能够开心"
}
```

**性能指标**:
- 延迟: 1188ms
- 音频时长: 4.39s
- RTF: 0.27x
- 文件大小: 193 KB

**响应**:
- Content-Type: `audio/wav`
- X-Latency-ms: 延迟（毫秒）
- X-Duration-s: 音频时长（秒）

### 3. 流式 TTS
```
POST /tts/stream
Content-Type: application/json

{
    "text": "你好，我是数字人助手，很高兴认识大家",
    "prompt_text": "希望你今天能够开心",
    "chunk_size_ms": 150
}
```

**性能指标**:
- 总耗时: 2002ms
- 切片数量: 124
- 文件大小: 407 KB

## 技术要点

### CosyVoice-300M 模型特点

1. **Zero-shot 模式**: 不需要预训练的 spk2info.pt 文件
2. **使用 `inference_zero_shot` API**:
   ```python
   for audio_chunk in model.inference_zero_shot(
       tts_text=text,
       prompt_text=prompt_text,
       prompt_wav=ref_wav,
       stream=False
   ):
       # 处理音频片段
   ```

3. **需要提供参考音频**:
   - 默认路径: `/opt/digital-human-platform/models/CosyVoice/pretrained_models/CosyVoice-300M/asset/default_prompt.wav`
   - 或通过 `prompt_audio_url` 参数提供

### 与之前尝试的差异

| 方案 | 结果 | 问题 |
|------|------|------|
| Docker (inference_sft) | ❌ | CosyVoice-300M 不支持 SFT 模式 |
| Docker (torchcodec) | ❌ | 缺少 ffmpeg 依赖 |
| 本地 (zero-shot) | ✅ | 完全正常工作 |

## 启动命令

```bash
source /opt/digital-human-platform/backend/venv/bin/activate

export PYTHONPATH="/opt/digital-human-platform/models/CosyVoice/third_party/Matcha-TTS:/opt/digital-human-platform/models/CosyVoice:$PYTHONPATH"

cd /opt/digital-human-platform/docker/vllm-cosyvoice
python3 cosyvoice_server_v2.py
```

或使用启动脚本：
```bash
bash /opt/digital-human-platform/docker/run-cosyvoice-local.sh
```

## 下一步

CosyVoice TTS 服务已验证可用，可以继续实施五阶段流式架构：

1. ✅ CosyVoice TTS 验证完成
2. ⏳ 阶段1: 项目脚手架与基础环境搭建
3. ⏳ 阶段2: CosyVoice 流式音频生产者实现 (150-200ms 切片)
4. ⏳ 阶段3: SoulX 视觉消费者与内存队列对接
5. ⏳ 阶段4: WebRTC 媒体轨道封装
6. ⏳ 阶段5: 前端接收与展示

## 附录: 音频样例

生成的音频文件: `/tmp/test_cosyvoice.wav`
- 格式: RIFF WAVE
- 编码: Microsoft PCM
- 位深度: 16 bit
- 声道: 单声道
- 采样率: 22050 Hz
