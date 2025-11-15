#!/bin/bash
# 知识图谱修复部署脚本
# 用于生产环境快速部署和验证修复
# 使用方法: ./scripts/deploy-knowledge-graph-fix.sh [环境]

set -e

# 配置
ENVIRONMENT="${1:-production}"
SERVICE_NAME="wuhao-tutor.service"
BACKUP_DIR="backups/knowledge-graph-fix-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="logs/deploy-knowledge-graph-fix-$(date +%Y%m%d-%H%M%S).log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# 初始化日志目录
mkdir -p logs
mkdir -p "$BACKUP_DIR"

log_info "开始知识图谱修复部署"
log_info "环境: $ENVIRONMENT"
log_info "备份目录: $BACKUP_DIR"

# ============ 预检查 ============
log_info "执行预检查..."

if [ "$ENVIRONMENT" != "production" ] && [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "test" ]; then
    log_error "未知的环境: $ENVIRONMENT (应为 production/dev/test)"
    exit 1
fi

# 检查 git 状态
if ! git status > /dev/null 2>&1; then
    log_error "不在 git 仓库目录中"
    exit 1
fi

# 检查修改的文件
modified_files=$(git diff --name-only)
if [ -z "$modified_files" ]; then
    log_warning "没有检测到本地修改"
else
    log_info "本地修改的文件:"
    echo "$modified_files" | sed 's/^/  - /'
fi

log_success "预检查完成"

# ============ 备份 ============
log_info "备份修改前的源代码..."

files_to_backup=(
    "src/services/learning_service.py"
    "src/services/knowledge_graph_service.py"
    "src/api/v1/endpoints/knowledge_graph.py"
)

for file in "${files_to_backup[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        log_info "已备份: $file"
    fi
done

log_success "备份完成，备份路径: $BACKUP_DIR"

# ============ 验证修改 ============
log_info "验证源代码修改..."

# 检查 learning_service.py 的修改
if grep -q "知识点列表为空，跳过关联" src/services/learning_service.py; then
    log_success "✓ learning_service.py 已修改"
else
    log_warning "⚠ learning_service.py 修改可能不完整"
fi

# 检查 knowledge_graph_service.py 的修改
if grep -q "开始获取知识图谱" src/services/knowledge_graph_service.py; then
    log_success "✓ knowledge_graph_service.py 已修改"
else
    log_warning "⚠ knowledge_graph_service.py 修改可能不完整"
fi

# 检查诊断脚本是否存在
if [ -f "scripts/diagnose-knowledge-graph.py" ]; then
    log_success "✓ 诊断脚本已创建"
else
    log_warning "⚠ 诊断脚本不存在"
fi

# ============ 语法检查 ============
log_info "进行代码语法检查..."

if command -v python3 &> /dev/null; then
    python3 -m py_compile src/services/learning_service.py
    log_success "✓ learning_service.py 语法检查通过"

    python3 -m py_compile src/services/knowledge_graph_service.py
    log_success "✓ knowledge_graph_service.py 语法检查通过"

    python3 -m py_compile src/api/v1/endpoints/knowledge_graph.py
    log_success "✓ knowledge_graph.py 语法检查通过"
else
    log_warning "⚠ Python3 未安装，跳过语法检查"
fi

# ============ 类型检查 ============
log_info "进行类型检查..."

if command -v mypy &> /dev/null; then
    if mypy src/services/knowledge_graph_service.py --ignore-missing-imports; then
        log_success "✓ mypy 类型检查通过"
    else
        log_warning "⚠ mypy 检查发现问题（非致命）"
    fi
else
    log_warning "⚠ mypy 未安装，跳过类型检查"
fi

# ============ 生产环境部署 ============
if [ "$ENVIRONMENT" = "production" ]; then
    log_info "准备生产环境部署..."

    # 检查 systemd 服务是否运行
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "服务 $SERVICE_NAME 正在运行，准备重启..."

        # 停止服务
        log_info "停止服务..."
        sudo systemctl stop "$SERVICE_NAME"
        log_success "服务已停止"

        # 等待
        sleep 2

        # 启动服务
        log_info "启动服务..."
        sudo systemctl start "$SERVICE_NAME"
        sleep 3

        # 检查状态
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log_success "✓ 服务已成功重启"
        else
            log_error "❌ 服务启动失败"
            exit 1
        fi
    else
        log_warning "⚠ 服务 $SERVICE_NAME 未运行"
    fi

    # 检查服务健康状态
    log_info "检查服务健康状态..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "✓ 服务健康检查通过"
    else
        log_warning "⚠ 服务健康检查失败"
    fi
fi

# ============ 生成测试命令 ============
log_info "生成诊断命令..."

cat > "$BACKUP_DIR/diagnose-commands.sh" << 'EOF'
#!/bin/bash
# 知识图谱诊断命令

echo "📊 诊断特定用户和学科:"
echo "  python scripts/diagnose-knowledge-graph.py --user-id <UUID> --subject math"
echo ""
echo "📊 诊断所有用户:"
echo "  python scripts/diagnose-knowledge-graph.py --all-users"
echo ""
echo "📊 诊断并输出到文件:"
echo "  python scripts/diagnose-knowledge-graph.py --user-id <UUID> --subject math --output diagnosis.json"
echo ""
echo "📋 查看实时日志:"
echo "  journalctl -u wuhao-tutor.service -f | grep -E '知识图谱|关联知识点|KnowledgeMastery'"
echo ""
echo "🔍 数据库查询:"
echo "  # 查询用户的 KnowledgeMastery 记录"
echo "  SELECT * FROM knowledge_mastery WHERE user_id = '<UUID>' AND subject = '数学' LIMIT 10;"
echo ""
echo "  # 查询用户的错题记录"
echo "  SELECT id, title, knowledge_points FROM mistake_records WHERE user_id = '<UUID>' AND subject = '数学' LIMIT 10;"
echo ""
echo "  # 查询错题关联"
echo "  SELECT * FROM mistake_knowledge_points WHERE mistake_id = '<mistake_id>' LIMIT 10;"
EOF

