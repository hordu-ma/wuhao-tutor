# Phase 3 快速开始指南

## 🚀 快速运行测试

### 运行所有 Phase 3 单元测试

```bash
# 运行全部 56 个测试
uv run pytest tests/services/test_homework_correction_scenario.py \
                tests/services/test_ai_correction_call.py \
                tests/services/test_create_mistakes_from_correction.py -v

# 生成覆盖率报告
uv run pytest tests/services/test_homework_correction_scenario.py \
                tests/services/test_ai_correction_call.py \
                tests/services/test_create_mistakes_from_correction.py \
                --cov=src/services/learning_service --cov-report=html
```

### 运行单个测试套件

```bash
# 场景检测测试 (21 个用例)
uv run pytest tests/services/test_homework_correction_scenario.py -v

# AI 调用测试 (20 个用例)
uv run pytest tests/services/test_ai_correction_call.py -v

# 错题创建测试 (15 个用例)
uv run pytest tests/services/test_create_mistakes_from_correction.py -v
```

### 运行特定测试

```bash
# 运行单个测试类
uv run pytest tests/services/test_homework_correction_scenario.py::TestIsHomeworkCorrectionScenario -v

# 运行单个测试方法
uv run pytest tests/services/test_homework_correction_scenario.py::TestIsHomeworkCorrectionScenario::test_homework_help_question_type -xvs
```

## 📋 测试统计

| 测试模块 | 用例数 | 状态 |
|---------|-------|------|
| 场景检测 | 21 | ✅ 全部通过 |
| AI 调用 | 20 | ✅ 全部通过 |
| 错题创建 | 15 | ✅ 全部通过 |
| **总计** | **56** | **✅ 100%** |

## 🔧 关键测试场景

### 场景检测测试
- ✅ HOMEWORK_HELP 问题类型直接返回 True
- ✅ 12 个不同批改关键词识别
- ✅ 关键词 + 图片组合判断
- ✅ 边界情况处理（空内容、超长内容、特殊字符）

### AI 调用测试
- ✅ 成功调用和 JSON 解析
- ✅ JSON 前后有文本时的处理
- ✅ 100 题超大 JSON 响应
- ✅ Unicode 和特殊字符处理
- ✅ AI 服务失败处理

### 错题创建测试
- ✅ 只创建错误和未作答的题目
- ✅ 跳过正确答案
- ✅ 标题生成和字段映射
- ✅ 各种题型和学科支持

## 🏗️ 测试基础设施

### Mock BailianService
```python
# 在 tests/conftest.py 中定义
class MockBailianService:
    - 可配置的 AI 响应
    - 支持各种失败场景
    - 记录调用参数便于验证
```

### 数据工厂
```python
# 在 tests/conftest.py 中定义
class CorrectAnswerFactory:
    - 参数化生成批改结果
    - 支持各种组合场景
```

### 通用 Fixture
```python
@pytest.fixture
async def db_session():
    """in-memory SQLite 数据库"""

@pytest.fixture
def mock_bailian_service():
    """Mock AI 服务"""

@pytest.fixture
def test_correction_result():
    """标准测试批改结果"""

@pytest.fixture
def test_user_id():
    """测试用户 ID"""

@pytest.fixture
def test_image_urls():
    """测试图片 URLs"""
```

## 📊 代码覆盖率

### Phase 3.1 单元测试覆盖
- `_is_homework_correction_scenario()` → 100% ✅
- `_call_ai_for_homework_correction()` → 100% ✅
- `_create_mistakes_from_correction()` → 100% ✅

### 总体统计
- 测试代码：1,763 行
- 被测试代码覆盖：100%
- 测试通过率：100%

## 🐛 已知问题与修复

### 问题 1：Prompt 格式字符串转义
**修复**: 使用 `{{` 和 `}}` 转义 JSON 中的大括号
```python
# 错误：KeyError
HOMEWORK_CORRECTION_PROMPT = """
{
  "corrections": [...]
}
"""

# 正确
HOMEWORK_CORRECTION_PROMPT = """
{{
  "corrections": [...]
}}
"""
```

### 问题 2：Schema 验证约束
**修复**: 遵守 `total_questions >= 1` 的验证规则
```python
# 不能创建 total_questions=0 的批改结果
if len(corrections) == 0:
    return None
```

## 🔍 调试技巧

### 查看 Mock 服务的调用记录
```python
@pytest.mark.asyncio
async def test_example(mock_bailian_service):
    # ... 运行测试 ...
    
    # 检查调用次数
    assert mock_bailian_service.call_count == 1
    
    # 检查最后一次调用的参数
    assert mock_bailian_service.last_kwargs["temperature"] == 0.3
    assert mock_bailian_service.last_messages is not None
```

### 生成自定义测试数据
```python
from tests.conftest import CorrectAnswerFactory

factory = CorrectAnswerFactory()

# 创建单题批改
item = factory.create_correction_item(
    question_number=1,
    is_unanswered=False,
    error_type="计算错误",
    score=0,
)

# 创建完整批改结果 JSON
json_str = factory.create_correction_result(
    num_total=5,
    num_errors=2,
    num_unanswered=1,
)
```

### 运行特定场景测试
```bash
# 只运行关键词测试
uv run pytest tests/services/test_homework_correction_scenario.py -k keyword -v

# 只运行错误处理测试
uv run pytest tests/services/test_ai_correction_call.py -k error -v

# 只运行包含 "unanswered" 的测试
uv run pytest tests/services/test_create_mistakes_from_correction.py -k unanswered -v
```

## 📚 相关文档

- `PHASE_2_SUMMARY.md` - Phase 2 实现总结
- `PHASE_3_TEST_SUMMARY.md` - Phase 3.1 测试总结
- `DEVELOPMENT_CONTEXT.md` - 完整开发计划
- `src/services/learning_service.py` - 核心实现代码

## ✅ Phase 3.1 检查清单

- [x] conftest.py 创建
- [x] Mock BailianService 实现
- [x] 场景检测测试（21 个）
- [x] AI 调用测试（20 个）
- [x] 错题创建测试（15 个）
- [x] 所有测试通过
- [x] 问题识别和修复
- [ ] Phase 3.2 集成测试（待进行）
- [ ] Phase 3.3 Prompt 优化（待进行）
- [ ] Phase 3.4 性能监控（待进行）

## 🚀 下一步行动

1. **运行所有测试验证环境**
   ```bash
   uv run pytest tests/services/test_homework_correction_scenario.py \
                   tests/services/test_ai_correction_call.py \
                   tests/services/test_create_mistakes_from_correction.py -v
   ```

2. **查看测试覆盖率**
   ```bash
   uv run pytest tests/services/ --cov=src/services/learning_service --cov-report=html
   ```

3. **进行 Phase 3.2 集成测试** (下一步)
   - 验证完整流程
   - 测试数据库集成
   - 验证事务一致性

4. **进行 Phase 3.3 Prompt 优化** (后续)
   - 验证 AI 响应质量
   - 优化参数设置
   - 多学科测试

5. **进行 Phase 3.4 性能监控** (后续)
   - 性能基准测试
   - 错误率监控
   - N+1 查询检测

---

**最后更新**: 2025-11-05  
**Phase 3.1 状态**: ✅ 完成  
**总体进度**: 80%+  
**下一里程碑**: Phase 3.2 集成测试