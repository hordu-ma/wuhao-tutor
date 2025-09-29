# 五好伴学部署指南 (DEPLOYMENT)

Last Updated: 2025-09-29
适用版本：后端 0.1.x
部署策略：Docker Compose（当前）→ Kubernetes（规划）

---

## 1. 部署概览

| 环境 | 策略 | 技术栈 | 状态 |
|------|------|--------|------|
| 开发 (development) | 本地 Docker Compose | SQLite/PostgreSQL + Redis + Nginx | ✅ |
| 测试 (testing) | 隔离容器 | 内存数据库 + 模拟依赖 | ✅ |
| 预生产 (staging) | Docker Compose | PostgreSQL + Redis + 完整监控 | 规划 |
| 生产 (production) | Docker Compose / K8s | PostgreSQL + Redis + TLS + 备份 | ✅ 基础版 |

部署目标：
- **快速启动**：5 分钟内从零到运行
- **配置隔离**：环境变量模板化管理
- **回滚友好**：容器标签 + 数据库备份策略
- **监控集成**：健康检查 + 指标导出就绪
- **安全基线**：TLS + 安全头 + 密钥管理

---

## 2. 系统要求

| 组件 | 最低要求 | 推荐配置 | 备注 |
|------|----------|----------|------|
| 操作系统 | Linux / macOS | Ubuntu 20.04+ / macOS 12+ | Windows 需 WSL2 |
| Docker | 20.10+ | 24.0+ | 支持 BuildKit |
| Docker Compose | 2.0+ | 2.20+ | v2 语法 |
| CPU | 2 核 | 4 核 | AI 调用密集时需更多 |
| 内存 | 4GB | 8GB | PostgreSQL + Redis + 应用 |
| 磁盘 | 20GB | 50GB | 日志 + 数据库 + 备份 |
| 网络 | - | 固定 IP（生产） | 域名解析 + TLS 证书 |

---

## 3. Docker 配置详解

### 3.1 主应用 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（OCR 相关）
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖管理器
RUN pip install --no-cache-dir uv

# 复制依赖文件并安装
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 多环境 Docker Compose 配置

#### 开发环境 (docker-compose.dev.yml)

```yaml
version: "3.8"

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD:-devpass}@postgres:5432/wuhao_tutor_dev
      - REDIS_URL=redis://redis:6379/0
      - BAILIAN_APPLICATION_ID=${BAILIAN_APPLICATION_ID}
      - BAILIAN_API_KEY=${BAILIAN_API_KEY}
    volumes:
      - ./src:/app/src  # 开发热重载
      - ./uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: wuhao_tutor_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devpass}
    ports:
      - "5432:5432"  # 开发环境暴露端口
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"  # 开发环境暴露端口
    volumes:
      - redis_dev_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_dev_data:
  redis_dev_data:
```

#### 生产环境 (docker-compose.yml)

```yaml
version: "3.8"

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./uploads:/var/www/uploads:ro
    depends_on:
      - web
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/wuhao_tutor
      - REDIS_URL=redis://redis:6379/0
      - BAILIAN_APPLICATION_ID=${BAILIAN_APPLICATION_ID}
      - BAILIAN_API_KEY=${BAILIAN_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost}
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: wuhao_tutor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # 备份服务（可选）
  backup:
    image: postgres:15
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: wuhao_tutor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./backups:/backups
      - ./scripts:/scripts:ro
    command: /bin/bash -c "while true; do /scripts/db_backup.sh; sleep 86400; done"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    driver: bridge
```

---

## 4. 环境配置管理

### 4.1 环境变量模板

**开发环境 (.env.dev.example)**：
```bash
# === 基础配置 ===
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1

# === 数据库配置 ===
POSTGRES_PASSWORD=devpass
SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://postgres:devpass@localhost:5432/wuhao_tutor_dev

# === Redis 配置 ===
REDIS_URL=redis://localhost:6379/0

# === AI 服务配置 ===
BAILIAN_APPLICATION_ID=your_app_id_here
BAILIAN_API_KEY=your_api_key_here
BAILIAN_TIMEOUT=30
BAILIAN_MAX_RETRIES=3

# === 文件上传配置 ===
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_PATH=./uploads
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf,txt,md

# === 日志配置 ===
LOG_LEVEL=DEBUG
LOG_FILE=./logs/app.log
```

**生产环境 (.env.prod.example)**：
```bash
# === 基础配置 ===
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your_generated_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# === 数据库配置 ===
POSTGRES_PASSWORD=your_strong_postgres_password
SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://postgres:your_strong_postgres_password@postgres:5432/wuhao_tutor

# === Redis 配置 ===
REDIS_URL=redis://redis:6379/0

# === AI 服务配置 ===
BAILIAN_APPLICATION_ID=your_production_app_id
BAILIAN_API_KEY=your_production_api_key
BAILIAN_TIMEOUT=25
BAILIAN_MAX_RETRIES=2

# === 安全配置 ===
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_SECRET_KEY=your_csrf_secret_key

# === TLS 配置 ===
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# === 监控配置 ===
ENABLE_METRICS=true
METRICS_PATH=/metrics

# === 备份配置 ===
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=your-backup-bucket  # 可选
```

