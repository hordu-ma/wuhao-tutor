# 项目文件结构说明

## 📁 完整项目结构

```
wuhao-tutor/
│
├── 📄 核心配置文件
│   ├── pyproject.toml           # Python 项目配置（uv、依赖、工具）
│   ├── uv.lock                  # 依赖锁定文件
│   ├── Makefile                 # 任务自动化
│   ├── alembic.ini              # 数据库迁移配置
│   ├── .flake8                  # Linter 配置
│   ├── .python-version          # Python 版本指定
│   └── README.md                # 项目说明
│
├── 📁 源代码 (src/)
│   ├── main.py                  # FastAPI 应用入口
│   ├── api/                     # API 路由层 (50+ endpoints)
│   ├── services/                # 业务逻辑层 (10+ services)
│   ├── repositories/            # 数据访问层 (Generic BaseRepository)
│   ├── models/                  # 数据模型 (11+ models)
│   └── core/                    # 核心基础设施
│       ├── config.py            # 配置管理 (Pydantic Settings v2)
│       ├── database.py          # SQLAlchemy 异步引擎
│       ├── security.py          # JWT + 多层限流
│       ├── monitoring.py        # 性能监控
│       ├── performance.py       # 慢查询检测
│       └── exceptions.py        # 统一异常处理 (20+ types)
│
├── 🧪 测试 (tests/)
│   ├── unit/                    # 单元测试 (Services、Repositories)
│   ├── integration/             # 集成测试 (API endpoints)
│   ├── performance/             # 性能测试
│   └── conftest.py              # pytest 配置
│
├── 📦 前端 (frontend/)
│   ├── src/
│   │   ├── components/          # Vue3 组件
│   │   ├── pages/               # 页面
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── router/              # 路由配置
│   │   └── App.vue
│   ├── package.json             # npm 依赖
│   ├── vite.config.ts           # Vite 构建配置
│   ├── tsconfig.json            # TypeScript 配置
│   └── tailwind.config.js       # Tailwind CSS 配置
│
├── 📱 微信小程序 (miniprogram/)
│   ├── app.js                   # 小程序入口
│   ├── pages/                   # 小程序页面 (15+)
│   ├── components/              # 小程序组件
│   ├── utils/                   # 工具函数
│   └── app.json                 # 小程序配置
│
├── 🗂️ 数据库 (alembic/)
│   ├── versions/                # 迁移脚本 (15+ migrations)
│   ├── env.py                   # Alembic 环境配置
│   └── script.py.mako           # 迁移模板
│
├── 📚 数据 (data/)
│   ├── knowledge/               # 知识库数据 (静态) ✅ 提交
│   ├── knowledge_dict/          # 知识词典 (静态) ✅ 提交
│   └── local/                   # 本地运行时数据 (生成) ❌ 不提交
│       └── [.gitignore]
│
├── ⚙️ 配置 (config/)
│   └── templates/               # 配置模板和默认值
│
├── 📖 文档 (docs/)
│   ├── api/                     # API 文档
│   ├── database/                # 数据库设计文档
│   ├── deployment/              # 部署说明
│   └── README.md
│
├── 🚀 部署 (deploy/)
│   ├── systemd/                 # Systemd 服务配置
│   └── docker/                  # Docker 配置 (如有)
│
├── 🔍 监控 (monitoring/)
│   ├── prometheus.yml           # Prometheus 配置
│   ├── alertmanager/            # 告警配置
│   ├── grafana/                 # Grafana 配置
│   └── rules/                   # 告警规则
│
├── 🌐 Web 服务器 (nginx/)
│   ├── nginx.conf               # Nginx 主配置
│   └── [其他配置文件]
│
├── 🛠️ 脚本 (scripts/)
│   ├── dev/                     # 开发脚本
│   ├── deploy/                  # 部署脚本
│   ├── init/                    # 初始化脚本
│   └── start-dev.sh             # 一键启动脚本
│
├── 💾 数据管理
│   ├── backups/                 # 数据库备份 (运行时生成)
│   └── uploads/                 # 用户上传文件 (运行时生成)
│
├── 📋 Git 和 CI/CD
│   ├── .git/                    # Git 仓库
│   ├── .github/                 # GitHub Actions 配置
│   ├── .gitignore               # Git 忽略规则
│   └── .gitattributes           # Git 属性配置
│
├── 📝 文档和指南
│   ├── AGENTS.md                # AI 代理开发指南 (English)
│   ├── AGENTS_zh.md             # AI 代理开发指南 (中文)
│   └── MAKE_GUIDE.md            # Make 工具学习手册
│
├── 🔐 开发环境
│   ├── .env                     # 开发环境变量 [.gitignore]
│   ├── .env.example             # 环境变量模板
│   ├── .python-version          # Python 版本 (pyenv)
│   ├── .venv/                   # 虚拟环境 [.gitignore]
│   ├── .vscode/                 # VS Code 配置
│   └── .idea/                   # JetBrains IDE 配置
│
└── 🔧 其他
    ├── .qoder/                  # Qoder 配置
    ├── .serena/                 # Serena 配置
    ├── .mcp.json                # MCP 服务器配置
    └── .playwright-mcp/         # Playwright 配置
```

---

## 🏗️ 核心架构说明

### 四层严格分层

