#!/bin/bash
###############################################################################
# 知识图谱历史数据补全 - 生产环境部署脚本
#
# 功能: 在阿里云生产环境执行知识图谱历史数据批量补全
# 
# 使用方法:
#   # 1. 先在本地执行 DRY-RUN 测试
#   ./scripts/deploy_backfill.sh --dry-run
#
#   # 2. 小批量测试（10条）
#   ./scripts/deploy_backfill.sh --test
#
#   # 3. 正式执行（全量）
#   ./scripts/deploy_backfill.sh --production
#
# 作者: 五好伴学开发团队
# 日期: 2025-11-15
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
REMOTE_USER="root"
REMOTE_HOST="121.199.173.244"
PROJECT_DIR="/opt/wuhao-tutor"
BACKUP_DIR="/opt/wuhao-tutor/backups"
PYTHON_BIN="/opt/wuhao-tutor/venv/bin/python3"

# 打印带颜色的日志
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

# 显示帮助信息
show_help() {
    cat << EOF
知识图谱历史数据补全 - 生产环境部署脚本

使用方法:
    $0 [选项]

选项:
    --dry-run       DRY-RUN 模式（仅预览，不实际执行）
    --test          小批量测试模式（10条）
    --production    正式执行模式（全量）
    -h, --help      显示此帮助信息

示例:
    # 1. 先执行 DRY-RUN 测试
    $0 --dry-run

    # 2. 小批量测试
    $0 --test

    # 3. 确认无误后，正式执行
    $0 --production

EOF
}

# 检查参数
if [ $# -eq 0 ]; then
    log_error "缺少参数！"
    show_help
    exit 1
fi

MODE=""
BATCH_SIZE=100

case "$1" in
    --dry-run)
        MODE="dry-run"
        log_info "模式: DRY-RUN (仅预览)"
        ;;
    --test)
        MODE="test"
        BATCH_SIZE=10
        log_info "模式: 小批量测试 (10条)"
        ;;
    --production)
        MODE="production"
        BATCH_SIZE=100
        log_info "模式: 正式执行 (全量)"
        ;;
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        log_error "未知参数: $1"
        show_help
        exit 1
        ;;
esac

echo "==============================================================================="
echo "🚀 知识图谱历史数据批量补全 - 生产环境部署"
echo "==============================================================================="
echo "远程服务器: ${REMOTE_HOST}"
echo "项目目录:   ${PROJECT_DIR}"
echo "执行模式:   ${MODE}"
echo "批次大小:   ${BATCH_SIZE}"
echo "==============================================================================="

# 确认
if [ "$MODE" = "production" ]; then
    log_warning "⚠️  即将在生产环境执行全量数据补全！"
    read -p "确认继续? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "已取消"
        exit 0
    fi
fi

# 步骤1: 上传补全脚本
log_info "📤 步骤1: 上传补全脚本到生产服务器..."
scp scripts/backfill_knowledge_graph.py ${REMOTE_USER}@${REMOTE_HOST}:${PROJECT_DIR}/scripts/

if [ $? -eq 0 ]; then
    log_success "✅ 脚本上传成功"
else
    log_error "❌ 脚本上传失败"
    exit 1
fi

# 步骤2: 执行数据补全
log_info "🔄 步骤2: 执行数据补全..."

if [ "$MODE" = "dry-run" ]; then
    CMD="cd ${PROJECT_DIR} && ENVIRONMENT=production ${PYTHON_BIN} scripts/backfill_knowledge_graph.py --dry-run --batch-size ${BATCH_SIZE}"
else
    CMD="cd ${PROJECT_DIR} && ENVIRONMENT=production ${PYTHON_BIN} scripts/backfill_knowledge_graph.py --batch-size ${BATCH_SIZE}"
fi

ssh ${REMOTE_USER}@${REMOTE_HOST} "$CMD"

if [ $? -eq 0 ]; then
    log_success "✅ 数据补全执行完成"
else
    log_error "❌ 数据补全执行失败"
    exit 1
fi

# 步骤3: 结果总结
echo ""
echo "==============================================================================="
log_success "🎉 部署完成！"
echo "==============================================================================="

if [ "$MODE" = "dry-run" ]; then
    log_info "这是 DRY-RUN 模式的结果，没有实际修改数据"
    log_info "确认无误后，请使用以下命令执行小批量测试:"
    echo ""
    echo "  ./scripts/deploy_backfill.sh --test"
    echo ""
elif [ "$MODE" = "test" ]; then
    log_success "小批量测试完成 (10条)"
    log_info "确认无误后，请使用以下命令执行全量补全:"
    echo ""
    echo "  ./scripts/deploy_backfill.sh --production"
    echo ""
else
    log_success "全量数据补全完成！"
    log_info "建议检查知识图谱显示是否正常"
fi

echo "==============================================================================="
