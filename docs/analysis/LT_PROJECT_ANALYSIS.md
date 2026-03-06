# /opt/lt 项目分析与迁移计划

**分析日期:** 2026-03-05
**项目名称:** LiveTalking - 实时交互式数字人
**目标:** 学习经验并迁移到 SoulX-FlashHead 项目

---

## 📊 项目概览

### 核心特性

LiveTalking 是一个**生产级别的实时数字人系统**，具备以下特性：

- ✅ **WebRTC 实时通信** - aiortc 实现低延迟音视频传输
- ✅ **LLM 集成** - OpenAI 兼容 API，支持多种模型
- ✅ **TTS 集成** - 8 种 TTS 服务（edge, doubao, tencent, azure, fish, sovits, cosyvoice, indextts2, xtts）
- ✅ **ASR 集成** - 4 种 ASR 服务（tencent, funasr, huber, lip）
- ✅ **多模型支持** - musetalk, wav2lip, ultralight
- ✅ **会话管理** - 多会话支持（max 10）
- ✅ **音频处理** - 高质量音频处理器

---

## 🏗️ 架构分析

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    LiveTalking 架构                          │
└─────────────────────────────────────────────────────────────┘

前端 (WebRTC)
    ↓
HTTP/WebSocket 服务器 (aiohttp + Flask)
    ↓
┌───────────────────────────────────────────────────────────┐
│                    会话管理层                               │
│  - 多会话管理 (max 10)                                      │
│  - 会话状态追踪                                              │
│  - 资源分配和释放                                            │
└────────┬──────────────────────────────────────────────────┘
         ↓
┌───────────────────────────────────────────────────────────┐
│                   核心处理层 (BaseReal)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   ASR    │  │   LLM    │  │   TTS    │  │  视频    │  │
│  │  语音识别 │→│ 智能对话 │→│ 语音合成 │→│ 生成    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└───────────────────────────────────────────────────────────┘
         ↓
    WebRTC 媒体流
         ↓
      前端播放
```

---

### 2. 关键组件

#### 2.1 WebRTC 通信 (src/main/app.py)

**实现方式:**
```python
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiohttp import web

async def offer(request):
    # 1. 创建 WebRTC 连接
    pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[...]))
    pcs.add(pc)

    # 2. 设置远程描述
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    await pc.setRemoteDescription(offer)

    # 3. 创建媒体轨道
    player = HumanPlayer(nerfreals[sessionid])
    audio_sender = pc.addTrack(player.audio)
    video_sender = pc.addTrack(player.video)

    # 4. 创建应答
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(text=json.dumps({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
        "sessionid": sessionid
    }))

@pc.on("track")
def on_track(track):
    if track.kind == "audio":
        async def process_audio_frames():
            while True:
                frame = await track.recv()
                audio_array = frame.to_ndarray()
                nerfreals[sessionid].asr.put_audio_frame(audio_array, {})
```

**关键点:**
- ✅ 使用 aiortc 实现 WebRTC
- ✅ 支持音频轨道接收和发送
- ✅ 支持 H.264/VP8 编解码器
- ✅ STUN 服务器配置

---

#### 2.2 LLM 集成 (src/llm/llm.py)

**配置方式:**
```bash
# .env 文件
LLM_MODEL=mimo-v2-flash
OPEN_AI_URL=https://api.xiaomimimo.com/v1
OPEN_AI_API_KEY=sk-cct12qwb4bgmv08z5xg2ia6je67p0p3uaauel81hw6g2e51p
```

**实现代码:**
```python
from openai import OpenAI

def llm_response(message, nerfreal: BaseReal):
    api_key = os.getenv("OPEN_AI_API_KEY")
    base_url = os.getenv("OPEN_AI_URL")
    model = os.getenv("LLM_MODEL", "qwen-plus")

    client = OpenAI(api_key=api_key, base_url=base_url)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': message}
        ],
        stream=True
    )

    result = ""
    for chunk in completion:
        msg = chunk.choices[0].delta.content
        if msg:
            # 按标点符号切分
            for i, char in enumerate(msg):
                if char in ",.!;:，。！？：；":
                    result = result + msg[lastpos:i+1]
                    if len(result) > 10:
                        nerfreal.put_msg_txt(result)
                        result = ""
