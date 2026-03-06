# 测试快速参考

## 🚀 快速运行

```bash
# 激活环境并运行测试
source backend/venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# 运行所有单元测试
python -m pytest test/unit/ -v

# 生成覆盖率报告
python -m pytest test/unit/ --cov=backend --cov-report=html
```

## 📊 测试结果

| 模块 | 状态 | 通过/总数 |
|------|------|----------|
| ASR | ✅ | 15/15 |
| LLM | ✅ | 8/15 (7个需要API) |
| TTS | ✅ | 20/22 (2个需要依赖) |
| WebSocket | ✅ | 22/22 |
| **总计** | ✅ | **65/74** |

## 📈 覆盖率: 25%

**亮点:**
- Edge TTS: 92%
- ASR Base: 89%
- Exceptions: 82%

## 📁 测试文件

```
test/unit/
├── test_asr_workflow.py         ✅ 15 tests
├── test_llm_workflow.py         ✅ 15 tests
├── test_tts_workflow.py         ✅ 22 tests
└── test_websocket_workflow.py   ✅ 22 tests
```

## 🎯 业务流程覆盖

- ✅ ASR 识别流程
- ✅ LLM 对话流程
- ✅ TTS 合成流程
- ✅ WebSocket 会话管理
- ✅ 错误处理
- ✅ 并发控制
- ✅ 速率限制

## 📚 详细文档

- [TEST_FIXES_COMPLETION_REPORT.md](TEST_FIXES_COMPLETION_REPORT.md) - 完整修复报告
- [test/README.md](test/README.md) - 测试使用指南
- [htmlcov/index.html](htmlcov/index.html) - 覆盖率报告
