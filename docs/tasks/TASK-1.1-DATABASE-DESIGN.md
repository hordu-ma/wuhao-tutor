# Task 1.1: 错题手册数据库设计与迁移

> **委派类型**: Coding Agent Task  
> **优先级**: 🔥 P0 (最高)  
> **预估工作量**: 3-4 天  
> **技术难度**: ⭐⭐ (中等)  
> **前置依赖**: 无  
> **输出交付物**: Alembic 迁移脚本 + 索引优化 + 单元测试

---

## 📋 任务概述

为错题手册功能设计完整的数据库表结构,包括 `mistake_reviews` 表的创建和 `mistake_records` 表的优化。需要使用 Alembic 生成迁移脚本,并添加性能优化索引。

### 当前状态

✅ **已完成**:

- `mistake_records` 表已存在 (见 `src/models/study.py` 第 50-189 行)
- 包含基础字段: user_id, subject, knowledge_points, mastery_status 等
- BaseModel 已提供 UUID 主键和时间戳字段

❌ **待实现**:

- `mistake_reviews` 表 (记录每次复习的详细信息)
- 性能优化索引 (复合索引、GIN 索引)
- Alembic 迁移脚本
- 数据库约束和触发器

---

## 🎯 验收标准

### 1. 数据库表设计 ✅

#### 1.1 `mistake_reviews` 表 (新建)

**必需字段**:

```python
class MistakeReview(BaseModel):
    """错题复习记录模型"""
    __tablename__ = "mistake_reviews"

    # 关联字段
    mistake_id: UUID          # 外键关联 mistake_records.id
    user_id: UUID             # 外键关联 users.id (冗余,便于查询)

    # 复习信息
    review_date: DateTime     # 复习时间
    review_result: str        # 复习结果: 'correct' | 'incorrect' | 'partial'
    time_spent: int           # 耗时(秒)
    confidence_level: int     # 信心等级 1-5

    # 掌握度评估
    mastery_level: float      # 掌握度 0.0-1.0
    next_review_date: DateTime  # 计算的下次复习时间
    interval_days: int        # 复习间隔天数

    # 学习记录
    user_answer: Text         # 用户答案(可选)
    notes: Text               # 复习笔记(可选)

    # 元数据
    review_method: str        # 复习方式: 'manual' | 'scheduled' | 'random'
```

**约束要求**:

- `mistake_id` 必须外键约束到 `mistake_records.id`
- `user_id` 必须外键约束到 `users.id`
- `review_result` 只能是: 'correct', 'incorrect', 'partial'
- `confidence_level` 范围: 1-5
- `mastery_level` 范围: 0.0-1.0

#### 1.2 `mistake_records` 表优化 (已存在)

**新增字段**:

```python
# 在现有 MistakeRecord 模型基础上添加
total_review_count: int = 0     # 总复习次数
average_mastery: float = 0.0    # 平均掌握度
last_mastery_update: DateTime   # 最后掌握度更新时间
is_archived: bool = False       # 是否归档
```

**注意**: 不要删除现有字段,只添加新字段!

### 2. 索引设计 ✅

**必需索引**:

```sql
-- mistake_reviews 表索引
CREATE INDEX idx_mistake_reviews_user_review
    ON mistake_reviews(user_id, review_date DESC);

CREATE INDEX idx_mistake_reviews_next_review
    ON mistake_reviews(user_id, next_review_date)
    WHERE next_review_date IS NOT NULL;

CREATE INDEX idx_mistake_reviews_mistake
    ON mistake_reviews(mistake_id, review_date DESC);

-- mistake_records 表优化索引 (新增)
CREATE INDEX idx_mistake_records_user_next_review
    ON mistake_records(user_id, next_review_at)
    WHERE next_review_at IS NOT NULL AND mastery_status != 'mastered';

CREATE INDEX idx_mistake_records_subject_status
    ON mistake_records(user_id, subject, mastery_status);

-- PostgreSQL GIN 索引 (JSON 字段)
CREATE INDEX idx_mistake_records_knowledge_points
    ON mistake_records USING GIN(knowledge_points);

CREATE INDEX idx_mistake_records_tags
    ON mistake_records USING GIN(tags);
```

**索引选择理由**:

- 复合索引覆盖常见查询模式 (用户 + 时间)
- 部分索引减少存储开销 (只索引需要复习的记录)
- GIN 索引支持 JSON 数组查询

### 3. Alembic 迁移脚本 ✅

**文件命名**: `YYYYMMDD_add_mistake_reviews_table.py`

**必需内容**:

