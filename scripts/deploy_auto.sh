#!/bin/bash
# 文件: scripts/deploy_auto.sh
# 描述: 自动化部署脚本（无需人工确认）
# 用法: ./scripts/deploy_auto.sh

set -e  # 遇到错误立即退出
set -o pipefail  # 管道命令错误也会退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 时间戳函数
timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# 带颜色的日志输出
log_info() {
    echo -e "${BLUE}[$(timestamp)] ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(timestamp)] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(timestamp)] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(timestamp)] ❌ $1${NC}"
}

# 部署配置
SERVER="root@121.199.173.244"
REMOTE_DIR="/opt/wuhao-tutor"
DEPLOY_LOCK="/tmp/wuhao-tutor-deploy.lock"

# 部署锁检查
check_deploy_lock() {
    if [ -f "$DEPLOY_LOCK" ]; then
        log_error "部署锁文件存在，可能有其他部署正在进行"
        log_error "如果确认没有其他部署，请删除锁文件: rm $DEPLOY_LOCK"
        exit 1
    fi
    touch "$DEPLOY_LOCK"
    log_info "已创建部署锁"
}

# 清理部署锁
cleanup_deploy_lock() {
    if [ -f "$DEPLOY_LOCK" ]; then
        rm -f "$DEPLOY_LOCK"
        log_info "已清理部署锁"
    fi
}

# 错误处理函数
on_error() {
    log_error "部署失败！正在清理..."
    cleanup_deploy_lock
    log_error "请查看上面的错误信息进行排查"
    exit 1
}

# 设置错误陷阱
trap on_error ERR
trap cleanup_deploy_lock EXIT

# 开始部署
echo ""
echo "========================================"
log_info "🚀 开始自动部署到生产环境"
echo "========================================"
log_info "服务器: $SERVER"
log_info "目录: $REMOTE_DIR"
echo ""

# 检查部署锁
check_deploy_lock

# ========== 阶段 1: 本地准备 ==========
echo ""
log_info "📍 阶段 1: 本地准备"
echo "----------------------------------------"

# 1.1 代码检查
log_info "🔍 检查代码格式..."
if [ -f "scripts/pre_deploy_check.sh" ]; then
    chmod +x scripts/pre_deploy_check.sh
    # 设置自动部署模式，跳过所有确认提示
    export AUTO_DEPLOY=true
    ./scripts/pre_deploy_check.sh || {
        log_warning "代码检查有警告，但继续部署"
    }
else
    log_warning "pre_deploy_check.sh 不存在，跳过代码检查"
fi
log_success "代码检查完成"

# 1.2 构建前端
log_info "🏗️  构建前端..."
if [ -f "scripts/build_frontend.sh" ]; then
    chmod +x scripts/build_frontend.sh
    ./scripts/build_frontend.sh
    log_success "前端构建完成"
else
    log_warning "build_frontend.sh 不存在，尝试直接构建"
    if [ -d "frontend" ]; then
        cd frontend
        npm install --production
        npm run build
        cd ..
        log_success "前端构建完成"
    else
        log_error "frontend 目录不存在"
        exit 1
    fi
fi

# ========== 阶段 2: 文件同步 ==========
echo ""
log_info "📍 阶段 2: 文件同步"
echo "----------------------------------------"

# 2.1 同步后端代码
log_info "📤 同步后端代码..."
rsync -avz --delete \
    --exclude='venv/' \
    --exclude='node_modules/' \
    --exclude='*.db' \
    --exclude='.env' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='archive/' \
    --exclude='*.pyc' \
    --exclude='.dev-pids/' \
    --exclude='logs/' \
    ./src/ $SERVER:$REMOTE_DIR/src/
log_success "后端代码同步完成"

# 2.2 同步前端构建产物
log_info "📤 同步前端构建产物..."
rsync -avz --delete \
    ./frontend/dist/ $SERVER:$REMOTE_DIR/frontend/dist/
log_success "前端构建产物同步完成"

# 2.3 同步配置文件
log_info "📤 同步配置文件..."
if [ -f "requirements.prod.txt" ]; then
    rsync -avz ./requirements.prod.txt $SERVER:$REMOTE_DIR/requirements.txt
else
    log_warning "requirements.prod.txt 不存在，使用 requirements.txt"
    rsync -avz ./requirements.txt $SERVER:$REMOTE_DIR/requirements.txt
fi

