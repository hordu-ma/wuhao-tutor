# 五好伴学 - AI 助手上下文指南

> **🤖 AI 助手必读**
> 本文档是与 AI 助手交互的核心上下文文件，包含项目关键信息、技术架构、开发约定和常用命令。

**最后更新**: 2025-10-02
**项目版本**: 0.2.0 (Beta)

---

## 🎯 项目核心信息

### 项目身份

- **名称**: 五好伴学 (Wuhao Tutor)
- **类型**: K12 AI 学情管理平台
- **路径**: `~/my-devs/python/wuhao-tutor`
- **维护者**: Liguo Ma <maliguo@outlook.com>

### 核心功能

1. **智能作业批改** - AI 驱动的作业自动评分与反馈
2. **学习问答互动** - 个性化学习问题解答
3. **学情分析反馈** - 学习数据分析与建议

### 当前状态

- **开发阶段**: Beta (Phase 2 完成，Phase 3 进行中)
- **Phase 1**: ✅ 核心功能打通 (作业批改功能)
- **Phase 2**: ✅ 数据持久化完善 (Analytics API + 数据库迁移)
- **Phase 3**: 🔄 前后端联调 (进行中)
- **技术债务**: 测试覆盖率需提升至80%+、前端集成测试待完成

---

## 🏗️ 技术架构

### 技术栈

```
后端:  Python 3.11+ + FastAPI + SQLAlchemy 2.x (Async) + Pydantic v2
数据库: PostgreSQL 14+ (生产) / SQLite (开发)
缓存:  Redis 6+
AI:    阿里云百炼智能体
前端:  Vue 3 + TypeScript + Vite + Element Plus
依赖:  uv (Python) + npm (Node.js)
运维:  Docker + Nginx
```

### 架构分层

```
API 层 (src/api/)         ← HTTP 路由、请求验证、响应封装
  ↓
Service 层 (src/services/) ← 业务逻辑编排、AI 服务封装
  ↓
Repository 层 (src/repositories/) ← 数据访问抽象、查询优化
  ↓
Model 层 (src/models/)     ← ORM 模型、数据结构定义
```

**设计原则**: 单一职责、依赖倒置、接口隔离

### 关键目录

```
src/           # 核心应用代码
scripts/       # 开发运维脚本 (重要！)
docs/          # 结构化文档
tests/         # 测试代码
frontend/      # Vue3 前端
alembic/       # 数据库迁移
```

---

## ⚡ 快速命令参考

### 环境管理

```bash
# 依赖安装与环境准备
uv sync                              # 安装依赖
cp .env.example .env                 # 配置环境变量
uv run python scripts/diagnose.py   # 环境诊断

# 服务启动与状态
./scripts/start-dev.sh               # 启动前后端 (推荐)
./scripts/status-dev.sh              # 检查服务状态
./scripts/stop-dev.sh                # 停止所有服务
```

### 代码质量

```bash
make format                          # 代码格式化 (Black + isort)
make type-check                      # 类型检查 (mypy)
make test                            # 运行测试
make pre-commit                      # 提交前完整检查 (必须通过!)
```

### 数据库

```bash
make db-migrate                      # 生成迁移文件
make db-upgrade                      # 应用迁移
uv run python scripts/manage_db.py --help  # 数据库管理工具
```

### 核心端点

- **API 文档**: http://localhost:8000/docs (Swagger)
- **健康检查**: http://localhost:8000/health
- **性能指标**: http://localhost:8000/api/v1/health/performance
- **前端**: http://localhost:5173

---

## 📋 开发约定与规范

### 代码规范

```python
# 函数设计
def function_name(param: Type) -> ReturnType:
    """
    必须: 类型注解 + Docstring
    限制: ≤60 行，单一职责
    """
    try:
        # 业务逻辑
        pass
    except SpecificError as e:  # 精确捕获，禁用裸 except:
        logger.error("具体错误", error=str(e))
        raise

# 命名约定
user_service = UserService()           # 变量/函数: snake_case
class UserService:                     # 类: PascalCase
    pass
DEFAULT_PAGE_SIZE = 20                 # 常量: UPPER_CASE
```

### Git 提交规范

```bash
# 格式
<type>: <简述>

# 类型
feat     # 新功能
fix      # 缺陷修复
docs     # 文档更新
refactor # 代码重构
test     # 测试相关
chore    # 其他杂项

# 示例
feat: 增加学情分析知识点掌握度算法
fix: 修复用户登录 session 超时问题
docs: 更新 API 文档错误码说明
```

