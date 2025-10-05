# 登录重复问题诊断与修复

## 问题描述

用户从仪表盘点击"学习问答"时，需要再次登录才能进入页面。

## 问题分析

### 1. 路由守卫流程

每次路由跳转时，`router/index.ts` 的 `beforeEach` 守卫会执行以下检查：

```typescript
// 如果明确设置为需要认证
if (requiresAuth === true) {
  // 检查是否登录
  if (!authStore.isAuthenticated) {
    next('/login') // ← 重定向到登录页
    return
  }

  // 验证token有效性
  const isValid = await authStore.validateAuth() // ← 关键检查
  if (!isValid) {
    next('/login') // ← 重定向到登录页
    return
  }
}
```

### 2. Token 验证逻辑 (`stores/auth.ts`)

```typescript
async validateAuth(): Promise<boolean> {
  if (!this.isAuthenticated || !this.accessToken) {
    return false;  // ← 导致重定向到登录页
  }

  // 如果token过期，尝试刷新
  if (this.isTokenExpired()) {
    return await this.refreshAccessToken()  // ← 可能失败
  }

  // 验证用户信息是否完整
  if (!this.user) {
    await this.fetchUserInfo()
  }

  return this.isAuthenticated
}
```

### 3. Token 过期检查 (`stores/auth.ts`)

```typescript
isTokenExpired(token?: string): boolean {
  try {
    const actualToken = token || this.accessToken
    if (!actualToken) return true  // ← 没有 token，返回已过期

    const payload = JSON.parse(atob(actualToken.split('.')[1]))
    const exp = payload.exp * 1000

    return Date.now() >= exp  // ← 时间戳比较
  } catch {
    return true  // ← 解析失败，返回已过期
  }
}
```

## 可能的原因

### 原因 1: Token 未正确保存到 localStorage/sessionStorage

**检查方法**：

1. 打开浏览器开发者工具
2. 进入 Application/Storage 标签
3. 查看 localStorage 和 sessionStorage 中是否有 `access_token`

**检查脚本**：

```javascript
// 在浏览器控制台执行
const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
console.log('Token:', token)
console.log('User Info:', localStorage.getItem('user_info') || sessionStorage.getItem('user_info'))
```

### 原因 2: Token 格式不正确或解析失败

**检查方法**：

```javascript
// 在浏览器控制台执行
const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
if (token) {
  try {
    const parts = token.split('.')
    if (parts.length === 3) {
      const payload = JSON.parse(atob(parts[1]))
      console.log('Payload:', payload)
      console.log('过期时间 (exp):', new Date(payload.exp * 1000))
      console.log('当前时间:', new Date())
      console.log('是否过期:', Date.now() >= payload.exp * 1000)
    } else {
      console.error('Token 不是标准 JWT 格式，部分数:', parts.length)
    }
  } catch (e) {
    console.error('Token 解析失败:', e)
  }
}
```

### 原因 3: Token 过期时间设置过短

**检查后端配置** (`src/core/config.py`):

```python
# 查看这些配置
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 如果太短会导致频繁过期
REFRESH_TOKEN_EXPIRE_MINUTES = 10080  # 7天
```

### 原因 4: 刷新 Token 逻辑失败

**问题**：

- 前端 `refreshAccessToken()` 调用后端 `/auth/refresh` 接口
- 但后端可能没有返回有效的 refresh_token
- 或者 refresh_token 未保存到 localStorage/sessionStorage

**检查**：

```typescript
// 查看 src/stores/auth.ts:174
setAuth(response: LoginResponse, rememberMe: boolean = false): void {
  const { access_token, user, expires_in } = response

  // 问题: 这里没有保存 refresh_token！
  this.accessToken = access_token
  this.user = user

  // ...
  storage.setItem('access_token', access_token)
  // ⚠️ 缺失: storage.setItem('refresh_token', refresh_token)
}
```

### 原因 5: 页面刷新后状态丢失

**问题**：

- 用户刷新页面
- `main.ts` 中的 `restoreAuth()` 尝试恢复状态
- 但可能因为各种原因失败

**检查 `main.ts` 初始化**：

```typescript
setTimeout(() => {
  const authStore = useAuthStore()
  if (authStore.restoreAuth()) {
    console.log('✅ 认证状态已恢复')
  } else {
    console.log('ℹ️ 未找到有效的认证状态') // ← 这里可能有问题
  }
}, 100)
```

