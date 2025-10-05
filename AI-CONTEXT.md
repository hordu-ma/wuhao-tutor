# 五好伴学 - AI 助手上下文指南

> **🤖 AI 助手必读**  
> 本文档是与 AI 助手交互的核心上下文文件，包含项目关键信息、技术架构、开发约定和常用命令。

**最后更新**: 2025-10-05  
**项目版本**: 0.4.x (Phase 4 - 智能上下文增强)  
**整体状况**: B+ (良好) - 架构清晰，核心功能完备，采用 MCP+RAG 混合策略

---

## 🎯 项目核心信息

### 项目身份

- **名称**: 五好伴学 (Wuhao Tutor)
- **类型**: K12 AI 学情管理平台 (智能作业批改 + 个性化问答 + 学情分析)
- **路径**: `~/my-devs/python/wuhao-tutor`
- **维护者**: Liguo Ma <maliguo@outlook.com>

### 核心功能

1. **✅ 智能作业批改** - AI 驱动的作业自动评分与反馈 (完成度: 95%)
2. **✅ 学习问答互动** - 个性化学习问题解答 (完成度: 90%)
3. **⚠️ 学情分析反馈** - 学习数据分析与建议 (完成度: 70%)

### 当前开发状态 (2025-10-05)

| 维度           | 评分 | 说明                                  |
| -------------- | ---- | ------------------------------------- |
| **架构设计**   | A    | FastAPI + SQLAlchemy 2.x 异步架构清晰 |
| **代码质量**   | B+   | 类型安全，部分模块需重构              |
| **功能完整度** | B    | 核心功能完备，知识库建设不足          |
| **生产就绪度** | B-   | 缺少向量数据库和 RAG 实现             |
| **技术债务**   | B    | 可控范围内，需要专项优化              |

**关键改进项**:

- ✅ **TD-002 知识点提取优化** - 已完成（规则+AI混合提取）
- ✅ **TD-003 知识图谱数据导入** - 已完成（七年级数学25节点）
- ✅ **TD-005 答案质量评估** - 已完成（5维度评分系统）
- ✅ **前端学习问答页面已重构** - 采用通义千问极简风格
- ✅ **登录重复问题已修复** - refresh_token 机制正常工作
- 🔄 **MCP 上下文服务开发** - 进行中（优先级高）
- 📋 **RAG 向量检索系统** - 计划中（Phase 2）

**📋 参考文档**:

- **[项目开发状况深度分析](docs/PROJECT_DEVELOPMENT_STATUS.md)** - 技术债务审计 + 功能完整性检查
- **[前端重构总结](docs/FRONTEND_REFACTOR_SUMMARY.md)** - Learning.vue 重构成果

---

## 🏗️ 技术架构

### 技术栈全览

```yaml
后端:
  框架: FastAPI 0.104+
  ORM: SQLAlchemy 2.x (Async)
  验证: Pydantic v2
  语言: Python 3.11+

数据库:
  主库: PostgreSQL 14+ (生产) / SQLite (开发)
  缓存: Redis 6+
  向量库: 📋 计划集成 PGVector (Phase 2)

AI 服务:
  提供商: 阿里云百炼智能体
  模型: 通义千问
  功能: 作业批改 + 学习问答
  智能体架构: 单一智能体 + 场景参数化
  上下文策略: MCP 优先（精确查询）+ RAG 增强（语义检索）

前端:
  框架: Vue 3.4+ (Composition API)
  语言: TypeScript 5.6+
  UI: Element Plus 2.5+
  构建: Vite 5+
  状态: Pinia 2.1+
  数学公式: KaTeX + Marked

开发工具:
  Python: uv (包管理)
  Node.js: npm
  容器: Docker + Docker Compose

运维:
  反向代理: Nginx
  监控: Prometheus (配置已就绪)
  日志: 结构化日志 (JSON)
```

### 架构分层 (四层架构)

```
┌─────────────────────────────────────────────┐
│  API Layer (api/v1/endpoints/)             │  HTTP 请求处理
├─────────────────────────────────────────────┤
│  Service Layer (services/)                  │  业务逻辑
├─────────────────────────────────────────────┤
│  Repository Layer (repositories/)           │  数据访问
├─────────────────────────────────────────────┤
│  Model Layer (models/)                      │  ORM 数据模型
└─────────────────────────────────────────────┘

核心基础设施 (core/):
- config.py: 环境配置管理
- database.py: 数据库连接池
- security.py: 认证 + 限流
- monitoring.py: 性能监控
- logging.py: 结构化日志
```

