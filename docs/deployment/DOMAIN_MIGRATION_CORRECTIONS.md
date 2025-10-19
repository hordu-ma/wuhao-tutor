# 域名迁移文档修正总结

> **修正日期**: 2025-10-19  
> **修正依据**: SSH 远程登录新服务器实际检查  
> **服务器 IP**: 121.199.173.244

---

## 📝 修正内容概览

基于实际 SSH 登录阿里云生产环境检查，对以下 4 个域名迁移文档进行了修正：

1. ✅ `domain-migration-guide.md` - 完整操作指南
2. ✅ `QUICK-START-DOMAIN-MIGRATION.md` - 快速开始指南
3. ✅ `DOMAIN_MIGRATION_CHECKLIST.md` - 执行检查清单
4. ✅ `DOMAIN_MIGRATION_INDEX.md` - 文档索引
5. ✅ `CURRENT_SERVER_STATUS.md` - **新增**服务器现状说明

---

## 🔧 主要修正项

### 1. Nginx 配置文件路径

**错误路径**（文档原有）：

```bash
/etc/nginx/sites-available/wuhao-tutor.conf
/etc/nginx/sites-enabled/wuhao-tutor.conf
```

**正确路径**（实际检查）：

```bash
/etc/nginx/conf.d/wuhao-tutor.conf
```

**说明**：Ubuntu Nginx 可以使用 `sites-available/enabled` 或 `conf.d/`，本项目实际使用的是 `conf.d/` 方式。

---

### 2. 前端部署目录

**错误路径**（文档原有）：

```bash
/var/www/wuhao-tutor/frontend/
```

**正确路径**（实际检查）：

```bash
/var/www/html/
```

**Nginx 配置验证**：

```nginx
server {
    root /var/www/html;  # 实际配置的前端根目录
    index index.html index.htm;
}
```

---

### 3. 文件上传目录

**错误路径**（文档原有）：

```bash
/var/www/wuhao-tutor/uploads/
/var/www/uploads/
```

**正确路径**（实际检查）：

```bash
/opt/wuhao-tutor/uploads/
```

**Nginx 配置验证**：

```nginx
location /uploads/ {
    alias /opt/wuhao-tutor/uploads/;
    expires 7d;
}
```

**目录实际存在验证**：

```bash
$ ls -la /opt/wuhao-tutor/uploads/
drwxr-xr-x  3 root root     4096 Oct 12 16:26 .
drwxr-xr-x 14  501 staff    4096 Oct 19 13:38 ..
drwxr-xr-x  2 root root     4096 Oct 14 19:03 avatars
-rw-r--r--  1 root root  3242637 Oct 12 10:00 learning_*.jpeg
...
```

---

### 4. 后端环境变量文件路径

**模糊路径**（文档原有）：

```bash
vim /path/to/wuhao-tutor/.env.production
```

**明确路径**（实际检查）：

```bash
vim /opt/wuhao-tutor/.env.production
```

---

### 5. 前端配置更新策略

**文档原有建议**：

```bash
# 修改前端配置
vim frontend/.env.production
VITE_API_BASE_URL=https://www.horsduroot.com

# 重新构建和部署
npm run build
scp -r dist/* root@121.199.173.244:/var/www/wuhao-tutor/frontend/
```

**修正后建议**：

```bash
# 前端无需修改，已使用相对路径
cat /opt/wuhao-tutor/frontend/.env.production
# VITE_API_BASE_URL=/api/v1  ← 自动适配域名和 IP

# 如需重新部署（可选）
npm run build
scp -r dist/* root@121.199.173.244:/var/www/html/  # 正确路径
```

**优势**：

- ✅ 使用相对路径，无需为域名切换修改前端配置
- ✅ 同时支持 IP 访问和域名访问
- ✅ 减少配置维护工作量

---

### 6. 新服务器域名配置现状

**重要发现**：

❌ **新服务器当前未配置域名**