```

**关键点:**
- ✅ 使用 OpenAI SDK（兼容多种 API）
- ✅ 流式输出（stream=True）
- ✅ 按标点符号切分，提前播放
- ✅ 环境变量配置

---

#### 2.3 TTS 集成 (src/core/ttsreal.py)

**支持的 TTS 服务:**
1. **Edge TTS** - 免费，无需配置
2. **豆包 TTS** - 需要访问令牌
3. **腾讯 TTS** - 需要密钥
4. **Azure TTS** - 需要密钥
5. **Fish TTS** - 本地服务
6. **GPT-SoVITS** - 本地服务
7. **CosyVoice** - 本地服务
8. **IndexTTS2** - 本地服务

**Edge TTS 实现:**
```python
import edge_tts

class EdgeTTS(BaseTTS):
    def txt_to_audio(self, msg: tuple[str, dict]):
        voicename = self.opt.REF_FILE  # "zh-CN-YunxiaNeural"
        text, textevent = msg

        # 异步生成音频
        asyncio.run_until_complete(self.__main(voicename, text))

        # 读取音频流
        self.input_stream.seek(0)
        stream, sample_rate = sf.read(self.input_stream)

        # 重采样到 16kHz
        stream = resampy.resample(stream, sr_orig=sample_rate, sr_new=16000)

        # 按 chunk 发送（实时节奏）
        chunk = 320  # 20ms @ 16kHz
        idx = 0
        while streamlen >= chunk:
            self.parent.put_audio_frame(stream[idx:idx+chunk], eventpoint)
            time.sleep(chunk / 16000)  # 实时节奏
            idx += chunk

    async def __main(self, voicename: str, text: str):
        communicate = edge_tts.Communicate(text, voicename)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                self.input_stream.write(chunk["data"])
```

**关键点:**
- ✅ 多种 TTS 支持
- ✅ 实时节奏控制（time.sleep）
- ✅ 音频重采样
- ✅ 分块发送（20ms chunk）

---

#### 2.4 ASR 集成 (src/core/)

**支持的 ASR 服务:**
1. **腾讯 ASR** - 实时语音识别
2. **FunASR** - 阿里语音识别
3. **Lip ASR** - 本地口型识别
4. **Huber ASR** - 本地模型

**腾讯 ASR 实现:**
```python
class TencentASR(BaseASR):
    def __init__(self, opt, parent: BaseReal):
        self.appid = os.getenv("TENCENT_APPID")
        self.secret_id = os.getenv("TENCENT_ASR_SECRET_ID")
        self.secret_key = os.getenv("TENCENT_ASR_SECRET_KEY")

    def put_audio_frame(self, frame, eventpoint):
        # 累积音频帧
        self.audio_buffer.append(frame)

        # 达到 200ms 时识别
        if len(self.audio_buffer) >= 10:  # 200ms
            audio_data = np.concatenate(self.audio_buffer)
            self.recognize(audio_data)
```

**关键点:**
- ✅ 实时语音识别
- ✅ 缓冲区管理（200ms）
- ✅ 文本输出到 LLM

---

#### 2.5 会话管理

**实现方式:**
```python
nerfreals: Dict[int, BaseReal] = {}  # sessionid: BaseReal

# 会话限制
if len(nerfreals) >= opt.max_session:
    return web.Response(text=json.dumps({
        "code": -1,
        "msg": "reach max session"
    }), status=429)

# 创建会话
sessionid = randN(6)  # 6 位随机数
nerfreals[sessionid] = build_nerfreal(sessionid)

# 清理会话
del nerfreals[sessionid]
```

**关键点:**
- ✅ 会话 ID 随机生成
- ✅ 最大会话数限制
- ✅ 自动清理断开的会话

---

## 🔧 配置文件分析

### .env 配置

```bash
# LLM 配置
LLM_MODEL=mimo-v2-flash
OPEN_AI_URL=https://api.xiaomimimo.com/v1
OPEN_AI_API_KEY=sk-xxx

# TTS 配置
TTS_TYPE=edge
EDGE_TTS_VOICE=zh-CN-YunxiNeural

# ASR 配置
ASR_TYPE=tencent
TENCENT_APPID=xxx
TENCENT_ASR_SECRET_ID=xxx
TENCENT_ASR_SECRET_KEY=xxx

