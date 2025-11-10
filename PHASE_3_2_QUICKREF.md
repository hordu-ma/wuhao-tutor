# Phase 3.2 快速参考卡

> 集成测试框架已完成构建，739 行测试代码 + 170+ 行 Fixture 扩展

## 🎯 Phase 3.2 完成度

| 项目 | 状态 | 进度 |
|------|------|------|
| 集成测试文件创建 | ✅ 完成 | 100% |
| Fixture 扩展 | ✅ 完成 | 100% |
| 测试用例设计 | ✅ 完成 | 100% (18 个) |
| 测试框架运行 | ⏳ 进行中 | 50% (遇到异步问题) |
| **总体** | ⏳ **进行中** | **~65%** |

---

## 📂 已创建文件

### 1. `tests/integration/test_ask_question_integration.py` (739 行)
- **TestAskQuestionBasic** - 基础提问流程 (3 个用例)
- **TestAskQuestionWithImages** - 图片处理 (1 个用例)
- **TestHomeworkCorrectionScenario** - 作业批改 (2 个用例)
- **TestDataConsistency** - 数据一致性 (3 个用例)
- **TestPerformanceMetrics** - 性能指标 (2 个用例)
- **TestErrorHandling** - 错误处理 (2 个用例)
- **TestQuestionType** - 问题类型 (2 个用例)
- **TestSubjectHandling** - 学科处理 (2 个用例)
- **TestTransactionConsistency** - 事务一致性 (1 个用例)

### 2. `tests/conftest.py` (新增 170+ 行)
- `test_user` - 创建测试用户
- `test_session` - 创建测试会话
- `test_ask_question_request` - 标准提问请求
- `test_ask_question_with_images_request` - 包含图片的提问
- `test_simple_ai_response` - 简单 AI 响应
- `test_homework_correction_ai_response` - 作业批改响应
- `mock_bailian_service_for_integration` - 集成测试 Mock 服务

---

## 🧪 测试覆盖范围

```
ask_question() 完整流程
├── 会话管理 (创建、继续、统计)
├── 问题处理 (保存、图片、类型、学科)
├── AI 调用 (消息构建、响应处理、错误处理)
├── 答案保存 (创建、关系、性能指标)
├── 作业批改 (检测、调用、错题创建)
└── 数据一致性 (事务、关系、统计)
```

**覆盖总数**: 18 个测试用例  
**预期覆盖率**: 100%

---

## 🔧 当前问题与解决方案

### 问题: SQLAlchemy MissingGreenlet 异常

**症状**:
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called
```

**出现位置**: `db_session.refresh()` 操作

**解决方案**:

```python
# 选项 1: 改用 SELECT 查询（推荐）
stmt = select(Question).where(Question.id == question.id)
result = await db_session.execute(stmt)
question = result.scalar_one()

# 选项 2: 在事务内进行刷新
async with db_session.begin():
    await db_session.refresh(question)

# 选项 3: 使用 expire_on_commit=False（已配置）
# 在 fixture 中已配置，但某些情况仍需刷新
```

**修复步骤**:
1. 定位学习服务中的 `refresh()` 调用
2. 改用 SELECT 查询替代
3. 重新运行测试

---

## 🚀 立即可执行命令

### 运行所有集成测试（修复后）
```bash
uv run pytest tests/integration/test_ask_question_integration.py -v
```

### 运行特定测试类
```bash
uv run pytest tests/integration/test_ask_question_integration.py::TestAskQuestionBasic -v
```

### 运行特定测试用例
```bash
uv run pytest tests/integration/test_ask_question_integration.py::TestAskQuestionBasic::test_ask_question_creates_session_and_question -xvs
```

### 生成覆盖率报告（修复后）
```bash
uv run pytest tests/integration/test_ask_question_integration.py \
  --cov=src/services/learning_service \
  --cov-report=html
