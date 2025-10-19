# 紧急修复：图片上传一直转圈问题

## 问题现象

用户报告：在小程序中点击添加图片后，页面一直显示 loading 转圈，无法完成上传。

## 根本原因

经过代码审查，发现了 **两个关键 Bug**：

### 1. ❌ baseUrl 未定义错误

**错误代码**：

```javascript
wx.uploadFile({
  url: `${api.baseUrl}/files/upload-for-ai`, // ❌ api.baseUrl 不存在！
  // ...
})
```

**问题分析**：

- `api` 是从 `miniprogram/api/index.js` 导出的 API 模块集合对象
- 该对象只包含 `user`、`homework`、`learning` 等 API 模块
- **没有** `baseUrl` 属性！
- 导致上传 URL 变成 `undefined/files/upload-for-ai`，请求失败

**正确用法**：

```javascript
const config = require('../../../config/index.js')

wx.uploadFile({
  url: `${config.api.baseUrl}/api/v1/files/upload-for-ai`, // ✅ 正确
  // ...
})
```

### 2. ⚠️ Promise.all 并发上传导致 loading 混乱

**错误代码**：

```javascript
const uploadPromises = imagesToUpload.map(async (img, index) => {
  wx.showLoading({
    title: `上传图片 ${index + 1}/${imagesToUpload.length}`,
    mask: true,
  })
  // 并发执行时，多个 showLoading 相互覆盖
  const aiUrl = await this.uploadImageToAI(img.tempFilePath)
  return aiUrl
})

const aiUrls = await Promise.all(uploadPromises) // 并发上传
wx.hideLoading() // 只执行一次 hideLoading
```

**问题分析**：

- `Promise.all` 并发执行时，多个异步任务同时调用 `wx.showLoading()`
- 每次调用都会覆盖前一个 loading 提示
- 如果某个请求失败，其他请求的 loading 可能无法正确关闭
- 导致页面一直转圈

**改进方案**：

```javascript
// 顺序上传图片（避免并发问题）
const aiUrls = []
for (let i = 0; i < imagesToUpload.length; i++) {
  wx.showLoading({
    title: `上传图片 ${i + 1}/${imagesToUpload.length}`,
    mask: true,
  })

  const aiUrl = await this.uploadImageToAI(img.tempFilePath)
  aiUrls.push(aiUrl)
}

wx.hideLoading()
```

---

## 修复方案

### 修改文件：`miniprogram/pages/learning/index/index.js`

#### 1️⃣ 导入 config 模块

```javascript
// 在文件顶部添加
const config = require('../../../config/index.js')
```

#### 2️⃣ 修复 uploadImageToAI 方法

```javascript
async uploadImageToAI(filePath) {
  try {
    const token = await authManager.getToken();

    const uploadResult = await new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${config.api.baseUrl}/api/v1/files/upload-for-ai`, // ✅ 修复
        filePath: filePath,
        name: 'file',
        header: {
          Authorization: `Bearer ${token}`,
        },
        success: res => {
          try {
            console.log('上传响应:', res);  // 添加调试日志
            const result = JSON.parse(res.data);
            if (result.success && result.data) {
              resolve(result.data.ai_accessible_url);
            } else {
              reject(new Error(result.message || '图片上传失败'));
            }
          } catch (error) {
            console.error('响应解析失败:', res.data);
            reject(new Error('响应解析失败'));
          }
        },
        fail: error => {
          console.error('上传请求失败:', error);
          reject(error);
        },
      });
    });

    return uploadResult;
  } catch (error) {
    console.error('图片上传失败:', error);
    throw error;
  }
}
```

#### 3️⃣ 优化 uploadAllImages 方法

```javascript
async uploadAllImages() {
  const imagesToUpload = this.data.uploadedImages.filter(img => !img.aiUrl);
  if (imagesToUpload.length === 0) {
    return [];
  }

  console.log(`开始上传 ${imagesToUpload.length} 张图片...`);

  // 显示初始上传进度
  wx.showLoading({
    title: `上传图片 0/${imagesToUpload.length}`,
    mask: true,
  });

  this.setData({ uploadingCount: imagesToUpload.length });

  try {
    const aiUrls = [];

    // ✅ 改为顺序上传（避免并发问题）
    for (let i = 0; i < imagesToUpload.length; i++) {
      const img = imagesToUpload[i];

      // 更新上传进度
      wx.showLoading({
        title: `上传图片 ${i + 1}/${imagesToUpload.length}`,
        mask: true,
      });

      try {
        const aiUrl = await this.uploadImageToAI(img.tempFilePath);

        // 更新图片列表中的 aiUrl
        const allImages = [...this.data.uploadedImages];
        const imgIndex = allImages.findIndex(item => item.tempFilePath === img.tempFilePath);
        if (imgIndex !== -1) {
          allImages[imgIndex].aiUrl = aiUrl;
        }

        this.setData({ uploadedImages: allImages });

        aiUrls.push(aiUrl);
      } catch (error) {
        console.error(`图片 ${i + 1} 上传失败:`, error);
        throw error;
      }
    }

    wx.hideLoading();
    this.setData({ uploadingCount: 0 });

    console.log('所有图片上传成功:', aiUrls);
    return aiUrls;
  } catch (error) {
    wx.hideLoading();
    this.setData({ uploadingCount: 0 });

    wx.showToast({
      title: '图片上传失败',
      icon: 'error',
      duration: 2000,
    });

    throw error;
  }
}
```

---

## 修复效果

### ✅ 修复前后对比

| 问题         | 修复前                          | 修复后                                               |
| ------------ | ------------------------------- | ---------------------------------------------------- |
| 上传 URL     | `undefined/files/upload-for-ai` | `https://121.199.173.244/api/v1/files/upload-for-ai` |
| 上传方式     | 并发上传（Promise.all）         | 顺序上传（for 循环）                                 |
| Loading 显示 | 混乱覆盖，可能无法关闭          | 清晰的进度提示                                       |
| 错误处理     | 部分 loading 无法关闭           | 统一的错误处理和 loading 关闭                        |
| 调试日志     | 缺少关键日志                    | 添加详细日志                                         |

