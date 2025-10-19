# 图片上传超时问题诊断与修复

## 问题现象

从控制台错误日志可以看到：

```
uploadFile:fail timeout
(env: macOS,mp,1.06.2504038; lib: 2.32.3)
```

这是 **网络超时错误**，说明小程序无法在规定时间内完成图片上传。

## 根本原因

### 1. 超时时间设置问题

- **之前**：`wx.uploadFile` 没有设置 `timeout` 参数
- **默认超时**：可能只有 10-20 秒
- **图片上传**：需要更长时间，特别是大图片或慢网络

### 2. 网络连接问题

可能的原因：

- 后端服务器未启动
- URL 配置错误
- 防火墙阻止连接
- 微信开发者工具网络代理问题

## 已修复的内容

### ✅ 修复 1：增加超时时间

```javascript
wx.uploadFile({
  url: `${config.api.baseUrl}/api/v1/files/upload-for-ai`,
  filePath: filePath,
  name: 'file',
  timeout: 60000, // ✅ 设置 60 秒超时
  header: {
    Authorization: `Bearer ${token}`,
  },
  // ...
})
```

### ✅ 修复 2：添加上传进度监听

```javascript
uploadTask.onProgressUpdate((res) => {
  console.log('上传进度:', res.progress + '%')
  console.log('已上传:', res.totalBytesSent)
  console.log('总大小:', res.totalBytesExpectedToSend)
})
```

### ✅ 修复 3：详细的错误日志

```javascript
fail: (error) => {
  console.error('===== 上传失败 =====')
  console.error('错误类型:', error.errMsg)
  console.error('完整错误:', error)

  let errorMessage = '图片上传失败'
  if (error.errMsg.includes('timeout')) {
    errorMessage = '上传超时，请检查网络连接'
  } else if (error.errMsg.includes('fail')) {
    errorMessage = '网络连接失败，请重试'
  }

  reject(new Error(errorMessage))
}
```

## 诊断步骤

### 步骤 1：检查后端服务器

1. **确认后端服务器正在运行**

打开终端，执行：

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor
make restart-dev
# 或
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **检查服务器是否响应**

在浏览器中访问：

```
http://localhost:8000/docs
```

应该看到 FastAPI 的 Swagger 文档。

### 步骤 2：检查 URL 配置

1. **查看小程序配置**

打开文件：`miniprogram/config/index.js`

检查 `baseUrl` 配置：

```javascript
api: {
  baseUrl: 'https://121.199.173.244', // 生产环境
  // 或
  baseUrl: 'http://localhost:8000',   // 本地开发
}
```

2. **如果使用本地开发环境**

需要修改配置：

```javascript
api: {
  baseUrl: 'http://localhost:8000',
  // ...
}
```

然后在小程序开发者工具中：

- 点击右上角详情
- 勾选 "不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书"

### 步骤 3：测试网络连接

在微信开发者工具的控制台中执行：

```javascript
// 测试基础网络连接
wx.request({
  url: 'https://121.199.173.244/api/v1/health',
  success: (res) => console.log('服务器在线:', res),
  fail: (err) => console.error('服务器离线:', err),
})
```

### 步骤 4：检查文件大小

1. **查看选择的图片大小**

从控制台日志中可以看到文件大小。如果图片很大（>5MB），可能需要：

- 增加超时时间（已改为 60 秒）
- 压缩图片后再上传

2. **测试小图片**

先选择一张很小的图片（<100KB）测试上传是否成功。

## 测试验证

### 1. 清除缓存并重新编译

- 工具 → 清除缓存 → 清除全部缓存
- 重新编译小程序

### 2. 打开控制台并执行测试

**操作步骤**：

1. 进入作业问答页面
2. 点击 "+" 按钮
3. 选择"从相册选择"
4. 选择一张**小图片**（<1MB）
5. 点击发送按钮

**期望的控制台输出**：

```
===== 开始上传图片 =====
文件路径: wxfile://tmp_...
上传 URL: https://121.199.173.244/api/v1/files/upload-for-ai
Token: 已获取

上传进度: 10%
上传进度: 25%
上传进度: 50%
上传进度: 75%
上传进度: 100%

===== 上传成功响应 =====
HTTP 状态码: 200
响应数据: {"success":true,"data":{"ai_accessible_url":"https://..."}}
AI URL: https://121.199.173.244/...
===== 上传完成 =====
```

