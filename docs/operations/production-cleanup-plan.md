# 五好伴学 - 生产环境清理计划

## 📋 生成时间

2025-10-08 23:40

## 🎯 清理目标

- 移除 Docker 相关冗余资源
- 清理过时的部署文件
- 优化磁盘空间使用
- 确保服务稳定运行

---

## 问题 1: 阿里云生产环境诊断与清理

### ✅ 当前状态概览

**运行服务:**

- ✅ wuhao-tutor.service (systemd) - 主应用 (4 workers)
- ✅ nginx.service - 反向代理 (HTTP/HTTPS)
- ⚠️ docker.service - 运行但未使用
- ⚠️ supervisord - 运行但未使用

**资源使用:**

- 磁盘: 7.5G/40G (21% 使用)
- /opt/wuhao-tutor: 1.1G
- /opt/backups: 262M
- 日志: 120M (journald)

**端口占用:**

- :80 (nginx)
- :443 (nginx)
- :8000 (uvicorn)

---

### 🗑️ 需要清理的项目

#### 1. Docker 相关资源 (无需保留)

**Docker 镜像:**

```bash
# 当前镜像
nginx:alpine      - 58.8MB
python:3.11-slim  - 125MB
```

**问题:** Docker 服务在运行但完全未使用,占用系统资源

**清理命令:**

```bash
# 1. 停止并禁用 Docker 服务
sudo systemctl stop docker
sudo systemctl disable docker

# 2. 删除所有镜像和容器
sudo docker system prune -a -f --volumes

# 3. (可选) 完全卸载 Docker
sudo apt-get remove -y docker.io docker-compose
sudo apt-get autoremove -y

# 释放空间: ~184MB
```

#### 2. 冗余部署文件

**文件清单:**

```
/opt/deploy-package.tar.gz          - 2.3M  (旧部署包)
/opt/wuhao-tutor/*.tar.gz           - 需检查
/opt/wuhao-tutor/docker-compose.*   - 不再需要
/opt/wuhao-tutor/Dockerfile*        - 不再需要
/opt/wuhao-tutor/._*                - macOS 垃圾文件
```

**清理命令:**

```bash
# 删除旧部署包
sudo rm /opt/deploy-package.tar.gz

cd /opt/wuhao-tutor

# 删除 Docker 相关文件
sudo rm -f docker-compose*.yml Dockerfile* .dockerignore

# 删除 macOS 元数据文件
sudo find . -name '._*' -delete
sudo find . -name '.DS_Store' -delete

# 删除临时脚本
sudo rm -f check_schema.py create_test_user.py

# 释放空间: ~10MB
```

#### 3. Supervisord 服务 (未使用)

**问题:** 系统中运行 supervisord 但未配置任何管理任务

**清理命令:**

```bash
# 停止并禁用 supervisord
sudo systemctl stop supervisor
sudo systemctl disable supervisor

# (可选) 卸载
sudo apt-get remove -y supervisor
sudo apt-get autoremove -y
```

#### 4. 日志文件优化

**当前状态:**

- journald: 120M
- nginx logs: ~250K

**优化配置:**

```bash
# 限制 journald 大小
sudo journalctl --vacuum-size=50M
sudo journalctl --vacuum-time=7d

# 配置日志轮转
sudo nano /etc/systemd/journald.conf
# 添加:
# SystemMaxUse=100M
# MaxRetentionSec=7day

sudo systemctl restart systemd-journald
```

#### 5. 备份目录清理

**路径:** `/opt/backups` (262M)

**清理策略:**

```bash
# 仅保留最近3个备份
cd /opt/backups
ls -t | tail -n +4 | xargs rm -f

# 释放空间: ~200MB
```

---

### 📊 清理后预期效果

| 项目        | 清理前 | 清理后 | 释放空间   |
| ----------- | ------ | ------ | ---------- |
| Docker 镜像 | 184MB  | 0      | 184MB      |
| 部署文件    | ~10MB  | 0      | 10MB       |
| 日志文件    | 120MB  | 50MB   | 70MB       |
| 备份文件    | 262MB  | 60MB   | 200MB      |
| **总计**    | ~576MB | 110MB  | **~464MB** |

