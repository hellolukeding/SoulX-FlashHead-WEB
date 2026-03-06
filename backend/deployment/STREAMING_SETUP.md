# 流式处理功能部署指南

## 系统要求

### 硬件要求
- **GPU**: NVIDIA RTX 4090/5090 (推荐) 或其他支持 CUDA 的 GPU
- **内存**: 至少 32GB RAM
- **存储**: 至少 50GB 可用空间

### 软件要求
- **操作系统**: Ubuntu 22.04+ (推荐) 或其他 Linux 发行版
- **Python**: 3.10+
- **CUDA**: 12.8+
- **FFmpeg**: 6.0+

## 安装步骤

### 1. 系统依赖安装

```bash
# 更新系统包
sudo apt-get update

# 安装 FFmpeg 和编解码库
sudo apt-get install -y \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libavdevice-dev

# 安装 Python 开发依赖
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    build-essential
```

### 2. 安装 CUDA

如果尚未安装 CUDA：

```bash
# 从 NVIDIA 官网下载 CUDA 12.8
# 或使用 NVIDIA 仓库安装

# 验证 CUDA 安装
nvidia-smi
nvcc --version
```

### 3. 安装 PyTorch

```bash
# CUDA 12.8 版本
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

### 4. 安装 SoulX-FlashHead 模型

```bash
# 克隆模型仓库
git clone https://github.com/Soul-AILab/SoulX-FlashHead.git /opt/soulx/SoulX-FlashHead

# 下载预训练权重
cd /opt/soulx/SoulX-FlashHead
# 按照仓库说明下载模型文件
```

### 5. 安装项目依赖

```bash
# 进入项目目录
cd /opt/digital-human-platform/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

## 配置

### 1. 环境变量配置

创建 `.env` 文件：

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
nano .env
```

`.env` 文件内容：

```env
# 应用配置
APP_NAME=Digital Human Platform
APP_VERSION=1.0.0
DEBUG=false

# 服务器配置
HOST=0.0.0.0
PORT=8000

# CORS 配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# 模型配置
MODEL_PATH=/opt/soulx/SoulX-FlashHead
DEFAULT_MODEL_TYPE=lite

# GPU 配置
GPU_MEMORY_FRACTION=0.9
MAX_CONCURRENT_SESSIONS=5

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 2. 流式处理配置

编辑 `app/config/stream_config.yaml`：

```yaml
stream:
  audio:
    window_size: 1.0      # 音频缓冲窗口（秒）
    sample_rate: 16000    # 采样率
    channels: 1           # 声道数

  video:
    fps: 25               # 帧率
    resolution: [512, 512]
    codec: h264_nvenc     # H.264 编码器 (h264_nvenc 或 libx264)
    bitrate: 2M           # 比特率

  session:
    max_concurrent: 5     # 最大并发会话数
    cleanup_interval: 300 # 清理间隔（秒）

  gpu:
    max_memory_utilization: 0.9
    enable_nvenc: true    # 启用 NVENC
```

## 启动服务

### 开发模式

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate

# 启动开发服务器（支持热重载）
python -m app.main
```

### 生产模式

```bash
# 使用 Uvicorn 启动
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log
```

### 使用 Systemd 服务

创建服务文件 `/etc/systemd/system/digital-human.service`：

```ini
[Unit]
Description=Digital Human Platform Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/digital-human-platform/backend
Environment="PATH=/opt/digital-human-platform/backend/venv/bin"
ExecStart=/opt/digital-human-platform/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable digital-human.service

# 启动服务
sudo systemctl start digital-human.service

# 查看状态
sudo systemctl status digital-human.service

# 查看日志
sudo journalctl -u digital-human.service -f
```

## 验证部署

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

预期响应：

```json
{
  "status": "healthy",
  "gpu_available": true,
  "cuda_version": "12.8"
}
```

### 2. 运行测试

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate

# 运行单元测试
pytest tests/core/ -v

# 运行集成测试（需要完整环境）
pytest tests/integration/ -v
```

