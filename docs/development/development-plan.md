# 🚀 实时数字人平台 - 开发方案

## 📊 项目评估

### 当前状态
- ✅ **项目结构**：完整的前后端分离架构
- ✅ **基础文档**：API 文档、架构文档齐全
- ✅ **前端框架**：React 19 + TypeScript + Tauri 已搭建
- ✅ **后端框架**：FastAPI 基础已就绪
- 🔴 **核心功能**：推理引擎、WebSocket 服务待实现
- 🔴 **实时通信**：前后端 WebSocket 连接待建立

### 技术优势
1. **高性能模型**：SoulX-FlashHead 1.3B，RTX 5090 可达 126 FPS
2. **现代技术栈**：React 19 + FastAPI + WebSocket
3. **跨平台支持**：Tauri 桌面应用
4. **清晰架构**：前后端分离，模块化设计

### 主要挑战
1. **实时性要求**：音频流输入 → 视频流输出，延迟需控制在 1.5-2.5 秒
2. **并发处理**：单卡支持 4-5 个并发会话
3. **资源管理**：GPU 内存管理、会话状态维护
4. **流式同步**：音频缓冲与视频生成的协调

---

## 🎯 开发方案

### 阶段一：核心功能实现（1-2 周）

#### 1.1 后端推理引擎
**优先级**：🔴 最高

**目标**：封装 SoulX-FlashHead 模型，提供统一的推理接口

**实现步骤**：
```python
# backend/app/core/inference/flashhead_engine.py
class FlashHeadEngine:
    def __init__(self):
        # 模型加载
        # GPU 配置
        # 性能监控

    def load_model(self):
        # 加载 SoulX-FlashHead 1.3B
        # 加载 wav2vec2 音频模型
        pass

    def process_audio(self, audio_data):
        # 音频预处理
        # 特征提取
        pass

    def generate_frame(self, audio_features):
        # 单帧视频生成
        # 返回视频帧数据
        pass

    def generate_stream(self, audio_stream):
        # 流式视频生成
        # yield 视频帧
        pass
```

**关键点**：
- 模型路径配置（/opt/soulx/SoulX-FlashHead/）
- 音频采样率处理（16kHz）
- 视频帧率控制（25 FPS）
- GPU 内存优化

#### 1.2 WebSocket 服务
**优先级**：🔴 最高

**目标**：实现实时双向通信，接收音频流，推送视频流

**实现步骤**：
```python
# backend/app/api/websocket/handler.py
class WebSocketHandler:
    def __init__(self):
        self.engine = FlashHeadEngine()
        self.sessions = {}

    async def connect(self, websocket, session_id):
        # 建立 WebSocket 连接
        # 初始化会话
        pass

    async def handle_audio(self, session_id, audio_chunk):
        # 接收音频数据
        # 调用推理引擎
        # 返回视频帧
        pass

    async def disconnect(self, session_id):
        # 清理会话资源
        pass
```

**消息协议**：
```json
// 客户端 → 服务端（音频数据）
{
  "type": "audio",
  "session_id": "uuid",
  "data": "base64_audio",
  "timestamp": 1234567890
}

// 服务端 → 客户端（视频帧）
{
  "type": "frame",
  "session_id": "uuid",
  "data": "base64_frame",
  "frame_number": 123,
  "timestamp": 1234567890
}
```

#### 1.3 会话管理
**优先级**：🔴 高

**目标**：管理多个并发会话，分配 GPU 资源

**实现步骤**：
```python
# backend/app/core/session/state.py
class SessionManager:
    def __init__(self, max_sessions=5):
        self.sessions = {}
        self.max_sessions = max_sessions
        self.gpu_queue = GPUMemoryManager()

    def create_session(self, user_id):
        # 检查并发限制
        # 分配 GPU 资源
        # 初始化会话状态
        pass

    def close_session(self, session_id):
        # 释放资源
        # 清理状态
        pass

    def get_session(self, session_id):
        # 获取会话信息
        pass
```

#### 1.4 前端 WebSocket 客户端
**优先级**：🔴 高

