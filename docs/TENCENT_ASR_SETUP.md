# 腾讯云 ASR 配置指南

**文档版本:** 1.0
**更新日期:** 2026-03-05

---

## 📋 概述

腾讯云语音识别（ASR）已集成到项目中，支持实时语音转文本功能。

### 支持的 ASR 类型

| ASR 类型 | 状态 | 说明 |
|----------|------|------|
| **MockASR** | ✅ 可用 | 模拟 ASR，用于测试 |
| **腾讯 ASR** | ✅ 已集成 | 需要配置腾讯云凭证 |
| **FunASR** | 🔲 待实现 | 阿里 FunASR（计划中）|

---

## 🔧 腾讯 ASR 配置

### 1. 获取腾讯云凭证

#### 步骤 1: 注册腾讯云账号
1. 访问 [腾讯云官网](https://cloud.tencent.com/)
2. 注册并登录账号

#### 步骤 2: 开通语音识别服务
1. 访问 [语音识别产品页](https://cloud.tencent.com/product/asr)
2. 点击"立即使用"
3. 开通服务（新用户有免费额度）

#### 步骤 3: 获取 API 密钥
1. 访问 [API 密钥管理](https://console.cloud.tencent.com/cam/capi)
2. 创建密钥或使用现有密钥
3. 记录 `SecretId` 和 `SecretKey`

---

### 2. 配置环境变量

编辑项目的 `.env` 文件：

```bash
# ASR 配置
ASR_TYPE=tencent

# 腾讯 ASR 凭证
TENCENT_ASR_SECRET_ID=your_secret_id_here
TENCENT_ASR_SECRET_KEY=your_secret_key_here
```

或通过环境变量设置：

```bash
export TENCENT_ASR_SECRET_ID=your_secret_id_here
export TENCENT_ASR_SECRET_KEY=your_secret_key_here
```

---

### 3. 验证配置

运行测试脚本验证配置：

```bash
cd /opt/digital-human-platform/backend
source venv/bin/activate
python tests/integration/test_tencent_asr.py
```

**预期输出:**
```
✅ 腾讯 ASR 凭证已配置: AKIDxxxxxxxx...
[ASR] 创建 ASR 实例: tencent
✅ 腾讯 ASR 初始化成功
ASR 类型: TencentASR
```

---

## 📊 ASR 对比

| 特性 | MockASR | 腾讯 ASR | FunASR |
|------|---------|----------|--------|
| **准确性** | ❌ 模拟数据 | ✅ 高 | ✅ 很高 |
| **实时性** | ✅ 即时 | ✅ 快 | ✅ 快 |
| **成本** | ✅ 免费 | 🟡 按量计费 | ✅ 免费 |
| **配置难度** | ✅ 无需配置 | 🟡 需要密钥 | 🟡 需要部署 |
| **中文支持** | ❌ 不支持 | ✅ 优秀 | ✅ 优秀 |

---

## 🧪 使用示例

### Python 代码

```python
from app.services.asr.factory import get_asr
import numpy as np

# 获取 ASR 实例
asr = get_asr()

# 准备音频数据（16kHz, float32）
audio_data = np.random.randn(16000).astype(np.float32) * 0.1

# 识别语音
result = await asr.recognize(audio_data)
print(f"识别结果: {result}")
```

### WebSocket 集成

在 WebSocket Handler 中自动使用：

```python
async def _handle_user_message(self, session_id: str, data: dict):
    # 获取 ASR 服务
    asr = get_asr()

    # 识别音频
    user_text = await asr.recognize(user_audio)

    # 继续对话流程...
```

---

## ⚠️ 注意事项

### 1. API 限制

腾讯云 ASR 限制：
- **一句话识别**: 最大音频时长 60s
- **录音文件识别**: 最大 5 小时
- **并发限制**: 根据购买的并发数

### 2. 音频格式要求

- **格式**: WAV (推荐)
- **采样率**: 16kHz
- **声道**: 单声道 (mono)
- **编码**: PCM

### 3. 费用说明

腾讯云 ASR 计费：
- **按调用次数计费**
- **新用户**: 每月 1000 次免费额度
- **超出部分**: 按量计费

详细价格: https://cloud.tencent.com/product/asr/pricing

---

## 🔄 回退机制

如果腾讯 ASR 配置失败或不可用，系统会自动回退到 MockASR：

```
腾讯 ASR 初始化失败
       ↓
警告日志记录
       ↓
回退到 MockASR
       ↓
继续服务（返回模拟文本）
```

**日志示例:**
```
⚠️  [ASR] 腾讯 ASR 凭证未配置，回退到 MockASR
```

---

## 📝 配置文件示例

### 完整的 .env 配置

```bash
# ==================== ASR 配置 ====================
# ASR 类型: mock, tencent, funasr
ASR_TYPE=tencent

# 腾讯 ASR 凭证（必需）
TENCENT_ASR_SECRET_ID=AKIDxxxxxxxxxxxxxxxx
TENCENT_ASR_SECRET_KEY=xxxxxxxxxxxxxxxx

# 可选：腾讯 ASR 参数
# TENCENT_ASR_ENGINE_MODEL_TYPE=16k_zh  # 引擎模型
# TENCENT_ASR_REGION=ap-beijing          # 地域
```

---

## 🐛 故障排除

### 问题 1: 认证失败

**错误:**
```
❌ 腾讯 ASR 认证失败: SecretId 不存在
```

**解决方案:**
1. 检查 `TENCENT_ASR_SECRET_ID` 是否正确
2. 确认密钥未被删除
3. 检查密钥是否有 ASR 服务权限

---

### 问题 2: 签名验证失败

**错误:**
```
❌ 腾讯 ASR 认证失败: 签名验证失败
```

**解决方案:**
1. 检查 `TENCENT_ASR_SECRET_KEY` 是否正确
2. 确保密钥没有多余空格
3. 尝试重新生成密钥

---

### 问题 3: 音频格式错误

**错误:**
```
❌ 腾讯 ASR 音频格式错误
```

**解决方案:**
1. 确保音频是 16kHz 采样率
2. 确保音频是单声道
3. 使用 WAV 格式

---

## 📚 相关文档

- [腾讯云 ASR 文档](https://cloud.tencent.com/document/product/1093)
- [一句话识别 API](https://cloud.tencent.com/document/api/1093/37822)
- [API 密钥管理](https://console.cloud.tencent.com/cam/capi)

---

## ✨ 下一步

### 高优先级
1. ✅ 集成腾讯 ASR（已完成）
2. 🔲 实现 FunASR（本地免费方案）
3. 🔲 性能优化（缓存、批量识别）

### 低优先级
4. 🔲 实时流式识别
5. 🔲 说话人分离
6. 🔲 情感识别

---

**配置完成时间:** 2026-03-05
**集成状态:** ✅ 已完成
**测试状态:** ✅ 通过
