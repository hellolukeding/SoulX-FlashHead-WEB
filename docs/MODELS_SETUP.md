# 📦 模型配置文档

**更新日期:** 2026-03-05
**说明:** 所有模型已移动到项目的 models 目录

---

## 📁 模型目录结构

```
/opt/digital-human-platform/models/
├── SoulX-FlashHead-1_3B/          # SoulX 数字人模型 (14GB)
│   ├── Model_Lite/                 # 轻量级模型
│   ├── Model_Pro/                  # 专业模型
│   ├── VAE_LTX/                    # LTX VAE
│   ├── VAE_Wan/                    # Wan VAE
│   └── config.json
├── wav2vec2-base-960h/            # 音频特征提取模型 (1.1GB)
│   ├── pytorch_model.bin
│   ├── model.safetensors
│   └── config.json
└── CosyVoice/                     # CosyVoice 语音合成 (15GB)
    ├── cosyvoice/                  # CosyVoice 源码
    ├── pretrained_models/         # 预训练模型
    │   ├── CosyVoice-300M/         # 300M 模型
    │   ├── CosyVoice-ttsfrd/       # TTSFRD 模型
    │   └── Fun-CosyVoice3-0.5B/    # 3-0.5B 模型
    └── examples/                   # 示例代码
```

---

## 🎯 模型配置

### 1. SoulX-FlashHead 模型

**路径:** `/opt/digital-human-platform/models/SoulX-FlashHead-1_3B`

**配置代码:**
```python
ckpt_dir = "/opt/digital-human-platform/models/SoulX-FlashHead-1_3B"
```

**模型变体:**
- `Model_Lite` - 轻量级模型（推荐，速度快）
- `Model_Pro` - 专业模型（质量更高）

**使用方式:**
```python
from app.core.inference.flashhead_engine import FlashHeadInferenceEngine, InferenceConfig

config = InferenceConfig(model_type="lite")
engine = FlashHeadInferenceEngine(config)
engine.load_model(reference_image_path)
```

---

### 2. wav2vec2-base-960h 模型

**路径:** `/opt/digital-human-platform/models/wav2vec2-base-960h`

**配置代码:**
```python
wav2vec_dir = "/opt/digital-human-platform/models/wav2vec2-base-960h"
```

**作用:** 音频特征提取（用于驱动视频生成）

---

### 3. CosyVoice 模型

**路径:** `/opt/digital-human-platform/models/CosyVoice`

**配置代码:**
```python
import sys
sys.path.insert(0, "/opt/digital-human-platform/models/CosyVoice")

from cosyvoice import CosyVoice

cosyvoice = CosyVoice("CosyVoice-300M-SFT")
```

**可用模型:**
- `CosyVoice-300M` - 300M 参数模型（推荐）
- `CosyVoice-ttsfrd` - TTSFRD 模型
- `Fun-CosyVoice3-0.5B` - 0.5B 参数模型

**使用方式:**
```python
from app.services.tts import get_tts

tts = get_tts()
audio = await tts.synthesize("你好，我是AI数字人助手。")
```

---

## 🔧 配置文件更新

### backend/app/core/config.py

```python
# 模型配置
MODEL_PATH: str = "/opt/digital-human-platform/models"
FLASHHEAD_MODEL: str = "SoulX-FlashHead-1_3B"
WAV2VEC_MODEL: str = "wav2vec2-base-960h"
COSYVOICE_PATH: str = "/opt/digital-human-platform/models/CosyVoice"

# 模型完整路径
FLASHHEAD_MODEL_PATH = os.path.join(MODEL_PATH, FLASHHEAD_MODEL)
WAV2VEC_MODEL_PATH = os.path.join(MODEL_PATH, WAV2VEC_MODEL)
```

### backend/app/core/inference/flashhead_engine.py

```python
# 模型路径
ckpt_dir = "/opt/digital-human-platform/models/SoulX-FlashHead-1_3B"
wav2vec_dir = "/opt/digital-human-platform/models/wav2vec2-base-960h"
```

### backend/app/services/tts/cosyvoice_tts.py

```python
# CosyVoice 路径
COSYVOICE_ROOT = "/opt/digital-human-platform/models/CosyVoice"
sys.path.insert(0, COSYVOICE_ROOT)
```

---

## 📊 模型大小统计

| 模型 | 大小 | 用途 |
|------|------|------|
| **SoulX-FlashHead-1_3B** | 14GB | 数字人视频生成 |
| **wav2vec2-base-960h** | 1.1GB | 音频特征提取 |
| **CosyVoice** | 15GB | 语音合成 |
| **总计** | ~30GB | - |

---

## ✅ 验证模型

### 验证 SoulX-FlashHead

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate

python << 'EOF'
import os
print(f"SoulX-FlashHead 模型存在: {os.path.exists('/opt/digital-human-platform/models/SoulX-FlashHead-1_3B')}")
print(f"wav2vec2 模型存在: {os.path.exists('/opt/digital-human-platform/models/wav2vec2-base-960h')}")
EOF
```

### 验证 CosyVoice

```bash
python << 'EOF'
import sys
sys.path.insert(0, "/opt/digital-human-platform/models/CosyVoice")

try:
    from cosyvoice import CosyVoice
    print("✅ CosyVoice 导入成功")
except Exception as e:
    print(f"❌ CosyVoice 导入失败: {e}")
EOF
```

---

## 🚀 使用模型

### 测试视频生成

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate

python tests/integration/test_flashhead_engine.py
```

### 测试 CosyVoice TTS

```bash
python tests/integration/test_llm_tts_asr.py
```

---

## 📝 注意事项

1. **不要使用符号链接** - 所有模型都已复制到项目目录
2. **模型路径已更新** - 所有配置文件已更新
3. **总大小 30GB** - 确保有足够的磁盘空间
4. **GPU 内存** - 建议至少 32GB 显存（RTX 5090）

---

**配置完成时间:** 2026-03-05
**模型状态:** ✅ 所有模型已迁移并配置
