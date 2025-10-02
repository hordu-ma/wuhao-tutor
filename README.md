# 五好伴学 (Wuhao Tutor)

> 基于阿里云百炼智能体的 K12 智能学习支持平台

一个现代化的教育科技平台，利用AI技术为K12学生提供智能作业批改、个性化学习问答和全面的学情分析服务。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D.svg)
![Status](https://img.shields.io/badge/status-Beta-green.svg)

## ✨ 核心特性

### 🤖 智能作业批改

- **AI驱动评分**：基于阿里云百炼智能体的自动批改系统
- **多维度反馈**：提供详细的评分解释和改进建议
- **多媒体支持**：支持文本、图片等多种作业形式

### 💬 智能学习问答

- **对话式学习**：自然语言交互，个性化解答学习疑问
- **上下文记忆**：维持连贯的对话会话，深度理解学习需求
- **知识追踪**：记录学习轨迹，构建个人知识图谱

### 📊 学情分析

- **学习数据统计**：全面的学习活跃度和频次分析
- **知识掌握评估**：智能推断学生对不同知识点的掌握程度
- **个性化建议**：基于数据分析提供针对性学习建议

### 🔒 企业级特性

- **多维限流保护**：IP/用户/AI服务多层限流机制
- **安全头配置**：CSP、HSTS等完整安全策略
- **性能监控**：实时性能指标收集和慢查询监控
- **结构化日志**：便于问题排查和系统优化

## 🏗️ 技术架构

### 后端技术栈

- **核心框架**：Python 3.11+ + FastAPI + SQLAlchemy 2.x (Async)
- **数据验证**：Pydantic v2 严格类型校验
- **数据库**：PostgreSQL 14+ (生产) / SQLite (开发)
- **缓存**：Redis 6+ (限流/缓存)
- **AI服务**：阿里云百炼智能体统一封装

### 前端技术栈

- **框架**：Vue 3 + TypeScript + Composition API
- **构建工具**：Vite 5.x
- **UI组件**：Element Plus + Tailwind CSS
- **状态管理**：Pinia + Vue Router 4

### 架构特点

- **分层设计**：API → Service → Repository → Model 清晰分层
- **类型安全**：全量TypeScript类型注解，mypy零错误
- **可观测性**：完整的监控、限流、性能指标体系
- **容器化部署**：Docker + Nginx + 脚本化管理

## 🚀 快速开始

### 环境要求

- Python ≥ 3.11
- Node.js ≥ 18 (如需前端开发)
- PostgreSQL 14+ (生产) 或 SQLite (开发)
- Redis 6+ (可选)

### 安装与运行

```bash
# 1. 克隆项目
git clone <repository-url>
cd wuhao-tutor

# 2. 安装Python依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和AI服务密钥

# 4. 环境诊断
uv run python scripts/diagnose.py

# 5. 启动后端服务
./scripts/start-dev.sh
```

访问应用：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **前端界面**: http://localhost:5173 (如果启动前端)

### 最小配置

创建 `.env` 文件：

```env
# 基础配置
ENVIRONMENT=development
DEBUG=true
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db

# AI服务配置 (可选)
BAILIAN_API_KEY=your-api-key
BAILIAN_APPLICATION_ID=your-app-id
```

## 📋 项目结构

```
wuhao-tutor/
├── src/                    # 🔥 核心应用代码
│   ├── api/               # FastAPI 路由与端点
│   ├── core/              # 配置、安全、监控、性能
│   ├── models/            # SQLAlchemy ORM 模型
│   ├── repositories/      # 数据访问层抽象
│   ├── schemas/           # Pydantic 数据模型
│   ├── services/          # 业务逻辑与AI封装
│   └── utils/             # 工具函数
├── frontend/              # 🎨 Vue3 前端项目
├── scripts/               # 🛠️ 开发运维脚本
├── tests/                 # 🧪 测试代码
├── docs/                  # 📚 项目文档
├── alembic/               # 🗄️ 数据库迁移
├── Makefile              # 📋 任务自动化
└── pyproject.toml        # 📦 项目配置
```

## 🛠️ 开发指南

### 代码规范

- **函数长度**: ≤60行，单一职责原则
- **类型注解**: 必须包含完整类型注解
- **异常处理**: 精确捕获，禁用裸 `except:`
- **命名规范**: snake_case(变量/函数)，PascalCase(类)，UPPER_CASE(常量)

### 常用命令

```bash
# 代码质量检查
make format                # 代码格式化 (Black + isort)
make type-check           # 类型检查 (mypy)
make test                 # 运行测试
make pre-commit          # 提交前完整检查

# 数据库管理
make db-migrate          # 生成迁移文件
make db-upgrade          # 应用迁移

# 服务管理
./scripts/start-dev.sh   # 启动开发环境
./scripts/status-dev.sh  # 检查服务状态
./scripts/stop-dev.sh    # 停止服务
```

### Git 提交规范

```bash
feat: 新功能开发
fix: 问题修复
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 其他杂项
```

## 📚 API 文档

### 核心端点

- `POST /api/v1/homework/submit` - 提交作业
- `POST /api/v1/chat/ask` - 发起学习问答
- `GET /api/v1/analytics/learning-stats` - 获取学情分析

### 统一响应格式

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应格式

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求参数验证失败"
    }
}
```

完整API文档请访问：http://localhost:8000/docs

## 🧪 测试

### 运行测试

```bash
# 快速测试
uv run pytest -q

