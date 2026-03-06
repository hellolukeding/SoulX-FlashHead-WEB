# 🔍 根本原因分析

**分析时间**: 2026-03-06
**状态**: 问题已定位，准备修复

---

## 问题清单

### ❌ 问题1: LLM 未配置
```
WARNING  | app.services.llm.client:__init__:24 - ⚠️  OPEN_AI_API_KEY 未配置，LLM 功能不可用
ERROR    | app.services.llm.client:chat_stream:66 - ❌ LLM 客户端未初始化
```

**原因**: `.env` 文件中没有配置 `OPEN_AI_API_KEY`

**影响**: 所有回复都是固定的测试响应

---

### ❌ 问题2: CosyVoice 模型目录不存在
```
ERROR    | app.services.tts.cosyvoice_tts:__init__:71 - [CosyVoice] 模型目录不存在: /opt/digital-human-platform/models/CosyVoice/pretrained_models/CosyVoice-300M-SFT
WARNING  | app.services.tts.cosyvoice_tts:__init__:72 - [CosyVoice] 回退到 Edge TTS
```

**原因**: CosyVoice 模型文件路径不正确

**影响**: 使用 Edge TTS 而不是 CosyVoice

---

### ❌ 问题3: SoulX-FlashHead 音频处理失败（核心问题）
```
ERROR    | app.core.inference.flashhead_engine:process_audio:140 - 音频处理失败:
got EinopsError(' Error while processing rearrange-reduction pattern "b (f l) c -> (b f) l c".\n
Input tensor shape: torch.Size([1, 1280, 1536]). Additional info: {\'f\': 36}.\n
Shape mismatch, can\'t divide axis of length 1280 in chunks of 36')
```

**原因**: 音频长度 (1280) 不能被 36 整除

**SoulX-FlashHead 要求**:
- 音频长度必须是 36 的倍数
- 采样率必须是 16000 Hz
- 音频长度应该是: `n * 36 / 50 = n * 0.72 秒`

**当前问题**:
- 音频长度: 180096 samples ≈ 11.26 秒
- 180096 / 36 = 5002.666... ❌ 不能整除！

---

## 🔧 解决方案

### 方案1: 修复 LLM 配置

```bash
# 编辑 .env 文件
cd /opt/digital-human-platform/backend
cat .env
```

需要添加:
```env
OPEN_AI_API_KEY=your_api_key_here
OPEN_AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

### 方案2: 修复 CosyVoice 路径

检查 CosyVoice 模型是否存在:
```bash
ls -la /opt/digital-human-platform/models/CosyVoice/
```

### 方案3: 修复 SoulX-FlashHead 音频长度（核心）

**问题分析**:
```
音频长度 = 180096 samples (11.26秒)
采样率 = 16000 Hz
帧率 = 50 fps

每帧样本数 = 16000 / 50 = 320
有效帧数 = 180096 / 320 = 562.8

SoulX-FlashHead 要求:
- 音频编码后的序列长度必须是 36 的倍数
- 180096 samples 编码后 → 1280 tokens
- 1280 / 36 = 35.555... ❌
```

**修复方法**: 填充音频到 36 的倍数

```python
# 计算需要填充的长度
audio_length = len(audio)
# 编码后的长度 (大约是音频长度 / 140)
encoded_length = audio_length // 140

# 需要填充到 36 的倍数
padding_needed = (36 - (encoded_length % 36)) % 36
audio_padding = padding_needed * 140

# 填充音频
padded_audio = np.concatenate([
    audio,
    np.zeros(audio_padding, dtype=np.float32)
])
```

---

## 📋 修复优先级

1. **🔴 高优先级**: 修复 SoulX-FlashHead 音频长度问题
2. **🟡 中优先级**: 配置 LLM API
3. **🟢 低优先级**: 配置 CosyVoice 路径

---

## 🎯 下一步行动

1. 立即修复 SoulX-FlashHead 音频长度问题
2. 配置 LLM API
3. 测试完整流程
