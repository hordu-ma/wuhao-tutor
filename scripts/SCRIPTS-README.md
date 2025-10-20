# 脚本目录使用说明# 脚本目录使用说明# 五好伴学开发脚本

本目录包含五好伴学项目的核心自动化脚本，覆盖开发和生产部署场景。本目录包含五好伴学项目的核心自动化脚本，覆盖开发和生产部署场景。本目录包含五好伴学项目的核心开发脚本（已精简，仅保留必需功能）。

## 快速开始## 快速开始## 📁 脚本列表

### 开发环境启动### 开发环境启动### 开发脚本

```bash````bash| 脚本 | 功能 | 用途 |

# 启动完整开发环境（前端 + 后端）

./scripts/start-dev.sh# 启动完整开发环境（前端 + 后端）| ----------------------- | -------------- | ------------------------------ |

# 仅启动前端开发服务器./scripts/start-dev.sh| `start-dev.sh` | 启动开发服务器 | 启动前端(Vite) + 后端(FastAPI) |

./scripts/start-frontend-dev.sh

| `stop-dev.sh` | 停止开发服务器 | 优雅停止所有开发服务 |

# 检查开发环境状态

./scripts/status-dev.sh# 仅启动前端开发服务器| `status-dev.sh` | 检查服务状态 | 查看进程、端口、资源使用 |

# 停止开发环境./scripts/start-frontend-dev.sh| `start-frontend-dev.sh` | 启动前端 | 仅启动 Vue3 前端服务 |

./scripts/stop-dev.sh

````



### 生产部署（⭐ 推荐）# 检查开发环境状态### 生产部署脚本



```bash./scripts/status-dev.sh

# 一键部署到生产环境

./scripts/deploy.sh| 脚本                          | 功能     | 用途                     |



# 验证生产环境状态# 停止开发环境| ----------------------------- | -------- | ------------------------ |

./scripts/check-production.sh

```./scripts/stop-dev.sh| `deploy-to-production.sh`     | 生产部署 | 推送代码到阿里云生产环境 |



**详细部署文档**：请参阅 [DEPLOY-README.md](./DEPLOY-README.md)```| `verify_deployment.sh`        | 部署验证 | 验证生产环境服务状态     |



---| `update_production_config.py` | 配置管理 | 更新生产环境配置文件     |



## 核心脚本列表（6个）### 生产部署（⭐ 推荐）



### 开发环境（4个）### SQL 脚本 (sql/)



| 脚本名称 | 功能描述 | 使用场景 |```bash

|---------|---------|---------|

| `start-dev.sh` | 启动前后端开发服务器 | 日常开发 |# 一键部署到生产环境- `01-init-extensions.sql` - 初始化 PostgreSQL 扩展

| `stop-dev.sh` | 停止开发服务器 | 清理开发环境 |

| `status-dev.sh` | 检查服务状态 | 排查启动问题 |./scripts/deploy.sh- `02-create-indexes.sql` - 创建数据库索引

| `start-frontend-dev.sh` | 仅启动前端 | 前端独立开发 |



### 生产部署（2个）⭐

# 验证生产环境状态---

| 脚本名称 | 功能描述 | 使用场景 |

|---------|---------|---------|./scripts/check-production.sh

| `deploy.sh` | **一键部署到生产环境** | **生产代码上线**（推荐） |

| `check-production.sh` | 验证生产环境状态 | 部署后验证 |```## 🚀 快速开始



---



## 详细使用指南**详细部署文档**：请参阅 [DEPLOY-README.md](./DEPLOY-README.md)### 开发环境



### deploy.sh（⭐ 推荐）



**功能**：统一生产环境部署流程---```bash



**执行阶段**：# 1. 启动开发环境

1. SSH 连接检查

2. 后端代码同步（rsync）## 核心脚本列表./scripts/start-dev.sh

3. 后端服务重启（systemctl）

4. 前端本地构建（npm run build）

5. 前端文件同步（rsync dist/）

6. 部署验证（健康检查 + 前端访问）### 开发环境（4个）# 2. 查看服务状态



**使用方法**：./scripts/status-dev.sh

```bash