---

### 🔧 完整清理脚本

保存为: `/opt/cleanup_production.sh`

```bash
#!/bin/bash
set -e

echo "🧹 开始清理阿里云生产环境..."

# 1. 停止未使用的服务
echo "📦 停止 Docker 和 Supervisord..."
systemctl stop docker || true
systemctl disable docker || true
systemctl stop supervisor || true
systemctl disable supervisor || true

# 2. 清理 Docker 资源
echo "🐋 清理 Docker 资源..."
docker system prune -a -f --volumes 2>/dev/null || true

# 3. 删除冗余文件
echo "🗑️ 删除冗余部署文件..."
rm -f /opt/deploy-package.tar.gz
cd /opt/wuhao-tutor
rm -f docker-compose*.yml Dockerfile* .dockerignore
find . -name '._*' -delete
find . -name '.DS_Store' -delete
rm -f check_schema.py create_test_user.py =5.9.0

# 4. 清理日志
echo "📋 清理日志文件..."
journalctl --vacuum-size=50M
journalctl --vacuum-time=7d

# 5. 清理旧备份 (保留最近3个)
echo "💾 清理旧备份..."
cd /opt/backups
ls -t | tail -n +4 | xargs rm -f 2>/dev/null || true

# 6. 显示清理结果
echo "✅ 清理完成!"
echo ""
echo "📊 当前磁盘使用:"
df -h /
echo ""
echo "📁 /opt 目录大小:"
du -sh /opt/*

# 7. 验证服务状态
echo ""
echo "🔍 验证关键服务:"
systemctl status wuhao-tutor --no-pager -l | head -10
systemctl status nginx --no-pager -l | head -10
```

**执行方法:**

```bash
# 上传到服务器
scp PRODUCTION_CLEANUP_PLAN.md root@121.199.173.244:/opt/

# 创建并执行清理脚本
ssh root@121.199.173.244 'bash -s' < cleanup_production.sh

# 或手动执行
ssh root@121.199.173.244
sudo bash /opt/cleanup_production.sh
```

---

### ⚠️ 注意事项

1. **执行前备份:** 虽然清理的都是冗余文件,但建议先创建快照
2. **服务验证:** 清理后验证 wuhao-tutor 和 nginx 服务正常
3. **定期清理:** 建议每月执行一次备份和日志清理
4. **监控告警:** 配置磁盘使用告警 (>80%)

---

### 🔍 清理后验证清单

```bash
# 1. 验证服务状态
systemctl status wuhao-tutor nginx

# 2. 验证端口监听
netstat -tlnp | grep -E ':(80|443|8000)'

# 3. 验证应用可访问
curl -k https://121.199.173.244/api/health

# 4. 检查磁盘空间
df -h

# 5. 检查进程
ps aux | grep -E 'uvicorn|nginx' | grep -v grep
```

---

### 📅 定期维护建议

**每周:**

- 检查服务日志: `journalctl -u wuhao-tutor -n 100`
- 验证应用健康: `curl https://121.199.173.244/api/health`

**每月:**

- 清理旧日志: `journalctl --vacuum-time=30d`
- 清理旧备份: 保留最近 30 天
- 检查磁盘使用: `df -h`

**每季度:**

- 更新系统包: `apt update && apt upgrade`
- 更新 SSL 证书 (如需要)
- 性能评估和优化

---

## ✅ 总结

**当前问题:**

- Docker 服务运行但未使用 (184MB)
- 存在多个旧部署文件 (10MB)
- 日志文件累积 (120MB)
- 旧备份文件过多 (262MB)

**清理收益:**

- 释放 ~464MB 磁盘空间
- 减少 2 个无用后台服务
- 降低系统资源消耗
- 简化维护流程

**风险评估:** ⭐ 低风险

- 所有清理项均为冗余资源
- 不影响当前生产服务
- 可随时回滚 (通过备份快照)