**架构评价**: ⭐⭐⭐⭐⭐

- 层次分明，符合 DDD 思想
- 依赖倒置原则应用得当
- 异步编程实践规范

---

## 📂 项目目录结构

```
wuhao-tutor/
├── src/                      # 后端源码
│   ├── api/v1/endpoints/    # API 路由层
│   ├── services/            # 业务逻辑层
│   ├── repositories/        # 数据访问层
│   ├── models/              # ORM 数据模型
│   ├── schemas/             # Pydantic 数据验证
│   └── core/                # 核心基础设施
│
├── frontend/                 # Vue3 前端
│   ├── src/views/           # 页面组件
│   ├── src/stores/          # Pinia 状态管理
│   ├── src/api/             # API 封装
│   └── src/components/      # 可复用组件
│
├── miniprogram/             # 微信小程序
│   ├── pages/               # 页面
│   ├── api/                 # API 封装
│   └── utils/               # 工具函数
│
├── docs/                    # 📚 文档中心
│   ├── PROJECT_DEVELOPMENT_STATUS.md  # 开发状况深度分析
│   ├── FRONTEND_REFACTOR_SUMMARY.md   # 前端重构总结
│   ├── api/                 # API 文档
│   ├── architecture/        # 架构设计
│   ├── guide/               # 开发指南
│   ├── operations/          # 运维文档
│   └── reports/             # 技术报告
│
├── scripts/                 # 开发脚本
│   ├── diagnose.py          # 环境诊断
│   ├── init_database.py     # 数据库初始化
│   └── start-dev.sh         # 开发服务器启动
│
├── tests/                   # 测试套件
├── alembic/                 # 数据库迁移
├── config/                  # 配置模板
├── monitoring/              # 监控配置
├── nginx/                   # Nginx 配置
│
├── AI-CONTEXT.md            # 🤖 AI 助手上下文 (本文档)
├── README.md                # 📖 项目概述
├── pyproject.toml           # Python 项目配置
└── Makefile                 # 快捷命令
```

---

## 🔧 开发环境

### 必需工具

```bash
# Python 环境
Python 3.11+
uv (包管理器)

# Node.js 环境
Node.js 18+
npm 8+

# 数据库
PostgreSQL 14+ (生产) / SQLite (开发，已内置)
Redis 6+ (可选，用于限流缓存)

# 容器 (可选)
Docker + Docker Compose
```

### 快速启动

```bash
# 1. 环境诊断 (首次必运行)
uv run python scripts/diagnose.py

# 2. 安装依赖
uv sync                    # 后端依赖
cd frontend && npm install # 前端依赖

# 3. 配置环境变量
cp .env.dev .env
# 编辑 .env 配置 BAILIAN_API_KEY 等

# 4. 初始化数据库
make db-reset              # 重置数据库 + 示例数据

# 5. 启动开发服务器
./scripts/start-dev.sh     # 同时启动后端 + 前端

# 访问:
# - 后端 API: http://localhost:8000
# - API 文档: http://localhost:8000/docs
# - 前端界面: http://localhost:5173
```

### 常用 Make 命令

```bash
make help          # 查看所有命令
make dev           # 启动后端开发服务器
make test          # 运行测试套件
make lint          # 代码质量检查
make db-reset      # 重置数据库
make db-backup     # 备份数据库
make docker-dev    # Docker 开发环境
```

---

## 🔑 关键技术要点

### 1. 异步编程模式

**所有数据库操作和外部 API 调用必须使用 async/await**

```python
# ✅ 正确
async def ask_question(self, user_id: str, request: AskQuestionRequest):
    session = await self.repository.get_session(session_id)
    answer = await self.bailian_service.chat_completion(messages)

# ❌ 错误
def ask_question(self, user_id: str, request: AskQuestionRequest):
    session = self.repository.get_session(session_id)  # 阻塞调用!
```

### 2. 类型安全

**所有函数必须有完整的类型注解**

```python
# ✅ 正确
async def create_session(
    self,
    user_id: str,
    title: Optional[str] = None
) -> ChatSession:
    ...

# ❌ 错误
async def create_session(user_id, title=None):  # 缺少类型
    ...
```

### 3. 错误处理

**使用具体的异常类型，禁用裸 except**

