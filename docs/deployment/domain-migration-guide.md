# 域名迁移指南 - www.horsduroot.com 切换到新服务器

> **操作日期**: 2025-10-19  
> **目标域名**: www.horsduroot.com  
> **旧服务器**: 60.205.124.67 (i-2ze7ncpvr0pvja23beht)  
> **新服务器**: 121.199.173.244 (i-bp17y72dzkqcsby31sy3)  
> **项目**: 五好伴学 (Wuhao Tutor)

---

## 📋 切换前检查清单

- [ ] 新服务器后端服务运行正常
- [ ] 新服务器 Nginx 运行正常
- [ ] 新服务器防火墙已开放 80/443 端口
- [ ] 已备份旧服务器配置文件
- [ ] DNS 管理权限已确认
- [ ] SSL 证书准备就绪

---

## 🔄 详细操作步骤

### Step 1: 验证新服务器服务状态

**执行位置**: 新服务器 (121.199.173.244)

```bash
# SSH 登录新服务器
ssh root@121.199.173.244

# 检查后端服务
systemctl status wuhao-tutor.service

# 检查 Nginx
systemctl status nginx

# 测试健康检查接口
curl http://127.0.0.1:8000/health
```

**预期结果**:

```json
{
  "status": "healthy",
  "version": "0.2.1"
}
```

**如果服务未运行**:

```bash
systemctl start wuhao-tutor.service
systemctl start nginx
```

---

### Step 2: 修改 Nginx 配置支持域名

**配置文件位置**: `/etc/nginx/sites-available/wuhao-tutor.conf`

#### 2.1 备份当前配置

```bash
cp /etc/nginx/sites-available/wuhao-tutor.conf /etc/nginx/sites-available/wuhao-tutor.conf.backup.$(date +%Y%m%d)
```

#### 2.2 编辑配置文件

```bash
vim /etc/nginx/sites-available/wuhao-tutor.conf
```

**修改内容**:

```nginx
# HTTP 配置 (临时支持 HTTP，用于 SSL 证书申请)
server {
    listen 80;
    server_name www.horsduroot.com horsduroot.com 121.199.173.244;

    # Let's Encrypt 证书验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # 其他请求暂时允许 HTTP (SSL 配置完成后会改为强制跳转 HTTPS)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件
    location /static/ {
        alias /var/www/wuhao-tutor/static/;
        expires 30d;
    }

    location /uploads/ {
        alias /var/www/wuhao-tutor/uploads/;
        expires 7d;
    }
}
```

#### 2.3 测试配置并重载

```bash
# 测试配置语法
nginx -t

# 预期输出
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# 重载 Nginx
systemctl reload nginx
```

---

### Step 3: 修改 DNS 解析

**操作位置**: 阿里云控制台 → 域名管理 → DNS 解析

#### 3.1 登录阿里云控制台

访问: https://dns.console.aliyun.com/

#### 3.2 找到域名 horsduroot.com

在域名列表中点击 **解析设置**

#### 3.3 修改 A 记录

| 操作     | 记录类型 | 主机记录 | 解析线路 | 记录值          | TTL |
| -------- | -------- | -------- | -------- | --------------- | --- |
| **修改** | A        | www      | 默认     | 121.199.173.244 | 600 |
| **修改** | A        | @        | 默认     | 121.199.173.244 | 600 |

**详细步骤**:

1. 找到 `www` 记录，点击 **修改**
2. 将记录值从 `60.205.124.67` 改为 `121.199.173.244`
3. TTL 设置为 **600 秒** (10 分钟)
4. 保存修改

5. 重复上述步骤修改 `@` 记录 (根域名 horsduroot.com)

#### 3.4 验证 DNS 解析生效

```bash
# 在本地 Mac 执行
nslookup www.horsduroot.com

# 预期输出（可能需要等待 10-30 分钟）
# Server:  xxx.xxx.xxx.xxx
# Address: xxx.xxx.xxx.xxx#53
#
# Non-authoritative answer:
# Name:    www.horsduroot.com
# Address: 121.199.173.244
```

**加速 DNS 刷新** (可选):

```bash
# Mac 清除 DNS 缓存
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

---

### Step 4: 配置 SSL 证书 (HTTPS)

#### 4.1 安装 Certbot (如未安装)

```bash
# 在新服务器上执行
apt update
apt install certbot python3-certbot-nginx -y
```

#### 4.2 申请 SSL 证书

```bash
# 自动申请并配置证书
certbot --nginx -d www.horsduroot.com -d horsduroot.com

# 交互式问题回答：
# 1. 输入邮箱 (用于证书到期提醒)
# 2. 同意服务条款: Y
# 3. 是否分享邮箱: N
# 4. 选择重定向选项: 2 (强制 HTTPS)
```

**手动验证模式** (如果自动模式失败):

```bash
certbot certonly --webroot -w /var/www/certbot \
  -d www.horsduroot.com -d horsduroot.com
```

#### 4.3 验证证书安装成功

```bash
# 检查证书文件
ls -la /etc/letsencrypt/live/www.horsduroot.com/

