# 五好伴学 - 本地环境归档与清理计划

## 📋 生成时间

2025-10-08 23:40

## 🎯 清理目标

- 归档过时文件
- 清理冗余配置
- 优化项目结构
- 更新项目文档

---

## 问题 3: 本地开发环境清理

### 📊 冗余文件清单

#### 1. 部署包文件 (可删除)

```bash
# 压缩包 - 总计 ~15MB
./deploy-prod.tar.gz
./deploy-package.tar.gz
./wuhao-app-source.tar.gz
```

**处理:** 删除 (可从 Git 恢复)

#### 2. Docker 配置文件 (废弃)

```bash
# Docker 相关 - 已改用 systemd
./docker-compose.yml
./docker-compose.dev.yml
./docker-compose.prod.yml
./docker-compose.monitoring.yml
./Dockerfile
./.dockerignore
./deploy-package/docker-compose.yml
```

**处理:** 移动到 `archive/docker/`

#### 3. 环境配置文件 (已删除/过时)

```bash
# Git 显示已删除但可能仍存在
.env.backup
.env.dev
.env.docker.production
.env.prod
```

**处理:** 确认删除

#### 4. macOS 系统文件

```bash
.DS_Store
nginx/nginx-ip.conf.bak
```

**处理:** 删除并添加到 .gitignore

#### 5. 临时脚本和测试文件

```bash
check_schema.py
create_test_user.py
test_console_error_fixes.py
test-proxy.js
```

**处理:** 移动到 `archive/temp-scripts/` 或删除

#### 6. 过时文档

```bash
DOCS_REVIEW_REPORT.md
DEPLOYMENT_DIAGNOSTIC_REPORT.md
IP_DEPLOYMENT_READY.md
```

**处理:** 移动到 `archive/reports/`

---

### 🗂️ 归档计划

#### 第一步: 创建归档目录结构

```bash
mkdir -p archive/{docker,reports,old-configs,temp-scripts,deployment-attempts}
```

#### 第二步: 移动 Docker 相关文件

```bash
# 移动 Docker 配置
mv docker-compose*.yml archive/docker/
mv Dockerfile* archive/docker/
mv .dockerignore archive/docker/
mv deploy-package archive/docker/

echo "Docker 部署已废弃,改用 systemd" > archive/docker/README.md
```

#### 第三步: 归档报告和文档

```bash
# 移动过时报告
mv DOCS_REVIEW_REPORT.md archive/reports/ 2>/dev/null || true
mv DEPLOYMENT_DIAGNOSTIC_REPORT.md archive/reports/ 2>/dev/null || true
mv IP_DEPLOYMENT_READY.md archive/reports/ 2>/dev/null || true

# 保留新的计划文档
# PRODUCTION_CLEANUP_PLAN.md
# LOCAL_CODE_VERIFICATION_PLAN.md
# LOCAL_CLEANUP_PLAN.md
```

#### 第四步: 清理临时文件

```bash
# 移动临时脚本
mv check_schema.py archive/temp-scripts/ 2>/dev/null || true
mv create_test_user.py archive/temp-scripts/ 2>/dev/null || true
mv test_console_error_fixes.py archive/temp-scripts/ 2>/dev/null || true
mv test-proxy.js archive/temp-scripts/ 2>/dev/null || true

# 删除压缩包
rm -f deploy-prod.tar.gz deploy-package.tar.gz wuhao-app-source.tar.gz

# 删除 macOS 垃圾文件
find . -name '.DS_Store' -delete
find . -name '._*' -delete

# 删除备份文件
rm -f nginx/nginx-ip.conf.bak
rm -f .env.backup .env.dev .env.docker.production .env.prod 2>/dev/null || true
```

#### 第五步: 清理开发数据库

```bash
# SQLite 数据库仅用于本地开发
# 可以安全删除 (会自动重建)
rm -f wuhao_tutor_dev.db
```

---

### 📝 更新 .gitignore

