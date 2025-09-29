#!/bin/bash

# 五好伴学开发环境启动脚本
# 同时启动前端和后端开发服务器

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

# 清理函数
cleanup() {
    log_warning "正在停止开发服务器..."

    # 停止前端服务
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            log_frontend "停止前端服务器 (PID: $FRONTEND_PID)"
            kill -TERM "$FRONTEND_PID" 2>/dev/null || true
            sleep 2
            kill -KILL "$FRONTEND_PID" 2>/dev/null || true
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    # 停止后端服务
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_backend "停止后端服务器 (PID: $BACKEND_PID)"
            kill -TERM "$BACKEND_PID" 2>/dev/null || true
            sleep 2
            kill -KILL "$BACKEND_PID" 2>/dev/null || true
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    log_success "所有开发服务器已停止"
    exit 0
}

# 检查项目根目录
check_project_root() {
    log_info "检查项目结构..."

    if [ ! -f "pyproject.toml" ]; then
        log_error "未在项目根目录下执行脚本，请在 wuhao-tutor 目录下运行"
        exit 1
    fi

    if [ ! -d "frontend" ]; then
        log_error "frontend 目录不存在"
        exit 1
    fi

    if [ ! -d "src" ]; then
        log_error "src 目录不存在"
        exit 1
    fi

    log_success "项目结构检查通过"
}

# 检查 Python 环境
check_python_env() {
    log_info "检查 Python 环境..."

    if ! command -v uv &> /dev/null; then
        log_error "uv 未安装，请先安装 uv 包管理器"
        log_info "安装命令: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        log_info "创建虚拟环境..."
        uv venv
    fi

    # 激活虚拟环境
    source .venv/bin/activate

    # 安装依赖
    log_info "安装 Python 依赖..."
    uv sync --dev

    PYTHON_VERSION=$(python --version)
    log_success "Python 环境检查通过 ($PYTHON_VERSION)"
}

# 检查 Node.js 环境
check_node_env() {
    log_info "检查 Node.js 环境..."

    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js 18+"
        exit 1
    fi

    NODE_VERSION=$(node --version | cut -d'v' -f2)
    MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1)

    if [ "$MAJOR_VERSION" -lt "18" ]; then
        log_error "Node.js 版本过低 ($NODE_VERSION)，需要 18+ 版本"
        exit 1
    fi

    log_success "Node.js 环境检查通过 (v$NODE_VERSION)"
}

# 检查包管理器
check_package_manager() {
    log_info "检查前端包管理器..."

    cd frontend

    if [ -f "pnpm-lock.yaml" ]; then
        PACKAGE_MANAGER="pnpm"
        if ! command -v pnpm &> /dev/null; then
            log_warning "检测到 pnpm 锁文件但 pnpm 未安装，尝试安装..."
            npm install -g pnpm
        fi
    elif [ -f "yarn.lock" ]; then
        PACKAGE_MANAGER="yarn"
        if ! command -v yarn &> /dev/null; then
            log_warning "检测到 yarn 锁文件但 yarn 未安装，尝试安装..."
            npm install -g yarn
        fi
    else
        PACKAGE_MANAGER="npm"
    fi

    log_success "使用包管理器: $PACKAGE_MANAGER"
    cd ..
}

# 安装前端依赖
install_frontend_dependencies() {
    log_info "安装前端依赖..."

    cd frontend

    case $PACKAGE_MANAGER in
        "pnpm")
            pnpm install
            ;;
        "yarn")
            yarn install
            ;;
        "npm")
            npm install
            ;;
    esac

    if [ $? -eq 0 ]; then
        log_success "前端依赖安装完成"
    else
        log_error "前端依赖安装失败"
        exit 1
    fi

    cd ..
}

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# 查找可用端口
find_available_port() {
    local start_port=$1
    local max_port=$2

    for ((port=$start_port; port<=$max_port; port++)); do
        if check_port $port; then
            echo $port
            return
        fi
    done

    log_error "未找到可用端口 ($start_port-$max_port)"
    exit 1
}

# 清理僵尸端口进程
cleanup_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)

    if [ -n "$pids" ]; then
        log_warning "端口 $port 被占用，正在清理进程..."
        for pid in $pids; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "终止进程 PID: $pid"
                kill -TERM "$pid" 2>/dev/null || true
                sleep 1
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
        sleep 2
    fi
}

# 启动后端服务器
start_backend_server() {
    log_backend "启动后端开发服务器..."

    # 创建PID目录
    mkdir -p "$PIDFILE_DIR"

    # 清理可能的僵尸进程
    cleanup_port 8000

    # 查找可用端口
    BACKEND_PORT=$(find_available_port 8000 8020)
    export BACKEND_PORT

    # 设置环境变量
    export ENVIRONMENT=development
    export DEBUG=true
    export HOST=127.0.0.1
    export PORT=$BACKEND_PORT

    # 激活虚拟环境并启动后端
    source .venv/bin/activate

    log_backend "后端服务器将在端口 $BACKEND_PORT 启动"

    # 后台启动后端服务器
    nohup uv run uvicorn src.main:app \
        --host 127.0.0.1 \
        --port $BACKEND_PORT \
        --reload \
        --log-level info \
        > "$PIDFILE_DIR/backend.log" 2>&1 &

    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"

    log_backend "后端服务器已启动 (PID: $BACKEND_PID)"
}