./scripts/deploy.sh| 脚本名称 | 功能描述 | 使用场景 |

````

|---------|---------|---------|# 3. 停止服务

**配置信息**：

- 服务器：`root@121.199.173.244`| `start-dev.sh` | 启动前后端开发服务器 | 日常开发 |./scripts/stop-dev.sh

- 域名：`horsduroot.com`（SSL: Let's Encrypt）

- 后端路径：`/opt/wuhao-tutor`| `stop-dev.sh` | 停止开发服务器 | 清理开发环境 |```

- 前端路径：`/var/www/html`

- 服务名：`wuhao-tutor.service`| `status-dev.sh` | 检查服务状态 | 排查启动问题 |

**核心特性**：| `start-frontend-dev.sh` | 仅启动前端 | 前端独立开发 |### 生产部署

- ✅ 前端本地构建，避免服务器 npm install 超时

- ✅ 自动健康检查和状态验证

- ✅ 无交互设计，支持 CI/CD 集成

- ⚠️ 数据库迁移需手动执行（见下方命令）### 生产部署（2 个）⭐```bash

**手动数据库迁移**：# 完整部署流程

```bash

ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'| 脚本名称 | 功能描述 | 使用场景 |./scripts/deploy-to-production.sh

```

|---------|---------|---------|

---

| `deploy.sh` | **一键部署到生产环境** | **生产代码上线**（推荐） |# 快速部署（跳过备份和测试）

### check-production.sh

| `check-production.sh` | 验证生产环境状态 | 部署后验证 |./scripts/deploy-to-production.sh --quick

**功能**：验证生产环境状态

**检查项**：

- ✅ 后端服务状态（systemctl）### 数据库初始化（1 个）# 预览部署步骤（不执行）

- ✅ API 健康检查（/api/v1/health）

- ✅ 前端页面访问（https://horsduroot.com）./scripts/deploy-to-production.sh --dry-run

- ✅ SSL 证书有效性

- ✅ 系统资源（磁盘/内存）| 脚本名称 | 功能描述 | 使用场景 |

**使用方法**：|---------|---------|---------|# 仅验证生产环境

```bash

./scripts/check-production.sh| `init_database.py` | 初始化数据库并生成测试数据 | 首次设置、开发环境重置 |./scripts/verify_deployment.sh

```

```````

**输出示例**：

```### 诊断工具（1 个）

✅ 后端服务运行中 (PID: 175330)

✅ API 健康检查通过---

✅ 前端页面可访问

✅ SSL 证书有效 (到期: 2025-04-15)| 脚本名称 | 功能描述 | 使用场景 |

```

|---------|---------|---------|## 📖 脚本详细说明

---

| `diagnose.py` | 环境诊断工具 | 排查环境问题 |

### start-dev.sh

### 开发脚本

**功能**：启动完整开发环境

---

**启动服务**：

- 后端：FastAPI (端口 8000)#### start-dev.sh

- 前端：Vite Dev Server (端口 5173)

## 详细使用指南

**使用方法**：

```bash**功能：**

./scripts/start-dev.sh

```### deploy.sh（⭐ 推荐）



**日志位置**：- 自动检查 Python 3.11+ 和 Node.js 18+

- 后端：`logs/backend.log`

- 前端：`logs/frontend.log`**功能**：统一生产环境部署流程- 自动安装依赖（uv sync + npm install）



**进程管理**：- 智能端口分配（避免冲突）

- PID 文件：`logs/{backend,frontend}.pid`

- 自动清理旧进程**执行阶段**：- 同时启动前后端服务



---1. SSH 连接检查



## 最佳实践2. 后端代码同步（rsync）**默认端口：**



### 日常开发流程3. 后端服务重启（systemctl）



1. **启动开发环境**4. 前端本地构建（npm run build）- 前端：5173（自动寻找可用端口）

   ```bash

   ./scripts/start-dev.sh5. 前端文件同步（rsync dist/）- 后端：8000（自动寻找可用端口）

   ```

6. 部署验证（健康检查 + 前端访问）

2. **代码修改与测试**

   - 后端自动重载（uvicorn --reload）**生成文件：**

   - 前端热更新（Vite HMR）

**使用方法**：

3. **停止开发环境**

   ```bash```bash- `.dev-pids/frontend.pid` - 前端进程 ID

   ./scripts/stop-dev.sh

   ```./scripts/deploy.sh- `.dev-pids/backend.pid` - 后端进程 ID



