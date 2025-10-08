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

**当前版本**: 0.4.x (Phase 4 - 智能上下文增强)  
**整体状况**: **A- (优秀)** - 核心功能完整，MCP+Analytics 全面上线，向 RAG 增强演进  
**最后更新**: 2025-10-06

| 维度           | 评分 | 说明                         |
| -------------- | ---- | ---------------------------- |
| **架构设计**   | A    | 四层架构清晰，异步编程规范   |
| **代码质量**   | A-   | 类型安全，测试覆盖率 80%+    |
| **功能完整度** | A-   | 核心功能完整，学情分析全面   |
| **生产就绪度** | B+   | 性能优化完成，RAG 系统计划中 |
| **技术债务**   | A    | 主要债务已清理，系统稳定     |

### 核心文档

- **[� 全链条对齐开发补齐计划](docs/development/COMPREHENSIVE_TODO_PLAN.md)** ⭐ - 最新开发状态与任务计划
- **[📊 代码对齐分析报告](docs/reports/CODE_ALIGNMENT_ANALYSIS.md)** - 全链路对齐度分析
- **[🎨 前端重构总结](docs/FRONTEND_REFACTOR_SUMMARY.md)** - Learning.vue 通义千问风格重构成果
- **[🤖 AI 助手上下文](AI-CONTEXT.md)** - AI 协作必读的项目核心信息
- **[📚 文档中心](docs/README.md)** - 完整的项目文档导航

### 🎯 最近更新 (2025-10-06)

**🎉 Phase 4 重大突破完成：**

- ✅ **TD-006: MCP 上下文服务全面上线** - 个性化学情分析完整实现
  - 薄弱知识点智能识别（时间衰减算法）
  - 学习偏好多维度分析（5 个维度）
  - AI 服务深度集成，响应质量显著提升
  - 21 个单元测试全部通过
- ✅ **作业 API 重构完成** - 从硬编码到生产就绪
  - 4 个核心端点完全重构，告别假数据
  - 数据库性能优化（7 个复合索引，查询效率提升 50-90%）
  - 前端兼容性 API 层，平滑迁移
  - 多格式输出支持（JSON/Markdown/HTML）
- ✅ **前端错误处理修复** - 用户体验显著提升
  - 完全消除 8 个 Promise.reject 崩溃点
  - 创建统一错误处理机制
  - 实现友好的"功能开发中"提示组件
- ✅ **基础学情分析 API 上线** - 核心数据分析功能完整
  - 3 个核心 Analytics API 端点（学习进度、知识点掌握、学科统计）
  - 复杂时间序列数据聚合与分析算法
  - 完整的 Service + Repository 架构层
  - API 文档和 Swagger UI 集成完成
- 🔄 **当前重点**: 错题本功能开发（TD-009）

---

## ✨ 核心特性

### 🤖 智能作业批改 (完成度: 98%)

- **✅ AI 驱动评分**：基于阿里云百炼智能体的自动批改系统
- **✅ 多维度反馈**：提供详细的评分解释和改进建议
- **✅ 多媒体支持**：支持文本、图片等多种作业形式
- **✅ 知识点提取**: 规则+AI 混合提取，准确率高
- **✅ 答案质量评估**: 5 维度评分，支持人工反馈学习
- **✅ 作业历史查询**: 完整的提交历史和批改结果管理
- **✅ 统计分析**: 时间趋势、正确率分析、学科分布统计

### 💬 智能学习问答 (完成度: 95%)

- **✅ 对话式学习**：自然语言交互，个性化解答学习疑问
- **✅ 上下文记忆**：维持连贯的对话会话，深度理解学习需求
- **✅ 数学公式支持**: KaTeX 渲染，支持 LaTeX 语法
- **✅ 通义千问风格**: 极简交互，三栏可折叠布局
- **✅ MCP 上下文服务**: 基于个人学情的智能上下文构建
  - 薄弱知识点识别（时间衰减算法）
  - 学习偏好分析（5 个维度）
  - 历史错题关联分析
- **📋 RAG 语义检索**: 计划中（Phase 6），用于相似问题/错题检索

### 📊 学情分析 (完成度: 85%)

- **✅ 学习数据统计**：全面的学习活跃度和频次分析
- **✅ 知识图谱数据**: 已导入七年级数学知识点（25 节点+18 关系）
- **✅ 个性化建议**：基于数据分析提供针对性学习建议
- **✅ 核心分析 API**: 3 个核心端点全面上线
  - 学习进度分析（时长、完成率、正确率趋势）
  - 知识点掌握情况（掌握度统计、关联分析）
  - 学科统计分析（学习时长、平均分、提升趋势）
