#!/bin/bash

# 五好伴学开发环境状态检查脚本
# 检查前端和后端开发服务器的运行状态

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

# 获取进程信息
get_process_info() {
    local pid=$1
    if kill -0 "$pid" 2>/dev/null; then
        local cpu_usage=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null | xargs)
        local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | xargs)
        local start_time=$(ps -p "$pid" -o lstart --no-headers 2>/dev/null)
        echo "CPU: ${cpu_usage}%, 内存: ${mem_usage}%, 启动时间: ${start_time}"
    else
        echo "进程不存在"
    fi
}

# 检查端口状态
check_port_status() {
    local port=$1
    local service_name=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local process_info=$(lsof -Pi :$port -sTCP:LISTEN 2>/dev/null | tail -n +2)
        echo -e "${GREEN}✓${NC} $service_name 端口 $port 正在监听"
        echo "  进程信息: $(echo "$process_info" | awk '{print $1" (PID: "$2")"}')"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name 端口 $port 未在监听"
        return 1
    fi
}

# 检查健康状态
check_health_status() {
    local url=$1
    local service_name=$2

    if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
        local response_time=$(curl -s -w "%{time_total}" -o /dev/null --max-time 5 "$url" 2>/dev/null)
        echo -e "${GREEN}✓${NC} $service_name 健康检查通过 (响应时间: ${response_time}s)"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name 健康检查失败"
        return 1
    fi
}