### 生产部署流程（⭐ 推荐）```- `.dev-pids/\*.log` - 服务日志



1. **执行一键部署****配置信息**：---

   ```bash

   ./scripts/deploy.sh- 服务器：`root@121.199.173.244`

   ```

- 域名：`horsduroot.com`（SSL: Let's Encrypt）#### stop-dev.sh

2. **（可选）手动数据库迁移**

   ```bash- 后端路径：`/opt/wuhao-tutor`

   ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'

   ```- 前端路径：`/var/www/html`**功能：** 优雅停止开发服务器并清理资源



3. **验证部署结果**- 服务名：`wuhao-tutor.service`

   ```bash

   ./scripts/check-production.sh**参数：**

   ```

**核心特性**：

4. **查看服务日志**

   ```bash- ✅ 前端本地构建，避免服务器 npm install 超时```bash

   ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'

   ```- ✅ 自动健康检查和状态验证./scripts/stop-dev.sh # 正常停止



### 数据库操作- ✅ 无交互设计，支持 CI/CD 集成./scripts/stop-dev.sh --clean-logs # 停止并删除日志



```bash- ⚠️ 数据库迁移需手动执行（见下方命令）./scripts/stop-dev.sh --force # 强制杀死进程

# 开发环境数据库重置

make db-reset  # 包含：删除数据库 + Alembic 迁移 + 初始化测试数据````



# 生产环境数据库迁移（手动执行）**手动数据库迁移**：

ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'

``````bash---



---ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'



## 故障排查```#### status-dev.sh



### 开发服务器无法启动



1. **检查端口占用**---**功能：** 检查服务运行状态和资源使用

   ```bash

   ./scripts/status-dev.sh

   lsof -i :8000  # 后端

   lsof -i :5173  # 前端### check-production.sh**参数：**

   ```



2. **查看日志**

   ```bash**功能**：验证生产环境状态```bash

   tail -f logs/backend.log

   tail -f logs/frontend.log./scripts/status-dev.sh           # 基本状态

   ```

**检查项**：./scripts/status-dev.sh --verbose # 详细信息

3. **重启开发环境**

   ```bash- ✅ 后端服务状态（systemctl）./scripts/status-dev.sh --watch   # 持续监控（每5秒刷新）

   ./scripts/stop-dev.sh

   ./scripts/start-dev.sh- ✅ API 健康检查（/api/v1/health）```

   ```

- ✅ 前端页面访问（https://horsduroot.com）

### 生产部署问题

- ✅ SSL 证书有效性**状态指示：**

1. **检查 SSH 连接**

   ```bash- ✅ 系统资源（磁盘/内存）

   ssh root@121.199.173.244 'echo "SSH 连接正常"'

   ```- ✓ 绿色：服务正常运行



2. **查看服务状态****使用方法**：- ✗ 红色：服务未运行或异常

   ```bash

   ssh root@121.199.173.244 'systemctl status wuhao-tutor'```bash- ⚠️ 黄色：警告状态

   ```

./scripts/check-production.sh

3. **查看实时日志**

   ```bash```---

   ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'

   ```



4. **手动重启服务****输出示例**：### 生产部署脚本

   ```bash

   ssh root@121.199.173.244 'systemctl restart wuhao-tutor.service'````

   ```

✅ 后端服务运行中 (PID: 175330)#### deploy-to-production.sh

---

✅ API 健康检查通过

## 注意事项

✅ 前端页面可访问**功能：** 完整的 5 阶段生产部署流程

