# CosyVoice TTS 测试报告

**时间**: 2026-03-06 08:17
**状态**: ✅ **Cross-lingual 模式工作正常**

---

## 问题诊断

### 零样本模式 (Zero-shot) 问题

- **症状**: 生成的音频几乎静音（峰值 0.0001）
- **错误**: `RuntimeError: sampling reaches max_trials 100 and still get eos`
- **原因**: LLM 在采样时无法生成有效 token，导致音频生成失败

### Cross-lingual 模式成功 ✅

- **症状**: 生成完整、清晰的音频
- **峰值**: 0.38 - 0.51（正常音频水平）
- **RMS**: 0.05 - 0.06（正常音频水平）
- **时长**: 3.3 - 5.5 秒

---

## 成功生成的音频

| 文件 | 内容 | 时长 | 大小 | 峰值 | RMS |
|------|------|------|------|------|-----|
| `cosyvoice_cl_1.wav` | 你好，我是数字人助手... | 3.69秒 | 160 KB | 0.48 | 0.054 |
| `cosyvoice_cl_2.wav` | 今天天气真好... | 3.33秒 | 144 KB | 0.38 | 0.050 |
| `cosyvoice_cl_3.wav` | 这是一个测试音频... | 4.66秒 | 201 KB | 0.51 | 0.061 |
| `cosyvoice_cl_4.wav` | 收到好友从远方寄来的生日礼物... | 5.54秒 | 239 KB | 0.48 | 0.059 |

---

## 使用方法

### Cross-lingual 模式（推荐）

```python
from cosyvoice.cli.cosyvoice import AutoModel
import torchaudio

# 初始化模型
cosyvoice = AutoModel(model_dir='pretrained_models/CosyVoice-300M')

# 参考音频
ref_audio = '/path/to/reference.mp3'

# 生成音频
for output in cosyvoice.inference_cross_lingual(
    '你好，我是数字人助手。',
    ref_audio,
    stream=False
):
    torchaudio.save('output.wav', output['tts_speech'], cosyvoice.sample_rate)
    break
```

### 关键参数

- **model_dir**: `CosyVoice-300M`（支持 Cross-lingual）
- **ref_audio**: 参考音频路径（用于声音克隆）
- **stream**: `False`（返回完整音频）或 `True`（流式输出）
- **sample_rate**: 22050 Hz（CosyVoice 默认）

---

## 依赖修复

安装的依赖包：

```bash
pip install conformer==0.3.2
pip install hydra-core==1.3.2 hydra-colorlog==1.2.0
pip install rootutils phonemizer Unidecode
pip install pyarrow pyworld
pip install 'setuptools<75'
```

---

## 性能指标

- **RTF (Real-Time Factor)**: 0.26 - 0.35
- **生成速度**: 约 3 秒音频 / 1 秒处理时间
- **采样率**: 22050 Hz
- **编码**: WAV (PCM)

---

## 后续集成

### 后端集成

在 `app/services/tts/cosyvoice_tts.py` 中：

```python
async def synthesize(self, text: str) -> np.ndarray:
    # 使用 Cross-lingual 模式
    for output in self.cosyvoice.inference_cross_lingual(
        text,
        self.speaker_reference,
        stream=False
    ):
        audio = output['tts_speech'].numpy().squeeze()
        # 重采样到 16000 Hz
        audio_16k = librosa.resample(audio, orig_sr=22050, target_sr=16000)
        return audio_16k
```

### API 调用

```bash
# 使用 CosyVoice 生成音频
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是数字人助手。",
    "tts_type": "cosyvoice",
    "reference_audio": "/path/to/reference.mp3"
  }'
```

---

## 参考音频

当前使用: `assets/simple_voice.mp3` (16.56秒)

建议:
- 使用清晰、无背景音的人声
- 时长 5-20 秒
- 单声道，采样率 44100 Hz

---

## 测试命令

```bash
# 播放生成的音频
ffplay /opt/digital-human-platform/assets/cosyvoice_cl_1.wav

# 运行测试
cd /opt/digital-human-platform/models/CosyVoice
source /opt/digital-human-platform/backend/venv/bin/activate
python /tmp/test_cosyvoice_final.py
```

---

**验证人**: Claude AI
**验证日期**: 2026-03-06
