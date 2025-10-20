# 生产环境部署脚本使用指南

## 快速开始

```bash
# 一键部署后端 + 前端
./scripts/deploy.sh
```

## 脚本功能

✅ **自动化部署流程**：

1. 后端 Python 服务（FastAPI）
2. 前端 Vue3 应用

❌ **不包含**：

- 微信小程序（在本地开发工具中编译上传）

## 部署内容

### 后端服务

- **部署路径**: `/opt/wuhao-tutor`
- **服务名**: `wuhao-tutor.service`
- **同步内容**: `src/`, `alembic/`, 配置文件
- **自动重启**: 是

### 前端应用

- **部署路径**: `/var/www/html`
- **构建命令**: `npm run build`
- **同步内容**: `frontend/dist/`

## 生产环境信息

- **服务器**: 121.199.173.244
- **域名**: horsduroot.com
- **前端地址**: https://horsduroot.com
- **后端 API**: https://horsduroot.com/api/v1/
- **健康检查**: https://horsduroot.com/api/v1/health

## 查看日志

```bash
# 后端服务日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'

# Nginx 访问日志
ssh root@121.199.173.244 'tail -f /var/log/nginx/access.log'

# Nginx 错误日志
ssh root@121.199.173.244 'tail -f /var/log/nginx/error.log'
```

## 手动操作

```bash
# 仅部署后端
rsync -avz --exclude='venv' --exclude='*.pyc' src/ root@121.199.173.244:/opt/wuhao-tutor/
ssh root@121.199.173.244 'systemctl restart wuhao-tutor.service'

# 仅部署前端
cd frontend && npm run build
rsync -avz dist/ root@121.199.173.244:/var/www/html/

# 检查后端服务状态
ssh root@121.199.173.244 'systemctl status wuhao-tutor.service'

# 查看后端运行日志（最后50行）
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -n 50 --no-pager'
```

## 故障排查

### 1. 部署失败

```bash
# 检查 SSH 连接
ssh root@121.199.173.244 'echo "连接正常"'

# 检查磁盘空间
ssh root@121.199.173.244 'df -h'
```

### 2. 后端服务无法启动

```bash
# 查看详细错误
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -n 100 --no-pager'

# 手动启动测试
ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && python -m src.main'
```

### 3. 前端访问 404

```bash
# 检查文件是否存在
ssh root@121.199.173.244 'ls -la /var/www/html/'

# 检查 Nginx 配置
ssh root@121.199.173.244 'nginx -t'
ssh root@121.199.173.244 'systemctl reload nginx'
```

## 注意事项

⚠️ **生产环境配置**：

- `.env.production` 文件在服务器上，不会被覆盖
- 数据库迁移需要手动执行：`ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'`
- 前端构建需要 Node.js 和 npm（本地执行）

✅ **最佳实践**：

- 部署前先在本地测试构建：`cd frontend && npm run build`
- 部署后检查健康端点：`curl https://horsduroot.com/api/v1/health`
- 重要更新建议在低峰时段部署

## 版本历史

- **2025-10-20**: 创建统一部署脚本，移除旧脚本
- 移除的旧脚本：
  - `deploy_to_production.sh` (卡在 npm install)
  - `deploy_auto.sh`
  - `deploy-mobile-image-fix.sh`
  - `deploy-miniprogram.sh`
  - `deploy-experience-version.sh`