# 应该看到以下文件：
# - fullchain.pem   (完整证书链)
# - privkey.pem     (私钥)
# - cert.pem        (证书)
# - chain.pem       (证书链)
```

#### 4.4 Certbot 自动续期配置

```bash
# 测试自动续期
certbot renew --dry-run

# 查看自动续期计划任务
systemctl list-timers | grep certbot
```

#### 4.5 最终 Nginx 配置 (Certbot 自动生成)

查看 Certbot 生成的配置:

```bash
cat /etc/nginx/sites-available/wuhao-tutor.conf
```

**预期配置** (Certbot 会自动添加):

```nginx
# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name www.horsduroot.com horsduroot.com;

    ssl_certificate /etc/letsencrypt/live/www.horsduroot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.horsduroot.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 应用配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件
    location /static/ {
        alias /var/www/wuhao-tutor/static/;
        expires 30d;
    }

    location /uploads/ {
        alias /var/www/wuhao-tutor/uploads/;
        expires 7d;
    }
}

# HTTP 自动跳转 HTTPS
server {
    listen 80;
    server_name www.horsduroot.com horsduroot.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

---

### Step 5: 更新项目配置文件

#### 5.1 后端环境变量

```bash
# 在新服务器上编辑 .env.production
vim /path/to/wuhao-tutor/.env.production
```

**修改内容**:

```bash
# API 域名配置
API_BASE_URL=https://www.horsduroot.com
FRONTEND_URL=https://www.horsduroot.com

# CORS 允许的源
CORS_ORIGINS=["https://www.horsduroot.com", "https://horsduroot.com"]
```

**重启后端服务**:

```bash
systemctl restart wuhao-tutor.service
```

#### 5.2 前端配置 (本地构建)

**在本地 Mac 执行**:

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor/frontend

# 编辑生产环境配置
vim .env.production
```

**修改内容**:

```bash
VITE_API_BASE_URL=https://www.horsduroot.com
```

**重新构建前端**:

```bash
npm run build

# 部署到服务器
scp -r dist/* root@121.199.173.244:/var/www/wuhao-tutor/frontend/
```

#### 5.3 小程序配置 (本地修改)

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor/miniprogram

# 编辑配置文件
vim config/index.js
```

**修改内容**:

```javascript
const production = {
  api: {
    baseUrl: 'https://www.horsduroot.com',
  },
  appId: 'your-wechat-appid',
}
```

#### 5.4 微信小程序服务器域名配置

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入 **开发管理 → 开发设置 → 服务器域名**
3. 配置以下域名：

| 类型         | 域名                       |
| ------------ | -------------------------- |
| request 域名 | https://www.horsduroot.com |
| uploadFile   | https://www.horsduroot.com |
| downloadFile | https://www.horsduroot.com |

4. **删除旧域名** (如果配置了 IP): `https://60.205.124.67`

---

### Step 6: 验证切换成功

#### 6.1 DNS 解析验证

```bash
# 在本地 Mac 执行
nslookup www.horsduroot.com
dig www.horsduroot.com

# 预期: 返回 121.199.173.244
```

#### 6.2 HTTP/HTTPS 访问验证

```bash
# 测试 HTTP 自动跳转
curl -I http://www.horsduroot.com

# 预期: 301 Moved Permanently, Location: https://www.horsduroot.com

# 测试 HTTPS 访问
curl -I https://www.horsduroot.com

# 预期: 200 OK
```

#### 6.3 API 接口验证

```bash
# 健康检查
curl https://www.horsduroot.com/health

# 预期输出
# {"status":"healthy","version":"0.2.1"}

# API 文档访问
curl -I https://www.horsduroot.com/docs

# 预期: 200 OK
```

#### 6.4 SSL 证书验证

```bash
# 检查证书有效期
curl -vI https://www.horsduroot.com 2>&1 | grep -i "expire"

# 或使用在线工具
# https://www.ssllabs.com/ssltest/analyze.html?d=www.horsduroot.com
```

#### 6.5 浏览器完整测试

1. **前端页面**:

   - 访问 https://www.horsduroot.com
   - 检查是否正常加载
   - 检查浏览器地址栏是否显示 🔒 (安全锁)

2. **功能测试**:

   - 用户登录
   - 作业问答
   - 错题手册
   - 学习进度

3. **小程序测试**:
   - 打开微信小程序
   - 测试所有核心功能
   - 检查网络请求是否正常

---

### Step 7: 监控和观察

#### 7.1 实时日志监控

**在新服务器执行**:

```bash
# 监控 Nginx 访问日志
tail -f /var/log/nginx/access.log

# 监控 Nginx 错误日志
tail -f /var/log/nginx/error.log

# 监控应用日志
tail -f /path/to/wuhao-tutor/logs/app.log
```

#### 7.2 旧服务器访问量观察

**在旧服务器执行**:

```bash
ssh root@60.205.124.67

# 统计最近 1 小时的访问量
awk -v d1="$(date --date='-1 hour' '+%d/%b/%Y:%H:%M')" \
    '$4 > "["d1' /var/log/nginx/access.log | wc -l
```

**预期结果**: 24 小时后接近 0

---

### Step 8: 清理工作 (24-48 小时后)

#### 8.1 确认旧服务器无流量

```bash
# 在旧服务器检查最近 24 小时访问量
tail -n 10000 /var/log/nginx/access.log | grep -c "$(date +%d/%b/%Y)"
```

#### 8.2 保留旧服务器配置备份

```bash
# 在旧服务器执行
tar -czf ~/wuhao-tutor-backup-$(date +%Y%m%d).tar.gz \
  /etc/nginx/sites-available/wuhao-tutor.conf \
  /path/to/wuhao-tutor/.env.production \
  /etc/letsencrypt/live/*/
```

#### 8.3 旧服务器服务停止 (可选)

```bash
# 如果确认无流量，可停止旧服务器服务
systemctl stop nginx
systemctl stop wuhao-tutor.service
```

---

## ⚠️ 常见问题与解决方案

### 问题 1: DNS 解析长时间未生效

**症状**: 30 分钟后 `nslookup` 仍返回旧 IP

**解决方案**:

```bash
# 1. 检查 DNS 配置是否保存成功
# 登录阿里云控制台确认

# 2. 使用公共 DNS 测试
nslookup www.horsduroot.com 8.8.8.8

# 3. 清除本地 DNS 缓存
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### 问题 2: SSL 证书申请失败

**症状**: Certbot 报错 `Failed authorization procedure`

**原因**: DNS 解析未生效或 Nginx 配置错误

**解决方案**:

```bash
# 1. 确认 DNS 已解析到新服务器
nslookup www.horsduroot.com

# 2. 确认 80 端口可访问
curl -I http://www.horsduroot.com

# 3. 检查防火墙
ufw status
ufw allow 80/tcp

# 4. 使用 webroot 模式重试
mkdir -p /var/www/certbot
certbot certonly --webroot -w /var/www/certbot \
  -d www.horsduroot.com -d horsduroot.com
```

### 问题 3: 小程序提示 "不在以下 request 合法域名列表中"

**解决方案**:

1. 登录微信公众平台
2. 开发管理 → 开发设置 → 服务器域名
3. 添加 `https://www.horsduroot.com`
4. **等待 5 分钟生效**
5. 重新编译小程序

### 问题 4: CORS 错误

**症状**: 浏览器控制台报错 `Access-Control-Allow-Origin`

**解决方案**:

```bash
# 编辑后端配置
vim /path/to/wuhao-tutor/.env.production

# 添加域名到 CORS_ORIGINS
CORS_ORIGINS=["https://www.horsduroot.com", "https://horsduroot.com"]

# 重启服务
systemctl restart wuhao-tutor.service
```

---

## 🚨 紧急回滚方案

如果切换后出现严重问题，立即执行以下步骤：

### 回滚步骤

1. **回滚 DNS 解析** (最快 5 分钟生效):

   ```
   阿里云控制台 → DNS 解析
   www.horsduroot.com  →  60.205.124.67
   horsduroot.com      →  60.205.124.67
   TTL 改为 60 秒
   ```

2. **通知用户** (如有):

   ```
   "服务临时维护中，请稍后重试"
   ```

3. **分析问题**:

   - 查看新服务器错误日志
   - 对比配置差异
   - 找到根本原因

4. **修复后重新切换**

---

## 📊 验收清单

切换完成后，逐项确认：

| 验收项              | 验证方法                                 | 状态 |
| ------------------- | ---------------------------------------- | ---- |
| DNS 解析正确        | `nslookup www.horsduroot.com`            | [ ]  |
| HTTP 自动跳转 HTTPS | `curl -I http://www.horsduroot.com`      | [ ]  |
| HTTPS 访问正常      | 浏览器访问，无证书警告                   | [ ]  |
| API 健康检查        | `curl https://www.horsduroot.com/health` | [ ]  |
| 前端页面正常加载    | 浏览器访问首页                           | [ ]  |
| 用户登录功能        | 测试登录流程                             | [ ]  |
| 作业问答功能        | 测试 AI 对话                             | [ ]  |
| 图片上传功能        | 测试上传图片                             | [ ]  |
| 小程序访问正常      | 打开小程序测试                           | [ ]  |
| SSL 证书有效        | 证书有效期 >30 天                        | [ ]  |
| 错误日志无异常      | 检查最近 1 小时日志                      | [ ]  |
| 旧服务器流量接近 0  | 24 小时后检查旧服务器访问日志            | [ ]  |

---

## 📞 技术支持

如遇到问题，按以下顺序排查：

1. **检查文档**: 查看本文档的常见问题部分
2. **查看日志**: 新旧服务器的 Nginx 和应用日志
3. **验证配置**: 对比配置文件是否正确
4. **网络测试**: 使用 `curl`、`nslookup` 等工具诊断

---

**文档生成时间**: 2025-10-19  
**文档版本**: v1.0  
**操作者**: liguoma  
**预计操作时长**: 1-2 小时 (不含 DNS 生效等待时间)
