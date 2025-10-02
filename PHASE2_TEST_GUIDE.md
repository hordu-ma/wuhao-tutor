# Phase 2 测试验证指南

**日期**: 2025-10-02  
**状态**: ✅ 测试脚本就绪  
**任务**: 验证 Phase 2 成果

---

## 🎯 测试目标

验证以下 Phase 2 功能:

1. ✅ LearningService 数据持久化完整
2. ✅ Analytics API 返回正确数据
3. ✅ Session 统计自动更新
4. ✅ 数据库数据完整性

---

## 🚀 快速开始

### 方式 1: 运行完整测试脚本 (推荐)

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor

# 运行Phase 2测试
uv run python scripts/test_phase2_analytics.py
```

**预期输出**:

```
================================================================================
🚀 Phase 2 Analytics API 测试
================================================================================

🧪 测试 1: 学习统计数据
==================================================
📊 时间范围: 7d
  ├─ 学习天数: X
  ├─ 提问总数: X
  ├─ 作业总数: X
  ├─ 平均分数: X
  └─ 知识点数量: X

✅ 学习统计API测试通过

🧪 测试 2: 用户统计数据
==================================================
👤 用户统计:
  ├─ 加入日期: XXXX-XX-XX
  ├─ 最后登录: XXXX-XX-XX
  └─ ...

✅ 用户统计API测试通过

...

================================================================================
📊 测试结果汇总
================================================================================
✅ 学习统计API: 通过
✅ 用户统计API: 通过
✅ 知识图谱API: 通过
✅ Session统计更新: 通过
✅ 数据完整性: 通过

🎉 所有测试通过! (5/5)
```

---

### 方式 2: 手动测试单个功能

#### 测试 1: 启动后端服务

```bash
# 方式A: 使用开发脚本
./scripts/start-dev.sh

# 方式B: 直接启动
uv run python src/main.py
```

#### 测试 2: 健康检查

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查Analytics端点注册
curl http://localhost:8000/api/v1/health
```

#### 测试 3: 测试 Analytics API (需要 Token)

```bash
# 1. 获取测试用户Token (需要先创建用户)
# 使用 scripts/create_test_user.py 或登录接口

# 2. 测试学习统计API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/analytics/learning-stats?time_range=30d"

# 预期返回:
{
  "success": true,
  "data": {
    "total_study_days": 5,
    "total_questions": 10,
    "total_homework": 3,
    "avg_score": 85.5,
    "knowledge_points": [...],
    "study_trend": [...]
  }
}

# 3. 测试用户统计API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/analytics/user/stats"

# 4. 测试知识图谱API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/analytics/knowledge-map?subject=math"
```

---

## 📋 测试检查清单

### 基础环境 ✅

- [x] Python 环境配置正确 (uv)
- [x] 数据库连接正常 (SQLite/PostgreSQL)
- [x] 依赖包安装完整
- [x] 测试脚本错误已修复 (21 个)

### Analytics Service ✅

- [ ] `get_learning_stats()` 返回正确数据
  - [ ] 时间范围过滤正确 (7d/30d/90d/all)
  - [ ] 学习天数统计准确
  - [ ] 知识点列表非空
  - [ ] 学习趋势数据正确
- [ ] `get_user_stats()` 返回正确数据
  - [ ] 加入日期正确
  - [ ] 作业/提问计数准确
  - [ ] 平均分数计算正确
- [ ] `get_knowledge_map()` 返回正确数据
  - [ ] 全部学科查询正常
  - [ ] 特定学科过滤正确
  - [ ] 知识点节点结构合理

### LearningService ✅

- [ ] Question 保存完整
- [ ] Answer 保存完整
  - [ ] content 字段非空
  - [ ] tokens_used 已记录
  - [ ] generation_time 已记录
  - [ ] model_name 已记录
- [ ] Session 统计更新
  - [ ] question_count 自动更新
  - [ ] total_tokens 累加正确
  - [ ] last_activity_at 更新及时

### 数据库完整性 ✅

- [ ] 所有字段非 NULL (必填字段)
- [ ] 外键关联正确
  - [ ] Question.session_id → ChatSession.id
  - [ ] Answer.question_id → Question.id
- [ ] 索引生效
  - [ ] user_id 索引
  - [ ] created_at 索引
  - [ ] session_id + created_at 复合索引

---

## 🐛 常见问题排查

### 问题 1: 测试脚本报错

**现象**: 运行 test_phase2_analytics.py 出现导入错误或类型错误

**解决**:

```bash
# 1. 检查错误是否已修复
cat PHASE2_TEST_FIX_REPORT.md

# 2. 重新检查文件
uv run python -c "from src.services.analytics_service import AnalyticsService; print('Import OK')"

# 3. 查看详细错误
uv run python scripts/test_phase2_analytics.py 2>&1 | tee test_output.log
```

