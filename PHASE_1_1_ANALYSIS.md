# Phase 1.1 分析结果 - MistakeRecord 模型现状

> **执行时间**: 2025-11-05  
> **任务**: 分析 MistakeRecord 模型是否包含错题本优化所需的 4 个新字段  
> **状态**: ✅ 完成

---

## 📋 检查结果总结

### 关键发现

| 字段名 | 需求 | 当前状态 | 数据类型 | 备注 |
|--------|------|---------|---------|------|
| `question_number` | ✅ 需要 | ❌ 不存在 | Integer | **需新增** |
| `is_unanswered` | ✅ 需要 | ❌ 不存在 | Boolean | **需新增** |
| `question_type` | ✅ 需要 | ❌ 不存在 | String(50) | **需新增** |
| `error_type` | ✅ 需要 | ❌ 不存在 | String(100) | **需新增** |

**结论**: ❌ 4 个新字段都不存在，需要全部新增

---

## 📊 现有字段分析

### MistakeRecord 表当前字段清单

```
基础字段（继承自 BaseModel）:
  - id (UUID/String): 主键
  - created_at (DateTime): 创建时间
  - updated_at (DateTime): 更新时间

用户关联:
  ✅ user_id (UUID/String): 用户ID，已有索引

学科信息:
  ✅ subject (String[20]): 学科
  ✅ chapter (String[100]): 章节

题目内容:
  ✅ title (String[200]): 题目标题
  ✅ image_urls (JSON): 题目图片URL列表
  ✅ ocr_text (Text): OCR识别的文本内容

AI分析结果:
  ✅ ai_feedback (JSON): AI批改和反馈结果
  ✅ knowledge_points (JSON): 涉及的知识点列表
  ✅ error_reasons (JSON): 错误原因分析

题目属性:
  ✅ difficulty_level (Integer[1-5]): 难度等级
  ✅ estimated_time (Integer): 预估解题时间（分钟）

学习状态:
  ✅ mastery_status (String[20]): 掌握状态
  ✅ review_count (Integer): 复习次数
  ✅ correct_count (Integer): 正确次数

时间信息:
  ✅ last_review_at (DateTime): 最后复习时间
  ✅ next_review_at (DateTime): 下次复习时间

元数据:
  ✅ source (String[50]): 来源（learning/homework/manual/upload等）
  ✅ source_question_id (UUID/String): 关联的Question ID
  ✅ student_answer (Text): 学生答案
  ✅ correct_answer (Text): 正确答案
  ✅ tags (JSON): 标签列表
  ✅ notes (Text): 学生备注

关系:
  ✅ user: 关联 User
  ✅ reviews: 关联 MistakeReview
  ✅ review_sessions: 关联 MistakeReviewSession
```

### 现有基础的优势

1. ✅ **已有 `source` 字段** - 可以区分来源（learning/homework等），便于扩展
2. ✅ **已有 `source_question_id` 字段** - 可以关联到学习问答的 Question
3. ✅ **已有 `ai_feedback` 字段** - 可以存储 AI 批改的完整 JSON 结果
4. ✅ **已有 `knowledge_points` 字段** - 可以存储知识点列表
5. ✅ **已有 `student_answer` 和 `correct_answer`** - 可以存储答案对比
6. ✅ **已有 `difficulty_level`** - 支持难度级别
7. ✅ **已有 `error_reasons` 字段** - 可以存储错误原因分析

---

## 🎯 需新增的 4 个字段

### 1. `question_number` (Integer) - 题号

**作用**: 在作业中唯一标识题目位置（从 1 开始）

**字段定义**:
```python
question_number = Column(
    Integer, 
    nullable=True, 
    comment="题号(从1开始，同一作业内唯一递增)"
)
```

**约束条件**:
- nullable=True（向后兼容，旧数据为 NULL）
- 同一错题本内，不需要唯一性（因为一个错题只对应一个题号）
- 取值范围: 1-999（合理上限）

**索引建议**:
- (user_id, question_number) 复合索引 - 便于快速查询用户的某题错题

---

### 2. `is_unanswered` (Boolean) - 是否未作答

**作用**: 标识题目是否为未作答状态

**字段定义**:
```python
is_unanswered = Column(
    Boolean, 
    default=False, 
    nullable=False, 
    comment="是否未作答"
)
```

**语义规则**:
- `is_unanswered=True` → 学生未作答该题
- `is_unanswered=False` → 学生有作答（可能正确或错误）

**逻辑关系**:
- 当 `is_unanswered=True` 时，`student_answer` 应为 None 或空字符串
- 仅在 AI 判断为未作答时设置为 True（作为错题原因之一）

---

### 3. `question_type` (String[50]) - 题目类型

**作用**: 标识题目的类型，便于分类统计和针对性复习

