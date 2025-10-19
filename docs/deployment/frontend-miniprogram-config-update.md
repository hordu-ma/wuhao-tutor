# 前端和小程序域名配置更新指南

> **域名**: www.horsduroot.com  
> **更新时间**: 2025-10-19  
> **相关文档**: [域名迁移主文档](./domain-migration-guide.md)

---

## 📋 需要更新的配置文件清单

### ✅ 已由脚本自动更新

- [x] 后端 `.env.production` (新服务器上)
- [x] Nginx 配置文件 (新服务器上)

### 📝 需要手动更新

- [ ] 前端生产环境配置
- [ ] 小程序配置文件
- [ ] 微信小程序后台服务器域名

---

## 🌐 前端配置更新 (Web)

### Step 1: 更新前端环境变量

**文件位置**: `frontend/.env.production`

```bash
# 在本地项目目录执行
cd /Users/liguoma/my-devs/python/wuhao-tutor/frontend

# 编辑生产环境配置
vim .env.production
```

**修改内容**:

```bash
# API 基础 URL (修改为新域名)
VITE_API_BASE_URL=https://www.horsduroot.com

# 如果有 WebSocket 配置，也需要更新
VITE_WS_URL=wss://www.horsduroot.com/ws
```

### Step 2: 重新构建前端

```bash
# 确保依赖已安装
npm install

# 生产环境构建
npm run build

# 构建完成后，dist 目录包含所有静态文件
```

### Step 3: 部署到服务器

```bash
# 方法 1: 使用 SCP 上传
scp -r dist/* root@121.199.173.244:/var/www/wuhao-tutor/frontend/

# 方法 2: 使用 rsync (推荐，支持增量更新)
rsync -avz --delete dist/ root@121.199.173.244:/var/www/wuhao-tutor/frontend/

# 方法 3: 在服务器上直接构建 (不推荐，消耗服务器资源)
ssh root@121.199.173.244
cd /opt/wuhao-tutor/frontend
git pull
npm install
npm run build
```

### Step 4: 验证前端部署

```bash
# 访问前端页面
open https://www.horsduroot.com

# 检查浏览器控制台
# 1. Network 选项卡确认 API 请求指向新域名
# 2. Console 选项卡确认无跨域错误
```

---

## 📱 小程序配置更新

### Step 1: 更新小程序配置文件

**文件位置**: `miniprogram/config/index.js`

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor/miniprogram

# 编辑配置文件
vim config/index.js
```

**修改内容**:

```javascript
// 生产环境配置
const production = {
  api: {
    baseUrl: 'https://www.horsduroot.com', // 修改为新域名
    timeout: 30000,
  },
  appId: 'your-wechat-appid', // 微信小程序 AppID
}

// 开发环境配置 (保持不变或根据需要修改)
const development = {
  api: {
    baseUrl: 'http://121.199.173.244', // 开发环境可保留 IP
    timeout: 30000,
  },
}

// 根据环境变量选择配置
const config = process.env.NODE_ENV === 'production' ? production : development

module.exports = config
```

### Step 2: 更新小程序其他可能的配置

**检查以下文件是否有域名引用**:

```bash
# 搜索旧 IP 地址
grep -r "121.199.173.244" miniprogram/
grep -r "60.205.124.67" miniprogram/

# 搜索可能的域名配置
grep -r "baseUrl\|BASE_URL\|api_url" miniprogram/ --include="*.js"
```

**常见需要更新的位置**:

1. **`miniprogram/utils/request.js`** (如果有硬编码 URL)
2. **`miniprogram/app.js`** (全局配置)
3. **`miniprogram/project.config.json`** (项目配置，一般不需要改)

---

## 🔐 微信小程序后台配置

### Step 1: 登录微信公众平台

访问: https://mp.weixin.qq.com/

使用你的微信小程序管理员账号登录

### Step 2: 配置服务器域名

**路径**: 开发管理 → 开发设置 → 服务器域名

#### 2.1 request 合法域名

点击 **修改** 按钮，添加以下域名：

```
https://www.horsduroot.com
```

**配置截图示例**:

```
┌─────────────────────────────────────────┐
│ request 合法域名                         │
├─────────────────────────────────────────┤
│ https://www.horsduroot.com             │
│                                         │
│ [+ 添加]                                │
└─────────────────────────────────────────┘
```

#### 2.2 uploadFile 合法域名

如果小程序有文件上传功能，也需要添加：

```
https://www.horsduroot.com
```

#### 2.3 downloadFile 合法域名

如果小程序有文件下载功能，也需要添加：

```
https://www.horsduroot.com
```

#### 2.4 删除旧配置 (如果有)

如果之前配置了 IP 地址或其他域名，建议删除：

- ~~`https://60.205.124.67`~~
- ~~`http://121.199.173.244`~~ (HTTP 不被允许)

**注意事项**:

- ✅ 必须使用 HTTPS 协议
- ✅ 域名必须已备案 (中国大陆服务器)
- ✅ 配置后 **5-10 分钟** 生效
- ❌ 不支持 IP 地址
- ❌ 不支持 HTTP 协议
- ❌ 不支持端口号 (默认 443)

### Step 3: 验证域名配置

**在微信开发者工具中测试**:

1. 打开微信开发者工具
2. 加载小程序项目
3. 点击 **编译** 按钮
4. 查看 **Console** 选项卡

