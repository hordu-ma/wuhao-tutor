# 五好伴学 - 生产环境部署标准流程

## 📋 版本信息

- 文档版本: v1.1
- 创建日期: 2025-10-08
- 更新日期: 2025-11-13
- 部署方式: Python + systemd (非 Docker)
- 生产状态: ✅ 运行中 (https://www.horsduroot.com)

---

## 问题 4: 生产环境部署标准流程

### 🎯 部署目标

将本地开发完成的新功能安全、可靠地部署到阿里云生产环境。

---

## 📐 部署架构

```
本地开发环境 (macOS)
    ↓
[代码验证] → [构建前端] → [Git推送]
    ↓
生产服务器 (阿里云 ECS - 121.199.173.244)
    ↓
[拉取代码] → [安装依赖] → [日志轮转检查] → [数据库迁移] → [重启服务]
    ↓
[健康检查] → [API 验证] → [监控检查]
    ↓
访问地址: https://www.horsduroot.com
```

## 📊 当前生产环境状态

**更新: 2025-11-13**

| 项目        | 状态        | 说明                               |
| ----------- | ----------- | ---------------------------------- |
| 应用服务    | ✅ 运行中   | 内存占用 <200MB                    |
| 数据库      | ✅ 连接正常 | PostgreSQL RDS                     |
| 缓存系统    | ✅ 连接正常 | Redis RDS                          |
| 日志轮转    | ✅ 已配置   | /etc/logrotate.d/wuhao-tutor       |
| Python 缓存 | ✅ 已优化   | -B 参数禁用 .pyc 生成              |
| 磁盘使用    | ✅ 充足     | 24% (8.6GB/40GB)                   |
| SSL 证书    | ✅ 有效     | Let's Encrypt, 有效期至 2026-01-17 |
| Nginx       | ✅ 运行中   | 反向代理配置正确                   |

---

## 🔄 标准部署流程

### 阶段 1: 开发完成 (本地)

#### 步骤 1.1: 代码质量检查

```bash
#!/bin/bash
# 文件: scripts/pre_deploy_check.sh

echo "🔍 开始部署前检查..."

# 1. 运行代码验证
python scripts/verify_local_code.py
if [ $? -ne 0 ]; then
    echo "❌ 代码验证失败"
    exit 1
fi

# 2. 运行测试 (如果有)
if [ -f "pytest.ini" ]; then
    echo "🧪 运行测试..."
    pytest tests/ -v --tb=short || exit 1
fi

# 3. 检查 .env 文件
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "❌ 错误: .env 文件不应提交到Git"
    exit 1
fi

# 4. 检查代码格式
echo "📝 检查代码格式..."
black --check src/ || exit 1
# flake8 src/ || exit 1

echo "✅ 部署前检查通过"
```

#### 步骤 1.2: 构建前端

```bash
#!/bin/bash
# 文件: scripts/build_frontend.sh

echo "🏗️  构建前端..."

cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 检查构建产物
if [ ! -d "dist" ]; then
    echo "❌ 前端构建失败"
    exit 1
fi

echo "✅ 前端构建完成: $(du -sh dist | cut -f1)"

cd ..
```

#### 步骤 1.3: 提交代码

```bash
#!/bin/bash
# 文件: scripts/commit_changes.sh

# 查看变更
git status

# 添加文件
git add src/ frontend/dist/ alembic/versions/

# 提交 (遵循约定式提交)
git commit -m "feat: 添加新功能描述

- 详细说明1
- 详细说明2

Refs: #issue-number"

# 推送到远程
git push origin main
```

---

### 阶段 2: 部署准备 (服务器)

#### 步骤 2.1: 备份现有环境

```bash
#!/bin/bash
# 文件: scripts/deploy/backup_production.sh
# 在服务器上执行

BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/wuhao-tutor"

echo "💾 备份生产环境..."

# 1. 备份代码
echo "📦 备份代码..."
tar -czf "$BACKUP_DIR/code_$TIMESTAMP.tar.gz" \
    -C /opt wuhao-tutor \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='*.pyc' \
    --exclude='__pycache__'

# 2. 备份数据库
echo "🗄️  备份数据库..."
pg_dump -h $DB_HOST -U $DB_USER -d wuhao_tutor \
    | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# 3. 备份 .env
cp /opt/wuhao-tutor/.env "$BACKUP_DIR/env_$TIMESTAMP"

# 4. 清理旧备份 (保留最近5个)
ls -t $BACKUP_DIR/code_*.tar.gz | tail -n +6 | xargs rm -f
ls -t $BACKUP_DIR/db_*.sql.gz | tail -n +6 | xargs rm -f

echo "✅ 备份完成: $BACKUP_DIR"
ls -lh $BACKUP_DIR | tail -10
```

#### 步骤 2.2: 拉取最新代码

```bash
#!/bin/bash
# 文件: scripts/deploy/pull_code.sh
# 在服务器上执行

APP_DIR="/opt/wuhao-tutor"

echo "📥 拉取最新代码..."

cd $APP_DIR

# 暂存本地修改 (如 .env)
git stash

# 拉取最新代码
git fetch origin
git checkout main
git pull origin main

# 恢复本地修改
git stash pop || true

echo "✅ 代码更新完成"
git log -1 --oneline
```

---

### 阶段 3: 部署执行 (服务器)

#### 步骤 3.1: 更新依赖

```bash
#!/bin/bash
# 文件: scripts/deploy/update_dependencies.sh

APP_DIR="/opt/wuhao-tutor"

echo "📦 更新依赖..."

cd $APP_DIR

# 激活虚拟环境
source venv/bin/activate

# 更新 Python 依赖
uv pip install -r requirements.txt --upgrade

# 检查依赖
uv pip list | grep -E "fastapi|uvicorn|sqlalchemy|pydantic"

echo "✅ 依赖更新完成"
```

#### 步骤 3.2: 数据库迁移

```bash
#!/bin/bash
# 文件: scripts/deploy/migrate_database.sh

APP_DIR="/opt/wuhao-tutor"

echo "🗄️  执行数据库迁移..."

cd $APP_DIR
source venv/bin/activate

# 检查待执行的迁移
echo "📋 检查迁移状态..."
alembic current
alembic history | head -10

# 执行迁移
echo "⬆️  执行迁移..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ 数据库迁移成功"
    alembic current
else
    echo "❌ 数据库迁移失败"
    exit 1
fi
```

#### 步骤 3.3: 部署前端

```bash
#!/bin/bash
# 文件: scripts/deploy/deploy_frontend.sh

APP_DIR="/opt/wuhao-tutor"
FRONTEND_DIR="/var/www/wuhao-tutor"

echo "🎨 部署前端..."

# 备份旧版本
if [ -d "$FRONTEND_DIR" ]; then
    mv $FRONTEND_DIR ${FRONTEND_DIR}_backup_$(date +%Y%m%d_%H%M%S)
fi

# 复制新版本
cp -r $APP_DIR/frontend/dist $FRONTEND_DIR

# 设置权限
chown -R www-data:www-data $FRONTEND_DIR
chmod -R 755 $FRONTEND_DIR

# 验证
ls -lh $FRONTEND_DIR/assets/ | head -5

echo "✅ 前端部署完成"
```

#### 步骤 3.4: 重启服务

```bash
#!/bin/bash
# 文件: scripts/deploy/restart_services.sh

echo "🔄 重启服务..."

# 1. 重启应用
echo "🐍 重启 wuhao-tutor..."
systemctl restart wuhao-tutor

# 等待启动
sleep 5

# 检查状态
systemctl status wuhao-tutor --no-pager -l | head -15

# 2. 重新加载 Nginx
echo "🌐 重新加载 Nginx..."
nginx -t && nginx -s reload

echo "✅ 服务重启完成"
```

---

### 阶段 4: 部署验证 (服务器)

#### 步骤 4.1: 健康检查

```bash
#!/bin/bash
# 文件: scripts/deploy/verify_deployment.sh

echo "🏥 健康检查..."

# 1. 检查服务状态
echo "📊 服务状态..."
systemctl is-active wuhao-tutor || {
    echo "❌ wuhao-tutor 服务未运行"
    journalctl -u wuhao-tutor -n 50 --no-pager
    exit 1
}

systemctl is-active nginx || {
    echo "❌ nginx 服务未运行"
    exit 1
}

# 2. 检查端口监听
echo "🔌 端口检查..."
netstat -tlnp | grep -E ':(80|443|8000)' || {
    echo "❌ 端口未正常监听"
    exit 1
}

# 3. 健康检查端点
echo "🩺 API 健康检查..."
curl -f -k https://localhost/api/health || {
    echo "❌ 健康检查失败"
    exit 1
}

# 4. 测试登录
echo "🔐 测试登录..."
TOKEN=$(curl -s -k -X POST https://localhost/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"phone":"13800000001","password":"password123"}' \
    | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ 登录测试失败"
    exit 1
fi

echo "✅ Token: ${TOKEN:0:20}..."

# 5. 测试核心 API
echo "🧪 测试核心功能..."
curl -s -k -H "Authorization: Bearer $TOKEN" \
    https://localhost/api/v1/learning/sessions?limit=1 \
    | jq '.total' || {
    echo "❌ API 测试失败"
    exit 1
}

echo "✅ 部署验证通过"
```

#### 步骤 4.2: 监控检查

```bash
#!/bin/bash
# 文件: scripts/deploy/check_monitoring.sh

echo "📊 监控检查..."

# 1. 检查错误日志
echo "📋 最近错误日志..."
journalctl -u wuhao-tutor -p err -n 10 --no-pager

# 2. 检查资源使用
echo "💻 资源使用..."
ps aux | grep -E 'uvicorn|nginx' | grep -v grep
free -h
df -h /

# 3. 检查网络连接
echo "🌐 网络连接..."
netstat -an | grep :8000 | wc -l
echo "当前活跃连接数"

echo "✅ 监控检查完成"
```

---

### 阶段 5: 回滚流程 (应急)

#### 回滚脚本

```bash
#!/bin/bash
# 文件: scripts/deploy/rollback.sh

BACKUP_DIR="/opt/backups"

echo "⏮️  开始回滚..."

# 1. 列出可用备份
echo "📦 可用备份:"
ls -lht $BACKUP_DIR/code_*.tar.gz | head -5

# 2. 选择备份版本
read -p "输入备份文件名 (或按Enter使用最新): " BACKUP_FILE

if [ -z "$BACKUP_FILE" ]; then
    BACKUP_FILE=$(ls -t $BACKUP_DIR/code_*.tar.gz | head -1)
fi

echo "使用备份: $BACKUP_FILE"

# 3. 停止服务
systemctl stop wuhao-tutor

# 4. 恢复代码
cd /opt
rm -rf wuhao-tutor_old
mv wuhao-tutor wuhao-tutor_old
tar -xzf $BACKUP_FILE

# 5. 恢复 .env (从同时间备份)
TIMESTAMP=$(basename $BACKUP_FILE | sed 's/code_\(.*\).tar.gz/\1/')
if [ -f "$BACKUP_DIR/env_$TIMESTAMP" ]; then
    cp "$BACKUP_DIR/env_$TIMESTAMP" /opt/wuhao-tutor/.env
fi

# 6. 重启服务
systemctl start wuhao-tutor

# 7. 验证
sleep 3
systemctl status wuhao-tutor --no-pager

echo "✅ 回滚完成"
```

## ⚠️ 部署前清单更新 (2025-11-13)

### 新增检查项

在部署前，请确保以下优化已在生产环境中：

- [ ] 日志轮转配置已验证 (`logrotate -d /etc/logrotate.d/wuhao-tutor`)
- [ ] 旧日志文件已清理或备份
- [ ] Python 缓存清理脚本已运行
- [ ] Systemd 配置包含 `-B` 参数
- [ ] 应用重启后 API 健康检查通过

---

## 🚀 一键部署脚本

综合所有步骤的主脚本:

```bash
#!/bin/bash
# 文件: scripts/deploy_to_production.sh

set -e

SERVER="root@121.199.173.244"  # 生产服务器 (www.horsduroot.com)
REMOTE_DIR="/opt/wuhao-tutor"

echo "🚀 开始部署到生产环境..."
echo "服务器: $SERVER"
echo "目录: $REMOTE_DIR"
echo ""

# ========== 本地阶段 ==========

echo "📍 阶段1: 本地准备"

# 1.1 代码检查
echo "🔍 代码检查..."
./scripts/pre_deploy_check.sh

# 1.2 构建前端
echo "🏗️  构建前端..."
./scripts/build_frontend.sh

# 1.3 确认部署
read -p "✅ 本地检查通过,确认部署到生产环境? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 取消部署"
    exit 1
fi

# ========== 服务器阶段 ==========

echo ""
echo "📍 阶段2: 服务器准备"

# 2.1 备份
echo "💾 备份生产环境..."
ssh $SERVER "bash /opt/wuhao-tutor/scripts/deploy/backup_production.sh"

# 2.2 拉取代码
echo "📥 拉取最新代码..."
ssh $SERVER "bash /opt/wuhao-tutor/scripts/deploy/pull_code.sh"

echo ""
echo "📍 阶段3: 部署执行"

# 3.1 同步文件 (仅关键文件)
echo "📤 同步文件到服务器..."
rsync -avz --delete \
    --exclude='venv/' \
    --exclude='node_modules/' \
    --exclude='*.db' \
    --exclude='.env' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='archive/' \
    ./src/ $SERVER:$REMOTE_DIR/src/

rsync -avz --delete \
    ./frontend/dist/ $SERVER:$REMOTE_DIR/frontend/dist/

rsync -avz \
    ./alembic/versions/ $SERVER:$REMOTE_DIR/alembic/versions/

# 3.2 更新依赖
echo "📦 更新依赖..."
ssh $SERVER "bash $REMOTE_DIR/scripts/deploy/update_dependencies.sh"

# 3.3 数据库迁移
echo "🗄️  数据库迁移..."
ssh $SERVER "bash $REMOTE_DIR/scripts/deploy/migrate_database.sh"

# 3.4 部署前端
echo "🎨 部署前端..."
ssh $SERVER "bash $REMOTE_DIR/scripts/deploy/deploy_frontend.sh"

# 3.5 重启服务
echo "🔄 重启服务..."
ssh $SERVER "bash $REMOTE_DIR/scripts/deploy/restart_services.sh"

echo ""
echo "📍 阶段4: 部署验证"

# 4.1 健康检查
echo "🏥 健康检查..."
ssh $SERVER "bash $REMOTE_DIR/scripts/deploy/verify_deployment.sh"

# 4.2 监控检查
echo "📊 监控检查..."
ssh $SERVER "bash $REMOTE_DIR/scripts/deploy/check_monitoring.sh"

# ========== 完成 ==========

echo ""
echo "=" * 60
echo "✅ 部署成功完成!"
echo "=" * 60
echo ""
echo "🌐 访问地址: https://www.horsduroot.com"
echo "📊 健康检查: https://www.horsduroot.com/health"
echo "📋 查看日志: ssh $SERVER 'journalctl -u wuhao-tutor -f'"
echo ""
echo "⏮️  如需回滚: ssh $SERVER 'bash $REMOTE_DIR/scripts/deploy/rollback.sh'"
```

**使用方法:**

```bash
# 确保脚本可执行
chmod +x scripts/deploy_to_production.sh

# 执行部署
./scripts/deploy_to_production.sh
```

---

## 📋 部署检查清单

### 部署前 (本地)

- [ ] 代码已提交到 Git
- [ ] 所有测试通过
- [ ] 前端已构建 (npm run build)
- [ ] .env 文件未提交
- [ ] 代码格式检查通过

### 部署中 (服务器)

- [ ] 已备份代码和数据库
- [ ] 代码拉取成功
- [ ] 依赖更新成功
- [ ] 数据库迁移成功
- [ ] 服务重启成功

### 部署后 (验证)

- [ ] 健康检查通过
- [ ] 登录功能正常
- [ ] 核心 API 正常
- [ ] 前端页面加载正常
- [ ] 无错误日志

---

## 🔧 故障排查

### 问题 1: 服务启动失败

```bash
# 查看服务日志
journalctl -u wuhao-tutor -n 100 --no-pager

# 查看错误详情
systemctl status wuhao-tutor -l

# 手动启动测试
cd /opt/wuhao-tutor
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 问题 2: 数据库迁移失败

```bash
# 检查迁移状态
alembic current
alembic history

# 回滚一个版本
alembic downgrade -1

# 重新迁移
alembic upgrade head
```

### 问题 3: 前端页面 404

```bash
# 检查 Nginx 配置
nginx -t

# 检查前端文件
ls -la /var/www/wuhao-tutor/

# 查看 Nginx 日志
tail -f /var/log/nginx/error.log
```

---

## 📊 部署日志示例

```
🚀 开始部署到生产环境...
服务器: root@121.199.173.244 (www.horsduroot.com)
目录: /opt/wuhao-tutor

📍 阶段1: 本地准备
🔍 代码检查...
✅ 所有关键文件完整
✅ 代码验证通过,可以安全部署到生产环境

🏗️  构建前端...
✅ 前端构建完成: 3.2M

📍 阶段2: 服务器准备
💾 备份生产环境...
✅ 备份完成: /opt/backups

📥 拉取最新代码...
✅ 代码更新完成

📍 阶段3: 部署执行
📤 同步文件到服务器...
✅ 文件同步完成

📦 更新依赖...
✅ 依赖更新完成

🗄️  数据库迁移...
✅ 数据库迁移成功

🎨 部署前端...
✅ 前端部署完成

🔄 重启服务...
✅ 服务重启完成

📍 阶段4: 部署验证
🏥 健康检查...
✅ Token: eyJhbGciOiJIUzI1NiIs...
✅ 部署验证通过

📊 监控检查...
✅ 监控检查完成

============================================================
✅ 部署成功完成!
============================================================

🌐 访问地址: https://www.horsduroot.com
📊 健康检查: https://www.horsduroot.com/health
```

---

## ✅ 总结

**部署方式:** Python + systemd (非 Docker)

**关键步骤:**

1. ✅ 本地代码检查和构建
2. ✅ 服务器备份
3. ✅ 代码同步和依赖更新
4. ✅ 数据库迁移
5. ✅ 服务重启
6. ✅ 验证测试

**安全保障:**

- 自动备份 (代码+数据库)
- 部署前检查
- 健康检查验证
- 快速回滚机制

**维护建议:**

- 定期清理旧备份 (保留最近 5 个)
- 监控服务日志
- 定期更新依赖
- 记录部署历史
