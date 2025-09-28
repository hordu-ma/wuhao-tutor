# 五好伴学开发环境脚本使用说明

本目录包含了五好伴学项目的开发环境管理脚本，提供了完整的开发服务器启动、停止、状态检查和重启功能。

## 📁 脚本概览

| 脚本名称 | 功能说明 | 推荐使用场景 |
|---------|---------|-------------|
| `start-dev.sh` | 启动前端和后端开发服务器 | 开始开发工作 |
| `stop-dev.sh` | 停止所有开发服务器 | 结束开发工作 |
| `restart-dev.sh` | 重启开发环境 | 配置变更后重启 |
| `status-dev.sh` | 检查服务运行状态 | 诊断问题 |
| `start-frontend-dev.sh` | 仅启动前端服务器（旧版本） | 单独前端开发 |

## 🚀 快速开始

### 1. 启动开发环境
```bash
# 启动前端和后端服务器
./scripts/start-dev.sh
```

### 2. 检查运行状态
```bash
# 查看服务状态
./scripts/status-dev.sh

# 查看详细状态
./scripts/status-dev.sh --verbose
```

### 3. 停止开发环境
```bash
# 正常停止服务
./scripts/stop-dev.sh

# 停止服务并清理日志
./scripts/stop-dev.sh --clean-logs
```

## 📖 详细说明

### start-dev.sh - 开发环境启动脚本

**功能特点：**
- 自动检查 Python 和 Node.js 环境
- 自动安装和管理依赖
- 智能端口分配（避免端口冲突）
- 同时启动前端和后端服务器
- 提供健康检查和状态监控
- 保存进程PID便于管理

**环境要求：**
- Python 3.11+
- Node.js 18+
- uv 包管理器
- 支持的前端包管理器：npm、yarn、pnpm

**使用方法：**
```bash
# 基础启动
./scripts/start-dev.sh

# 查看启动过程详细信息
./scripts/start-dev.sh 2>&1 | tee dev-startup.log
```

**默认端口分配：**
- 前端：5173-5200 (自动寻找可用端口)
- 后端：8000-8020 (自动寻找可用端口)

**生成文件：**
- `.dev-pids/frontend.pid` - 前端服务器进程ID
- `.dev-pids/backend.pid` - 后端服务器进程ID
- `.dev-pids/frontend.log` - 前端服务器日志
- `.dev-pids/backend.log` - 后端服务器日志

---

### stop-dev.sh - 开发环境停止脚本

**功能特点：**
- 优雅停止所有开发服务器
- 支持强制停止模式
- 自动清理相关进程
- 保留或清理日志文件
- 验证停止状态

**使用方法：**
```bash
# 正常停止
./scripts/stop-dev.sh

# 停止并清理日志
./scripts/stop-dev.sh --clean-logs

# 强制停止所有相关进程
./scripts/stop-dev.sh --force

# 查看帮助
./scripts/stop-dev.sh --help
```

**参数说明：**
- `--clean-logs` : 停止服务并删除所有日志文件
- `--force` : 强制杀死所有相关进程，不等待优雅停止
- `--help` : 显示使用帮助

---

### status-dev.sh - 状态检查脚本

**功能特点：**
- 检查前端和后端服务运行状态
- 显示进程信息（CPU、内存使用率）
- 端口监听状态检查
- 服务健康状态检查
- 系统资源监控
- 持续监控模式

**使用方法：**
```bash
# 基本状态检查
./scripts/status-dev.sh

# 详细状态信息
./scripts/status-dev.sh --verbose

# 持续监控模式（每5秒刷新）
./scripts/status-dev.sh --watch

# 查看帮助
./scripts/status-dev.sh --help
```

**状态指示：**
- ✓ 绿色：服务正常运行
- ✗ 红色：服务异常或未运行
- ⚠️ 黄色：警告或需要注意的状态

---

### restart-dev.sh - 重启脚本

**功能特点：**
- 安全停止并重新启动开发环境
- 支持快速重启模式
- 自动验证重启状态
- 保留或清理启动日志