### 脚本清理说明（2025-10-16）

✅ SSL 证书有效 (到期: 2025-04-15)

本目录已进行大规模清理，从 **21 个脚本精简到 6 个核心脚本**：

````**部署阶段：**

- ✅ **保留的核心脚本（6个）**：

  - 开发环境：start-dev.sh, stop-dev.sh, status-dev.sh, start-frontend-dev.sh

  - 生产部署：deploy.sh, check-production.sh

---1. **本地检查** - Git 状态、关键文件、前端构建、测试

- 🗑️ **已删除的脚本（18个）**：

  - 旧部署脚本：deploy-to-production.sh, deploy-auto.sh, deploy-mobile-image-fix.sh, deploy-miniprogram.sh, deploy-experience-version.sh2. **生产备份** - 自动备份代码和配置（保留最近 5 个）

  - 测试脚本：create_test_mistakes.py, test_mistake_ai_analysis.py, test_production_api.sh, miniprogram-sync-test.js

  - 诊断脚本：diagnose_mobile_cache_issue.sh, diagnose.py### start-dev.sh3. **同步代码** - rsync 增量同步后端/前端/Nginx

  - 配置脚本：update_production_config.py, check_miniprogram_config.sh

  - 构建脚本：build_frontend.sh, verify_legacy_build.sh, optimize-package-size.sh4. **服务器操作** - 更新依赖、数据库迁移、重启服务

  - 数据库脚本：recreate_db.py, create_dev_test_accounts.py, server_create_test_accounts.py, init_database.py

  - 验证脚本：pre_deploy_check.sh, verify_deployment.sh**功能**：启动完整开发环境5. **部署验证** - 健康检查、API 测试、日志查看



**迁移指南**：

- 旧部署流程（5个脚本）→ 新部署流程（deploy.sh 一键完成）

- 部署验证（verify_deployment.sh）→ 生产状态检查（check-production.sh）**启动服务**：**可用选项：**

- 详细部署文档：[DEPLOY-README.md](./DEPLOY-README.md)

- 后端：FastAPI (端口 8000)

**清理原因**：

- 一次性使用脚本（已完成使命）- 前端：Vite Dev Server (端口 5173)```bash

- 功能重复脚本（被新脚本替代）

- 过时脚本（不再适用新架构）--dry-run       # 预览部署步骤（不执行）

- 危险操作脚本（如 recreate_db.py）

**使用方法**：--quick         # 快速部署（跳过备份和测试）

---

```bash--skip-backup   # 跳过备份步骤

### 安全提示

./scripts/start-dev.sh--skip-tests    # 跳过本地测试

1. **生产环境操作**

   - 所有生产部署必须经过测试验证````

   - 数据库迁移需手动执行（避免自动化风险）

   - 敏感配置（.env.production）不纳入版本控制**日志位置**：**特性：**



2. **SSH 密钥管理**- 后端：`logs/backend.log`

   - 使用密钥认证，禁用密码登录

   - 密钥权限必须为 600- 前端：`logs/frontend.log`- 彩色输出和进度提示

   - 定期检查服务器 authorized_keys

- 完整的错误处理和回滚指导

3. **日志安全**

   - 日志文件不包含敏感信息（密码、Token）**进程管理**：- 交互式确认机制

   - 生产日志自动脱敏处理

   - systemd 日志通过 journalctl 管理- PID 文件：`logs/{backend,frontend}.pid`- 自动备份管理（保留 5 个最近备份）



### 环境配置- 自动清理旧进程



- **开发环境**：`.env` 配置在项目根目录**示例：**

- **生产环境**：`.env.production` 配置在服务器 `/opt/wuhao-tutor/`

- **配置模板**：`config/templates/.env.example`---



### 依赖管理````bash



- **Python**：使用 `uv` 管理依赖（pyproject.toml）### diagnose.py# 首次部署（完整流程）

- **Node.js**：使用 `npm` 管理前端依赖（package.json）

- **数据库**：开发环境使用 SQLite，生产环境使用 PostgreSQL./scripts/deploy-to-production.sh



