# 📤 推送到 GitHub 指南

## 当前状态

✅ Git 仓库已初始化
✅ 代码已提交（78 个文件，12384 行）
✅ 远程仓库已配置

## 需要认证

推送需要 GitHub 认证，请选择以下方式之一：

## 方式 1: 使用 Personal Access Token（推荐）

### 1. 创建 GitHub Token
1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 勾选权限：
   - `repo` (完整仓库访问权限)
4. 点击 "Generate token"
5. **复制 token**（只显示一次！）

### 2. 推送
```bash
cd /opt/digital-human-platform

# 推送时会提示输入用户名和密码
# 用户名：hellolukeding
# 密码：<粘贴刚才创建的 token>

git push -u origin main
```

## 方式 2: 使用 SSH 密钥

### 1. 生成 SSH 密钥
```bash
# 生成新的 SSH 密钥
ssh-keygen -t ed25519 -C "hellolukeding@example.com" -f ~/.ssh/github_ed25519 -N ""

# 查看公钥
cat ~/.ssh/github_ed25519.pub
```

### 2. 添加到 GitHub
1. 复制公钥内容
2. 访问：https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥，添加

### 3. 配置并推送
```bash
# 切换到 SSH URL
git remote set-url origin git@github.com:hellolukeding/SoulX-FlashHead-WEB.git

# 推送
git push -u origin main
```

## 方式 3: 在本地执行

如果你有本地开发环境：

```bash
# 1. 在本地克隆空仓库（如果还没创建）
# 先在 GitHub 创建仓库：SoulX-FlashHead-WEB

# 2. 添加远程并推送
git remote add origin https://github.com/hellolukeding/SoulX-FlashHead-WEB.git
git push -u origin main
```

## 验证推送成功

推送成功后，访问：
```
https://github.com/hellolukeding/SoulX-FlashHead-WEB
```

你应该能看到：
- ✅ README.md
- ✅ backend/
- ✅ desktop_app/
- ✅ docs/
- ✅ 所有文档和代码

## 常见问题

### Q: 提示 "Permission denied"
A: 检查：
1. 仓库是否已创建
2. Token/SSH 密钥是否正确
3. 用户名是否正确（hellolukeding）

### Q: 提示 "Repository not found"
A: 先在 GitHub 创建仓库：
1. 访问：https://github.com/new
2. 仓库名：SoulX-FlashHead-WEB
3. 设为 Public 或 Private
4. 不要初始化 README
5. 创建后再推送

### Q: Token 过期
A: 重新创建 token 并使用

## 下次推送

认证配置好后，下次直接：
```bash
git add .
git commit -m "your message"
git push
```
