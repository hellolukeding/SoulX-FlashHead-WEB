#!/bin/bash

# 测试运行脚本
# Digital Human Platform Test Runner

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
    -h, --help          显示此帮助信息
    -u, --unit          只运行单元测试
    -i, --integration   只运行集成测试
    -a, --all           运行所有测试（默认）
    -c, --cov           生成覆盖率报告
    -v, --verbose       详细输出
    -s, --skip-slow     跳过慢速测试
    --no-api            跳过需要 API key 的测试

示例:
    $0                  # 运行所有测试
    $0 -u               # 只运行单元测试
    $0 -c               # 运行测试并生成覆盖率报告
    $0 -v -s            # 详细输出，跳过慢速测试

EOF
}

# 默认参数
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_COVERAGE=false
VERBOSE="-v"
SKIP_SLOW=false
SKIP_API=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--unit)
            RUN_UNIT=true
            RUN_INTEGRATION=false
            shift
            ;;
        -i|--integration)
            RUN_UNIT=false
            RUN_INTEGRATION=true
            shift
            ;;
        -a|--all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            shift
            ;;
        -c|--cov)
            RUN_COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE="-vv --tb=short"
            shift
            ;;
        -s|--skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        --no-api)
            SKIP_API=true
            shift
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 进入项目根目录
cd "$(dirname "$0")"

# 检查 Python 环境
print_info "检查 Python 环境..."
if ! command -v python &> /dev/null; then
    print_error "未找到 Python"
    exit 1
fi

PYTHON_VERSION=$(python --version | cut -d' ' -f2)
print_info "Python 版本: $PYTHON_VERSION"

# 检查依赖
print_info "检查测试依赖..."
if ! python -c "import pytest" 2>/dev/null; then
    print_warning "pytest 未安装"
    print_info "安装测试依赖..."
    pip install pytest pytest-asyncio pytest-cov pytest-mock
fi

# 设置 Python 路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# 构建 pytest 命令
PYTEST_CMD="pytest"

# 添加测试路径
TEST_PATHS=""
if [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = false ]; then
    TEST_PATHS="test/unit/"
elif [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = true ]; then
    TEST_PATHS="test/integration/"
fi

# 添加覆盖率
if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=backend --cov-report=term-missing --cov-report=html"
fi

# 添加标记
MARKERS=""
if [ "$SKIP_SLOW" = true ]; then
    MARKERS="$MARKERS and not slow"
fi
if [ "$SKIP_API" = true ]; then
    MARKERS="$MARKERS and not requires_api"
fi

if [ -n "$MARKERS" ]; then
    # 移除开头的 " and "
    MARKERS="${MARKERS# and }"
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

# 组合完整命令
if [ -n "$TEST_PATHS" ]; then
    PYTEST_CMD="$PYTEST_CMD $TEST_PATHS"
fi

PYTEST_CMD="$PYTEST_CMD $VERBOSE"

# 打印运行信息
echo ""
print_info "=========================================="
print_info "Digital Human Platform 测试运行"
print_info "=========================================="
echo ""
if [ "$RUN_UNIT" = true ]; then
    print_info "✓ 运行单元测试"
else
    print_warning "✗ 跳过单元测试"
fi

if [ "$RUN_INTEGRATION" = true ]; then
    print_info "✓ 运行集成测试"
else
    print_warning "✗ 跳过集成测试"
fi

if [ "$RUN_COVERAGE" = true ]; then
    print_info "✓ 生成覆盖率报告"
fi

if [ "$SKIP_SLOW" = true ]; then
    print_warning "⚠ 跳过慢速测试"
fi

if [ "$SKIP_API" = true ]; then
    print_warning "⚠ 跳过需要 API key 的测试"
fi

echo ""
print_info "运行命令: $PYTEST_CMD"
echo ""

# 运行测试
print_info "开始运行测试..."
echo ""

eval $PYTEST_CMD
TEST_EXIT_CODE=$?

echo ""

# 检查结果
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "所有测试通过！"
    echo ""

    # 显示覆盖率报告
    if [ "$RUN_COVERAGE" = true ]; then
        print_info "覆盖率报告已生成:"
        print_info "  - 终端: 见上方输出"
        print_info "  - HTML: htmlcov/index.html"
        echo ""

        # 尝试打开浏览器
        if command -v xdg-open &> /dev/null; then
            print_info "正在打开浏览器..."
            xdg-open htmlcov/index.html &> /dev/null &
        elif command -v open &> /dev/null; then
            print_info "正在打开浏览器..."
            open htmlcov/index.html &> /dev/null &
        fi
    fi

    exit 0
else
    print_error "测试失败"
    echo ""
    print_info "提示:"
    print_info "  - 使用 -v 查看详细输出"
    print_info "  - 使用 -s 查看打印的调试信息"
    print_info "  - 检查日志文件获取更多信息"
    echo ""
    exit 1
fi
