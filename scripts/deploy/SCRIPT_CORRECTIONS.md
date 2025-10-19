# 域名迁移脚本修正说明

> **修正日期**: 2025-10-19  
> **修正依据**: SSH 实际检查服务器配置  
> **脚本路径**: `scripts/deploy/`

---

## 📋 修正的脚本

### 1. domain-migration.sh（域名切换自动化脚本）

**修正内容**：

#### ✅ 修正 1：Nginx 配置文件路径

**原配置**：

```bash
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}.conf"
```

**修正为**：

```bash
NGINX_CONF="/etc/nginx/conf.d/${APP_NAME}.conf"  # ✅ 实际路径
```

---

#### ✅ 修正 2：Nginx 配置更新策略

**原策略**：完全覆盖配置文件

```bash
cat > "$NGINX_CONF" << 'EOF'
# 完整的新配置...
EOF
```

**问题**：

- ❌ 会丢失现有的限流配置（rate limiting）
- ❌ 会丢失现有的安全头配置
- ❌ 会丢失现有的日志配置
- ❌ 会丢失 upstream 配置

**修正为**：在现有配置基础上添加域名

```bash
# 使用 sed 在现有配置中添加域名
sed -i "s/server_name 121.199.173.244 localhost;/server_name ${DOMAIN} ${ROOT_DOMAIN} 121.199.173.244 localhost;/g" "$NGINX_CONF"
```

**优势**：

- ✅ 保留所有现有配置
- ✅ 仅添加域名支持
- ✅ 不破坏限流、安全头等配置

---

#### ✅ 修正 3：应用配置更新（.env.production）

**原配置更新**：

```bash
sed -i "s|API_BASE_URL=.*|API_BASE_URL=https://${DOMAIN}|g" "${APP_DIR}/.env.production"
sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=https://${DOMAIN}|g" "${APP_DIR}/.env.production"
```

**问题**：

- ❌ 实际配置中不存在 `API_BASE_URL` 变量
- ❌ 实际配置中不存在 `FRONTEND_URL` 变量
- ❌ 需要更新的是 `BASE_URL`
- ❌ 需要更新的是 `BACKEND_CORS_ORIGINS`

**修正为**：

```bash
# 更新 BASE_URL
if grep -q "^BASE_URL=" "${APP_DIR}/.env.production"; then
    sed -i "s|^BASE_URL=.*|BASE_URL=https://${DOMAIN}|g" "${APP_DIR}/.env.production"
else
    echo "BASE_URL=https://${DOMAIN}" >> "${APP_DIR}/.env.production"
fi

# 更新 CORS 配置（添加域名到现有列表）
if grep -q "^BACKEND_CORS_ORIGINS=" "${APP_DIR}/.env.production"; then
    CURRENT_CORS=$(grep "^BACKEND_CORS_ORIGINS=" "${APP_DIR}/.env.production" | cut -d= -f2-)
    if ! echo "$CURRENT_CORS" | grep -q "${DOMAIN}"; then
        NEW_CORS="'[\"https://${DOMAIN}\",\"http://${DOMAIN}\",\"https://${ROOT_DOMAIN}\",\"http://${ROOT_DOMAIN}\",\"https://121.199.173.244\",\"http://121.199.173.244\"]'"
        sed -i "s|^BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=${NEW_CORS}|g" "${APP_DIR}/.env.production"
    fi
fi
```

**实际变量对照**：

| 脚本原变量              | 实际变量  | 说明               |
| ----------------------- | --------- | ------------------ |
| API_BASE_URL            | ❌ 不存在 | -                  |
| FRONTEND_URL            | ❌ 不存在 | -                  |
| ✅ BASE_URL             | ✅ 存在   | 需要更新为域名     |
| ✅ BACKEND_CORS_ORIGINS | ✅ 存在   | 需要添加域名到列表 |

---

#### ✅ 修正 4：SSL 证书配置增强

**新增功能**：

1. **检查证书是否已存在**：避免重复申请

   ```bash
   if [[ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
       log_info "✓ Let's Encrypt 证书已存在，跳过申请"
       return
   fi
   ```

2. **邮箱格式验证**：

   ```bash
   if [[ ! "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
       log_warn "邮箱格式无效，使用默认邮箱"
       EMAIL="admin@${ROOT_DOMAIN}"
   fi
   ```

3. **失败处理增强**：
   ```bash
   if [[ $? -ne 0 ]]; then
       log_error "✗ SSL 证书申请失败"
       log_warn "可能的原因："
       log_warn "  1. DNS 尚未完全生效，请等待后重试"
       log_warn "  2. 80 端口未开放或被占用"
       log_warn "  3. Nginx 配置有误"
       read -p "是否继续（跳过 SSL 配置）？[y/N] " CONTINUE
       if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
           exit 1
       fi
   fi
   ```

---

#### ✅ 修正 5：增加配置备份

**新增**：

```bash
# 备份环境变量文件
cp "${APP_DIR}/.env.production" "${APP_DIR}/.env.production.backup-$(date +%Y%m%d_%H%M%S)"

# 备份 Nginx 配置（额外备份）
cp "$NGINX_CONF" "${NGINX_CONF}.pre-domain-migration"
```

---

### 2. verify-domain-migration.sh（验证脚本）

**状态**：✅ 基本正确，无需修改

**功能检查**：

- ✅ DNS 解析验证
- ✅ HTTP 跳转验证
- ✅ HTTPS 访问验证
- ✅ API 接口验证
- ✅ 性能检查
- ✅ 安全配置检查
- ✅ 静态资源验证
- ✅ 测试报告生成

---

## 🔍 修正对照表

