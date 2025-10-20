#!/bin/bash
# 五好伴学 - 生产环境一键部署脚本
# 用途：部署后端 Python 服务和前端 Vue3 应用到阿里云服务器
# 服务器：121.199.173.244 (horsduroot.com)
# 无需交互，适合自动化执行

set -e  # 遇到错误立即退出

# ==================== 配置部分 ====================
SERVER_USER="root"
SERVER_HOST="121.199.173.244"
SERVER_SSH="${SERVER_USER}@${SERVER_HOST}"

# 后端配置
BACKEND_REMOTE_DIR="/opt/wuhao-tutor"
BACKEND_SERVICE="wuhao-tutor.service"

# 前端配置
FRONTEND_REMOTE_DIR="/var/www/html"
FRONTEND_LOCAL_DIR="frontend"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 辅助函数 ====================
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

# ==================== 前置检查 ====================
log_info "开始部署到生产环境: ${SERVER_HOST}"
echo

# 检查 SSH 连接
log_info "检查服务器连接..."
if ! ssh -o ConnectTimeout=5 "${SERVER_SSH}" "echo 'SSH连接成功'" > /dev/null 2>&1; then
    log_error "无法连接到服务器 ${SERVER_HOST}"
    exit 1
fi
log_success "服务器连接正常"
echo

# ==================== 后端部署 ====================
log_info "=== 第1步：部署后端服务 ==="

log_info "同步后端代码..."
rsync -avz --delete \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/dist' \
    --exclude='uploads' \
    --exclude='logs' \
    --exclude='.env' \
    --exclude='miniprogram' \
    src/ alembic/ alembic.ini pyproject.toml requirements.txt \
    "${SERVER_SSH}:${BACKEND_REMOTE_DIR}/"

log_success "后端代码同步完成"

log_info "重启后端服务..."
ssh "${SERVER_SSH}" "systemctl restart ${BACKEND_SERVICE}"
sleep 3

# 检查服务状态
log_info "检查服务状态..."
if ssh "${SERVER_SSH}" "systemctl is-active --quiet ${BACKEND_SERVICE}"; then
    log_success "后端服务运行正常"
else
    log_error "后端服务启动失败"
    ssh "${SERVER_SSH}" "systemctl status ${BACKEND_SERVICE} --no-pager -l | tail -20"
    exit 1
fi
echo

# ==================== 前端部署 ====================
log_info "=== 第2步：部署前端应用 ==="

# 检查前端目录
if [ ! -d "${FRONTEND_LOCAL_DIR}" ]; then
    log_error "前端目录不存在: ${FRONTEND_LOCAL_DIR}"
    exit 1
fi

cd "${FRONTEND_LOCAL_DIR}"

log_info "安装前端依赖..."
if ! npm install --production=false > /dev/null 2>&1; then
    log_warning "npm install 失败，尝试清理缓存..."
    rm -rf node_modules package-lock.json
    npm install --production=false
fi

log_info "构建前端应用..."
npm run build

if [ ! -d "dist" ]; then
    log_error "前端构建失败，dist 目录不存在"
    exit 1
fi

log_success "前端构建完成"

log_info "同步前端文件到服务器..."
rsync -avz --delete \
    dist/ \
    "${SERVER_SSH}:${FRONTEND_REMOTE_DIR}/"

log_success "前端文件同步完成"

cd ..
echo

# ==================== 验证部署 ====================
log_info "=== 第3步：验证部署 ==="

# 检查后端健康状态
log_info "检查后端 API..."
if ssh "${SERVER_SSH}" "curl -s http://localhost:8000/api/v1/health | grep -q 'ok'"; then
    log_success "后端 API 响应正常"
else
    log_warning "后端 API 可能未响应"
fi

# 检查前端文件
log_info "检查前端文件..."
if ssh "${SERVER_SSH}" "[ -f ${FRONTEND_REMOTE_DIR}/index.html ]"; then
    log_success "前端文件部署正常"
else
    log_error "前端 index.html 文件不存在"
    exit 1
fi

echo
log_success "=========================================="
log_success "✅ 部署完成！"
log_success "=========================================="
echo
log_info "访问地址："
echo "  - 前端: https://horsduroot.com"
echo "  - 后端: https://horsduroot.com/api/v1/health"
echo
log_info "查看日志："
echo "  - 后端: ssh ${SERVER_SSH} 'journalctl -u ${BACKEND_SERVICE} -f'"
echo "  - Nginx: ssh ${SERVER_SSH} 'tail -f /var/log/nginx/access.log'"
echo
