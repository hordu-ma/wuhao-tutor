# Nginx 配置文件说明

## 📂 文件清单

| 文件                              | 说明                           | 行数   |
| --------------------------------- | ------------------------------ | ------ |
| `wuhao-tutor.conf`                | **当前生产环境配置**（已清理） | 219 行 |
| `wuhao-tutor.conf.before-cleanup` | 清理前的备份（2025-11-01）     | 314 行 |
| `wuhao-tutor-clean.conf`          | 清理版本模板                   | 219 行 |

## ✅ 清理内容（2025-11-01）

### 移除的 Server 块

1. **`admin.wuhao-tutor.com`** - 管理后台（未使用）

   - 证书不匹配（只有 `horsduroot.com` 和 `www.horsduroot.com`）
   - 无实际内容

2. **`docs.wuhao-tutor.com`** - API 文档（未使用）
   - 证书不匹配
   - 无实际内容

### 保留的 Server 块

1. **HTTP → HTTPS 重定向** (Port 80)

   - `horsduroot.com`
   - `www.horsduroot.com`

2. **HTTPS 主站** (Port 443)
   - Vue3 前端：`/var/www/html`
   - FastAPI 后端：`/api/*` → `http://wuhao_backend:8000`
   - WebSocket 流式问答：`/api/v1/learning/ws/`

## 🔒 SSL 证书信息

```bash
证书路径: /etc/letsencrypt/live/www.horsduroot.com/fullchain.pem
私钥路径: /etc/letsencrypt/live/www.horsduroot.com/privkey.pem
覆盖域名:
  - horsduroot.com
  - www.horsduroot.com
颁发机构: Let's Encrypt
```

## 🚀 重要优化（2025-11-01）

### Android WebSocket 兼容性

```nginx
# WebSocket 连接超时增加以适应 Android 平台
location /api/v1/learning/ws/ {
    proxy_connect_timeout 120s;  # 从 75s 增加到 120s
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
```

### SSL 协议优化

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;

# OCSP Stapling (Let's Encrypt 不支持，会有警告但不影响)
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
```

## 📋 生产环境备份位置

服务器备份文件：

```bash
/etc/nginx/conf.d/wuhao-tutor.conf.backup-20251031-174759
/etc/nginx/conf.d/wuhao-tutor.conf.backup-before-cleanup-20251101-003043
/etc/nginx/conf.d/wuhao-tutor.conf.backup-before-real-cleanup-20251101-003323
```

## 🔄 部署流程

### 更新配置到生产环境

```bash
# 1. 上传配置到服务器
scp nginx/wuhao-tutor.conf root@121.199.173.244:/tmp/

# 2. SSH 登录服务器
ssh root@121.199.173.244

# 3. 备份当前配置
cp /etc/nginx/conf.d/wuhao-tutor.conf \
   /etc/nginx/conf.d/wuhao-tutor.conf.backup-$(date +%Y%m%d-%H%M%S)

# 4. 替换配置
cp /tmp/wuhao-tutor.conf /etc/nginx/conf.d/wuhao-tutor.conf

# 5. 测试配置
nginx -t

# 6. 重载 Nginx
nginx -s reload
```

### 回滚配置

```bash
# 恢复到最近的备份
ssh root@121.199.173.244 'cp /etc/nginx/conf.d/wuhao-tutor.conf.backup-YYYYMMDD-HHMMSS /etc/nginx/conf.d/wuhao-tutor.conf && nginx -t && nginx -s reload'
```

## 📊 配置统计

- **Server 块数量**: 2 个（HTTP 重定向 + HTTPS 主站）
- **Location 块数量**: 15 个
- **SSL 证书数量**: 1 个（覆盖 2 个域名）
- **配置文件大小**: 6.2 KB
- **清理减少**: 95 行（30% 精简）

## 🛡️ 安全特性

- ✅ HSTS 启用（1 年有效期）
- ✅ X-Frame-Options: DENY
- ✅ X-Content-Type-Options: nosniff
- ✅ X-XSS-Protection 启用
- ✅ 强制 HTTPS 重定向
- ✅ 隐藏文件和备份文件禁止访问
- ✅ 危险脚本文件禁止执行

## 📝 维护日志

| 日期       | 操作           | 说明                                 |
| ---------- | -------------- | ------------------------------------ |
| 2025-10-31 | 初始配置       | 包含 admin 和 docs 未使用域名        |
| 2025-11-01 | 配置清理       | 移除未使用的 admin 和 docs server 块 |
| 2025-11-01 | WebSocket 优化 | 增加连接超时以支持 Android           |
| 2025-11-01 | SSL 优化       | 添加 OCSP Stapling 和协议优化        |

---

**最后更新**: 2025-11-01  
**维护者**: liguoma
