# Week 1 核心功能部署指南

> **完成日期**: 2025-11-04  
> **功能**: 知识点自动关联 + AI 学情上下文 + 小程序筛选

---

## 📋 完成的功能

### ✅ Task 1: 修复知识点自动关联逻辑

**修改的文件**:
- `src/services/learning_service.py`
  - 增强了 `_auto_create_mistake_if_needed()` 方法，确保 AI 知识点数据完整传递
  - 新增 `_extract_knowledge_points_from_answer()` 方法，从 AI 回答中提取知识点
  - 新增 `_trigger_knowledge_association()` 方法，触发知识图谱关联

**效果**:
- 错题创建时自动从 AI 回答中提取知识点
- 自动调用知识图谱服务创建关联记录
- 支持多种知识点提取策略（关键词匹配 + 模式匹配）

---

### ✅ Task 2: 实现 AI 学情上下文注入

**修改的文件**:
- `src/services/knowledge_context_builder.py`
  - 新增 `_get_mastery_from_snapshot()` 方法，优先从知识图谱快照获取掌握度
  - 增强 `build_context()` 方法，集成快照数据

**效果**:
- AI 问答时能够获取用户的知识图谱快照
- 提供个性化的学情上下文
- 代码已集成在 `learning_service.py` 的第 510-570 行

---

### ✅ Task 3: 打通小程序知识点筛选功能

**验证结果**:
- 小程序代码已就绪（`miniprogram/pages/mistakes/list/index.js`）
- API 客户端已就绪（`miniprogram/api/mistakes.js`）
- 后端端点已就绪（`src/api/v1/endpoints/knowledge_graph.py`）

**效果**:
- 小程序可按知识点筛选错题
- 学科切换时自动加载知识点选项
- 支持知识点统计和展示

---

## 🚀 部署步骤

### 1. 连接到生产服务器

```bash
ssh root@121.199.173.244
cd /opt/wuhao-tutor
```

### 2. 备份数据库（重要！）

```bash
# 备份 PostgreSQL 数据库
pg_dump wuhao_tutor > backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用项目脚本
./scripts/backup_database.sh
```

### 3. 拉取最新代码

```bash
git pull origin main

# 或使用部署脚本（推荐）
cd ~/my-devs/python/wuhao-tutor
./scripts/deploy.sh
```

### 4. 重启后端服务

```bash
# 方式 1: 使用 systemd
ssh root@121.199.173.244 'systemctl restart wuhao-tutor.service'

# 方式 2: 使用部署脚本（自动重启）
./scripts/deploy.sh

# 验证服务状态
ssh root@121.199.173.244 'systemctl status wuhao-tutor.service'
```

### 5. 数据回填（首次部署必需）

在生产服务器上运行数据回填脚本：

```bash
ssh root@121.199.173.244
cd /opt/wuhao-tutor

# 🔍 Step 1: 干运行测试（查看将要处理的数据）
source venv/bin/activate
python scripts/backfill_knowledge_associations.py --dry-run --limit=10

# ✅ Step 2: 小批量测试（处理前10条）
python scripts/backfill_knowledge_associations.py --limit=10

# 🚀 Step 3: 全量回填（确认无误后）
python scripts/backfill_knowledge_associations.py

# 📊 查看回填结果
# 检查 mistake_knowledge_points 表是否有数据
psql -U postgres -d wuhao_tutor -c "SELECT COUNT(*) FROM mistake_knowledge_points;"
```

**预期输出**:
```
==============================================================
错题知识点关联数据回填脚本
模式: 正式运行
限制: 无限制
==============================================================
找到 45 条需要处理的错题记录
[1/45] 处理错题 xxx-xxx-xxx
错题 xxx-xxx-xxx 提取到 2 个知识点: ['二次函数', '函数图像']
✅ 成功为错题 xxx-xxx-xxx 创建 2 个知识点关联
...
==============================================================
处理完成！统计信息：
  总计: 45
  成功: 38
  跳过: 7
  失败: 0
==============================================================
```

### 6. 验证功能

#### 6.1 验证后端 API

```bash
# 测试知识点列表 API
curl -H "Authorization: Bearer <your_token>" \
  "https://horsduroot.com/api/v1/knowledge-graph/knowledge-points?subject=数学"

# 预期返回
{
  "subject": "数学",
  "knowledge_points": [
    {"name": "二次函数", "mistake_count": 5},
    {"name": "函数图像", "mistake_count": 3}
  ],
  "total_count": 2
}
```

#### 6.2 验证小程序功能

1. 打开微信小程序「五好伴学」
2. 进入「错题手册」页面
3. 点击筛选按钮
4. 选择学科（如"数学"）
5. 验证知识点选项是否自动加载
6. 选择知识点筛选
7. 验证错题列表是否正确筛选

#### 6.3 验证 AI 学情上下文

1. 小程序中提问一个数学问题
2. 检查服务器日志，查看是否注入了学情上下文：

```bash
ssh root@121.199.173.244
journalctl -u wuhao-tutor.service -f | grep "MCP上下文"

# 预期日志
MCP上下文已构建 - 用户: xxx, 薄弱知识点: 3
✅ 从快照获取掌握度: user=xxx, knowledge_points=5
```

#### 6.4 验证知识点自动关联

1. 小程序中上传一道题目图片提问
2. 查看服务器日志：