**如果仍然超时，会看到**：

```
===== 上传失败 =====
错误类型: uploadFile:fail timeout
完整错误: {...}
```

## 常见问题与解决方案

### 问题 1：连接被拒绝（Connection refused）

**症状**：

```
uploadFile:fail connect:fail
```

**原因**：后端服务器未启动或 URL 错误

**解决**：

1. 检查后端服务器是否运行：`ps aux | grep uvicorn`
2. 启动后端服务器：`make restart-dev`
3. 检查 URL 配置是否正确

### 问题 2：SSL 证书错误

**症状**：

```
uploadFile:fail ssl hand shake error
```

**原因**：HTTPS 证书问题

**解决**：

1. 如果是开发环境，改用 `http://` 而不是 `https://`
2. 在开发者工具中勾选"不校验合法域名"

### 问题 3：上传进度卡住

**症状**：

- 看到上传进度 0% → 10% → 然后卡住

**原因**：

- 网络不稳定
- 服务器处理缓慢
- 文件太大

**解决**：

1. 检查网络连接
2. 检查服务器日志（是否有错误）
3. 尝试上传更小的图片

### 问题 4：HTTP 401 未授权

**症状**：

```
HTTP 状态码: 401
响应数据: {"detail":"Not authenticated"}
```

**原因**：Token 无效或过期

**解决**：

1. 重新登录小程序
2. 检查 Token 是否正确获取
3. 检查后端 JWT 配置

### 问题 5：HTTP 413 文件过大

**症状**：

```
HTTP 状态码: 413
响应数据: {"detail":"Request Entity Too Large"}
```

**原因**：图片文件超过服务器限制（10MB）

**解决**：

1. 选择更小的图片
2. 实现图片压缩功能

## 临时解决方案

如果网络连接确实有问题，可以暂时使用以下方案：

### 方案 A：使用本地开发环境

```javascript
// miniprogram/config/index.js
api: {
  baseUrl: 'http://localhost:8000',  // 改为本地
  timeout: 60000,
}
```

### 方案 B：增加重试机制

```javascript
async uploadImageToAI(filePath, retryCount = 3) {
  for (let i = 0; i < retryCount; i++) {
    try {
      return await this._doUpload(filePath);
    } catch (error) {
      if (i === retryCount - 1) throw error;
      console.log(`上传失败，重试 ${i + 1}/${retryCount}...`);
      await new Promise(resolve => setTimeout(resolve, 2000)); // 等待 2 秒
    }
  }
}
```

### 方案 C：先压缩图片再上传

```javascript
// 使用 wx.compressImage 压缩图片
wx.compressImage({
  src: tempFilePath,
  quality: 50, // 压缩质量 0-100
  success: (res) => {
    const compressedPath = res.tempFilePath
    this.uploadImageToAI(compressedPath)
  },
})
```

## 验证清单

完成以下检查后再测试：

- [ ] 后端服务器已启动（访问 http://localhost:8000/docs 正常）
- [ ] `config/index.js` 中的 `baseUrl` 配置正确
- [ ] 微信开发者工具已勾选"不校验合法域名"
- [ ] 清除了缓存并重新编译
- [ ] 控制台已打开并清空
- [ ] 选择的是小图片（<1MB）用于测试

## 下一步

请按照以下顺序执行：

1. **检查后端服务器**

   ```bash
   cd /Users/liguoma/my-devs/python/wuhao-tutor
   make restart-dev
   ```

2. **访问后端健康检查**

   ```
   浏览器打开: http://localhost:8000/docs
   应该看到 Swagger 文档
   ```

3. **检查小程序配置**

   ```javascript
   // miniprogram/config/index.js
   // 确认 baseUrl 是否正确
   ```

4. **重新编译并测试**

   - 清除缓存
   - 重新编译
   - 选择小图片测试上传

5. **截图控制台日志**
   - 如果还有问题，截图完整的控制台日志
   - 包括 "开始上传" 到 "上传失败/成功" 的所有日志

---

**关键修复**：已将 `timeout` 从默认（约 10 秒）增加到 **60 秒**，并添加了详细的进度日志。

**请先检查后端服务器是否运行！** 🚀
