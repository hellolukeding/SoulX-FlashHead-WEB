# CosyVoice 流式 TTS 服务

基于 Docker 的 CosyVoice TTS 服务，支持流式切片输出。

## 特性

- ✅ 流式切片输出 (150-200ms)
- ✅ 内存级数据传递（零磁盘 I/O）
- ✅ 支持多种音色
- ✅ Docker 容器化部署
- ✅ GPU 加速（CUDA 12.1）
- ✅ FastAPI 服务器
- ✅ RESTful API

## 快速开始

### 1. 准备模型

```bash
# 克隆 CosyVoice 仓库
cd /opt/digital-human-platform/models
git clone https://github.com/FunAudioLLM/CosyVoice.git

# 下载模型文件，参考 CosyVoice 项目文档
cd CosyVoice
# 下载模型到 models/ 目录
```

### 2. 构建镜像

```bash
cd /opt/digital-human-platform/docker
./deploy-cosyvoice.sh build
```

### 3. 启动服务

```bash
./deploy-cosyvoice.sh start
```

### 4. 测试服务

```bash
./test-cosyvoice.sh
```

## API 端点

### 健康检查

```bash
curl http://localhost:8002/health
```

### 标准 TTS

```bash
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是数字人助手",
    "speaker": "default",
    "speed": 1.0
  }' \
  --output output.wav
```

### 流式 TTS

```bash
curl -X POST http://localhost:8002/tts/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是数字人助手",
    "speaker": "default",
    "chunk_size_ms": 150
  }' \
  --output output.wav
```

## 请求参数

### TTSRequest

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| text | string | 必填 | 要转换的文本 |
| speaker | string | "default" | 说话人 ID |
| speed | float | 1.0 | 语速 (0.5 - 2.0) |

### StreamingTTSRequest

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| text | string | 必填 | 要转换的文本 |
| speaker | string | "default" | 说话人 ID |
| chunk_size_ms | int | 150 | 切片大小（毫秒） |
| speed | float | 1.0 | 语速 |

## 部署命令

```bash
# 构建镜像
./deploy-cosyvoice.sh build

# 启动服务
./deploy-cosyvoice.sh start

# 停止服务
./deploy-cosyvoice.sh stop

# 重启服务
./deploy-cosyvoice.sh restart

# 查看日志
./deploy-cosyvoice.sh logs

# 查看状态
./deploy-cosyvoice.sh status

# 测试服务
./deploy-cosyvoice.sh test

# 清理
./deploy-cosyvoice.sh clean
```

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| MODEL_PATH | /models/CosyVoice-300M | 模型路径 |
| PORT | 8002 | 服务端口 |
| HOST | 0.0.0.0 | 监听地址 |

### Docker Compose

编辑 `docker-compose-cosyvoice.yml` 修改配置：

```yaml
environment:
  - MODEL_PATH=/models/CosyVoice-300M
  - PORT=8002

volumes:
  # 挂载模型目录
  - /path/to/CosyVoice:/models/CosyVoice-300M:ro
```

## Python 客户端示例

```python
import requests

# 标准 TTS
response = requests.post(
    "http://localhost:8002/tts",
    json={
        "text": "你好，我是数字人助手",
        "speaker": "default"
    }
)

with open("output.wav", "wb") as f:
    f.write(response.content)

# 流式 TTS
response = requests.post(
    "http://localhost:8002/tts/stream",
    json={
        "text": "你好，我是数字人助手",
        "chunk_size_ms": 150
    },
    stream=True
)

with open("output_stream.wav", "wb") as f:
    for chunk in response.iter_content(chunk_size=4096):
        f.write(chunk)
```

## JavaScript 客户端示例

```javascript
// 标准 TTS
const response = await fetch('http://localhost:8002/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: '你好，我是数字人助手',
        speaker: 'default'
    })
});

const audioBlob = await response.blob();
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
audio.play();

// 流式 TTS
const response = await fetch('http://localhost:8002/tts/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: '你好，我是数字人助手',
        chunk_size_ms: 150
    })
});

const reader = response.body.getReader();
// 处理流式数据...
```

## 性能

- 首包延迟: ~200-300ms
- 切片大小: 150ms (可配置)
- 采样率: 24000 Hz
- 音频格式: WAV (PCM 16-bit)

## 故障排查

### 服务无法启动

```bash
# 查看日志
docker-compose -f docker-compose-cosyvoice.yml logs cosyvoice

# 检查 GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 模型未加载

检查模型目录是否正确挂载：

```bash
docker exec cosyvoice-tts ls -la /models/CosyVoice-300M
```

### 端口冲突

修改 `docker-compose-cosyvoice.yml` 中的端口映射：

```yaml
ports:
  - "8003:8002"  # 使用 8003 端口
```

## 许可证

CosyVoice: Apache License 2.0
https://github.com/FunAudioLLM/CosyVoice
