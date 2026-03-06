# CosyVoice TTS 服务 - Docker 部署指南

> 基于 CosyVoice-300M Zero-shot 模型的流式 TTS 服务
>
> **验证状态**: ✅ 本地测试通过 (2026-03-06)

---

## 📋 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [性能指标](#性能指标)
- [故障排除](#故障排除)

---

## ✨ 功能特性

- **Zero-shot 音色克隆**: 只需 3-5 秒参考音频即可克隆音色
- **流式输出**: 支持 150-200ms 切片流式输出，低延迟
- **GPU 加速**: 基于 CUDA 12.1，支持 NVIDIA GPU
- **REST API**: 标准 HTTP 接口，易于集成
- **健康检查**: 内置健康检查端点

---

## 🚀 快速开始

### 1. 前置要求

- Docker & Docker Compose
- NVIDIA GPU + 驱动
- CosyVoice-300M 模型（约 1.5 GB）

### 2. 一键部署

```bash
cd /opt/digital-human-platform/docker/cosyvoice
bash deploy.sh
```

### 3. 手动部署

```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 编辑配置（可选）
vim .env

# 3. 创建 Docker 网络
docker network create digital-human-network

# 4. 构建镜像（10-30 分钟）
docker build -t cosyvoice-tts:latest .

# 5. 启动服务
docker compose up -d

# 6. 查看日志
docker compose logs -f
```

### 4. 测试服务

```bash
# 使用测试脚本
bash test.sh

# 或手动测试
curl http://localhost:8002/health

# TTS 测试
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是数字人助手",
    "prompt_text": "希望你今天能够开心"
  }' \
  -o test.wav
```

---

## ⚙️ 配置说明

### 环境变量 (.env)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `COSYVOICE_PORT` | `8002` | 服务端口 |
| `COSYVOICE_ROOT` | `/opt/digital-human-platform/models/CosyVoice` | 模型根目录 |
| `COSYVOICE_ASSETS` | `./assets` | 自定义资源目录 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 模型目录结构

```
/opt/digital-human-platform/models/CosyVoice/
├── cosyvoice/                    # CosyVoice 源代码
│   ├── cli/
│   ├── model.py
│   └── ...
├── third_party/
│   └── Matcha-TTS/              # Matcha-TTS 依赖
└── pretrained_models/
    └── CosyVoice-300M/          # 模型权重
        ├── llm.pt
        ├── flow.pt
        ├── hift.pt
        ├── campplus.onnx
        ├── speech_tokenizer_v1.onnx
        └── asset/
            └── default_prompt.wav  # 默认参考音频
```

---

## 📡 API 文档

### 1. 健康检查

```
GET /health
```

**响应**:
```json
{
    "status": "healthy",
    "service": "CosyVoice TTS",
    "model": "CosyVoice-300M (Zero-shot)",
    "model_loaded": true,
    "gpu_available": true,
    "device": "NVIDIA GeForce RTX 5090",
    "default_prompt_available": true
}
```

### 2. 标准 TTS

```
POST /tts
Content-Type: application/json

{
    "text": "你好，我是数字人助手",
    "prompt_text": "希望你今天能够开心",
    "prompt_audio_url": ""  // 可选，留空使用默认
}
```

**响应**:
- Content-Type: `audio/wav`
- X-Latency-ms: 延迟（毫秒）
- X-Duration-s: 音频时长（秒）

### 3. 流式 TTS

```
POST /tts/stream
Content-Type: application/json

{
    "text": "你好，我是数字人助手",
    "prompt_text": "希望你今天能够开心",
    "prompt_audio_url": "",
    "chunk_size_ms": 150
}
```

**响应**:
- Transfer-Encoding: `chunked`
- 流式音频数据

---

## 📊 性能指标

基于 RTX 5090 的测试结果：

| 指标 | 数值 |
|------|------|
| 首包延迟 (TTFT) | ~1200ms |
| RTF (实时率) | 0.27x |
| 采样率 | 22050 Hz |
| 音频格式 | WAV (16-bit, mono) |

---

## 🔧 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看状态
docker compose ps

# 进入容器
docker compose exec cosyvoice bash

# 更新镜像
docker compose build --no-cache
docker compose up -d
```

---

## 🐛 故障排除

### 1. 模型加载失败

**错误**: `模型未加载，请检查模型路径`

**解决**:
- 检查 `COSYVOICE_ROOT` 环境变量
- 确保模型目录结构正确
- 查看容器日志: `docker compose logs`

### 2. GPU 不可用

**错误**: `gpu_available: false`

**解决**:
- 安装 NVIDIA Container Toolkit:
  ```bash
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
  curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    tee /etc/apt/sources.list.d/nvidia-docker.list
  apt-get update && apt-get install -y nvidia-container-toolkit
  systemctl restart docker
  ```

### 3. 端口冲突

**错误**: `port is already allocated`

**解决**: 修改 `.env` 中的 `COSYVOICE_PORT`

### 4. 默认参考音频缺失

**错误**: `请提供 prompt_audio_url 或确保服务器已加载默认参考音频`

**解决**:
```bash
# 创建默认参考音频
cd /opt/digital-human-platform/docker/cosyvoice
bash deploy.sh
```

---

## 📝 相关文档

- [本地部署报告](../../../docs/reports/COSYVOICE_LOCAL_DEPLOYMENT_SUCCESS.md)
- [五阶段流式架构](../../../docs/reports/)
- [项目 README](../../../README.md)

---

## 📄 许可证

本服务基于 CosyVoice (Apache 2.0) 开发。
