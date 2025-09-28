#!/bin/bash

# 五好伴学开发环境重启脚本
# 快速重启前端和后端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查脚本是否存在
check_scripts() {
    if [ ! -f "$SCRIPT_DIR/stop-dev.sh" ]; then
        log_error "停止脚本不存在: $SCRIPT_DIR/stop-dev.sh"
        exit 1
    fi

    if [ ! -f "$SCRIPT_DIR/start-dev.sh" ]; then
        log_error "启动脚本不存在: $SCRIPT_DIR/start-dev.sh"
        exit 1
    fi

    if [ ! -x "$SCRIPT_DIR/stop-dev.sh" ]; then
        log_warning "停止脚本没有执行权限，正在修复..."
        chmod +x "$SCRIPT_DIR/stop-dev.sh"
    fi

    if [ ! -x "$SCRIPT_DIR/start-dev.sh" ]; then
        log_warning "启动脚本没有执行权限，正在修复..."
        chmod +x "$SCRIPT_DIR/start-dev.sh"
    fi
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --clean-logs    重启时清理所有日志文件"
    echo "  --force         强制停止并重启服务"
    echo "  --quick         快速重启（跳过依赖检查）"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 正常重启开发环境"
    echo "  $0 --clean-logs       # 重启并清理日志文件"
    echo "  $0 --force           # 强制重启所有服务"
    echo "  $0 --quick           # 快速重启模式"
}

# 停止服务
stop_services() {
    local stop_args=""

    case "${1:-}" in
        --clean-logs)
            stop_args="--clean-logs"
            log_info "停止服务并清理日志文件..."
            ;;
        --force)
            stop_args="--force"
            log_info "强制停止所有服务..."
            ;;
        *)
            log_info "正常停止服务..."
            ;;
    esac

    if "$SCRIPT_DIR/stop-dev.sh" $stop_args; then
        log_success "服务停止成功"
    else
        log_error "服务停止失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动开发服务..."

    # 给系统一些时间完全清理
    sleep 2

    if [ "$1" = "--quick" ]; then
        # 快速模式：直接启动，不检查依赖
        log_info "快速启动模式（跳过环境检查）"

        # 设置启动环境变量
        export SKIP_ENV_CHECK=1

        # 后台启动，避免阻塞
        nohup "$SCRIPT_DIR/start-dev.sh" > /dev/null 2>&1 &

        local start_pid=$!
        log_info "启动脚本已在后台运行 (PID: $start_pid)"

        # 等待一下让服务有时间启动
        log_info "等待服务启动..."
        sleep 10

        # 检查启动状态
        if "$SCRIPT_DIR/status-dev.sh" > /dev/null 2>&1; then
            log_success "快速启动完成"
            "$SCRIPT_DIR/status-dev.sh"
        else
            log_warning "服务可能还在启动中，请稍后检查状态"
        fi
    else
        # 正常启动模式
        if "$SCRIPT_DIR/start-dev.sh"; then
            log_success "服务启动成功"
        else
            log_error "服务启动失败"
            exit 1
        fi
    fi
}

# 检查重启前状态
check_pre_restart_status() {
    log_info "检查重启前状态..."

    if [ -f "$(pwd)/.dev-pids/frontend.pid" ] || [ -f "$(pwd)/.dev-pids/backend.pid" ]; then
        log_info "发现运行中的开发服务器"
        return 0
    else
        log_warning "没有发现运行中的开发服务器"

        # 检查是否有相关端口在监听
        local has_services=false
        for port in 5173 5174 5175 8000 8001 8002; do
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                has_services=true
                break
            fi
        done

        if [ "$has_services" = true ]; then
            log_info "发现相关端口有服务运行"
            return 0
        else
            log_warning "没有发现任何相关服务，将直接启动"
            return 1
        fi
    fi
}

# 验证重启后状态
verify_restart_status() {
    log_info "验证重启后状态..."

    sleep 3

    if "$SCRIPT_DIR/status-dev.sh" > /dev/null 2>&1; then
        log_success "重启验证通过"
        echo ""
        echo "=========================================="
        echo "🎉 五好伴学开发环境重启完成"
        echo "=========================================="
        "$SCRIPT_DIR/status-dev.sh"
    else
        log_error "重启验证失败，请检查服务状态"
        exit 1
    fi
}

# 主函数
main() {
    echo ""
    echo "🔄 重启五好伴学开发环境..."
    echo ""

    # 处理命令行参数
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --clean-logs|--force|--quick)
            # 有效参数，继续处理
            ;;
        "")
            # 无参数，正常模式
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac

    # 检查必要的脚本
    check_scripts

    # 检查重启前状态
    local has_running_services=false
    if check_pre_restart_status; then
        has_running_services=true
    fi

    # 如果有运行中的服务，先停止
    if [ "$has_running_services" = true ]; then
        stop_services "$1"
        echo ""
    else
        log_info "没有需要停止的服务，直接启动..."
        echo ""
    fi

    # 启动服务
    start_services "$1"

    # 如果不是快速模式，验证重启状态
    if [ "$1" != "--quick" ]; then
        echo ""
        verify_restart_status
    fi

    echo ""
    echo "💡 提示:"
    echo "  - 运行 './scripts/status-dev.sh' 检查服务状态"
    echo "  - 运行 './scripts/stop-dev.sh' 停止服务"
    echo "  - 查看日志: tail -f .dev-pids/*.log"
    echo ""
}

# 捕获中断信号
trap 'log_warning "重启过程被中断"; exit 1' INT TERM

# 运行主函数
main "$@"