当前 Nginx 配置：

```nginx
server {
    listen 80;
    server_name 121.199.173.244 localhost;  # ⚠️ 缺少域名
}

server {
    listen 443 ssl http2;
    server_name 121.199.173.244 localhost;  # ⚠️ 缺少域名
}
```

需要修改为：

```nginx
server_name www.horsduroot.com horsduroot.com 121.199.173.244 localhost;
```

---

### 7. SSL 证书状态

**当前证书**（实际检查）：

```nginx
ssl_certificate /etc/nginx/ssl/wuhao-tutor.crt;         # ⚠️ 自签名证书
ssl_certificate_key /etc/nginx/ssl/wuhao-tutor.key;
```

**需要替换为**：

```nginx
ssl_certificate /etc/letsencrypt/live/www.horsduroot.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/www.horsduroot.com/privkey.pem;
```

**说明**：需要使用 Certbot 申请 Let's Encrypt 免费证书。

---

### 8. DNS 当前状态

**实际检查**（2025-10-19）：

```bash
$ nslookup www.horsduroot.com
Name:   www.horsduroot.com
Address: 60.205.124.67  # ⚠️ 仍然指向旧服务器
```

**HTTPS 访问验证**：

```bash
$ ssh root@121.199.173.244 "curl -I https://www.horsduroot.com 2>&1 | head -5"
HTTP/2 200
server: nginx/1.18.0 (Ubuntu)
```

**说明**：域名当前解析到旧服务器 (60.205.124.67)，但通过该域名访问是正常的，说明旧服务器配置正确。

---

## 📋 文档修正详情

### domain-migration-guide.md

**修正项**：

1. ✅ Nginx 配置路径：`sites-available` → `conf.d`
2. ✅ 上传目录路径：`/var/www/wuhao-tutor/uploads/` → `/opt/wuhao-tutor/uploads/`
3. ✅ 前端部署路径：`/var/www/wuhao-tutor/frontend/` → `/var/www/html/`
4. ✅ 后端配置路径：`/path/to/wuhao-tutor/` → `/opt/wuhao-tutor/`
5. ✅ 增加 Nginx 配置修改说明（添加域名到现有配置）
6. ✅ 前端配置策略：改为"无需修改"（已使用相对路径）
7. ✅ SSL 证书配置说明更新

### QUICK-START-DOMAIN-MIGRATION.md

**修正项**：

1. ✅ Step 5 前端配置：改为"无需修改"
2. ✅ 增加后端配置步骤（BASE_URL 和 CORS）
3. ✅ 添加完成检查清单
4. ✅ 添加问题排查引用链接

### DOMAIN_MIGRATION_CHECKLIST.md

**修正项**：

1. ✅ Nginx 配置路径修正
2. ✅ Step 9 重命名为"后端和前端配置更新"
3. ✅ 增加后端配置更新步骤
4. ✅ 前端配置改为"无需修改"说明
5. ✅ 前端部署路径修正（可选步骤）
6. ✅ Step 编号调整（原 Step 10/11 → Step 11/12）

### DOMAIN_MIGRATION_INDEX.md

**修正项**：

1. ✅ 文档清单增加 `CURRENT_SERVER_STATUS.md`
2. ✅ 增加"关键路径说明"表格
3. ✅ 增加"当前服务器状态"警告说明
4. ✅ 步骤 4 更新为"后端和小程序配置"
5. ✅ 删除步骤 5 前端配置（无需修改）

### CURRENT_SERVER_STATUS.md（新增）

**内容**：

1. ✅ 服务状态检查结果
2. ✅ 域名配置现状说明
3. ✅ 实际文件路径对照表
4. ✅ Nginx 配置关键点分析
5. ✅ 环境变量配置现状
6. ✅ 域名切换需要的具体修改
7. ✅ 验证检查点清单

---

## 🎯 关键修正对照表

