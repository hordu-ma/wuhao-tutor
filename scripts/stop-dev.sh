#!/bin/bash

# 五好伴学开发环境停止脚本
# 优雅地停止前端和后端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 进程ID存储文件
PIDFILE_DIR="$(pwd)/.dev-pids"
FRONTEND_PID_FILE="$PIDFILE_DIR/frontend.pid"
BACKEND_PID_FILE="$PIDFILE_DIR/backend.pid"

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

log_frontend() {
    echo -e "${CYAN}[FRONTEND]${NC} $1"
}

log_backend() {
    echo -e "${PURPLE}[BACKEND]${NC} $1"
}

# 检查是否有服务运行
check_services_status() {
    local services_running=false

    if [ -f "$FRONTEND_PID_FILE" ] || [ -f "$BACKEND_PID_FILE" ]; then
        services_running=true
    fi

    if [ "$services_running" = false ]; then
        log_info "没有发现正在运行的开发服务器"
        exit 0
    fi
}

# 停止前端服务
stop_frontend() {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")

        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            log_frontend "正在停止前端服务器 (PID: $FRONTEND_PID)"

            # 尝试优雅停止
            if kill -TERM "$FRONTEND_PID" 2>/dev/null; then
                # 等待进程停止
                local attempts=0
                while kill -0 "$FRONTEND_PID" 2>/dev/null && [ $attempts -lt 10 ]; do
                    sleep 1
                    attempts=$((attempts + 1))
                done

                # 如果还没停止，强制结束
                if kill -0 "$FRONTEND_PID" 2>/dev/null; then
                    log_warning "前端服务器未响应，强制停止..."
                    kill -KILL "$FRONTEND_PID" 2>/dev/null || true
                fi

                log_success "前端服务器已停止"
            else
                log_warning "无法停止前端服务器，进程可能已经停止"
            fi
        else
            log_warning "前端服务器进程不存在 (PID: $FRONTEND_PID)"
        fi

        rm -f "$FRONTEND_PID_FILE"
    else
        log_info "未发现前端服务器PID文件"
    fi
}

# 停止后端服务
stop_backend() {
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")

        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_backend "正在停止后端服务器 (PID: $BACKEND_PID)"

            # 尝试优雅停止
            if kill -TERM "$BACKEND_PID" 2>/dev/null; then
                # 等待进程停止
                local attempts=0
                while kill -0 "$BACKEND_PID" 2>/dev/null && [ $attempts -lt 10 ]; do
                    sleep 1
                    attempts=$((attempts + 1))
                done

                # 如果还没停止，强制结束
                if kill -0 "$BACKEND_PID" 2>/dev/null; then
                    log_warning "后端服务器未响应，强制停止..."
                    kill -KILL "$BACKEND_PID" 2>/dev/null || true
                fi

                log_success "后端服务器已停止"
            else
                log_warning "无法停止后端服务器，进程可能已经停止"
            fi
        else
            log_warning "后端服务器进程不存在 (PID: $BACKEND_PID)"
        fi

        rm -f "$BACKEND_PID_FILE"
    else
        log_info "未发现后端服务器PID文件"
    fi
}

# 清理相关进程
cleanup_related_processes() {
    log_info "清理相关进程..."

    # 清理可能的僵尸进程
    pkill -f "uvicorn src.main:app" 2>/dev/null || true
    pkill -f "vite.*--port" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true

    # 等待一下让进程完全停止
    sleep 2
}

