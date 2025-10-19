# 新服务器当前状态说明

> **服务器 IP**: 121.199.173.244 (i-bp17y72dzkqcsby31sy3)  
> **检查日期**: 2025-10-19  
> **状态**: ✅ 运行正常，但尚未配置域名

---

## 📊 当前配置概览

### 服务状态

| 服务             | 状态      | 说明                        |
| ---------------- | --------- | --------------------------- |
| wuhao-tutor      | ✅ 运行中 | 4 个 worker 进程，端口 8000 |
| Nginx            | ✅ 运行中 | 配置完整，支持 HTTPS        |
| PostgreSQL (RDS) | ✅ 已连接 | 阿里云 RDS                  |
| Redis (云)       | ✅ 已连接 | 阿里云 Redis                |

### 域名配置情况

**当前状态**：

- ❌ Nginx **未配置** `www.horsduroot.com` 域名
- ✅ 仅配置了 `121.199.173.244` 和 `localhost`
- ❌ SSL 证书为**自签名证书**，非 Let's Encrypt

**DNS 现状**：

- `www.horsduroot.com` 当前解析到 **60.205.124.67** (旧服务器)
- 新服务器 (121.199.173.244) 尚未配置域名访问

---

## 📁 实际文件路径

### Nginx 配置

```bash
配置文件: /etc/nginx/conf.d/wuhao-tutor.conf
备份文件: /etc/nginx/conf.d/wuhao-tutor.conf.backup.20251013_083132
主配置: /etc/nginx/nginx.conf
```

**重要**: 文档中提到的 `/etc/nginx/sites-available/` 路径**不存在**，实际配置在 `conf.d/` 目录。

### 应用部署路径

```bash
后端代码: /opt/wuhao-tutor/
前端静态文件: /var/www/html/
文件上传目录: /opt/wuhao-tutor/uploads/
```

### 配置文件

```bash
后端环境变量: /opt/wuhao-tutor/.env.production
前端环境变量: /opt/wuhao-tutor/frontend/.env.production
服务配置: /etc/systemd/system/wuhao-tutor.service
```

---

## 🔧 当前 Nginx 配置关键点

### Server Name

```nginx
# HTTP 配置
server {
    listen 80;
    server_name 121.199.173.244 localhost;  # ⚠️ 缺少域名
    # ...
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name 121.199.173.244 localhost;  # ⚠️ 缺少域名
    # ...
}
```

**需要添加**: `www.horsduroot.com horsduroot.com`

### SSL 证书

```nginx
ssl_certificate /etc/nginx/ssl/wuhao-tutor.crt;         # ⚠️ 自签名证书
ssl_certificate_key /etc/nginx/ssl/wuhao-tutor.key;
```

**需要替换为**: Let's Encrypt 证书

### 上传文件路径

```nginx
location /uploads/ {
    alias /opt/wuhao-tutor/uploads/;  # ✅ 实际路径正确
    # ...
}
```

### 前端根目录

```nginx
root /var/www/html;  # ✅ 实际路径正确
```

---

## 🌐 环境变量配置

### 后端 .env.production

**当前配置**：

```bash
# CORS - 仅包含 IP 地址
BACKEND_CORS_ORIGINS='["https://121.199.173.244","http://121.199.173.244","https://wuhao-tutor.com","https://admin.wuhao-tutor.com"]'

# 基础 URL - 使用 IP
BASE_URL=https://121.199.173.244
```

**需要更新**：

- 添加 `www.horsduroot.com` 到 CORS
- 更新 BASE_URL 为域名

### 前端 .env.production

**当前配置**（✅ 无需修改）：

```bash
# 使用相对路径，自动适配域名和 IP
VITE_API_BASE_URL=/api/v1
```

---

## 📋 域名切换需要做的修改

### 1. Nginx 配置修改

在 `/etc/nginx/conf.d/wuhao-tutor.conf` 中：

```bash
# 修改 HTTP server 块
server_name www.horsduroot.com horsduroot.com 121.199.173.244 localhost;

# 修改 HTTPS server 块
server_name www.horsduroot.com horsduroot.com 121.199.173.244 localhost;
```

### 2. 后端环境变量修改

在 `/opt/wuhao-tutor/.env.production` 中：

```bash
# 更新 BASE_URL
BASE_URL=https://www.horsduroot.com

# 更新 CORS（添加域名）
BACKEND_CORS_ORIGINS='["https://www.horsduroot.com","http://www.horsduroot.com","https://horsduroot.com","http://horsduroot.com","https://121.199.173.244","http://121.199.173.244"]'
```

### 3. SSL 证书申请

使用 Certbot 申请 Let's Encrypt 证书：

```bash
certbot --nginx -d www.horsduroot.com -d horsduroot.com
```

### 4. 前端配置

**无需修改**，当前已使用相对路径。

---

## 🔍 验证检查点

域名切换完成后，需要验证：

- [ ] DNS 解析正确（`nslookup www.horsduroot.com` 返回 121.199.173.244）
- [ ] HTTP 自动跳转 HTTPS
- [ ] HTTPS 访问正常（Let's Encrypt 证书，绿锁）
- [ ] API 接口正常（`/api/v1/health` 返回 200）
- [ ] 静态资源加载正常（前端页面）
- [ ] 文件上传下载正常（`/uploads/` 路径）
- [ ] 后端服务健康（`systemctl status wuhao-tutor.service`）

---

## 📌 重要提醒

1. **DNS 生效时间**：修改 DNS 后需要等待 10-30 分钟生效
2. **证书申请时机**：必须在 DNS 生效后才能申请 Let's Encrypt 证书
3. **配置备份**：修改前务必备份配置文件
4. **服务重启**：修改环境变量后需要重启服务
5. **Nginx 重载**：修改 Nginx 配置后需要测试并重载

---

## 🔗 相关文档

- [域名切换快速指南](./QUICK-START-DOMAIN-MIGRATION.md) - 5 步完成切换
- [域名迁移完整指南](./domain-migration-guide.md) - 详细操作步骤
- [域名迁移检查清单](./DOMAIN_MIGRATION_CHECKLIST.md) - 执行检查清单
- [域名迁移文档索引](./DOMAIN_MIGRATION_INDEX.md) - 文档导航

---

**最后更新**: 2025-10-19  
**检查方式**: SSH 远程登录实际查看配置文件
