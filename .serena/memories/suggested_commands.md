# 常用开发命令

## 环境管理
```bash
# 安装依赖
make install            # 基础依赖
make install-dev        # 开发依赖
uv sync                 # 同步依赖

# 环境管理
uv run python scripts/env_manager.py  # 环境切换
uv run python scripts/diagnose.py     # 环境诊断
```

## 开发服务器
```bash
# 启动开发环境 (前端+后端)
./scripts/start-dev.sh
make dev

# 单独启动
make backend           # 仅后端
make frontend          # 仅前端

# 停止服务
./scripts/stop-dev.sh
```

## 数据库操作
```bash
make db-reset          # 重置数据库+示例数据
make db-backup         # PostgreSQL 备份
make db-migrate        # 运行迁移

# Alembic 迁移
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
```

## 代码质量
```bash
make test              # 运行测试+覆盖率
make lint              # 格式化+检查 (black+flake8+mypy)
make format            # 仅格式化

# 单独工具
uv run black .
uv run flake8 .
uv run mypy src
uv run pytest tests/
```

## 构建和部署
```bash
make build             # 构建 Docker 镜像
make docker-dev        # 开发环境容器
make deploy            # 生产部署

# 监控
make monitor           # 检查服务状态
make logs              # 查看日志
```

## 脚本工具
```bash
# 常用脚本 (都用 uv run 前缀)
uv run python scripts/init_database.py     # 初始化数据库
uv run python scripts/create_test_user.py  # 创建测试用户
uv run python scripts/manage_db.py         # 数据库管理
uv run python scripts/diagnose.py          # 环境诊断
```

## Git 提交规范
```bash
# 类型: feat|fix|docs|refactor|test|chore
git commit -m "feat(api): 添加用户认证接口"
git commit -m "fix(frontend): 修复响应式布局问题"
```