**字段定义**:
```python
question_type = Column(
    String(50), 
    nullable=True, 
    comment="题目类型: 选择题/填空题/解答题/判断题/其他"
)
```

**枚举值（建议）**:
- `选择题` (multiple_choice)
- `填空题` (fill_blank)
- `解答题` (essay)
- `判断题` (true_false)
- `计算题` (calculation)
- `其他` (other)

**获取来源**:
- 从 AI 批改 Prompt 的返回结果中提取
- 在创建错题记录时写入数据库

---

### 4. `error_type` (String[100]) - 错误类型

**作用**: 分类错误原因，用于知识点关联和个性化学习建议

**字段定义**:
```python
error_type = Column(
    String(100), 
    nullable=True, 
    comment="错误类型: 未作答/计算错误/概念错误/审题错误/知识缺陷/粗心错误等"
)
```

**枚举值（建议）**:
- `未作答` (not_answered)
- `计算错误` (calculation_error)
- `概念错误` (concept_error)
- `审题错误` (misreading_error)
- `知识缺陷` (knowledge_gap)
- `粗心错误` (careless_error)
- `推理错误` (reasoning_error)
- `其他` (other)

**获取来源**:
- 从 AI 批改 Prompt 的返回结果中提取 `error_type` 字段
- 在创建错题记录时写入数据库

---

## 🗄️ 迁移策略

### 兼容性设计

所有新字段都设为 `nullable=True` 或有默认值，确保：
- ✅ 现有错题记录不受影响
- ✅ 可以平滑升级生产数据库
- ✅ 旧数据可以查询（字段为 NULL）
- ✅ 新创建的错题数据完整填充

### 建议的迁移脚本模式

```python
def upgrade():
    # 添加 4 个新列
    op.add_column('mistake_records', 
        sa.Column('question_number', sa.Integer(), nullable=True))
    op.add_column('mistake_records', 
        sa.Column('is_unanswered', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('mistake_records', 
        sa.Column('question_type', sa.String(50), nullable=True))
    op.add_column('mistake_records', 
        sa.Column('error_type', sa.String(100), nullable=True))
    
    # 添加复合索引
    op.create_index('ix_mistake_records_user_question', 
        'mistake_records', ['user_id', 'question_number'])

def downgrade():
    op.drop_index('ix_mistake_records_user_question', 'mistake_records')
    op.drop_column('mistake_records', 'error_type')
    op.drop_column('mistake_records', 'question_type')
    op.drop_column('mistake_records', 'is_unanswered')
    op.drop_column('mistake_records', 'question_number')
```

---

## 📝 模型代码更新方案

### 在 `src/models/study.py` 中的 MistakeRecord 类中添加

位置：在 `notes` 字段之后，`__allow_unmapped__` 之前

```python
# 【新增】作业批改相关字段（用于逐题提取）
question_number = Column(
    Integer, 
    nullable=True, 
    index=True,
    comment="题号(从1开始，同一作业内递增)"
)

is_unanswered = Column(
    Boolean, 
    default=False, 
    nullable=False, 
    comment="是否未作答"
)

question_type = Column(
    String(50), 
    nullable=True, 
    comment="题目类型: 选择题/填空题/解答题等"
)

error_type = Column(
    String(100), 
    nullable=True, 
    comment="错误类型: 未作答/计算错误/概念错误等"
)
```

### 索引更新

建议修改 `__table_args__` 以添加复合索引：

```python
__table_args__ = (
    Index('ix_mistake_records_user_question', 'user_id', 'question_number'),
    # 其他现有索引...
)
```

---

## ✅ 验证清单

在执行迁移前，确保：

- [x] 分析了现有 MistakeRecord 的所有字段
- [x] 确认 4 个新字段都不存在
- [x] 理解了每个字段的作用和约束
- [x] 设计了向后兼容的迁移策略
- [x] 准备好了模型代码更新

---

## 🚀 下一步行动

**进入 Phase 1.2**：创建 Alembic 迁移脚本

1. 运行 `alembic revision --autogenerate -m "add_mistake_fields_for_homework_correction"`
2. 手动检查生成的迁移脚本
3. 确保 upgrade() 和 downgrade() 都正确
4. 在本地测试迁移

---

## 📊 对业务的影响

| 方面 | 影响 | 说明 |
|------|------|------|
| 存储 | 低 | 新增 4 个小字段，数据库增长可忽略 |
| 查询 | 中 | 复合索引会提升查询性能 |
| 兼容性 | 低 | 所有字段可空或有默认值，向后兼容 |
| 迁移风险 | 低 | 纯字段新增，无删除或修改 |
| 应用层 | 中 | 需要更新 Service 和 Schema 层逻辑 |

---

**完成时间**: 2025-11-05  
**估计耗时**: ~10 分钟  
**Token 消耗**: 低（~3k tokens）