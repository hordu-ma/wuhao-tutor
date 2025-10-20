#!/bin/bash
# 五好伴学 - 生产环境一键部署脚本 v2.0
# 用途：部署后端 Python 服务和前端 Vue3 应用到阿里云服务器
# 服务器：121.199.173.244 (horsduroot.com)
# 特性：自动修复配置、完整验证、无交互执行
# 更新：2025-10-20 - 修复 __init__.py 同步和环境配置问题

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

# 健康检查配置
HEALTH_CHECK_URL="http://localhost:8000/health"
HEALTH_CHECK_TIMEOUT=30

# 颜色代码
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 辅助函数 ====================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查 SSH 连接
check_ssh_connection() {
    log_info "检查 SSH 连接..."
    if ! ssh -o ConnectTimeout=5 "${SERVER_SSH}" "echo 'SSH connection OK'" > /dev/null 2>&1; then
        log_error "无法连接到服务器 ${SERVER_HOST}"
        log_info "请检查："
        echo "  1. 服务器是否在线"
        echo "  2. SSH 密钥是否配置正确"
        echo "  3. 防火墙是否开放 SSH 端口"
        exit 1
    fi
    log_success "SSH 连接正常"
}

# 确保 .env.production 存在
ensure_env_production() {
    log_info "检查环境配置文件..."
    
    if ssh "${SERVER_SSH}" "[ ! -f ${BACKEND_REMOTE_DIR}/.env.production ]"; then
        log_warning ".env.production 不存在，将从 .env 创建"
        
        if ssh "${SERVER_SSH}" "[ -f ${BACKEND_REMOTE_DIR}/.env ]"; then
            ssh "${SERVER_SSH}" "cp ${BACKEND_REMOTE_DIR}/.env ${BACKEND_REMOTE_DIR}/.env.production"
            log_success "已创建 .env.production"
        else
            log_error ".env 和 .env.production 都不存在！"
            log_info "请先在服务器上创建 .env 配置文件"
            exit 1
        fi
    else
        log_success ".env.production 已存在"
    fi
}

# 验证并修复 systemd 配置
validate_systemd_config() {
    log_info "验证 systemd 配置..."
    
    local systemd_config="/etc/systemd/system/${BACKEND_SERVICE}"
    local needs_fix=false
    
    # 检查是否使用了错误的应用路径
    if ssh "${SERVER_SSH}" "grep -q 'src\.main:app' ${systemd_config}" 2>/dev/null; then
        log_warning "检测到错误的应用路径 (src.main:app)，将修复为 main:app"
        ssh "${SERVER_SSH}" "sed -i 's/src\.main:app/main:app/g' ${systemd_config}"
        needs_fix=true
    fi
    
    # 检查是否缺少 PYTHONPATH
    if ! ssh "${SERVER_SSH}" "grep -q 'PYTHONPATH=${BACKEND_REMOTE_DIR}' ${systemd_config}" 2>/dev/null; then
        log_warning "systemd 配置缺少 PYTHONPATH，将添加"
        ssh "${SERVER_SSH}" "sed -i '/^\[Service\]/a Environment=\"PYTHONPATH=${BACKEND_REMOTE_DIR}\"' ${systemd_config}"
        needs_fix=true
    fi
    
    # 检查是否使用了正确的环境文件
    if ! ssh "${SERVER_SSH}" "grep -q 'EnvironmentFile=${BACKEND_REMOTE_DIR}/.env.production' ${systemd_config}" 2>/dev/null; then
        log_warning "systemd 配置未使用 .env.production"
        ssh "${SERVER_SSH}" "sed -i '/^\[Service\]/a EnvironmentFile=${BACKEND_REMOTE_DIR}/.env.production' ${systemd_config}"
        needs_fix=true
    fi
    
    if [ "$needs_fix" = true ]; then
        log_info "重新加载 systemd 配置..."
        ssh "${SERVER_SSH}" "systemctl daemon-reload"
        log_success "systemd 配置已修复"
    else
        log_success "systemd 配置正确"
    fi
}