```python
# ✅ 正确
try:
    result = await self.api_call()
except httpx.TimeoutException:
    raise ServiceError("服务请求超时")
except httpx.HTTPStatusError as e:
    raise ServiceError(f"HTTP 错误: {e.response.status_code}")

# ❌ 错误
try:
    result = await self.api_call()
except:  # 裸 except 会捕获所有异常
    raise ServiceError("调用失败")
```

### 4. 数据库事务管理

```python
# 使用 Repository 模式，事务在 Service 层管理
async with self.repository.transaction():
    session = await self.repository.create_session(data)
    await self.repository.create_question(question_data)
    # 自动提交或回滚
```

### 5. AI 服务调用

```python
# 通过 BailianService 统一调用
response = await self.bailian_service.chat_completion(
    messages=[
        {"role": "system", "content": "你是 K12 学习助手"},
        {"role": "user", "content": "问题内容"}
    ],
    context=ai_context,  # 包含学生档案和作业历史
    temperature=0.7,
    max_tokens=2000
)
```

---

## 📊 核心数据模型

### 用户相关

```python
User                 # 用户 (学生/教师/家长)
UserSession          # 用户登录会话
```

### 学习问答

```python
ChatSession          # 问答会话
Question             # 用户提问
Answer               # AI 回答
LearningAnalytics    # 学习分析数据
```

### 作业批改

```python
HomeworkSubmission   # 作业提交
HomeworkGrading      # 批改结果
```

### 知识图谱 (⚠️ 数据为空)

```python
KnowledgeNode        # 知识节点 (概念/技能/题型)
KnowledgeRelation    # 知识关系 (前置/包含/相似)
LearningPath         # 学习路径
UserLearningPath     # 用户学习进度
```

---

## 🚨 技术债务与改进方向

### ✅ 已完成 (Phase 4)

| ID         | 债务项                   | 完成时间   | 状态      |
| ---------- | ------------------------ | ---------- | --------- |
| ~~TD-002~~ | ~~知识点提取简化~~       | 2025-10-05 | ✅ 已完成 |
| ~~TD-003~~ | ~~知识图谱数据为空~~     | 2025-10-05 | ✅ 已完成 |
| ~~TD-004~~ | ~~学习问答页面交互复杂~~ | 2025-10-05 | ✅ 已完成 |
| ~~TD-005~~ | ~~答案质量评估缺失~~     | 2025-10-05 | ✅ 已完成 |

### 🔄 进行中 (Phase 4 - 当前)

| ID     | 任务项                     | 影响             | 预估工时 | 状态      |
| ------ | -------------------------- | ---------------- | -------- | --------- |
| TD-006 | **MCP 上下文构建服务**     | 个性化能力核心   | 16h      | 🔥 进行中 |
| TD-007 | **流式响应实现**           | 用户体验优化     | 12h      | 📋 待开发 |
| TD-008 | **请求缓存机制**           | 降低 AI 成本     | 8h       | 📋 待开发 |

### 📋 计划中 (Phase 5)

| ID     | 任务项                 | 预估工时 | 优先级 |
| ------ | ---------------------- | -------- | ------ |
| TD-009 | **错题本功能**         | 16h      | 中     |
| TD-010 | **学情分析算法优化**   | 16h      | 中     |
| TD-011 | **知识图谱数据扩展**   | 24h      | 中     |

### 🚀 未来增强 (Phase 6 - RAG 系统)

| ID     | 任务项                   | 预估工时 | 说明                     |
| ------ | ------------------------ | -------- | ------------------------ |
| TD-012 | **PGVector 扩展集成**    | 16h      | PostgreSQL 向量搜索      |
| TD-013 | **Embedding 服务对接**   | 8h       | 通义千问 Embedding API   |
| TD-014 | **语义检索服务**         | 12h      | 相似错题、历史问答检索   |
| TD-015 | **混合检索策略**         | 12h      | MCP + RAG 融合算法       |

### 技术债务详情

