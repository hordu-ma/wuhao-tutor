# Phase 3.2 进度报告 - 集成测试编写

> **开始时间**: 2025-11-05  
> **目前状态**: 框架设计完成，测试文件已创建，遇到 SQLAlchemy 异步问题  
> **进度**: 约 60% 完成（框架和测试用例设计）

---

## 📋 Phase 3.2 任务清单

### ✅ 已完成

- [x] **1. 扩展 conftest.py**
  - 添加了 5 个新的集成测试 fixture
  - `test_user`: 创建真实数据库中的测试用户
  - `test_session`: 创建 ChatSession
  - `test_ask_question_request`: 标准提问请求
  - `test_ask_question_with_images_request`: 包含图片的提问
  - `test_homework_correction_ai_response`: 作业批改 AI 响应
  - `mock_bailian_service_for_integration`: 集成测试用 Mock 服务

- [x] **2. 创建集成测试文件** (`tests/integration/test_ask_question_integration.py`)
  - 739 行完整的集成测试代码
  - 8 个测试类，20+ 个测试用例

- [x] **3. 设计测试架构**
  - TestAskQuestionBasic: 基础提问流程 (3 个用例)
  - TestAskQuestionWithImages: 图片处理 (1 个用例)
  - TestHomeworkCorrectionScenario: 作业批改 (2 个用例)
  - TestDataConsistency: 数据一致性 (3 个用例)
  - TestPerformanceMetrics: 性能指标 (2 个用例)
  - TestErrorHandling: 错误处理 (2 个用例)
  - TestQuestionType: 问题类型 (2 个用例)
  - TestSubjectHandling: 学科处理 (2 个用例)
  - TestTransactionConsistency: 事务一致性 (1 个用例)

### ⚠️ 当前遇到的问题

**问题 1: SQLAlchemy MissingGreenlet 异常**

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; 
can't call await_only() here. Was IO attempted in an unexpected place?
```

**症状**: 在运行集成测试时，`db_session.refresh()` 操作失败

**原因**: SQLAlchemy async 的 ORM 对象刷新在某些上下文中不支持

**当前阶段**: 需要调查和修复

### ❌ 待解决

- [ ] 修复 SQLAlchemy 异步问题
- [ ] 运行所有 20+ 个测试用例并验证通过
- [ ] 验证数据库状态正确性
- [ ] 性能基准测试
- [ ] 文档完善

---

## 🏗️ 集成测试设计总览

### 测试类和覆盖范围

| 测试类 | 测试数 | 覆盖内容 | 状态 |
|--------|--------|---------|------|
| TestAskQuestionBasic | 3 | 基础流程、会话管理、响应字段 | ⏳ 待修复 |
| TestAskQuestionWithImages | 1 | 图片URL处理、AI调用验证 | ⏳ 待修复 |
| TestHomeworkCorrectionScenario | 2 | 作业批改检测、错题创建 | ⏳ 待修复 |
| TestDataConsistency | 3 | 会话统计、关系完整性、多问题 | ⏳ 待修复 |
| TestPerformanceMetrics | 2 | processing_time、tokens_used | ⏳ 待修复 |
| TestErrorHandling | 2 | AI失败、invalid session_id | ⏳ 待修复 |
| TestQuestionType | 2 | concept、problem_solving | ⏳ 待修复 |
| TestSubjectHandling | 2 | math、chinese | ⏳ 待修复 |
| TestTransactionConsistency | 1 | 事务一致性验证 | ⏳ 待修复 |
| **总计** | **18** | **完整流程覆盖** | **⏳ 待修复** |

### 测试覆盖的核心功能

```
ask_question() 完整流程
├── 1. 会话管理
│   ├── 创建新会话
│   ├── 使用现有会话
│   └── 统计更新
│
├── 2. 问题处理
│   ├── 保存问题
│   ├── 图片 URL 处理
│   └── 问题类型验证
│
├── 3. AI 调用
│   ├── 消息构建
│   ├── AI 响应处理
│   └── 错误处理
│
├── 4. 答案保存
│   ├── 创建 Answer 记录
│   ├── 关系完整性
│   └── 性能指标记录
│
├── 5. 作业批改
│   ├── 场景检测
│   ├── AI 批改调用
│   └── 错题创建
│
└── 6. 数据一致性
    ├── 事务完整性
    ├── 关系验证
    └── 性能监控