```python
"""add mistake reviews table and optimize indexes

Revision ID: <auto_generated>
Revises: <previous_revision>
Create Date: 2025-10-XX XX:XX:XX
"""

def upgrade() -> None:
    # 1. 创建 mistake_reviews 表
    op.create_table(
        'mistake_reviews',
        # ... 所有字段定义
    )

    # 2. 添加外键约束
    op.create_foreign_key(...)

    # 3. 添加所有索引
    op.create_index(...)

    # 4. 添加检查约束
    op.create_check_constraint(
        'ck_review_result',
        'mistake_reviews',
        "review_result IN ('correct', 'incorrect', 'partial')"
    )

    # 5. 为 mistake_records 添加新字段
    op.add_column(
        'mistake_records',
        sa.Column('total_review_count', sa.Integer(), ...)
    )

    # 6. 为 mistake_records 添加新索引
    op.create_index(...)

def downgrade() -> None:
    # 完整回滚逻辑
    op.drop_table('mistake_reviews')
    # ... 删除所有索引和字段
```

**注意事项**:

- 必须兼容 SQLite (开发环境) 和 PostgreSQL (生产环境)
- 使用 `get_settings()` 检测数据库类型
- SQLite 使用 `String(36)` 作为 UUID,PostgreSQL 使用 `UUID(as_uuid=True)`
- GIN 索引仅在 PostgreSQL 中创建

### 4. 单元测试 ✅

**测试文件**: `tests/migrations/test_mistake_reviews_migration.py`

**必需测试用例**:

```python
async def test_upgrade_migration():
    """测试迁移升级"""
    # 1. 验证 mistake_reviews 表创建成功
    # 2. 验证所有字段存在且类型正确
    # 3. 验证外键约束生效
    # 4. 验证索引创建成功

async def test_downgrade_migration():
    """测试迁移回滚"""
    # 1. 执行 downgrade()
    # 2. 验证 mistake_reviews 表删除
    # 3. 验证 mistake_records 新字段删除

async def test_foreign_key_constraints():
    """测试外键约束"""
    # 1. 尝试插入不存在的 mistake_id (应失败)
    # 2. 尝试删除有关联的 mistake_record (应失败或级联)

async def test_check_constraints():
    """测试检查约束"""
    # 1. 尝试插入无效的 review_result (应失败)
    # 2. 尝试插入超出范围的 mastery_level (应失败)

async def test_indexes_performance():
    """测试索引性能"""
    # 1. 插入 1000 条测试数据
    # 2. 查询今日复习列表 (应使用索引,<50ms)
    # 3. EXPLAIN ANALYZE 验证索引命中
```

---

## 📁 项目结构参考

### 需要修改的文件

```
wuhao-tutor/
├── src/models/
│   └── study.py                    # 添加 MistakeReview 模型类
├── alembic/versions/
│   └── YYYYMMDD_add_mistake_reviews_table.py  # 新建迁移脚本
├── tests/migrations/
│   └── test_mistake_reviews_migration.py      # 新建测试文件
└── docs/database/
    └── mistake_reviews_schema.md   # 表结构文档
```

### 现有代码参考

**BaseModel**: `src/models/base.py` 第 22-99 行

- 提供 UUID 主键、created_at、updated_at 等字段
- 继承此类即可自动获取通用字段

**现有迁移示例**: `alembic/versions/8656ac8e3fe6_create_all_missing_tables.py`

- 参考如何处理 SQLite/PostgreSQL 兼容性
- 参考如何创建索引和约束

**MistakeRecord 模型**: `src/models/study.py` 第 50-189 行

- 已有字段不要删除
- 新字段添加在现有字段之后

---

## 🔧 技术要求

### 数据库兼容性

```python
from src.core.config import get_settings

settings = get_settings()
is_sqlite = "sqlite" in str(settings.SQLALCHEMY_DATABASE_URI)

if is_sqlite:
    # SQLite 使用 String(36) 存储 UUID
    mistake_id = Column(String(36), ForeignKey(...))
else:
    # PostgreSQL 使用原生 UUID 类型
    from sqlalchemy.dialects.postgresql import UUID
    mistake_id = Column(UUID(as_uuid=True), ForeignKey(...))
```

### 时间字段处理

```python
# 开发环境 (SQLite) - 使用字符串
review_date = Column(String(50), nullable=False)

# 生产环境 (PostgreSQL) - 使用 DateTime
review_date = Column(DateTime(timezone=True), server_default=func.now())
```

### GIN 索引条件创建

```python
def upgrade() -> None:
    if not is_sqlite:
        # 仅在 PostgreSQL 创建 GIN 索引
        op.execute("""
            CREATE INDEX idx_mistake_records_knowledge_points
            ON mistake_records USING GIN(knowledge_points)
        """)
```

