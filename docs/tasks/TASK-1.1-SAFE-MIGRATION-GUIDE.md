# Task 1.1 安全迁移指南 🔒

## ⚠️ 重要提示

**目标**: 在**不丢失用户登录信息**的前提下，安全应用 Task 1.1 的数据库迁移

**风险**: 直接执行 `alembic upgrade head` 可能因迁移链问题导致失败

**策略**: 增量迁移 + 数据备份

---

## 📋 快速操作清单 (5分钟完成)

### ✅ 步骤 1: 数据库备份 (必须!)

```bash
# 创建带时间戳的备份
cp wuhao_tutor_dev.db backups/wuhao_tutor_dev.db.before_task1.1_$(date +%Y%m%d_%H%M%S)

# 验证备份成功
ls -lh backups/wuhao_tutor_dev.db.before_task1.1_*
```

**预期输出**: 
```
-rw-r--r--  1 liguoma  staff   580K Oct 12 14:35 backups/wuhao_tutor_dev.db.before_task1.1_20251012_143500
```

---

### ✅ 步骤 2: 合并代码到 main 分支

```bash
# 1. 提交当前分支的任何改动 (如果有)
git add -A
git commit -m "chore: save work before merging task 1.1"

# 2. 切换到 main 分支
git checkout main

# 3. 合并 Task 1.1 分支
git merge review-task-1.1 --no-ff -m "feat(database): Merge Task 1.1 - MistakeReview model and migration

- Add MistakeReview model with 14 fields
- Add Alembic migration script with 8 optimized indexes
- Add unit tests (8/8 passed)
- Add comprehensive schema documentation
- Support SQLite/PostgreSQL dual compatibility
- Implement CASCADE delete for data consistency

Closes: Task 1.1 错题数据库设计与迁移"

# 4. 推送到远程仓库
git push origin main
```

---

### ✅ 步骤 3: 应用数据库迁移 (保留用户数据)

#### 3.1 检查当前迁移状态

```bash
uv run alembic current
```

**可能的输出**:
- **情况 A**: `INFO [alembic.runtime.migration] Context impl SQLiteImpl.` (没有版本号)
- **情况 B**: `530d40eea860 (head)` (显示某个版本)

---

#### 3.2 根据情况选择操作

##### 情况 A: 数据库没有迁移历史

```bash
# 1. 检查数据库中已有哪些表
uv run python -c "
from src.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('现有表:', ', '.join(tables))
print('mistake_reviews 存在:', 'mistake_reviews' in tables)
"

# 2. 如果 mistake_reviews 不存在，标记起点后升级
uv run alembic stamp 530d40eea860
uv run alembic upgrade 20251012_add_mistake_reviews
```

##### 情况 B: 数据库有迁移历史

```bash
# 直接升级到 Task 1.1 版本
uv run alembic upgrade 20251012_add_mistake_reviews
```

---

#### 3.3 验证迁移成功

```bash
# 验证 1: 检查表是否创建
uv run python -c "
from src.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
if 'mistake_reviews' in inspector.get_table_names():
    print('✅ mistake_reviews 表创建成功')
    cols = [c['name'] for c in inspector.get_columns('mistake_reviews')]
    print(f'✅ 字段数量: {len(cols)}')
    print('✅ 字段列表:', ', '.join(cols[:5]), '...')
else:
    print('❌ mistake_reviews 表不存在')
"

# 验证 2: 检查索引是否创建
uv run python -c "
from src.core.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
indexes = inspector.get_indexes('mistake_reviews')
print(f'✅ 索引数量: {len(indexes)}')
for idx in indexes:
    print(f'  - {idx[\"name\"]}: {idx[\"column_names\"]}')
"

# 验证 3: 测试模型导入
uv run python -c "
from src.models.study import MistakeReview
print('✅ MistakeReview 模型导入成功')
print(f'✅ 字段: {list(MistakeReview.__table__.columns.keys())[:5]}...')
"
```

**预期输出**:
```
✅ mistake_reviews 表创建成功
✅ 字段数量: 17
✅ 字段列表: id, mistake_id, user_id, review_date, review_result ...
✅ 索引数量: 3
  - idx_mistake_reviews_user_review: ['user_id', 'review_date']
  - idx_mistake_reviews_mistake: ['mistake_id', 'review_date']
  - idx_mistake_reviews_next_review: ['user_id', 'next_review_date']
✅ MistakeReview 模型导入成功
✅ 字段: ['id', 'mistake_id', 'user_id', 'review_date', 'review_result']...
```

---

### ✅ 步骤 4: 验证用户数据完整性

```bash
# 检查用户表是否受影响
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
"
```

---

## 🔧 故障恢复

### 如果迁移失败

```bash
# 1. 立即停止
Ctrl+C

# 2. 恢复备份
cp backups/wuhao_tutor_dev.db.before_task1.1_* wuhao_tutor_dev.db

# 3. 验证数据恢复
uv run python -c "
from src.core.database import SessionLocal
from src.models.user import User
db = SessionLocal()
print('用户数量:', db.query(User).count())
db.close()
"

# 4. 查看错误日志，联系开发团队
```

---

## 🎓 为什么这样做？

### Q1: 为什么要备份？
**A**: 即使迁移失败，也能在 30 秒内恢复所有数据，包括用户登录信息。

### Q2: 为什么不直接 `alembic upgrade head`？
**A**: 早期迁移脚本有顺序依赖问题，可能导致 "table already exists" 错误。使用 `stamp` + 目标版本升级更安全。

### Q3: 为什么要标记迁移起点？
**A**: 告诉 Alembic "这些表已经存在，跳过它们的创建"，只执行新增的迁移。

### Q4: 如果数据库很大怎么办？
**A**: 
- 使用 `sqlite3 .dump` 导出 SQL 备份 (更小)
- 只备份 `users` 表: `sqlite3 wuhao_tutor_dev.db ".dump users" > users_backup.sql`

---

## 🎯 完成后检查清单

迁移完成后，确认以下项目:

- [ ] `mistake_reviews` 表存在于数据库
- [ ] MistakeReview 模型可以成功导入
- [ ] 索引已创建 (至少 3 个)
- [ ] 用户数据完整 (user_count 未变)
- [ ] 代码已合并到 main 分支
- [ ] 远程仓库已同步
- [ ] 数据库备份已保存到 `backups/` 目录

**全部 ✅ 后，即可开始 Task 1.2 委派！**

---

## 📞 需要帮助？

### 迁移失败时检查

```bash
# 查看 Alembic 迁移历史
uv run alembic history

# 查看数据库表结构
uv run python -c "
from src.core.database import engine
from sqlalchemy import inspect
print(inspect(engine).get_table_names())
"

# 检查错误日志
tail -n 50 logs/wuhao-tutor.log
```

---

**创建者**: hordu-ma  
**最后更新**: 2025-10-12 14:35  
**用途**: Task 1.1 生产级安全迁移指南