```

---

## 🔧 已创建的代码

### conftest.py 扩展 (新增 170+ 行)

```python
# 集成测试 Fixture

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    
@pytest.fixture
async def test_session(db_session: AsyncSession, test_user: User) -> ChatSession:
    """创建测试会话"""
    
@pytest.fixture
def test_ask_question_request() -> AskQuestionRequest:
    """标准提问请求"""
    
@pytest.fixture
def test_ask_question_with_images_request() -> AskQuestionRequest:
    """包含图片的提问请求"""
    
@pytest.fixture
def test_simple_ai_response() -> str:
    """简单的 AI 响应"""
    
@pytest.fixture
def test_homework_correction_ai_response() -> str:
    """作业批改的 AI 响应"""
    
@pytest.fixture
def mock_bailian_service_for_integration():
    """用于集成测试的 Mock 服务"""
```

### test_ask_question_integration.py (739 行)

完整的集成测试文件，包含：

1. **导入和设置** (40 行)
   - 必要的模块导入
   - 日志配置

2. **TestAskQuestionBasic** (80 行)
   - `test_ask_question_creates_session_and_question()`
   - `test_ask_question_with_existing_session()`
   - `test_ask_question_response_fields()`

3. **TestAskQuestionWithImages** (50 行)
   - `test_ask_question_with_image_urls()`

4. **TestHomeworkCorrectionScenario** (80 行)
   - `test_homework_correction_full_flow()`
   - `test_homework_correction_creates_mistakes()`

5. **TestDataConsistency** (100 行)
   - `test_session_statistics_updated()`
   - `test_question_answer_relationship()`
   - `test_multiple_questions_in_session()`

6. **TestPerformanceMetrics** (50 行)
   - `test_processing_time_metric()`
   - `test_tokens_used_metric()`

7. **TestErrorHandling** (60 行)
   - `test_ai_service_failure_handling()`
   - `test_invalid_session_id_handling()`

8. **TestQuestionType** (50 行)
   - `test_concept_question_type()`
   - `test_problem_solving_question_type()`

9. **TestSubjectHandling** (50 行)
   - `test_math_subject()`
   - `test_chinese_subject()`

10. **TestTransactionConsistency** (50 行)
    - `test_question_answer_transaction()`

---

## 🐛 当前问题分析

### SQLAlchemy MissingGreenlet 异常

**根本原因**: 

SQLAlchemy 2.x 的异步 ORM 在刷新对象时需要在正确的异步上下文中。`db_session.refresh()` 操作在某些情况下会失败。

**尝试的解决方案**:

1. **使用 `expire_on_commit=False`** ✅ 已在 fixture 中配置
2. **避免刷新相关对象** ❌ 但学习服务中的代码需要刷新
3. **改用查询而非刷新** ✅ 可能的解决方案

**建议的修复方向**:

```python
# 选项 1: 改用 SELECT 查询替代 refresh
# 而不是:
await db_session.refresh(question)
# 使用:
stmt = select(Question).where(Question.id == question.id)
result = await db_session.execute(stmt)
question = result.scalar_one()

# 选项 2: 确保在事务内部进行刷新
async with db_session.begin():
    # ... 操作 ...
    await db_session.refresh(question)

# 选项 3: 在学习服务中使用 select 而非 refresh
```

---

## 📊 测试用例详解

### 基础提问流程测试

```python
async def test_ask_question_creates_session_and_question():
    """验证新提问创建会话、问题、答案"""
    # 验证点:
    # 1. 响应包含所有必要字段
    # 2. 会话被创建并关联用户
    # 3. 问题被保存到数据库
    # 4. 答案被创建并关联问题
    # 5. 会话统计正确更新
```

### 会话管理测试

```python
async def test_ask_question_with_existing_session():
    """验证继续现有会话"""
    # 验证点:
    # 1. 新问题关联到现有会话
    # 2. 会话问题计数增加
    # 3. 会话主题保持一致
```

### 作业批改测试

```python
async def test_homework_correction_full_flow():
    """验证作业批改的完整流程"""
    # 验证点:
    # 1. 检测到作业批改场景（HOMEWORK_HELP + 图片）
    # 2. AI 被正确调用并返回批改结果
    # 3. 错题自动创建
    # 4. 响应包含 correction_result 字段
```

### 数据一致性测试

```python
async def test_question_answer_relationship():
    """验证 Question-Answer 关系完整性"""
    # 验证点:
    # 1. 答案正确关联到问题
    # 2. 数据库中关系一致
    # 3. 一个问题只有一个答案
