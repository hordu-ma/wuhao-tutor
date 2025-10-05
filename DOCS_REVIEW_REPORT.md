# 文档审查报告 - MCP+RAG 架构一致性检查

> **审查时间**: 2025-10-05  
> **审查目的**: 确保所有保留文档与 MCP+RAG 混合策略一致  
> **文档总数**: 25个（docs/）+ 3个（根目录）= 28个

---

## 📋 审查范围

### 根目录文档 (3个)
- ✅ README.md - 已更新
- ✅ AI-CONTEXT.md - 已更新  
- ✅ NEXT_STEPS.md - 已更新

### docs/ 子目录 (25个)
```
docs/
├── README.md (1)
├── architecture/ (4)
├── api/ (6)
├── guide/ (3)
├── integration/ (3)
├── miniprogram/ (4)
├── operations/ (1)
└── reference/ (3)
```

---

## 🔍 审查发现

### ⚠️ 需要更新的文档 (6个)

#### 1. **docs/architecture/overview.md** (高优先级)
**问题**:
- Line 152: 提到"引入向量检索/语义缓存"，但描述为"后续演进"
- Line 4: 更新时间为 2025-09-29，需要更新
- 缺少 MCP 上下文构建的描述
- 未明确说明 MCP+RAG 两阶段策略

**建议更新**:
```markdown
# 第 152 行附近 "AI 集成策略" 部分
| 上下文管理 | 依赖会话结构           | 引入向量检索 / 语义缓存       |
# 改为：
| 上下文管理 | Phase 4: MCP精确查询   | Phase 6: 引入RAG向量检索     |

# 增加新章节 "8.2 上下文构建策略"
## 8.2 上下文构建策略 (MCP + RAG 混合)

**Phase 4-5: MCP 上下文服务** (当前阶段)
- 基于精确SQL查询构建学情画像
- 薄弱知识点查询（错误率 + 时间衰减）
- 学习偏好分析
- 最近错题统计
- 知识点掌握度评估

**Phase 6: RAG 语义检索增强** (计划中)
- PGVector 向量数据库集成
- Embedding 服务对接（通义千问 API）
- 相似错题语义检索
- 历史问答语义检索
- MCP（精确）+ RAG（语义）混合检索策略
```

---

#### 2. **docs/reference/project-status.md** (中优先级)
**问题**:
- Line 3: 生成时间为 2025-10-03，信息过时
- Line 75: 知识图谱标注为 90%，实际已完成（七年级数学）
- 缺少 Phase 4 已完成任务（TD-002/003/005）
- 缺少当前任务（TD-006 MCP 上下文服务）

**建议更新**:
```markdown
# 更新生成时间
**生成时间**: 2025-10-05

# 更新 Phase 4 已完成工作
#### 已完成工作 ✅
- ✅ TD-002: 知识点提取优化（规则+AI混合）
- ✅ TD-003: 知识图谱数据导入（七年级数学25节点）
- ✅ TD-005: 答案质量评估（5维度评分）
- ✅ 前端学习问答重构（通义千问风格 + KaTeX）
- ✅ 登录认证修复（refresh_token 自动续期）

#### 进行中工作 🔄
- 🔥 TD-006: MCP 上下文构建服务（最高优先级）
- 📋 TD-007: 流式响应实现
- 📋 TD-008: 请求缓存机制

# 更新知识图谱状态
|| **学情分析** | 知识图谱 | ✅   | 100%    | 七年级数学数据已导入       |
```

---

#### 3. **docs/reference/glossary.md** (中优先级)
**问题**:
- 缺少 MCP、RAG、向量检索等新术语
- AI 术语部分需要补充

**建议更新**:
```markdown
# 在 "2. AI 相关术语" 部分增加：

|| MCP | Model Context Protocol | 基于精确数据库查询的上下文构建协议 | Phase 4-5 实现 |
|| RAG | Retrieval-Augmented Generation | 检索增强生成，结合向量检索和LLM | Phase 6 计划 |
|| 向量检索 | Vector Search | 基于语义相似度的检索技术 | 使用 PGVector 实现 |
|| Embedding | Embedding | 文本向量化表示 | 通义千问 Embedding API |
|| 语义检索 | Semantic Search | 理解语义的智能检索 | RAG 核心能力 |
|| 混合检索 | Hybrid Search | MCP（精确）+ RAG（语义）融合检索 | 最终目标架构 |
|| 时间衰减 | Time Decay | 近期数据权重更高的衰减算法 | MCP 查询策略 |
|| 知识点掌握度 | Knowledge Mastery Score | 基于错误率和时间衰减的掌握度评估 | MCP 输出指标 |
```

---

#### 4. **docs/guide/development.md** (低优先级)
**问题**: 
- 可能包含过时的技术栈描述
- 需要检查是否提到"向量数据库"或"RAG"，如果有需确保描述为"计划中"

**操作**: 快速扫描检查，如有提及需微调

---