```
API 层 (src/api/v1/endpoints/)
  ↓ (HTTP 请求处理)
Service 层 (src/services/)
  ↓ (业务逻辑)
Repository 层 (src/repositories/)
  ↓ (数据访问)
Model 层 (src/models/)
  ↓ (数据库模型)
PostgreSQL/SQLite
```

**关键原则**：

- ✅ 禁止跨层调用 (如 API → Repository)
- ✅ 所有 I/O 操作使用 `async/await`
- ✅ 全部类型注解 (mypy strict)

### 核心基础设施 (src/core/)

| 模块           | 功能                 | 说明                  |
| -------------- | -------------------- | --------------------- |
| config.py      | Pydantic Settings v2 | 环境配置管理          |
| database.py    | SQLAlchemy 2.x       | 异步数据库连接        |
| security.py    | JWT + 限流           | 认证和访问控制        |
| monitoring.py  | 性能指标             | 响应时间、错误率      |
| performance.py | 慢查询检测           | >1.0s 告警 + N+1 检测 |
| exceptions.py  | 异常体系             | 20+ 具体异常类型      |

---

## 📊 关键数据指标

### API

- **端点数**：50+ 个 RESTful endpoints
- **版本**：v1 (src/api/v1/endpoints/)
- **功能**：
  - AI 问答 (25+ endpoints)
  - 错题手册 (10+ endpoints)
  - 知识图谱 (3+ endpoints)
  - 学习分析 (8+ endpoints)

### 数据库

- **表数**：11+ 个 models
- **迁移数**：15+ 个 migration files
- **ORM**：SQLAlchemy 2.x (asyncpg + aiosqlite)
- **环境**：Dev (SQLite) | Prod (PostgreSQL)

### 依赖管理

- **工具**：uv (现代 Python 包管理)
- **锁定文件**：uv.lock (2730+ 行)
- **依赖数**：50+ 生产依赖 + 15+ 开发依赖
- **Python 版本**：3.11+

### 前端

- **框架**：Vue 3.4+ (Composition API)
- **语言**：TypeScript 5.6+
- **构建**：Vite 5+
- **UI 库**：Element Plus 2.5+
- **状态管理**：Pinia 2.1+

### 小程序

- **平台**：微信小程序 (在线运行)
- **页面**：15+ 页面
- **连接**：生产环境 (horsduroot.com)
- **功能**：学习、错题、分析、个人中心

---

## 🔄 开发工作流

### 日常开发

```bash
make quick-start     # 首次初始化：安装依赖 + 初始化DB + 生成数据
make dev             # 启动后端开发服务器
cd frontend && npm run dev  # 启动前端开发
```

### 代码质量

```bash
make format          # 格式化代码 (black + isort)
make lint            # 代码检查 (flake8)
make type-check      # 类型检查 (mypy strict)
make pre-commit      # 提交前全检查
```

### 测试

```bash
make test                  # 运行所有测试
make test-unit             # 单元测试
make test-integration      # 集成测试
make test-coverage         # 覆盖率报告 (htmlcov/)
```

### 数据库

```bash
make db-migrate      # 生成迁移文件 (Alembic)
make db-init         # 应用迁移
make db-reset        # 重置数据库 (开发用)
```

### 部署

```bash
./scripts/deploy.sh  # 一键部署到生产
```

---

## 📦 生产部署

### 部署位置

- **后端**：`/opt/wuhao-tutor`
- **前端**：`/var/www/html`
- **日志**：`/var/log/wuhao-tutor`
- **配置**：`/opt/wuhao-tutor/.env.production`

### 部署命令

```bash
# 在本地执行
./scripts/deploy.sh

# 或手动
cd frontend && npm run build  # 构建前端
# 前端构建输出到 dist/
git pull origin main         # 更新后端代码
systemctl restart wuhao-tutor.service  # 重启服务
```

### 验证

```bash
curl https://www.horsduroot.com/health
journalctl -u wuhao-tutor.service -f
```

---

## 🎯 文件大小参考

| 位置         | 大小     | 说明            |
| ------------ | -------- | --------------- |
| src/         | ~2000 行 | 50+ API 端点    |
| tests/       | ~1000 行 | 单元 + 集成测试 |
| frontend/    | ~5000 行 | Vue3 组件和页面 |
| miniprogram/ | ~3000 行 | 小程序代码      |
| docs/        | ~50 KB   | 文档和说明      |

---

## 🔒 敏感文件和目录

```
✅ Git 跟踪：
- src/                   (源代码)
- tests/                 (测试)
- frontend/              (前端)
- miniprogram/           (小程序)
- alembic/               (迁移)
- docs/                  (文档)
- scripts/               (脚本)
- config/templates/      (配置模板)
- data/knowledge*/       (知识库)
- monitoring/            (监控配置)
- pyproject.toml, Makefile, README.md 等

❌ 不跟踪（.gitignore）：
- .env                   (环境变量)
- .env.production        (生产配置)
- secrets/               (密钥文件)
- *.log                  (日志文件)
- *.db                   (数据库文件)
- htmlcov/               (覆盖率报告)
- test-results/          (测试报告)
- uploads/               (用户上传)
- .venv/                 (虚拟环境)
```

---

## 📚 相关文档

- **开发指南**：AGENTS.md (English) / AGENTS_zh.md (中文)
- **Make 工具**：MAKE_GUIDE.md
- **API 文档**：docs/api/
- **数据库设计**：docs/database/
- **部署说明**：docs/deployment/

---

**最后更新**：2025-11-13
**维护者**：Development Team