**预期结果**:

```
✓ request 成功: https://www.horsduroot.com/api/v1/xxx
✓ 无 "不在以下 request 合法域名列表中" 错误
```

**如果报错**:

```
不在以下 request 合法域名列表中，请参考文档
```

**解决方案**:

1. 确认域名已在微信公众平台配置
2. 等待 5-10 分钟配置生效
3. 重启微信开发者工具
4. 清除小程序缓存: 工具 → 清除缓存

---

## 🧪 测试清单

### 前端测试

- [ ] 页面正常加载 (https://www.horsduroot.com)
- [ ] 用户登录功能正常
- [ ] API 请求指向新域名
- [ ] 图片和静态资源正常加载
- [ ] WebSocket 连接正常 (如有)
- [ ] 浏览器控制台无 CORS 错误
- [ ] 浏览器控制台无跨域错误

### 小程序测试

- [ ] 小程序正常启动
- [ ] 登录功能正常
- [ ] API 请求成功
- [ ] 图片上传功能正常
- [ ] 错题本功能正常
- [ ] 学习记录同步正常
- [ ] 无 "域名不合法" 错误

---

## 🔄 完整更新流程总结

### 1️⃣ 本地更新配置文件

```bash
# 前端配置
vim frontend/.env.production
# 修改: VITE_API_BASE_URL=https://www.horsduroot.com

# 小程序配置
vim miniprogram/config/index.js
# 修改: baseUrl: 'https://www.horsduroot.com'
```

### 2️⃣ 重新构建前端

```bash
cd frontend
npm run build
```

### 3️⃣ 部署到服务器

```bash
# 上传前端静态文件
scp -r dist/* root@121.199.173.244:/var/www/wuhao-tutor/frontend/
```

### 4️⃣ 配置微信小程序后台

- 登录微信公众平台
- 添加服务器域名: `https://www.horsduroot.com`
- 删除旧域名配置
- 等待 5-10 分钟生效

### 5️⃣ 测试验证

```bash
# 使用验证脚本
bash scripts/deploy/verify-domain-migration.sh

# 手动测试
# 1. 浏览器访问 https://www.horsduroot.com
# 2. 微信开发者工具测试小程序
# 3. 真机测试小程序
```

---

## ⚠️ 注意事项

### 前端缓存问题

**问题**: 用户浏览器缓存旧版本前端代码

**解决方案**:

1. **添加版本号** (推荐):

   ```javascript
   // vite.config.ts
   export default defineConfig({
     build: {
       rollupOptions: {
         output: {
           entryFileNames: `assets/[name].[hash].js`,
           chunkFileNames: `assets/[name].[hash].js`,
           assetFileNames: `assets/[name].[hash].[ext]`,
         },
       },
     },
   })
   ```

2. **清除缓存提示**:
   - 在前端添加版本检查逻辑
   - 版本不匹配时提示用户刷新页面

### 小程序审核

**如果小程序已发布**:

1. 修改配置后需要重新提交审核
2. 审核通过前，线上版本仍使用旧配置
3. 建议在低峰时段发布新版本

**如果小程序未发布**:

1. 直接修改配置即可
2. 提交审核时确保域名配置正确

### CORS 配置检查

**后端 CORS 配置** (应已在脚本中更新):

```python
# .env.production
CORS_ORIGINS=["https://www.horsduroot.com", "https://horsduroot.com"]
```

**验证方式**:

```bash
# 测试跨域请求
curl -H "Origin: https://www.horsduroot.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://www.horsduroot.com/api/v1/xxx -v
```

---

## 📞 问题排查

### 问题 1: 前端 API 请求 404

**原因**: Nginx 配置错误或后端服务未运行

**排查步骤**:

```bash
# 1. 检查 Nginx 配置
ssh root@121.199.173.244
nginx -t

# 2. 检查后端服务
systemctl status wuhao-tutor.service

# 3. 查看错误日志
tail -f /var/log/nginx/error.log
```

### 问题 2: 小程序提示域名不合法

**原因**: 微信小程序后台未配置域名

**解决方案**:

1. 确认已在微信公众平台配置域名
2. 等待 5-10 分钟生效
3. 重启微信开发者工具
4. 检查域名拼写是否正确

### 问题 3: 前端静态资源 404

**原因**: 静态文件路径配置错误

**解决方案**:

```bash
# 检查 Nginx 静态文件配置
cat /etc/nginx/sites-available/wuhao-tutor.conf

# 确认静态文件目录存在
ls -la /var/www/wuhao-tutor/static/
ls -la /var/www/wuhao-tutor/uploads/
```

---

## ✅ 验收标准

### 前端

- ✅ 浏览器访问 https://www.horsduroot.com 正常
- ✅ 所有页面正常加载
- ✅ API 请求成功（200 OK）
- ✅ 浏览器控制台无错误
- ✅ SSL 证书有效（绿色锁图标）

### 小程序

- ✅ 小程序正常启动
- ✅ 所有功能正常使用
- ✅ 无 "域名不合法" 错误
- ✅ 图片上传/下载正常
- ✅ 数据同步正常

---

**文档版本**: v1.0  
**更新时间**: 2025-10-19  
**相关脚本**:

- [域名切换脚本](../../scripts/deploy/domain-migration.sh)
- [验证测试脚本](../../scripts/deploy/verify-domain-migration.sh)
