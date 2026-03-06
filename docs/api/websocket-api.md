# WebSocket API 文档

## 连接信息

- **URL**: `ws://localhost:8000/ws`
- **协议**: WebSocket
- **认证**: 通过 Token 参数

## 连接建立

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=<jwt_token>');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

## 消息格式

所有消息使用 JSON 格式：

```json
{
  "type": "message_type",
  "data": { ... },
  "timestamp": "2026-03-05T05:00:00Z"
}
```

## 客户端 → 服务器消息

### 1. 创建会话

**请求**:
```json
{
  "type": "create_session",
  "data": {
    "model_type": "lite",
    "reference_image": "base64_encoded_image",
    "config": {
      "fps": 25,
      "resolution": "512x512"
    }
  }
}
```

**响应**:
```json
{
  "type": "session_created",
  "data": {
    "session_id": "uuid",
    "status": "ready"
  }
}
```

### 2. 发送音频数据

**请求**:
```json
{
  "type": "audio_chunk",
  "data": {
    "session_id": "uuid",
    "audio_data": "base64_encoded_audio",
    "sequence": 1,
    "timestamp": "2026-03-05T05:00:00Z"
  }
}
```

**响应**:
```json
{
  "type": "audio_received",
  "data": {
    "session_id": "uuid",
    "sequence": 1,
    "status": "processing"
  }
}
```

### 3. 暂停会话

**请求**:
```json
{
  "type": "pause_session",
  "data": {
    "session_id": "uuid"
  }
}
```

**响应**:
```json
{
  "type": "session_paused",
  "data": {
    "session_id": "uuid",
    "status": "paused"
  }
}
```

### 4. 恢复会话

**请求**:
```json
{
  "type": "resume_session",
  "data": {
    "session_id": "uuid"
  }
}
```

**响应**:
```json
{
  "type": "session_resumed",
  "data": {
    "session_id": "uuid",
    "status": "active"
  }
}
```

### 5. 关闭会话

**请求**:
```json
{
  "type": "close_session",
  "data": {
    "session_id": "uuid"
  }
}
```

**响应**:
```json
{
  "type": "session_closed",
  "data": {
    "session_id": "uuid",
    "status": "closed"
  }
}
```

## 服务器 → 客户端消息

### 1. 视频帧数据

**消息**:
```json
{
  "type": "video_frame",
  "data": {
    "session_id": "uuid",
    "frame_data": "base64_encoded_frame",
    "sequence": 1,
    "timestamp": "2026-03-05T05:00:00Z",
    "fps": 25
  }
}
```

### 2. 会话状态更新

**消息**:
```json
{
  "type": "session_status",
  "data": {
    "session_id": "uuid",
    "status": "active",
    "latency_ms": 200,
    "fps": 25
  }
}
```

### 3. 错误消息

**消息**:
```json
{
  "type": "error",
  "data": {
    "code": 400,
    "message": "Invalid audio format",
    "details": {
      "expected": "16kHz PCM",
      "received": "44.1kHz PCM"
    }
  }
}
```

### 4. 心跳消息

**消息**:
```json
{
  "type": "ping",
  "data": {
    "timestamp": "2026-03-05T05:00:00Z"
  }
}
```

**客户端响应**:
```json
{
  "type": "pong",
  "data": {
    "timestamp": "2026-03-05T05:00:00Z"
  }
}
```

## 使用示例

### JavaScript 客户端

```javascript
class DigitalHumanClient {
  constructor(token, onVideoFrame, onError) {
    this.ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
    this.sessionId = null;
    this.sequence = 0;

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.onVideoFrame = onVideoFrame;
    this.onError = onError;
  }

  handleMessage(message) {
    switch (message.type) {
      case 'video_frame':
        this.onVideoFrame(message.data);
        break;
      case 'error':
        this.onError(message.data);
        break;
      case 'session_created':
        this.sessionId = message.data.session_id;
        console.log('Session created:', this.sessionId);
        break;
      default:
        console.log('Unhandled message:', message);
    }
  }

  createSession(referenceImage, config = {}) {
    this.ws.send(JSON.stringify({
      type: 'create_session',
      data: {
        model_type: config.modelType || 'lite',
        reference_image: referenceImage,
        config: {
          fps: config.fps || 25,
          resolution: config.resolution || '512x512'
        }
      }
    }));
  }

  sendAudioChunk(audioData) {
    this.sequence++;
    this.ws.send(JSON.stringify({
      type: 'audio_chunk',
      data: {
        session_id: this.sessionId,
        audio_data: btoa(String.fromCharCode(...new Uint8Array(audioData))),
        sequence: this.sequence,
        timestamp: new Date().toISOString()
      }
    }));
  }

  closeSession() {
    this.ws.send(JSON.stringify({
      type: 'close_session',
      data: {
        session_id: this.sessionId
      }
    }));
  }

  disconnect() {
    this.ws.close();
  }
}

// 使用示例
const client = new DigitalHumanClient(
  'your_jwt_token',
  (videoData) => {
    console.log('Received video frame:', videoData.sequence);
    // 显示视频帧
  },
  (error) => {
    console.error('Error:', error.message);
  }
);

// 创建会话
const referenceImage = 'base64_encoded_image';
client.createSession(referenceImage, {
  modelType: 'lite',
  fps: 25
});

// 发送音频
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (event) => {
      client.sendAudioChunk(event.data);
    };
    mediaRecorder.start(100); // 每100ms发送一次
  });
```

## 性能优化建议

### 1. 音频分块大小

推荐：**100-200ms** 的音频块

```javascript
const CHUNK_DURATION = 150; // ms
const SAMPLE_RATE = 16000;
const CHUNK_SIZE = CHUNK_DURATION * SAMPLE_RATE / 1000; // samples
```

### 2. 视频帧缓冲

```javascript
const frameBuffer = [];
const BUFFER_SIZE = 5; // 缓冲5帧

function onVideoFrame(frameData) {
  frameBuffer.push(frameData);

  if (frameBuffer.length >= BUFFER_SIZE) {
    // 播放缓冲的帧
    playFrames(frameBuffer);
    frameBuffer.length = 0;
  }
}
```

### 3. 连接重连

```javascript
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

ws.onclose = () => {
  if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    setTimeout(() => {
      reconnectAttempts++;
      connect(); // 重新连接
    }, 1000 * reconnectAttempts);
  }
};
```

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 连接失败 | 自动重连 |
| 音频格式错误 | 转换音频格式 |
| 会话超时 | 重新创建会话 |
| 推理失败 | 降级处理 |