### ✅ 预期行为

1. **单张图片上传**：

   - 选择图片 → 显示预览
   - 点击发送 → 显示 "上传图片 1/1"
   - 上传成功 → Loading 关闭 → 发送 AI 请求

2. **多张图片上传**：

   - 选择 3 张图片 → 显示预览
   - 点击发送 → 依次显示 "上传图片 1/3"、"上传图片 2/3"、"上传图片 3/3"
   - 全部上传成功 → Loading 关闭 → 发送 AI 请求

3. **上传失败**：
   - 上传过程中如果失败 → Loading 关闭 → 显示错误提示 "图片上传失败"
   - 消息不发送，用户可以重试

---

## 测试验证

### 测试步骤

1. **清除缓存**：

   - 在微信开发者工具中，点击 "清除缓存" → "清除全部缓存"
   - 重新编译小程序

2. **单张图片测试**：

   - 打开作业问答页面
   - 点击 "+" → 选择 "从相册选择"
   - 选择一张图片
   - 点击发送按钮
   - **预期**：显示 "上传图片 1/1" → 上传成功 → AI 返回分析结果

3. **多张图片测试**：

   - 选择 3 张图片
   - 点击发送按钮
   - **预期**：依次显示上传进度 → 所有图片上传成功 → AI 返回综合分析

4. **网络异常测试**：
   - 在开发者工具中，勾选 "模拟网络离线"
   - 选择图片并点击发送
   - **预期**：显示 "图片上传失败" → 消息不发送

### 查看日志

在微信开发者工具的 Console 中，应该能看到：

```
已选择图片: 1
开始上传 1 张图片...
上传响应: {statusCode: 200, data: "...", ...}
所有图片上传成功: ["https://121.199.173.244/api/v1/files/ai/..."]
发送请求参数: {content: "...", image_urls: [...], ...}
```

---

## 根本原因总结

1. **API 设计理解错误**：

   - 误以为 `api` 对象包含 `baseUrl` 属性
   - 实际上 `api` 只是 API 模块的集合
   - 应该从 `config` 模块获取 `baseUrl`

2. **异步并发控制不当**：

   - `Promise.all` 并发上传在微信小程序环境中可能导致 UI 状态混乱
   - 顺序上传虽然稍慢，但更稳定可靠

3. **调试日志不足**：
   - 缺少关键节点的日志输出
   - 导致问题排查困难

---

## 预防措施

1. **代码审查检查清单**：

   - [ ] 所有外部 URL 拼接都使用 `config.api.baseUrl`
   - [ ] 异步操作有明确的错误处理
   - [ ] Loading 状态有明确的开启和关闭
   - [ ] 关键节点添加 console.log 调试日志

2. **测试验证**：

   - [ ] 单张图片上传
   - [ ] 多张图片上传
   - [ ] 网络异常情况
   - [ ] 上传超时情况

3. **文档更新**：
   - [ ] 更新开发文档，明确 `config.api.baseUrl` 的使用
   - [ ] 添加常见错误排查指南

---

## 修复时间

- **问题发现**：2025-10-19
- **修复完成**：2025-10-19
- **影响范围**：小程序图片上传功能
- **修复类型**：紧急 Bug 修复

---

## 相关文档

- [图片上传功能修复方案](./image-upload-fix.md) - 完整的功能设计文档
- [API 配置说明](../../miniprogram/config/index.js) - 配置文件说明

---

**修复人员**：GitHub Copilot  
**审核状态**：待用户测试验证
