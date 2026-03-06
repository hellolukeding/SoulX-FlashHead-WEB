# REST API 文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

## API 端点

### 1. 会话管理

#### 1.1 创建会话

**请求**:
```http
POST /api/v1/sessions
Content-Type: application/json
Authorization: Bearer <token>

{
  "model_type": "lite",
  "reference_image": "base64_encoded_image",
  "config": {
    "fps": 25,
    "resolution": "512x512"
  }
}
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "uuid",
    "status": "ready",
    "created_at": "2026-03-05T05:00:00Z"
  }
}
```

#### 1.2 获取会话状态

**请求**:
```http
GET /api/v1/sessions/{session_id}
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "uuid",
    "status": "active",
    "fps": 25,
    "latency_ms": 200,
    "created_at": "2026-03-05T05:00:00Z",
    "updated_at": "2026-03-05T05:05:00Z"
  }
}
```

#### 1.3 关闭会话

**请求**:
```http
DELETE /api/v1/sessions/{session_id}
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "message": "session closed"
}
```

#### 1.4 列出活跃会话

**请求**:
```http
GET /api/v1/sessions
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "sessions": [
      {
        "session_id": "uuid",
        "status": "active",
        "created_at": "2026-03-05T05:00:00Z"
      }
    ],
    "total": 1
  }
}
```

### 2. 任务管理

#### 2.1 创建视频生成任务

**请求**:
```http
POST /api/v1/tasks
Content-Type: application/json
Authorization: Bearer <token>

{
  "session_id": "uuid",
  "audio_data": "base64_encoded_audio",
  "config": {
    "encode_mode": "stream",
    "output_format": "mp4"
  }
}
```

**响应**:
```json
{
  "code": 0,
  "message": "task created",
  "data": {
    "task_id": "uuid",
    "status": "processing",
    "estimated_time": 10
  }
}
```

#### 2.2 获取任务状态

**请求**:
```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "status": "completed",
    "progress": 100,
    "result": {
      "video_url": "http://example.com/videos/uuid.mp4",
      "duration": 66,
      "size": 3379200
    }
  }
}
```

### 3. 系统状态

#### 3.1 获取系统状态

**请求**:
```http
GET /api/v1/system/status
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "gpu": {
      "name": "NVIDIA GeForce RTX 5090",
      "utilization": 85,
      "memory_used": 24576,
      "memory_total": 32607
    },
    "model": {
      "type": "lite",
      "status": "loaded",
      "fps": 126
    },
    "sessions": {
      "active": 3,
      "total": 10
    }
  }
}
```

#### 3.2 获取性能指标

**请求**:
```http
GET /api/v1/system/metrics
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "inference_latency_ms": 190,
    "end_to_end_latency_ms": 1500,
    "concurrent_sessions": 3,
    "success_rate": 99.5
  }
}
```

## 错误码

| 错误码 | 说明 |
|-------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 错误响应格式

```json
{
  "code": 400,
  "message": "Invalid parameter",
  "details": {
    "field": "model_type",
    "error": "must be 'lite' or 'pro'"
  }
}
```

## WebSocket API

详见 [WebSocket API 文档](websocket-api.md)