| 配置项                | 脚本原有                      | ✅ 修正后                     |
| --------------------- | ----------------------------- | ----------------------------- |
| Nginx 配置路径        | `/etc/nginx/sites-available/` | `/etc/nginx/conf.d/`          |
| Nginx 配置更新策略    | 完全覆盖                      | 增量更新（保留现有配置）      |
| 环境变量 API_BASE_URL | 尝试更新（但不存在）          | 更新 `BASE_URL`               |
| 环境变量 FRONTEND_URL | 尝试更新（但不存在）          | 更新 `BACKEND_CORS_ORIGINS`   |
| SSL 证书申请          | 直接申请                      | 检查是否已存在 + 失败处理增强 |
| 配置备份              | 基本备份                      | 增强备份（带时间戳）          |

---

## 🎯 修正后的执行流程

### domain-migration.sh 执行步骤

1. ✅ **检查服务状态**

   - 检查 wuhao-tutor.service
   - 检查 nginx.service
   - 测试健康检查接口

2. ✅ **备份当前配置**

   - 备份 Nginx 配置（带时间戳）
   - 备份 .env.production（带时间戳）

3. ✅ **更新 Nginx 配置**（修正：增量更新）

   - 使用 sed 添加域名到 server_name
   - 保留所有现有配置（限流、安全头等）
   - 测试配置并重载

4. ✅ **等待 DNS 解析生效**

   - 提示手动修改阿里云 DNS
   - 循环检查 DNS 解析（最多 10 分钟）

5. ✅ **配置 SSL 证书**（修正：增强错误处理）

   - 检查证书是否已存在
   - 验证邮箱格式
   - 申请 Let's Encrypt 证书
   - 失败时提供详细原因和手动命令

6. ✅ **更新应用配置**（修正：更新正确的变量）

   - 更新 BASE_URL
   - 更新 BACKEND_CORS_ORIGINS
   - 重启服务

7. ✅ **验证切换结果**
   - 测试 HTTP 跳转
   - 测试 HTTPS 访问
   - 测试健康检查
   - 检查 SSL 证书

---

## 📝 使用说明

### 执行前准备

```bash
# 1. 确保脚本有执行权限
chmod +x scripts/deploy/domain-migration.sh
chmod +x scripts/deploy/verify-domain-migration.sh

# 2. 将脚本上传到新服务器
scp scripts/deploy/domain-migration.sh root@121.199.173.244:/tmp/

# 3. 检查当前配置（可选）
ssh root@121.199.173.244 "cat /etc/nginx/conf.d/wuhao-tutor.conf | grep server_name"
```

### 执行脚本

```bash
# 在新服务器上执行
ssh root@121.199.173.244
sudo bash /tmp/domain-migration.sh
```

### 验证切换

```bash
# 在本地 Mac 执行
bash scripts/deploy/verify-domain-migration.sh
```

---

## ⚠️ 重要提醒

### 1. Nginx 配置保护

脚本现在会：

- ✅ 检查域名是否已添加（避免重复修改）
- ✅ 保留所有现有配置（限流、安全头、upstream 等）
- ✅ 创建备份（`.pre-domain-migration`）

### 2. DNS 生效时间

- 正常情况：10-30 分钟
- 脚本会循环检查，最多等待 10 分钟
- 如果超时，请手动检查 DNS 设置

### 3. SSL 证书申请

**前置条件**：

- ✅ DNS 必须已生效（指向新服务器）
- ✅ 80 端口必须开放
- ✅ Nginx 配置必须正确

**失败时**：

- 脚本会提供详细原因
- 提供手动申请命令
- 询问是否继续（可跳过 SSL 配置）

### 4. 环境变量更新

**实际需要更新的变量**：

```bash
# /opt/wuhao-tutor/.env.production
BASE_URL=https://www.horsduroot.com
BACKEND_CORS_ORIGINS='["https://www.horsduroot.com","http://www.horsduroot.com","https://horsduroot.com","http://horsduroot.com","https://121.199.173.244","http://121.199.173.244"]'
```

**不需要修改**：

- 前端 `.env.production`（已使用相对路径 `/api/v1`）

---

## 🔧 手动修复命令

如果脚本执行失败，可以使用以下命令手动修复：

### 手动添加域名到 Nginx

```bash
# 备份配置
cp /etc/nginx/conf.d/wuhao-tutor.conf /etc/nginx/conf.d/wuhao-tutor.conf.backup

# 添加域名
sed -i 's/server_name 121.199.173.244 localhost;/server_name www.horsduroot.com horsduroot.com 121.199.173.244 localhost;/g' /etc/nginx/conf.d/wuhao-tutor.conf

# 测试并重载
nginx -t && systemctl reload nginx
```

### 手动申请 SSL 证书

```bash
# 确保 DNS 已生效
nslookup www.horsduroot.com

# 申请证书
certbot --nginx -d www.horsduroot.com -d horsduroot.com --email your@email.com
```

### 手动更新环境变量

```bash
# 备份
cp /opt/wuhao-tutor/.env.production /opt/wuhao-tutor/.env.production.backup

# 编辑
vim /opt/wuhao-tutor/.env.production
# 修改 BASE_URL 和 BACKEND_CORS_ORIGINS

# 重启服务
systemctl restart wuhao-tutor.service
```

---

## 📚 相关文档

- [服务器当前状态](../docs/deployment/CURRENT_SERVER_STATUS.md)
- [域名迁移指南](../docs/deployment/domain-migration-guide.md)
- [快速开始指南](../docs/deployment/QUICK-START-DOMAIN-MIGRATION.md)
- [文档修正总结](../docs/deployment/DOMAIN_MIGRATION_CORRECTIONS.md)

---

**修正完成时间**: 2025-10-19 19:30  
**修正依据**: SSH 实际检查 + 脚本逻辑分析  
**测试状态**: ⚠️ 待实际执行验证