| 配置项         | 文档原有路径/配置                | ✅ 实际正确路径/配置           | 影响文档数量 |
| -------------- | -------------------------------- | ------------------------------ | ------------ |
| Nginx 配置文件 | `/etc/nginx/sites-available/`    | `/etc/nginx/conf.d/`           | 3 个         |
| 前端部署目录   | `/var/www/wuhao-tutor/frontend/` | `/var/www/html/`               | 3 个         |
| 上传目录       | `/var/www/uploads/` 等           | `/opt/wuhao-tutor/uploads/`    | 2 个         |
| 后端 .env      | `/path/to/wuhao-tutor/`          | `/opt/wuhao-tutor/`            | 3 个         |
| 前端 BASE_URL  | 需修改为域名                     | 无需修改（已使用相对路径）     | 3 个         |
| Server Name    | 文档未提示当前配置缺少域名       | 明确说明需要添加域名           | 4 个         |
| SSL 证书       | 文档未说明当前是自签名           | 明确说明需要申请 Let's Encrypt | 2 个         |

---

## ✅ 修正验证

### SSH 实际检查命令

```bash
# Nginx 配置
ssh root@121.199.173.244 "cat /etc/nginx/conf.d/wuhao-tutor.conf"

# 前端部署目录
ssh root@121.199.173.244 "ls -la /var/www/html/"

# 上传目录
ssh root@121.199.173.244 "ls -la /opt/wuhao-tutor/uploads/"

# 后端环境变量
ssh root@121.199.173.244 "cat /opt/wuhao-tutor/.env.production"

# 前端环境变量
ssh root@121.199.173.244 "cat /opt/wuhao-tutor/frontend/.env.production"

# 服务状态
ssh root@121.199.173.244 "systemctl status wuhao-tutor.service | head -20"

# DNS 解析
nslookup www.horsduroot.com
```

### 关键发现

1. ✅ **Nginx 配置在 conf.d/**：`/etc/nginx/conf.d/wuhao-tutor.conf`
2. ✅ **前端在 /var/www/html/**：Nginx root 配置验证
3. ✅ **上传在 /opt/wuhao-tutor/uploads/**：Nginx location 和目录验证
4. ✅ **前端使用相对路径**：`VITE_API_BASE_URL=/api/v1`
5. ❌ **新服务器未配置域名**：server_name 只有 IP 和 localhost
6. ❌ **使用自签名证书**：需要替换为 Let's Encrypt
7. ❌ **DNS 仍指向旧服务器**：需要在阿里云控制台修改

---

## 📌 后续行动建议

### 执行域名迁移前

1. **阅读新文档** `CURRENT_SERVER_STATUS.md`，了解当前配置
2. **备份配置文件**：
   ```bash
   ssh root@121.199.173.244
   cp /etc/nginx/conf.d/wuhao-tutor.conf \
      /etc/nginx/conf.d/wuhao-tutor.conf.backup.$(date +%Y%m%d_%H%M%S)
   ```

### 执行域名迁移时

1. **严格按照修正后的路径执行**
2. **使用 QUICK-START 快速指南**（已修正）
3. **使用 CHECKLIST 逐项检查**（已修正）

### 执行域名迁移后

1. **验证所有路径正确**
2. **检查 SSL 证书有效**
3. **确认前后端都能访问**

---

## 🔗 相关文档

- [服务器当前状态](./CURRENT_SERVER_STATUS.md) - **新增**，必读
- [快速开始指南](./QUICK-START-DOMAIN-MIGRATION.md) - 已修正
- [完整操作指南](./domain-migration-guide.md) - 已修正
- [执行检查清单](./DOMAIN_MIGRATION_CHECKLIST.md) - 已修正
- [文档索引](./DOMAIN_MIGRATION_INDEX.md) - 已修正

---

**修正完成时间**: 2025-10-19 19:00  
**修正方式**: SSH 远程实际检查 + 文档逐项对照修正  
**修正人**: GitHub Copilot + 用户确认
