# 五好伴学开发脚本

本目录包含五好伴学项目的核心开发脚本（已精简，仅保留必需功能）。

## 📁 脚本列表

### 开发脚本

| 脚本                    | 功能           | 用途                           |
| ----------------------- | -------------- | ------------------------------ |
| `start-dev.sh`          | 启动开发服务器 | 启动前端(Vite) + 后端(FastAPI) |
| `stop-dev.sh`           | 停止开发服务器 | 优雅停止所有开发服务           |
| `status-dev.sh`         | 检查服务状态   | 查看进程、端口、资源使用       |
| `start-frontend-dev.sh` | 启动前端       | 仅启动 Vue3 前端服务           |

### 生产部署脚本

| 脚本                          | 功能     | 用途                     |
| ----------------------------- | -------- | ------------------------ |
| `deploy-to-production.sh`     | 生产部署 | 推送代码到阿里云生产环境 |
| `verify_deployment.sh`        | 部署验证 | 验证生产环境服务状态     |
| `update_production_config.py` | 配置管理 | 更新生产环境配置文件     |

### SQL 脚本 (sql/)

- `01-init-extensions.sql` - 初始化 PostgreSQL 扩展
- `02-create-indexes.sql` - 创建数据库索引

---

## 🚀 快速开始

### 开发环境

```bash
# 1. 启动开发环境
./scripts/start-dev.sh

# 2. 查看服务状态
./scripts/status-dev.sh

# 3. 停止服务
./scripts/stop-dev.sh
```

### 生产部署

```bash
# 完整部署流程
./scripts/deploy-to-production.sh

# 快速部署（跳过备份和测试）
./scripts/deploy-to-production.sh --quick

# 预览部署步骤（不执行）
./scripts/deploy-to-production.sh --dry-run

# 仅验证生产环境
./scripts/verify_deployment.sh
```

---

## 📖 脚本详细说明

### 开发脚本

#### start-dev.sh

**功能：**

- 自动检查 Python 3.11+ 和 Node.js 18+
- 自动安装依赖（uv sync + npm install）
- 智能端口分配（避免冲突）
- 同时启动前后端服务

**默认端口：**

- 前端：5173（自动寻找可用端口）
- 后端：8000（自动寻找可用端口）

**生成文件：**

- `.dev-pids/frontend.pid` - 前端进程 ID
- `.dev-pids/backend.pid` - 后端进程 ID
- `.dev-pids/*.log` - 服务日志

---

#### stop-dev.sh

**功能：** 优雅停止开发服务器并清理资源

**参数：**

```bash
./scripts/stop-dev.sh              # 正常停止
./scripts/stop-dev.sh --clean-logs # 停止并删除日志
./scripts/stop-dev.sh --force      # 强制杀死进程
```

---

#### status-dev.sh

**功能：** 检查服务运行状态和资源使用

**参数：**

```bash
./scripts/status-dev.sh           # 基本状态
./scripts/status-dev.sh --verbose # 详细信息
./scripts/status-dev.sh --watch   # 持续监控（每5秒刷新）
```

**状态指示：**

- ✓ 绿色：服务正常运行
- ✗ 红色：服务未运行或异常
- ⚠️ 黄色：警告状态

---

### 生产部署脚本

#### deploy-to-production.sh

**功能：** 完整的 5 阶段生产部署流程

**部署阶段：**

1. **本地检查** - Git 状态、关键文件、前端构建、测试
2. **生产备份** - 自动备份代码和配置（保留最近 5 个）
3. **同步代码** - rsync 增量同步后端/前端/Nginx
4. **服务器操作** - 更新依赖、数据库迁移、重启服务
5. **部署验证** - 健康检查、API 测试、日志查看

**可用选项：**

```bash
--dry-run       # 预览部署步骤（不执行）
--quick         # 快速部署（跳过备份和测试）
--skip-backup   # 跳过备份步骤
--skip-tests    # 跳过本地测试
```

**特性：**

- 彩色输出和进度提示
- 完整的错误处理和回滚指导
- 交互式确认机制
- 自动备份管理（保留 5 个最近备份）

**示例：**

```bash
# 首次部署（完整流程）
./scripts/deploy-to-production.sh

# 快速部署小改动
./scripts/deploy-to-production.sh --quick

# 预览部署计划
./scripts/deploy-to-production.sh --dry-run
```

---

#### verify_deployment.sh

**功能：** 验证生产环境服务状态

**检查项目：**

- systemd 服务状态
- API 健康检查端点
- 数据库连接
- 日志最新错误

---

#### update_production_config.py

**功能：** 批量更新生产环境配置文件

**用途：**

- 同步 secrets/ 到生产环境
- 更新环境变量
- 重启相关服务

---

## 🔧 故障排查

### 端口被占用

```bash
# 查看端口占用
lsof -i :8000
lsof -i :5173

# 强制停止
./scripts/stop-dev.sh --force
```

### 服务启动失败

```bash
# 查看日志
cat .dev-pids/backend.log
cat .dev-pids/frontend.log

# 检查详细状态
./scripts/status-dev.sh --verbose
```

### 依赖问题

```bash
# 重新安装依赖
rm -rf .venv frontend/node_modules
./scripts/start-dev.sh
```

---

## 📝 日志管理

```bash
# 实时查看日志
tail -f .dev-pids/frontend.log
tail -f .dev-pids/backend.log

# 查看最近50行
tail -50 .dev-pids/backend.log

# 清理日志
./scripts/stop-dev.sh --clean-logs
```

---

## 📚 相关文档

- **开发指南**: `docs/development/`
- **API 文档**: `docs/api/`
- **架构文档**: `docs/architecture/`

---

## ⚠️ 注意事项

1. **首次运行**会自动安装依赖（需几分钟）
2. **端口冲突**时会自动寻找可用端口
3. **日志文件**保存在 `.dev-pids/` 目录
4. **PID 文件**在停止时自动清理
5. 确保在**项目根目录**下运行脚本

---

**最后更新**: 2025-10-09  
**脚本数量**: 8 个核心脚本（4 个开发 + 3 个部署 + SQL）

---

## 📦 归档说明

以下脚本已完成使命并归档至 `archive/scripts/`：

- `cleanup_local.sh` - 本地环境清理（已执行，节省 94MB）
- `cleanup_production.sh` - 生产环境清理（已执行，节省 ~200MB）
- `deploy_to_alicloud.sh` - 初次部署脚本（已被 deploy-to-production.sh 取代）

已删除的临时脚本：

- `backup_database.sh` - 临时备份脚本
- `setup_ssl.sh` / `renew_ssl.sh` - SSL 配置脚本（已完成配置）
- `migrate_database.py` - 旧迁移脚本（功能重复）
- `create_missing_tables.py` - 临时数据库绕过方案
