# MistakeReview 表结构文档

## 表信息

- **表名**: `mistake_reviews`
- **用途**: 记录每次错题复习的详细信息，包括复习结果、掌握度评估和下次复习计划
- **创建时间**: 2025-10-12
- **迁移脚本**: `alembic/versions/20251012_add_mistake_reviews_table.py`

## 字段定义

### 关联字段

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `mistake_id` | UUID/String(36) | NOT NULL, FK | 关联 `mistake_records.id`，级联删除 |
| `user_id` | UUID/String(36) | NOT NULL, FK | 关联 `users.id`，冗余字段便于查询，级联删除 |

### 复习信息

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `review_date` | DateTime/String(50) | NOT NULL | now() | 复习时间 |
| `review_result` | String(20) | NOT NULL, CHECK | - | 复习结果: 'correct' \| 'incorrect' \| 'partial' |
| `time_spent` | Integer | NULL | - | 耗时（秒） |
| `confidence_level` | Integer | NOT NULL, CHECK | 3 | 信心等级 1-5 |

### 掌握度评估

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `mastery_level` | Numeric(3,2) | NOT NULL, CHECK | 0.0 | 掌握度 0.0-1.0 |
| `next_review_date` | DateTime/String(50) | NULL | - | 计算的下次复习时间 |
| `interval_days` | Integer | NULL | - | 复习间隔天数 |

### 学习记录

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `user_answer` | Text | NULL | - | 用户答案（可选） |
| `notes` | Text | NULL | - | 复习笔记（可选） |

### 元数据

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `review_method` | String(20) | NOT NULL | 'manual' | 复习方式: 'manual' \| 'scheduled' \| 'random' |

### 基础字段（继承自 BaseModel）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | UUID/String(36) | PRIMARY KEY | 主键 |
| `created_at` | DateTime/String(50) | NOT NULL | 创建时间 |
| `updated_at` | DateTime/String(50) | NOT NULL | 更新时间 |

## 约束

### 外键约束

- `mistake_id` → `mistake_records.id` (ON DELETE CASCADE)
- `user_id` → `users.id` (ON DELETE CASCADE)

### 检查约束

1. **ck_review_result**: `review_result IN ('correct', 'incorrect', 'partial')`
2. **ck_confidence_level**: `confidence_level >= 1 AND confidence_level <= 5`
3. **ck_mastery_level**: `mastery_level >= 0.0 AND mastery_level <= 1.0`

## 索引

### 标准索引

1. **idx_mistake_reviews_user_review**: `(user_id, review_date DESC)`
   - 用途: 查询用户的复习历史记录

2. **idx_mistake_reviews_mistake**: `(mistake_id, review_date DESC)`
   - 用途: 查询某道错题的复习历史

### 部分索引（Partial Index）

3. **idx_mistake_reviews_next_review**: `(user_id, next_review_date) WHERE next_review_date IS NOT NULL`
   - 用途: 查询用户待复习的错题列表
   - 优点: 只索引有下次复习时间的记录，减少索引大小

## mistake_records 表新增字段

为了支持错题复习功能，在 `mistake_records` 表中新增以下字段：

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `total_review_count` | Integer | NOT NULL | 0 | 总复习次数 |
| `average_mastery` | Numeric(3,2) | NOT NULL | 0.0 | 平均掌握度 |
| `last_mastery_update` | DateTime/String(50) | NULL | - | 最后掌握度更新时间 |
| `is_archived` | Boolean | NOT NULL | false | 是否归档 |

### mistake_records 新增索引

1. **idx_mistake_records_user_next_review**: `(user_id, next_review_at) WHERE next_review_at IS NOT NULL AND mastery_status != 'mastered'`
   - 用途: 查询需要复习且未掌握的错题

2. **idx_mistake_records_subject_status**: `(user_id, subject, mastery_status)`
   - 用途: 按学科和掌握状态查询错题

3. **idx_mistake_records_knowledge_points** (PostgreSQL only): `USING GIN(knowledge_points)`
   - 用途: 支持 JSON 数组的快速查询

4. **idx_mistake_records_tags** (PostgreSQL only): `USING GIN(tags)`
   - 用途: 支持标签数组的快速查询

## 数据库兼容性

- **SQLite**: 使用 `String(36)` 存储 UUID，`String(50)` 存储时间
- **PostgreSQL**: 使用原生 `UUID` 类型和 `DateTime(timezone=True)`
- **GIN 索引**: 仅在 PostgreSQL 中创建

## 使用示例

### 创建复习记录

```python
from src.models.study import MistakeReview
from datetime import datetime
from uuid import uuid4

review = MistakeReview(
    id=str(uuid4()),
    mistake_id="<mistake_record_id>",
    user_id="<user_id>",
    review_result="correct",
    confidence_level=4,
    mastery_level=0.8,
    time_spent=120,  # 2分钟
    review_method="scheduled"
)
```

### 查询今日待复习错题

```python
from datetime import datetime
from sqlalchemy import select, and_

# 查询用户今日待复习的错题
query = select(MistakeReview).where(
    and_(
        MistakeReview.user_id == user_id,
        MistakeReview.next_review_date <= datetime.now()
    )
).order_by(MistakeReview.next_review_date.asc())
```

## 测试覆盖

- ✅ 表结构创建验证
- ✅ 字段定义验证
- ✅ 外键约束验证
- ✅ 索引创建验证
- ✅ 检查约束验证
- ✅ confidence_level 范围验证
- ✅ mastery_level 范围验证
- ✅ mistake_records 表存在性验证

所有测试通过 (8/8)

## 迁移说明

### 升级迁移

```bash
uv run alembic upgrade head
```

### 回滚迁移

```bash
uv run alembic downgrade -1
```

## ER 图

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────┐
│     users       │       │ mistake_records  │       │mistake_     │
│                 │       │                  │       │  reviews    │
├─────────────────┤       ├──────────────────┤       ├─────────────┤
│ id (PK)         │◄──────┤ user_id (FK)     │◄──────┤mistake_id   │
│ phone           │       │ subject          │       │  (FK)       │
│ password_hash   │       │ mastery_status   │       │user_id (FK) │─┐
│ ...             │       │ review_count     │       │review_result│ │
└─────────────────┘       │ total_review_... │       │mastery_...  │ │
                          │ average_mastery  │       │confidence_..│ │
                          │ is_archived      │       │...          │ │
                          │ ...              │       └─────────────┘ │
                          └──────────────────┘                       │
                                                                     │
                          └──────────────────────────────────────────┘
```

## 注意事项

1. **级联删除**: 删除用户或错题记录时，会自动删除相关的复习记录
2. **冗余字段**: `user_id` 在 `mistake_reviews` 中是冗余字段，便于查询用户的所有复习记录
3. **部分索引**: 仅索引需要的数据，减少存储开销和提高查询性能
4. **GIN 索引**: PostgreSQL 的 GIN 索引支持高效的 JSON 数组查询

## 性能优化建议

1. 定期归档旧的复习记录（如6个月前的记录）
2. 使用分区表存储大量复习记录
3. 监控索引使用情况，及时调整索引策略
4. 考虑使用物化视图缓存统计数据

---

**维护者**: hordu-ma  
**最后更新**: 2025-10-12