#### 5. **docs/guide/deployment.md** (低优先级)
**问题**: 
- 部署文档可能需要提及 PGVector 扩展安装（当前可标注为"可选/Phase 6"）

**建议更新**:
```markdown
# 在数据库部分增加：
## PostgreSQL 扩展（可选）

### PGVector（Phase 6 - RAG 系统）
```bash
# 安装 PGVector 扩展（当前阶段可跳过）
# 在 PostgreSQL 数据库中执行：
CREATE EXTENSION IF NOT EXISTS vector;
```

**注意**: PGVector 扩展将在 Phase 6（RAG 增强系统）阶段使用，当前 Phase 4-5 阶段无需安装。
```

---

#### 6. **docs/README.md** (低优先级)
**问题**: 刚创建，但可以加入一行说明当前架构策略

**建议更新**:
```markdown
# 在"核心文档"部分增加一行：
- **[NEXT_STEPS.md](../NEXT_STEPS.md)** - 下一步开发任务
- **[架构策略](../README.md#核心特性)** - MCP 优先 + RAG 增强两阶段演进
```

---

### ✅ 无需更新的文档 (19个)

#### API 文档 (6个) - ✅ 无需更新
- `api/overview.md` - API 设计原则，与架构策略无关
- `api/endpoints.md` - 接口列表，无需更新
- `api/models.md` - 数据模型，无需更新
- `api/errors.md` - 错误码，无需更新
- `api/sdk-js.md` - JavaScript SDK，无需更新
- `api/sdk-python.md` - Python SDK，无需更新

#### 架构文档 (3个) - 部分需检查
- ⚠️ `architecture/overview.md` - **需要更新**（见上）
- ✅ `architecture/data-access.md` - 数据访问层，无需更新
- ✅ `architecture/security.md` - 安全策略，无需更新
- ✅ `architecture/observability.md` - 监控日志，无需更新

#### 开发指南 (3个) - 需快速扫描
- ⚠️ `guide/development.md` - **需快速检查**（见上）
- ⚠️ `guide/deployment.md` - **需微调**（见上）
- ✅ `guide/testing.md` - 测试指南，无需更新

#### 集成文档 (3个) - ✅ 无需更新
- `integration/frontend.md` - 前端集成，无需更新
- `integration/wechat-miniprogram.md` - 小程序开发，无需更新
- `integration/wechat-auth.md` - 微信认证，无需更新

#### 小程序文档 (4个) - ✅ 无需更新
- `miniprogram/api-integration.md` - API 对接，无需更新
- `miniprogram/network-architecture.md` - 网络架构，无需更新
- `miniprogram/user-role-system.md` - 用户角色，无需更新
- `miniprogram/MINIPROGRAM_FIXES.md` - 修复记录，无需更新

#### 运维文档 (1个) - ✅ 无需更新
- `operations/database-migration.md` - 数据库迁移，无需更新

#### 参考文档 (3个)
- ⚠️ `reference/project-status.md` - **需要更新**（见上）
- ⚠️ `reference/glossary.md` - **需要更新**（见上）
- ✅ `reference/learning-guide.md` - 学习指南，无需更新

---

## 📊 审查统计

| 类别           | 数量 | 比例  |
| -------------- | ---- | ----- |
| 需要更新       | 6个  | 21%   |
| 无需更新       | 19个 | 68%   |
| 需快速检查     | 3个  | 11%   |
| **文档总数**   | **28** | **100%** |

---

## 🎯 更新优先级

### 高优先级（必须更新）
1. ✅ `architecture/overview.md` - 架构核心文档，影响技术理解
2. ✅ `reference/project-status.md` - 项目状态，需反映最新进展

### 中优先级（建议更新）
3. ✅ `reference/glossary.md` - 术语表，补充新概念
4. ✅ `docs/README.md` - 导航文档，增加策略说明

### 低优先级（可选更新）
5. ⚠️ `guide/development.md` - 快速扫描检查
6. ⚠️ `guide/deployment.md` - 补充 PGVector 说明

---

## ✅ 行动建议

### 立即执行（本次）
1. 更新 `architecture/overview.md`
2. 更新 `reference/project-status.md`
3. 更新 `reference/glossary.md`
4. 微调 `docs/README.md`

### 后续优化（Week 2）
1. 扫描 `guide/development.md`
2. 补充 `guide/deployment.md` PGVector 说明
3. TD-006 完成后创建 MCP 架构专项文档

---

## 📝 备注

### 文档维护原则
1. ✅ 核心架构文档必须准确反映当前策略
2. ✅ API 和集成文档通常不受架构策略影响
3. ✅ 项目状态文档需要及时更新
4. ✅ 术语表是理解项目的关键文档

### 文档同步机制
- 每个 Phase 结束后审查核心文档
- 重大架构调整后立即更新相关文档
- 新概念出现时及时补充术语表

---

**审查完成时间**: 2025-10-05  
**下次审查**: Phase 4 完成后（预计 2025-10-12）
