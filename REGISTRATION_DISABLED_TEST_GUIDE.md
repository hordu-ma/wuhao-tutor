# 生产环境注册禁用功能 - 测试指南

## 📋 功能概述

本次修改实现了生产环境禁止用户自主注册的功能，用户需要通过助教老师开通账户后才能登录使用系统。

## 🎯 实现内容

### 前端修改
1. ✅ 创建了新的注册禁用提示页面 (`RegistrationDisabledView.vue`)
2. ✅ 更新了路由配置，添加 `/register-disabled` 路由
3. ✅ 修改了登录页面的"立即注册"按钮逻辑，根据环境自动跳转

### 后端修改
1. ✅ 在注册接口添加了环境检查逻辑
2. ✅ 生产环境下返回 403 错误，禁止注册
3. ✅ 添加了安全日志记录

## 🧪 测试计划

### 一、开发环境测试（ENVIRONMENT=development）

#### 1.1 前端测试
```bash
# 启动开发服务器
cd /Users/liguoma/my-devs/python/wuhao-tutor/frontend
npm run dev
```

**测试步骤：**
- [ ] 访问 http://localhost:5173/login
- [ ] 点击"立即注册"按钮
- [ ] **预期结果**：跳转到 `/register` 注册页面（正常注册表单）
- [ ] 填写注册信息并提交
- [ ] **预期结果**：可以成功注册新用户

#### 1.2 后端测试
```bash
# 确认环境变量
echo $ENVIRONMENT  # 应该为空或 development

# 启动后端服务
cd /Users/liguoma/my-devs/python/wuhao-tutor
make dev
```

**API 测试：**
```bash
# 测试注册接口（应该成功）
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138001",
    "name": "测试用户",
    "password": "Test123456",
    "password_confirm": "Test123456",
    "verification_code": "123456",
    "role": "student"
  }'
```

**预期响应**：返回 200 状态码，包含登录 token 和用户信息

---

### 二、生产环境测试（ENVIRONMENT=production）

#### 2.1 设置生产环境
```bash
# 方式1：设置环境变量
export ENVIRONMENT=production

# 方式2：修改 .env 文件
# 编辑 .env 文件，设置：
# ENVIRONMENT=production
```

#### 2.2 前端测试（生产构建）
```bash
# 构建生产版本
cd /Users/liguoma/my-devs/python/wuhao-tutor/frontend
npm run build

# 预览生产构建（可选）
npm run preview
```

**测试步骤：**
- [ ] 访问生产环境的登录页面
- [ ] 点击"立即注册"按钮
- [ ] **预期结果**：跳转到 `/register-disabled` 提示页面
- [ ] 查看页面显示内容
- [ ] **预期结果**：显示优雅的提示信息，说明需要联系助教老师开通账户
- [ ] 点击"返回登录"按钮
- [ ] **预期结果**：跳转回 `/login` 登录页面

#### 2.3 直接访问注册页面测试
- [ ] 尝试直接访问 `/register` 路由
- [ ] **预期结果**：前端仍然显示注册表单（路由未限制）
- [ ] 填写信息并尝试提交
- [ ] **预期结果**：后端返回 403 错误，提示"生产环境不支持自主注册，请联系助教老师开通账户"

#### 2.4 后端 API 测试
```bash
# 确认环境变量
echo $ENVIRONMENT  # 应该为 production

# 测试注册接口（应该被拒绝）
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138002",
    "name": "测试用户2",
    "password": "Test123456",
    "password_confirm": "Test123456",
    "verification_code": "123456",
    "role": "student"
  }'
```

**预期响应**：
```json
{
  "detail": "生产环境不支持自主注册，请联系助教老师开通账户"
}
```
状态码：403 Forbidden

#### 2.5 日志检查
```bash
# 查看后端日志
tail -f logs/app.log | grep "生产环境注册尝试被阻止"
```

**预期结果**：日志记录包含被阻止的注册尝试，包括手机号和 IP 地址

---

### 三、响应式设计测试

#### 3.1 桌面端测试
- [ ] 浏览器窗口：1920x1080
- [ ] 检查页面布局是否正常
- [ ] 检查按钮是否可点击
- [ ] 检查文字是否清晰可读

#### 3.2 平板端测试
- [ ] 浏览器窗口：768x1024
- [ ] 检查页面自适应效果
- [ ] 检查步骤说明是否显示完整

#### 3.3 移动端测试
- [ ] 浏览器窗口：375x667 (iPhone SE)
- [ ] 检查页面在小屏幕上的显示
- [ ] 确认按钮大小适合点击
- [ ] 确认文字大小适合阅读

---

## 📝 部署前检查清单

### 前端
- [x] 新页面组件已创建：`RegistrationDisabledView.vue`
- [x] 路由配置已更新：添加 `/register-disabled` 路由
- [x] 登录页面逻辑已修改：环境条件跳转
- [ ] 生产构建成功：`npm run build`
- [ ] 构建产物已生成：`frontend/dist/` 目录

### 后端
- [x] 注册接口已添加环境检查
- [x] 生产环境返回 403 错误
- [x] 添加了安全日志记录
- [ ] Python 语法检查通过
- [ ] 本地测试通过

### 环境配置
- [ ] 确认生产服务器 `.env` 文件中 `ENVIRONMENT=production`
- [ ] 确认开发环境 `.env` 文件中 `ENVIRONMENT=development` 或未设置

---

## 🚀 部署步骤

### 1. Git 提交
```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor

# 查看修改的文件
git status

# 添加修改的文件
git add frontend/src/views/auth/RegistrationDisabledView.vue
git add frontend/src/router/index.ts
git add frontend/src/views/auth/LoginView.vue
git add src/api/v1/endpoints/auth.py
git add REGISTRATION_DISABLED_TEST_GUIDE.md

# 提交
git commit -m "feat(auth): 生产环境禁用自主注册功能

- 创建注册禁用提示页面，提供优雅的用户引导
- 前端根据环境自动跳转到对应页面
- 后端添加生产环境注册限制，返回403错误
- 保留开发环境的正常注册功能
- 添加完整的响应式设计支持

Closes #注册管理需求"
```

### 2. 部署到生产环境
```bash
# 使用您的部署脚本
./scripts/deploy_to_production.sh

# 或手动部署
# 1. 同步代码到生产服务器
# 2. 构建前端
# 3. 重启后端服务
# 4. 验证功能
```

### 3. 部署后验证
- [ ] 访问生产环境登录页面
- [ ] 点击"立即注册"，确认跳转到禁用提示页
- [ ] 尝试调用注册 API，确认返回 403
- [ ] 检查系统日志，确认记录正常
- [ ] 使用已有账户登录，确认正常功能不受影响

---

## 🔧 回滚方案

如果部署后发现问题，可以快速回滚：

```bash
# 1. Git 回滚
git revert HEAD
git push

# 2. 重新部署上一个版本
./scripts/deploy_to_production.sh

# 3. 或临时修改环境变量（不推荐）
# 在 .env 中设置 ENVIRONMENT=development
```

---

## 📞 联系方式

如有问题，请联系：
- 项目维护者: Liguo Ma
- 邮箱: maliguo@outlook.com

---

## 📅 更新记录

- **2025-10-12**: 初始版本创建，实现生产环境注册禁用功能
