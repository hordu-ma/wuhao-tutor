# Task 1.2 Coding Agent 提示词

> **使用时机**: Task 1.1 (数据库设计) 完成并合并到 main 分支后  
> **预估工期**: 5-6 天  
> **优先级**: P0

---

## 📋 执行前检查清单

在委派 Task 1.2 之前,请确认以下条件:

```bash
# 1. 确认 Task 1.1 已完成
git log --oneline | grep "task-1.1"

# 2. 验证 MistakeReview 模型存在
uv run python -c "from src.models.study import MistakeReview; print('✅ 模型可用')"

# 3. 验证数据库迁移成功
uv run alembic current
uv run alembic upgrade head

# 4. 创建新分支
git checkout -b feature/task-1.2-mistake-service

# 5. 确认环境正常
uv run pytest tests/ -v --co  # 列出所有测试
```

**如果以上检查有任何失败,请先解决 Task 1.1 的问题!**

---

## 🎯 正式提示词 (复制使用)

### 版本 A: 详细版 (推荐首次使用)

````
@workspace /newTask Task 1.2: MistakeService 业务逻辑实现

**前置条件**:
✅ Task 1.1 已完成 (MistakeReview 模型和数据库表已创建)

**上下文**:
- 项目: 五好伴学 - 错题手册功能 Phase 1
- 文档: docs/tasks/TASK-1.2-MISTAKE-SERVICE.md
- 工期: 5-6 天
- 优先级: P0

**任务分解**:

### Step 1: 创建 Repository 层 (25%)

#### 1.1 MistakeRepository
文件: src/repositories/mistake_repository.py

要求:
- 继承 BaseRepository[MistakeRecord]
- 参考: src/repositories/base_repository.py (基类实现)
- 必需方法 (文档第 1.1 节):
  * find_by_user() - 查询用户错题列表 (支持分页和筛选)
  * find_due_for_review() - 查询今日需要复习的错题
  * find_by_knowledge_point() - 按知识点查询 (JSON 字段查询)
  * update_mastery_status() - 更新掌握状态
  * get_statistics() - 获取统计数据

技术要点:
- 使用 SQLAlchemy 2.0 异步语法
- JSON 字段查询兼容 SQLite 和 PostgreSQL
- 分页查询返回 (items, total) 元组

#### 1.2 MistakeReviewRepository
文件: src/repositories/mistake_review_repository.py

要求:
- 继承 BaseRepository[MistakeReview]
- 必需方法 (文档第 1.2 节):
  * find_by_mistake() - 查询某错题的复习历史
  * get_latest_review() - 获取最近一次复习
  * calculate_average_mastery() - 计算平均掌握度
  * get_review_streak() - 获取连续复习天数

### Step 2: 实现遗忘曲线算法 (20%)

文件: src/services/algorithms/spaced_repetition.py

要求:
- 类名: SpacedRepetitionAlgorithm
- 核心常量: EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]
- 必需方法 (文档第 2 节):
  * calculate_next_review() - 计算下次复习时间
    - 参数: review_count, review_result, current_mastery, last_review_date
    - 返回: (next_review_date, interval_days)
    - 逻辑:
      * incorrect → 重置为 1 天
      * partial → 重复当前间隔
      * correct → 进入下一间隔
      * 根据 mastery 调整: <0.5 缩短 20%, >0.8 延长 20%

  * calculate_mastery_level() - 计算掌握度
    - 参数: review_history (最近 5 次复习)
    - 返回: 0.0 - 1.0
    - 逻辑: 加权平均,最近的权重更高 [0.4, 0.3, 0.15, 0.1, 0.05]

算法参考: 文档第 2 节的详细代码示例

### Step 3: 完善 MistakeService (35%)

文件: src/services/mistake_service.py (已有框架代码)

当前状态:
- 已有类定义和占位方法
- 需要实现完整业务逻辑

必需实现的方法 (文档第 3.1 节):

1. **get_mistake_list()** - 获取错题列表
   - 支持筛选: subject, mastery_status, search
   - 支持排序: created_at, next_review_at, mastery
   - 分页返回 MistakeListResponse

2. **create_mistake()** - 创建错题
   - 验证请求数据
   - (可选) 调用 AI 分析知识点
   - 初始化 next_review_at = 明天
   - 返回 MistakeDetailResponse

3. **complete_review()** - 完成复习
   - 创建 MistakeReview 记录
   - 调用遗忘曲线算法计算下次复习时间
   - 更新 MistakeRecord 的掌握状态
   - 判断是否已掌握 (mastery >= 0.9)
   - 返回 ReviewCompleteResponse

4. **get_today_review()** - 获取今日复习任务
   - 查询 next_review_at <= now() 且未掌握的错题
   - 返回列表和统计信息

5. **get_statistics()** - 获取统计数据
   - 总数、掌握数、按学科分布、按难度分布
   - 返回 MistakeStatisticsResponse

