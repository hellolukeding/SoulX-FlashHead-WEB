# 📚 文档中心

## 文档结构

```
docs/
├── README.md                      # 本文件
├── architecture.md                # 系统架构文档
│
├── api/                           # API 文档
│   ├── rest-api.md               # REST API 接口
│   └── websocket-api.md          # WebSocket API 接口
│
├── development/                   # 开发文档
│   ├── development-plan.md       # 📋 开发方案（新增）
│   └── project-summary.md        # 📊 项目总结
│
└── operations/                    # 运维文档
    ├── multi-account-guide.md   # 🔑 多账户配置
    ├── push-guide.md            # 📤 推送指南
    ├── push-success.md          # ✅ 推送成功记录
    └── ssh-config-complete.md   # 🔒 SSH 配置完成记录
```

## 📖 文档导航

### 快速开始
1. [项目 README](../README.md) - 项目概述
2. [快速开始指南](../START_HERE.md) - 新手入门
3. [开发方案](development/development-plan.md) - **完整开发计划**
4. [项目总结](development/project-summary.md) - 项目结构和状态

### 技术文档
1. [系统架构](architecture.md) - 系统设计和技术选型
2. [REST API](api/rest-api.md) - REST 接口规范
3. [WebSocket API](api/websocket-api.md) - WebSocket 协议定义

### 运维文档
1. [多账户配置](operations/multi-account-guide.md) - Git 多账户设置
2. [推送指南](operations/push-guide.md) - 代码推送步骤
3. [推送成功记录](operations/push-success.md) - 首次推送记录
4. [SSH 配置完成](operations/ssh-config-complete.md) - SSH 密钥配置

## 🎯 开发路线图

### 阶段一：核心功能（1-2 周）
- ✅ 项目结构搭建
- ✅ 基础文档编写
- 🔴 **进行中**：推理引擎封装
- 🔴 **待开始**：WebSocket 服务
- 🔴 **待开始**：会话管理
- 🔴 **待开始**：前端 WebSocket 客户端

### 阶段二：优化完善（1 周）
- 性能优化
- 错误处理
- UI 优化

### 阶段三：扩展功能（可选）
- REST API 完善
- 用户认证
- 部署配置

## 📊 项目状态

| 模块 | 状态 | 进度 |
|------|------|------|
| 前端框架 | ✅ 完成 | 100% |
| 后端框架 | ✅ 完成 | 100% |
| 文档编写 | ✅ 完成 | 100% |
| 推理引擎 | 🔴 开发中 | 0% |
| WebSocket 服务 | 🔴 待开始 | 0% |
| 会话管理 | 🔴 待开始 | 0% |
| 前端集成 | 🔴 待开始 | 0% |

**总体进度**: 🟡 基础架构完成（30%），核心功能待实现

## 🚀 下一步行动

### 立即可做
1. 查看开发方案
2. 实现推理引擎封装
3. 实现 WebSocket 服务
4. 前后端集成测试

### 快速启动
```bash
# 查看开发方案
cat docs/development/development-plan.md

# 启动开发环境
./scripts/dev.sh

# 查看项目总结
cat docs/development/project-summary.md
```

---

**最后更新**: 2026-03-05
**维护者**: hellolukeding
