# Phase 3.3 快速开始指南

## 📍 当前状态

- ✅ Phase 3.1: 单元测试框架（56 tests）
- ✅ Phase 3.2: 集成测试框架（18 tests, 100% pass）
- ⏸️ Phase 3.3: Prompt 优化（准备开始）

---

## 🎯 本阶段目标

1. **准确率**: ≥90% 的作业批改准确率
2. **覆盖**: 5 种典型场景 + 5 种边界情况
3. **性能**: ≤30 秒（5 题以内）
4. **交付**: 完整测试 + 优化文档

---

## 📋 Todo List（12 项）

查看详细计划: `cat PHASE_3_3_PLAN.md`

### 进度概览

```
阶段 1: 理解与准备 (15 min)  [ ] Task 1-2
阶段 2: 基线测试 (10 min)    [ ] Task 3-4
阶段 3: Prompt 优化 (20 min) [ ] Task 5-7
阶段 4: 边界测试 (10 min)    [ ] Task 8-9
阶段 5: 性能验证 (5 min)     [ ] Task 10
阶段 6: 文档收尾 (10 min)    [ ] Task 11-12
```

**总预计时长**: 60 分钟

---

## 🚀 立即开始

### 第一步：阅读当前 Prompt

```bash
# 查看当前 Prompt 实现
cat src/services/learning_service.py | sed -n '75,127p'
```

### 第二步：创建测试目录

```bash
# 创建测试数据目录
mkdir -p tests/fixtures/homework_samples
mkdir -p tests/performance
```

### 第三步：启动第一个任务

参考 `PHASE_3_3_PLAN.md` 中的 Task 1 详细说明

---

## 🔧 常用命令

```bash
# 运行 Prompt 准确性测试
uv run pytest tests/integration/test_prompt_accuracy.py -v

# 运行边界测试
uv run pytest tests/integration/test_prompt_edge_cases.py -v

# 运行性能测试
uv run pytest tests/performance/test_prompt_performance.py -v

# 代码检查
mypy src/services/learning_service.py --strict
black src/services/learning_service.py

# 测试覆盖率
pytest tests/integration/test_prompt_*.py \
       --cov=src.services.learning_service \
       --cov-report=html
```

---

## 📝 关键文件

| 文件                                           | 用途                     |
| ---------------------------------------------- | ------------------------ |
| `PHASE_3_3_PLAN.md`                            | 详细计划和任务说明       |
| `src/services/learning_service.py`             | Prompt 实现（行 75-127） |
| `tests/integration/test_prompt_accuracy.py`    | 准确性测试（待创建）     |
| `tests/integration/test_prompt_edge_cases.py`  | 边界测试（待创建）       |
| `tests/performance/test_prompt_performance.py` | 性能测试（待创建）       |
| `tests/fixtures/homework_samples/`             | 测试数据（待创建）       |

---

## ⚠️ 注意事项

1. **谨慎稳健**: 每次修改 Prompt 后立即运行测试验证
2. **记录数据**: 记录每次优化前后的准确率变化
3. **控制范围**: 最多 2 次 Prompt 优化迭代
4. **保持备份**: 优化前保存原始 Prompt 到注释

---

## 📞 遇到问题？

- 查看详细计划: `cat PHASE_3_3_PLAN.md`
- 查看主文档: `cat DEVELOPMENT_CONTEXT.md`
- 查看开发规范: `cat .github/copilot-instructions.md`

---

**准备好了吗？** 开始 Task 1！ 🎯