依赖注入:
```python
def __init__(
    self,
    db: AsyncSession,
    bailian_service: Optional[BailianService] = None
):
    self.db = db
    self.mistake_repo = MistakeRepository(MistakeRecord, db)
    self.review_repo = MistakeReviewRepository(MistakeReview, db)
    self.bailian_service = bailian_service
    self.algorithm = SpacedRepetitionAlgorithm()
````

参考实现: src/services/learning_service.py (现有 Service 层代码)

### Step 4: 定义 Schema (10%)

文件: src/schemas/mistake.py (新建)

要求:

- 使用 Pydantic BaseModel
- 所有 Schema 定义参考文档第 4 节

必需 Schema:

1. CreateMistakeRequest - 创建错题请求
2. ReviewCompleteRequest - 完成复习请求
3. MistakeResponse - 错题响应
4. MistakeDetailResponse - 错题详情响应
5. MistakeListResponse - 错题列表响应
6. ReviewCompleteResponse - 复习完成响应
7. TodayReviewResponse - 今日复习响应
8. MistakeStatisticsResponse - 统计数据响应

验证规则:

- review_result 必须是 'correct', 'incorrect', 'partial'
- confidence_level 范围 1-5
- mastery_level 范围 0.0-1.0

### Step 5: 编写单元测试 (10%)

必需测试文件:

1. **tests/repositories/test_mistake_repository.py**

   - 测试所有 Repository 方法
   - JSON 查询兼容性测试
   - 分页测试

2. **tests/repositories/test_mistake_review_repository.py**

   - 测试复习记录查询
   - 测试掌握度计算

3. **tests/services/test_spaced_repetition.py**

   - 测试算法所有分支
   - 边界条件测试 (review_count=0, mastery=0.0/1.0)
   - 参数化测试 EBBINGHAUS_INTERVALS

4. **tests/services/test_mistake_service.py**

   - 测试所有业务方法
   - 测试完整流程: 创建 → 复习 → 掌握
   - Mock AI 服务测试
   - 异常处理测试

5. **tests/fixtures/mistake_fixtures.py**
   - 提供测试数据 Fixtures
   - test_mistake, test_user, mock_bailian_service

参考:

- tests/services/test_learning_service.py (现有测试)
- 文档第 5 节的详细测试用例

**验收标准**:

- [ ] 2 个 Repository 类完整实现 (共 12 个方法)
- [ ] 遗忘曲线算法实现和测试
- [ ] MistakeService 所有方法实现
- [ ] 8 个 Schema 定义完整
- [ ] 5 个测试文件,覆盖率 >85%
- [ ] 代码通过 black + mypy 检查
- [ ] 所有单元测试通过

**技术约束**:

- Python 3.12+ / SQLAlchemy 2.0 / FastAPI 0.104+
- 异步编程 (async/await)
- 类型注解完整 (mypy strict mode)
- Google 风格 Docstring
- 遵循项目编码规范

**参考文件**:

- src/repositories/base_repository.py - Repository 基类
- src/services/learning_service.py - Service 层参考
- tests/services/test_learning_service.py - 测试参考
- src/schemas/learning.py - Schema 参考

**关键注意事项**:

1. Repository 方法必须使用 SQLAlchemy 2.0 语法 (select().where())
2. JSON 字段查询需要兼容 SQLite 和 PostgreSQL
3. 时间计算使用 timedelta,不要直接加天数
4. 掌握度计算要考虑历史记录为空的情况
5. AI 服务调用失败不应影响主流程

开始执行前请确认:

- [ ] 已阅读完整文档 docs/tasks/TASK-1.2-MISTAKE-SERVICE.md
- [ ] 理解遗忘曲线算法逻辑
- [ ] 理解 Repository 模式和泛型用法
- [ ] 了解异步编程和事务处理
- [ ] 准备好参考现有代码

请告诉我你的执行计划,我会确认后再让你开始实施。

```

---

### 版本 B: 简洁版 (熟悉项目后使用)

```

@workspace /newTask 实现 Task 1.2: MistakeService 业务逻辑

前置条件: Task 1.1 已完成 ✅

按照文档 docs/tasks/TASK-1.2-MISTAKE-SERVICE.md 完成:

**Step 1: Repository 层 (25%)**

- src/repositories/mistake_repository.py
- src/repositories/mistake_review_repository.py
- 继承 BaseRepository,实现文档第 1 节的 12 个方法

**Step 2: 遗忘曲线算法 (20%)**

- src/services/algorithms/spaced_repetition.py
- SpacedRepetitionAlgorithm 类
- 艾宾浩斯间隔 [1,2,4,7,15,30] + 掌握度调整

**Step 3: MistakeService (35%)**

- src/services/mistake_service.py (完善现有代码)
- 实现 5 个核心方法: get_list, create, complete_review, today_review, statistics
- 集成 Repository + 算法 + AI 服务 (可选)

**Step 4: Schema (10%)**

- src/schemas/mistake.py
- 8 个 Pydantic Schema,完整验证规则

**Step 5: 单元测试 (10%)**

- tests/repositories/test_mistake\*.py
- tests/services/test_spaced_repetition.py
- tests/services/test_mistake_service.py
- tests/fixtures/mistake_fixtures.py
- 覆盖率 >85%

参考: src/services/learning_service.py, tests/services/test_learning_service.py

验收: 所有测试通过, black + mypy 检查通过

```