# 启动前端服务器
start_frontend_server() {
    log_frontend "启动前端开发服务器..."

    # 保存当前目录
    local project_root=$(pwd)
    cd frontend

    # 清理可能的僵尸进程
    cleanup_port 5173

    # 查找可用端口
    FRONTEND_PORT=$(find_available_port 5173 5200)

    # 设置环境变量
    export NODE_ENV=development
    export VITE_API_BASE_URL=http://localhost:$BACKEND_PORT/api/v1
    export VITE_DEV_PORT=$FRONTEND_PORT

    log_frontend "前端服务器将在端口 $FRONTEND_PORT 启动"

    # 使用绝对路径来写入日志
    local frontend_log_file="$project_root/.dev-pids/frontend.log"

    # 后台启动前端服务器，禁用自动打开浏览器
    case $PACKAGE_MANAGER in
        "pnpm")
            nohup pnpm run dev --port $FRONTEND_PORT --host --no-open > "$frontend_log_file" 2>&1 &
            ;;
        "yarn")
            nohup yarn dev --port $FRONTEND_PORT --host --no-open > "$frontend_log_file" 2>&1 &
            ;;
        "npm")
            nohup npm run dev -- --port $FRONTEND_PORT --host --no-open > "$frontend_log_file" 2>&1 &
            ;;
    esac

    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"

    log_frontend "前端服务器已启动 (PID: $FRONTEND_PID)"

    cd ..
}

# 健康检查
health_check() {
    log_info "等待服务器启动..."
    sleep 5

    # 检查后端健康状态
    local backend_attempts=20
    local backend_healthy=false

    for ((i=1; i<=backend_attempts; i++)); do
        if curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
            log_backend "后端服务器健康检查通过"
            backend_healthy=true
            break
        fi
        log_info "等待后端启动... ($i/$backend_attempts)"
        sleep 2
    done

    if [ "$backend_healthy" = false ]; then
        log_error "后端服务器启动失败，请检查日志："
        log_error "tail -f $PIDFILE_DIR/backend.log"
        cleanup
        exit 1
    fi

    # 检查前端健康状态
    local frontend_attempts=20
    local frontend_healthy=false

    for ((i=1; i<=frontend_attempts; i++)); do
        # 检查前端进程是否还在运行
        if [ -f "$FRONTEND_PID_FILE" ]; then
            FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
            if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
                log_error "前端进程异常退出，请检查日志："
                log_error "tail -f $PIDFILE_DIR/frontend.log"
                break
            fi
        fi

        if curl -s "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
            log_frontend "前端服务器健康检查通过"
            frontend_healthy=true
            break
        fi
        log_info "等待前端启动... ($i/$frontend_attempts)"
        sleep 3
    done

    if [ "$frontend_healthy" = false ]; then
        log_warning "前端服务器可能需要更多时间启动"
        log_warning "请检查日志: tail -f $PIDFILE_DIR/frontend.log"
        log_warning "或手动访问: http://localhost:$FRONTEND_PORT"
    fi
}

# 显示项目信息
show_project_info() {
    echo ""
    echo "=========================================="
    echo "🚀 五好伴学开发环境已启动"
    echo "=========================================="
    echo "📁 项目目录: $(pwd)"
    echo "🐍 Python: $(python --version 2>/dev/null || echo '未激活')"
    echo "🔧 Node.js: $(node --version)"
    echo "📦 包管理器: $PACKAGE_MANAGER"
    echo ""
    echo "🖥️  前端服务:"
    echo "  - 本地访问: http://localhost:$FRONTEND_PORT"
    echo "  - 网络访问: http://$(ifconfig | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' 2>/dev/null || echo '127.0.0.1'):$FRONTEND_PORT"
    echo "  - 前端日志: tail -f $PIDFILE_DIR/frontend.log"
    echo ""
    echo "🔧 后端服务:"
    echo "  - API 地址: http://localhost:$BACKEND_PORT"
    echo "  - API 文档: http://localhost:$BACKEND_PORT/docs"
    echo "  - 健康检查: http://localhost:$BACKEND_PORT/health"
    echo "  - 后端日志: tail -f $PIDFILE_DIR/backend.log"
    echo ""
    echo "📝 日志文件:"
    echo "  - 前端日志: $PIDFILE_DIR/frontend.log"
    echo "  - 后端日志: $PIDFILE_DIR/backend.log"
    echo ""
    echo "=========================================="
    echo ""
    echo "💡 开发提示:"
    echo "  - 修改代码会自动热重载"
    echo "  - 按 Ctrl+C 停止所有服务器"
    echo "  - 运行 './scripts/stop-dev.sh' 手动停止服务"
    echo "  - 查看日志: tail -f $PIDFILE_DIR/*.log"
    echo ""
}

# 监控服务状态
monitor_services() {
    log_info "监控服务状态中... (按 Ctrl+C 停止)"

    while true; do
        # 检查后端服务
        if [ -f "$BACKEND_PID_FILE" ]; then
            BACKEND_PID=$(cat "$BACKEND_PID_FILE")
            if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
                log_error "后端服务器异常停止"
                cleanup
                exit 1
            fi
        fi

        # 检查前端服务
        if [ -f "$FRONTEND_PID_FILE" ]; then
            FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
            if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
                log_error "前端服务器异常停止"
                cleanup
                exit 1
            fi
        fi

        sleep 5
    done
}

# 主函数
main() {
    echo ""
    echo "🎯 启动五好伴学开发环境..."
    echo ""

    # 执行检查和启动流程
    check_project_root
    check_python_env
    check_node_env
    check_package_manager
    install_frontend_dependencies

    # 启动服务器
    start_backend_server
    start_frontend_server

    # 健康检查
    health_check

    # 显示项目信息
    show_project_info

    # 监控服务状态
    monitor_services
}

# 捕获中断信号
trap cleanup INT TERM

# 运行主函数
main "$@"