---**功能**：环境诊断工具



## 相关文档# 快速部署小改动



- **[部署文档](./DEPLOY-README.md)**（⭐ 推荐）- 生产环境部署完整指南**检查项**：./scripts/deploy-to-production.sh --quick

- [项目 README](../README.md) - 项目概览和快速开始

- [Copilot 指令](../.github/copilot-instructions.md) - AI 助手开发规范- Python 版本和依赖



---- 数据库连接# 预览部署计划



**最后更新**：2025-10-16  - 配置文件完整性./scripts/deploy-to-production.sh --dry-run

**维护者**：五好伴学开发团队

**脚本版本**：v2.0（从 21 个精简到 6 个）- 目录权限```


- 端口占用

---

**使用方法**：

```bash#### verify_deployment.sh

uv run python scripts/diagnose.py

```**功能：** 验证生产环境服务状态



**输出示例**：**检查项目：**

```````

✓ Python 3.11.7- systemd 服务状态

✓ 数据库连接正常- API 健康检查端点

✗ BAILIAN_API_KEY 未配置- 数据库连接

```````- 日志最新错误



------



## 最佳实践#### update_production_config.py



### 日常开发流程**功能：** 批量更新生产环境配置文件



1. **启动开发环境****用途：**

   ```bash

   ./scripts/start-dev.sh- 同步 secrets/ 到生产环境

   ```- 更新环境变量

- 重启相关服务

2. **代码修改与测试**

   - 后端自动重载（uvicorn --reload）---

   - 前端热更新（Vite HMR）

## 🔧 故障排查

3. **停止开发环境**

   ```bash### 端口被占用

   ./scripts/stop-dev.sh

   ``````bash

# 查看端口占用

### 生产部署流程（⭐ 推荐）lsof -i :8000

lsof -i :5173

1. **执行一键部署**

   ```bash# 强制停止

   ./scripts/deploy.sh./scripts/stop-dev.sh --force

```````

2. **（可选）手动数据库迁移**### 服务启动失败

   ````bash

   ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'```bash

   ```# 查看日志
   ````

cat .dev-pids/backend.log

3. **验证部署结果**cat .dev-pids/frontend.log

   ````bash

   ./scripts/check-production.sh# 检查详细状态

   ```./scripts/status-dev.sh --verbose
   ````

```````

4. **查看服务日志**

   ```bash### 依赖问题

   ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'

   ``````bash

# 重新安装依赖

### 开发环境数据库重置rm -rf .venv frontend/node_modules

./scripts/start-dev.sh

```bash```

make db-reset  # 包含：删除数据库 + Alembic 迁移 + 初始化数据

```---



---## 📝 日志管理



## 故障排查```bash

# 实时查看日志

### 开发服务器无法启动tail -f .dev-pids/frontend.log

tail -f .dev-pids/backend.log

1. **检查端口占用**

   ```bash# 查看最近50行

   ./scripts/status-dev.shtail -50 .dev-pids/backend.log

   lsof -i :8000  # 后端

   lsof -i :5173  # 前端# 清理日志

   ```./scripts/stop-dev.sh --clean-logs

```````

2. **查看日志**

   ```bash---

   tail -f logs/backend.log

   tail -f logs/frontend.log## 📚 相关文档

   ```

- **开发指南**: `docs/development/`

3. **重启开发环境**- **API 文档**: `docs/api/`

   ```bash- **架构文档**: `docs/architecture/`

   ./scripts/stop-dev.sh

   ./scripts/start-dev.sh---

   ```

   ```

## ⚠️ 注意事项

### 生产部署问题

1. **首次运行**会自动安装依赖（需几分钟）

1. **检查 SSH 连接**2. **端口冲突**时会自动寻找可用端口

   ```bash3. **日志文件**保存在 `.dev-pids/` 目录

   ssh root@121.199.173.244 'echo "SSH 连接正常"'4. **PID 文件**在停止时自动清理

   ```5. 确保在**项目根目录**下运行脚本

   ```

1. **查看服务状态**---

   ````bash

   ssh root@121.199.173.244 'systemctl status wuhao-tutor'**最后更新**: 2025-10-09

   ```**脚本数量**: 8 个核心脚本（4 个开发 + 3 个部署 + SQL）

   ````

