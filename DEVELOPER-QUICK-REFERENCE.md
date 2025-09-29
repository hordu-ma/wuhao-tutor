# 五好伴学 - 开发者快速参考卡片

> **🎯 AI助手专用上下文卡片**
>
> 本文件为AI助手提供项目的核心上下文信息，便于快速理解项目结构、约定和工作流程。

---

## 📋 项目身份卡

- **项目名**: 五好伴学 (Wuhao Tutor)
- **类型**: K12 AI学情管理平台
- **版本**: 0.1.0 (开发阶段)
- **主技术栈**: Python 3.11+ FastAPI + Vue3 TypeScript
- **依赖管理**: uv (Python) + npm (Node.js)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **AI服务**: 阿里云百炼智能体

---

## 🏗️ 核心架构速览

```
API层 (src/api/) → Service层 (src/services/) → Repository层 (src/repositories/) → Model层 (src/models/)
```

**关键目录**:
- `src/` - 应用核心代码
- `scripts/` - 开发运维脚本 (重要)
- `docs/` - 结构化文档
- `tests/` - 测试代码
- `frontend/` - Vue3前端

---

## ⚡ 快速命令参考

### 环境管理
```bash
# 基础环境
uv sync                           # 安装依赖
cp .env.example .env             # 配置环境变量
uv run python scripts/diagnose.py # 环境诊断

# 启动开发服务
./scripts/start-dev.sh           # 启动前后端 (推荐)
./scripts/status-dev.sh          # 检查状态
./scripts/stop-dev.sh            # 停止服务
```

### 代码质量
```bash
make format                      # 代码格式化
make lint                        # 代码检查
make type-check                  # 类型检查
make test                        # 运行测试
make pre-commit                  # 提交前完整检查
```

### 数据库
```bash
make db-migrate                  # 生成迁移
make db-upgrade                  # 应用迁移
uv run python scripts/manage_db.py --help # 数据库管理
```

---

## 🎯 开发约定

### 代码规范
- **函数**: ≤60行，必须类型注解
- **异常**: 精确捕获，禁用 `except:`
- **命名**: snake_case (变量/函数), PascalCase (类)
- **格式化**: Black (88字符), isort

### Git约定
```
<type>: <简述>

类型: feat|fix|docs|style|refactor|test|chore
```

### API响应格式
```json
// 成功
{"success": true, "data": {...}, "message": "OK"}

// 失败
{"success": false, "error": {"code": "ERROR_CODE", "message": "错误信息"}}
```

---

## 🛠️ 关键脚本说明

| 脚本 | 功能 | 使用时机 |
|------|------|----------|
| `scripts/start-dev.sh` | 启动完整开发环境 | 开始开发 |
| `scripts/diagnose.py` | 环境诊断检查 | 排查问题 |
| `scripts/manage_db.py` | 数据库统一管理 | DB操作 |
| `scripts/performance_monitor.py` | 性能监控 | 性能分析 |

---

## 🔧 故障排除速查

| 问题 | 解决方案 |
|------|----------|
| 服务启动失败 | `./scripts/diagnose.py` |
| 端口占用 | `./scripts/stop-dev.sh --force` |
| 依赖问题 | `uv sync` |
| 数据库连接失败 | 检查 `.env` 中 `SQLALCHEMY_DATABASE_URI` |
| 类型检查失败 | `uv run mypy src/` |
| 测试失败 | `uv run pytest -v` |

---

## 📂 重要文件路径

### 配置文件
- `pyproject.toml` - 项目配置与依赖
- `.env` - 环境变量 (从 `.env.example` 复制)
- `alembic.ini` - 数据库迁移配置

### 核心文档
- `README.md` - 完整上下文指南 (本项目主文档)
- `docs/DEVELOPMENT.md` - 详细开发工作流
- `docs/ARCHITECTURE.md` - 架构设计说明
- `scripts/README.md` - 脚本使用说明

### 应用入口
- `src/main.py` - FastAPI应用主入口
- `src/core/config.py` - 配置管理
- `src/api/v1/api.py` - API路由注册

---

## 🎨 开发模式

### 标准开发流程
1. `./scripts/start-dev.sh` (启动)
2. 编码开发
3. `make pre-commit` (检查)
4. Git提交
5. `./scripts/stop-dev.sh` (结束)

### 测试流程
1. `uv run pytest tests/unit` (单元测试)
2. `uv run pytest tests/integration` (集成测试)
3. `uv run pytest --cov=src` (覆盖率)

### 数据库操作
1. 修改 `src/models/` 下模型
2. `make db-migrate` (生成迁移)
3. 检查生成的迁移文件
4. `make db-upgrade` (应用迁移)

---

## 🌐 服务端点

### 开发环境
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **前端**: http://localhost:5173

### 健康检查
- `/health` - 基础检查
- `/api/v1/health/performance` - 性能指标
- `/api/v1/health/rate-limits` - 限流状态

---

## 🔐 安全要点

### 环境变量安全
- 不提交真实密钥到版本控制
- 使用 `.env.example` 作为模板
- 生产环境严格配置CORS

### 日志安全
- 不在日志中输出密钥/token
- 使用结构化日志
- 生产环境控制日志级别

---

## 📦 依赖管理要点

### Python (uv)
- 优先使用标准库
- 新增依赖需说明用途
- 定期检查安全漏洞

### 关键依赖
- `fastapi` - Web框架
- `sqlalchemy` - ORM
- `pydantic` - 数据验证
- `alembic` - 数据库迁移
- `pytest` - 测试框架

---

## 💻 IDE配置建议

### VSCode设置
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"]
}
```

### 推荐扩展
- Python
- Pylance
- Black Formatter
- GitLens

---

## 🎯 性能考虑

### 开发阶段关注点
- 避免N+1查询
- 使用异步IO
- 合理使用索引
- 监控慢查询

### 监控工具
- `/api/v1/health/performance` - 实时指标
- `scripts/performance_monitor.py` - 性能监控脚本

---

## 🚀 部署考虑

### 环境区分
- 开发: SQLite + 宽松CORS
- 测试: PostgreSQL + 模拟外部服务
- 生产: PostgreSQL + 严格安全策略

### Docker支持
- `Dockerfile` - 容器化配置
- `docker-compose.yml` - 服务编排

---

## 📞 获取帮助

1. **查看文档**: `docs/` 目录下相关文档
2. **运行诊断**: `./scripts/diagnose.py`
3. **检查日志**: `.dev-pids/*.log`
4. **联系维护者**: Liguo Ma <maliguo@outlook.com>

---

## 🏷️ 快速标签

`#Python` `#FastAPI` `#Vue3` `#TypeScript` `#AI教育` `#SQLAlchemy` `#Pytest` `#Docker` `#K12平台`

---

_本参考卡片与 README.md 配合使用，提供项目核心上下文信息。_