### API 设计约定

```json
// 成功响应
{
  "success": true,
  "data": {...},
  "message": "OK"
}

// 错误响应
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}

// 路由规范
/api/v1/users          # GET: 列表, POST: 创建
/api/v1/users/{id}     # GET: 详情, PUT: 更新, DELETE: 删除
```

---

## 🔄 标准开发流程

### 日常开发循环

```bash
# 1. 环境准备
uv sync                           # 同步依赖
./scripts/diagnose.py             # 环境诊断
./scripts/start-dev.sh            # 启动服务

# 2. 开发过程
# 编码 → 热更新自动生效 → 测试

# 3. 提交前检查 (必须!)
make pre-commit                   # 格式化 + 类型检查 + 测试
# 必须全部通过才能提交!

# 4. 提交代码
git add .
git commit -m "feat: 功能描述"
git push

# 5. 清理环境
./scripts/stop-dev.sh
```

### 数据库迁移流程

```bash
# 1. 修改模型 (src/models/)
# 2. 生成迁移
make db-migrate                   # 或 alembic revision --autogenerate -m "描述"
# 3. 检查生成的迁移文件 (alembic/versions/)
# 4. 应用迁移
make db-upgrade                   # 或 alembic upgrade head
```

---

## 🛠️ 关键脚本说明

| 脚本                             | 功能               | 使用场景 |
| -------------------------------- | ------------------ | -------- |
| `./scripts/start-dev.sh`         | 启动完整开发环境   | 开始开发 |
| `./scripts/stop-dev.sh`          | 优雅停止所有服务   | 结束工作 |
| `./scripts/status-dev.sh`        | 检查服务状态与诊断 | 排查问题 |
| `./scripts/diagnose.py`          | 环境诊断与问题检查 | 环境异常 |
| `scripts/manage_db.py`           | 数据库统一管理     | DB 操作  |
| `scripts/performance_monitor.py` | 性能监控           | 性能分析 |

**原则**: 优先使用项目提供的脚本，而非直接执行底层命令

---

## 🔐 安全要点

### 安全基线

- **多维限流**: IP/用户/AI 服务/登录尝试
- **安全头**: CSP, HSTS(生产), X-Frame-Options
- **输入验证**: Pydantic 严格校验
- **敏感数据**: 加密存储，不记录到日志

### 配置安全

```bash
.env           # 本地开发配置 (不提交到版本控制)
.env.example   # 配置模板 (无敏感信息)
secrets/       # 生产密钥管理 (gitignore)
```

**禁止**: 硬编码密钥、密码等敏感信息到代码中

---

## 🚨 故障排查速查

| 问题           | 解决方案                                 |
| -------------- | ---------------------------------------- |
| 服务启动失败   | `./scripts/diagnose.py` → 检查环境       |
| 端口被占用     | `./scripts/stop-dev.sh --force`          |
| 依赖问题       | `uv sync` 重新同步                       |
| 数据库连接失败 | 检查 `.env` 中 `SQLALCHEMY_DATABASE_URI` |
| AI 功能异常    | 验证 `.env` 中 `BAILIAN_API_KEY`         |
| 类型检查错误   | `uv run mypy src/` 查看详细错误          |
| 测试失败       | `uv run pytest -v --tb=short` 查看详情   |

### 调试工具

```bash
# 查看日志
tail -f .dev-pids/backend.log
tail -f .dev-pids/frontend.log

# 检查端口
lsof -i :8000                    # 后端端口
lsof -i :5173                    # 前端端口

# 性能诊断
./scripts/status-dev.sh --verbose
uv run python scripts/performance_monitor.py status
```

---

## 📚 文档导航

### 核心文档

- **本文档** (`AI-CONTEXT.md`) - AI 助手快速上下文
- `README.md` - 项目主页
- `docs/README.md` - 📚 文档导航中心
- `docs/architecture/overview.md` - 详细架构设计
- `docs/guide/development.md` - 完整开发工作流
- `docs/architecture/security.md` - 安全策略与实践
- `docs/guide/testing.md` - 测试策略与规范

### 开发指南文档

- `docs/development/LEARNING_GUIDE.md` - 学习指南
- `docs/development/WECHAT_MINIPROGRAM_DEVELOPMENT_GUIDE.md` - 小程序开发指南

### API 文档

- `docs/api/overview.md` - API 总览与认证
- `docs/api/endpoints.md` - 端点详细说明
- `docs/api/models.md` - 数据模型
- `docs/api/errors.md` - 错误码说明

