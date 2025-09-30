# 项目上下文总结 - AI助手认知框架

> **🤖 AI助手专用**
>
> 本文件为AI助手提供完整的项目认知框架，包含项目本质、技术决策、开发模式和关键约定。

---

## 🎯 项目本质认知

### 项目定位
- **项目名称**: 五好伴学 (Wuhao Tutor)
- **领域**: K12教育AI平台
- **核心价值**: 基于阿里云百炼AI的学情分析与智能学习支持
- **目标用户**: 初高中学生、教师、家长

### 功能闭环
1. **智能作业批改** - AI驱动的作业自动批改与评分
2. **学习问答互动** - 个性化学习问题解答
3. **学情分析反馈** - 学习数据分析与个性化建议

### 当前状态
- **版本**: 0.1.0 (Alpha阶段)
- **完成度**: 后端核心 ~90%，前端基础框架完成
- **开发重点**: 学情分析模块迭代，监控体系完善

---

## 🏗️ 技术架构认知

### 技术栈选择理由
```
后端: Python 3.11+ FastAPI
├── 原因: 异步性能 + AI库生态丰富 + 快速开发
├── 数据库: SQLAlchemy 2.x (异步ORM)
└── 验证: Pydantic v2 (类型安全 + 性能)

前端: Vue 3 + TypeScript
├── 原因: 组合式API + 强类型 + 生态成熟
├── 构建: Vite (快速热更新)
└── 组件: Element Plus + Tailwind CSS

AI服务: 阿里云百炼
├── 原因: 教育场景优化 + 中文支持好
└── 封装: 统一Service层抽象

部署: Docker + Docker Compose
├── 开发: SQLite + Redis
└── 生产: PostgreSQL + Redis + Nginx
```

### 架构分层哲学
```
API层 (路由控制)
  ↓ 职责: HTTP协议适配，请求验证
Service层 (业务逻辑)
  ↓ 职责: 业务流程编排，AI服务调用
Repository层 (数据访问)
  ↓ 职责: 数据持久化抽象，查询优化
Model层 (数据模型)
  ↓ 职责: 数据结构定义，业务约束
```

### 设计原则
- **单一职责**: 每层只关注自己的职责
- **依赖倒置**: 高层不依赖低层实现细节
- **接口隔离**: 服务间通过明确接口交互
- **开闭原则**: 对扩展开放，对修改封闭

---

## 🛠️ 开发工具链认知

### 依赖管理策略
```bash
Python: uv (性能优秀，兼容性好)
├── 虚拟环境管理
├── 依赖解析与锁定
└── 脚本执行环境

Node.js: npm/pnpm (前端生态标准)
├── 包管理与版本控制
└── 构建工具链集成
```

### 代码质量工具链
```bash
格式化: Black (88字符) + isort
├── 统一代码风格
└── 自动import排序

类型检查: mypy
├── 静态类型验证
└── 运行时错误预防

测试: pytest + pytest-asyncio
├── 单元测试 + 集成测试
└── 异步代码测试支持
```

### 开发脚本体系
```bash
./scripts/start-dev.sh    # 一键启动完整开发环境
./scripts/stop-dev.sh     # 优雅停止所有服务
./scripts/status-dev.sh   # 服务状态检查与诊断
./scripts/restart-dev.sh  # 重启开发环境
scripts/diagnose.py       # 环境诊断与问题排查
scripts/manage_db.py      # 数据库统一管理入口
```

---

## 📋 开发约定认知

### 代码规范哲学
```python
# 函数设计原则
def function_name(param: Type) -> ReturnType:
    """
    职责单一，长度≤60行
    必须类型注解，便于维护
    """
    # 精确异常处理，禁用裸except
    try:
        # 业务逻辑
        pass
    except SpecificError as e:
        logger.error("具体错误描述", error=str(e))
        raise
```

### 命名约定
```python
# 变量和函数: snake_case
user_service = UserService()
def get_user_by_id(user_id: int) -> User:
    pass

# 类: PascalCase
class UserService:
    pass

# 常量: UPPER_CASE
DEFAULT_PAGE_SIZE = 20
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
```