### 3. 性能测试

```bash
# 测试推理速度
python scripts/benchmark_inference.py

# 测试并发性能
python scripts/benchmark_concurrent.py
```

## 监控

### 日志监控

```bash
# 查看应用日志
tail -f backend/logs/app.log

# 查看 streaming 日志
tail -f backend/logs/streaming.log
```

### 性能监控

访问 Prometheus 指标：

```bash
curl http://localhost:8000/metrics
```

### GPU 监控

```bash
# 实时 GPU 使用情况
watch -n 1 nvidia-smi
```

## 故障排查

### 问题 1: GPU 内存不足

**症状**:
```
CUDA out of memory
```

**解决方案**:
1. 减少并发会话数（修改 `stream_config.yaml`）
2. 降低视频分辨率
3. 使用更小的模型

### 问题 2: NVENC 编码失败

**症状**:
```
av.error.ValueError: [Errno 22] Invalid argument: 'avcodec_open2(h264_nvenc)'
```

**解决方案**:
1. 检查 FFmpeg 是否支持 NVENC
2. 切换到 CPU 编码器：修改 `codec: libx264`
3. 更新 NVIDIA 驱动

### 问题 3: WebSocket 连接失败

**症状**:
```
WebSocket connection failed
```

**解决方案**:
1. 检查防火墙设置
2. 验证 CORS 配置
3. 查看服务器日志

### 问题 4: 模型加载失败

**症状**:
```
FileNotFoundError: Model file not found
```

**解决方案**:
1. 验证模型路径配置
2. 检查模型文件完整性
3. 确认文件权限

## 性能优化

### 1. GPU 优化

```python
# 调整 GPU 内存分配
import torch
torch.cuda.set_per_process_memory_fraction(0.9)
```

### 2. 并发优化

```yaml
# stream_config.yaml
stream:
  session:
    max_concurrent: 4  # 根据 GPU 内存调整
```

### 3. 编码优化

```yaml
# 使用更快的编码预设
stream:
  video:
    preset: p1  # p1 最快，p7 最慢但质量最好
    tune: ll    # 低延迟优化
```

## 安全建议

1. **使用 HTTPS**: 在生产环境部署反向代理（Nginx）
2. **限制 CORS**: 仅允许可信来源
3. **添加认证**: 实现用户认证机制
4. **速率限制**: 防止滥用
5. **日志脱敏**: 不要记录敏感信息

## 备份和恢复

### 配置备份

```bash
# 备份配置文件
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
    backend/.env \
    backend/app/config/
```

### 模型备份

```bash
# 备份模型文件
tar -czf model-backup-$(date +%Y%m%d).tar.gz \
    /opt/soulx/SoulX-FlashHead/
```

## 升级指南

### 更新代码

```bash
# 拉取最新代码
cd /opt/digital-human-platform
git pull origin main

# 更新依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart digital-human.service
```

### 数据库迁移（如需要）

```bash
# 运行迁移
alembic upgrade head
```

## 支持

- **文档**: [docs/](../../docs/)
- **问题反馈**: [GitHub Issues](https://github.com/hellolukeding/SoulX-FlashHead-WEB/issues)
- **技术支持**: 创建 GitHub Issue

## 附录

### A. 端口使用

- **8000**: 主应用端口
- **8001**: 开发服务器（如使用）

### B. 目录结构

```
/opt/digital-human-platform/backend/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   ├── core/              # 核心逻辑
│   ├── config/            # 配置文件
│   └── main.py            # 主入口
├── tests/                 # 测试代码
├── logs/                  # 日志文件
├── scripts/               # 脚本工具
├── deployment/            # 部署文档
├── .env                   # 环境变量
└── requirements.txt       # Python 依赖
```

### C. 环境变量参考

参见 `app/core/config.py` 获取完整的环境变量列表。
