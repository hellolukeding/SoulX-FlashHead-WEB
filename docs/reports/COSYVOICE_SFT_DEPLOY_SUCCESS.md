# CosyVoice SFT 服务部署成功

**日期**: 2026-03-06
**状态**: ✅ 部署成功

---

## 服务状态

| 服务 | 端口 | 状态 | 特点 |
|------|------|------|------|
| CosyVoice Zero-shot | 8002 | ✅ 运行中 | 需要参考音频，灵活克隆音色 |
| CosyVoice-300M-SFT | 8003 | ✅ 运行中 | 7个预设音色，无需参考音频 |

---

## 预设音色列表

| ID | 音色 | 语言 | 性别 |
|----|------|------|------|
| 1 | 中文女 | 中文 | 女 |
| 2 | 中文男 | 中文 | 男 |
| 3 | 日语男 | 日语 | 男 |
| 4 | 粤语女 | 粤语 | 女 |
| 5 | 英文女 | 英文 | 女 |
| 6 | 英文男 | 英文 | 男 |
| 7 | 韩语女 | 韩语 | 女 |

---

## 性能指标

- **延迟**: ~500ms
- **采样率**: 22050 Hz
- **音频格式**: WAV (16-bit, mono)

---

## API 使用

### 获取音色列表

```bash
curl http://localhost:8003/speakers
```

### 生成音频

```bash
curl -X POST http://localhost:8003/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，我是数字人助手", "speaker": "中文女"}' \
  -o output.wav
```

### 流式生成

```bash
curl -X POST http://localhost:8003/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "你好", "speaker": "中文女", "chunk_size_ms": 150}' \
  -o output.wav
```

---

## 部署文件

- **服务代码**: `docker/cosyvoice/cosyvoice_sft_server.py`
- **启动脚本**: `docker/cosyvoice/start-sft-local.sh`
- **Dockerfile**: `docker/cosyvoice/Dockerfile.sft`
- **Docker Compose**: `docker/cosyvoice/docker-compose-sft.yml`

---

## 启动命令

```bash
# 本地启动
cd /opt/digital-human-platform/docker/cosyvoice
bash start-sft-local.sh

# 或手动启动
source /opt/digital-human-platform/backend/venv/bin/activate
export PYTHONPATH="/opt/digital-human-platform/models/CosyVoice/third_party/Matcha-TTS:/opt/digital-human-platform/models/CosyVoice:$PYTHONPATH"
python3 cosyvoice_sft_server.py
```

---

## Docker 部署说明

Docker 构建遇到 pip 依赖问题，推荐使用本地部署方式。

如果需要 Docker 部署，建议：
1. 使用预构建的 Python 镜像作为基础
2. 或等待 pip 依赖问题修复

---

## 测试结果

**测试音频**: `/tmp/test_sft_final.wav`
- 大小: 67KB
- 时长: 1.53s
- 格式: WAV (16-bit, mono, 22050Hz)
- 音色: 中文女

---

## 相关文档

- [Zero-shot 测试报告](COSYVOICE_ZERO_SHOT_TEST.md)
- [SFT 测试报告](COSYVOICE_SFT_TEST_SUCCESS.md)
- [本地部署报告](COSYVOICE_LOCAL_DEPLOYMENT_SUCCESS.md)