### 历史文档

- `docs/history/phase1/` - Phase 1 完成总结
- `docs/history/phase2/` - Phase 2 完成总结
- `docs/history/phase3/` - Phase 3 完成总结
- `docs/archived/phase4/` - Phase 4 归档文档

### 运维文档

- `docs/guide/deployment.md` - 部署策略
- `docs/architecture/observability.md` - 监控体系
- `docs/operations/database-migration.md` - 数据库迁移

---

## 🎯 AI 助手工作模式

### 优先级原则

1. **安全第一**: 不泄露敏感信息，谨慎操作生产数据
2. **约定遵循**: 严格遵守项目编码规范和提交流程
3. **工具优先**: 优先使用 `scripts/` 目录下的脚本工具
4. **文档引用**: 优先参考 `docs/` 目录下的专题文档
5. **渐进迭代**: 小步快跑，确保每一步可验证、可回滚

### 工作检查清单

**开始工作前**:

- [ ] 阅读本文档了解项目状态
- [ ] 运行 `./scripts/diagnose.py` 检查环境
- [ ] 确认开发目标和影响范围

**开发过程中**:

- [ ] 遵循代码规范（类型注解、函数长度、命名约定）
- [ ] 编写必要的单元测试
- [ ] 更新相关文档（如有 API 变更）

**提交前检查**:

- [ ] `make pre-commit` 全部通过
- [ ] `./scripts/diagnose.py` 无错误
- [ ] 核心功能手动测试正常
- [ ] Git 提交信息符合规范

### 沟通模式

- **简洁高效**: 直击要点，提供可执行方案
- **解释原因**: 不仅说"怎么做"，还要说"为什么"
- **权衡分析**: 涉及技术选择时分析利弊
- **风险提示**: 指出潜在问题和注意事项

---

## 💡 常见开发场景

### 场景 1: 添加新 API 端点

```bash
1. 在 src/api/v1/ 创建路由
2. 在 src/services/ 实现业务逻辑
3. 在 src/repositories/ 添加数据访问（如需要）
4. 编写单元测试 tests/unit/
5. 编写集成测试 tests/integration/
6. 更新 docs/api/endpoints.md
7. make pre-commit 检查
```

### 场景 2: 修改数据模型

```bash
1. 修改 src/models/ 下的模型
2. make db-migrate 生成迁移文件
3. 检查 alembic/versions/ 下生成的迁移
4. make db-upgrade 应用迁移
5. 更新相关的 Repository 和 Service 代码
6. 更新测试
7. make pre-commit 检查
```

### 场景 3: 性能优化

```bash
1. 访问 /api/v1/health/performance 查看当前指标
2. 运行 scripts/performance_monitor.py status
3. 识别瓶颈（数据库查询、AI 调用等）
4. 实施优化（添加索引、缓存、异步等）
5. 重新测试性能指标验证效果
6. 更新 docs/OBSERVABILITY.md 记录优化结果
```

---

## 📝 快速备忘

### 性能目标

- API 响应: P95 < 200ms
- 数据库查询: P95 < 50ms
- AI 服务调用: P95 < 3s

### 数据库核心模型

```
User (用户)
├── ChatSession (对话会话)
│   ├── Question (问题)
│   └── Answer (回答)
└── HomeworkSubmission (作业提交)
    └── 关联 Question (批改结果)
```

### 环境变量关键配置

```env
ENVIRONMENT=development              # 环境标识
DEBUG=true                           # 调试模式
SQLALCHEMY_DATABASE_URI=...          # 数据库连接
BAILIAN_API_KEY=...                  # AI 服务密钥
BAILIAN_APPLICATION_ID=...           # AI 应用ID
```

---

## 🏷️ 项目标签

`#Python` `#FastAPI` `#Vue3` `#TypeScript` `#SQLAlchemy` `#AI教育` `#K12` `#阿里云百炼`

---

**💡 记住**:

- 这是一个教育 AI 平台，安全性和数据隐私至关重要
- 遵循 Unix 哲学：专一、简洁、可组合
- 代码可读性优先于聪明技巧
- 提交前必须通过 `make pre-commit` 检查
- 遇到问题先运行 `./scripts/diagnose.py`

---

_本文档整合自 README.md、PROJECT-CONTEXT.md、DEVELOPER-QUICK-REFERENCE.md 等多个文档，作为 AI 助手的统一上下文入口。_
