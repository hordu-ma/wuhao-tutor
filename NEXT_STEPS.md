# 🚀 下一步开发行动计划

> **更新时间**: 2025-10-05  
> **当前阶段**: Phase 4 - 智能上下文增强  
> **当前任务**: TD-006 MCP 上下文构建服务开发  
> **核心策略**: MCP 优先（精确查询）→ RAG 增强（语义检索）两阶段演进

---

## ✅ Phase 4 已完成任务 (2025-10-05)

### ✅ TD-002: 知识点提取优化

**完成时间**: 2025-10-05  
**实际工时**: 1 天

#### 交付成果

- ✅ `KnowledgeExtractionService` - 规则+AI 混合提取
- ✅ jieba 0.42.1 中文分词集成
- ✅ 3 个学科知识词典 (22 个知识点)
- ✅ 13 个单元测试 (100% 通过率)
- ✅ 完整技术文档

#### 关键文件

```
src/services/knowledge_extraction_service.py  ✅
data/knowledge_dict/                          ✅
  ├── math.json
  ├── chinese.json
  └── english.json
tests/unit/test_knowledge_extraction.py       ✅
docs/reports/TD-002-KNOWLEDGE-EXTRACTION-PROGRESS.md ✅
```

---

### ✅ TD-003: 知识图谱数据导入

**完成时间**: 2025-10-05  
**实际工时**: 1 天

#### 交付成果

- ✅ 知识图谱数据格式规范 (`data/knowledge/README.md`)
- ✅ 七年级数学知识图谱 (25 节点 + 18 关系)
- ✅ 知识图谱导入脚本 (480+ 行)
- ✅ SQLite UUID 类型兼容性修复
- ✅ 数据验证和增量更新机制

---

### ✅ TD-005: 答案质量评估

**完成时间**: 2025-10-05  
**实际工时**: 4 小时

#### 交付成果

- ✅ `AnswerQualityScore` 模型 - 5 维度评分
- ✅ `AnswerQualityService` - 规则/AI/混合评估
- ✅ `AnswerQualityRepository` - 数据访问层
- ✅ 13 个单元测试 (100% 通过率)
- ✅ 技术文档 (2000+ 行)

#### 关键文件

```
src/models/answer_quality.py                   ✅
src/services/answer_quality_service.py         ✅
src/repositories/answer_quality_repository.py  ✅
tests/unit/test_answer_quality_service.py      ✅
docs/reports/TD-005-ANSWER-QUALITY-PROGRESS.md ✅
```

#### 核心特性

1. **多维度评分**: accuracy (30%), completeness (25%), relevance (20%), clarity (15%), usefulness (10%)
2. **混合评估**: 规则引擎 (30%) + AI 模型 (70%)
3. **人工反馈**: 支持教师手动覆盖评分
4. **高质量检索**: 快速查询优质答案

#### 关键文件

```
data/knowledge/README.md                      ✅
data/knowledge/math/grade_7.json              ✅
scripts/init_knowledge_graph.py               ✅
docs/reports/TD-003-KNOWLEDGE-GRAPH-PROGRESS.md ✅
```

#### 技术亮点

- **UUID 类型处理**: 解决 SQLite `UUID(as_uuid=True)` 查询/赋值问题
- **数据验证**: JSON Schema 验证 + 关系完整性检查
- **增量更新**: 支持重复导入，自动跳过/更新现有数据
- **命令行接口**: `--subject`, `--grade`, `--file` 参数灵活控制

---

## 🔥 当前任务 (Week 2, 2025-10-06~12)

### 1️⃣ TD-006: MCP 上下文构建服务 - 🔥 最高优先级

**目标**: 实现基于精确数据库查询的个性化学情上下文服务  
**预估工时**: 16 小时 (2 天)  
**截止日期**: 2025-10-08

#### 核心功能

```python
class KnowledgeContextBuilder:
    """MCP 上下文构建服务"""
    
    async def build_context(
        self, 
        user_id: str, 
        subject: str,
        session_type: str  # "learning_qa" or "homework_grading"
    ) -> Dict[str, Any]:
        """构建个性化学情上下文"""
        return {
            "weak_knowledge_points": await self._query_weak_points(user_id, subject),
            "learning_preferences": await self._query_preferences(user_id),
            "recent_errors": await self._query_recent_errors(user_id, subject, limit=5),
            "mastery_stats": await self._query_mastery_stats(user_id, subject),
        }
```

