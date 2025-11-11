#!/bin/bash
# 五好伴学 - 紧急回滚脚本
# 用途：当生产环境部署出现问题时，快速回滚到上一个稳定版本
# 使用：./scripts/rollback.sh [commit-hash]

set -e

# 配置
SERVER_USER="root"
SERVER_HOST="121.199.173.244"
SERVER_SSH="${SERVER_USER}@${SERVER_HOST}"
BACKEND_REMOTE_DIR="/opt/wuhao-tutor"
BACKEND_SERVICE="wuhao-tutor.service"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 获取回滚目标
ROLLBACK_COMMIT=$1

echo
log_warning "=========================================="
log_warning "⚠️  紧急回滚流程"
log_warning "=========================================="
echo

if [ -z "$ROLLBACK_COMMIT" ]; then
    log_info "未指定回滚目标，将回滚到上一个提交"
    log_info "获取最近提交历史..."
    git log --oneline -n 5
    echo
    read -p "请输入要回滚到的 commit hash (或按 Enter 回滚到上一个提交): " ROLLBACK_COMMIT
    
    if [ -z "$ROLLBACK_COMMIT" ]; then
        ROLLBACK_COMMIT="HEAD~1"
    fi
fi

log_info "回滚目标: ${ROLLBACK_COMMIT}"
echo

# 确认回滚
read -p "确认要回滚吗？这将影响生产环境！(yes/NO): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "已取消回滚"
    exit 0
fi

echo

# ==================== 步骤 1: 数据库回滚 ====================
log_info "步骤 1/4: 数据库回滚"
echo

log_warning "请手动执行数据库回滚（如需要）："
echo "  ssh ${SERVER_SSH}"
echo "  cd ${BACKEND_REMOTE_DIR}"
echo "  source venv/bin/activate"
echo "  alembic downgrade -1  # 回滚一个版本"
echo "  # 或"
echo "  alembic downgrade <revision_id>  # 回滚到指定版本"
echo

read -p "是否已完成数据库回滚（或不需要回滚）？(yes/NO): " DB_DONE

if [ "$DB_DONE" != "yes" ]; then
    log_error "请先完成数据库回滚"
    exit 1
fi

log_success "数据库回滚完成"
echo

# ==================== 步骤 2: 代码回滚 ====================
log_info "步骤 2/4: 代码回滚"
echo

# 在服务器上回滚代码
log_info "在服务器上回滚代码到 ${ROLLBACK_COMMIT}..."

ssh "${SERVER_SSH}" << EOF
    set -e
    cd ${BACKEND_REMOTE_DIR}
    
    # 保存当前状态
    git stash
    
    # 回滚到目标提交
    git reset --hard ${ROLLBACK_COMMIT}
    
    # 更新依赖
    source venv/bin/activate
    pip install -r requirements.prod.txt -q
    
    echo "代码回滚完成"
EOF

log_success "代码回滚完成"
echo

# ==================== 步骤 3: 重启服务 ====================
log_info "步骤 3/4: 重启后端服务"
echo

ssh "${SERVER_SSH}" "systemctl restart ${BACKEND_SERVICE}"
log_success "服务已重启"

# 等待服务启动
log_info "等待服务启动..."
sleep 5

# ==================== 步骤 4: 验证回滚 ====================
log_info "步骤 4/4: 验证回滚结果"
echo

# 检查服务状态
if ssh "${SERVER_SSH}" "systemctl is-active --quiet ${BACKEND_SERVICE}"; then
    log_success "后端服务运行正常"
else
    log_error "后端服务启动失败！"
    log_info "查看日志："
    ssh "${SERVER_SSH}" "journalctl -u ${BACKEND_SERVICE} -n 50"
    exit 1
fi

# 检查健康接口
log_info "检查健康接口..."
if ssh "${SERVER_SSH}" "curl -sf http://localhost:8000/health | grep -q 'healthy'" 2>/dev/null; then
    log_success "健康检查通过"
else
    log_warning "健康检查失败，请手动验证"
fi

echo
log_success "=========================================="
log_success "✅ 回滚完成！"
log_success "=========================================="
echo

log_info "📊 回滚摘要："
echo "  ✓ 代码版本: ${ROLLBACK_COMMIT}"
echo "  ✓ 服务状态: 运行中"
echo

log_info "📋 后续检查："
echo "  1. 测试关键功能: curl https://horsduroot.com/health"
echo "  2. 检查错误日志: ssh ${SERVER_SSH} 'journalctl -u ${BACKEND_SERVICE} -n 100'"
echo "  3. 监控用户反馈"
echo

log_info "💡 恢复到最新版本："
echo "  cd ${BACKEND_REMOTE_DIR}"
echo "  git pull origin main"
echo "  ./scripts/deploy.sh"
echo