**使用方法：**
```bash
# 正常重启
./scripts/restart-dev.sh

# 重启并清理日志
./scripts/restart-dev.sh --clean-logs

# 强制重启
./scripts/restart-dev.sh --force

# 快速重启（跳过环境检查）
./scripts/restart-dev.sh --quick
```

**重启流程：**
1. 检查当前服务状态
2. 安全停止所有服务
3. 清理相关进程和资源
4. 重新启动服务
5. 验证启动状态

---

## 🛠️ 高级用法

### 并发开发
```bash
# 启动多个开发环境实例（不同端口）
VITE_DEV_PORT=5174 BACKEND_PORT=8001 ./scripts/start-dev.sh
```

### 日志管理
```bash
# 实时查看前端日志
tail -f .dev-pids/frontend.log

# 实时查看后端日志
tail -f .dev-pids/backend.log

# 查看所有日志
tail -f .dev-pids/*.log
```

### 调试模式
```bash
# 启用详细日志
DEBUG=true ./scripts/start-dev.sh

# 查看启动详细信息
./scripts/start-dev.sh 2>&1 | tee startup-debug.log
```

### 生产环境准备
```bash
# 检查所有服务状态
./scripts/status-dev.sh --verbose

# 优雅停止所有服务
./scripts/stop-dev.sh

# 清理所有临时文件
./scripts/stop-dev.sh --clean-logs
```

---

## 🔧 故障排除

### 常见问题

**1. 端口被占用**
```bash
# 查看端口占用情况
lsof -i :5173
lsof -i :8000

# 强制停止相关进程
./scripts/stop-dev.sh --force
```

**2. 服务启动失败**
```bash
# 检查详细状态
./scripts/status-dev.sh --verbose

# 查看错误日志
tail -50 .dev-pids/frontend.log
tail -50 .dev-pids/backend.log
```

**3. 环境依赖问题**
```bash
# 重新安装依赖
rm -rf .venv frontend/node_modules
./scripts/start-dev.sh
```

**4. 进程残留**
```bash
# 强制清理所有相关进程
./scripts/stop-dev.sh --force

# 手动清理
pkill -f "uvicorn src.main:app"
pkill -f "vite.*--port"
```

### 日志文件说明

- **前端日志** (`.dev-pids/frontend.log`)
  - Vite 开发服务器输出
  - 编译错误和警告
  - 热更新信息

- **后端日志** (`.dev-pids/backend.log`)
  - FastAPI 应用输出
  - API 请求日志
  - 数据库连接信息
  - 错误堆栈跟踪

---

## 📝 最佳实践

### 开发工作流

1. **开始工作**
   ```bash
   ./scripts/start-dev.sh
   ```

2. **检查状态**
   ```bash
   ./scripts/status-dev.sh
   ```

3. **开发过程中**
   - 代码会自动热重载
   - 查看浏览器控制台和服务器日志
   - 使用 API 文档调试接口

4. **遇到问题时**
   ```bash
   ./scripts/status-dev.sh --verbose
   ./scripts/restart-dev.sh
   ```

5. **结束工作**
   ```bash
   ./scripts/stop-dev.sh
   ```

### 性能优化

- 使用 `--quick` 模式快速重启
- 定期清理日志文件
- 监控系统资源使用情况
- 合理配置端口范围

### 团队协作

- 统一使用脚本启动开发环境
- 共享脚本配置和最佳实践
- 定期更新脚本版本
- 记录常见问题和解决方案

---

## 🔄 版本更新

### v2.0 (当前版本)
- ✅ 同时支持前端和后端服务
- ✅ 智能端口分配
- ✅ 完整的服务生命周期管理
- ✅ 详细的状态检查和监控
- ✅ 优雅的停止和重启机制

### v1.0 (旧版本)
- 仅支持前端服务 (`start-frontend-dev.sh`)
- 基础的启动和停止功能

---

## 📞 支持

如果遇到问题或需要功能改进，请：

1. 查看本文档的故障排除部分
2. 检查项目的 GitHub Issues
3. 联系开发团队
4. 提交 Pull Request

---

**注意事项：**
- 确保在项目根目录下运行脚本
- 首次运行可能需要较长时间安装依赖
- 建议定期更新开发环境和依赖包
- 生产环境请勿使用这些开发脚本

**Happy Coding! 🎉**