#### 任务分解

**Day 1 (周六, 4h)**:

- [ ] **设计服务接口** (2h)
  - 定义 `KnowledgeContextBuilder` 类结构
  - 设计数据查询逻辑（SQL 查询）
  - 定义返回数据结构

- [ ] **实现薄弱知识点查询** (2h)
  - 查询错误率最高的知识点
  - 应用时间衰减权重（近期错误权重更高）
  - 按错误率排序，返回 Top 5

**Day 2 (周日, 6h)**:

- [ ] **实现其他查询功能** (3h)
  - 学习偏好查询（活跃学科、难度偏好）
  - 最近错题查询（时间倒序）
  - 知识点掌握度统计

- [ ] **集成到服务层** (2h)
  - 在 `LearningService` 中集成
  - 在 `HomeworkService` 中集成
  - 传递到 `BailianService` 的 AI 上下文

- [ ] **测试和优化** (1h)
  - 编写单元测试（10+ 用例）
  - 性能测试（查询耗时 < 50ms）
  - SQL 查询优化（索引检查）

**Day 3 (周一, 6h)**:

- [ ] **端到端测试** (3h)
  - 使用真实数据测试上下文构建
  - 验证 AI 响应质量提升
  - 边界情况测试（新用户、无数据）

- [ ] **文档和提交** (3h)
  - 编写技术文档
  - 代码注释和 docstring
  - Git 提交和推送

#### 关键文件

```
src/services/knowledge_context_builder.py      (新建)
src/services/learning_service.py               (修改 - 集成上下文)
src/services/homework_service.py               (修改 - 集成上下文)
tests/unit/test_knowledge_context_builder.py   (新建)
docs/reports/TD-006-MCP-CONTEXT-PROGRESS.md    (新建)
```

#### 验收标准

- ✅ 支持 4+ 类型上下文数据（薄弱点、偏好、错题、掌握度）
- ✅ 查询性能 < 50ms（P95）
- ✅ 集成到两个服务层（Learning + Homework）
- ✅ 单元测试覆盖率 > 80%
- ✅ AI 响应质量提升可验证

---

## 📍 Phase 4-5 计划 (Week 2-4)

### ✅ Week 1 (10/05) - 已完成

- ✅ **TD-002 知识点提取优化** - 完成
- ✅ **TD-003 知识图谱数据导入** - 完成
- ✅ **TD-005 答案质量评估** - 完成
- ✅ **前端学习问答重构** - 完成
- ✅ **登录认证修复** - 完成

**成果**: 5/5 任务完成 (100%)

### 🔥 Week 2 (10/06 - 10/12) - 进行中

**核心任务**: MCP 上下文服务开发

- 🔥 **TD-006 MCP 上下文构建服务** (16h, 2-3天) - 当前任务
- 📋 **TD-007 流式响应实现** (12h) - 待开发
- 📋 **TD-008 请求缓存机制** (8h) - 待开发

**目标**: 实现基于精确数据库查询的个性化学情上下文

### 📋 Week 3-4 (10/13 - 10/26) - Phase 5 体验优化

- **TD-009 错题本功能** (16h)
- **TD-010 学情分析算法优化** (16h) - 遗忘曲线、时间衰减
- **TD-011 知识图谱数据扩展** (24h) - 扩展到更多学科

---

## 🎯 当前状态 (2025-10-05)

### ✅ Phase 4 已完成 (5/5 任务)

- [x] **TD-002 知识点提取优化** - ✅ 完成
  - 规则+AI 混合提取
  - jieba 中文分词集成
  - 3 个学科知识词典（22个知识点）
  - 13 个单元测试 (100%通过)

- [x] **TD-003 知识图谱数据导入** - ✅ 完成
  - 七年级数学知识图谱（25节点+18关系）
  - 数据格式规范和导入脚本
  - UUID 类型兼容性修复
  - 数据验证机制

- [x] **TD-005 答案质量评估** - ✅ 完成
  - 5维度评分系统
  - 规则/AI/混合评估策略
  - 人工反馈覆盖机制
  - 13 个单元测试 (100%通过)