# 同步 Python 包结构（包括所有 __init__.py）
sync_python_packages() {
    log_info "同步 Python 包结构..."
    
    # 使用 rsync 同步 src 目录，明确包含 __init__.py 文件
    rsync -avz --delete \
        --include='**/__init__.py' \
        --include='**/*.py' \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        src/ "${SERVER_SSH}:${BACKEND_REMOTE_DIR}/src/"
    
    log_success "Python 包结构同步完成"
}

# 同步主要应用文件
sync_main_files() {
    log_info "同步主应用文件..."
    
    # 同步 main.py（从 src/ 复制到根目录）
    # 注意：本地在 src/main.py，生产环境需要在根目录
    rsync -avz src/main.py "${SERVER_SSH}:${BACKEND_REMOTE_DIR}/"
    
    # 同步其他必要文件
    rsync -avz \
        alembic.ini \
        pyproject.toml \
        requirements.txt \
        requirements.prod.txt \
        "${SERVER_SSH}:${BACKEND_REMOTE_DIR}/"
    
    # 同步 alembic 目录
    rsync -avz --delete \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        alembic/ "${SERVER_SSH}:${BACKEND_REMOTE_DIR}/alembic/"
    
    log_success "主应用文件同步完成"
}

# 验证后端部署
verify_backend_deployment() {
    log_info "验证后端部署..."
    
    # 检查关键文件是否存在
    local files_to_check=(
        "main.py"
        "src/__init__.py"
        "src/core/__init__.py"
        ".env.production"
    )
    
    for file in "${files_to_check[@]}"; do
        if ! ssh "${SERVER_SSH}" "[ -f ${BACKEND_REMOTE_DIR}/${file} ]"; then
            log_error "关键文件缺失: ${file}"
            exit 1
        fi
    done
    
    log_success "后端关键文件检查通过"
}

# 等待服务启动
wait_for_service() {
    local max_wait=$HEALTH_CHECK_TIMEOUT
    local elapsed=0
    
    log_info "等待服务启动 (最多 ${max_wait} 秒)..."
    
    while [ $elapsed -lt $max_wait ]; do
        if ssh "${SERVER_SSH}" "curl -sf ${HEALTH_CHECK_URL} > /dev/null 2>&1"; then
            log_success "服务已启动 (${elapsed}s)"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done
    
    echo
    log_warning "服务启动超时，请手动检查"
    return 1
}

# 构建前端
build_frontend() {
    log_info "构建前端应用..."
    
    if [ ! -d "${FRONTEND_LOCAL_DIR}" ]; then
        log_error "前端目录不存在: ${FRONTEND_LOCAL_DIR}"
        exit 1
    fi
    
    cd "${FRONTEND_LOCAL_DIR}"
    
    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi
    
    # 构建
    log_info "执行前端构建..."
    npm run build
    
    if [ ! -d "dist" ]; then
        log_error "前端构建失败，dist 目录不存在"
        exit 1
    fi
    
    cd ..
    log_success "前端构建完成"
}

# ==================== 主流程 ====================

echo
log_info "=========================================="
log_info "🚀 开始部署到生产环境"
log_info "=========================================="
echo

# 1. 预检查
check_ssh_connection

# ==================== 后端部署 ====================
echo
log_info "📦 后端部署阶段"
echo

# 2. 同步 Python 包结构
sync_python_packages

# 3. 同步主要应用文件
sync_main_files

# 4. 确保环境配置正确
ensure_env_production

# 5. 验证并修复 systemd 配置
validate_systemd_config

# 6. 验证部署文件
verify_backend_deployment

# 7. 安装/更新 Python 依赖
log_info "更新 Python 依赖..."
ssh "${SERVER_SSH}" "cd ${BACKEND_REMOTE_DIR} && source venv/bin/activate && pip install -r requirements.prod.txt -q"
log_success "Python 依赖更新完成"

# 8. 执行数据库迁移
log_info "执行数据库迁移..."
if ssh "${SERVER_SSH}" "cd ${BACKEND_REMOTE_DIR} && source venv/bin/activate && alembic upgrade head"; then
    log_success "数据库迁移完成"