## 临时诊断方案

### 步骤 1: 添加详细日志

修改 `frontend/src/stores/auth.ts` 添加调试日志：

```typescript
async validateAuth(): Promise<boolean> {
  console.log('🔍 validateAuth 开始检查...');
  console.log('isAuthenticated:', this.isAuthenticated);
  console.log('accessToken:', this.accessToken ? '存在' : '不存在');
  console.log('user:', this.user ? JSON.stringify(this.user) : '不存在');

  if (!this.isAuthenticated || !this.accessToken) {
    console.error('❌ 未登录或无 token');
    return false;
  }

  // 如果token过期，尝试刷新
  const isExpired = this.isTokenExpired();
  console.log('Token 是否过期:', isExpired);

  if (isExpired) {
    console.log('🔄 尝试刷新 token...');
    const refreshed = await this.refreshAccessToken();
    console.log('刷新结果:', refreshed);
    return refreshed;
  }

  // 验证用户信息是否完整
  if (!this.user) {
    console.log('📥 获取用户信息...');
    await this.fetchUserInfo();
  }

  console.log('✅ validateAuth 检查通过');
  return this.isAuthenticated;
}
```

### 步骤 2: 检查登录响应

修改 `frontend/src/stores/auth.ts` 的 `login` 方法：

```typescript
async login(loginData: LoginRequest): Promise<boolean> {
  this.loginLoading = true
  try {
    const response: LoginResponse = await AuthAPI.login(loginData)

    console.log('登录响应:', response);  // ← 添加日志
    console.log('access_token:', response.access_token);
    console.log('user:', response.user);
    console.log('expires_in:', response.expires_in);
    console.log('refresh_token:', response.refresh_token);  // ← 检查是否存在

    // 保存认证信息
    this.setAuth(response, loginData.remember_me)

    // 获取用户详细信息
    await this.fetchUserInfo()

    ElMessage.success('登录成功！')
    return true
  } catch (error) {
    console.error('Login failed:', error)
    return false
  } finally {
    this.loginLoading = false
  }
}
```

## 修复方案

### 修复 1: 保存 refresh_token

修改 `frontend/src/stores/auth.ts` 的 `setAuth` 方法：

```typescript
setAuth(response: LoginResponse, rememberMe: boolean = false): void {
  const { access_token, refresh_token, user, expires_in } = response

  // 更新状态
  this.accessToken = access_token
  this.refreshToken = refresh_token  // ← 添加这行
  this.user = user
  this.isAuthenticated = true
  this.rememberMe = rememberMe

  // 选择存储方式
  const storage = rememberMe ? localStorage : sessionStorage

  // 保存到本地存储
  storage.setItem('access_token', access_token)

  // ← 添加这行：保存 refresh_token
  if (refresh_token) {
    storage.setItem('refresh_token', refresh_token)
  }

  storage.setItem('user_info', JSON.stringify(user))
  storage.setItem('remember_me', rememberMe.toString())

  // 保存过期时间
  if (expires_in) {
    const expiryTime = Date.now() + expires_in * 1000
    storage.setItem('token_expiry', expiryTime.toString())
  }
}
```

### 修复 2: 恢复 refresh_token

修改 `frontend/src/stores/auth.ts` 的 `restoreAuth` 方法：

```typescript
restoreAuth(): boolean {
  try {
    // 优先从localStorage读取
    let token = localStorage.getItem('access_token')
    let refreshToken = localStorage.getItem('refresh_token')  // ← 添加
    let userInfo = localStorage.getItem('user_info')
    let rememberMe = localStorage.getItem('remember_me') === 'true'

    // 如果localStorage没有，从sessionStorage读取
    if (!token) {
      token = sessionStorage.getItem('access_token')
      refreshToken = sessionStorage.getItem('refresh_token')  // ← 添加
      userInfo = sessionStorage.getItem('user_info')
      rememberMe = sessionStorage.getItem('remember_me') === 'true'
    }

    if (token && userInfo) {
      // 检查token是否过期
      if (this.isTokenExpired(token)) {
        console.warn('Token 已过期，清除认证状态');
        this.clearAuth()
        return false
      }

      // 恢复状态
      this.accessToken = token
      this.refreshToken = refreshToken  // ← 添加
      this.user = JSON.parse(userInfo)
      this.isAuthenticated = true
      this.rememberMe = rememberMe

      console.log('✅ 认证状态已恢复，token:', token.substring(0, 20) + '...');
      return true
    }
  } catch (error) {
    console.error('Failed to restore auth state:', error)
    this.clearAuth()
  }

  return false
}
```

