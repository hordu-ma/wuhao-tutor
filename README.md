# 五好伴学 (Wuhao Tutor)

> 基于阿里云百炼智能体的 K12 智能学习支持平台
> AI 驱动的作业问答 + 智能错题手册 + 全面学情分析

一个现代化的教育科技平台，专为 K12 学生打造，利用 AI 技术提供智能学习问答、错题管理和全面的学情分析服务。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D.svg)
![Status](https://img.shields.io/badge/status-Production-green.svg)

---

## 📊 项目现状

**生产环境**: https://www.horsduroot.com
**最后更新**: 2025-10-19
**技术架构**: FastAPI + Vue3 + PostgreSQL + 阿里云百炼 AI

### 核心功能模块

| 模块           | 状态        | 说明                                                 |
| -------------- | ----------- | ---------------------------------------------------- |
| **作业问答**   | ✅ 生产可用 | AI 驱动的学习助手,支持对话式问答、数学公式渲染       |
| **错题手册**   | ✅ 生产可用 | 错题记录、智能复习提醒、知识点关联分析、艾宾浩斯算法 |
| **学习进度**   | ✅ 生产可用 | 学习时长统计、知识点掌握度、学科分布分析             |
| **个人中心**   | ✅ 生产可用 | 用户信息管理、头像上传、学习统计展示                 |
| **微信小程序** | ✅ 已完成   | 完整的小程序端,支持所有核心功能,已上线使用           |

### 📚 关键文档

| 文档                                                | 说明                                 |
| --------------------------------------------------- | ------------------------------------ |
| **[开发进度](DEVELOPMENT_STATUS.md)** ⭐            | 当前开发状态、已完成功能、下阶段计划 |
| **[更新日志](CHANGELOG.md)**                        | 版本更新和功能变更记录               |
| **[开发路线图](DEVELOPMENT_ROADMAP.md)**            | 长期开发规划（12 个月路线图）        |
| **[文档中心](docs/DOCS-README.md)**                 | 完整的项目文档导航                   |
| **[Copilot 指令](.github/copilot-instructions.md)** | AI 辅助开发规范                      |

**按类别浏览**:

- 📐 [架构设计](docs/architecture/) - 系统架构、数据模型、API 设计
- 🔌 [API 文档](docs/api/) - 接口文档、模型定义
- 💾 [数据库](docs/database/) - 表结构、迁移脚本
- 📱 [小程序](docs/miniprogram/) - 微信小程序开发文档
- 🌐 [前端](docs/frontend/) - Web 前端开发指南
- 🔧 [解决方案](docs/solutions/) - 常见问题修复方案
- 📖 [使用指南](docs/guide/) - 功能使用说明

### 🎯 近期更新 (2025-10-12)

- ✅ **错题手册功能完成** - 完整的错题记录、复习提醒、掌握度跟踪和统计分析
- ✅ **微信小程序上线** - 完整的小程序端,支持错题本、作业问答、学习报告等核心功能
- ✅ **每日学习目标** - 基于真实数据的学习目标追踪与进度展示
- ✅ **头像上传功能修复** - 完善 Pinia 响应式更新机制,优化 Nginx location 配置优先级
- ✅ **移动端兼容性优化** - 修复图片上传超时、缓存问题、浏览器兼容性

---

## ✨ 核心特性

### 💬 作业问答 (核心功能)

- **AI 驱动问答**: 基于阿里云百炼智能体的对话式学习助手
- **上下文感知**: 自动维持会话上下文,理解连续提问意图
- **多模态支持**: 支持文字提问、图片上传、数学公式输入
- **公式渲染**: 集成 KaTeX 支持,完美显示数学公式和符号
- **学情关联**: 结合用户薄弱知识点和学习偏好,提供个性化答案
- **会话管理**: 支持多会话并行、会话归档、历史记录搜索

**技术实现**:

- 通义千问风格极简 UI (三栏可折叠布局)
- MCP 上下文服务集成 (薄弱知识点 + 学习偏好分析)
- 实时流式响应,优化用户等待体验
- Markdown 渲染 + 代码高亮支持

### 📚 错题手册

- **智能记录**: 手动添加或从学习问答中记录错题和难点
- **复习提醒**: 基于艾宾浩斯遗忘曲线的智能复习计划
- **知识关联**: 知识点标签管理,识别知识点薄弱环节
- **统计分析**: 错题分布、掌握度趋势、复习效果追踪
- **今日复习**: 每日自动生成待复习错题清单

**技术实现**:

- ✅ 完整的前端界面 (Web + 小程序)
- ✅ API 端点 (错题 CRUD、复习、统计等 7 个端点)
- ✅ MistakeService 完整业务逻辑
- ✅ 数据库表结构 (mistake_records + mistake_reviews)
- ✅ 间隔重复算法 (SpacedRepetitionAlgorithm)

### 📊 学习进度分析

- **学习统计**: 学习时长、提问次数、活跃天数追踪
- **知识掌握**: 基于答题记录的知识点掌握度分析
- **学科分布**: 各学科学习时长、平均分、提升趋势
- **时间序列**: 支持日/周/月多粒度数据聚合和可视化
- **个性化建议**: AI 驱动的学习建议和改进方向

**核心 API**:

- `/api/v1/analytics/learning-progress` - 学习进度趋势
- `/api/v1/analytics/knowledge-mastery` - 知识点掌握情况
- `/api/v1/analytics/subject-stats` - 学科统计分析

### 🔒 企业级特性

- **多维限流保护**: IP/用户/AI 服务三层限流机制 (Token Bucket + Sliding Window)
- **安全头配置**: CSP、HSTS、X-Frame-Options 完整安全策略
- **性能监控**: 实时性能指标收集,自动慢查询监控 (>500ms)
- **结构化日志**: JSON 格式日志,便于问题排查和系统优化
- **JWT 双 Token**: access_token + refresh_token 自动续期机制

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
  向量库: 计划集成 PGVector (语义检索)

AI 服务:
  提供商: 阿里云百炼智能体
  模型: 通义千问
  功能: 学习问答 + 作业批改
  架构: 单一智能体 + 场景参数化
  策略: MCP 精确查询 + RAG 语义检索(规划中)

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
  生产环境: systemd + Nginx + HTTPS
  开发环境: 本地 Python + Vite Dev Server
  监控: Prometheus (配置已就绪)
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
├── config.py       # 环境配置管理 (Pydantic Settings)
├── database.py     # 异步数据库连接池
├── security.py     # JWT 认证 + 多维限流
├── monitoring.py   # 性能监控指标收集
├── performance.py  # 查询监听 + N+1 检测
└── logging.py      # 结构化日志记录
```

**架构特点**:

- 严格分层,单向依赖
- 全异步架构 (async/await)
- 依赖注入 (Depends)
- 类型安全 (Type Hints + mypy)

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
git clone https://github.com/hordu-ma/wuhao-tutor.git
cd wuhao-tutor
```

#### 2. 后端环境配置

```bash
# 使用 uv 同步依赖
uv sync

# 复制环境变量模板
cp config/templates/.env.development .env

# 编辑 .env 配置必要的环境变量:
# - DATABASE_URL (默认 SQLite,生产用 PostgreSQL)
# - BAILIAN_* (阿里云百炼 API 配置)
# - SECRET_KEY (JWT 密钥)
```

#### 3. 初始化数据库

```bash
# 运行数据库迁移
uv run alembic upgrade head

# 初始化示例数据 (可选)
uv run python scripts/init_database.py
```

#### 4. 启动后端服务

```bash
# 开发模式
uv run python src/main.py

# 或使用 Make 命令
make dev
```

#### 5. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

#### 6. 访问应用

- 前端界面: http://localhost:5173
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 开发工具脚本

```bash
# 环境诊断
uv run python scripts/diagnose.py

# 数据库重置
make db-reset

# 数据库备份
make db-backup

# 运行测试
make test

# 代码格式化
make lint
```

---

## 📚 项目文档

### 开发文档

- [架构概览](docs/architecture/overview.md) - 四层架构设计、技术选型
- [数据访问层](docs/architecture/data-access.md) - Repository 模式、数据库设计
- [API 端点文档](docs/api/endpoints.md) - 完整 API 清单和使用说明
- [开发指南](docs/guide/development.md) - 环境搭建、开发流程、工具使用

### 部署文档

- **[一键部署脚本](scripts/DEPLOY-README.md)** ⭐ - 简单高效的生产部署工具
- [生产部署指南](docs/deployment/production-deployment-guide.md) - systemd + Nginx 完整部署流程
- [本地代码验证](docs/deployment/local-code-verification.md) - 部署前代码安全检查
- [RDS 数据库配置](docs/deployment/RDS_CONNECTION_GUIDE.md) - PostgreSQL 连接配置
- [Redis 缓存配置](docs/deployment/REDIS_CONNECTION_GUIDE.md) - Redis 连接和使用
- [安全密钥管理](docs/deployment/SECURITY_KEYS_GUIDE.md) - API Key 和密钥配置

### 集成文档

- [前端集成](docs/integration/frontend.md) - Vue3 集成方案、API 调用
- [微信小程序开发](docs/integration/wechat-miniprogram.md) - 小程序架构和开发规范
- [微信认证集成](docs/integration/wechat-auth.md) - 微信登录和用户绑定

---

## 🛠️ 开发规范

### Git 提交规范

```
类型(范围): 简洁描述

类型:
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- refactor: 重构
- test: 测试相关
- chore: 构建/工具链更新

示例:
feat(learning): 添加数学公式渲染支持
fix(avatar): 修复头像上传 Pinia 响应式问题
docs(readme): 更新项目现状和核心功能说明
```

### 代码质量标准

- **类型注解**: 所有函数必须有类型注解 (mypy strict)
- **错误处理**: 使用具体异常类型,禁用裸 `except:`
- **函数职责**: 单一职责原则,≤ 60 行
- **测试覆盖**: 核心功能必须有单元测试
- **文档注释**: 复杂逻辑必须有 Google 风格 docstring

### 架构规范

- **严格分层**: API → Service → Repository → Model
- **依赖注入**: 使用 FastAPI Depends 机制
- **异步优先**: 所有 I/O 操作使用 async/await
- **配置外化**: 所有配置使用环境变量,禁止硬编码

---

## 📊 项目统计

```
代码行数:
- Python 后端: ~15,000 行
- Vue 前端: ~8,000 行
- 测试代码: ~3,000 行

测试覆盖率:
- 核心模块: 80%+
- Service 层: 85%+
- Repository 层: 90%+

性能指标:
- API 响应时间: P95 < 200ms
- 数据库查询: P95 < 50ms
- AI 问答延迟: P95 < 3s
```

---

## 🔮 未来规划

详见 [开发计划](DEVELOPMENT_ROADMAP.md)

### 短期目标 (1-2 个月)

1. **基础推荐系统** - 协同过滤 + 规则推荐,个性化练习推荐
2. **知识图谱可视化** - 前端展示知识点关系图,辅助学习路径规划
3. **RAG 语义检索** - 集成 PGVector,实现相似问题/错题检索
4. **小程序功能增强** - 语音输入、离线缓存、消息推送

### 中期目标 (3-6 个月)

1. **RAG 语义增强** - 升级推荐系统和问答系统,提升准确率
2. **协作学习功能** - 学习小组、问题分享、互助答疑
3. **多模态输入增强** - 手写识别、图片 OCR 优化
4. **学习报告生成** - 周报/月报自动生成,家长/教师查看

### 长期愿景 (6-12 个月)

1. **多学科扩展** - 从数学扩展到语文、英语、物理、化学
2. **自适应学习** - 动态调整难度,个性化学习路径推荐
3. **教师管理端** - 班级管理、作业批改、学情分析
4. **开放平台** - 提供 API,支持第三方集成

---

## 🤝 贡献指南

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 开发流程

1. 在 Issues 中讨论新功能或 Bug
2. 获得认可后开始开发
3. 确保代码通过所有测试
4. 更新相关文档
5. 提交 PR 并等待 Review

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 维护者

- **hordu-ma** - [GitHub](https://github.com/hordu-ma)

---

## 📮 联系方式

- 项目地址: https://github.com/hordu-ma/wuhao-tutor
- 问题反馈: https://github.com/hordu-ma/wuhao-tutor/issues
- 生产环境: https://wuhao-tutor.liguoma.top

---

<div align="center">

**⭐ 如果这个项目对你有帮助,请给它一个 Star! ⭐**

Made with ❤️ by hordu-ma

</div>