- [x] **前端学习问答重构** - ✅ 完成
  - 通义千问极简风格
  - KaTeX 数学公式渲染
  - 三栏可折叠布局

- [x] **登录认证修复** - ✅ 完成
  - refresh_token 自动续期
  - Token 过期无缝刷新

### 🔥 当前任务 (Week 2)

**TD-006: MCP 上下文构建服务开发** (进行中)

- 目标: 实现基于精确数据库查询的个性化学情画像
- 预估工时: 16h (2-3天)
- 截止日期: 2025-10-08

### 📋 待办任务

**Week 2 剩余任务**:
- TD-007: 流式响应实现 (12h)
- TD-008: 请求缓存机制 (8h)

**Phase 5 任务** (Week 3-4):
- TD-009: 错题本功能 (16h)
- TD-010: 学情分析算法优化 (16h)
- TD-011: 知识图谱数据扩展 (24h)

**Phase 6 任务** (Week 5-8):
- TD-012: PGVector 扩展集成 (16h)
- TD-013: Embedding 服务对接 (8h)
- TD-014: 语义检索服务 (12h)
- TD-015: 混合检索策略 (12h)

## 🎯 本周具体任务 (Week 2, Day by Day)

### ✅ 周六 (10/05) - 已完成

- [x] TD-002 知识点提取优化 - ✅
- [x] TD-003 知识图谱数据导入 - ✅
- [x] TD-005 答案质量评估 - ✅
- [x] 文档体系重组 - ✅

### 🔥 周六 (10/06) - TD-006 Day 1

**目标**: 设计服务接口 + 实现薄弱知识点查询

**上午 (2h)**:
- [ ] 设计 `KnowledgeContextBuilder` 类结构
- [ ] 定义数据查询 SQL 逻辑
- [ ] 设计返回数据格式

**下午 (2h)**:
- [ ] 实现薄弱知识点查询（错误率 + 时间衰减）
- [ ] 编写初步单元测试

### 🔥 周日 (10/07) - TD-006 Day 2

**目标**: 实现其他查询 + 集成到服务层

**上午 (3h)**:
- [ ] 学习偏好查询
- [ ] 最近错题查询
- [ ] 知识点掌握度统计

**下午 (3h)**:
- [ ] 集成到 `LearningService`
- [ ] 集成到 `HomeworkService`
- [ ] 单元测试补充和性能测试

### 🔥 周一 (10/08) - TD-006 Day 3

**目标**: 端到端测试 + 文档提交

**上午 (3h)**:
- [ ] 使用真实数据测试
- [ ] 验证 AI 响应质量
- [ ] 边界情况测试

**下午 (3h)**:
- [ ] 编写技术文档
- [ ] 代码注释和 docstring
- [ ] Git 提交: `feat(mcp): 实现MCP上下文构建服务`

### 周二-周三 (10/09-10/10) - TD-007 & TD-008

**TD-007 流式响应** (12h):
- [ ] 后端 SSE 实现
- [ ] 前端 EventSource 集成
- [ ] 打字机效果

**TD-008 请求缓存** (8h):
- [ ] Redis 缓存策略
- [ ] 相似度匹配算法
- [ ] 缓存失效策略

---

## ✅ 今日行动清单 (2025-10-05)

### ✅ 已完成

- [x] TD-002 知识点提取优化 - 完成并提交
- [x] TD-003 知识图谱数据导入 - 完成并提交
- [x] TD-005 答案质量评估 - 完成并提交
- [x] 文档体系重组 - AI-CONTEXT.md, README.md, NEXT_STEPS.md 更新
- [x] Git 提交和推送

**成果**: Phase 4 核心任务全部完成！5/5 任务 (100%)

---

## 🔥 明日行动清单 (2025-10-06)

### TD-006: MCP 上下文构建服务 - Day 1

**目标**: 设计服务接口 + 实现薄弱知识点查询 (4h)

**上午 (2h)**:
- [ ] 设计 `KnowledgeContextBuilder` 类结构
- [ ] 定义数据查询 SQL 逻辑
- [ ] 设计返回数据格式

