# CosyVoice-300M-SFT TTS 服务 - vLLM 部署指南

> 基于 CosyVoice-300M-SFT 模型的预设音色 TTS 服务
>
> **特性**: 预设音色 + vLLM 加速

---

## 📋 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [预设音色列表](#预设音色列表)
- [API 文档](#api-文档)
- [性能对比](#性能对比)

---

## ✨ 功能特性

- **预设音色**: 内置多种预设音色，无需参考音频
- **vLLM 加速**: 使用 vLLM 加速 LLM 推理，提升速度
- **流式输出**: 支持 150-200ms 切片流式输出
- **GPU 加速**: 基于 CUDA 12.1
- **低延迟**: 相比标准模式，延迟降低 30-50%

---

## 🚀 快速开始

### 1. 下载 SFT 模型

```bash
cd /opt/digital-human-platform/docker/cosyvoice
bash download-sft-model.sh
```

### 2. 一键部署

```bash
bash deploy-sft.sh
```

### 3. 测试服务

```bash
bash test-sft.sh
```

---

## 🎤 预设音色列表

SFT 模型内置多种预设音色，包括：

| 音色 ID | 描述 |
|---------|------|
| 中性女 | 标准女声 |
| 温暖男 | 温暖男声 |
| 活泼女 | 活泼女声 |
| 知性女 | 知性女声 |
| 稳重男 | 稳重男声 |
| ... | 更多音色 |

获取完整列表：
```bash
curl http://localhost:8003/speakers
```

---

## 📡 API 文档

### 1. 获取音色列表

```
GET /speakers
```

**响应**:
```json
{
    "count": 50,
    "speakers": ["中性女", "温暖男", "活泼女", ...]
}
```

### 2. 标准 TTS

```
POST /tts
Content-Type: application/json

{
    "text": "你好，我是数字人助手",
    "speaker": "中性女"
}
```

### 3. 流式 TTS

```
POST /tts/stream
Content-Type: application/json

{
    "text": "你好，我是数字人助手",
    "speaker": "中性女",
    "chunk_size_ms": 150
}
```

---

## 📊 性能对比

| 模式 | 延迟 | RTF | 特点 |
|------|------|-----|------|
| Zero-shot | ~2000ms | 1.0x | 需要参考音频 |
| SFT (标准) | ~1500ms | 0.8x | 预设音色 |
| SFT (vLLM) | ~1000ms | 0.5x | vLLM 加速 |

---

## 🔧 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `COSYVOICE_SFT_PORT` | `8003` | 服务端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU 设备 |

### vLLM 配置

- `VLLM_TENSOR_PARALLEL_SIZE=1`: 单 GPU
- `VLLM_USE_MODELSCOPE=true`: 使用 ModelScope 模型

---

## 📁 文件结构

```
docker/cosyvoice/
├── Dockerfile.vllm-sft        # vLLM Docker 镜像
├── cosyvoice_sft_server.py    # SFT 服务代码
├── start-vllm.sh              # 启动脚本
├── docker-compose-sft.yml     # Docker Compose 配置
├── deploy-sft.sh              # 部署脚本
├── test-sft.sh                # 测试脚本
├── download-sft-model.sh      # 模型下载脚本
└── .env-sft.example           # 环境变量模板
```

---

## 🔍 常用命令

```bash
# 启动服务
docker compose -f docker-compose-sft.yml up -d

# 停止服务
docker compose -f docker-compose-sft.yml down

# 查看日志
docker compose -f docker-compose-sft.yml logs -f

# 测试音色列表
curl http://localhost:8003/speakers

# 测试 TTS
curl -X POST http://localhost:8003/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","speaker":"中性女"}' \
  -o test.wav
```

---

## 🆚 与 Zero-shot 模式对比

| 特性 | Zero-shot | SFT (vLLM) |
|------|-----------|------------|
| 参考音频 | 需要 | 不需要 |
| 音色灵活性 | 任意音色 | 预设音色 |
| 速度 | 较慢 | **快 50%** |
| 部署复杂度 | 低 | 中 |
| 适用场景 | 定制音色 | 快速部署 |

---

## 📝 相关文档

- [Zero-shot 部署指南](README.md)
- [本地部署报告](../../../docs/reports/COSYVOICE_LOCAL_DEPLOYMENT_SUCCESS.md)