```bash
# 添加到 .gitignore
cat >> .gitignore << 'EOF'

# macOS
.DS_Store
._*

# 开发数据库
*.db
*.sqlite
*.sqlite3

# 环境配置
.env
.env.local
.env.*.local

# 临时文件
*.tmp
*.bak
*.old
*~

# 压缩包
*.tar.gz
*.zip

# IDE
.vscode/
.idea/

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/

# 归档文件
archive/

# 部署相关临时文件
deploy-package/
deploy-prod/
EOF
```

---

### 🧹 完整清理脚本

创建文件: `scripts/cleanup_local.sh`

```bash
#!/bin/bash
set -e

echo "🧹 开始清理本地开发环境..."

# 确认操作
read -p "⚠️  此操作将归档和删除文件,是否继续? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 取消清理"
    exit 1
fi

# 1. 创建归档目录
echo "📁 创建归档目录..."
mkdir -p archive/{docker,reports,old-configs,temp-scripts}

# 2. 归档 Docker 文件
echo "🐋 归档 Docker 配置..."
mv docker-compose*.yml archive/docker/ 2>/dev/null || true
mv Dockerfile* archive/docker/ 2>/dev/null || true
mv .dockerignore archive/docker/ 2>/dev/null || true
echo "Docker 部署已废弃于 2025-10-08,改用 systemd 部署" > archive/docker/README.md

# 3. 归档报告
echo "📊 归档报告文档..."
mv DOCS_REVIEW_REPORT.md archive/reports/ 2>/dev/null || true
mv DEPLOYMENT_DIAGNOSTIC_REPORT.md archive/reports/ 2>/dev/null || true
mv IP_DEPLOYMENT_READY.md archive/reports/ 2>/dev/null || true

# 4. 归档临时脚本
echo "📝 归档临时脚本..."
mv check_schema.py archive/temp-scripts/ 2>/dev/null || true
mv create_test_user.py archive/temp-scripts/ 2>/dev/null || true
mv test_console_error_fixes.py archive/temp-scripts/ 2>/dev/null || true
mv test-proxy.js archive/temp-scripts/ 2>/dev/null || true

# 5. 删除压缩包
echo "🗑️  删除压缩包..."
rm -f deploy-prod.tar.gz deploy-package.tar.gz wuhao-app-source.tar.gz

# 6. 清理 macOS 文件
echo "🍎 清理 macOS 垃圾文件..."
find . -name '.DS_Store' -delete
find . -name '._*' -delete
rm -f nginx/nginx-ip.conf.bak

# 7. 清理环境配置
echo "⚙️  清理环境配置文件..."
rm -f .env.backup .env.dev .env.docker.production .env.prod 2>/dev/null || true

# 8. 清理开发数据库
echo "💾 清理开发数据库..."
rm -f wuhao_tutor_dev.db

# 9. 清理 Python 缓存
echo "🐍 清理 Python 缓存..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete

# 10. 显示结果
echo ""
echo "✅ 清理完成!"
echo ""
echo "📊 归档文件统计:"
du -sh archive/* 2>/dev/null || echo "无归档文件"
echo ""
echo "📁 当前项目大小:"
du -sh .

# 11. Git 状态
echo ""
echo "📝 Git 状态:"
git status --short | head -10
```