```bash
journalctl -u wuhao-tutor.service -f | grep "知识点"

# 预期日志
✅ 从AI回答中提取到 2 个知识点
🔗 知识点关联已触发: mistake_id=xxx
✅ 知识点关联成功: mistake_id=xxx, 关联数量=2
```

3. 检查数据库：

```bash
# 查看新创建的关联
psql -U postgres -d wuhao_tutor -c \
  "SELECT m.id, m.title, COUNT(mkp.id) as kp_count 
   FROM mistake_records m 
   LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id 
   WHERE m.created_at > NOW() - INTERVAL '1 hour' 
   GROUP BY m.id, m.title;"
```

---

## 🔍 故障排查

### 问题 1: 知识点列表为空

**症状**: 小程序筛选弹窗中知识点选项为空

**排查步骤**:
1. 检查后端 API 是否返回数据
   ```bash
   curl -H "Authorization: Bearer <token>" \
     "https://horsduroot.com/api/v1/knowledge-graph/knowledge-points?subject=数学"
   ```

2. 检查数据库是否有数据
   ```bash
   psql -U postgres -d wuhao_tutor -c \
     "SELECT * FROM mistake_knowledge_points LIMIT 10;"
   ```

3. 如果数据库为空，运行回填脚本
   ```bash
   python scripts/backfill_knowledge_associations.py
   ```

---

### 问题 2: 知识点关联创建失败

**症状**: 日志显示「触发知识点关联失败」

**排查步骤**:
1. 检查 `knowledge_graph_service.py` 的导入是否正常
   ```bash
   python -c "from src.services.knowledge_graph_service import KnowledgeGraphService; print('OK')"
   ```

2. 检查数据库表是否存在
   ```bash
   psql -U postgres -d wuhao_tutor -c "\dt mistake_knowledge_points"
   ```

3. 查看详细错误日志
   ```bash
   journalctl -u wuhao-tutor.service -n 100 | grep -A 10 "知识点关联失败"
   ```

---

### 问题 3: AI 学情上下文未注入

**症状**: AI 回答不够个性化

**排查步骤**:
1. 检查是否有知识图谱快照
   ```bash
   psql -U postgres -d wuhao_tutor -c \
     "SELECT COUNT(*) FROM user_knowledge_graph_snapshots;"
   ```

2. 如果快照表为空，需要先生成快照（这是 Week 2 的任务）
   ```bash
   # 临时方案：直接使用实时计算的掌握度
   # 快照功能将在 Week 2 实现
   ```

3. 检查 MCP 上下文构建日志
   ```bash
   journalctl -u wuhao-tutor.service -f | grep "MCP"
   ```

---

## 📊 监控指标

### 关键指标

1. **知识点关联成功率**
   ```sql
   -- 有 AI feedback 的错题数
   SELECT COUNT(*) FROM mistake_records WHERE ai_feedback IS NOT NULL;
   
   -- 已关联知识点的错题数
   SELECT COUNT(DISTINCT mistake_id) FROM mistake_knowledge_points;
   
   -- 关联成功率 = 已关联 / 有 feedback
   ```

2. **API 响应时间**
   ```bash
   # 监控知识点列表 API
   time curl -s -H "Authorization: Bearer <token>" \
     "https://horsduroot.com/api/v1/knowledge-graph/knowledge-points?subject=数学" > /dev/null
   
   # 预期: < 500ms
   ```

3. **知识点提取准确率**
   ```bash
   # 查看最近创建的错题及其知识点
   psql -U postgres -d wuhao_tutor -c \
     "SELECT m.title, COUNT(mkp.id) as kp_count 
      FROM mistake_records m 
      LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id 
      WHERE m.created_at > NOW() - INTERVAL '24 hours' 
      GROUP BY m.id, m.title 
      ORDER BY m.created_at DESC 
      LIMIT 10;"
   ```

---

## 🎯 验收标准

- [x] **功能 1**: 新创建的错题自动关联知识点
- [x] **功能 2**: AI 批改时能获取用户学情上下文
- [x] **功能 3**: 小程序可按知识点筛选错题
- [x] **代码质量**: 类型注解完整，异常处理妥当
- [x] **文档完善**: 部署说明、故障排查文档齐全

---

## 📝 注意事项

1. **数据回填脚本只需运行一次**（为现有错题补充关联）
2. **新创建的错题会自动关联**，无需再次运行脚本
3. **知识图谱快照功能**将在 Week 2 实现，当前使用实时计算
4. **监控服务日志**以确保功能正常运行

---

## 🔄 回滚方案

如果部署出现问题，可以快速回滚：

```bash
# 1. 回滚代码
ssh root@121.199.173.244
cd /opt/wuhao-tutor
git reset --hard <previous_commit_hash>

# 2. 重启服务
systemctl restart wuhao-tutor.service

# 3. 验证服务状态
systemctl status wuhao-tutor.service
curl https://horsduroot.com/health
```

---

**部署完成后，请在此打勾确认** ✅

- [ ] 代码部署完成
- [ ] 服务重启成功
- [ ] 数据回填完成
- [ ] 功能验证通过
- [ ] 监控指标正常

---

**联系方式**: 如有问题，请查看日志或联系开发团队  
**文档版本**: v1.0  
**最后更新**: 2025-11-04