# 清理临时文件
cleanup_temp_files() {
    if [ -d "$PIDFILE_DIR" ]; then
        log_info "清理临时文件..."

        # 保留日志文件，但显示统计信息
        if [ -f "$PIDFILE_DIR/frontend.log" ]; then
            FRONTEND_LOG_SIZE=$(wc -l < "$PIDFILE_DIR/frontend.log" 2>/dev/null || echo "0")
            log_info "前端日志: $FRONTEND_LOG_SIZE 行 ($PIDFILE_DIR/frontend.log)"
        fi

        if [ -f "$PIDFILE_DIR/backend.log" ]; then
            BACKEND_LOG_SIZE=$(wc -l < "$PIDFILE_DIR/backend.log" 2>/dev/null || echo "0")
            log_info "后端日志: $BACKEND_LOG_SIZE 行 ($PIDFILE_DIR/backend.log)"
        fi

        # 只删除PID文件，保留日志
        rm -f "$FRONTEND_PID_FILE" "$BACKEND_PID_FILE"

        # 如果目录为空（除了日志文件），则删除
        if [ -z "$(find "$PIDFILE_DIR" -name "*.log" -prune -o -type f -print)" ]; then
            # 询问是否删除日志文件
            if [ "$1" = "--clean-logs" ]; then
                log_info "清理日志文件..."
                rm -rf "$PIDFILE_DIR"
            fi
        fi
    fi
}

# 验证停止状态
verify_stop_status() {
    log_info "验证服务停止状态..."

    local frontend_port_found=false
    local backend_port_found=false

    # 检查常见端口是否还有服务运行
    for port in 5173 5174 5175 8000 8001 8002; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            local process_info=$(lsof -Pi :$port -sTCP:LISTEN 2>/dev/null | tail -n +2)
            if echo "$process_info" | grep -q -E "(vite|node|uvicorn)"; then
                if [ $port -ge 5173 ] && [ $port -le 5200 ]; then
                    frontend_port_found=true
                elif [ $port -ge 8000 ] && [ $port -le 8020 ]; then
                    backend_port_found=true
                fi
                log_warning "端口 $port 仍有进程运行:"
                echo "$process_info"
            fi
        fi
    done

    if [ "$frontend_port_found" = false ] && [ "$backend_port_found" = false ]; then
        log_success "所有开发服务器已完全停止"
    else
        log_warning "可能还有相关进程在运行，请手动检查"
    fi
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --clean-logs    停止服务并清理日志文件"
    echo "  --force         强制停止所有相关进程"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 正常停止开发服务器"
    echo "  $0 --clean-logs       # 停止服务器并清理日志"
    echo "  $0 --force           # 强制停止所有相关进程"
}

# 强制停止所有相关进程
force_stop() {
    log_warning "强制停止所有相关进程..."

    # 强制杀死所有相关进程
    pkill -9 -f "uvicorn src.main:app" 2>/dev/null || true
    pkill -9 -f "vite.*--port" 2>/dev/null || true
    pkill -9 -f "node.*vite" 2>/dev/null || true
    pkill -9 -f "npm run dev" 2>/dev/null || true
    pkill -9 -f "yarn dev" 2>/dev/null || true
    pkill -9 -f "pnpm run dev" 2>/dev/null || true

    # 清理PID文件
    rm -f "$FRONTEND_PID_FILE" "$BACKEND_PID_FILE"

    log_success "强制停止完成"
}

# 主函数
main() {
    echo ""
    echo "🛑 停止五好伴学开发环境..."
    echo ""

    # 处理命令行参数
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --force|-f)
            force_stop
            cleanup_temp_files "$1"
            verify_stop_status
            exit 0
            ;;
        --clean-logs)
            # 正常停止流程，但清理日志
            ;;
        "")
            # 正常停止流程
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac

    # 检查服务状态
    check_services_status

    # 停止服务
    log_info "开始停止开发服务器..."

    stop_frontend
    stop_backend

    # 清理相关进程
    cleanup_related_processes

    # 清理临时文件
    cleanup_temp_files "$1"

    # 验证停止状态
    verify_stop_status

    echo ""
    echo "✅ 五好伴学开发环境已停止"
    echo ""

    if [ "$1" != "--clean-logs" ] && [ -d "$PIDFILE_DIR" ]; then
        echo "💡 提示:"
        echo "  - 日志文件已保留在 $PIDFILE_DIR/"
        echo "  - 运行 '$0 --clean-logs' 可以清理日志文件"
        echo "  - 查看日志: tail -f $PIDFILE_DIR/*.log"
        echo ""
    fi
}

# 运行主函数
main "$@"