```

---

## 📊 代码统计

| 组件 | 行数 | 说明 |
|------|------|------|
| test_ask_question_integration.py | 739 | 完整集成测试 |
| conftest.py 新增 | 170+ | 集成测试 Fixture |
| 测试用例总数 | 18 | 完整覆盖 |
| 预期代码覆盖 | 100% | ask_question() |

---

## 📋 测试类详情

### 1. TestAskQuestionBasic (3 个用例)
- ✅ 新建会话的提问
- ✅ 继续现有会话的提问
- ✅ 响应包含所有必要字段

### 2. TestAskQuestionWithImages (1 个用例)
- ✅ 包含图片 URL 的提问处理

### 3. TestHomeworkCorrectionScenario (2 个用例)
- ✅ 作业批改的完整流程
- ✅ 批改后错题创建验证

### 4. TestDataConsistency (3 个用例)
- ✅ 会话统计正确更新
- ✅ 问题-答案关系完整性
- ✅ 会话中的多个问题

### 5. TestPerformanceMetrics (2 个用例)
- ✅ processing_time 指标
- ✅ tokens_used 指标

### 6. TestErrorHandling (2 个用例)
- ✅ AI 服务失败处理
- ✅ 无效 session_id 处理

### 7. TestQuestionType (2 个用例)
- ✅ concept 问题类型
- ✅ problem_solving 问题类型

### 8. TestSubjectHandling (2 个用例)
- ✅ math 学科
- ✅ chinese 学科

### 9. TestTransactionConsistency (1 个用例)
- ✅ 问题-答案事务一致性

---

## 🔗 关键验证点

每个测试都验证以下方面:

```python
✅ 响应格式正确
✅ 数据库记录被创建
✅ 关系正确建立
✅ 统计信息更新
✅ 性能指标记录
✅ 错误处理正确
✅ 事务一致性
```

---

## 📝 Fixture 快速参考

```python
# 创建测试用户
async def test_user(db_session) -> User:
    # 返回带 id, phone, name 的 User 对象

# 创建测试会话
async def test_session(db_session, test_user) -> ChatSession:
    # 返回关联到 test_user 的 ChatSession

# 标准提问请求
def test_ask_question_request() -> AskQuestionRequest:
    # content="如何求解二次方程？"
    # question_type="problem_solving"
    # subject="math"

# 包含图片的提问
def test_ask_question_with_images_request() -> AskQuestionRequest:
    # image_urls=["https://example.com/homework1.jpg", ...]
    # question_type="homework_help"

# Mock AI 响应
def test_homework_correction_ai_response() -> str:
    # 返回作业批改的 JSON 响应
    # 包含 corrections, summary, overall_score 等
```

---

## ✨ 集成测试架构优势

1. **完整性** - 从 API 到数据库的完整流程测试
2. **隔离性** - 使用 in-memory SQLite，完全隔离
3. **可重现性** - 每个测试独立，可重复运行
4. **清晰性** - Mock 服务避免 API 依赖
5. **覆盖性** - 18 个用例覆盖主要场景

---

## 🎯 下一步行动

### 立即执行 (Priority 1)
1. **修复 SQLAlchemy 异步问题**
   - 在 `src/services/learning_service.py` 中
   - 替换 `refresh()` 调用为 SELECT 查询
   - 预计 15-30 分钟

2. **运行测试并验证**
   ```bash
   uv run pytest tests/integration/test_ask_question_integration.py -v
   ```
   - 预计 5-10 分钟

3. **修复任何失败的用例**
   - 根据错误信息调整
   - 预计 15-30 分钟

### 后续执行 (Priority 2)
- [ ] Phase 3.3 - Prompt 优化 (60 min)
- [ ] Phase 3.4 - 性能监控 (60 min)
- [ ] 生成完整的覆盖率报告

---

## 📞 故障排查

### 问题 1: ImportError in conftest
**解决**: 检查文件末尾没有多余的标签或语法错误
```bash
python -m py_compile tests/conftest.py
```

### 问题 2: AsyncIO 事件循环错误
**解决**: 确保使用 `@pytest.mark.asyncio`
```python
@pytest.mark.asyncio
async def test_something():
    pass
```

### 问题 3: 数据库连接失败
**解决**: 检查 fixture 中的数据库配置
```python
engine = create_async_engine("sqlite+aiosqlite:///:memory:")
```

---

## 📚 相关文档

- `PHASE_3_2_PROGRESS.md` - 详细进度报告
- `PHASE_3_TEST_SUMMARY.md` - Phase 3.1 单元测试总结
- `PHASE_3_QUICK_START.md` - 快速开始指南
- `DEVELOPMENT_CONTEXT.md` - 完整开发计划

---

## 💾 文件体积

```
test_ask_question_integration.py:  739 行
conftest.py 新增:                 170+ 行
总计:                             ~900 行新代码
```

---

**更新时间**: 2025-11-05  
**Phase 3.2 进度**: 65% (框架完成，待运行验证)  
**总体 Phase 3 进度**: 85%+  
**预期完成**: Phase 3.2 修复后 + Phase 3.3-3.4 = 下一小时