**下午 (2h)**:
- [ ] 实现薄弱知识点查询
  ```sql
  -- 查询薄弱知识点（错误率 + 时间衰减）
  SELECT 
      kn.id, kn.name, 
      COUNT(*) as error_count,
      AVG(CASE WHEN a.is_correct = False THEN 1 ELSE 0 END) as error_rate,
      -- 时间衰减权重: 近期错误权重更高
      SUM(
          CASE WHEN a.is_correct = False 
          THEN EXP(-EXTRACT(EPOCH FROM (NOW() - a.created_at)) / 2592000) -- 30天衰减
          ELSE 0 END
      ) as weighted_errors
  FROM answers a
  JOIN knowledge_nodes kn ON a.knowledge_point_id = kn.id
  WHERE a.user_id = $1 AND a.created_at > NOW() - INTERVAL '90 days'
  GROUP BY kn.id
  ORDER BY weighted_errors DESC
  LIMIT 5
  ```
- [ ] 编写初步单元测试

---

## �📖 参考资源

### 技术文档

- [jieba 中文分词](https://github.com/fxsjy/jieba) ✅
- [百炼 API 文档](https://help.aliyun.com/document_detail/2712195.html) ✅
- [知识图谱构建指南](docs/guide/knowledge-graph.md)

### 数据资源

- 人教版教材目录: http://www.pep.com.cn/
- 教育部课程标准: http://www.moe.gov.cn/
- K12 开源知识图谱: https://github.com/search?q=K12+knowledge+graph

### 项目文档

- [开发路线图](docs/DEVELOPMENT_ROADMAP.md) - 完整计划
- [项目状况分析](docs/PROJECT_DEVELOPMENT_STATUS.md) - 技术债务
- [AI 助手上下文](AI-CONTEXT.md) - 核心信息
- [TD-002 进度报告](docs/reports/TD-002-KNOWLEDGE-EXTRACTION-PROGRESS.md) ✅
- [TD-003 进度报告](docs/reports/TD-003-KNOWLEDGE-GRAPH-PROGRESS.md) ✅

---

## 🔔 提醒事项

### 重要原则

1. ✅ **每天提交代码**: 保持小步快跑，持续集成
2. ✅ **测试先行**: 先写测试，再写实现
3. ✅ **文档同步**: 代码和文档同步更新
4. ✅ **性能监控**: 关注提取时间，避免阻塞

### Git 提交规范

```bash
# 最近提交示例
git commit -m "feat(knowledge): 实现知识点提取服务基础框架"  # TD-002
git commit -m "fix(knowledge): 修复知识图谱导入中的 UUID 类型转换问题"  # TD-003

# TD-005 建议格式
git commit -m "feat(quality): 实现答案质量评估服务"
git commit -m "test(quality): 添加答案质量评估单元测试"
git commit -m "docs(quality): 添加 TD-005 技术进度报告"
```

### 开发节奏

- **小步快跑**: 每个 TD 任务 1-2 天完成
- **频繁提交**: 每完成一个子功能就提交
- **持续测试**: 边开发边测试，保证质量
- **文档同步**: 完成后立即写文档

---

## 📞 需要帮助?

### 技术问题

- 查看 [AI-CONTEXT.md](AI-CONTEXT.md) § 常见问题排查
- 运行诊断脚本: `uv run python scripts/diagnose.py`

### 设计问题

- 参考 [开发路线图](docs/DEVELOPMENT_ROADMAP.md) 详细方案
- 参考 [项目状况分析](docs/PROJECT_DEVELOPMENT_STATUS.md) 架构设计

### 其他问题

- 邮箱: maliguo@outlook.com
- 项目 Issues: GitHub Issues

---

## 🎯 里程碑

### ✅ Phase 4 已完成: 100% (5/5 任务)

- ✅ TD-002: 知识点提取优化
- ✅ TD-003: 知识图谱数据导入
- ✅ TD-005: 答案质量评估
- ✅ 前端学习问答重构
- ✅ 登录认证修复

### 🔥 Phase 4 当前任务: Week 2

- 🔥 TD-006: MCP 上下文构建服务 ← **当前任务**
- 📋 TD-007: 流式响应实现
- 📋 TD-008: 请求缓存机制

**🔥 目标**: 实现基于 MCP 的个性化学情上下文，为 RAG 系统打好基础！

### 📋 Phase 5-6 计划

- **Phase 5** (Week 3-4): 错题本 + 学情算法优化 + 知识图谱扩展
- **Phase 6** (Week 5-8): PGVector + Embedding + 语义检索 + 混合策略