1. **查看实时日志**---

   ```bash

   ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'## 📦 归档说明

   ```

以下脚本已完成使命并归档至 `archive/scripts/`：

4. **手动重启服务**

   ```bash- `cleanup_local.sh` - 本地环境清理（已执行，节省 94MB）

   ssh root@121.199.173.244 'systemctl restart wuhao-tutor.service'- `cleanup_production.sh` - 生产环境清理（已执行，节省 ~200MB）

   ```- `deploy_to_alicloud.sh` - 初次部署脚本（已被 deploy-to-production.sh 取代）

---已删除的临时脚本：

## 注意事项- `backup_database.sh` - 临时备份脚本

- `setup_ssl.sh` / `renew_ssl.sh` - SSL 配置脚本（已完成配置）

### 脚本清理说明- `migrate_database.py` - 旧迁移脚本（功能重复）

- `create_missing_tables.py` - 临时数据库绕过方案

本目录已于 **2025-10-16** 进行大规模清理，删除以下类型脚本：

- ✅ 已删除：18 个冗余脚本（一次性使用、已过时、被新脚本替代）
- ✅ 保留：6 个核心脚本（开发 4 个 + 部署 2 个）
- 🗑️ 删除列表：
  - 旧部署脚本：deploy-to-production.sh, deploy-auto.sh, deploy-mobile-image-fix.sh, deploy-miniprogram.sh, deploy-experience-version.sh
  - 测试脚本：create_test_mistakes.py, test_mistake_ai_analysis.py, test_production_api.sh, miniprogram-sync-test.js
  - 诊断脚本：diagnose_mobile_cache_issue.sh, diagnose.py
  - 配置脚本：update_production_config.py, check_miniprogram_config.sh
  - 构建脚本：build_frontend.sh, verify_legacy_build.sh, optimize-package-size.sh
  - 数据库脚本：recreate_db.py, create_dev_test_accounts.py, server_create_test_accounts.py, init_database.py
  - 验证脚本：pre_deploy_check.sh, verify_deployment.sh

**迁移指南**：

- 旧部署流程（deploy-to-production.sh）→ 新部署流程（deploy.sh）
- 部署验证（verify_deployment.sh）→ 生产状态检查（check-production.sh）
- 详细部署文档已迁移至：[DEPLOY-README.md](./DEPLOY-README.md)

---

### 安全提示

1. **生产环境操作**

   - 所有生产部署必须经过测试验证
   - 数据库迁移需手动执行（避免自动化风险）
   - 敏感配置（.env.production）不纳入版本控制

2. **SSH 密钥管理**

   - 使用密钥认证，禁用密码登录
   - 密钥权限必须为 600
   - 定期检查服务器 authorized_keys

3. **日志安全**
   - 日志文件不包含敏感信息（密码、Token）
   - 生产日志自动脱敏处理
   - systemd 日志通过 journalctl 管理

### 环境配置

- **开发环境**：`.env` 配置在项目根目录
- **生产环境**：`.env.production` 配置在服务器 `/opt/wuhao-tutor/`
- **配置模板**：`config/templates/.env.example`

### 依赖管理

- **Python**：使用 `uv` 管理依赖（pyproject.toml）
- **Node.js**：使用 `npm` 管理前端依赖（package.json）
- **数据库**：开发环境使用 SQLite，生产环境使用 PostgreSQL

---

## 相关文档

- **[部署文档](./DEPLOY-README.md)**（⭐ 推荐）- 生产环境部署完整指南
- [项目 README](../README.md) - 项目概览和快速开始
- [Copilot 指令](../.github/copilot-instructions.md) - AI 助手开发规范

---

**最后更新**：2025-10-16  
**维护者**：五好伴学开发团队  
**脚本版本**：v2.0（清理后）
