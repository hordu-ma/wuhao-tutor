# 🚀 Coding Agent 委派快速指南

> **适用场景**: 使用 GitHub Copilot "Delegate to Coding Agent" 功能执行开发任务  
> **文档版本**: v1.0  
> **更新时间**: 2025-10-12

---

## 📋 委派前准备

### 1. 确认环境

```bash
# 进入项目目录
cd ~/my-devs/python/wuhao-tutor

# 确认 Git 状态干净
git status

# 确认依赖已安装
uv sync

# 确认数据库连接正常
uv run python -c "from src.core.database import get_db; print('✅ 数据库连接正常')"
```

### 2. 阅读任务文档

**Phase 1 任务列表**:

- 📄 [总览文档](./PHASE1-OVERVIEW.md) - 先看这个!
- 📄 [Task 1.1: 数据库设计](./TASK-1.1-DATABASE-DESIGN.md)
- 📄 [Task 1.2: 业务逻辑](./TASK-1.2-MISTAKE-SERVICE.md)

### 3. 选择委派任务

**推荐顺序**:

```
Task 1.1 → Task 1.2 → Task 1.3 → Task 1.4
```

**不要跳过**: 每个 Task 都有前置依赖!

---

## 🤖 如何使用 Coding Agent

### 方法 1: 通过 Chat 面板

1. **打开 GitHub Copilot Chat**

   - 快捷键: `Cmd+I` (macOS) 或 `Ctrl+I` (Windows/Linux)

2. **输入委派指令**

   ```
   @workspace /new task

   请根据文档 docs/tasks/TASK-1.1-DATABASE-DESIGN.md 的要求,
   完成 Task 1.1: 错题数据库设计与迁移。

   具体要求:
   1. 创建 MistakeReview 模型类
   2. 编写 Alembic 迁移脚本
   3. 添加 8 个性能优化索引
   4. 编写单元测试 (覆盖率 >80%)

   请严格按照文档中的验收标准执行。
   ```

3. **Copilot 会分析文档并开始执行**

   - 它会读取现有代码结构
   - 参考 `src/models/base.py` 和 `BaseRepository`
   - 自动创建文件和测试

4. **监控进度**
   - Copilot 会显示当前步骤
   - 可以随时中断或调整

### 方法 2: 通过文件注释

1. **打开目标文件** (或创建新文件)

   ```python
   # src/models/study.py

   # TODO: 添加 MistakeReview 模型类
   # 参考文档: docs/tasks/TASK-1.1-DATABASE-DESIGN.md
   # 要求:
   # - 继承 BaseModel
   # - 包含所有必需字段
   # - 添加外键约束
   ```

2. **触发 Copilot**

   - 输入 `class MistakeReview` 后按 `Tab`
   - Copilot 会根据 TODO 和文档生成代码

3. **逐步验证**
   - 每生成一部分代码就验证一次
   - 运行测试确保正确性

---

## ✅ 委派最佳实践

### DO ✅ 应该做的

1. **提供清晰的上下文**

   ```
   ✅ 好的委派:
   "请根据 docs/tasks/TASK-1.1-DATABASE-DESIGN.md 的第 1.1 节要求,
   在 src/models/study.py 中添加 MistakeReview 模型类。
   参考现有的 MistakeRecord 类 (第 50-189 行)。
   必需字段见文档第 85-105 行。"

   ❌ 不好的委派:
   "做一下错题功能"
   ```

2. **指定输出位置**

   ```
   ✅ 明确:
   "在 src/repositories/ 目录下创建 mistake_repository.py"

   ❌ 模糊:
   "创建 Repository"
   ```

3. **引用具体的文档章节**

   ```
   ✅ 精确:
   "按照 TASK-1.1 文档第 2 节'索引设计'的要求,
   创建 8 个索引,包括 GIN 索引 (仅 PostgreSQL)"

   ❌ 宽泛:
   "添加一些索引"
   ```

4. **分步验证**
   - 每完成一个子任务就运行测试
   - 不要等全部完成再测试
   - 发现问题及时调整

### DON'T ❌ 不应该做的

1. **一次性委派多个任务**

   ```
   ❌ 错误:
   "完成 Task 1.1, 1.2, 1.3"

   ✅ 正确:
   "完成 Task 1.1" → 验收 → "完成 Task 1.2"
   ```

2. **省略重要约束**

   ```
   ❌ 遗漏:
   "创建 MistakeReview 表"

   ✅ 完整:
   "创建 MistakeReview 表,必须支持 SQLite 和 PostgreSQL,
   UUID 字段需要兼容处理,参考 src/models/base.py 第 30-50 行"
   ```

3. **忽略现有代码规范**

   ```
   ❌ 忽视规范:
   "写一个 Repository"

   ✅ 遵循规范:
   "创建 MistakeRepository,继承 BaseRepository[MistakeRecord],
   参考 src/repositories/base_repository.py 的泛型模式"
   ```

4. **跳过测试**

   ```
   ❌ 只要实现:
   "实现 MistakeService"

   ✅ 包含测试:
   "实现 MistakeService 和对应的单元测试,
   覆盖率要求 >85%,参考 tests/services/test_learning_service.py"
   ```

---

## 🧪 验收检查流程

### 每个 Task 完成后必须执行:

```bash
# 1. 代码格式检查
uv run black src/ tests/
uv run mypy src/

# 2. 运行单元测试
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# 3. 检查测试覆盖率
# 目标: >85%

# 4. 运行迁移测试 (Task 1.1)
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head

# 5. 手动功能测试
# 根据验收标准逐项检查

# 6. 提交代码
git add <修改的文件>
git commit -m "feat(scope): 描述

- 详细说明
- 测试覆盖率 X%

Refs: TASK-X.X"
```