### 4.2 密钥生成与管理

使用项目提供的密钥管理脚本：

```bash
# 生成生产环境密钥
python scripts/secrets_manager.py generate-all --env production

# 验证密钥强度
python scripts/secrets_manager.py validate

# 轮换密钥（规划中）
python scripts/secrets_manager.py rotate --key SECRET_KEY
```

---

## 5. 部署流程

### 5.1 首次部署（开发环境）

```bash
# 1. 克隆项目
git clone <repository-url>
cd wuhao-tutor

# 2. 准备环境变量
cp .env.dev.example .env
# 编辑 .env 填入必要的配置

# 3. 构建并启动服务
docker-compose -f docker-compose.dev.yml up --build -d

# 4. 初始化数据库
docker-compose -f docker-compose.dev.yml exec web uv run python scripts/init_database.py

# 5. 运行数据库迁移
docker-compose -f docker-compose.dev.yml exec web alembic upgrade head

# 6. 验证部署
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI
```

### 5.2 生产环境部署

```bash
# 1. 准备服务器环境
sudo apt update && sudo apt install -y docker.io docker-compose-plugin

# 2. 克隆项目到生产服务器
git clone <repository-url> /opt/wuhao-tutor
cd /opt/wuhao-tutor

# 3. 准备生产环境配置
cp .env.prod.example .env
# 仔细编辑 .env，设置强密码和正确域名

# 4. 生成密钥和证书
python scripts/secrets_manager.py generate-all --env production
# 配置 SSL 证书到 nginx/ssl/ 目录

# 5. 构建并启动生产服务
docker-compose up --build -d

# 6. 初始化生产数据库
docker-compose exec web uv run python scripts/init_database.py
docker-compose exec web alembic upgrade head

# 7. 设置备份定时任务（可选）
# 参见下文备份策略

# 8. 验证生产部署
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/health/performance
```

### 5.3 更新部署

```bash
# 1. 备份当前数据
python scripts/db_backup.py create --description "pre-update-backup"

# 2. 拉取最新代码
git pull origin main

# 3. 重建镜像并更新服务
docker-compose build --no-cache
docker-compose up -d

# 4. 运行数据库迁移（如有）
docker-compose exec web alembic upgrade head

# 5. 验证更新
docker-compose exec web uv run python scripts/diagnose.py
curl http://localhost:8000/health
```

---

## 6. Nginx 反向代理配置