- **✅ 时间序列分析**: 支持日/周/月多粒度数据聚合
- **✅ 性能优化**: 7 个数据库索引，查询效率提升 60%+
- **🔄 错题本功能**: 开发中（TD-009）
- **📋 算法优化**: 计划引入遗忘曲线和时间衰减权重（Phase 5）

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
  向量库: 📋 计划集成 PGVector (Phase 6)

AI 服务:
  提供商: 阿里云百炼智能体
  模型: 通义千问
  功能: 作业批改 + 学习问答
  智能体架构: 单一智能体 + 场景参数化
  上下文策略: MCP优先（精确查询）+ RAG增强（语义检索）

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

部署:
  生产环境: Python + systemd + Nginx
  开发环境: 本地 Python 进程

运维:
  进程管理: systemd (wuhao-tutor.service)
  反向代理: Nginx (HTTPS/SSL)
  监控: Prometheus (配置已就绪)
  日志: journald + 结构化日志 (JSON)
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

## 🚨 当前开发重点与计划

### ✅ Phase 4 重大成果（已完成）

**🎉 核心功能完整上线，系统稳定性显著提升**

| 任务                       | 状态      | 实际工时 | 主要成果                                    |
| -------------------------- | --------- | -------- | ------------------------------------------- |
| **TD-006: MCP 上下文服务** | ✅ 已完成 | 13.5h    | 个性化学情分析完整实现，21 个单元测试全通过 |
| **作业 API 重构**          | ✅ 已完成 | 12h      | 4 个核心端点重构，性能提升 50-90%           |
| **前端错误处理修复**       | ✅ 已完成 | 3h       | 消除 8 个崩溃点，统一错误处理机制           |
| **基础学情分析 API**       | ✅ 已完成 | 12h      | 3 个核心分析端点，复杂数据聚合算法          |

**重要里程碑**：

- 🎯 **技术债务清理完成**：主要硬编码数据已消除，系统稳定性大幅提升
- 🎯 **MCP 个性化能力上线**：AI 服务质量显著提升，基于学情的智能上下文
- 🎯 **数据分析功能完整**：学习进度、知识点掌握、学科统计全面可用
- 🎯 **前端用户体验优化**：错误处理完善，崩溃问题彻底解决

### 🔄 当前任务（Week 2-3）

**核心目标**: 完成错题本功能，为用户提供完整的学习闭环

| ID     | 任务项             | 影响                       | 预估工时 | 状态      |
| ------ | ------------------ | -------------------------- | -------- | --------- |
| TD-009 | **错题本功能开发** | 学习效果跟踪核心功能       | 16h      | � 进行中  |
| TD-007 | **流式响应实现**   | 用户交互体验优化           | 12h      | 📋 待开发 |
| TD-008 | **请求缓存机制**   | 降低 AI 成本，提升响应速度 | 8h       | 📋 待开发 |

### 下一步开发计划

**🎯 核心策略**: **MCP 优先（精确查询）+ RAG 增强（语义检索）** 两阶段演进

#### Phase 5: 体验完善 (Week 4-6, 预计 2025-10-20~11-10)

1. **错题本功能** (TD-009, 16h) - 🔄 当前重点

   - 错题自动收集、分类、复习提醒
   - 知识点关联分析和薄弱环节识别
   - 错题复习模式和效果跟踪

2. **流式响应实现** (TD-007, 12h)

   - 后端 SSE (Server-Sent Events)
   - 前端打字机效果，提升等待体验

3. **请求缓存机制** (TD-008, 8h)
   - 基于相似度的智能缓存
   - 降低 AI 服务成本

#### Phase 6: 功能完善 (Week 7-10, 预计 2025-11-10~12-08)

4. **学习目标管理** (12h) - 目标设定、进度跟踪、达成分析
5. **成就系统** (16h) - 学习激励、等级晋升、社交分享
6. **学习日历和提醒** (12h) - 计划制定、智能提醒、热力图
7. **数据导出功能** (8h) - PDF 报告、CSV 数据、学习档案

#### Phase 7: RAG 增强 (Week 11-14, 预计 2025-12-08~01-05)

**目标**: 在 MCP 精确查询基础上，增加语义相似检索能力

8. **PGVector 集成** (TD-012, 16h) - PostgreSQL 向量搜索扩展
9. **Embedding 服务** (TD-013, 8h) - 通义千问 Embedding API 对接
10. **语义检索** (TD-014, 12h) - 相似错题、历史问答检索
11. **混合检索策略** (TD-015, 12h) - MCP + RAG 融合算法

详细信息参见 **[全链条对齐开发补齐计划](docs/development/COMPREHENSIVE_TODO_PLAN.md)**

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

### ✅ Phase 4 (已完成 - 智能上下文增强)

**🎉 重大突破完成**：

