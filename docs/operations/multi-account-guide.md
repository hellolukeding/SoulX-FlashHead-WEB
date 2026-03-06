# GitHub 多账户配置指南

## 📋 当前状态

- **全局 Git 配置**: lukeding (lukeding9627@gmail.com)
- **目标账户**: hellolukeding
- **项目远程仓库**: github.com/hellolukeding/SoulX-FlashHead-WEB

## 🔑 方案 1: SSH 多账户配置（推荐）

### 步骤 1: 为 hellolukeding 创建专用 SSH 密钥

```bash
# 创建新的 SSH 密钥（使用邮箱作为注释）
ssh-keygen -t ed25519 -C "hellolukeding@example.com" -f ~/.ssh/id_ed25519_hellolukeding -N ""
```

### 步骤 2: 配置 SSH config 文件

```bash
# 创建或编辑 SSH config
cat >> ~/.ssh/config << 'EOF'

# GitHub 账户 1: lukeding (默认)
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519

# GitHub 账户 2: hellolukeding
Host github-hellolukeding
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_hellolukeding
EOF

# 设置正确权限
chmod 600 ~/.ssh/config
```

### 步骤 3: 添加公钥到 GitHub

1. **复制公钥**：
```bash
cat ~/.ssh/id_ed25519_hellolukeding.pub
```

2. **添加到 GitHub**：
   - 访问：https://github.com/settings/keys
   - 点击 "New SSH key"
   - Title: `hellolukeding@example.com`
   - Key: 粘贴公钥内容
   - 点击 "Add SSH key"

### 步骤 4: 修改项目远程仓库（使用 SSH 别名）

```bash
cd /opt/digital-human-platform

# 切换到 SSH（使用别名）
git remote set-url origin git@github-hellolukeding:hellolukeding/SoulX-FlashHead-WEB.git

# 验证
git remote -v
```

### 步骤 5: 配置项目本地 Git 账户

```bash
cd /opt/digital-human-platform

# 为本项目设置独立的用户配置（不覆盖全局配置）
git config user.name "hellolukeding"
git config user.email "hellolukeding@example.com"

# 验证
git config user.name
git config user.email
```

### 步骤 6: 测试并推送

```bash
# 测试 SSH 连接
ssh -T git@github-hellolukeding

# 应该显示：Hi hellolukeding! You've successfully authenticated...

# 推送
git push -u origin main
```

---

## 🌐 方案 2: HTTPS 凭据管理（备选）

如果不想使用 SSH，可以使用 HTTPS + 凭据助手：

### 步骤 1: 创建 GitHub Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 勾选权限：
   - ✅ repo (完整仓库访问权限)
4. 点击 "Generate token"
5. **复制 token**（只显示一次！）

### 步骤 2: 配置 Git 凭据助手

```bash
# 启用凭据存储
git config --global credential.helper store

# 针对本项目使用特定账户
cd /opt/digital-human-platform
git config user.name "hellolukeding"
git config user.email "hellolukeding@example.com"
```

### 步骤 3: 首次推送（输入凭据）

```bash
cd /opt/digital-human-platform

# 推送（会提示输入用户名和密码）
git push -u origin main

# 用户名：hellolukeding
# 密码：<粘贴刚才创建的 token>
```

凭据会被保存，下次推送无需再输入。

---

## 📊 账户配置总结

### 全局配置（~/.gitconfig）
```bash
[user]
    name = lukeding
    email = lukeding9627@gmail.com
```

### 项目本地配置（/opt/digital-human-platform/.git/config）
```bash
[user]
    name = hellolukeding
    email = hellolukeding@example.com
```

### SSH Config（~/.ssh/config）
```bash
# 默认账户：lukeding
Host github.com
    IdentityFile ~/.ssh/id_ed25519

# 特定账户：hellolukeding
Host github-hellolukeding
    HostName github.com
    IdentityFile ~/.ssh/id_ed25519_hellolukeding
```

---

## 🎯 使用示例

### 账户 1: lukeding（默认）
```bash
# 克隆 lukeding 的仓库
git clone git@github.com:lukeding/some-project.git

# 推送
git push
```

### 账户 2: hellolukeding（本项目）
```bash
cd /opt/digital-human-platform

# 远程 URL 使用别名
git remote -v
# origin  git@github-hellolukeding:hellolukeding/SoulX-FlashHead-WEB.git

# 推送
git push
```

---

## ✅ 验证配置

```bash
# 1. 检查全局 Git 配置
git config --global user.name
git config --global user.email

# 2. 检查项目本地配置
cd /opt/digital-human-platform
git config user.name
git config user.email

# 3. 检查 SSH 配置
cat ~/.ssh/config

# 4. 测试 SSH 连接
ssh -T git@github.com          # lukeding 账户
ssh -T git@github-hellolukeding  # hellolukeding 账户

# 5. 检查远程仓库
git remote -v
```

---

## 🔧 故障排查

### 问题 1: SSH 权限被拒绝
```bash
# 检查 SSH agent 是否加载了正确的密钥
ssh-add -l

# 添加特定密钥
ssh-add ~/.ssh/id_ed25519_hellolukeding
```

### 问题 2: 推送时显示错误的账户
```bash
# 检查项目的 .git/config
cat .git/config

# 确保远程 URL 使用正确的别名
git remote set-url origin git@github-hellolukeding:hellolukeding/repo.git
```

### 问题 3: Git 提交显示错误的作者
```bash
# 为项目设置本地配置
git config user.name "正确的名字"
git config user.email "正确的邮箱"
```

---

## 📝 推荐配置（一键脚本）

如果你选择方案 1（SSH），我可以帮你一键执行所有配置。需要我执行吗？

```bash
# 创建 SSH 密钥
# 配置 SSH config
# 设置项目本地 Git 配置
# 修改远程仓库 URL
# 测试连接
```

只需要告诉我：**执行 SSH 配置** 或者 **使用 HTTPS 方式**