### 6.1 Nginx 主配置 (nginx/nginx.conf)

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'rt=$request_time ut=$upstream_response_time';

    access_log /var/log/nginx/access.log main;

    # 基础配置
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    client_max_body_size 10M;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # 上游服务器
    upstream app_backend {
        server web:8000;
        keepalive 32;
    }

    # HTTP 服务器（重定向到 HTTPS）
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS 服务器
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL 配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # 安全头
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; font-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none';" always;
        add_header Permissions-Policy "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()";

        # API 代理
        location /api/ {
            proxy_pass http://app_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;

            # 超时配置
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 健康检查
        location /health {
            proxy_pass http://app_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 文档页面
        location /docs {
            proxy_pass http://app_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 静态文件服务
        location /uploads/ {
            alias /var/www/uploads/;
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options "nosniff";
        }

        # 根路径
        location / {
            return 404;
        }
    }
}
```

---

## 7. 备份与恢复策略

### 7.1 自动备份配置

**备份脚本增强版 (scripts/db_backup.py)**：

```bash
# 每日备份（添加到 crontab）
0 2 * * * cd /opt/wuhao-tutor && python scripts/db_backup.py create --auto

# 每周全量备份
0 1 * * 0 cd /opt/wuhao-tutor && python scripts/db_backup.py create --full --compress

# 清理老备份
0 3 * * * cd /opt/wuhao-tutor && python scripts/db_backup.py cleanup --days 30
```

### 7.2 容灾恢复流程

```bash
# 1. 停止服务
docker-compose down

# 2. 恢复数据库
python scripts/db_backup.py restore --file backups/backup_2025-09-29_02-00-00.sql

# 3. 验证数据完整性
docker-compose up -d postgres redis
docker-compose exec postgres psql -U postgres -d wuhao_tutor -c "SELECT count(*) FROM users;"

# 4. 重启所有服务
docker-compose up -d

# 5. 验证应用功能
curl https://yourdomain.com/health
```

---

## 8. 监控与健康检查

### 8.1 健康检查端点

| 端点 | 用途 | 响应时间要求 |
|------|------|-------------|
| `/health` | 基础存活检查 | < 100ms |
| `/health/live` | Kubernetes liveness | < 200ms |
| `/health/ready` | Kubernetes readiness | < 500ms |
| `/api/v1/health/performance` | 性能指标 | < 1s |

### 8.2 Docker 健康检查

所有服务均配置了健康检查：
- **应用容器**: HTTP 检查 `/health`
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Nginx**: HTTP 检查代理后端

### 8.3 监控集成（规划）

```yaml
# 添加到 docker-compose.yml（可选）
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
```

---

## 9. 性能调优

### 9.1 容器资源限制

```yaml
# 生产环境资源限制示例
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    ulimits:
      nofile:
        soft: 65536
        hard: 65536

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### 9.2 数据库调优

**PostgreSQL 配置优化 (postgresql.conf)**：
```ini
# 内存配置
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 256MB

# 连接配置
max_connections = 200
max_prepared_transactions = 100

# 日志配置
log_min_duration_statement = 1000  # 记录慢查询
log_checkpoints = on
log_connections = on
log_disconnections = on
```

---

## 10. 安全配置

### 10.1 防火墙设置

```bash
# Ubuntu 防火墙配置
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5432/tcp   # PostgreSQL（仅容器内访问）
sudo ufw deny 6379/tcp   # Redis（仅容器内访问）
sudo ufw enable
```

### 10.2 Docker 安全

```bash
# 运行 Docker 安全检查
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image wuhao-tutor:latest

# 定期更新基础镜像
docker-compose build --no-cache --pull
```

---

## 11. 故障排查

### 11.1 常见问题

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| 容器启动失败 | `docker-compose up` 报错 | 检查环境变量和端口占用 |
| 数据库连接失败 | 500 错误 | 检查 PostgreSQL 健康状态和连接字符串 |
| AI 服务超时 | 批改功能失效 | 检查 BAILIAN_API_KEY 和网络连接 |
| 文件上传失败 | 413 错误 | 调整 Nginx client_max_body_size |
| SSL 证书错误 | 浏览器警告 | 检查证书路径和有效期 |

### 11.2 日志查看

```bash
# 查看应用日志
docker-compose logs -f web

# 查看数据库日志
docker-compose logs -f postgres

# 查看 Nginx 日志
docker-compose logs -f nginx

# 查看所有服务状态
docker-compose ps
```

### 11.3 调试模式

```bash
# 开启详细日志
export LOG_LEVEL=DEBUG

# 进入容器调试
docker-compose exec web /bin/bash

# 手动运行诊断脚本
docker-compose exec web uv run python scripts/diagnose.py
```

---

## 12. 扩展与演进

### 12.1 水平扩展

```yaml
# 多实例部署
services:
  web:
    deploy:
      replicas: 3

  nginx:
    # 更新上游配置支持多实例
    volumes:
      - ./nginx/nginx-cluster.conf:/etc/nginx/nginx.conf:ro
```

### 12.2 Kubernetes 迁移准备

```bash
# 生成 K8s 配置
kompose convert -f docker-compose.yml

# 添加 ConfigMap 和 Secret
kubectl create configmap wuhao-config --from-env-file=.env
kubectl create secret generic wuhao-secrets --from-env-file=.env.secrets
```

---

## 13. 维护检查清单

### 13.1 日常维护

- [ ] 检查磁盘空间使用（< 80%）
- [ ] 查看应用错误日志
- [ ] 验证备份完整性
- [ ] 检查 SSL 证书过期时间
- [ ] 监控数据库性能指标

### 13.2 周期维护

**每周**：
- [ ] 更新系统安全补丁
- [ ] 清理旧日志文件
- [ ] 验证恢复流程

**每月**：
- [ ] 更新 Docker 镜像
- [ ] 性能基线测试
- [ ] 安全扫描

---

## 14. 联系与支持

| 类型 | 联系方式 |
|------|----------|
| 技术问题 | 项目 Issues |
| 紧急故障 | 运维负责人 |
| 部署支持 | 开发团队 |

---

## 15. 附录：快速命令参考

```bash
# === 开发环境 ===
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 重启应用（保留数据）
docker-compose -f docker-compose.dev.yml restart web

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f web

# === 生产环境 ===
# 部署/更新生产环境
docker-compose up -d --build

# 备份数据库
python scripts/db_backup.py create --description "manual-backup"

# 恢复数据库
python scripts/db_backup.py restore --file backups/backup_xxx.sql

# 健康检查
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/health/performance

# === 维护 ===
# 清理未使用的 Docker 资源
docker system prune -af

# 查看容器资源使用
docker stats

# 进入容器 shell
docker-compose exec web /bin/bash
```

---

（END）