else
    log_warning "数据库迁移可能失败，请手动检查"
fi

# 9. 重启后端服务
log_info "重启后端服务..."
ssh "${SERVER_SSH}" "systemctl restart ${BACKEND_SERVICE}"
log_success "后端服务已重启"

# 10. 验证服务状态
log_info "验证服务状态..."
sleep 3  # 给服务一点启动时间

if ssh "${SERVER_SSH}" "systemctl is-active --quiet ${BACKEND_SERVICE}"; then
    log_success "后端服务运行正常"
    
    # 等待健康检查通过
    wait_for_service
else
    log_error "后端服务启动失败"
    log_info "查看日志："
    ssh "${SERVER_SSH}" "journalctl -u ${BACKEND_SERVICE} -n 50"
    exit 1
fi

# ==================== 前端部署 ====================
echo
log_info "🎨 前端部署阶段"
echo

# 11. 构建前端
build_frontend

# 12. 同步前端文件
log_info "同步前端文件到服务器..."
rsync -avz --delete \
    "${FRONTEND_LOCAL_DIR}/dist/" \
    "${SERVER_SSH}:${FRONTEND_REMOTE_DIR}/"
log_success "前端文件同步完成"

# 13. 重启 Nginx
log_info "重启 Nginx..."
ssh "${SERVER_SSH}" "systemctl reload nginx"
log_success "Nginx 已重启"

# ==================== 部署验证 ====================
echo
log_info "🔍 部署验证阶段"
echo

# 14. 检查后端健康状态
log_info "检查后端 API..."
if ssh "${SERVER_SSH}" "curl -sf ${HEALTH_CHECK_URL} | grep -q 'healthy'"; then
    log_success "后端 API 响应正常"
else
    log_warning "后端 API 健康检查失败"
    log_info "手动测试："
    echo "  curl https://horsduroot.com/health"
fi

# 15. 检查前端文件
log_info "检查前端文件..."
if ssh "${SERVER_SSH}" "[ -f ${FRONTEND_REMOTE_DIR}/index.html ]"; then
    log_success "前端文件部署正常"
else
    log_error "前端 index.html 文件不存在"
    exit 1
fi

# 16. 检查 Python 包结构
log_info "检查 Python 包结构..."
init_count=$(ssh "${SERVER_SSH}" "find ${BACKEND_REMOTE_DIR}/src -name '__init__.py' -type f | wc -l")
if [ "$init_count" -gt 0 ]; then
    log_success "Python 包结构正常 (${init_count} 个 __init__.py 文件)"
else
    log_error "Python 包结构异常，缺少 __init__.py 文件"
    exit 1
fi

# ==================== 完成 ====================
echo
log_success "=========================================="
log_success "✅ 部署完成！"
log_success "=========================================="
echo

log_info "📊 部署摘要："
echo "  ✓ 后端服务：运行中"
echo "  ✓ 前端应用：已更新"
echo "  ✓ Python 包：${init_count} 个 __init__.py"
echo "  ✓ 环境配置：.env.production"
echo "  ✓ systemd 配置：已验证"
echo

log_info "🌐 访问地址："
echo "  - 前端: https://horsduroot.com"
echo "  - 后端 API: https://horsduroot.com/api/v1/"
echo "  - 健康检查: https://horsduroot.com/health"
echo

log_info "📋 查看日志："
echo "  - 后端: ssh ${SERVER_SSH} 'journalctl -u ${BACKEND_SERVICE} -f'"
echo "  - Nginx: ssh ${SERVER_SSH} 'tail -f /var/log/nginx/access.log'"
echo

log_info "💡 故障排查："
echo "  - 检查服务状态: ssh ${SERVER_SSH} 'systemctl status ${BACKEND_SERVICE}'"
echo "  - 测试后端 API: curl https://horsduroot.com/health"
echo "  - 查看错误日志: ssh ${SERVER_SSH} 'journalctl -u ${BACKEND_SERVICE} -n 100'"
echo