### 问题 2: 数据库无数据

**现象**: 测试显示"数据库中暂无数据"

**解决**:

```bash
# 1. 初始化数据库
uv run python scripts/init_database.py

# 2. 或运行诊断
uv run python scripts/diagnose.py

# 3. 手动创建测试数据
uv run python scripts/create_test_user.py
```

### 问题 3: API 返回 401 未授权

**现象**: curl 测试返回 401 错误

**解决**:

```bash
# 1. 创建测试用户并获取Token
uv run python scripts/create_test_user.py

# 2. 或通过登录接口获取
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000", "password": "test123"}'

# 3. 使用返回的access_token
export TOKEN="eyJ..."
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/analytics/learning-stats"
```

### 问题 4: 后端服务未启动

**现象**: 连接拒绝 (Connection refused)

**解决**:

```bash
# 1. 检查服务状态
./scripts/status-dev.sh

# 2. 启动服务
./scripts/start-dev.sh

# 3. 查看日志
tail -f backend.log
```

---

## 📊 预期测试结果

### 成功标准

**全部通过** (5/5):

- ✅ 学习统计 API: 返回正确的聚合数据
- ✅ 用户统计 API: 返回完整的用户信息
- ✅ 知识图谱 API: 返回结构化知识点
- ✅ Session 统计更新: question_count 自动更新
- ✅ 数据完整性: Answer 元数据完整

**可接受** (4/5):

- ⚠️ 如果数据库初始数据较少,部分统计可能为 0 或空
- ⚠️ 知识图谱可能返回空数据(正常,需要积累)

**需要关注** (<4/5):

- ❌ 检查具体失败原因
- ❌ 查看错误日志
- ❌ 确认数据库连接
- ❌ 验证 Service 实现

---

## 📝 测试报告模板

### 测试执行记录

**测试时间**: YYYY-MM-DD HH:MM  
**测试环境**: 开发环境 (SQLite)  
**执行人**: [测试人员]

#### 测试结果

| 测试项       | 状态  | 备注 |
| ------------ | ----- | ---- |
| 学习统计 API | ✅/❌ |      |
| 用户统计 API | ✅/❌ |      |
| 知识图谱 API | ✅/❌ |      |
| Session 统计 | ✅/❌ |      |
| 数据完整性   | ✅/❌ |      |

#### 发现的问题

1. **问题描述**: ...
   - **严重程度**: 高/中/低
   - **影响范围**: ...
   - **建议解决方案**: ...

#### 测试结论

- [ ] ✅ 全部通过,可以进入 Phase 3
- [ ] ⚠️ 部分问题,需要修复后重测
- [ ] ❌ 严重问题,需要返工

---

## 🚀 测试完成后的下一步

### 如果测试全部通过 ✅

1. **更新文档**:

   ```bash
   # 添加测试结果到报告
   echo "测试通过: $(date)" >> PHASE2_COMPLETION_SUMMARY.md
   ```

2. **提交代码**:

   ```bash
   git add .
   git commit -m "feat: Phase 2完成 - Analytics API + 数据持久化完善"
   git push origin feature/miniprogram-init
   ```

3. **进入 Phase 3**:
   - 开始前后端联调
   - 测试小程序连接
   - 测试 Web 前端连接

### 如果测试发现问题 ⚠️

1. **记录问题**: 创建 `PHASE2_TEST_ISSUES.md`
2. **优先级排序**: P0 阻塞 > P1 重要 > P2 优化
3. **逐个修复**: 修复后重新测试
4. **回归测试**: 确保修复不影响其他功能

---

## 📞 技术支持

### 日志查看

```bash
# 后端日志
tail -f backend.log

# 数据库查询日志
tail -f backend.log | grep "SELECT"

# 错误日志
tail -f backend.log | grep "ERROR"
```

### 数据库检查

```bash
# SQLite数据库
sqlite3 wuhao_tutor_dev.db

# 查看表
.tables

# 查看数据
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM chat_sessions;
SELECT COUNT(*) FROM questions;
SELECT COUNT(*) FROM answers;
```

### 性能监控

```bash
# 运行性能监控
uv run python scripts/performance_monitor.py status

# 查看慢查询
grep "slow query" backend.log
```

---

## ✅ 测试验证 Ready!

**测试脚本**: ✅ 已修复 (21 个错误)  
**测试环境**: ✅ 已准备  
**测试数据**: ✅ 可用  
**文档**: ✅ 完整

**现在可以开始测试!** 🚀

```bash
# 立即执行
uv run python scripts/test_phase2_analytics.py
```

---

**最后更新**: 2025-10-02  
**下次更新**: 测试完成后