# 详细测试
uv run pytest tests/ -v

# 覆盖率测试
uv run pytest --cov=src --cov-report=html

# 性能测试
uv run pytest tests/performance
```

### 测试分类

- **单元测试**: `tests/unit/` - 独立函数/类测试
- **集成测试**: `tests/integration/` - API端到端测试
- **性能测试**: `tests/performance/` - 基准性能测试

## 🚀 部署

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

### 生产环境

详细部署指南请参考：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 📊 监控与观测

### 健康检查端点

- `/health` - 基础健康检查
- `/api/v1/health/performance` - 性能指标
- `/api/v1/health/rate-limits` - 限流状态
- `/api/v1/health/metrics` - 系统指标

### 性能目标

- API响应：P95 < 200ms
- 数据库查询：P95 < 50ms
- AI服务调用：P95 < 3s

## 🔐 安全特性

- **多维限流**：IP/用户/AI服务/登录尝试
- **安全头**：CSP, HSTS, X-Frame-Options
- **输入验证**：Pydantic严格校验
- **错误处理**：统一异常处理，避免信息泄露
- **密钥管理**：脚本化密钥生成与轮换

## 📖 文档

| 文档                                                                   | 说明               |
| ---------------------------------------------------------------------- | ------------------ |
| [📚 文档导航](docs/README.md)                                          | **文档中心入口**   |
| [🤖 AI助手上下文](AI-CONTEXT.md)                                       | AI开发助手必读     |
| [📋 MVP开发计划](MVP-DEVELOPMENT-PLAN.md)                              | 当前开发计划       |
| [架构设计](docs/ARCHITECTURE.md)                                       | 系统分层与模块设计 |
| [开发指南](docs/DEVELOPMENT.md)                                        | 详细开发工作流     |
| [API文档](docs/api/)                                                   | 接口规范与示例     |
| [学习指南](docs/development/LEARNING_GUIDE.md)                         | 学习现代Python开发 |
| [小程序开发](docs/development/WECHAT_MINIPROGRAM_DEVELOPMENT_GUIDE.md) | 微信小程序指南     |
| [历史文档](docs/history/)                                              | Phase 1/2 完成总结 |

## 🗓️ 版本规划

| 版本  | 状态    | 主要特性                |
| ----- | ------- | ----------------------- |
| 0.1.x | ✅ 完成 | Phase 1: 核心功能打通   |
| 0.2.x | ✅ 完成 | Phase 2: 数据持久化完善 |
| 0.3.x | 🔄 当前 | Phase 3: 前后端联调     |
| 0.4.x | 📋 规划 | Phase 4: MVP 基线测试   |
| 1.0.0 | 🎯 目标 | 稳定发布版本            |

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建 Pull Request

### 贡献要求

- 遵循项目代码规范
- 包含必要的测试用例
- 通过所有CI检查
- 更新相关文档

## 📞 支持与反馈

- **维护者**: Liguo Ma <maliguo@outlook.com>
- **问题反馈**: [GitHub Issues](../../issues)
- **功能建议**: [Pull Requests](../../pulls)
- **文档问题**: 创建Issue标记 `docs` 标签

## 📜 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个Star⭐，这是对我们最大的鼓励！

---

<div align="center">

**🎓 让AI为教育赋能，让学习更智能更高效**

</div>