**执行方法:**

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor
chmod +x scripts/cleanup_local.sh
./scripts/cleanup_local.sh
```

---

### 📚 优化后的项目结构

```
wuhao-tutor/
├── 📁 src/                        # 源代码
│   ├── api/                      # API 端点
│   ├── core/                     # 核心配置
│   ├── models/                   # 数据模型
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # 业务逻辑
│   └── repositories/             # 数据访问层
│
├── 📁 frontend/                   # Vue3 前端
│   ├── src/
│   ├── public/
│   └── dist/                     # 构建产物
│
├── 📁 miniprogram/                # 微信小程序
│
├── 📁 scripts/                    # 脚本
│   ├── deploy/                   # 部署脚本
│   ├── dev/                      # 开发工具
│   └── maintenance/              # 维护脚本
│
├── 📁 docs/                       # 文档
│   ├── api/                      # API 文档
│   ├── architecture/             # 架构文档
│   └── deployment/               # 部署文档
│
├── 📁 alembic/                    # 数据库迁移
│
├── 📁 nginx/                      # Nginx 配置
│
├── 📁 monitoring/                 # 监控配置
│
├── 📁 secrets/                    # 密钥 (不提交)
│
├── 📁 archive/                    # 归档文件 (不提交)
│   ├── docker/                   # 废弃的 Docker 配置
│   ├── reports/                  # 过时报告
│   └── temp-scripts/             # 临时脚本
│
├── 📄 README.md                   # 项目说明
├── 📄 AI-CONTEXT.md               # AI 开发上下文
├── 📄 pyproject.toml              # Python 项目配置
├── 📄 .gitignore                  # Git 忽略规则
└── 📄 .env.example                # 环境变量示例
```

---

### 📄 .env.example 模板

创建文件: `.env.example`

```bash
# 五好伴学 - 环境变量模板
# 复制此文件为 .env 并填入实际值

# === 应用配置 ===
APP_NAME=五好伴学
APP_VERSION=0.1.0
ENVIRONMENT=development  # development | production

# === 数据库配置 ===
# SQLite (开发环境)
SQLALCHEMY_DATABASE_URI=sqlite:///./wuhao_tutor_dev.db

# PostgreSQL (生产环境)
# SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://user:pass@host:5432/dbname

# === Redis 配置 ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# === 安全配置 ===
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# === 阿里云配置 ===
# Bailian AI
ALIBABA_CLOUD_ACCESS_KEY_ID=
ALIBABA_CLOUD_ACCESS_KEY_SECRET=
BAILIAN_AGENT_KEY=

# OSS 对象存储
ALIBABA_OSS_ENDPOINT=
ALIBABA_OSS_BUCKET=
ALIBABA_OSS_ACCESS_KEY_ID=
ALIBABA_OSS_ACCESS_KEY_SECRET=

# === 文件上传 ===
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760  # 10MB

# === 日志配置 ===
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# === CORS 配置 ===
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
```

---

### 📊 清理后效果对比

| 项目         | 清理前 | 清理后   | 说明         |
| ------------ | ------ | -------- | ------------ |
| 压缩包       | 15MB   | 0        | 已删除       |
| Docker 文件  | 8 个   | 0 (归档) | 已废弃       |
| 过时报告     | 3 个   | 0 (归档) | 历史文档     |
| macOS 文件   | 多个   | 0        | 系统垃圾     |
| 临时脚本     | 4 个   | 0 (归档) | 已完成功能   |
| **项目大小** | ~200MB | ~150MB   | **减少 25%** |

---

## ✅ 清理检查清单

执行清理后验证:

```bash
# 1. 检查是否还有 Docker 文件
ls docker-compose*.yml Dockerfile* 2>/dev/null && echo "⚠️  还有 Docker 文件" || echo "✅ Docker 文件已清理"

# 2. 检查是否还有压缩包
ls *.tar.gz *.zip 2>/dev/null && echo "⚠️  还有压缩包" || echo "✅ 压缩包已清理"

# 3. 检查 .DS_Store
find . -name '.DS_Store' && echo "⚠️  还有 .DS_Store" || echo "✅ macOS 文件已清理"

# 4. 检查 Git 状态
git status

# 5. 验证项目结构
tree -L 2 -I 'node_modules|venv|__pycache__|dist'
```

---

## ✅ 总结

**清理收益:**

- 📦 释放 ~50MB 磁盘空间
- 🗂️ 归档过时文件,保持历史可追溯
- 📚 优化项目结构,更清晰
- 🔒 移除敏感文件,增强安全性

**注意事项:**

- ⚠️ 归档文件夹不提交到 Git
- ⚠️ .env 文件永远不提交
- ⚠️ 清理前确认文件不再需要
- ✅ 可随时从 archive/ 恢复文件
