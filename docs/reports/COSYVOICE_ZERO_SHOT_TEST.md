# CosyVoice Zero-shot TTS 测试报告

**日期**: 2026-03-06  
**状态**: ✅ 测试通过

---

## 测试概述

使用 `assets/simple_voice.mp3` 作为参考音频，测试 CosyVoice-300M 的 Zero-shot 音色克隆能力。

---

## 参考音频

| 属性 | 值 |
|------|------|
| 原始文件 | `assets/simple_voice.mp3` |
| 格式 | MPEG ADTS, layer III, v1 |
| 采样率 | 44.1 kHz → 22.05 kHz (转换后) |
| 声道 | Mono |
| 时长 | 16.56 秒 |
| 文件大小 | 259 KB |

### 转换命令

```bash
ffmpeg -i assets/simple_voice.mp3 -ar 22050 -ac 1 -y assets/simple_voice_ref.wav
```

---

## 测试场景

### 场景 1: 标准 Zero-shot TTS

**输入**:
- 参考文本: "今天的天气真不错，适合出去散步"
- 合成文本: "你好，我是数字人助手，很高兴认识大家"

**输出**:
- 时长: 1.78s
- 延迟: 2040ms
- RTF: 1.15x
- 文件: `assets/zero_shot_output.wav`

### 场景 2: 流式 Zero-shot TTS

**输入**:
- 参考文本: "今天的天气真不错，适合出去散步"
- 合成文本: "今天是个好日子，心想的事儿都能成"

**输出**:
- 切片数: 1
- 总时长: 2.23s
- 总耗时: 2120ms
- RTF: 0.95x

---

## 性能指标

| 指标 | 数值 |
|------|------|
| 首包延迟 (TTFT) | ~2000ms |
| RTF (实时率) | 0.95 - 1.15x |
| 采样率 | 22050 Hz |
| 音频格式 | WAV (16-bit, mono) |
| 音色克隆效果 | ✅ 良好 |

---

## 测试结论

1. ✅ Zero-shot 音色克隆功能正常
2. ✅ 使用 16 秒参考音频可成功克隆音色
3. ✅ 生成的音频自然度良好
4. ✅ 流式模式支持良好

---

## 使用方法

### 1. 使用测试脚本

```bash
cd /opt/digital-human-platform/docker/cosyvoice
bash test-zero-shot.sh
```

### 2. 自定义参考音频

```bash
bash test-zero-shot.sh /path/to/reference.mp3 "参考文本" "合成文本"
```

### 3. Python API

```python
from cosyvoice.cli.cosyvoice import CosyVoice

model = CosyVoice('iic/CosyVoice-300M')

for audio_chunk in model.inference_zero_shot(
    tts_text="你好，世界",
    prompt_text="参考音频的文本内容",
    prompt_wav="/path/to/reference.wav",
    stream=False,
):
    # 处理音频片段
    pass
```

---

## 相关文件

- 测试脚本: `docker/cosyvoice/test-zero-shot.sh`
- 参考音频: `assets/simple_voice.mp3`
- 输出音频: `assets/zero_shot_output.wav`