### 修复 3: 优化路由守卫

修改 `frontend/src/router/index.ts`，添加更详细的日志：

```typescript
// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  console.log(`🔀 路由跳转: ${from.path} → ${to.path}`)

  // 开始加载进度条
  NProgress.start()

  // 设置页面标题
  const title = to.meta?.title
  if (title) {
    document.title = `${title} - 五好伴学`
  }

  // 获取认证状态
  const authStore = useAuthStore()
  console.log('认证状态:', {
    isAuthenticated: authStore.isAuthenticated,
    hasToken: !!authStore.accessToken,
    hasUser: !!authStore.user,
  })

  // 检查路由是否需要认证
  const requiresAuth = to.meta?.requiresAuth
  console.log('路由需要认证:', requiresAuth)

  // 如果明确设置为需要认证
  if (requiresAuth === true) {
    // 需要认证的页面
    if (!authStore.isAuthenticated) {
      console.warn('❌ 未登录，重定向到登录页')
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }

    // 验证token有效性
    console.log('🔍 验证 token 有效性...')
    const isValid = await authStore.validateAuth()
    console.log('Token 验证结果:', isValid)

    if (!isValid) {
      console.error('❌ Token 验证失败，重定向到登录页')
      ElMessage.error('登录已过期，请重新登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }

    console.log('✅ Token 验证通过，继续导航')
  }

  // ... 其他逻辑

  next()
})
```

## 验证步骤

1. **启动开发服务器** (如果未启动):

   ```bash
   cd frontend
   npm run dev
   ```

2. **打开浏览器控制台**:
   - 打开 http://localhost:5173
   - 按 F12 打开开发者工具
   - 切换到 Console 标签

3. **登录并观察日志**:
   - 输入用户名和密码登录
   - 观察控制台输出的日志
   - 特别注意 `access_token`、`refresh_token`、`user` 等信息

4. **测试路由跳转**:
   - 登录成功后，从仪表盘点击"学习问答"
   - 观察控制台日志：
     - 是否输出 `🔀 路由跳转: /dashboard → /learning`
     - 是否输出 `🔍 validateAuth 开始检查...`
     - Token 验证结果是什么

5. **检查 Storage**:
   - 打开 Application 标签
   - 查看 Local Storage 或 Session Storage
   - 确认 `access_token`、`refresh_token`、`user_info` 都已保存

6. **手动测试 Token 解析**:
   ```javascript
   // 在控制台执行
   const token = localStorage.getItem('access_token')
   const parts = token.split('.')
   const payload = JSON.parse(atob(parts[1]))
   console.log(payload)
   console.log('过期时间:', new Date(payload.exp * 1000))
   console.log('是否过期:', Date.now() >= payload.exp * 1000)
   ```

## 预期结果

修复后，应该看到：

1. ✅ 登录后 `access_token` 和 `refresh_token` 都保存到 storage
2. ✅ 页面跳转时 `validateAuth()` 返回 `true`
3. ✅ 不会重定向到登录页
4. ✅ 控制台输出 `✅ Token 验证通过，继续导航`

## 如果问题仍然存在

### 检查后端

1. 后端是否正确返回 `refresh_token`？

   ```bash
   # 查看登录 API 响应
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test","password":"test"}'
   ```

2. Token 过期时间是否合理？

   ```bash
   # 检查配置
   grep -E "ACCESS_TOKEN_EXPIRE|REFRESH_TOKEN_EXPIRE" src/core/config.py
   ```

3. Refresh Token API 是否工作？
   ```bash
   # 测试刷新 token
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"your_refresh_token"}'
   ```

## 总结

最可能的原因是 **refresh_token 未被保存和恢复**，导致 token 过期后无法自动刷新，从而要求用户重新登录。

按照上述修复方案添加 refresh_token 的保存和恢复逻辑即可解决问题。
