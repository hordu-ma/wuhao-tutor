# 五好伴学项目 Makefile
# 自动化开发任务配置

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# 项目配置
PROJECT_NAME := wuhao-tutor
PYTHON := python3
UV := uv
VENV := .venv

.PHONY: help
help: ## 显示帮助信息
	@echo "$(BLUE)五好伴学 - 开发任务自动化$(RESET)"
	@echo ""
	@echo "$(GREEN)可用命令:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ========================================
# 环境管理
# ========================================

.PHONY: install
install: ## 安装项目依赖
	@echo "$(GREEN)安装项目依赖...$(RESET)"
	$(UV) sync

.PHONY: install-dev
install-dev: ## 安装开发依赖
	@echo "$(GREEN)安装开发依赖...$(RESET)"
	$(UV) sync --extra dev

.PHONY: update
update: ## 更新依赖包
	@echo "$(GREEN)更新依赖包...$(RESET)"
	$(UV) sync --upgrade

.PHONY: clean
clean: ## 清理临时文件和缓存
	@echo "$(GREEN)清理临时文件...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# ========================================
# 开发服务器
# ========================================

.PHONY: dev
dev: ## 启动开发服务器
	@echo "$(GREEN)启动开发服务器...$(RESET)"
	$(UV) run python src/main.py

.PHONY: dev-reload
dev-reload: ## 启动开发服务器（自动重载）
	@echo "$(GREEN)启动开发服务器（自动重载）...$(RESET)"
	$(UV) run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# ========================================
# 代码质量
# ========================================

.PHONY: format
format: ## 格式化代码
	@echo "$(GREEN)格式化代码...$(RESET)"
	$(UV) run black src/ tests/ --line-length 88
	$(UV) run isort src/ tests/ --profile black

.PHONY: lint
lint: ## 代码检查
	@echo "$(GREEN)运行代码检查...$(RESET)"
	$(UV) run flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	$(UV) run black src/ tests/ --check --line-length 88
	$(UV) run isort src/ tests/ --check-only --profile black

.PHONY: type-check
type-check: ## 类型检查
	@echo "$(GREEN)运行类型检查...$(RESET)"
	$(UV) run mypy src/ --ignore-missing-imports

.PHONY: check-all
check-all: lint type-check ## 运行所有检查
	@echo "$(GREEN)所有检查完成！$(RESET)"

# ========================================
# 测试
# ========================================

.PHONY: test
test: ## 运行所有测试
	@echo "$(GREEN)运行测试...$(RESET)"
	$(UV) run pytest tests/ -v

.PHONY: test-unit
test-unit: ## 运行单元测试
	@echo "$(GREEN)运行单元测试...$(RESET)"
	$(UV) run pytest tests/unit/ -v

.PHONY: test-integration
test-integration: ## 运行集成测试
	@echo "$(GREEN)运行集成测试...$(RESET)"
	$(UV) run pytest tests/integration/ -v

.PHONY: test-coverage
test-coverage: ## 运行测试并生成覆盖率报告
	@echo "$(GREEN)运行测试覆盖率分析...$(RESET)"
	$(UV) run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(BLUE)覆盖率报告生成在 htmlcov/index.html$(RESET)"

.PHONY: test-watch
test-watch: ## 监控文件变化并自动运行测试
	@echo "$(GREEN)启动测试监控模式...$(RESET)"
	$(UV) run pytest-watch tests/

# ========================================
# 数据库管理
# ========================================

.PHONY: db-init
db-init: ## 初始化数据库
	@echo "$(GREEN)初始化数据库...$(RESET)"
	$(UV) run alembic upgrade head

.PHONY: db-migrate
db-migrate: ## 生成数据库迁移文件
	@echo "$(GREEN)生成数据库迁移文件...$(RESET)"
	@read -p "请输入迁移描述: " desc; \
	$(UV) run alembic revision --autogenerate -m "$$desc"

.PHONY: db-upgrade
db-upgrade: ## 应用数据库迁移
	@echo "$(GREEN)应用数据库迁移...$(RESET)"
	$(UV) run alembic upgrade head

.PHONY: db-downgrade
db-downgrade: ## 回滚数据库迁移
	@echo "$(GREEN)回滚数据库迁移...$(RESET)"
	$(UV) run alembic downgrade -1

