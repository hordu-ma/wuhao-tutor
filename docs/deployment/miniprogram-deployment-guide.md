# 微信小程序部署上线完整指南

> 五好伴学小程序从开发到生产上线的完整流程
> 最后更新：2025-10-19

---

## 📋 目录

- [准备阶段](#准备阶段)
- [配置检查](#配置检查)
- [构建上传](#构建上传)
- [提交审核](#提交审核)
- [发布上线](#发布上线)
- [问题排查](#问题排查)

---

## 🎯 准备阶段

### 1. 微信小程序账号准备

#### 注册小程序账号

1. **访问微信公众平台**

   - 地址：https://mp.weixin.qq.com/
   - 点击"立即注册" → 选择"小程序"

2. **完成账号注册**

   ```
   步骤 1：填写邮箱并验证
   步骤 2：选择主体类型（个人/企业/政府/其他组织）
   步骤 3：填写主体信息
   步骤 4：完成认证（企业需要300元认证费）
   ```

3. **记录关键信息**
   ```yaml
   AppID: wx2a8b340606664785 # 当前项目已配置的 AppID
   AppSecret: 需在小程序后台获取
   原始ID: gh_xxxxxxxxxxxxx
   ```

#### 主体认证类型建议

| 类型     | 适用场景   | 费用    | 审核周期 | 功能限制         |
| -------- | ---------- | ------- | -------- | ---------------- |
| **个人** | 个人开发者 | 免费    | 1-2 天   | 部分高级功能受限 |
| **企业** | 公司运营   | ¥300/年 | 3-5 天   | 功能完整         |
| **教育** | 学校/机构  | 免费    | 3-7 天   | 功能完整         |

**建议**：由于是教育类应用，推荐使用**企业**或**教育机构**主体，可使用支付、数据分析等完整功能。

### 2. 服务器域名配置

#### 域名要求检查清单

- [x] **HTTPS 协议**：必须使用 HTTPS（已满足：https://www.horsduroot.com）
- [ ] **域名备案**：需在工信部完成备案（⚠️ 请确认）
- [x] **SSL 证书**：有效期内的 SSL 证书
- [x] **80/443 端口**：正常访问

#### 在小程序后台配置域名

1. **登录小程序后台**

   - 访问：https://mp.weixin.qq.com/
   - 使用管理员微信扫码登录

2. **添加服务器域名**

   ```
   位置：开发 → 开发管理 → 开发设置 → 服务器域名

   request 合法域名（业务域名）:
     https://www.horsduroot.com

   uploadFile 合法域名（文件上传）:
     https://www.horsduroot.com

   downloadFile 合法域名（文件下载）:
     https://www.horsduroot.com
     https://t.alicdn.com        # 阿里云 CDN（如使用）
     https://at.alicdn.com       # 阿里云 CDN（如使用）
   ```

3. **业务域名配置**（可选）

   ```
   位置：开发 → 开发管理 → 业务域名

   用途：web-view 组件跳转
   域名：https://www.horsduroot.com

   验证：下载验证文件，上传到域名根目录
   ```

#### 域名配置注意事项

⚠️ **重要提示**：

- 域名配置后需要等待 **5-10 分钟**生效
- 一个月内最多可修改 **5 次**
- 必须下载**校验文件**并上传至服务器根目录
- 测试时可以在开发者工具中勾选"不校验合法域名"

### 3. 后端 API 准备

#### API 接口检查

确保生产环境 API 可正常访问：

```bash
# 测试健康检查接口
curl https://www.horsduroot.com/api/v1/health

# 预期响应
{
  "status": "healthy",
  "timestamp": "2025-10-19T10:00:00Z",
  "version": "1.0.0"
}
```

#### 跨域配置检查

确保后端 FastAPI 配置了正确的 CORS：

```python
# src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### API 限流配置

检查生产环境限流设置（避免小程序大量请求被拦截）：

```python
# src/core/security.py
RATE_LIMITS = {
    "ip": {"limit": 100, "window": 60},      # IP: 100次/分钟
    "user": {"limit": 50, "window": 60},     # 用户: 50次/分钟
    "ai": {"limit": 20, "window": 60},       # AI: 20次/分钟
}
```

---

## ⚙️ 配置检查

### 4. 小程序项目配置

#### 检查 `project.config.json`

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor/miniprogram
```

确认关键配置：

```json
{
  "appid": "wx2a8b340606664785", // ✅ 确认是你的 AppID
  "projectname": "五好伴学小程序",
  "libVersion": "2.32.3", // 基础库版本
  "compileType": "miniprogram",

  "setting": {
    "urlCheck": true, // ⚠️ 上线前改为 true（检查域名）
    "es6": true,
    "minified": true, // ✅ 代码压缩
    "minifyWXML": true,
    "minifyWXSS": true
  },

  "requestDomain": [
    "https://121.199.173.244" // ⚠️ 需改为域名
  ]
}
```

**需要修改的配置**：

```json
{
  "setting": {
    "urlCheck": true // 开发时可为 false，上线必须 true
  },
  "requestDomain": [
    "https://www.horsduroot.com" // 从 IP 改为域名
  ]
}
```

#### 检查 `config/index.js`

```javascript
const config = {
  // ✅ 环境配置
  environment: 'production',
  debug: false,
  version: '1.0.0',

  // ⚠️ API 配置（需修改）
  api: {
    baseUrl: 'https://www.horsduroot.com', // 从 IP 改为域名
    version: 'v1',
    timeout: 10000,
  },

  // ✅ 上传配置
  upload: {
    maxFileSize: 10 * 1024 * 1024, // 10MB
    compressQuality: 0.8,
  },
}

module.exports = config
```

### 5. 版本信息更新

#### 更新 `app.json`

```json
{
  "version": "1.0.0",
  "description": "五好伴学 K12 智能学习平台"
}
```

#### 更新 `package.json`

```json
{
  "name": "wuhao-tutor-miniprogram",
  "version": "1.0.0",
  "description": "五好伴学微信小程序"
}
```

---

## 📦 构建上传

### 6. 代码检查与构建

#### 步骤 1：安装依赖

```bash
cd miniprogram
npm install
```

#### 步骤 2：代码质量检查

```bash
# 运行代码检查
npm run lint

# 运行类型检查
npm run type-check

# 格式化代码
npm run format
```

#### 步骤 3：构建小程序 npm

微信小程序需要构建 npm 依赖：

1. 打开微信开发者工具
2. 点击菜单："工具" → "构建 npm"
3. 等待构建完成（生成 `miniprogram_npm/` 目录）

**或使用命令行**：

```bash
# 安装 miniprogram-ci
npm install -g @weixin-devtools/cli

# 构建 npm
miniprogram-ci build-npm --project .
```

#### 步骤 4：真机预览测试

1. **在开发者工具中预览**

   - 点击工具栏"预览"按钮
   - 使用微信扫码
   - 在手机上测试功能

2. **测试关键功能**

   - [ ] 微信登录授权
   - [ ] 作业问答（AI 对话）
   - [ ] 错题手册（增删改查）
   - [ ] 学习报告（图表展示）
   - [ ] 图片上传
   - [ ] 个人中心

3. **性能检查**
   - 打开"调试器" → "Audits"
   - 运行性能评分
   - 优化低分项

### 7. 上传代码到微信平台

#### 方式一：使用开发者工具上传（推荐）

1. **点击"上传"按钮**

   - 工具栏右上角"上传"图标
   - 或快捷键：`⌘ + Shift + U`（macOS）

2. **填写版本信息**

   ```
   版本号：1.0.0
   项目备注：
     - 初始版本
     - 核心功能：作业问答、错题手册、学习报告
     - 支持微信登录、图片上传
   ```

3. **上传成功确认**
   - 等待上传完成（可能需要 2-5 分钟）
   - 上传成功后，在小程序后台"版本管理"中可见

#### 方式二：使用命令行工具（CI/CD）

**安装 miniprogram-ci**：

```bash
npm install -g miniprogram-ci
```

**创建上传脚本**：

```javascript
// scripts/upload.js
const ci = require('miniprogram-ci')
const path = require('path')

const project = new ci.Project({
  appid: 'wx2a8b340606664785',
  type: 'miniProgram',
  projectPath: path.resolve(__dirname, '../miniprogram'),
  privateKeyPath: path.resolve(__dirname, '../secrets/upload-key.txt'),
  ignores: ['node_modules/**/*'],
})

;(async () => {
  const uploadResult = await ci.upload({
    project,
    version: '1.0.0',
    desc: '初始版本上传',
    setting: {
      es6: true,
      minified: true,
    },
  })
  console.log('上传成功：', uploadResult)
})()
```

**执行上传**：

```bash
node scripts/upload.js
```

---

## 🔍 提交审核

### 8. 提交审核前准备

#### 准备审核材料

**必需材料**：

1. **小程序截图**（3-5 张）

   - 首页截图
   - 核心功能截图（作业问答、错题手册）
   - 个人中心截图
   - 分辨率：750px × 1334px（iPhone 6/7/8）

2. **小程序服务类目**

   ```
   一级类目：教育
   二级类目：在线教育
   ```

3. **隐私政策与用户协议**

   - 需要有独立的隐私政策页面
   - 用户协议页面
   - 数据使用说明

4. **特殊资质**（如需要）
   - 教育机构资质证明
   - ICP 备案号
   - 软件著作权（可选）

#### 配置隐私政策

**在小程序后台配置**：

```
位置：设置 → 基本设置 → 服务内容声明 → 用户隐私保护指引

内容要点：
1. 收集的用户信息（微信昵称、头像、手机号）
2. 信息使用目的（身份认证、学习记录、数据分析）
3. 第三方共享情况（阿里云 AI 服务）
4. 用户权利（查看、修改、删除个人信息）
5. 联系方式
```

**在小程序中添加隐私协议页面**：

```javascript
// pages/profile/privacy/index.js
Page({
  data: {
    content: '隐私政策内容...',
  },
})
```

### 9. 提交审核

#### 步骤 1：进入版本管理

1. 登录小程序后台
2. 进入"管理" → "版本管理"
3. 找到"开发版本"中的最新上传版本

#### 步骤 2：填写审核信息

```yaml
版本号: 1.0.0

版本描述: 五好伴学 K12 智能学习平台首次发布版本

  核心功能：
  1. AI 作业问答 - 基于阿里云百炼的智能学习助手
  2. 错题手册 - 错题记录、复习提醒、掌握度追踪
  3. 学习报告 - 学习时长、知识点掌握、学科分布分析
  4. 个人中心 - 用户信息管理、头像上传、学习统计

服务类目: 教育 → 在线教育

测试账号:
  用户名: test_user
  密码: test123456
  说明: 提供完整功能访问权限

服务器域名: https://www.horsduroot.com

页面截图:
  - 首页（展示功能入口）
  - 作业问答页（AI 对话界面）
  - 错题手册页（错题列表）
  - 学习报告页（数据可视化）
  - 个人中心页（用户信息）
```

#### 步骤 3：配置审核快捷入口

为审核人员配置测试路径：

```json
// app.json 中配置
{
  "testAccount": {
    "username": "test_user",
    "password": "test123456"
  },

  "testPath": [
    "pages/index/index", // 首页
    "pages/learning/index/index", // 作业问答
    "pages/mistakes/list/index", // 错题手册
    "pages/analysis/report/index", // 学习报告
    "pages/profile/index/index" // 个人中心
  ]
}
```

#### 步骤 4：提交审核

1. 点击"提交审核"按钮
2. 确认信息无误
3. 等待微信审核团队审核

**审核时间**：

- 正常情况：1-7 个工作日
- 节假日：可能延长至 7-14 天
- 首次提交：可能需要 3-7 天

---

## ✅ 发布上线

### 10. 审核通过后发布

#### 审核结果通知

审核结果会通过以下方式通知：

1. **微信公众平台通知**

   - 小程序后台"消息"中心
   - 管理员微信会收到服务通知

2. **邮件通知**

   - 注册邮箱会收到审核结果

3. **审核状态查看**
   - 小程序后台："管理" → "版本管理" → "审核版本"

#### 审核通过 - 发布上线

1. **进入版本管理**

   ```
   路径：管理 → 版本管理 → 审核版本
   ```

2. **点击"发布"按钮**

   - 确认发布
   - 发布后 5-10 分钟生效

3. **验证线上版本**
   - 在微信中搜索"五好伴学"
   - 打开小程序
   - 测试核心功能

#### 审核失败 - 问题修复

**常见审核失败原因**：

| 失败原因                  | 解决方案                               |
| ------------------------- | -------------------------------------- |
| **服务类目不符**          | 重新选择正确的类目，提供相关资质       |
| **缺少用户协议/隐私政策** | 添加独立的协议页面，并在登录时展示     |
| **功能描述不清晰**        | 完善版本描述，添加详细的功能说明       |
| **测试账号无法登录**      | 检查测试账号有效性，提供准确的登录信息 |
| **涉及支付功能未申请**    | 如有支付，需申请微信支付权限           |
| **包含违规内容**          | 检查并移除任何违规文字、图片、链接     |
| **功能无法正常使用**      | 修复 Bug，确保所有功能稳定运行         |

**修复流程**：

1. 查看审核失败详细原因
2. 修改代码或配置
3. 重新上传代码
4. 再次提交审核

---

## 🔧 问题排查

### 11. 常见问题与解决方案

#### 问题 1：网络请求失败

**症状**：

```
request:fail url not in domain list
```

**原因**：

- API 域名未在小程序后台配置
- 或开发工具未勾选"不校验合法域名"

**解决**：

1. 在小程序后台添加域名
2. 等待 5-10 分钟生效
3. 或开发工具中："设置" → "项目设置" → 勾选"不校验合法域名"（仅开发时）

#### 问题 2：图片上传失败

**症状**：

```
uploadFile:fail
```

**原因**：

- uploadFile 域名未配置
- 文件大小超过限制（小程序限制 10MB）

**解决**：

```javascript
// 压缩图片后上传
wx.compressImage({
  src: tempFilePath,
  quality: 80,
  success(res) {
    wx.uploadFile({
      url: `${config.api.baseUrl}/api/v1/upload`,
      filePath: res.tempFilePath,
      name: 'file',
    })
  },
})
```

#### 问题 3：微信登录失败

**症状**：

```
login:fail
```

**原因**：

- AppID 或 AppSecret 配置错误
- 后端未正确处理 code 换取 session_key

**解决**：

1. 确认 AppID 和 AppSecret 正确
2. 检查后端 `/api/v1/auth/wechat/login` 接口
3. 查看后端日志排查问题

#### 问题 4：真机预览白屏

**症状**：

- 开发工具正常，真机白屏

**原因**：

- ES6 语法未转译
- 使用了不支持的 API

**解决**：

1. 开启 ES6 转 ES5

   ```json
   // project.config.json
   {
     "setting": {
       "es6": true
     }
   }
   ```

2. 检查基础库版本兼容性
   ```json
   {
     "libVersion": "2.32.3" // 确保不低于最低要求
   }
   ```

#### 问题 5：审核被拒 - 功能不完整

**症状**：

- 审核反馈"功能无法正常使用"

**解决**：

1. 提供有效的测试账号
2. 在"版本描述"中详细说明测试路径
3. 确保所有页面都可以正常访问
4. 提前自测所有功能

---

## 📊 发布后监控

### 12. 线上监控

#### 小程序数据分析

**在小程序后台查看**：

```
位置：统计 → 数据分析

关键指标：
- 访问分析（PV、UV、活跃用户）
- 实时统计（在线用户数）
- 访问页面（页面访问排名）
- 访问来源（场景值分析）
- 用户画像（地域、性别、年龄）
- 留存分析（日留存、周留存）
```

#### 后端 API 监控

确保后端配置了监控：

```bash
# 查看 API 日志
tail -f /var/log/wuhao-tutor/app.log

# 监控关键指标
curl https://www.horsduroot.com/api/v1/health/metrics
```

#### 错误日志收集

**小程序端**：

```javascript
// app.js
App({
  onError(error) {
    // 上报错误到后端
    wx.request({
      url: `${config.api.baseUrl}/api/v1/logs/error`,
      method: 'POST',
      data: {
        error: error,
        page: getCurrentPages().pop().route,
        timestamp: Date.now(),
      },
    })
  },
})
```

---

## 📝 发布检查清单

### 上线前完整检查

- [ ] **账号准备**

  - [ ] 已注册并认证小程序账号
  - [ ] 已获取 AppID 和 AppSecret
  - [ ] 已设置管理员和开发者权限

- [ ] **域名配置**

  - [ ] 域名已备案
  - [ ] HTTPS 证书有效
  - [ ] 已在小程序后台配置服务器域名
  - [ ] 已在小程序后台配置业务域名（如需）

- [ ] **代码配置**

  - [ ] `project.config.json` 中 AppID 正确
  - [ ] `config/index.js` 中 API 地址为生产域名
  - [ ] `urlCheck` 设置为 `true`
  - [ ] 已构建 npm 包

- [ ] **功能测试**

  - [ ] 微信登录正常
  - [ ] 作业问答功能正常
  - [ ] 错题手册功能正常
  - [ ] 学习报告展示正常
  - [ ] 图片上传正常
  - [ ] 个人中心功能正常

- [ ] **审核材料**

  - [ ] 已准备 3-5 张截图
  - [ ] 已添加隐私政策页面
  - [ ] 已添加用户协议页面
  - [ ] 已准备测试账号
  - [ ] 版本描述清晰完整

- [ ] **性能优化**

  - [ ] 代码已压缩
  - [ ] 图片已压缩
  - [ ] 无明显性能问题
  - [ ] 首屏加载时间 < 3 秒

- [ ] **上传发布**
  - [ ] 已上传代码到微信平台
  - [ ] 已提交审核
  - [ ] 审核通过后已发布

---

## 🚀 后续迭代

### 版本更新流程

1. **开发新功能**

   - 在开发分支开发
   - 完成功能测试

2. **更新版本号**

   ```json
   // package.json
   {
     "version": "1.1.0" // 遵循语义化版本
   }
   ```

3. **上传代码**

   - 上传新版本到微信平台
   - 版本号递增（1.0.0 → 1.1.0 → 1.2.0）

4. **提交审核**

   - 填写版本更新说明
   - 说明新增功能和修复的问题

5. **发布上线**
   - 审核通过后发布
   - 用户会自动更新

### 灰度发布

**适用场景**：

- 重大功能更新
- 高风险变更

**操作步骤**：

1. 小程序后台："管理" → "版本管理" → "灰度发布"
2. 设置灰度比例（如 10%）
3. 观察数据和反馈
4. 逐步扩大比例
5. 全量发布

---

## 📞 获取帮助

### 官方文档

- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [小程序运营规范](https://developers.weixin.qq.com/miniprogram/product/)
- [小程序审核指南](https://developers.weixin.qq.com/miniprogram/product/reject.html)

### 社区支持

- [微信开放社区](https://developers.weixin.qq.com/community/)
- [小程序开发者论坛](https://developers.weixin.qq.com/community/develop/mixflow)

### 项目联系方式

- **项目地址**: https://github.com/hordu-ma/wuhao-tutor
- **问题反馈**: https://github.com/hordu-ma/wuhao-tutor/issues

---

**文档维护者**: hordu-ma  
**最后更新**: 2025-10-19  
**版本**: v1.0
