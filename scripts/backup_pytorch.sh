#!/bin/bash

# PyTorch 版本备份和回滚脚本
# 用于在升级 PyTorch 失败时快速恢复

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录
BACKUP_DIR="/opt/digital-human-platform/pytorch_backup"
mkdir -p "$BACKUP_DIR"

print_info "创建备份目录: $BACKUP_DIR"

# 1. 备份当前 PyTorch 版本信息
print_info "备份当前 PyTorch 版本信息..."
source backend/venv/bin/activate
pip show torch > "$BACKUP_DIR/torch_version.txt"
pip show torchvision > "$BACKUP_DIR/torchvision_version.txt"
pip show torchaudio > "$BACKUP_DIR/torchaudio_version.txt"

current_torch=$(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
print_info "当前 PyTorch 版本: $current_torch"

# 2. 导出已安装包列表
print_info "导出已安装包列表..."
pip freeze > "$BACKUP_DIR/requirements_freeze.txt"
pip list --format=freeze > "$BACKUP_DIR/pip_list.txt"

# 3. 保存当前测试结果
print_info "保存当前测试结果..."
if [ -f "htmlcov/index.html" ]; then
    cp -r htmlcov "$BACKUP_DIR/"
    print_info "覆盖率报告已备份"
fi

# 4. 创建回滚脚本
print_info "创建回滚脚本..."
cat > "$BACKUP_DIR/rollback.sh" << 'EOF'
#!/bin/bash

# PyTorch 回滚脚本
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[INFO]${NC} 开始回滚 PyTorch 版本..."

cd /opt/digital-human-platform
source backend/venv/bin/activate

# 卸载当前版本
echo "卸载当前 PyTorch..."
pip uninstall torch torchvision torchaudio -y

# 安装备份版本
echo "恢复 PyTorch 版本..."
pip install torch==2.3.1+cu121 torchvision==0.18.1+cu121 torchaudio==2.3.1+cu121 --extra-index-url https://download.pytorch.org/whl/cu121

# 验证
python -c "import torch; print(f'PyTorch 版本: {torch.__version__}')"

echo -e "${GREEN}[SUCCESS]${NC} PyTorch 回滚完成"
EOF

chmod +x "$BACKUP_DIR/rollback.sh"
print_info "回滚脚本已创建: $BACKUP_DIR/rollback.sh"

# 5. 创建版本对比文件
print_info "创建版本对比文件..."
cat > "$BACKUP_DIR/VERSION_INFO.md" << EOF
# PyTorch 版本备份信息

**备份时间:** $(date '+%Y-%m-%d %H:%M:%S')

## 当前版本

- PyTorch: $(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
- CUDA: $(python -c "import torch; print(torch.version.cuda)" 2>/dev/null || echo "unknown")
- cuDNN: $(python -c "import torch; print(torch.backends.cudnn.version())" 2>/dev/null || echo "unknown")

## 支持的 GPU 架构

$(python -c "import torch; print(f'- {torch.cuda.get_arch_list()}')" 2>/dev/null || echo "unknown")

## 备份文件

- torch_version.txt - PyTorch 版本信息
- requirements_freeze.txt - 所有已安装包
- pip_list.txt - 包列表格式
- rollback.sh - 回滚脚本

## 回滚命令

\`\`\`bash
cd /opt/digital-human-platform
bash $BACKUP_DIR/rollback.sh
\`\`\`

## 升级目标版本

- PyTorch: 2.6.0 或更高 (支持 RTX 5090 sm_120)
- CUDA: 12.4 或更高
EOF

print_info "版本信息文件已创建: $BACKUP_DIR/VERSION_INFO.md"

# 6. 显示备份摘要
echo ""
print_info "=========================================="
print_info "PyTorch 备份完成"
print_info "=========================================="
echo ""
print_info "备份目录: $BACKUP_DIR"
print_info "当前版本: $current_torch"
echo ""
print_warning "回滚命令: bash $BACKUP_DIR/rollback.sh"
echo ""
print_info "现在可以安全地升级 PyTorch 了"
echo ""

# 显示备份内容
print_info "备份内容列表:"
ls -lh "$BACKUP_DIR"
