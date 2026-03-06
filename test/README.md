# 测试文档

Digital Human Platform 测试套件文档

## 📋 测试结构

```
test/
├── unit/                      # 单元测试
│   ├── test_asr_workflow.py    # ASR 业务流程测试
│   ├── test_llm_workflow.py    # LLM 业务流程测试
│   ├── test_tts_workflow.py    # TTS 业务流程测试
│   └── test_websocket_workflow.py  # WebSocket 处理测试
├── integration/                # 集成测试
│   └── test_complete_dialogue_flow.py  # 完整对话流程测试
└── e2e/                       # 端到端测试
    └── (待添加)

```

## 🎯 测试覆盖范围

### 单元测试 (Unit Tests)

测试单个组件的功能：

1. **test_asr_workflow.py** - ASR 服务测试
   - MockASR 功能测试
   - ASR 工厂模式测试
   - ASR 业务流程测试
   - 错误处理测试
   - 边界情况测试

2. **test_llm_workflow.py** - LLM 服务测试
   - LLM 客户端初始化测试
   - 流式对话测试
   - 非流式对话测试
   - 业务流程测试
   - 错误处理测试

3. **test_tts_workflow.py** - TTS 服务测试
   - EdgeTTS 功能测试
   - CosyVoiceTTS 功能测试
   - TTS 工厂模式测试
   - 错误处理测试
   - 性能测试

4. **test_websocket_workflow.py** - WebSocket 处理测试
   - 连接管理器测试
   - 会话生命周期测试
   - 消息处理测试
   - 错误处理测试
   - 并发连接测试

### 集成测试 (Integration Tests)

测试组件之间的协作：

1. **test_complete_dialogue_flow.py** - 完整对话流程测试
   - 文本对话流程
   - 音频对话流程
   - WebSocket 集成流程
   - 端到端场景测试
   - 性能测试
   - 可靠性测试

## 🚀 运行测试

### 安装依赖

```bash
cd backend
pip install -r requirements.txt

# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### 运行所有测试

```bash
# 从项目根目录运行
pytest

# 或者指定测试目录
pytest test/

# 详细输出
pytest -v

# 显示打印输出
pytest -s
```

### 运行特定测试

```bash
# 运行单元测试
pytest test/unit/

# 运行集成测试
pytest test/integration/

# 运行特定文件
pytest test/unit/test_asr_workflow.py

# 运行特定测试类
pytest test/unit/test_asr_workflow.py::TestMockASR

# 运行特定测试方法
pytest test/unit/test_asr_workflow.py::TestMockASR::test_mock_asr_instantiation
```

### 使用标记运行测试

```bash
# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 跳过慢速测试
pytest -m "not slow"

# 只运行需要 API key 的测试
pytest -m requires_api
```

### 生成覆盖率报告

```bash
# 生成终端覆盖率报告
pytest --cov=backend --cov-report=term

# 生成 HTML 覆盖率报告
pytest --cov=backend --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔧 环境配置

### 设置环境变量

创建 `.env.test` 文件：

```bash
# LLM 配置（用于 LLM 测试）
OPEN_AI_API_KEY=your_api_key_here

# ASR 配置（使用 Mock 即可不需要）
ASR_TYPE=mock

# TTS 配置（使用 Edge TTS）
TTS_TYPE=edge

# 其他配置
LOG_LEVEL=INFO
```

### API Key 要求

某些测试需要 API key：

- **LLM 测试**：需要 `OPEN_AI_API_KEY`
- **ASR 测试**：默认使用 Mock，不需要 key
- **TTS 测试**：使用 Edge TTS，不需要 key

如果没有 API key，相关测试会自动跳过。

## 📊 测试覆盖率目标

| 组件 | 当前覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| ASR 服务 | ~60% | 80% |
| LLM 服务 | ~50% | 80% |
| TTS 服务 | ~60% | 80% |
| WebSocket Handler | ~40% | 70% |
| **总体** | **~10%** | **70%** |

## 📝 编写测试指南

### 测试命名规范

- 文件名：`test_<module>.py`
- 类名：`Test<Feature>`
- 方法名：`test_<specific_functionality>`

### 测试结构

```python
class TestFeature:
    """测试功能描述"""

    @pytest.mark.asyncio
    async def test_business_workflow(self):
        """测试业务流程"""
        # Arrange（准备）
        component = Component()

        # Act（执行）
        result = await component.do_something()

        # Assert（断言）
        assert result is not None
        assert len(result) > 0
```

### 使用 Fixture

```python
@pytest.fixture
def mock_component():
    """创建 mock 组件"""
    return Component()

@pytest.fixture
async def async_fixture():
    """创建异步 fixture"""
    return await create_async_resource()
```

### 异步测试

```python
@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    result = await async_function()
    assert result is not None
```

### 跳过测试

```python
@pytest.mark.skipif(
    os.getenv("API_KEY") is None,
    reason="需要 API key"
)
async def test_with_api_key():
    """需要 API key 的测试"""
    pass

@pytest.mark.skip("暂时跳过")
def test_not_ready():
    """未完成的测试"""
    pass
```

## 🐛 调试测试

### 使用 pdb 调试

```bash
# 在测试中添加断点
import pdb; pdb.set_trace()

# 运行测试
pytest -s
```

### 查看详细输出

```bash
# 显示打印的输出
pytest -s -v

# 显示更详细的错误信息
pytest -vv --tb=long
```

### 只运行失败的测试

```bash
# 运行上次失败的测试
pytest --lf

# 先运行失败的，再运行其他的
pytest --ff
```

## 📈 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest --cov=backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 🔍 常见问题

### 1. 测试失败：ImportError

**问题**：找不到模块

**解决**：
```bash
# 从项目根目录运行
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
pytest
```

### 2. 异步测试失败

**问题**：asyncio 相关错误

**解决**：
```bash
# 确保安装了 pytest-asyncio
pip install pytest-asyncio

# 在 pytest.ini 中配置
# asyncio_mode = auto
```

### 3. 跳过需要 API 的测试

**问题**：没有 API key

**解决**：测试会自动跳过，或者在 `.env.test` 中配置 API key

## 📚 参考资源

- [Pytest 文档](https://docs.pytest.org/)
- [Pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [Pytest-cov 文档](https://pytest-cov.readthedocs.io/)

## ✨ 贡献指南

添加新测试时：

1. 确定测试类型（单元/集成/E2E）
2. 放置到正确的目录
3. 遵循命名规范
4. 添加必要的文档字符串
5. 运行测试确保通过
6. 更新此文档

---

**维护者**: Digital Human Platform Team
**最后更新**: 2026-03-05
