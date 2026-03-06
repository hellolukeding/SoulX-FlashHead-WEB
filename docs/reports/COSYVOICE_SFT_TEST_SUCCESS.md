# CosyVoice-300M-SFT 预设音色测试报告

**日期**: 2026-03-06
**状态**: ✅ 测试通过

---

## 测试概述

使用 CosyVoice-300M-SFT 模型的预设音色功能进行测试。

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

**总计**: 7 个预设音色

---

## 测试结果

### 生成的音频文件

| 音色 | 文件 | 大小 | 时长 | 格式 |
|------|------|------|------|------|
| 中文女 | `cosyvoice_sft_1_中文女.wav` | 127KB | 2.94s | WAV (16-bit, mono, 22050Hz) |
| 中文男 | `cosyvoice_sft_2_中文男.wav` | 165KB | 3.82s | WAV (16-bit, mono, 22050Hz) |
| 日语男 | `cosyvoice_sft_3_日语男.wav` | 181KB | 4.18s | WAV (16-bit, mono, 22050Hz) |

### 测试参数

- **合成文本**: "你好，我是数字人助手，很高兴认识大家"
- **采样率**: 22050 Hz
- **位深度**: 16-bit
- **声道**: 单声道

---

## 使用方法

### 本地 Python API

```python
from cosyvoice.cli.cosyvoice import CosyVoice

# 加载 SFT 模型
model = CosyVoice('iic/CosyVoice-300M-SFT')

# 获取音色列表
speakers = model.list_available_spks()
print(speakers)  # ['中文女', '中文男', '日语男', '粤语女', '英文女', '英文男', '韩语女']

# 使用预设音色生成音频
for audio_chunk in model.inference_sft(
    tts_text="你好，世界",
    spk_id="中文女",
    stream=False,
):
    # 处理音频
    pass
```

### Docker 部署

```bash
cd /opt/digital-human-platform/docker/cosyvoice

# 部署 SFT 服务
bash deploy-sft.sh

# 测试服务
bash test-sft.sh

# 使用 API
curl -X POST http://localhost:8003/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好", "speaker": "中文女"}' \
  -o output.wav
```

---

## 特性对比

| 特性 | Zero-shot | SFT |
|------|-----------|-----|
| 模型 | CosyVoice-300M | CosyVoice-300M-SFT |
| 音色来源 | 参考音频 | 预设音色 |
| 音色数量 | 无限 | 7 个 |
| 参考音频 | 需要 | 不需要 |
| 使用场景 | 定制音色 | 快速部署 |

---

## 部署文件

所有部署配置位于 `/opt/digital-human-platform/docker/cosyvoice/`:

- `Dockerfile.vllm-sft` - vLLM Docker 镜像
- `cosyvoice_sft_server.py` - SFT 服务代码
- `docker-compose-sft.yml` - Docker Compose 配置
- `deploy-sft.sh` - 部署脚本
- `test-sft.sh` - 测试脚本
- `README-SFT.md` - 详细文档

---

## 下一步

1. ✅ SFT 模型下载完成 (5.4 GB)
2. ✅ 预设音色测试通过
3. ⏳ Docker 部署 (可选)
4. ⏳ vLLM 加速配置 (可选)

---

## 相关文档

- [本地部署报告](COSYVOICE_LOCAL_DEPLOYMENT_SUCCESS.md)
- [Zero-shot 测试报告](COSYVOICE_ZERO_SHOT_TEST.md)
- [Docker 部署指南](../../../docker/cosyvoice/README-SFT.md)