.PHONY: db-reset
db-reset: ## 重置数据库（危险操作）
	@echo "$(RED)警告: 这将删除所有数据！$(RESET)"
	@read -p "确认重置数据库？(y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(UV) run alembic downgrade base && \
		$(UV) run alembic upgrade head; \
	else \
		echo "$(YELLOW)操作已取消$(RESET)"; \
	fi

# ========================================
# 数据管理
# ========================================

.PHONY: seed-data
seed-data: ## 生成测试数据
	@echo "$(GREEN)生成测试数据...$(RESET)"
	$(UV) run python scripts/init/seed_data.py

.PHONY: backup-db
backup-db: ## 备份数据库
	@echo "$(GREEN)备份数据库...$(RESET)"
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	pg_dump $(PROJECT_NAME)_dev > backups/backup_$$timestamp.sql
	@echo "$(BLUE)数据库备份完成: backups/backup_$$timestamp.sql$(RESET)"

# ========================================
# 生产部署
# ========================================

.PHONY: build
build: ## 构建生产镜像
	@echo "$(GREEN)构建Docker镜像...$(RESET)"
	docker build -t $(PROJECT_NAME):latest .

.PHONY: docker-up
docker-up: ## 启动Docker服务
	@echo "$(GREEN)启动Docker服务...$(RESET)"
	docker-compose up -d

.PHONY: docker-down
docker-down: ## 停止Docker服务
	@echo "$(GREEN)停止Docker服务...$(RESET)"
	docker-compose down

.PHONY: docker-logs
docker-logs: ## 查看Docker日志
	@echo "$(GREEN)查看Docker日志...$(RESET)"
	docker-compose logs -f

# ========================================
# 文档和工具
# ========================================

.PHONY: docs
docs: ## 生成API文档
	@echo "$(GREEN)生成API文档...$(RESET)"
	$(UV) run python scripts/dev/generate_docs.py

.PHONY: schema
schema: ## 导出API Schema
	@echo "$(GREEN)导出API Schema...$(RESET)"
	$(UV) run python -c "from src.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > docs/api/openapi.json

.PHONY: security-check
security-check: ## 安全检查
	@echo "$(GREEN)运行安全检查...$(RESET)"
	$(UV) run bandit -r src/ -f json -o security-report.json
	$(UV) run safety check

.PHONY: deps-check
deps-check: ## 检查依赖更新
	@echo "$(GREEN)检查依赖更新...$(RESET)"
	$(UV) run pip-audit

# ========================================
# 快捷操作
# ========================================

.PHONY: quick-start
quick-start: install-dev db-init seed-data ## 快速开始（安装依赖、初始化数据库、生成测试数据）
	@echo "$(GREEN)环境准备完成！运行 'make dev' 启动服务器$(RESET)"

.PHONY: pre-commit
pre-commit: format lint type-check test ## 提交前检查
	@echo "$(GREEN)提交前检查完成！$(RESET)"

.PHONY: ci
ci: install-dev check-all test-coverage ## CI流程
	@echo "$(GREEN)CI流程完成！$(RESET)"

# ========================================
# 状态检查
# ========================================

.PHONY: status
status: ## 显示项目状态
	@echo "$(BLUE)项目状态检查$(RESET)"
	@echo "Python版本: $$(python --version)"
	@echo "uv版本: $$(uv --version)"
	@echo "虚拟环境: $$(if [ -d "$(VENV)" ]; then echo "✓ 已创建"; else echo "✗ 未创建"; fi)"
	@echo "依赖安装: $$(if [ -f "uv.lock" ]; then echo "✓ 已安装"; else echo "✗ 未安装"; fi)"
	@echo "数据库状态: $$(if pg_isready -q; then echo "✓ 运行中"; else echo "✗ 未运行"; fi)"
	@echo "Redis状态: $$(if redis-cli ping >/dev/null 2>&1; then echo "✓ 运行中"; else echo "✗ 未运行"; fi)"

# ========================================
# 开发工具
# ========================================

.PHONY: shell
shell: ## 进入Python shell
	@echo "$(GREEN)启动Python shell...$(RESET)"
	$(UV) run python

.PHONY: notebook
notebook: ## 启动Jupyter Notebook
	@echo "$(GREEN)启动Jupyter Notebook...$(RESET)"
	$(UV) run jupyter notebook

.PHONY: profile
profile: ## 性能分析
	@echo "$(GREEN)运行性能分析...$(RESET)"
	$(UV) run python -m cProfile -o profile.stats src/main.py
	$(UV) run python -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"