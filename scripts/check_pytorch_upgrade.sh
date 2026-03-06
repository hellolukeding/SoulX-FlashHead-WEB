#!/bin/bash

# PyTorch 升级状态监控脚本

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}PyTorch 升级状态检查${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

source backend/venv/bin/activate 2>/dev/null || true

# 检查当前版本
echo -e "${GREEN}当前 PyTorch 版本:${NC}"
python -c "import torch; print(f'  版本: {torch.__version__}')" 2>/dev/null || echo "  未知（导入失败）"
python -c "import torch; print(f'  CUDA: {torch.version.cuda}')" 2>/dev/null || echo "  未知"
python -c "import torch; arch_list = torch.cuda.get_arch_list(); print(f'  架构: {arch_list}')" 2>/dev/null || echo "  未知"
echo ""

# 检查 SM_120 支持
echo -e "${GREEN}RTX 5090 支持检查:${NC}"
python -c "
import torch
arch_list = torch.cuda.get_arch_list()
if 'sm_120' in str(arch_list):
    print('  ✅ SM_120 支持: 是')
else:
    print('  ❌ SM_120 支持: 否')
    print(f'  当前支持: {arch_list}')
" 2>/dev/null || echo "  检查失败"
echo ""

# 检查升级进程
echo -e "${GREEN}升级进程状态:${NC}"
if ps aux | grep -q "pip install.*torch"; then
    pid=$(ps aux | grep "pip install.*torch" | grep -v grep | awk '{print $2}' | head -1)
    elapsed=$(ps -p $pid -o etime= 2>/dev/null | awk '{print $1}' || echo "未知")
    echo "  ⏳ 升级进程运行中 (PID: $pid, 运行时间: $elapsed)"
else
    echo "  ✅ 升级进程已完成或未运行"
fi
echo ""

# 检查 Qwen2ForCausalLM
echo -e "${GREEN}CosyVoice 依赖检查:${NC}"
python -c "
try:
    from transformers import Qwen2ForCausalLM
    print('  ✅ Qwen2ForCausalLM: 可用')
except ImportError as e:
    print(f'  ❌ Qwen2ForCausalLM: 不可用 ({e})')
" 2>/dev/null || echo "  检查失败"
echo ""

# 提供回滚选项
echo -e "${YELLOW}如果升级失败，可以使用以下命令回滚:${NC}"
echo -e "  bash /opt/digital-human-platform/pytorch_backup/rollback.sh"
echo ""

echo -e "${YELLOW}========================================${NC}"