参见 **[PROJECT_DEVELOPMENT_STATUS.md § 7. 技术债务清单](docs/PROJECT_DEVELOPMENT_STATUS.md#7-技术债务清单)**

---

## 🎯 下一阶段开发重点

**🎯 核心策略**: **MCP 优先（精确查询）+ RAG 增强（语义检索）** 的两阶段演进路线

### ✅ Phase 4 已完成 (Week 1, 2025-10-05)

1. **✅ TD-002: 知识点提取优化** (已完成)
   - 规则引擎 + AI 混合提取
   - jieba 中文分词集成
   - 3 个学科知识词典（22 个知识点）
   - 13 个单元测试（100% 通过率）

2. **✅ TD-003: 知识图谱数据导入** (已完成)
   - 七年级数学知识图谱（25 节点 + 18 关系）
   - 数据格式规范和导入脚本
   - SQLite UUID 类型兼容性修复
   - 数据验证和增量更新机制

3. **✅ TD-005: 答案质量评估** (已完成)
   - 5 维度评分系统（准确性、完整性、相关性等）
   - 规则/AI/混合评估策略
   - 人工反馈覆盖机制
   - 13 个单元测试（100% 通过率）

4. **✅ 前端学习问答重构** (已完成)
   - 通义千问极简风格
   - KaTeX 数学公式渲染
   - 三栏可折叠布局

5. **✅ 登录认证修复** (已完成)
   - refresh_token 自动续期
   - Token 过期无缝刷新

### 🔥 Phase 4 当前任务 (Week 2, 2025-10-06~12)

**核心目标**: 实现 MCP 上下文服务，基于精确数据库查询构建个性化学情画像

6. **🔥 TD-006: MCP 上下文构建服务** (16h, 优先级最高)
   ```python
   # 核心功能
   class KnowledgeContextBuilder:
       async def build_context(user_id: str, subject: str) -> Dict:
           # 1. 查询薄弱知识点（错误率、时间衰减）
           # 2. 查询学习偏好（活跃学科、难度偏好）
           # 3. 查询最近错题（历史问题）
           # 4. 知识点掌握度统计
   ```
   - ✅ 实现 `KnowledgeContextBuilder` 服务
   - ✅ 集成到 `LearningService` 和 `HomeworkService`
   - ✅ 单元测试覆盖
   - ✅ 性能优化（查询耗时 < 50ms）

7. **TD-007: 流式响应实现** (12h)
   - 后端 SSE (Server-Sent Events)
   - 前端打字机效果
   - 优化等待体验

8. **TD-008: 请求缓存机制** (8h)
   - 基于问题相似度的缓存策略
   - 降低 AI 服务成本

### 📋 Phase 5: 体验优化 (Week 3-4)

9. **错题本功能** (TD-009, 16h)
   - 错题收集、分类、复习提醒
   - 知识点关联分析

10. **学情分析算法优化 (MCP 版)** (TD-010, 16h)
    - 艾宾浩斯遗忘曲线
    - 时间衰减权重算法
    - 知识点掌握度趋势分析

11. **知识图谱数据扩展** (TD-011, 24h)
    - 扩展到更多学科和年级
    - 完善知识点关系

### 🚀 Phase 6: RAG 增强系统 (Week 5-8)

**目标**: 在 MCP 精确查询基础上，增加语义相似检索能力

12. **🔥 PGVector 扩展集成** (TD-012, 16h)
    - 安装 PostgreSQL PGVector 扩展
    - 为 `answers` 表添加 `embedding` 列
    - 创建向量索引（IVFFLAT/HNSW）

13. **🔥 Embedding 服务对接** (TD-013, 8h)
    - 集成通义千问 Embedding API
    - 实现批量向量化服务
    - 历史数据向量化迁移

14. **🔥 语义检索服务** (TD-014, 12h)
    - 相似错题检索
    - 历史问答检索
    - 学科知识文档检索

15. **🔥 混合检索策略** (TD-015, 12h)
    - MCP（精确）+ RAG（语义）融合算法
    - 重排序策略（时间衰减 + 相似度）
    - A/B 测试框架

16. **前后端联调与测试** (8h)
    - 集成测试
    - 性能基准测试
    - 用户体验验证

### 🎯 Phase 7: 未来增强 (Week 9+)

17. 支持作业批量导入
18. 开发教师管理后台
19. 优化移动端体验
20. 多语言支持

---

## 📚 文档导航

### 核心文档

- **[README.md](README.md)** - 项目概述和快速开始
- **[PROJECT_DEVELOPMENT_STATUS.md](docs/PROJECT_DEVELOPMENT_STATUS.md)** - 开发状况深度分析 ⭐
- **[FRONTEND_REFACTOR_SUMMARY.md](docs/FRONTEND_REFACTOR_SUMMARY.md)** - 前端重构总结

### 技术文档

- **[API 文档](docs/api/)** - RESTful API 接口文档
- **[架构设计](docs/architecture/)** - 系统架构和设计模式
- **[开发指南](docs/guide/)** - 开发规范和最佳实践
- **[运维文档](docs/operations/)** - 部署和监控指南

### 参考文档

- **[术语表](docs/reference/glossary.md)** - 项目术语定义
- **[学习指南](docs/reference/learning-guide.md)** - 技术学习资源

### 历史文档

- **[技术报告](docs/reports/)** - 历史技术报告和分析
- **[归档文档](docs/archived/)** - 已过时的历史文档

---

## 🐛 常见问题排查

### 问题 1: 后端启动失败

```bash
# 检查环境配置
uv run python scripts/diagnose.py

# 查看详细错误
uv run uvicorn src.main:app --reload --log-level debug
```

### 问题 2: 数据库连接失败

```bash
# 重置数据库
make db-reset

# 检查数据库配置
cat .env | grep SQLALCHEMY_DATABASE_URI
```

### 问题 3: 前端 API 调用 401 或重复登录

```bash
# 检查 token 是否保存
# 浏览器控制台执行:
localStorage.getItem('access_token')
localStorage.getItem('refresh_token')  # ✅ 2025-10-05 已修复

# 如果 refresh_token 为空，清除缓存重新登录:
localStorage.clear()
sessionStorage.clear()
```

### 问题 4: AI 服务调用失败

```bash
# 检查 API Key 配置
cat .env | grep BAILIAN_API_KEY

# 查看服务日志
tail -f logs/app.log
```

### 问题 5: 数学公式不显示

```bash
# 检查 KaTeX 依赖
cd frontend && npm list katex marked

# 重新安装依赖
npm install

# 参考文档: frontend/MATH_FORMULA_TEST.md
```

---

## 💡 开发约定

### Git 提交规范

```bash
# 格式: type(scope): description

feat(api): 添加学习路径推荐接口
fix(auth): 修复 refresh_token 未保存问题 ✅
refactor(learning): 重构学习问答页面为通义千问风格 ✅
docs(readme): 更新项目状态和技术栈说明
test(homework): 添加作业批改单元测试
chore(deps): 更新依赖版本
```

### 代码质量标准

- ✅ 所有代码必须通过 Black (Python) / Prettier (TypeScript) 格式化
- ✅ 所有函数必须有类型注解
- ✅ 核心功能必须有单元测试 (目标覆盖率 80%)
- ✅ 复杂算法必须有时间/空间复杂度注释
- ✅ 优先正确性和可读性，性能瓶颈出现后再优化

### 前端组件规范

- 使用 Vue 3 Composition API (`<script setup>`)
- 状态管理使用 Pinia
- 响应式数据优先使用 `ref`，对象使用 `reactive`
- 组件文件命名: PascalCase (如 `Learning.vue`)
- Markdown 渲染使用 marked + KaTeX (数学公式)

---

## 🔐 安全与性能

### 已实现安全措施

- ✅ JWT 认证机制 (access_token + refresh_token) ✨ 2025-10-05 修复
- ✅ 多维限流 (IP/用户/AI 服务)
- ✅ SQL 注入防护 (ORM 参数化)
- ✅ XSS 防护 (输入验证)
- ✅ CSRF 防护 (Token)
- ✅ 安全响应头 (CSP、HSTS)

### 性能监控指标

- API 响应时间: P95 < 200ms ✅
- 数据库查询: P95 < 50ms ✅
- AI 服务调用: P95 < 3s ✅

---

## 📞 支持与反馈

- **邮箱**: maliguo@outlook.com
- **文档问题**: 在 GitHub Issues 中提出
- **紧急问题**: 查看 `scripts/diagnose.py` 诊断报告

---

**AI 助手注意事项**:

1. 所有路径操作使用绝对路径: `/Users/liguoma/my-devs/python/wuhao-tutor/...`
2. Python 命令使用 `uv run python` 而不是直接 `python`
3. 修改代码前检查 `docs/PROJECT_DEVELOPMENT_STATUS.md` 了解当前状态
4. 遇到技术债务问题，参考该文档的改进建议
5. 前端问题参考 `docs/FRONTEND_REFACTOR_SUMMARY.md`
6. 登录/认证问题参考 `frontend/LOGIN_FIX_SUMMARY.md`

**最后更新**: 2025-10-05 by AI Agent  
**下次更新**: 完成 MCP 上下文服务后 (预计 Week 2)  
**核心策略**: MCP 优先（精确查询）→ RAG 增强（语义检索）两阶段演进  
**当前焦点**: TD-006 MCP 上下文构建服务开发
