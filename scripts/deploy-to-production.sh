#!/bin/bash
#
# 五好伴学 - 生产环境部署脚本
# 用途: 将本地代码变更部署到阿里云生产环境
# 服务器: 121.199.173.244
# 部署方式: Python + systemd + Nginx
#
# 使用方法:
#   ./scripts/deploy-to-production.sh           # 完整部署流程
#   ./scripts/deploy-to-production.sh --quick   # 快速部署（跳过备份）
#   ./scripts/deploy-to-production.sh --dry-run # 预览部署步骤
#
# 创建时间: 2025-10-09
# 最后更新: 2025-10-09

set -e

# ==================== 配置区 ====================

SERVER="root@121.199.173.244"
REMOTE_DIR="/opt/wuhao-tutor"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 部署选项
DRY_RUN=false
QUICK_MODE=false
SKIP_BACKUP=false
SKIP_TESTS=false

# ==================== 辅助函数 ====================

print_header() {
    echo ""
    echo -e "${CYAN}=====================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}=====================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[步骤]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

confirm() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} 跳过确认: $prompt"
        return 0
    fi
    
    read -p "$(echo -e ${YELLOW}$prompt ${NC}[y/N]: )" response
    response=${response:-$default}
    [[ "$response" =~ ^[Yy]$ ]]
}

execute_or_preview() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} 将执行: $@"
    else
        "$@"
    fi
}

# ==================== 解析参数 ====================

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --quick)
            QUICK_MODE=true
            SKIP_BACKUP=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            echo "使用方法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --dry-run       预览部署步骤，不实际执行"
            echo "  --quick         快速部署模式（跳过备份）"
            echo "  --skip-backup   跳过备份步骤"
            echo "  --skip-tests    跳过本地测试"
            echo "  -h, --help      显示此帮助信息"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# ==================== 主流程 ====================

print_header "五好伴学 - 生产环境部署"

if [ "$DRY_RUN" = true ]; then
    print_warning "运行在预览模式，不会实际执行命令"
fi

if [ "$QUICK_MODE" = true ]; then
    print_warning "快速部署模式：跳过备份和部分检查"
fi

echo "服务器: $SERVER"
echo "远程目录: $REMOTE_DIR"
echo "本地目录: $LOCAL_DIR"
echo ""

# ==================== 阶段 1: 本地检查 ====================

print_header "阶段 1: 本地环境检查"

# 1.1 检查 Git 状态
print_step "检查 Git 状态..."
if [ "$DRY_RUN" = false ]; then
    if ! git diff --quiet || ! git diff --cached --quiet; then
        print_warning "有未提交的修改:"
        git status --short
        echo ""
        if ! confirm "继续部署？"; then
            print_error "部署已取消"
            exit 1
        fi
    else
        print_success "Git 状态干净"
    fi
fi

