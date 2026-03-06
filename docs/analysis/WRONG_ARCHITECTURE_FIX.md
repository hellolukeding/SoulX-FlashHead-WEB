# 🎯 数字人视频通话 - WebRTC 架构重构方案

**根本问题**: 当前使用 WebSocket + MSE 批量传输架构，这不是实时视频通话的正确架构

---

## 📊 架构对比

### 错误架构 (当前)

```
用户发消息
    ↓ 等待 10+ 秒
    ↓ 后端生成完整视频
    ↓ 一次性发送所有数据 (WebSocket JSON)
    ↓ 前端等待接收完整数据
    ↓ 播放一次视频
    ↓ 空白期 10+ 秒
```

**问题:**
- ❌ 用户等待时间过长 (10-15秒)
- ❌ 不像实时视频通话
- ❌ 体验极差

---

### 正确架构 (参考 /opt/digit)

```
用户发消息
    ↓ 1 秒内
后端开始处理
    ↓
    ├─→ LLM 生成文本 (1秒)
    ├─→ TTS 合成音频 (2秒)
    └─→ 视频生成 (同时进行)

    ↓ 立即开始流式发送
    ↓ 每秒发送 1 帧 (25 FPS)
    ↓ 通过 WebRTC (UDP)
    ↓
┌─────────────────────────────────────────┐
│ 前端 WebRTC 接收                        │
│  RTCPeerConnection                        │
│    ├─ videoTrack: 接收视频帧               │
│    └─ audioTrack: 接收音频                 │
│                                          │
│  <video> 元素自动播放                      │
│  持续流畅，无空白期                        │
└─────────────────────────────────────────┘
```

**优势:**
- ✅ 1-2秒内开始播放
- ✅ 持续流畅播放
- ✅ 像真实视频通话
- ✅ 无明显等待

---

## 🔧 技术实现

### 后端改造

**使用 aiortc (Python WebRTC 库)**

```python
# 安装 aiortc
pip install aiortc

# 实现视频轨道
from aiortc import MediaStreamTrack, VideoFrame
import cv2
import numpy as np

class DigitalHumanVideoTrack(MediaStreamTrack):
    """数字人视频轨道"""

    kind = "video"

    def __init__(self, wav2lip_processor):
        super().__init__()
        self.wav2lip = wav2lip_processor
        self._queue = asyncio.Queue(maxsize=200)
        self._timestamp = 0
        self._frame_count = 0
        VIDEO_CLOCK_RATE = 90000
        VIDEO_PTIME = 1.0 / 25  # 25fps

    async def recv(self):
        """持续返回视频帧"""
        while True:
            # 从队列获取帧
            frame, _ = await self._queue.get()

            # 设置时间戳
            frame.pts = self._timestamp
            frame.time_base = fractions.Fraction(1, VIDEO_CLOCK_RATE)
            self._timestamp += int(VIDEO_PTIME * VIDEO_CLOCK_RATE)

            # 帧率控制：确保 25 FPS
            await asyncio.sleep(0.04)  # 1/25秒

            return frame

    async def add_frame(self, frame):
        """添加视频帧到队列"""
        await self._queue.put(frame)
```

### 前端改造

**使用 RTCPeerConnection (WebRTC)**

```typescript
// 创建 WebRTC 连接
const pc = new RTCPeerConnection({
    sdpSemantics: 'unified-plan'
});

// 添加视频轨道 (接收模式)
pc.addTransceiver('video', { direction: 'recvonly' });
pc.addTransceiver('audio', { direction: 'recvonly' });

// 监听轨道
pc.ontrack = (event) => {
    if (event.track.kind === 'video') {
        videoRef.current.srcObject = event.streams[0];
        videoRef.current.play().catch(e => console.error('播放失败:', e));
    } else if (event.track.kind === 'audio') {
        audioRef.current.srcObject = event.streams[0];
    }
};

// 创建 Offer
const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

// 发送到后端
const response = await fetch('/api/v1/offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        sdp: pc.localDescription.sdp
    })
});

// 设置远程描述
await pc.setRemoteDescription(await response.json());
```

---

## 📋 实施步骤

### 第1步: 安装 aiortc

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate
pip install aiortc opencv-python numpy
```

### 第2步: 创建 WebRTC 后端端点

```python
# backend/app/api/webrtc/video.py
from fastapi import FastAPI
from aiortc import MediaStreamTrack, VideoFrame, RTCConfiguration
from fastapi import WebSocket
import cv2
import numpy as np

router = APIRouter()

@router.post("/offer")
async def negotiate_offer(payload: dict):
    """WebRTC SDP 协商"""
    sdp = payload.get('sdp')

    # 创建 PeerConnection
    pc = RTCPeerConnection(RTCConfiguration(
        ice_servers=[{'urls': 'stun:stun.l.google.com:19302'}]
    )

    # 设置远程描述
    await pc.set_remote_description(
        RTCSessionDescription(sdp=sdp, type='answer')
    )

    # 添加视频轨道
    video_track = DigitalHumanVideoTrack()
    pc.addTrack(video_track)

    # 创建答案
    answer = await pc.create_answer()

    return {
        "sdp": answer.sdp,
        "type": "answer"
    }

@router.websocket("/video")
async def video_stream():
    """WebRTC 视频流"""
    # 实现 WebSocket 信令服务器
    pass
```

### 第3步: 修改前端为 WebRTC

**完全参考 /opt/digit 的实现**

---

## 🎯 预期效果

### 优化前
```
用户: 你好
      ↓ 等待 13 秒
      ↓ 显示视频（一次播放结束）
用户感受: 😡 极差
```

### 优化后
```
用户: 你好
      ↓ 1 秒
      ↓ 开始播放音频
      ↓ 2-3 秒
      ↓ 看到数字人视频
      ↓ 持续流畅播放
用户感受: 😊 像真实视频通话
```

---

## ⏱️ 实施时间

**阶段1: 后端 WebRTC (2-3天)**
- 安装 aiortc
- 实现 VideoTrack
- 实现 SDP 协商

**阶段2: 前端 WebRTC (1-2天)**
- 修改为 RTCPeerConnection
- 实现轨道接收
- 测试视频播放

**阶段3: 集成测试 (1天)**
- 端到端测试
- 性能调优
- 上线部署

**总计: 4-6天**

---

## ✅ 结论

**必须重构为 WebRTC 架构！**

当前 WebSocket + MSE 架构根本不适合实时视频通话场景。

参考项目 /opt/digit 使用 WebRTC + aiortc 架构，这才是正确的方向。

立即开始实施！