# 其他配置
FPS=30
LOG_LEVEL=INFO
MAX_SESSION=10
LISTEN_PORT=8010
AUDIO_HQ_PROCESSOR=1
AUDIO_CROSSFADE=64
AUDIO_CUTOFF=6000.0
```

---

## 📋 迁移计划

### 阶段一：基础架构迁移 (P0)

#### 1.1 配置管理

**从 /opt/lt 迁移:**
- ✅ .env 配置文件结构
- ✅ 环境变量加载逻辑
- ✅ 多服务配置支持

**迁移到 /opt/digital-human-platform:**
```python
# backend/app/core/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM 配置
    llm_model: str = "qwen-plus"
    openai_url: str = "https://api.xiaomimimo.com/v1"
    openai_api_key: str = ""

    # TTS 配置
    tts_type: str = "edge"
    edge_tts_voice: str = "zh-CN-YunxiNeural"

    # ASR 配置
    asr_type: str = "tencent"
    tencent_appid: str = ""
    tencent_asr_secret_id: str = ""
    tencent_asr_secret_key: str = ""

    # 其他配置
    fps: int = 30
    max_session: int = 5
    listen_port: int = 8000

    class Config:
        env_file = ".env"
```

---

#### 1.2 LLM 服务集成

**创建 LLM 模块:**
```python
# backend/app/services/llm/
├── __init__.py
├── client.py          # OpenAI 兼容客户端
└── prompts.py         # 系统提示词

# backend/app/services/llm/client.py
from openai import OpenAI
from app.core.config import settings

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_url
        )
        self.model = settings.llm_model

    async def chat_stream(self, message: str):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": message}
            ],
            stream=True
        )

        async for chunk in completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _get_system_prompt(self) -> str:
        return """你是一个友好的AI助手，擅长用自然的方式与人交流。
你的回复应该简洁、生动，像真人对话一样。"""
```

---

#### 1.3 TTS 服务集成

**创建 TTS 模块:**
```python
# backend/app/services/tts/
├── __init__.py
├── base.py             # TTS 基类
├── edge_tts.py         # Edge TTS
├── factory.py          # TTS 工厂

# backend/app/services/tts/base.py
from abc import ABC, abstractmethod
import numpy as np

