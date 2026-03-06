# CosyVoice TTS 快速参考

## 一键启动

```bash
cd /opt/digital-human-platform/docker/cosyvoice
bash deploy.sh
```

## 常用命令

```bash
# 启动
docker compose up -d

# 停止
docker compose down

# 日志
docker compose logs -f

# 测试
bash test.sh
```

## API 测试

```bash
# 健康检查
curl http://localhost:8002/health

# 标准 TTS
curl -X POST http://localhost:8002/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","prompt_text":"希望你今天能够开心"}' \
  -o test.wav

# 流式 TTS
curl -X POST http://localhost:8002/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","prompt_text":"希望你今天能够开心","chunk_size_ms":150}' \
  -o test_stream.wav
```

## 环境变量

| 变量 | 默认值 |
|------|--------|
| COSYVOICE_PORT | 8002 |
| COSYVOICE_ROOT | /opt/digital-human-platform/models/CosyVoice |
| LOG_LEVEL | INFO |

## 文件位置

- 服务代码: `cosyvoice_server.py`
- 启动脚本: `start.sh`
- 配置文件: `.env`
- 测试脚本: `test.sh`
- 部署脚本: `deploy.sh`

## 故障排除

```bash
# 检查容器状态
docker compose ps

# 查看详细日志
docker compose logs cosyvoice

# 进入容器调试
docker compose exec cosyvoice bash

# 重启服务
docker compose restart
```