**目标**：建立与后端的实时连接，处理音视频流

**实现步骤**：
```typescript
// desktop_app/src/api/websocket.ts
class WebSocketClient {
  private ws: WebSocket;
  private mediaRecorder: MediaRecorder;
  private videoElement: HTMLVideoElement;

  connect(url: string) {
    // 建立 WebSocket 连接
    // 处理连接状态
  }

  startRecording() {
    // 启动音频录制
    // 流式发送到后端
  }

  onFrame(callback: (frame: string) => void) {
    // 接收视频帧
    // 渲染到 video 元素
  }
}
```

---

### 阶段二：优化与完善（1 周）

#### 2.1 性能优化
- 音频缓冲管理（避免阻塞）
- 视频帧队列（平滑播放）
- GPU 内存优化（避免 OOM）
- 并发控制（队列调度）

#### 2.2 错误处理
- 网络断线重连
- GPU 错误恢复
- 会话超时处理
- 异常日志记录

#### 2.3 UI 优化
- 实时延迟显示
- 性能监控面板
- 连接状态指示
- 错误提示优化

---

### 阶段三：扩展功能（可选）

#### 3.1 REST API 完善
- 会话管理 API
- 任务查询 API
- 系统状态 API
- 健康检查 API

#### 3.2 用户认证
- JWT Token 认证
- 会话授权
- 使用量统计

#### 3.3 部署配置
- Docker 配置
- Nginx 反向代理
- 系统服务配置
- 监控告警

---

## 📝 实现优先级

### 第 1 周：核心功能
1. **Day 1-2**：FlashHead 推理引擎封装
2. **Day 3-4**：WebSocket 服务实现
3. **Day 5**：会话管理实现
4. **Day 6-7**：前端 WebSocket 客户端

### 第 2 周：集成测试
1. **Day 1-2**：前后端联调
2. **Day 3-4**：性能优化
3. **Day 5**：错误处理
4. **Day 6-7**：UI 优化和测试

---

## 🔧 开发环境配置

### 后端环境
```bash
# Python 虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python -m app.main
```

### 前端环境
```bash
# Node.js 依赖
cd desktop_app
yarn install

# 启动开发服务器
yarn dev
```

### 模型准备
```bash
# 确保模型文件存在
ls /opt/soulx/SoulX-FlashHead/

# 如果需要，创建软链接
ln -s /opt/soulx/SoulX-FlashHead /opt/digital-human-platform/models/flashhead
```

---

## 🧪 测试方案

### 单元测试
```bash
# 后端测试
cd backend
pytest tests/

# 前端测试
cd desktop_app
yarn test
```

### 集成测试
1. 启动后端服务
2. 启动前端应用
3. 建立 WebSocket 连接
4. 发送测试音频
5. 验证视频输出

### 性能测试
- 并发会话测试（4-5 个）
- 延迟测试（< 2.5 秒）
- 内存占用测试（GPU/CPU）
- 长时间运行测试

---

## 📚 参考资料

### 项目文档
- [系统架构](../architecture.md)
- [REST API](../api/rest-api.md)
- [WebSocket API](../api/websocket-api.md)

### 技术文档
- [SoulX-FlashHead](https://github.com/Soul-AILab/SoulX-FlashHead)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [React WebSocket](https://www.npmjs.com/package/react-use-websocket)
- [Tauri 文档](https://tauri.app/)

---

## 🎯 下一步行动

### 立即开始
1. **查看模型代码**：`/opt/soulx/SoulX-FlashHead/`
2. **创建推理引擎**：`backend/app/core/inference/flashhead_engine.py`
3. **实现 WebSocket**：`backend/app/api/websocket/handler.py`
4. **前端集成**：`desktop_app/src/api/websocket.ts`

### 快速启动
```bash
# 查看开发脚本
cat scripts/dev.sh

# 一键启动
./scripts/dev.sh
```

---

**项目状态**: 🟡 基础架构完成，核心功能开发中
**预计完成**: 2-3 周
**团队规模**: 1-2 人