```

---

## 🚀 下一步行动计划

### 立即 (Priority 1)
1. **修复 SQLAlchemy 异步问题**
   - 选项1: 修改学习服务中的 `refresh()` 调用
   - 选项2: 使用 select 查询替代刷新
   - 选项3: 在事务内部进行操作

2. **运行测试并验证**
   ```bash
   uv run pytest tests/integration/test_ask_question_integration.py -v
   ```

3. **修复任何失败的测试用例**

### 后续 (Priority 2)
- [ ] Phase 3.3 - Prompt 优化与验证 (60 min)
- [ ] Phase 3.4 - 性能与监控 (60 min)
- [ ] 生成测试覆盖率报告

---

## 📈 预期结果

### 成功标准

- ✅ 所有 18+ 个集成测试通过
- ✅ 数据库事务一致性验证通过
- ✅ 性能指标正常记录
- ✅ 错误处理正确
- ✅ 覆盖完整的 ask_question() 流程

### 预期覆盖范围

| 组件 | 覆盖率 | 说明 |
|------|--------|------|
| ask_question() | 100% | 完整流程 |
| 会话管理 | 100% | 新建、继续、统计 |
| 问题处理 | 100% | 保存、类型、学科 |
| AI 调用 | 100% | 消息构建、响应处理 |
| 作业批改 | 100% | 检测、调用、错题创建 |
| 数据一致性 | 100% | 事务、关系、统计 |
| 错误处理 | 80% | 主要场景覆盖 |

---

## 📝 关键代码片段

### Fixture 示例

```python
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户 - 完整的真实数据库操作"""
    user_id = str(uuid4())
    phone = f"1{str(uuid4())[:10]}"  # 模拟手机号
    user = User(
        id=user_id,
        phone=phone,
        password_hash="hashed_password",
        name=f"测试用户_{user_id[:8]}",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

### 测试示例

```python
@pytest.mark.asyncio
async def test_ask_question_creates_session_and_question(
    db_session: AsyncSession,
    test_user,
    test_ask_question_request: AskQuestionRequest,
    mock_bailian_service: MockBailianService,
):
    """测试新提问创建会话和问题"""
    with patch(
        "src.services.learning_service.get_bailian_service",
        return_value=mock_bailian_service,
    ):
        service = LearningService(db_session)
        response = await service.ask_question(
            str(test_user.id), test_ask_question_request
        )
        
        # 验证响应
        assert response.question is not None
        assert response.answer is not None
        assert response.session is not None
        assert response.processing_time > 0
```

---

## 💡 技术要点

### 1. 异步测试管理
- 使用 `@pytest.mark.asyncio` 标记异步测试
- pytest-asyncio 自动处理事件循环

### 2. Mock 服务隔离
- 使用 `patch()` 覆盖 `get_bailian_service()`
- 避免真实 API 调用
- 记录调用参数用于验证

### 3. 数据库事务
- 每个测试使用独立的 in-memory SQLite
- 自动隔离，避免测试间干扰
- 完整的 ACID 特性测试

### 4. 关系验证
- 测试一对一关系 (Question-Answer)
- 测试一对多关系 (Session-Questions)
- 测试外键关系

---

## 🎯 完成标志

✅ Phase 3.2 完成标志:

1. **框架完成** ✅
   - 集成测试文件创建: ✅ `test_ask_question_integration.py` (739 行)
   - Fixture 扩展: ✅ conftest.py (170+ 行新增)
   - 测试用例设计: ✅ 18 个完整用例

2. **测试运行** ⏳
   - 所有用例通过: 待修复 SQLAlchemy 问题
   - 覆盖率达成: 预期 100%
   - 性能基准: 待验证

3. **文档完善** ✅
   - 测试用例文档: ✅ 完整
   - 架构说明: ✅ 完整
   - 故障排查: ✅ 进行中

---

## 🔗 相关文件

- `tests/integration/test_ask_question_integration.py` - 集成测试文件 (739 行)
- `tests/conftest.py` - 测试基础设施 (扩展 170+ 行)
- `PHASE_3_TEST_SUMMARY.md` - Phase 3.1 单元测试总结
- `PHASE_3_QUICK_START.md` - 快速开始指南

---

**生成时间**: 2025-11-05  
**状态**: 框架完成，待解决异步问题  
**进度**: 约 60%（框架和设计）| 总体 Phase 3 进度 85%+  
**下一步**: 修复 SQLAlchemy 异步问题 → 运行测试 → Phase 3.3
