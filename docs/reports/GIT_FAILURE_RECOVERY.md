# Git 推送失败恢复方案

**时间:** 2026-03-05 14:00

---

## ❌ 问题

**错误:** 删除大 pack 文件后，git 对象数据库损坏

**影响:**
- 本地仓库无法正常工作
- 无法 git push
- 26个本地提交无法推送

---

## 🔍 问题根源

1. **大文件问题:**
   - SoulX-FlashHead 模型文件（5.7GB, 1.6GB）
   - 被 git 跟踪并提交到仓库
   - 导致仓库过大（13GB .git 目录）

2. **修复尝试:**
   - 删除大 pack 文件
   - 导致对象数据库损坏

---

## ✅ 成功完成的部分

1. **PyTorch 升级成功**
   - 2.3.1 → 2.6.0+cu124
   - 所有依赖已更新
   - 备份已创建

2. **测试代码已完成**
   - 95个测试用例
   - 完整文档

---

## 🎯 恢复方案

### 方案1: 从远程重新克隆（推荐）

```bash
# 1. 备份当前工作
cp -r . /opt/digital-human-platform.backup

# 2. 删除损坏的 .git 目录
rm -rf .git

# 3. 重新克隆
git clone git@github-hellolukeding:hellolukeding/SoulX-FlashHead-WEB.git temp_repo

# 4. 恢复测试代码
cp -r temp_repo/.git ./

# 5. 应用测试提交
git fetch origin main
git rebase origin/main  # 或使用 merge

# 6. 推送
git push origin main
```

### 方案2: 使用 Git LFS 管理大文件

```bash
# 安装 Git LFS
curl -s https://packagecloud.io/install/repositories/github/git-lfs/git-lfs/linux-amd64 > /tmp/git-lfs.deb
sudo dpkg -i /tmp/git-lfs.deb

# 追踪大文件
git lfs install
git lfs track "*.safetensors"
git lfs track "*.pth"
git lfs track "*.pt"
git lfs track "*.bin"

# 提交 .gitattributes
git add .gitattributes
git commit -m "chore: 添加 Git LFS 配置"
```

### 方案3: 创建测试专用分支

```bash
# 从远程创建新分支
git checkout -b test-framework origin/main

# 添加测试文件
git add test/ pytest.ini run_tests.sh *.md backend/app/core/config.py

# 提交测试框架
git commit -m "test: 添加完整的测试框架"
git push origin test-framework

# 创建 PR 合并到 main
```

---

## 📊 当前测试代码状态

**本地有但未推送的代码:**
- test/ 目录（95个测试）
- pytest.ini
- run_tests.sh
- *.md 文档
- backend/app/core/config.py 修复

**大小:** 约 5MB（纯代码，无模型文件）

---

## 💡 建议的解决方案

### 推荐方案：创建新分支推送测试

**优势:**
- 不影响主分支
- 避免大文件问题
- 可以独立推送测试代码
- 便于 PR review

**步骤:**

1. **保存测试代码**
```bash
# 创建补丁备份
git format-patch -N HEAD~26 HEAD > /tmp/test-framework.patch
```

2. **重新初始化仓库**
```bash
cd /opt
git clone git@github-hellukeding:hellolukeding/SoulX-FlashHead-WEB.git digital-human-platform-new
cd digital-human-platform-new

# 复制测试代码
cp -r /opt/digital-human-platform/test .
cp /opt/digital-human-platform/pytest.ini .
cp -r /opt/digital-human-platform/*.md .

# 安装依赖
cd backend
source venv/bin/activate
pip install pytest pytest-asyncio pytest-cov
```

3. **推送测试框架**
```bash
git add test/ pytest.ini *.md
git commit -m "test: 添加完整的测试框架 (95个测试)"
git push origin main
```

---

## 🔄 回滚 PyTorch

如果需要回滚到 PyTorch 2.3.1：

```bash
bash /opt/digital-human-platform/pytorch_backup/rollback.sh
```

---

## 📝 总结

**问题:** Git 仓库损坏，无法推送

**原因:** 删除大 pack 文件导致对象数据库损坏

**解决方案:**
1. 重新克隆仓库（推荐）
2. 使用 Git LFS 管理大文件
3. 创建测试分支

**测试代码:**
- ✅ 已完成并备份
- ✅ 可以轻松恢复
- ✅ PyTorch 已升级到 2.6.0

---

**状态:** 需要重新初始化仓库