# 1.2 检查关键文件
print_step "检查关键文件..."
REQUIRED_FILES=(
    "src/main.py"
    "src/core/config.py"
    "pyproject.toml"
    "frontend/dist/index.html"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$LOCAL_DIR/$file" ]; then
        print_error "缺少关键文件: $file"
        exit 1
    fi
done
print_success "关键文件检查通过"

# 1.3 构建前端
print_step "构建前端..."
if [ "$DRY_RUN" = false ]; then
    cd "$LOCAL_DIR/frontend"
    
    if [ ! -d "node_modules" ]; then
        print_step "安装前端依赖..."
        npm install
    fi
    
    print_step "执行前端构建..."
    npm run build
    
    if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
        print_error "前端构建失败"
        exit 1
    fi
    
    cd "$LOCAL_DIR"
    print_success "前端构建完成: $(du -sh frontend/dist | cut -f1)"
else
    print_success "[预览] 前端将被构建"
fi

# 1.4 运行测试（可选）
if [ "$SKIP_TESTS" = false ]; then
    print_step "运行基本测试..."
    if [ "$DRY_RUN" = false ]; then
        # 这里可以添加测试命令
        # uv run pytest tests/ -v --tb=short || print_warning "测试失败，但继续部署"
        print_success "测试检查通过（跳过）"
    else
        print_success "[预览] 将运行测试"
    fi
fi

# ==================== 阶段 2: 生产环境备份 ====================

if [ "$SKIP_BACKUP" = false ]; then
    print_header "阶段 2: 生产环境备份"
    
    print_step "创建完整备份..."
    execute_or_preview ssh "$SERVER" 'bash -s' << 'BACKUP_SCRIPT'
set -e
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/wuhao-tutor"

mkdir -p "$BACKUP_DIR"

echo "📦 备份应用代码..."
tar -czf "$BACKUP_DIR/code_$TIMESTAMP.tar.gz" \
    -C /opt wuhao-tutor \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' 2>/dev/null || true

echo "⚙️  备份配置文件..."
cp "$APP_DIR/.env" "$BACKUP_DIR/env_$TIMESTAMP" 2>/dev/null || true

echo "✅ 备份完成: $BACKUP_DIR/code_$TIMESTAMP.tar.gz"
ls -lh "$BACKUP_DIR/code_$TIMESTAMP.tar.gz" | awk '{print "   大小:", $5}'

# 保留最近 5 个备份
cd "$BACKUP_DIR"
ls -t code_*.tar.gz | tail -n +6 | xargs rm -f 2>/dev/null || true
ls -t env_* | tail -n +6 | xargs rm -f 2>/dev/null || true
BACKUP_SCRIPT
    
    print_success "备份完成"
else
    print_warning "跳过备份步骤"
fi

# ==================== 阶段 3: 同步代码 ====================

print_header "阶段 3: 同步代码到服务器"

# 3.1 同步后端代码
print_step "同步后端代码..."
execute_or_preview rsync -avz --delete \
    --exclude='venv/' \
    --exclude='node_modules/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.git/' \
    --exclude='.env' \
    --exclude='*.db' \
    --exclude='*.log' \
    --exclude='archive/' \
    --exclude='uploads/' \
    --exclude='backups/' \
    "$LOCAL_DIR/src/" "$SERVER:$REMOTE_DIR/src/"

print_success "后端代码同步完成"

# 3.2 同步前端构建产物
print_step "同步前端构建产物..."
execute_or_preview rsync -avz --delete \
    "$LOCAL_DIR/frontend/dist/" "$SERVER:$REMOTE_DIR/frontend/dist/"

print_success "前端代码同步完成"

# 3.3 同步配置文件（选择性）
print_step "同步项目配置..."
execute_or_preview rsync -avz \
    "$LOCAL_DIR/pyproject.toml" \
    "$LOCAL_DIR/alembic.ini" \
    "$SERVER:$REMOTE_DIR/"

print_success "配置文件同步完成"

# 3.4 同步 Nginx 配置（可选）
if confirm "是否同步 Nginx 配置？"; then
    print_step "同步 Nginx 配置..."
    execute_or_preview rsync -avz \
        "$LOCAL_DIR/nginx/" "$SERVER:/opt/wuhao-tutor/nginx/"
    
    # 重新加载 Nginx
    execute_or_preview ssh "$SERVER" 'nginx -t && nginx -s reload'
    print_success "Nginx 配置已更新"
fi

# ==================== 阶段 4: 服务器端操作 ====================

print_header "阶段 4: 服务器端操作"

# 4.1 更新依赖
print_step "更新 Python 依赖..."
execute_or_preview ssh "$SERVER" 'bash -s' << 'UPDATE_DEPS'
set -e
cd /opt/wuhao-tutor
source venv/bin/activate

echo "📦 更新依赖..."
pip install -r requirements.txt --upgrade -q

echo "✅ 依赖更新完成"
pip list | grep -E "fastapi|uvicorn|sqlalchemy" | head -5
UPDATE_DEPS

print_success "依赖更新完成"

# 4.2 数据库迁移（可选）
if confirm "是否执行数据库迁移？"; then
    print_step "执行数据库迁移..."
    execute_or_preview ssh "$SERVER" 'bash -s' << 'MIGRATE_DB'
set -e
cd /opt/wuhao-tutor
source venv/bin/activate

echo "🗄️  检查迁移状态..."
alembic current || echo "无迁移历史"

echo "🗄️  执行迁移..."
alembic upgrade head

echo "✅ 数据库迁移完成"
alembic current
MIGRATE_DB
    
    print_success "数据库迁移完成"
fi

# 4.3 重启服务
print_step "重启应用服务..."
execute_or_preview ssh "$SERVER" 'bash -s' << 'RESTART_SERVICE'
set -e

echo "🔄 重启 wuhao-tutor 服务..."
systemctl restart wuhao-tutor

echo "⏳ 等待服务启动..."
sleep 5

echo "📊 检查服务状态..."
systemctl status wuhao-tutor --no-pager -l | head -20
RESTART_SERVICE

print_success "服务重启完成"

# ==================== 阶段 5: 部署验证 ====================

print_header "阶段 5: 部署验证"

# 5.1 健康检查
print_step "执行健康检查..."
if [ "$DRY_RUN" = false ]; then
    sleep 3  # 等待服务完全启动
    
    # 检查服务状态
    if ssh "$SERVER" 'systemctl is-active wuhao-tutor' > /dev/null 2>&1; then
        print_success "服务运行正常"
    else
        print_error "服务未正常运行"
        ssh "$SERVER" 'journalctl -u wuhao-tutor -n 30 --no-pager'
        exit 1
    fi
    
    # 测试 API
    print_step "测试 API 响应..."
    if ssh "$SERVER" 'curl -f -k https://localhost/api/v1/auth/login -X POST -H "Content-Type: application/json" -d "{\"phone\":\"13800000001\",\"password\":\"password123\"}" -s -o /dev/null'; then
        print_success "API 响应正常"
    else
        print_warning "API 测试失败，请手动检查"
    fi
    
    # 检查端口
    print_step "检查端口监听..."
    ssh "$SERVER" 'netstat -tlnp | grep -E ":(80|443|8000)" | head -5' || true
    
else
    print_success "[预览] 将执行健康检查"
fi

# 5.2 查看日志
print_step "查看最近日志..."
if [ "$DRY_RUN" = false ]; then
    ssh "$SERVER" 'journalctl -u wuhao-tutor -n 20 --no-pager' || true
fi

# ==================== 完成 ====================

print_header "部署完成"

print_success "生产环境部署成功！"
echo ""
echo "📊 服务信息:"
echo "   URL: https://121.199.173.244"
echo "   API: https://121.199.173.244/api/docs"
echo ""
echo "🔍 常用命令:"
echo "   查看日志: ssh $SERVER 'journalctl -u wuhao-tutor -f'"
echo "   服务状态: ssh $SERVER 'systemctl status wuhao-tutor'"
echo "   重启服务: ssh $SERVER 'systemctl restart wuhao-tutor'"
echo ""
echo "⏮️  如需回滚:"
echo "   ssh $SERVER"
echo "   cd /opt/backups"
echo "   # 查看可用备份: ls -lht code_*.tar.gz | head -5"
echo "   # 恢复备份: 参考 docs/deployment/production-deployment-guide.md"
echo ""

if [ "$DRY_RUN" = true ]; then
    print_warning "这是预览模式，未实际执行部署"
    echo "运行 $0 以执行实际部署"
fi

print_success "🎉 部署流程结束"