---

## 🧪 测试策略

### 1. 迁移测试

```bash
# 创建测试数据库
uv run alembic upgrade head

# 验证表结构
uv run python -c "from src.models.study import MistakeReview; print(MistakeReview.__table__)"

# 回滚测试
uv run alembic downgrade -1
```

### 2. 性能测试

```python
# 创建性能测试脚本
async def test_review_query_performance():
    # 插入 10,000 条错题记录
    # 插入 100,000 条复习记录

    # 查询今日复习列表 (应 <100ms)
    start = time.time()
    reviews = await db.execute(
        select(MistakeReview)
        .where(
            and_(
                MistakeReview.user_id == user_id,
                MistakeReview.next_review_date <= datetime.now()
            )
        )
        .limit(20)
    )
    elapsed = time.time() - start
    assert elapsed < 0.1  # 100ms
```

### 3. 约束测试

```python
# 测试外键约束
async def test_foreign_key_violation():
    fake_uuid = uuid4()
    with pytest.raises(IntegrityError):
        review = MistakeReview(
            mistake_id=fake_uuid,  # 不存在的 ID
            user_id=user_id,
            review_result='correct'
        )
        db.add(review)
        await db.commit()
```

---

## 📊 验收检查清单

完成以下所有项目才能提交:

- [ ] `MistakeReview` 模型类完整定义 (study.py)
- [ ] Alembic 迁移脚本 upgrade() 函数完整
- [ ] Alembic 迁移脚本 downgrade() 函数完整
- [ ] 8 个索引全部创建 (包括条件索引和 GIN 索引)
- [ ] 外键约束添加 (mistake_id, user_id)
- [ ] 检查约束添加 (review_result, mastery_level)
- [ ] SQLite/PostgreSQL 兼容性处理
- [ ] 4 个单元测试用例全部通过
- [ ] 性能测试通过 (查询 <100ms)
- [ ] 文档完整 (表结构说明 + ER 图)
- [ ] 代码符合项目规范 (Black 格式化, mypy 类型检查)

---

## 🚨 常见陷阱

### 1. UUID 类型不兼容

```python
❌ 错误: 直接使用 UUID 类型
mistake_id = Column(UUID(as_uuid=True), ...)  # SQLite 不支持!

✅ 正确: 根据数据库类型选择
if is_sqlite:
    mistake_id = Column(String(36), ...)
else:
    mistake_id = Column(UUID(as_uuid=True), ...)
```

### 2. 时间字段默认值

```python
❌ 错误: 使用 Python datetime.now()
review_date = Column(DateTime, default=datetime.now)  # 不会自动更新!

✅ 正确: 使用数据库函数
review_date = Column(DateTime, server_default=func.now())
```

### 3. 外键约束缺失

```python
❌ 错误: 只声明字段,不添加约束
mistake_id = Column(UUID(as_uuid=True))

✅ 正确: 显式声明外键
mistake_id = Column(
    UUID(as_uuid=True),
    ForeignKey("mistake_records.id", ondelete="CASCADE")
)
```

### 4. 索引未生效

```python
❌ 错误: 查询条件与索引不匹配
# 索引: (user_id, review_date)
# 查询: WHERE review_date = ? AND user_id = ?  # 顺序错误!

✅ 正确: 查询条件匹配索引顺序
# 查询: WHERE user_id = ? AND review_date = ?
```

---

## 📚 参考资料

- **Alembic 官方文档**: https://alembic.sqlalchemy.org/
- **SQLAlchemy 2.0 文档**: https://docs.sqlalchemy.org/en/20/
- **PostgreSQL 索引优化**: https://www.postgresql.org/docs/current/indexes.html
- **项目现有迁移**: `alembic/versions/8656ac8e3fe6_create_all_missing_tables.py`
- **BaseModel 定义**: `src/models/base.py`

---

## 📝 提交清单

完成后提交以下内容:

```
git add src/models/study.py
git add alembic/versions/YYYYMMDD_add_mistake_reviews_table.py
git add tests/migrations/test_mistake_reviews_migration.py
git add docs/database/mistake_reviews_schema.md

git commit -m "feat(database): 添加错题复习记录表和性能索引

- 新增 MistakeReview 模型类
- 创建 mistake_reviews 表迁移脚本
- 添加 8 个性能优化索引
- 完整的单元测试覆盖
- 支持 SQLite 和 PostgreSQL

Refs: TASK-1.1"
```

---

**预估完成时间**: 3-4 天  
**下一步任务**: Task 1.2 (MistakeService 业务逻辑实现)  
**问题联系**: 项目维护者

---

_最后更新: 2025-10-12 | 版本: v1.0_
