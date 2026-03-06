# 项目结构说明

## 目录组织

```
digital-human-platform/
├── README.md                 # 项目说明
├── QUICK_START.md           # 快速开始
├── START_HERE.md            # 新手入门
├── .env                     # 环境配置
├── .gitignore              # Git 忽略规则
├── pytest.ini              # 测试配置
│
├── start.sh                # Linux 启动脚本
├── start.bat               # Windows 启动脚本
├── run_tests.sh            # 运行测试
│
├── backend/                # 后端服务
│   ├── app/               # 应用代码
│   ├── venv/              # Python 虚拟环境
│   └── requirements.txt   # Python 依赖
│
├── frontend/              # 前端页面
├── desktop_app/           # 桌面应用
│
├── test/                  # 测试代码
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── e2e/             # E2E 测试
│
├── models/               # AI 模型
│   ├── CosyVoice/       # TTS 模型
│   └── SoulX-FlashHead/ # 数字人模型
│
├── docs/                 # 文档
│   ├── reports/         # 项目报告
│   │   ├── ASR_INTEGRATION_COMPLETE.md
│   │   ├── CODE_REVIEW_REPORT.md
│   │   ├── COSYVOICE_TEST_SUCCESS.md
│   │   ├── FINAL_TESTING_REPORT.md
│   │   └── ...
│   └── testing/         # 测试文档
│       ├── TESTING_SUMMARY.md
│       └── TEST_DASHBOARD.md
│
├── scripts/              # 工具脚本
│   ├── backup_pytorch.sh
│   └── check_pytorch_upgrade.sh
│
└── archives/             # 归档文件
    ├── htmlcov/         # 测试覆盖率报告
    └── pytorch_backup/  # PyTorch 备份
```

## 核心目录说明

### `/backend` - 后端服务
- FastAPI 应用
- WebSocket 服务
- AI 模型集成

### `/frontend` - Web 前端
- React/Vue.js 界面
- 实时通信

### `/test` - 测试套件
- 95 个测试用例
- 单元测试、集成测试、E2E 测试
- 97% 通过率

### `/models` - AI 模型
- CosyVoice: TTS 语音合成
- SoulX-FlashHead: 数字人视频生成

### `/docs` - 文档中心
- `reports/`: 开发过程报告
- `testing/`: 测试相关文档

### `/scripts` - 运维脚本
- 备份、升级、检查工具

### `/archives` - 历史归档
- 测试报告
- 备份文件

## 快速导航

**启动项目:**
```bash
bash start.sh
```

**运行测试:**
```bash
bash run_tests.sh
```

**查看文档:**
- 快速开始: `QUICK_START.md`
- 项目说明: `README.md`
- 测试报告: `docs/testing/`

## 测试状态

✅ **92 passed** (97%)
- ASR: 15/15
- LLM: 12/15
- TTS: 22/22 (包括 CosyVoice)
- WebSocket: 22/22
- Integration: 9/11
- E2E: 10/10

## 技术栈

- **后端**: FastAPI + Python 3.12
- **前端**: React/Vue.js
- **AI**: PyTorch 2.6.0 + transformers 5.3.0
- **测试**: pytest + pytest-asyncio
- **部署**: Docker + Nginx
