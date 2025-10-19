# 域名切换快速操作指南 - 一页纸版本

> **域名**: www.horsduroot.com → 121.199.173.244  
> **操作时间**: 预计 30-60 分钟 (不含 DNS 生效时间)

---

## 🚀 快速执行 (5 步完成)

### Step 1: 上传并执行自动化脚本 (新服务器)

```bash
# 1. 将脚本上传到新服务器
scp scripts/deploy/domain-migration.sh root@121.199.173.244:/tmp/

# 2. SSH 登录新服务器
ssh root@121.199.173.244

# 3. 执行脚本
sudo bash /tmp/domain-migration.sh
```

**脚本会自动完成**:

- ✅ 检查服务状态
- ✅ 备份现有配置
- ✅ 更新 Nginx 配置
- ✅ 配置 SSL 证书
- ✅ 更新应用配置
- ✅ 验证切换结果

**中途需要你手动操作**:

- 📍 在阿里云控制台修改 DNS 解析
- 📍 输入邮箱地址（用于 SSL 证书）

---

### Step 2: 修改 DNS 解析 (阿里云控制台)

**登录**: https://dns.console.aliyun.com/

**操作**: 找到域名 `horsduroot.com`，修改 A 记录

| 记录类型 | 主机记录 | 记录值          | TTL |
| -------- | -------- | --------------- | --- |
| A        | www      | 121.199.173.244 | 600 |
| A        | @        | 121.199.173.244 | 600 |

**修改方式**: 从 `60.205.124.67` 改为 `121.199.173.244`

---

### Step 3: 等待 DNS 生效 (10-30 分钟)

```bash
# 在本地 Mac 检查
nslookup www.horsduroot.com

# 预期输出: 121.199.173.244
```

---

### Step 4: 验证切换成功 (本地 Mac)

```bash
# 在本地执行验证脚本
bash scripts/deploy/verify-domain-migration.sh
```

**关键检查项**:

- ✅ DNS 解析到新 IP
- ✅ HTTPS 访问正常
- ✅ API 接口正常
- ✅ SSL 证书有效

---

### Step 5: 更新前端和小程序配置

#### 5.1 前端配置

```bash
# 编辑配置
vim frontend/.env.production
# 改为: VITE_API_BASE_URL=https://www.horsduroot.com

# 重新构建
cd frontend && npm run build

# 部署到服务器
scp -r dist/* root@121.199.173.244:/var/www/wuhao-tutor/frontend/
```

#### 5.2 小程序配置

```bash
# 编辑配置
vim miniprogram/config/index.js
# 改为: baseUrl: 'https://www.horsduroot.com'
```

#### 5.3 微信小程序后台

登录: https://mp.weixin.qq.com/

路径: 开发管理 → 开发设置 → 服务器域名

添加: `https://www.horsduroot.com`

---

## ✅ 验收清单

- [ ] DNS 解析到新 IP (121.199.173.244)
- [ ] HTTPS 访问正常 (https://www.horsduroot.com)
- [ ] API 健康检查返回 200
- [ ] SSL 证书有效
- [ ] 前端页面正常加载
- [ ] 小程序正常访问
- [ ] 浏览器无 CORS 错误
- [ ] 微信开发者工具无域名错误

---

## 🚨 紧急回滚

如果出现严重问题，立即在阿里云控制台回滚 DNS：

```
www.horsduroot.com  →  60.205.124.67
horsduroot.com      →  60.205.124.67
TTL 改为 60 秒
```

---

## 📚 详细文档

- [完整操作指南](./domain-migration-guide.md)
- [前端配置更新](./frontend-miniprogram-config-update.md)
- [验证测试脚本](../../scripts/deploy/verify-domain-migration.sh)

---

**执行时间**: 2025-10-19  
**操作者**: liguoma  
**预计时长**: 30-60 分钟
