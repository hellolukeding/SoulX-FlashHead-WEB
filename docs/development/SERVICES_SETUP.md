# LLM + TTS + ASR 服务配置指南

**更新日期:** 2026-03-05
**目标:** 配置完整的智能对话系统

---

## 📋 服务状态

| 服务 | 状态 | 说明 |
|------|------|------|
| **LLM** | ✅ 已实现 | OpenAI 兼容 API |
| **TTS** | ✅ 已实现 | CosyVoice (推荐) + Edge TTS (fallback) |
| **ASR** | ✅ 已实现 | MockASR (待实现真实服务) |

---

## 🚀 快速配置

### 1. LLM 服务配置

**已配置的 API:**
```bash
# .env 文件
LLM_MODEL=qwen-plus
OPEN_AI_URL=https://api.xiaomimimo.com/v1
OPEN_AI_API_KEY=sk-cct12qwb4bgmv08z5xg2ia6je67p0p3uaauel81hw6g2e51p
```

**支持的模型:**
- ✅ Qwen 系列 (qwen-plus, qwen-turbo, qwen-max)
- ✅ GLM 系列 (glm-4, glm-4-plus)
- ✅ Claude 系列 (claude-3-5-sonnet-20241022)
- ✅ GPT 系列 (gpt-4o, gpt-4o-mini)

**使用其他 API:**
```bash
# OpenAI 官方
LLM_MODEL=gpt-4o-mini
OPEN_AI_URL=https://api.openai.com/v1
OPEN_AI_API_KEY=sk-your-api-key

# 阿里百炼
LLM_MODEL=qwen-plus
OPEN_AI_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPEN_AI_API_KEY=sk-your-api-key
```

---

### 2. TTS 服务配置

#### 推荐: CosyVoice (阿里开源，效果最好)

**安装 CosyVoice:**
```bash
cd /opt/digital-human-platform/backend

# 安装 CosyVoice
source venv/bin/activate
pip install -U cosyvoice

# 下载模型（首次运行时自动下载）
python -c "from cosyvoice import CosyVoice; CosyVoice('CosyVoice-300M-SFT')"
```

**配置:**
```bash
# .env 文件
TTS_TYPE=cosyvoice
COSYVOICE_MODEL=CosyVoice-300M-SFT
COSYVOICE_VOICE=中文女
```

**可用模型:**
- `CosyVoice-300M-SFT` - 微调模型（推荐）
- `CosyVoice-300M-Instruct` - 指令模型

**可用音色:**
- `中文女`
- `中文男`
- `英文女`
- `英文男`
- `日语女`
- `粤语女`
- `韩语女`

---

#### 备选: Edge TTS (微软，免费)

**无需安装，已内置。**

**配置:**
```bash
# .env 文件
TTS_TYPE=edge
EDGE_TTS_VOICE=zh-CN-YunxiNeural
```

**可用音色:**
- `zh-CN-YunxiNeural` (云阳，男声)
- `zh-CN-XiaoxiaoNeural` (晓晓，女声)
- `zh-CN-YunyangNeural` (云扬，男声)
- `zh-CN-XiaoyiNeural` (晓伊，女声)

---

#### 其他 TTS 服务

**豆包 TTS (需要配置):**
```bash
TTS_TYPE=doubao
DOUBAO_APPID=8228021615
DOUBAO_ACCESS_TOKEN=your-token
DOUBAO_SECRET_KEY=your-secret-key
DOUBAO_VOICE_ID=zh_female_tianxinxiaomei_emo_v2_mars_bigtts
```

**腾讯 TTS (需要配置):**
```bash
TTS_TYPE=tencent
TENCENT_APPID=your-appid
TENCENT_SECRET_ID=your-secret-id
TENCENT_SECRET_KEY=your-secret-key
TENCENT_VOICE_TYPE=1001
```

---

### 3. ASR 服务配置

**当前状态:** 使用 MockASR（模拟识别）

**待实现:**
- 腾讯 ASR
- FunASR (阿里)
- Lip ASR (本地口型识别)

**临时方案:**
```bash
# .env 文件
ASR_TYPE=mock  # 模拟识别，返回固定文本
```

---

## 📊 对比: CosyVoice vs Edge TTS

| 特性 | CosyVoice | Edge TTS |
|------|-----------|----------|
| **音色质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **中文支持** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **情感表达** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **响应速度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **网络依赖** | ❌ 本地 | ✅ 在线 |
| **费用** | 免费 | 免费 |
| **安装难度** | ⚠️ 需要安装 | ✅ 无需安装 |
| **音色数量** | 20+ | 10+ |

**推荐:**
- **生产环境:** CosyVoice（效果好，本地运行）
- **开发测试:** Edge TTS（无需安装，快速开始）

---

## 🔧 安装 CosyVoice

### 方式一: pip 安装（推荐）

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate
pip install -U cosyvoice
```

### 方式二: 源码安装

```bash
cd /opt
git clone https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
pip install -r requirements.txt
```

### 验证安装

```python
python -c "from cosyvoice import CosyVoice; print('✅ CosyVoice 安装成功')"
```

---

## 🧪 测试服务

### 测试 LLM

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate
python << 'EOF'
import asyncio
from app.services.llm import get_llm_client

async def test():
    llm = get_llm_client()
    if llm.is_available():
        response = await llm.chat("你好")
        print(f"LLM 回复: {response}")
    else:
        print("❌ LLM 未配置")

asyncio.run(test())
EOF
```

### 测试 TTS

```bash
python << 'EOF'
import asyncio
from app.services.tts import get_tts

async def test():
    tts = get_tts()
    audio = await tts.synthesize("你好，我是AI数字人助手。")
    print(f"✅ TTS 正常，音频时长: {len(audio)/16000:.2f}秒")

asyncio.run(test())
EOF
```

### 测试完整流程

```bash
python tests/integration/test_llm_tts_asr.py
```

---

## 🎯 完整对话流程

### 流程图

```
用户语音输入
    ↓
┌──────────────┐
│   ASR 节点    │ 识别用户说了什么
│   (待实现)    │
└──────┬───────┘
       ↓ 用户文本
┌──────────────┐
│   LLM 节点    │ AI 思考回复
│   (已实现)    │
└──────┬───────┘
       ↓ AI回复文本
┌──────────────┐
│   TTS 节点    │ 生成 AI 语音
│   (已实现)    │
└──────┬───────┘
       ↓ AI音频 (16kHz)
┌──────────────────┐
│ SoulX-FlashHead  │ 生成口型视频
│   (已实现)       │
└──────┬───────────┘
       ↓ 视频流
   前端播放
```

### 实施状态

| 阶段 | 组件 | 状态 |
|------|------|------|
| 1 | ASR | 🟡 MockASR |
| 2 | LLM | ✅ 已实现 |
| 3 | TTS | ✅ 已实现 |
| 4 | 视频生成 | ✅ 已实现 |
| 5 | 集成 | 🔴 待实施 |

---

## 📝 下一步

1. **安装 CosyVoice** (推荐)
   ```bash
   pip install -U cosyvoice
   ```

2. **配置 LLM API**
   ```bash
   # 编辑 .env
   OPEN_AI_API_KEY=your-api-key
   ```

3. **测试服务**
   ```bash
   python tests/integration/test_llm_tts_asr.py
   ```

4. **集成到 WebSocket**
   - 修改 `backend/app/api/websocket/handler.py`
   - 添加完整对话流程

---

**配置完成时间:** 2026-03-05
**状态:** ✅ 基础服务已实现，待集成