# 检查前端服务状态
check_frontend_status() {
    echo "=========================================="
    echo "🖥️  前端服务状态"
    echo "=========================================="

    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        log_frontend "PID文件存在: $FRONTEND_PID"

        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            log_success "前端进程运行中 (PID: $FRONTEND_PID)"
            echo "  $(get_process_info "$FRONTEND_PID")"

            # 检查常见前端端口
            local frontend_port_found=false
            for port in 5173 5174 5175 5176 5177; do
                if check_port_status $port "前端服务"; then
                    frontend_port_found=true
                    check_health_status "http://localhost:$port" "前端应用"
                    break
                fi
            done

            if [ "$frontend_port_found" = false ]; then
                log_warning "前端进程运行但未找到监听端口"
            fi
        else
            log_error "前端进程不存在 (PID: $FRONTEND_PID)"
        fi
    else
        log_info "前端PID文件不存在"

        # 仍然检查端口，可能有手动启动的服务
        for port in 5173 5174 5175 5176 5177; do
            if check_port_status $port "前端服务"; then
                check_health_status "http://localhost:$port" "前端应用"
                break
            fi
        done
    fi

    # 检查前端日志
    if [ -f "$PIDFILE_DIR/frontend.log" ]; then
        local log_size=$(wc -l < "$PIDFILE_DIR/frontend.log" 2>/dev/null || echo "0")
        local last_modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$PIDFILE_DIR/frontend.log" 2>/dev/null || echo "未知")
        echo "  日志文件: $PIDFILE_DIR/frontend.log ($log_size 行, 最后修改: $last_modified)"

        # 显示最近几行日志
        if [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
            echo "  最近日志:"
            tail -n 3 "$PIDFILE_DIR/frontend.log" 2>/dev/null | sed 's/^/    /' || echo "    无法读取日志"
        fi
    fi
}

# 检查后端服务状态
check_backend_status() {
    echo ""
    echo "=========================================="
    echo "🔧 后端服务状态"
    echo "=========================================="

    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        log_backend "PID文件存在: $BACKEND_PID"

        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_success "后端进程运行中 (PID: $BACKEND_PID)"
            echo "  $(get_process_info "$BACKEND_PID")"

            # 检查常见后端端口
            local backend_port_found=false
            for port in 8000 8001 8002 8003 8004; do
                if check_port_status $port "后端服务"; then
                    backend_port_found=true
                    check_health_status "http://localhost:$port/health" "后端API"
                    echo "  API文档: http://localhost:$port/docs"
                    break
                fi
            done

            if [ "$backend_port_found" = false ]; then
                log_warning "后端进程运行但未找到监听端口"
            fi
        else
            log_error "后端进程不存在 (PID: $BACKEND_PID)"
        fi
    else
        log_info "后端PID文件不存在"

        # 仍然检查端口，可能有手动启动的服务
        for port in 8000 8001 8002 8003 8004; do
            if check_port_status $port "后端服务"; then
                check_health_status "http://localhost:$port/health" "后端API"
                echo "  API文档: http://localhost:$port/docs"
                break
            fi
        done
    fi

    # 检查后端日志
    if [ -f "$PIDFILE_DIR/backend.log" ]; then
        local log_size=$(wc -l < "$PIDFILE_DIR/backend.log" 2>/dev/null || echo "0")
        local last_modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$PIDFILE_DIR/backend.log" 2>/dev/null || echo "未知")
        echo "  日志文件: $PIDFILE_DIR/backend.log ($log_size 行, 最后修改: $last_modified)"

        # 显示最近几行日志
        if [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
            echo "  最近日志:"
            tail -n 3 "$PIDFILE_DIR/backend.log" 2>/dev/null | sed 's/^/    /' || echo "    无法读取日志"
        fi
    fi
}

# 检查系统资源
check_system_resources() {
    echo ""
    echo "=========================================="
    echo "📊 系统资源状态"
    echo "=========================================="

    # CPU使用率
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | cut -d'%' -f1 2>/dev/null || echo "N/A")
    echo "CPU 使用率: ${cpu_usage}%"

    # 内存使用率
    local mem_info=$(vm_stat 2>/dev/null || echo "无法获取内存信息")
    if [ "$mem_info" != "无法获取内存信息" ]; then
        local pages_free=$(echo "$mem_info" | grep "Pages free" | awk '{print $3}' | cut -d. -f1)
        local pages_active=$(echo "$mem_info" | grep "Pages active" | awk '{print $3}' | cut -d. -f1)
        local pages_inactive=$(echo "$mem_info" | grep "Pages inactive" | awk '{print $3}' | cut -d. -f1)
        local pages_wired=$(echo "$mem_info" | grep "Pages wired down" | awk '{print $4}' | cut -d. -f1)

        if [ -n "$pages_free" ] && [ -n "$pages_active" ] && [ -n "$pages_inactive" ] && [ -n "$pages_wired" ]; then
            local total_pages=$((pages_free + pages_active + pages_inactive + pages_wired))
            local used_pages=$((pages_active + pages_inactive + pages_wired))
            local mem_usage=$((used_pages * 100 / total_pages))
            echo "内存使用率: ${mem_usage}%"
        else
            echo "内存使用率: 无法计算"
        fi
    else
        echo "内存使用率: N/A"
    fi

    # 磁盘使用率
    local disk_usage=$(df -h . | tail -1 | awk '{print $5}' 2>/dev/null || echo "N/A")
    echo "磁盘使用率: $disk_usage"
}

# 显示网络信息
show_network_info() {
    echo ""
    echo "=========================================="
    echo "🌐 网络信息"
    echo "=========================================="

    # 获取本机IP
    local local_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
    echo "本机IP: $local_ip"

    # 检查网络连接
    if ping -c 1 -W 3000 8.8.8.8 >/dev/null 2>&1; then
        echo -e "网络连接: ${GREEN}✓ 正常${NC}"
    else
        echo -e "网络连接: ${RED}✗ 异常${NC}"
    fi

    # 显示活跃的网络连接
    echo "活跃的开发端口:"
    lsof -iTCP -sTCP:LISTEN 2>/dev/null | grep -E ":(5173|5174|5175|8000|8001|8002)" | while read line; do
        echo "  $line"
    done
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --verbose, -v   显示详细信息（包括日志摘要）"
    echo "  --watch, -w     持续监控模式（每5秒刷新一次）"
    echo "  --help, -h      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 检查服务状态"
    echo "  $0 --verbose    # 显示详细状态信息"
    echo "  $0 --watch      # 持续监控模式"
}

# 监控模式
watch_mode() {
    log_info "进入持续监控模式... (按 Ctrl+C 退出)"

    while true; do
        clear
        echo "🔄 $(date '+%Y-%m-%d %H:%M:%S') - 五好伴学开发环境状态"
        check_frontend_status "$1"
        check_backend_status "$1"
        check_system_resources

        echo ""
        echo "下次刷新: 5秒后... (按 Ctrl+C 退出)"
        sleep 5
    done
}

# 主函数
main() {
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --watch|-w)
            trap 'echo -e "\n\n🛑 监控已停止"; exit 0' INT TERM
            watch_mode "${2:-}"
            ;;
        --verbose|-v)
            echo "🔍 五好伴学开发环境详细状态检查"
            check_frontend_status "$1"
            check_backend_status "$1"
            check_system_resources
            show_network_info
            ;;
        "")
            echo "🔍 五好伴学开发环境状态检查"
            check_frontend_status
            check_backend_status
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac

    echo ""
    echo "💡 提示:"
    echo "  - 运行 '$0 --verbose' 查看详细信息"
    echo "  - 运行 '$0 --watch' 进入持续监控模式"
    echo "  - 运行 './scripts/start-dev.sh' 启动开发环境"
    echo "  - 运行 './scripts/stop-dev.sh' 停止开发环境"
    echo ""
}

# 运行主函数
main "$@"
