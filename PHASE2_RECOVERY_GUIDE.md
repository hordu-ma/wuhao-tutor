# Phase 2 恢复指南

> **文档目的**: 系统中断后快速恢复 Phase 2 测试  
> **创建时间**: 2025-10-02 19:45  
> **预计恢复时间**: 5-10 分钟

---

## 🚨 当前状态

**阻塞问题**:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: answers
```

**根本原因**:

- Alembic 数据库迁移启动但进程中断
- `answers` 表未创建，导致测试脚本 4/5 失败

**测试结果**:

- ✅ 学习统计 API: 通过
- ❌ 用户统计 API: 失败 (answers 表不存在)
- ❌ 知识图谱 API: 失败 (answers 表不存在)
- ❌ Session 统计更新: 失败 (answers 表不存在)
- ❌ 数据完整性: 失败 (answers 表不存在)

---

## ✅ 快速恢复步骤

### Step 1: 完成数据库迁移 (P0 - Critical)

```bash
# 进入项目目录
cd /Users/liguoma/my-devs/python/wuhao-tutor

# 检查当前迁移状态
uv run alembic current

# 查看待应用的迁移
uv run alembic history

# 应用所有迁移 (创建 answers 表)
uv run alembic upgrade head
```

**预期输出**:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> ..., create answers table
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
```

---

### Step 2: 验证表创建成功

```bash
# 方法1: 使用 sqlite3 命令行
sqlite3 wuhao_tutor_dev.db ".tables"

# 应该看到包含 "answers" 的输出

# 方法2: 查看 answers 表结构
sqlite3 wuhao_tutor_dev.db ".schema answers"

# 应该显示完整的表定义
```

**预期表结构**:

```sql
CREATE TABLE answers (
    id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    content TEXT NOT NULL,
    model_name TEXT,
    tokens_used INTEGER,
    generation_time FLOAT,
    confidence_score FLOAT,
    user_rating INTEGER,
    user_feedback TEXT,
    is_helpful BOOLEAN,
    related_topics TEXT,  -- JSON array
    suggested_questions TEXT,  -- JSON array
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
    PRIMARY KEY (id),
    FOREIGN KEY(question_id) REFERENCES questions (id)
);
```

---

### Step 3: 重新运行测试

```bash
# 运行完整测试脚本
uv run python scripts/test_phase2_analytics.py
```

**预期结果**: ✅ 5/5 测试通过

```
学习统计API: ✅ 通过
用户统计API: ✅ 通过
知识图谱API: ✅ 通过
Session统计更新: ✅ 通过
数据完整性: ✅ 通过

总计: 5/5 通过
```

---

### Step 4: 生成测试报告

```bash
# 创建测试结果文档
# 手动编辑或使用以下命令生成基础模板
cat > PHASE2_TEST_RESULTS.md << 'EOF'
# Phase 2 测试结果报告

## 测试执行时间
- 开始: 2025-10-02 19:50
- 结束: 2025-10-02 19:55

## 测试结果汇总
- 总测试项: 5
- 通过: 5
- 失败: 0
- 通过率: 100%

## 详细测试结果
[填写详细测试数据...]

## 性能指标
[填写性能数据...]

## 发现的问题
[记录任何问题...]

## 优化建议
[记录优化建议...]
EOF
```

---

## 📋 检查清单

恢复完成后，确认以下项目：

- [ ] Alembic 迁移成功完成
- [ ] `answers` 表存在且结构正确
- [ ] 5 个测试项全部通过
- [ ] 无数据库连接错误
- [ ] 无类型错误或编译错误
- [ ] 测试数据创建成功
- [ ] Analytics API 返回正确数据
- [ ] LearningService 统计更新正常
- [ ] 生成测试报告文档
- [ ] 更新 MVP-DEVELOPMENT-PLAN.md

---

## 🔍 故障排查

### 问题 1: Alembic 迁移失败

**症状**: `alembic upgrade head` 报错

**排查步骤**:

```bash
# 检查 Alembic 配置
cat alembic.ini | grep sqlalchemy.url

# 检查数据库文件权限
ls -l wuhao_tutor_dev.db

# 查看迁移历史
uv run alembic history --verbose
```

**可能原因**:

- 数据库文件锁定 (其他进程占用)
- 迁移文件损坏
- Python 环境问题

**解决方案**:

```bash
# 如果数据库锁定，重启终端或杀死占用进程
lsof | grep wuhao_tutor_dev.db

# 如果迁移损坏，重新生成迁移
uv run alembic revision --autogenerate -m "recreate answers table"

# 检查 Python 环境
uv run python --version
uv sync
```

---

### 问题 2: 测试仍然失败

**症状**: 表创建成功但测试仍报错

**排查步骤**:

```bash
# 检查测试脚本是否使用正确的数据库
cat scripts/test_phase2_analytics.py | grep DATABASE

# 验证 Answer 模型导入
uv run python -c "from src.models import Answer; print(Answer.__tablename__)"

# 检查编译错误
uv run python scripts/test_phase2_analytics.py --verbose
```

**可能原因**:

- 测试使用了不同的数据库文件
- Model 定义与表结构不匹配
- 外键约束问题

---

### 问题 3: 性能问题

**症状**: 测试通过但运行很慢

**排查步骤**:

```bash
# 检查数据库索引
sqlite3 wuhao_tutor_dev.db "SELECT * FROM sqlite_master WHERE type='index';"

# 分析慢查询
# 在测试脚本中添加日志

# 查看数据库大小
ls -lh wuhao_tutor_dev.db
```

**优化建议**:

- 添加必要的数据库索引
- 优化 Analytics Service 的 SQL 查询
- 考虑添加缓存层

---

## 📚 相关文档

- **测试修复报告**: `PHASE2_TEST_FIX_REPORT.md` - 21 个编译错误的修复记录
- **测试执行指南**: `PHASE2_TEST_GUIDE.md` - 测试脚本使用说明
- **开发计划**: `MVP-DEVELOPMENT-PLAN.md` - Phase 2 完整规划
- **完成总结**: `PHASE2_COMPLETION_SUMMARY.md` - Phase 2 代码实现总结

---

## 🎯 下一步行动

Phase 2 测试通过后:

1. **标记 Phase 2 完成**

   - 在 MVP-DEVELOPMENT-PLAN.md 中更新状态
   - 创建 Git commit: `feat: complete Phase 2 - Analytics backend`

2. **准备进入 Phase 3: 前后端联调**

   - 启动后端开发服务器
   - 启动前端开发服务器 (Web + 小程序)
   - 测试端到端集成

3. **创建 Phase 3 任务计划**
   - API 对接验证
   - UI 交互测试
   - 用户体验优化

---

**最后更新**: 2025-10-02 19:45  
**状态**: ⏳ 等待系统修复后执行