### API设计模式
```python
# 统一响应格式
{
    "success": True,           # 操作是否成功
    "data": {...},            # 响应数据 (成功时)
    "message": "OK",          # 操作消息
    "error": {                # 错误信息 (失败时)
        "code": "ERROR_CODE",
        "message": "错误描述"
    }
}

# 路由设计
/api/v1/users          # GET: 列表，POST: 创建
/api/v1/users/{id}     # GET: 详情，PUT: 更新，DELETE: 删除
/api/v1/users/{id}/sessions  # 用户相关资源
```

---

## 🔄 工作流程认知

### 标准开发循环
```bash
# 1. 环境准备
uv sync                    # 同步依赖
cp .env.example .env      # 配置环境
./scripts/diagnose.py     # 环境诊断

# 2. 开发启动
./scripts/start-dev.sh    # 启动服务
# 访问 http://localhost:8000/docs 查看API

# 3. 开发过程
# 编码 → 热更新 → 测试 → 调试

# 4. 提交前检查
make format              # 代码格式化
make type-check         # 类型检查
make test              # 运行测试
make pre-commit        # 完整检查

# 5. 提交代码
git add .
git commit -m "feat: 功能描述"
git push

# 6. 环境清理
./scripts/stop-dev.sh   # 停止服务
```

### Git工作流
```bash
# 分支策略
main                    # 稳定分支
├── feature/功能名     # 新功能开发
├── fix/问题描述      # 缺陷修复
└── docs/文档更新     # 文档相关

# 提交格式
<type>: <简述>
# type: feat|fix|docs|style|refactor|test|chore

# 示例
feat: 增加作业批改评分算法
fix: 修复用户登录session超时问题
docs: 更新API文档错误码说明
```

---

## 🗄️ 数据库认知

### 数据库策略
```sql
-- 开发环境: SQLite
-- 优点: 无需安装，快速启动
-- 限制: 单连接，功能有限

-- 生产环境: PostgreSQL
-- 优点: 功能完整，性能优秀
-- 特性: 支持JSON，全文搜索，并发
```

### 迁移管理
```bash
# Alembic工作流
alembic revision --autogenerate -m "描述"  # 生成迁移
alembic upgrade head                      # 应用迁移
alembic downgrade -1                      # 回滚迁移

# 脚本封装
make db-migrate        # 生成迁移
make db-upgrade        # 应用迁移
make db-init          # 初始化数据库
```

### 核心模型关系
```
User (用户)
├── ChatSession (对话会话)
│   ├── Question (问题)
│   └── Answer (回答)
└── HomeworkSubmission (作业提交)
    ├── 关联Question (批改问题)
    └── 学情数据分析
```

---

## 🔐 安全认知

### 安全分层
```
1. 网络层: CORS + TrustedHost + 安全头
2. 应用层: 输入验证 + 输出编码 + 异常处理
3. 数据层: SQL注入防护 + 敏感数据加密
4. 监控层: 限流 + 异常告警 + 审计日志
```

### 限流策略
```python
# 多维限流
IP限流: 100请求/分钟        # 防止暴力攻击
用户限流: 1000请求/小时     # 防止滥用
AI服务限流: 50请求/分钟     # 控制成本
登录限流: 5次失败/15分钟    # 防止破解
```

### 敏感数据处理
```bash
# 配置安全
.env           # 本地开发配置
.env.example   # 配置模板 (无敏感信息)
环境变量       # 生产环境配置

# 日志安全
- 不输出密码、token等敏感信息
- 结构化日志便于分析
- 生产环境控制日志级别
```

---

## 📊 监控认知

### 可观测性体系
```
健康检查:
├── /health                        # 基础存活检查
├── /api/v1/health/performance    # 性能指标
├── /api/v1/health/rate-limits    # 限流状态
└── /api/v1/health/metrics        # 系统指标

监控维度:
├── 请求延迟 (P50, P95, P99)
├── 错误率 (4xx, 5xx)
├── 吞吐量 (RPS)
├── 系统资源 (CPU, Memory)
└── AI服务调用 (成功率, 延迟)
```

### 性能基准
```python
# 响应时间目标
API响应: P95 < 200ms
数据库查询: P95 < 50ms
AI服务调用: P95 < 3s
文件上传: 10MB < 30s

# 并发目标
单机QPS: 1000+
数据库连接: 50并发
AI服务: 10并发 (成本控制)
```

