# 五好伴学 - AI 助手上下文指南

> **🤖 AI 助手必读**  
> 本文档是与 AI 助手交互的核心上下文文件，包含项目关键信息、技术架构、开发约定和常用命令。

**最后更新**: 2025-10-05  
**项目版本**: 0.4.x (Phase 4 - 生产部署优化)  
**整体状况**: B+ (良好) - 架构清晰，核心功能完备，待优化 RAG 系统

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

**关键待改进项**:

- ⚠️ **RAG 系统缺失** - 缺少向量数据库集成(PGVector/Milvus/Chroma)
- ⚠️ **知识点提取简化** - 仅基于关键词匹配，未使用 NLP/LLM 提取
- ⚠️ **知识图谱数据为空** - 表结构完整但无数据
- ✅ **前端学习问答页面已重构** - 采用通义千问极简风格
- ✅ **登录重复问题已修复** - refresh_token 机制正常工作

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
  向量库: ❌ 未集成 (计划: PGVector)

AI 服务:
  提供商: 阿里云百炼智能体
  模型: 通义千问
  功能: 作业批改 + 学习问答

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

## 🚨 已知技术债务与改进方向

### 高优先级 (Critical)

| ID         | 债务项                   | 影响             | 预估工时 | 状态      |
| ---------- | ------------------------ | ---------------- | -------- | --------- |
| TD-001     | **RAG 系统缺失**         | 核心卖点无法实现 | 40h      | ⚠️ 待开发 |
| TD-002     | **知识点提取简化**       | 学情分析不准确   | 24h      | ⚠️ 待开发 |
| TD-003     | **知识图谱数据为空**     | 无法推荐学习路径 | 16h      | ⚠️ 待开发 |
| ~~TD-004~~ | ~~学习问答页面交互复杂~~ | ~~用户体验差~~   | 16h      | ✅ 已修复 |

### 中优先级

- TD-005: 答案质量评估缺失 (8h)
- TD-006: 流式响应未实现 (12h)
- TD-007: 请求缓存未实现 (8h)
- TD-008: 错题本功能缺失 (16h)

### 技术债务详情

参见 **[PROJECT_DEVELOPMENT_STATUS.md § 7. 技术债务清单](docs/PROJECT_DEVELOPMENT_STATUS.md#7-技术债务清单)**

---

## 🎯 下一阶段开发重点

**🎯 开发策略调整**: 基于技术风险和价值交付考虑，**RAG 系统后置开发**，优先完成其他高价值功能。

### 第一批：快速价值交付 (Week 1-2, 约 3 周)

1. **✅ 前端学习问答页面重构** (已完成 2025-10-05)

   - 采用通义千问极简风格
   - 三栏可折叠布局
   - 移除强制创建会话流程
   - 添加 KaTeX 数学公式渲染

2. **✅ 修复登录重复问题** (已完成 2025-10-05)

   - 添加 refresh_token 保存和恢复
   - Token 过期自动刷新
   - 优化认证状态管理

3. **🔥 知识点提取优化** (TD-002, 24h) - 下一步

   - 集成 NLP 库或调用百炼 API 提取
   - 建立学科知识点标准库
   - 实现置信度评分机制

4. **🔥 知识图谱数据导入** (TD-003, 16h)

   - 导入 K12 数学/语文/英语知识点
   - 建立知识点关联关系
   - 生成学习路径模板

5. **答案质量评估机制** (TD-005, 8h)
   - 实现准确性、完整性、适龄性评分
   - 支持人工反馈学习

### 第二批：体验优化 (Week 3-4, 约 2 周)

6. **流式响应实现** (TD-006, 12h)

   - 后端 SSE (Server-Sent Events)
   - 前端打字机效果
   - 优化等待体验

7. **请求缓存机制** (TD-007, 8h)

   - 基于问题相似度的缓存策略
   - 降低 AI 服务成本

8. **错题本功能** (TD-008, 16h)

   - 错题收集、分类、复习提醒
   - 知识点关联分析

9. **学情分析算法优化 (基础版)** (16h)
   - 艾宾浩斯遗忘曲线
   - 时间衰减权重
   - 知识点掌握度趋势

### 第三批：RAG 核心战役 (Week 5-8, 约 4 周)

10. **🔥 向量数据库集成 (PGVector)** (16h)

    - 安装 PostgreSQL PGVector 扩展
    - 创建向量表和索引
    - 实现基础检索功能

11. **🔥 Embedding 服务对接** (8h)

    - 集成通义千问 Embedding API
    - 实现文本向量化服务

12. **🔥 知识片段管理** (12h)

    - 错题向量化存储
    - 优质 QA 对向量化
    - 学科知识向量化

13. **🔥 检索策略实现** (12h)

    - 混合检索 (语义+关键词+时间衰减)
    - 重排序算法
    - 上下文注入优化

14. **🔥 前后端联调与测试** (8h)
    - 集成测试
    - 性能优化
    - 用户体验验证

### 第四批：RAG 增强优化 (Week 9+)

15. **学情分析算法优化 (RAG 增强版)** (12h)

    - 基于语义相似度的知识点关联
    - 个性化学习路径推荐

16. 支持作业批量导入
17. 开发教师管理后台
18. 优化移动端体验

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
**下次更新**: 完成第一批开发任务后 (预计 Week 3)  
**开发策略**: RAG 后置开发，优先完成知识点提取、知识图谱数据、体验优化