---

## 📊 进度跟踪

### 使用 GitHub Projects

1. **创建 Task Issue**

   ```markdown
   ### Task 1.1: 错题数据库设计与迁移

   **文档**: [TASK-1.1-DATABASE-DESIGN.md](...)

   **验收标准**:

   - [ ] MistakeReview 模型创建
   - [ ] Alembic 迁移脚本
   - [ ] 8 个索引创建
   - [ ] 单元测试 >80%
   - [ ] 文档完善

   **预估**: 3-4 天
   **开始**: 2025-10-14
   **截止**: 2025-10-18
   ```

2. **每日更新进度**

   - 在 Issue 中添加评论记录每日进展
   - 遇到问题及时标记 `blocked`
   - 完成后添加 `ready for review`

3. **Code Review**
   - 提交 Pull Request
   - 请求 Code Review
   - 根据反馈修改
   - 合并到 main 分支

---

## 🚨 常见问题

### Q1: Coding Agent 生成的代码不符合要求怎么办?

**解决方法**:

1. **明确指出问题**

   ```
   "生成的 MistakeReview 模型缺少 mastery_level 字段,
   请参考文档第 95 行添加该字段,类型为 float,范围 0.0-1.0"
   ```

2. **提供示例代码**

   ```
   "请按照以下格式添加字段:

   mastery_level = Column(
       Numeric(3, 2),
       default=0.0,
       nullable=False,
       comment='掌握度 0.0-1.0'
   )"
   ```

3. **分步骤修正**
   - 先修正结构问题
   - 再优化细节

### Q2: 如何处理 SQLite/PostgreSQL 兼容性?

**参考示例**:

```python
from src.core.config import get_settings

settings = get_settings()
is_sqlite = "sqlite" in str(settings.SQLALCHEMY_DATABASE_URI)

if is_sqlite:
    mistake_id = Column(String(36), ForeignKey(...))
else:
    from sqlalchemy.dialects.postgresql import UUID
    mistake_id = Column(UUID(as_uuid=True), ForeignKey(...))
```

**委派时明确说明**:

```
"创建字段时需要处理数据库兼容性,
SQLite 使用 String(36),PostgreSQL 使用 UUID(as_uuid=True),
参考 src/models/base.py 第 30-50 行的实现模式"
```

### Q3: 测试覆盖率不达标怎么办?

**检查遗漏**:

```bash
# 查看覆盖率报告
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

**补充测试**:

```python
# 重点测试:
# 1. 边界条件 (空值、最大值、最小值)
# 2. 异常路径 (错误输入、数据库异常)
# 3. 业务逻辑 (状态转换、计算逻辑)
```

### Q4: 如何验证遗忘曲线算法正确性?

**测试策略**:

```python
@pytest.mark.parametrize("review_count,expected_interval", [
    (0, 1),    # 第一次: 1 天
    (1, 2),    # 第二次: 2 天
    (2, 4),    # 第三次: 4 天
    (5, 30),   # 第六次: 30 天
])
async def test_ebbinghaus_intervals(review_count, expected_interval):
    next_review, interval = algorithm.calculate_next_review(
        review_count=review_count,
        review_result='correct',
        current_mastery=0.7,
        last_review_date=datetime.now()
    )

    assert interval == expected_interval
```

---

## 📚 参考资源

### 项目文档

- [README.md](../../README.md) - 项目总览
- [DEVELOPMENT_ROADMAP.md](../../DEVELOPMENT_ROADMAP.md) - 开发路线图
- [架构文档](../architecture/overview.md)

### 代码参考

- `src/models/base.py` - BaseModel 定义
- `src/repositories/base_repository.py` - Repository 模式
- `src/services/learning_service.py` - Service 层参考实现
- `tests/services/test_learning_service.py` - 测试参考

### 外部资料

- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [艾宾浩斯遗忘曲线](https://en.wikipedia.org/wiki/Forgetting_curve)
- [SuperMemo 算法](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)

---

## 💡 成功案例

### 示例: 委派 Task 1.1

**输入**:

```
@workspace /new task

请根据 docs/tasks/TASK-1.1-DATABASE-DESIGN.md 完成错题数据库设计。

具体步骤:
1. 在 src/models/study.py 添加 MistakeReview 模型类
   - 参考文档第 1.1 节的字段定义
   - 继承 BaseModel (参考第 50 行的 MistakeRecord)
   - 添加外键约束到 mistake_records 和 users

2. 创建 Alembic 迁移脚本
   - 文件名: YYYYMMDD_add_mistake_reviews_table.py
   - 参考 alembic/versions/8656ac8e3fe6*.py 的结构
   - 必须支持 SQLite 和 PostgreSQL
   - 添加文档要求的 8 个索引

3. 编写单元测试
   - 文件: tests/migrations/test_mistake_reviews_migration.py
   - 测试迁移升级和降级
   - 测试外键约束
   - 测试检查约束

验收标准见文档第 4 节。
```

**预期输出**:

- ✅ 3 个文件创建
- ✅ 代码符合规范
- ✅ 测试全部通过
- ✅ 可以正常 upgrade/downgrade

---

**祝委派顺利! 有问题随时在 GitHub Issues 提问。** 🎉

---

_最后更新: 2025-10-12 | 版本: v1.0_