- ✅ **TD-006: MCP 上下文服务全面上线** - 个性化学情分析完整实现
- ✅ **作业 API 重构完成** - 从硬编码到生产就绪，性能提升 50-90%
- ✅ **前端错误处理修复** - 消除 8 个崩溃点，统一错误处理机制
- ✅ **基础学情分析 API 上线** - 3 个核心分析端点，复杂数据聚合算法
- ✅ 知识点提取优化完成（规则+AI 混合）
- ✅ 知识图谱数据导入完成（七年级数学）
- ✅ 答案质量评估完成（5 维度评分）
- ✅ 前端学习问答重构（通义千问风格 + KaTeX）
- ✅ 登录认证修复（refresh_token 自动续期）

### 🔄 Phase 5 (进行中 - 体验完善)

- 🔄 **错题本功能** - 当前重点，学习效果跟踪核心功能
- 📋 流式响应实现 - 用户交互体验优化
- 📋 请求缓存机制 - 降低 AI 成本，提升响应速度
- 📋 学习目标管理 - 目标设定、进度跟踪、达成分析
- 📋 成就系统 - 学习激励、等级晋升、社交分享

### 📋 Phase 6 (计划中 - 功能完善)

- 学习日历和提醒
- 数据导出功能
- 学情分析算法优化（遗忘曲线、时间衰减）
- 知识图谱数据扩展

### 🚀 Phase 7 (未来 - RAG 增强)

- PGVector 向量数据库集成
- Embedding 服务对接
- 语义检索服务（相似错题、历史问答）
- 混合检索策略（MCP + RAG）

### ⚪ Phase 8 (远期)

- 教师管理后台
- 移动端优化
- 多语言支持

详细路线图参见 **[全链条对齐开发补齐计划](docs/development/COMPREHENSIVE_TODO_PLAN.md)**

---

## 🚀 生产部署

### 部署架构

本项目采用 **Python + systemd** 部署方案（已废弃 Docker 方案）：

```
阿里云 ECS (121.199.173.244)
├── Nginx (HTTPS反向代理)
│   ├── 端口: 80, 443
│   └── SSL: 自签名证书
├── systemd (进程管理)
│   └── wuhao-tutor.service
│       ├── 4 个 uvicorn worker 进程
│       └── 端口: 8000
└── PostgreSQL RDS
    └── 21 张数据表
```

### 部署流程

完整的部署流程参见 **[生产部署标准流程](PRODUCTION_DEPLOYMENT_GUIDE.md)**，包括：

1. **部署前检查** - 代码验证、构建前端、测试运行
2. **服务器备份** - 代码 + 数据库自动备份
3. **代码同步** - rsync 增量同步
4. **数据库迁移** - Alembic 自动迁移
5. **服务重启** - systemd 平滑重启
6. **健康检查** - API 端点验证
7. **回滚机制** - 一键回滚到上一版本

### 快速部署命令

```bash
# 一键部署到生产环境
./scripts/deploy_to_production.sh

# 查看服务状态
ssh root@121.199.173.244 'systemctl status wuhao-tutor'

# 查看服务日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor -f'

# 健康检查
curl -k https://121.199.173.244/api/health
```

### 关键配置文件

- `src/core/config.py` - 环境配置
- `.env` - 生产环境变量（需手动配置）
- `nginx/nginx.conf` - Nginx 配置
- `scripts/deploy/*.sh` - 部署脚本集合

### 数据库迁移注意事项 ⚠️

在 PostgreSQL 环境下，**必须严格匹配 UUID 类型**：

```python
# ❌ 错误 - 类型不匹配导致外键约束失败
user_id = Column(String(36), ForeignKey('users.id'))

# ✅ 正确
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
```

已修复的关键文件：

- `src/models/base.py` - 时间戳默认值
- `src/models/user.py`, `learning.py`, `homework.py` - 11 个外键类型修复
- `src/schemas/*.py` - UUID 序列化验证器

### 生产环境清理

参见以下文档进行环境优化：

- **[生产环境清理计划](PRODUCTION_CLEANUP_PLAN.md)** - 464MB 清理机会
- **[本地代码验证](LOCAL_CODE_VERIFICATION_PLAN.md)** - 防止错误部署
- **[本地环境清理](LOCAL_CLEANUP_PLAN.md)** - 50MB 本地清理

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

**最后更新**: 2025-10-08 (生产部署完成)  
**项目版本**: 0.4.x  
**整体状况**: A- (优秀)  
**核心策略**: MCP 优先（精确查询）→ RAG 增强（语义检索）

**🔥 当前焦点**: 生产环境稳定运行 + TD-009 错题本功能开发  
**重大成果**: Phase 4 完成 + 生产部署上线，系统全面就绪