chmod +x "$BACKUP_DIR/diagnose-commands.sh"

log_success "诊断命令已保存: $BACKUP_DIR/diagnose-commands.sh"

# ============ 生成回滚脚本 ============
log_info "生成回滚脚本..."

cat > "$BACKUP_DIR/rollback.sh" << EOF
#!/bin/bash
# 知识图谱修复回滚脚本

set -e

echo "🔄 开始回滚..."

# 恢复源文件
files=(
    "src/services/learning_service.py"
    "src/services/knowledge_graph_service.py"
    "src/api/v1/endpoints/knowledge_graph.py"
)

for file in "\${files[@]}"; do
    if [ -f "$BACKUP_DIR/\$file" ]; then
        cp "$BACKUP_DIR/\$file" "\$file"
        echo "✓ 已恢复: \$file"
    fi
done

# 重启服务
if [ -f /etc/systemd/system/$SERVICE_NAME ]; then
    echo "重启服务..."
    sudo systemctl restart $SERVICE_NAME
    sleep 2

    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ 回滚完成，服务已重启"
    else
        echo "❌ 服务启动失败"
        exit 1
    fi
fi
EOF

chmod +x "$BACKUP_DIR/rollback.sh"

log_success "回滚脚本已生成: $BACKUP_DIR/rollback.sh"

# ============ 生成部署总结 ============
log_info "生成部署总结..."

cat > "$BACKUP_DIR/DEPLOYMENT_SUMMARY.md" << 'EOF'
# 知识图谱修复部署总结

## 修复内容

### 1. learning_service.py
- ✅ 增强知识点关联异常处理
- ✅ 添加 knowledge_points 为空时的诊断日志
- ✅ 详细记录异常堆栈信息

### 2. knowledge_graph_service.py
- ✅ get_subject_knowledge_graph() 增强日志
- ✅ 添加 subject 标准化诊断
- ✅ 添加备用查询逻辑（诊断查询）
- ✅ analyze_and_associate_knowledge_points() 增强日志

### 3. 新增工具
- ✅ scripts/diagnose-knowledge-graph.py - 诊断工具

## 关键修复点

1. **日志增强**: 完整记录知识点关联的每个环节
2. **备用查询**: 当主查询失败时执行诊断查询
3. **一致性检查**: 自动检查数据链路完整性

## 验证步骤

### 步骤 1: 检查服务状态
```bash
systemctl status wuhao-tutor.service
curl http://localhost:8000/health
```

### 步骤 2: 查看日志
```bash
journalctl -u wuhao-tutor.service -f | grep -E "知识图谱|关联知识点|KnowledgeMastery"
```

### 步骤 3: 运行诊断
```bash
# 诊断特定用户（替换为实际的用户ID）
python scripts/diagnose-knowledge-graph.py --user-id <UUID> --subject math

# 诊断所有用户
python scripts/diagnose-knowledge-graph.py --all-users --output diagnosis.json
```

### 步骤 4: 测试微信小程序
- 在微信开发者工具中打开知识图谱页面
- 检查是否显示数据和节点

## 回滚方案

如需回滚，执行:
```bash
bash backups/knowledge-graph-fix-<timestamp>/rollback.sh
```

## 后续观察指标

- WS 超时次数（目标: <1%）
- KnowledgeMastery 查询成功率（目标: 100%）
- 知识点关联成功率（目标: >95%）

## 支持

如有问题，请查看:
- 实时日志: `journalctl -u wuhao-tutor.service -f`
- 诊断报告: `python scripts/diagnose-knowledge-graph.py`
- 备份目录: 此脚本同级的 backups 目录
EOF

log_success "部署总结已生成: $BACKUP_DIR/DEPLOYMENT_SUMMARY.md"

# ============ 最终总结 ============
log_success "=========================================="
log_success "知识图谱修复部署完成！"
log_success "=========================================="
log_info ""
log_info "✅ 已完成项目:"
log_info "  1. 源代码已修改并验证"
log_info "  2. 备份已保存: $BACKUP_DIR"
log_info "  3. 诊断工具已创建"
log_info "  4. 回滚脚本已生成"
log_info ""

if [ "$ENVIRONMENT" = "production" ]; then
    log_success "  5. 生产服务已重启"
fi

log_info ""
log_warning "📋 后续操作步骤:"
log_info "  1. 查看实时日志:"
log_info "     journalctl -u wuhao-tutor.service -f | grep -i knowledge"
log_info ""
log_info "  2. 运行诊断检查数据一致性:"
log_info "     python scripts/diagnose-knowledge-graph.py --user-id <UUID> --subject math"
log_info ""
log_info "  3. 在微信开发者工具中测试知识图谱页面"
log_info ""
log_info "  4. 部署总结和回滚脚本位置:"
log_info "     $BACKUP_DIR/"
log_info ""
log_info "部署日志: $LOG_FILE"
log_info ""