class BaseTTS(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> np.ndarray:
        """合成语音，返回 16kHz numpy 数组"""
        pass

# backend/app/services/tts/edge_tts.py
import edge_tts
import soundfile as sf
import resampy

class EdgeTTS(BaseTTS):
    async def synthesize(self, text: str) -> np.ndarray:
        communicate = edge_tts.Communicate(text, self.voice_name)

        audio_buffer = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_buffer.seek(0)
        stream, sample_rate = sf.read(audio_buffer)

        # 重采样到 16kHz
        if sample_rate != 16000:
            stream = resampy.resample(stream, sample_rate, 16000)

        return stream.astype(np.float32)
```

---

#### 1.4 ASR 服务集成

**创建 ASR 模块:**
```python
# backend/app/services/asr/
├── __init__.py
├── base.py             # ASR 基类
├── tencent_asr.py      # 腾讯 ASR
├── factory.py          # ASR 工厂

# backend/app/services/asr/base.py
from abc import ABC, abstractmethod

class BaseASR(ABC):
    @abstractmethod
    async def recognize(self, audio: np.ndarray) -> str:
        """识别语音，返回文本"""
        pass

# backend/app/services/asr/tencent_asr.py
class TencentASR(BaseASR):
    def __init__(self):
        self.appid = settings.tencent_appid
        self.secret_id = settings.tencent_asr_secret_id
        self.secret_key = settings.tencent_asr_secret_key

    async def recognize(self, audio: np.ndarray) -> str:
        # 实现腾讯云语音识别
        # ...
        pass
```

---

### 阶段二：WebSocket 服务升级 (P0)

**升级现有 WebSocket Handler:**
```python
# backend/app/api/websocket/handler.py

class WebSocketHandler:
    def __init__(self):
        # 现有组件
        self.gpu_manager = GPUMemoryManager(max_sessions=5)
        self.decoders = {}
        self.encoders = {}
        self.buffers = {}

        # 新增组件
        self.asr_clients = {}      # session_id -> ASR 实例
        self.llm_client = LLMClient()
        self.tts_clients = {}      # session_id -> TTS 实例

    async def handle_message(self, websocket: WebSocket, session_id: str, message: dict):
        msg_type = message.get("type")

        if msg_type == "audio":
            await self._handle_audio_chunk(session_id, message)
        elif msg_type == "text":
            await self._handle_text_message(session_id, message)
        elif msg_type == "interrupt":
            await self._handle_interrupt(session_id)

    async def _handle_text_message(self, session_id: str, message: dict):
        """处理文本消息（走 LLM 流程）"""
        text = message.get("text", "")

        # 1. LLM 流式生成
        llm_response = ""
        async for chunk in self.llm_client.chat_stream(text):
            llm_response += chunk

            # 按标点符号切分
            if any(punct in chunk for punct in ",.!?。！？"):
                # 2. TTS 合成
                if session_id not in self.tts_clients:
                    self.tts_clients[session_id] = TTSFactory.create()

                audio = await self.tts_clients[session_id].synthesize(llm_response)

                # 3. 发送到视频生成
                await self._process_audio_for_video(session_id, audio)

                llm_response = ""
```

---

### 阶段三：完整对话流程 (P1)

**端到端流程:**
```python
async def complete_dialogue_flow(session_id: str, user_audio: np.ndarray):
    # 1. ASR 识别用户语音
    user_text = await self.asr_clients[session_id].recognize(user_audio)

    # 2. LLM 生成回复
    ai_text_chunks = []
    async for chunk in self.llm_client.chat_stream(user_text):
        ai_text_chunks.append(chunk)

        # 累积到一句完整的话
        if self._is_complete_sentence("".join(ai_text_chunks)):
            sentence = "".join(ai_text_chunks)

            # 3. TTS 合成 AI 语音
            ai_audio = await self.tts_clients[session_id].synthesize(sentence)

            # 4. 视频生成（SoulX-FlashHead）
            video_frames = await self._generate_video(session_id, ai_audio)

            # 5. 发送到前端
            await self._send_video_packet(session_id, video_frames)

            ai_text_chunks = []
```

---

## 🚀 实施步骤

### Step 1: 创建配置文件

```bash
# 在项目根目录创建 .env
cat > /opt/digital-human-platform/.env << 'EOF'
# LLM 配置
LLM_MODEL=qwen-plus
OPEN_AI_URL=https://api.xiaomimimo.com/v1
OPEN_AI_API_KEY=sk-cct12qwb4bgmv08z5xg2ia6je67p0p3uaauel81hw6g2e51p

# TTS 配置
TTS_TYPE=edge
EDGE_TTS_VOICE=zh-CN-YunxiNeural

# ASR 配置
ASR_TYPE=tencent
TENCENT_APPID=8228021615
TENCENT_ASR_SECRET_ID=YOUR_SECRET_ID_HERE
TENCENT_ASR_SECRET_KEY=YOUR_SECRET_KEY_HERE

# 其他配置
FPS=25
MAX_SESSION=5
LISTEN_PORT=8000
EOF
```

### Step 2: 安装依赖

```bash
cd /opt/digital-human-platform/backend

# 添加到 requirements.txt
cat >> requirements.txt << 'EOF'
openai>=1.0.0
edge-tts>=6.1.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
resampy>=0.4.0
EOF

pip install -r requirements.txt
```

### Step 3: 创建服务模块

```bash
# 创建目录结构
mkdir -p backend/app/services/llm
mkdir -p backend/app/services/tts
mkdir -p backend/app/services/asr

# 创建文件
touch backend/app/services/llm/__init__.py
touch backend/app/services/llm/client.py
touch backend/app/services/tts/__init__.py
touch backend/app/services/tts/base.py
touch backend/app/services/tts/edge_tts.py
touch backend/app/services/tts/factory.py
touch backend/app/services/asr/__init__.py
touch backend/app/services/asr/base.py
touch backend/app/services/asr/factory.py
```

### Step 4: 集成到 WebSocket

修改 `backend/app/api/websocket/handler.py`，添加 LLM + TTS + ASR 支持。

---

## 📊 对比总结

| 特性 | /opt/lt | 我们的项目 | 迁移计划 |
|------|---------|-----------|----------|
| **LLM** | ✅ OpenAI API | ❌ 无 | ✅ P0 立即添加 |
| **TTS** | ✅ 8种服务 | ❌ 无 | ✅ P0 立即添加 |
| **ASR** | ✅ 4种服务 | ❌ 无 | ✅ P0 立即添加 |
| **视频生成** | MuseTalk/Wav2Lip | ✅ SoulX-FlashHead | 保持 |
| **通信协议** | WebRTC | WebSocket | 保持 |
| **会话管理** | ✅ 多会话 | ✅ 已实现 | 优化 |

---

## ✨ 下一步

**立即开始:**
1. 创建 .env 配置文件
2. 创建 LLM/TTS/ASR 服务模块
3. 升级 WebSocket Handler
4. 测试完整对话流程

**目标:** 实现完整的智能数字人对话系统

---

**分析完成时间:** 2026-03-05
**项目状态:** 架构清晰，可立即迁移
**推荐度:** ⭐⭐⭐⭐⭐ (强烈推荐)