---

## 🚨 故障处理认知

### 常见问题分类
```bash
# 1. 环境问题
依赖冲突: uv sync 重新安装
端口占用: ./scripts/stop-dev.sh --force
配置错误: 检查 .env 文件

# 2. 服务问题
启动失败: ./scripts/diagnose.py 诊断
连接异常: 检查数据库/Redis状态
性能问题: 查看 /api/v1/health/performance

# 3. 代码问题
类型错误: uv run mypy src/
测试失败: uv run pytest -v --tb=short
导入错误: 检查模块路径和依赖
```

### 诊断工具链
```bash
# 环境诊断
./scripts/diagnose.py              # 完整环境检查
./scripts/status-dev.sh --verbose  # 服务状态详情

# 性能诊断
scripts/performance_monitor.py status  # 性能监控
tail -f .dev-pids/backend.log         # 实时日志

# 数据库诊断
scripts/manage_db.py check            # 数据库状态
alembic current                       # 迁移状态
```

---

## 🎯 AI助手工作模式

### 优先级原则
1. **安全第一**: 不泄露敏感信息，谨慎操作
2. **约定遵循**: 严格遵守项目编码规范
3. **工具优先**: 优先使用项目提供的脚本工具
4. **文档引用**: 优先参考 docs/ 目录文档
5. **渐进迭代**: 小步快跑，可验证可回滚

### 工作检查清单
```bash
# 开始工作前
1. 阅读 README.md 了解项目状态
2. 运行 ./scripts/diagnose.py 检查环境
3. 确认开发目标和影响范围

# 开发过程中
1. 遵循代码规范和命名约定
2. 添加必要的类型注解和文档
3. 编写对应的测试用例
4. 使用项目提供的工具脚本

# 提交前检查
1. make pre-commit 通过所有检查
2. ./scripts/diagnose.py 无错误
3. 更新相关文档 (如有必要)
4. 测试核心功能正常
```

### 沟通模式
- **直接高效**: 直击要点，提供可执行方案
- **解释原因**: 不仅说"怎么做"，还要说"为什么"
- **权衡分析**: 涉及选择时分析利弊
- **风险提示**: 指出潜在问题和注意事项

---

## 📚 关键文档索引

### 必读文档
1. `README.md` - 项目完整上下文指南
2. `docs/DEVELOPMENT.md` - 详细开发工作流程
3. `docs/ARCHITECTURE.md` - 架构设计与分层说明
4. `scripts/README.md` - 脚本工具使用指南

### 专题文档
- `docs/SECURITY.md` - 安全策略与实践
- `docs/OBSERVABILITY.md` - 监控与指标体系
- `docs/DATA-ACCESS.md` - 数据访问层设计
- `docs/TESTING.md` - 测试策略与规范

### 配置文件
- `pyproject.toml` - 项目配置与依赖管理
- `Makefile` - 任务自动化脚本
- `.env.example` - 环境变量模板
- `alembic.ini` - 数据库迁移配置

---

## 🎨 开发体验优化

### IDE配置建议
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "python.testing.pytestEnabled": true
}
```

### 推荐插件
- Python + Pylance (语言支持)
- Black Formatter (代码格式化)
- GitLens (Git增强)
- REST Client (API测试)

### 调试配置
```json
// .vscode/launch.json
{
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["src.main:app", "--reload"],
            "console": "integratedTerminal"
        }
    ]
}
```

---

## 🏷️ 项目标签

`#Python` `#FastAPI` `#Vue3` `#TypeScript` `#SQLAlchemy` `#Pydantic` `#Alembic` `#Pytest` `#Docker` `#AI教育` `#K12` `#学情分析` `#阿里云百炼`

---

**🎯 AI助手记忆要点**:
1. 这是一个教育AI平台，服务K12学生群体
2. 后端Python技术栈，遵循分层架构和类型安全
3. 使用uv管理依赖，scripts/目录提供完整工具链
4. 严格遵循代码规范，提交前必须通过所有检查
5. 优先使用项目提供的脚本工具进行操作
6. 安全第一，不泄露敏感信息，谨慎处理配置
