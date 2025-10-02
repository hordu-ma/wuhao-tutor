# Phase 2 恢复命令速查卡

> 系统修复后的快速恢复命令 - 5分钟完成

---

## 🚀 一键恢复 (推荐)

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor && \
uv run alembic upgrade head && \
sqlite3 wuhao_tutor_dev.db ".tables" | grep answers && \
uv run python scripts/test_phase2_analytics.py
```

---

## 📋 分步执行

### Step 1: 完成数据库迁移
```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor
uv run alembic upgrade head
```

### Step 2: 验证表创建
```bash
# 检查所有表
sqlite3 wuhao_tutor_dev.db ".tables"

# 查看 answers 表结构
sqlite3 wuhao_tutor_dev.db ".schema answers"
```

### Step 3: 运行测试
```bash
uv run python scripts/test_phase2_analytics.py
```

---

## ✅ 成功标志

### Alembic 迁移成功
```
INFO  [alembic.runtime.migration] Running upgrade ... -> ..., create answers table
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
```

### 表创建成功
```sql
CREATE TABLE answers (
    id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    content TEXT NOT NULL,
    -- ... 其他字段
    PRIMARY KEY (id),
    FOREIGN KEY(question_id) REFERENCES questions (id)
);
```

### 测试全部通过
```
学习统计API: ✅ 通过
用户统计API: ✅ 通过
知识图谱API: ✅ 通过
Session统计更新: ✅ 通过
数据完整性: ✅ 通过

总计: 5/5 通过
✅ Phase 2 所有测试通过!
```

---

## 🔍 快速诊断

### 检查迁移状态
```bash
uv run alembic current
uv run alembic history
```

### 检查数据库连接
```bash
sqlite3 wuhao_tutor_dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
```

### 检查 Python 环境
```bash
uv run python --version
uv sync
```

---

## 📝 测试通过后

### 生成测试报告
```bash
# 基于测试输出手动创建或编辑
code PHASE2_TEST_RESULTS.md
```

### 更新 Git 状态
```bash
git add .
git commit -m "test: Phase 2 testing complete - all 5 tests passed"
```

### 准备 Phase 3
```bash
# 启动后端
./scripts/start-dev.sh

# 启动前端 (新终端)
cd frontend && npm run dev

# 启动小程序开发工具
# 手动打开微信开发者工具
```

---

## 🚨 故障排查

### 迁移失败
```bash
# 检查数据库锁定
lsof | grep wuhao_tutor_dev.db

# 重新同步环境
uv sync

# 重试迁移
uv run alembic upgrade head
```

### 测试仍失败
```bash
# 查看详细错误
uv run python scripts/test_phase2_analytics.py --verbose

# 检查编译错误
uv run python -m py_compile scripts/test_phase2_analytics.py

# 验证模型导入
uv run python -c "from src.models import Answer; print(Answer.__tablename__)"
```

---

## 📚 相关文档

- **详细指南**: `PHASE2_RECOVERY_GUIDE.md` (完整故障排查)
- **状态快照**: `PHASE2_STATUS_SNAPSHOT.md` (当前状态摘要)
- **测试指南**: `PHASE2_TEST_GUIDE.md` (测试说明)
- **错误修复**: `PHASE2_TEST_FIX_REPORT.md` (21个错误详解)

---

**创建时间**: 2025-10-02 19:45  
**用途**: 系统修复后快速恢复 Phase 2 测试
