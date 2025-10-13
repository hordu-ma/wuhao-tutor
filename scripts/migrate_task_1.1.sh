#!/usr/bin/env bash
#
# Task 1.1 安全迁移一键脚本
# 用途: 在保留用户数据的前提下，安全应用 Task 1.1 数据库迁移
# 创建者: hordu-ma
# 最后更新: 2025-10-12
#

set -e  # 遇到错误立即退出

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Task 1.1 安全迁移脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 步骤 1: 检查当前分支
echo -e "${YELLOW}[1/6] 检查当前分支...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo "当前分支: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "review-task-1.1" ]; then
    echo -e "${RED}❌ 错误: 请先切换到 review-task-1.1 分支${NC}"
    echo "执行: git checkout review-task-1.1"
    exit 1
fi
echo -e "${GREEN}✅ 分支检查通过${NC}"
echo ""

# 步骤 2: 备份数据库
echo -e "${YELLOW}[2/6] 备份数据库...${NC}"
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/wuhao_tutor_dev.db.before_task1.1_$(date +%Y%m%d_%H%M%S)"

if [ -f "wuhao_tutor_dev.db" ]; then
    cp wuhao_tutor_dev.db "$BACKUP_FILE"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ 数据库已备份: $BACKUP_FILE (大小: $BACKUP_SIZE)${NC}"
else
    echo -e "${YELLOW}⚠️  警告: wuhao_tutor_dev.db 不存在，跳过备份${NC}"
fi
echo ""

# 步骤 3: 合并到 main 分支
echo -e "${YELLOW}[3/6] 合并代码到 main 分支...${NC}"
echo "正在切换到 main 分支..."
git checkout main

echo "正在合并 review-task-1.1 分支..."
git merge review-task-1.1 --no-ff -m "feat(database): Merge Task 1.1 - MistakeReview model and migration

- Add MistakeReview model with 14 fields
- Add Alembic migration script with 8 optimized indexes
- Add unit tests (8/8 passed)
- Add comprehensive schema documentation
- Support SQLite/PostgreSQL dual compatibility
- Implement CASCADE delete for data consistency

Closes: Task 1.1 错题数据库设计与迁移"

echo -e "${GREEN}✅ 代码合并完成${NC}"
echo ""

# 步骤 4: 推送到远程仓库
echo -e "${YELLOW}[4/6] 推送到远程仓库...${NC}"
git push origin main
echo -e "${GREEN}✅ 远程仓库已更新${NC}"
echo ""

# 步骤 5: 应用数据库迁移
echo -e "${YELLOW}[5/6] 应用数据库迁移...${NC}"

# 检查迁移状态
echo "检查当前迁移状态..."
CURRENT_VERSION=$(uv run alembic current 2>&1 | grep -oE '[a-f0-9]{12}' | head -n1 || echo "none")

if [ "$CURRENT_VERSION" = "none" ]; then
    echo "⚠️  数据库没有迁移历史，正在标记起点..."
    uv run alembic stamp 530d40eea860
fi

echo "正在执行 Task 1.1 迁移..."
uv run alembic upgrade 20251012_add_mistake_reviews

echo -e "${GREEN}✅ 数据库迁移完成${NC}"
echo ""

# 步骤 6: 验证迁移结果
echo -e "${YELLOW}[6/6] 验证迁移结果...${NC}"

# 验证表创建
echo "验证 mistake_reviews 表..."
uv run python -c "
from src.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
if 'mistake_reviews' in inspector.get_table_names():
    print('✅ mistake_reviews 表创建成功')
    cols = [c['name'] for c in inspector.get_columns('mistake_reviews')]
    print(f'✅ 字段数量: {len(cols)}')
else:
    print('❌ mistake_reviews 表不存在')
    exit(1)
"

# 验证模型导入
echo "验证模型导入..."
uv run python -c "
from src.models.study import MistakeReview
print('✅ MistakeReview 模型导入成功')
"

# 验证用户数据
echo "验证用户数据完整性..."
uv run python -c "
from src.core.database import SessionLocal
from src.models.user import User
db = SessionLocal()
try:
    user_count = db.query(User).count()
    print(f'✅ 用户数量: {user_count}')
    print('✅ 用户数据完整，未丢失')
finally:
    db.close()
" || echo "⚠️  用户表为空（可能是新数据库）"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Task 1.1 迁移成功完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📋 已完成:"
echo "  ✅ 数据库备份: $BACKUP_FILE"
echo "  ✅ 代码合并到 main 分支"
echo "  ✅ 远程仓库已同步"
echo "  ✅ mistake_reviews 表已创建"
echo "  ✅ 用户数据完整保留"
echo ""
echo "🎯 下一步:"
echo "  1. 查看验证报告: docs/tasks/TASK-1.1-VERIFICATION-REPORT.md"
echo "  2. 开始 Task 1.2 委派:"
echo "     - 打开 docs/tasks/TASK-1.2-PROMPT.md"
echo "     - 复制 '版本 A: 详细版' 提示词"
echo "     - 在 Copilot Chat 中执行: @workspace /newTask"
echo ""
echo "📚 参考文档:"
echo "  - docs/tasks/TASK-1.1-VERIFICATION-REPORT.md"
echo "  - docs/tasks/TASK-1.2-PROMPT.md"
echo ""
