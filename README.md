# 五好伴学 (Wuhao Tutor)

> 基于阿里云百炼智能体的 K12 智能学习支持平台  
> 智能作业批改 + 个性化学习问答 + 全面学情分析

一个现代化的教育科技平台，利用 AI 技术为 K12 学生提供智能作业批改、个性化学习问答和全面的学情分析服务。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D.svg)
![Status](https://img.shields.io/badge/status-Phase_4-green.svg)

---

## 📊 项目状态总览

**当前版本**: 0.4.x (Phase 4 - 生产部署优化)  
**整体状况**: **B+ (良好)** - 架构清晰，核心功能完备，待优化 RAG 系统  
**最后更新**: 2025-10-05

| 维度           | 评分 | 说明                         |
| -------------- | ---- | ---------------------------- |
| **架构设计**   | A    | 四层架构清晰，异步编程规范   |
| **代码质量**   | B+   | 类型安全，部分模块需重构     |
| **功能完整度** | B    | 核心功能完备，知识库建设不足 |
| **生产就绪度** | B-   | 缺少向量数据库和 RAG 实现    |
| **技术债务**   | B    | 可控范围内，需要专项优化     |

### 📋 核心文档

- **[📊 项目开发状况深度分析](docs/PROJECT_DEVELOPMENT_STATUS.md)** ⭐ - 技术债务审计 + 功能完整性检查 + 下一阶段规划
- **[🎨 前端重构总结](docs/FRONTEND_REFACTOR_SUMMARY.md)** - Learning.vue 通义千问风格重构成果
- **[🤖 AI 助手上下文](AI-CONTEXT.md)** - AI 协作必读的项目核心信息
- **[📚 文档中心](docs/README.md)** - 完整的项目文档导航

### 🎯 最近更新 (2025-10-05)

- ✅ **Learning.vue 重构完成** - 采用通义千问极简风格，三栏可折叠布局
- ✅ **数学公式渲染支持** - 集成 KaTeX + Marked，支持行内和块级公式
- ✅ **登录重复问题修复** - refresh_token 机制正常工作，自动续期
- ✅ **文档体系重组** - 完成项目开发状况深度分析报告

---

## ✨ 核心特性

### 🤖 智能作业批改 (完成度: 95%)

- **✅ AI 驱动评分**：基于阿里云百炼智能体的自动批改系统
- **✅ 多维度反馈**：提供详细的评分解释和改进建议
- **✅ 多媒体支持**：支持文本、图片等多种作业形式
- **⚠️ 知识点提取**: 当前为关键词匹配，计划使用 NLP/LLM 提取

### 💬 智能学习问答 (完成度: 90%)

- **✅ 对话式学习**：自然语言交互，个性化解答学习疑问
- **✅ 上下文记忆**：维持连贯的对话会话，深度理解学习需求
- **✅ 数学公式支持**: KaTeX 渲染，支持 LaTeX 语法
- **✅ 通义千问风格**: 极简交互，三栏可折叠布局
- **⚠️ 缺少向量检索**: 无法检索历史相似问题 (计划集成 RAG)

### 📊 学情分析 (完成度: 70%)

- **✅ 学习数据统计**：全面的学习活跃度和频次分析
- **✅ 知识掌握评估**：智能推断学生对不同知识点的掌握程度
- **✅ 个性化建议**：基于数据分析提供针对性学习建议
- **⚠️ 算法简化**: 仅计数统计，未考虑遗忘曲线和时间衰减
- **❌ 知识图谱为空**: 表结构完整但无数据

### 🔒 企业级特性

- **✅ 多维限流保护**：IP/用户/AI 服务多层限流机制
- **✅ 安全头配置**：CSP、HSTS 等完整安全策略
- **✅ 性能监控**：实时性能指标收集和慢查询监控
- **✅ 结构化日志**：便于问题排查和系统优化
- **✅ JWT 双 Token 认证**: access_token + refresh_token 自动续期

---

## 🏗️ 技术架构

### 技术栈

```yaml
后端:
  框架: FastAPI 0.104+ (异步高性能)
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
  公式: KaTeX + Marked

开发工具:
  Python: uv (快速包管理)
  Node.js: npm
  容器: Docker + Docker Compose

运维:
  反向代理: Nginx
  监控: Prometheus (配置已就绪)
  日志: 结构化日志 (JSON)
```

### 四层架构设计

```
┌─────────────────────────────────────────────┐
│  API Layer (api/v1/endpoints/)             │ → HTTP 请求处理
├─────────────────────────────────────────────┤
│  Service Layer (services/)                  │ → 业务逻辑
├─────────────────────────────────────────────┤
│  Repository Layer (repositories/)           │ → 数据访问
├─────────────────────────────────────────────┤
│  Model Layer (models/)                      │ → ORM 数据模型
└─────────────────────────────────────────────┘

核心基础设施 (core/):
├── config.py       # 环境配置管理
├── database.py     # 数据库连接池
├── security.py     # 认证 + 限流
├── monitoring.py   # 性能监控
└── logging.py      # 结构化日志
```

**架构评价**: ⭐⭐⭐⭐⭐ 层次分明，符合 DDD 思想，异步编程实践规范

---

## 🚀 快速开始

### 环境要求

```bash
# 必需
Python 3.11+
Node.js 18+
uv (Python 包管理器)

# 可选
PostgreSQL 14+ (生产环境)
Redis 6+ (缓存和限流)
Docker + Docker Compose
```

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd wuhao-tutor
```

#### 2. 环境诊断 (首次必运行)

```bash
uv run python scripts/diagnose.py
```

这会检查：

- ✅ Python 版本和依赖
- ✅ Node.js 环境
- ✅ 数据库连接
- ✅ Redis 连接 (可选)
- ✅ 环境变量配置

#### 3. 安装依赖

```bash
# 后端依赖
uv sync

# 前端依赖
cd frontend
npm install
```

#### 4. 配置环境变量

```bash
cp .env.dev .env
# 编辑 .env 配置以下关键变量:
# - BAILIAN_API_KEY: 阿里云百炼 API 密钥
# - BAILIAN_APPLICATION_ID: 百炼应用 ID
# - SECRET_KEY: JWT 密钥 (可自动生成)
```

#### 5. 初始化数据库

```bash
make db-reset   # 重置数据库 + 创建示例用户
# 默认测试账号: 13800000001 / password123
```

#### 6. 启动开发服务器

```bash
# 方法 1: 使用启动脚本 (推荐)
./scripts/start-dev.sh    # 同时启动后端 + 前端

# 方法 2: 分别启动
make dev                  # 后端 (端口 8000)
cd frontend && npm run dev # 前端 (端口 5173)
```

#### 7. 访问应用

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs (Swagger UI)
- **备用 API 文档**: http://localhost:8000/redoc

---

## 📖 开发指南

### 常用命令

```bash
# 开发
make dev           # 启动后端开发服务器
make test          # 运行测试套件
make lint          # 代码质量检查 (black + flake8 + mypy)

# 数据库
make db-reset      # 重置数据库 + 示例数据
make db-backup     # 备份数据库
make db-migrate    # 运行数据库迁移

# Docker
make docker-dev    # Docker 开发环境
make docker-prod   # Docker 生产环境

# 清理
make clean         # 清理临时文件
make help          # 查看所有命令
```

### 项目结构

```
wuhao-tutor/
├── src/                      # 后端源码
│   ├── api/v1/endpoints/    # API 路由
│   ├── services/            # 业务逻辑
│   ├── repositories/        # 数据访问
│   ├── models/              # 数据模型
│   └── core/                # 核心基础设施
│
├── frontend/                 # Vue3 前端
│   ├── src/views/           # 页面组件
│   ├── src/stores/          # Pinia 状态
│   └── src/api/             # API 封装
│
├── docs/                    # 📚 文档中心
│   ├── PROJECT_DEVELOPMENT_STATUS.md   ⭐ 开发状况深度分析
│   ├── FRONTEND_REFACTOR_SUMMARY.md    前端重构总结
│   ├── api/                 # API 文档
│   ├── architecture/        # 架构设计
│   ├── guide/               # 开发指南
│   └── operations/          # 运维文档
│
├── scripts/                 # 开发脚本
│   ├── diagnose.py          # 环境诊断
│   ├── init_database.py     # 数据库初始化
│   └── start-dev.sh         # 开发服务器
│
├── tests/                   # 测试套件
├── alembic/                 # 数据库迁移
├── AI-CONTEXT.md            # 🤖 AI 助手上下文
└── README.md                # 📖 本文档
```

### 开发规范

#### Git 提交规范

```bash
feat(api): 添加学习路径推荐接口
fix(auth): 修复 refresh_token 未保存问题
refactor(learning): 重构学习问答页面为通义千问风格
docs(readme): 更新项目状态和技术栈说明
test(homework): 添加作业批改单元测试
chore(deps): 更新依赖版本
```

#### 代码质量标准

- ✅ 所有 Python 代码使用 Black 格式化
- ✅ 所有 TypeScript 代码使用 Prettier 格式化
- ✅ 所有函数必须有类型注解
- ✅ 核心功能必须有单元测试 (目标覆盖率 80%)
- ✅ 优先正确性和可读性，瓶颈出现后再优化

---

## 🚨 已知问题与改进方向

### 高优先级技术债务

| ID         | 债务项                   | 影响             | 预估工时 | 状态      |
| ---------- | ------------------------ | ---------------- | -------- | --------- |
| TD-001     | **RAG 系统缺失**         | 核心卖点无法实现 | 40h      | ⚠️ 计划中 |
| TD-002     | **知识点提取简化**       | 学情分析不准确   | 24h      | ⚠️ 计划中 |
| TD-003     | **知识图谱数据为空**     | 无法推荐学习路径 | 16h      | ⚠️ 计划中 |
| ~~TD-004~~ | ~~学习问答页面交互复杂~~ | ~~用户体验差~~   | 16h      | ✅ 已修复 |

### 下一步开发计划 (Week 1-4)

1. **🔥 实现 RAG 知识库系统** (Week 1-2)

   - 集成 PGVector 向量数据库
   - 使用通义千问 Embedding API
   - 实现混合检索 (语义+关键词)

2. **🔥 优化知识点提取** (Week 2-3)

   - 集成 NLP 库或调用百炼 API
   - 建立学科知识点标准库
   - 实现知识点置信度评分

3. **🔥 初始化知识图谱数据** (Week 3-4)
   - 导入 K12 各学科知识点
   - 构建知识点关联关系
   - 生成学习路径模板

详细信息参见 **[项目开发状况深度分析](docs/PROJECT_DEVELOPMENT_STATUS.md)**

---

## 📚 文档资源

### 核心文档

- **[📊 项目开发状况深度分析](docs/PROJECT_DEVELOPMENT_STATUS.md)** ⭐ - 技术债务审计 + 下一阶段规划
- **[🎨 前端重构总结](docs/FRONTEND_REFACTOR_SUMMARY.md)** - Learning.vue 重构成果
- **[🤖 AI 助手上下文](AI-CONTEXT.md)** - AI 协作必读

### 技术文档

- **[API 文档](docs/api/)** - RESTful API 接口文档
- **[架构设计](docs/architecture/)** - 系统架构和设计模式
- **[开发指南](docs/guide/)** - 开发规范和最佳实践
- **[运维文档](docs/operations/)** - 部署和监控指南

### 参考资料

- **[术语表](docs/reference/glossary.md)** - 项目术语定义
- **[学习指南](docs/reference/learning-guide.md)** - 技术学习资源
- **[技术报告](docs/reports/)** - 历史技术报告和分析

---

## 🐛 故障排查

### 常见问题

#### 1. 后端启动失败

```bash
# 运行环境诊断
uv run python scripts/diagnose.py

# 查看详细错误
uv run uvicorn src.main:app --reload --log-level debug
```

#### 2. 数据库连接失败

```bash
# 重置数据库
make db-reset

# 检查配置
cat .env | grep SQLALCHEMY_DATABASE_URI
```

#### 3. 前端重复要求登录

```bash
# 检查 token 保存 (浏览器控制台)
localStorage.getItem('access_token')
localStorage.getItem('refresh_token')

# 如果缺失，清除缓存重新登录
localStorage.clear()
sessionStorage.clear()

# 参考文档: frontend/LOGIN_FIX_SUMMARY.md
```

#### 4. 数学公式不显示

```bash
# 检查依赖
cd frontend && npm list katex marked

# 重新安装
npm install

# 参考文档: frontend/MATH_FORMULA_TEST.md
```

#### 5. AI 服务调用失败

```bash
# 检查 API Key
cat .env | grep BAILIAN_API_KEY

# 查看日志
tail -f logs/app.log
```

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！请查看以下资源：

- **[开发指南](docs/guide/)** - 开发规范和最佳实践
- **[架构设计](docs/architecture/)** - 了解系统设计
- **[技术债务清单](docs/PROJECT_DEVELOPMENT_STATUS.md#7-技术债务清单)** - 待改进项

### 提交流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'feat(scope): 添加某功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👥 团队与支持

- **项目维护者**: Liguo Ma
- **邮箱**: maliguo@outlook.com
- **技术支持**: 查看 `scripts/diagnose.py` 诊断报告

---

## 🎯 路线图

### Phase 4 (当前阶段)

- ✅ 前端学习问答页面重构 (通义千问风格)
- ✅ 数学公式渲染支持 (KaTeX)
- ✅ 登录重复问题修复 (refresh_token)
- ✅ 文档体系重组
- 🔄 RAG 知识库系统实现 (进行中)

### Phase 5 (计划中)

- 知识点智能提取优化
- 知识图谱数据导入
- 流式响应实现
- 学情分析算法优化

### Phase 6 (未来)

- 错题本功能
- 教师管理后台
- 移动端优化
- 多语言支持

详细路线图参见 **[项目开发状况深度分析](docs/PROJECT_DEVELOPMENT_STATUS.md)**

---

## 🌟 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python ORM
- [Element Plus](https://element-plus.org/) - Vue 3 UI 组件库
- [Pinia](https://pinia.vuejs.org/) - Vue 状态管理
- [阿里云百炼](https://www.aliyun.com/product/bailian) - AI 智能体服务

---

**最后更新**: 2025-10-05  
**项目版本**: 0.4.x  
**整体状况**: B+ (良好)

**🔥 下一步**: 实现 RAG 知识库系统，提升问答质量和个性化程度！