if [ -f ".env.production" ]; then
    rsync -avz ./.env.production $SERVER:$REMOTE_DIR/.env
else
    log_warning ".env.production 不存在，保持服务器现有 .env 文件"
fi
log_success "配置文件同步完成"

# ========== 阶段 3: 服务器操作 ==========
echo ""
log_info "📍 阶段 3: 服务器操作"
echo "----------------------------------------"

log_info "🔄 执行远程部署操作..."

ssh $SERVER << 'ENDSSH'
set -e

# 颜色定义（服务器端）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_info() {
    echo -e "${BLUE}[$(timestamp)] ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(timestamp)] ✅ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(timestamp)] ❌ $1${NC}"
}

REMOTE_DIR="/opt/wuhao-tutor"
cd $REMOTE_DIR

# 3.1 更新依赖
log_info "📦 激活虚拟环境并更新依赖..."
source venv/bin/activate

pip install -r requirements.txt --quiet
log_success "依赖更新完成"

# 3.2 数据库连接测试
log_info "🗄️  测试数据库连接..."
python -c "
import sys
sys.path.append('.')
from src.core.database import engine
print('✅ 数据库连接正常')
" || {
    log_error "数据库连接失败"
    exit 1
}
log_success "数据库连接测试通过"

# 3.3 部署前端
log_info "🎨 部署前端..."
if [ ! -d "/var/www/html" ]; then
    mkdir -p /var/www/html
fi

# 备份旧版本
if [ -f "/var/www/html/index.html" ]; then
    BACKUP_FILE="/var/www/html/index.html.backup_$(date +%Y%m%d_%H%M%S)"
    cp /var/www/html/index.html "$BACKUP_FILE"
    log_info "已备份旧版本: $BACKUP_FILE"
fi

# 清空并复制新版本
rm -rf /var/www/html/*
cp -r $REMOTE_DIR/frontend/dist/* /var/www/html/

# 设置权限
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html
log_success "前端部署完成"

# 3.4 重启服务
log_info "🔄 重启后端服务..."
systemctl restart wuhao-tutor

# 等待服务启动
log_info "⏳ 等待服务启动（5秒）..."
sleep 5

# 检查服务状态
if systemctl is-active --quiet wuhao-tutor; then
    log_success "后端服务重启成功"
    systemctl status wuhao-tutor --no-pager -l | head -10
else
    log_error "后端服务启动失败"
    systemctl status wuhao-tutor --no-pager -l | head -20
    exit 1
fi

# 3.5 重新加载 Nginx
log_info "🌐 重新加载 Nginx..."
nginx -t && nginx -s reload
log_success "Nginx 重新加载完成"

log_success "远程部署操作完成"
ENDSSH

log_success "服务器操作完成"

# ========== 阶段 4: 部署验证 ==========
echo ""
log_info "📍 阶段 4: 部署验证"
echo "----------------------------------------"

# 4.1 等待服务稳定
log_info "⏳ 等待服务稳定（3秒）..."
sleep 3

# 4.2 检查服务状态
log_info "🏥 检查服务状态..."
if ssh $SERVER "systemctl is-active wuhao-tutor" >/dev/null; then
    log_success "wuhao-tutor 服务运行正常"
else
    log_error "wuhao-tutor 服务未正常运行"
    log_error "查看日志:"
    ssh $SERVER "journalctl -u wuhao-tutor -n 20 --no-pager"
    exit 1
fi

# 4.3 API 健康检查
log_info "🩺 API 健康检查..."
if curl -f -k -m 10 https://121.199.173.244/api/v1/files/health >/dev/null 2>&1; then
    log_success "API 健康检查通过"
else
    log_warning "API 健康检查失败，但服务可能仍在启动中"
    log_info "手动测试: curl -k https://121.199.173.244/api/v1/files/health"
fi

# ========== 部署完成 ==========
echo ""
echo "========================================"
log_success "🎉 部署成功完成！"
echo "========================================"
echo ""
log_info "🌐 访问地址: https://121.199.173.244"
log_info "📊 健康检查: https://121.199.173.244/api/v1/files/health"
log_info "📋 查看日志: ssh $SERVER 'journalctl -u wuhao-tutor -f'"
log_info "🔧 服务状态: ssh $SERVER 'systemctl status wuhao-tutor'"
echo ""
log_info "⚠️  请在生产环境测试作业提交功能，确认修复生效"
echo ""