---

### 版本 C: 交互式版 (推荐初次合作)

```

@workspace 我需要委派 Task 1.2: MistakeService 业务逻辑实现。

**前提**: Task 1.1 (数据库设计) 已完成并合并

**任务文档**: docs/tasks/TASK-1.2-MISTAKE-SERVICE.md

在开始前,请先:

1. 阅读任务文档,理解总体架构
2. 检查 src/repositories/base_repository.py 了解 Repository 模式
3. 检查 src/services/learning_service.py 了解 Service 层实现
4. 检查 src/models/study.py 确认 MistakeReview 模型可用
5. 确认理解艾宾浩斯遗忘曲线算法

这是一个较复杂的任务,涉及:

- 2 个 Repository 类 (12 个方法)
- 1 个算法类 (遗忘曲线)
- 1 个 Service 类 (5 个核心方法)
- 8 个 Pydantic Schema
- 完整的单元测试 (覆盖率 >85%)

请先告诉我你的执行计划和预估时间,包括:

- 你打算如何拆分这个任务 (比如先做哪个模块)
- 你对遗忘曲线算法的理解
- 你认为哪些部分可能有挑战

我会根据你的反馈调整任务细节。

````

---

## 🎯 选择建议

### 使用场景对照表

| 提示词版本 | 适用场景 | 优点 | 缺点 |
|-----------|---------|------|------|
| **版本 A: 详细版** | 首次使用 Coding Agent | 上下文完整,易于理解 | 较长,可能超出 token 限制 |
| **版本 B: 简洁版** | 已完成 Task 1.1,熟悉项目 | 简洁高效,快速委派 | 需要 Agent 自行查阅文档 |
| **版本 C: 交互式** | 复杂任务,希望分步确认 | 可调整,降低风险 | 需要多轮对话 |

### 我的推荐

**首次使用**: 版本 A (详细版)
- 上下文最完整
- 减少理解偏差
- 成功率最高

**后续使用**: 版本 B (简洁版)
- 已有 Task 1.1 经验
- Agent 熟悉项目结构
- 效率更高

---

## 📝 执行后验收流程

```bash
# 1. 代码格式检查
uv run black src/ tests/
uv run mypy src/ --strict

# 2. 运行单元测试
uv run pytest tests/repositories/ -v --cov=src/repositories
uv run pytest tests/services/ -v --cov=src/services

# 3. 检查覆盖率
uv run pytest tests/ --cov=src --cov-report=term-missing
# 目标: >85%

# 4. 运行特定测试
uv run pytest tests/services/test_spaced_repetition.py -v
uv run pytest tests/services/test_mistake_service.py::TestMistakeService::test_complete_review_correct -v

# 5. 集成测试
uv run pytest tests/ -v -k "mistake"

# 6. 提交代码
git add src/repositories/mistake*.py
git add src/services/algorithms/spaced_repetition.py
git add src/services/mistake_service.py
git add src/schemas/mistake.py
git add tests/

git commit -m "feat(mistake): 实现错题手册核心业务逻辑

- 新增 MistakeRepository 和 MistakeReviewRepository
- 实现艾宾浩斯遗忘曲线算法
- 完整的 CRUD 操作和复习计划生成
- 集成 AI 服务分析知识点 (可选)
- 单元测试覆盖率 87%

Refs: TASK-1.2"
````

---

## 🚨 常见问题预案

### Q1: Repository 方法太多,一次性实现困难?

**建议**: 分批实现

```
第一批: 基础 CRUD (get_by_id, create, update)
第二批: 复杂查询 (find_by_user, find_due_for_review)
第三批: 统计方法 (get_statistics, calculate_average_mastery)
```

### Q2: 遗忘曲线算法逻辑不确定?

**参考**: 文档第 2 节有完整代码示例

```python
# 关键逻辑
if review_result == 'incorrect':
    interval_days = 1  # 重置
elif review_result == 'partial':
    interval_days = EBBINGHAUS_INTERVALS[current_index]  # 重复
else:  # correct
    interval_days = EBBINGHAUS_INTERVALS[next_index]  # 前进

# 根据掌握度调整
if current_mastery < 0.5:
    interval_days *= 0.8
elif current_mastery > 0.8:
    interval_days *= 1.2
```

### Q3: 测试覆盖率不够?

**补充测试**:

- 边界条件: review_count=0, mastery=0.0/1.0
- 异常路径: 数据库异常, AI 服务失败
- 并发场景: 同时复习同一错题

### Q4: AI 服务集成失败?

**降级处理**:

```python
try:
    analysis = await self.bailian_service.chat(...)
    data["knowledge_points"] = analysis["knowledge_points"]
except Exception as e:
    logger.warning(f"AI 分析失败: {e}")
    # 使用默认值,不影响主流程
```

---

**祝开发顺利! 🚀**

---

_最后更新: 2025-10-12 | 版本: v1.0_
