# CosyVoice SFT 快速参考

## 部署

```bash
# 一键部署
cd /opt/digital-human-platform/docker/cosyvoice
bash deploy-sft.sh

# 手动部署
docker compose -f docker-compose-sft.yml build
docker compose -f docker-compose-sft.yml up -d
```

## API

```bash
# 获取音色列表
curl http://localhost:8003/speakers

# 生成音频
curl -X POST http://localhost:8003/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","speaker":"中性女"}' \
  -o output.wav

# 流式生成
curl -X POST http://localhost:8003/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","speaker":"中性女","chunk_size_ms":150}' \
  -o output.wav
```

## 预设音色

- 中性女
- 温暖男
- 活泼女
- 知性女
- 稳重男
- ...

## 常用命令

```bash
# 查看日志
docker compose -f docker-compose-sft.yml logs -f

# 重启服务
docker compose -f docker-compose-sft.yml restart

# 停止服务
docker compose -f docker-compose-sft.yml down

# 测试
bash test-sft.sh
```

## 端口

| 服务 | 端口 |
|------|------|
| Zero-shot | 8002 |
| SFT (vLLM) | 8003 |
