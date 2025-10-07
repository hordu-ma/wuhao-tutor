# 五好伴学开发脚本

本目录包含五好伴学项目的核心开发脚本（已精简，仅保留必需功能）。

## 📁 脚本列表

| 脚本 | 功能 | 用途 |
|------|------|------|
| `start-dev.sh` | 启动开发服务器 | 启动前端(Vite) + 后端(FastAPI) |
| `stop-dev.sh` | 停止开发服务器 | 优雅停止所有开发服务 |
| `status-dev.sh` | 检查服务状态 | 查看进程、端口、资源使用 |
| `start-frontend-dev.sh` | 启动前端 | 仅启动Vue3前端服务 |

### SQL 脚本 (sql/)
- `01-init-extensions.sql` - 初始化 PostgreSQL 扩展
- `02-create-indexes.sql` - 创建数据库索引

---

## 🚀 快速开始

```bash
# 1. 启动开发环境
./scripts/start-dev.sh

# 2. 查看服务状态
./scripts/status-dev.sh

# 3. 停止服务
./scripts/stop-dev.sh
```

---

## 📖 脚本说明

### start-dev.sh
**功能：**
- 自动检查 Python 3.11+ 和 Node.js 18+
- 自动安装依赖（uv sync + npm install）
- 智能端口分配（避免冲突）
- 同时启动前后端服务

**默认端口：**
- 前端：5173（自动寻找可用端口）
- 后端：8000（自动寻找可用端口）

**生成文件：**
- `.dev-pids/frontend.pid` - 前端进程ID
- `.dev-pids/backend.pid` - 后端进程ID
- `.dev-pids/*.log` - 服务日志

---

### stop-dev.sh
**功能：** 优雅停止开发服务器并清理资源

**参数：**
```bash
./scripts/stop-dev.sh              # 正常停止
./scripts/stop-dev.sh --clean-logs # 停止并删除日志
./scripts/stop-dev.sh --force      # 强制杀死进程
```

---

### status-dev.sh
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

**最后更新**: 2025-10-07  
**脚本数量**: 4个核心脚本（已精简）
