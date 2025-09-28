#!/bin/bash

# 五好伴学前端开发服务器启动脚本
# 启动前端开发环境并进行基本健康检查
# v2.0 - 升级版本，保持向后兼容性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

    log_success "项目结构检查通过"
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
    log_info "检查包管理器..."

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

# 安装依赖
install_dependencies() {
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
        log_success "依赖安装完成"
    else
        log_error "依赖安装失败"
        exit 1
    fi

    cd ..
}

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "端口 $port 已被占用"
        return 1
    else
        return 0
    fi
}

# 查找可用端口
find_available_port() {
    local start_port=5173
    local max_port=5200

    for ((port=$start_port; port<=$max_port; port++)); do
        if check_port $port; then
            echo $port
            return
        fi
    done

    log_error "未找到可用端口 ($start_port-$max_port)"
    exit 1
}

# 启动开发服务器
start_dev_server() {
    log_info "启动前端开发服务器..."

    cd frontend

    # 设置环境变量
    export NODE_ENV=development
    export VITE_API_BASE_URL=http://localhost:8000/api/v1

    # 查找可用端口
    DEV_PORT=$(find_available_port)
    export VITE_DEV_PORT=$DEV_PORT

    log_info "开发服务器将在端口 $DEV_PORT 启动"

    # 启动开发服务器
    case $PACKAGE_MANAGER in
        "pnpm")
            pnpm run dev --port $DEV_PORT --host
            ;;
        "yarn")
            yarn dev --port $DEV_PORT --host
            ;;
        "npm")
            npm run dev -- --port $DEV_PORT --host
            ;;
    esac
}

# 健康检查
health_check() {
    local port=$1
    local max_attempts=30
    local attempt=1

    log_info "等待开发服务器启动..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$port >/dev/null 2>&1; then
            log_success "开发服务器健康检查通过"
            return 0
        fi

        log_info "尝试 $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done

    log_error "开发服务器启动失败或超时"
    return 1
}

# 显示项目信息
show_project_info() {
    echo ""
    echo "======================================"
    echo "🚀 五好伴学前端开发环境"
    echo "======================================"
    echo "📁 项目目录: $(pwd)"
    echo "🔧 Node.js: $(node --version)"
    echo "📦 包管理器: $PACKAGE_MANAGER"
    echo "🌐 本地访问: http://localhost:$DEV_PORT"
    echo "🔗 网络访问: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo '127.0.0.1'):$DEV_PORT"
    echo "🛠️  API 地址: $VITE_API_BASE_URL"
    echo "======================================"
    echo ""
    echo "💡 开发提示:"
    echo "  - 修改代码会自动热重载"
    echo "  - 按 Ctrl+C 停止开发服务器"
    echo "  - 访问 http://localhost:$DEV_PORT 查看应用"
    echo ""
    echo "⚠️  注意:"
    echo "  - 此脚本仅启动前端服务器"
    echo "  - 建议使用 './scripts/start-dev.sh' 启动完整环境"
    echo "  - 后端API可能需要单独启动"
    echo ""
}

# 显示升级提示
show_upgrade_notice() {
    echo ""
    echo "================================================"
    echo "📢 升级提示"
    echo "================================================"
    echo "🎉 新版本开发脚本已可用！"
    echo ""
    echo "✨ 新功能："
    echo "  - 同时启动前端和后端服务器"
    echo "  - 智能端口分配和冲突检测"
    echo "  - 完整的服务生命周期管理"
    echo "  - 详细的状态检查和监控"
    echo ""
    echo "🚀 推荐使用："
    echo "  ./scripts/start-dev.sh     # 启动完整开发环境"
    echo "  ./scripts/status-dev.sh    # 检查服务状态"
    echo "  ./scripts/stop-dev.sh      # 停止所有服务"
    echo ""
    echo "📖 详细文档："
    echo "  查看 scripts/README.md 了解更多信息"
    echo ""
    echo "⏳ 当前脚本将在 10 秒后继续（仅启动前端）..."
    echo "   按 Ctrl+C 取消，或输入 'n' 跳过等待"
    echo "================================================"

    # 等待用户输入或超时
    read -t 10 -p "是否继续使用当前脚本？[Y/n]: " response || response="Y"

    case $response in
        [nN]|[nN][oO])
            echo ""
            echo "🔄 推荐运行新版本脚本："
            echo "  ./scripts/start-dev.sh"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo "📝 继续使用当前脚本（仅前端）..."
            echo ""
            ;;
    esac
}

# 检查是否有新版脚本
check_new_scripts() {
    if [ -f "scripts/start-dev.sh" ] && [ -x "scripts/start-dev.sh" ]; then
        show_upgrade_notice
    fi
}

# 主函数
main() {
    echo ""
    echo "🎯 启动五好伴学前端开发环境..."
    echo ""

    # 检查是否有新版脚本可用
    check_new_scripts

    # 执行检查和启动流程
    check_project_root
    check_node_env
    check_package_manager
    install_dependencies

    # 显示项目信息
    show_project_info

    # 启动开发服务器
    start_dev_server
}

# 捕获中断信号
trap 'log_warning "前端开发服务器已停止"; exit 0' INT TERM

# 运行主函数
main "$@"
