# 小程序图片上传功能修复方案

## 问题分析

通过对比 Web 前端（`frontend/src/views/Learning.vue`）的工作实现，发现小程序图片上传存在以下问题：

### 1. 使用了错误的上传端点

- **Web 前端**（✅ 正确）：`/files/upload-for-ai`
- **小程序之前**（❌ 错误）：`/files/upload-image-for-learning`

### 2. 响应格式不匹配

- **Web 前端解析**（✅ 正确）：
  ```typescript
  const aiUrl = result.data.ai_accessible_url // 完整公开 URL
  ```
- **小程序之前**（❌ 错误）：
  ```javascript
  const imageUrl = result.data.image_url // 相对路径，AI 无法访问
  ```

### 3. 上传流程不完整

- **Web 前端**（✅ 正确）：

  1. 用户选择多张图片（最多 5 张）
  2. 显示图片预览
  3. 点击发送时批量上传所有图片
  4. 上传成功后获取 AI 可访问的公开 URL 数组
  5. 将 `image_urls` 参数传递给 `/api/v1/learning/ask` 端点

- **小程序之前**（❌ 错误）：
  1. 选择单张图片
  2. 立即上传
  3. 立即发送 AI 请求
  4. 使用相对路径 URL（AI 无法访问）

## 修复方案

### 修改文件清单

1. **miniprogram/pages/learning/index/index.js**

   - 添加 `uploadedImages` 数据字段（数组，存储待上传图片）
   - 添加 `maxImageCount: 5`（与 Web 保持一致）
   - 修改 `chooseImage()` 方法：只选择图片，不立即上传
   - 新增 `removeImage(index)` 方法：移除已选图片
   - 新增 `uploadImageToAI(filePath)` 方法：上传单张图片到 `/files/upload-for-ai`
   - 新增 `uploadAllImages()` 方法：批量上传所有待发送的图片
   - 修改 `sendMessage()` 方法：
     - 先上传所有图片获取 AI 可访问的 URL
     - 将 `image_urls` 参数传递给 API
     - 在消息对象中保存图片信息用于显示

2. **miniprogram/pages/learning/index/index.wxml**

   - 添加图片预览区域（显示已选图片缩略图）
   - 添加图片删除按钮
   - 添加上传状态指示器
   - 修改发送按钮激活条件（有图片时也可发送）
   - 在消息显示中支持显示用户发送的图片

3. **miniprogram/pages/learning/index/index.wxss**
   - 添加图片预览区域样式（`.image-preview-area`）
   - 添加图片缩略图样式（`.preview-image`）
   - 添加删除按钮样式（`.remove-image-btn`）
   - 添加上传状态指示器样式（`.upload-status`）
   - 添加消息中图片显示样式（`.message-images`, `.message-image`）

### 核心代码变更

#### 1. 图片选择（只选择，不上传）

```javascript
chooseImage(sourceType) {
  if (this.data.uploadedImages.length >= this.data.maxImageCount) {
    wx.showToast({
      title: `最多只能上传${this.data.maxImageCount}张图片`,
      icon: 'none',
    });
    return;
  }

  wx.chooseMedia({
    count: this.data.maxImageCount - this.data.uploadedImages.length,
    mediaType: ['image'],
    sourceType: [sourceType],
    success: res => {
      this.setData({ showImageActions: false });

      const newImages = res.tempFiles.map(file => ({
        tempFilePath: file.tempFilePath,
        size: file.size,
        aiUrl: null, // 上传后填充
      }));

      this.setData({
        uploadedImages: [...this.data.uploadedImages, ...newImages],
      });
    },
  });
}
```

#### 2. 批量上传图片

```javascript
async uploadAllImages() {
  const imagesToUpload = this.data.uploadedImages.filter(img => !img.aiUrl);
  if (imagesToUpload.length === 0) return [];

  const uploadPromises = imagesToUpload.map(async (img, index) => {
    wx.showLoading({
      title: `上传图片 ${index + 1}/${imagesToUpload.length}`,
      mask: true,
    });

    const aiUrl = await this.uploadImageToAI(img.tempFilePath);

    // 更新图片列表中的 aiUrl
    const allImages = [...this.data.uploadedImages];
    const imgIndex = allImages.findIndex(
      item => item.tempFilePath === img.tempFilePath
    );
    if (imgIndex !== -1) {
      allImages[imgIndex].aiUrl = aiUrl;
    }
    this.setData({ uploadedImages: allImages });

    return aiUrl;
  });

  const aiUrls = await Promise.all(uploadPromises);
  wx.hideLoading();

  return aiUrls;
}
```

#### 3. 发送消息（先上传图片）

```javascript
async sendMessage() {
  // 1. 上传所有图片
  let imageUrls = [];
  if (this.data.uploadedImages.length > 0) {
    try {
      imageUrls = await this.uploadAllImages();
    } catch (uploadError) {
      wx.showToast({ title: '图片上传失败，请重试', icon: 'error' });
      return;
    }
  }

  // 2. 创建用户消息（包含图片引用）
  const userMessage = {
    id: this.generateMessageId(),
    content: inputText || '[图片]',
    type: 'text',
    sender: 'user',
    images: this.data.uploadedImages.map(img => ({
      tempFilePath: img.tempFilePath,
      aiUrl: img.aiUrl,
    })),
  };

  // 3. 清空输入和图片
  this.setData({
    inputText: '',
    uploadedImages: [], // 清空已上传的图片
  });

  // 4. 调用 API（包含 image_urls）
  const requestParams = {
    content: inputText || '请分析这张图片...',
    session_id: this.data.sessionId,
    use_context: true,
    include_history: true,
    max_history: 10,
  };

  if (imageUrls.length > 0) {
    requestParams.image_urls = imageUrls; // 关键参数
  }

  const response = await api.learning.askQuestion(requestParams);
  // ... 处理响应
}
```

## 修复效果

### ✅ 修复后的完整流程

1. 用户点击 "+" 按钮 → 显示图片选择菜单
2. 选择"拍照"或"从相册选择" → 选择图片（最多 5 张）
3. 图片显示在输入框上方的预览区域
4. 用户可以：
   - 继续添加更多图片（最多 5 张）
   - 删除已选图片（点击 × 按钮）
   - 输入文本描述
5. 点击发送按钮：
   - 显示上传进度提示（"上传图片 1/3"）
   - 批量上传所有图片到 `/files/upload-for-ai`
   - 获取 AI 可访问的公开 URL 数组
   - 将 `image_urls` 参数传递给 AI
6. AI 分析图片并返回回复（支持多模态理解）
7. 消息列表显示用户发送的图片缩略图

### 与 Web 前端的一致性

| 特性       | Web 前端               | 小程序（修复后）          |
| ---------- | ---------------------- | ------------------------- |
| 上传端点   | `/files/upload-for-ai` | ✅ `/files/upload-for-ai` |
| 响应字段   | `ai_accessible_url`    | ✅ `ai_accessible_url`    |
| 最大图片数 | 5 张                   | ✅ 5 张                   |
| 图片预览   | ✅ 支持                | ✅ 支持                   |
| 批量上传   | ✅ 支持                | ✅ 支持                   |
| API 参数   | `image_urls: [...]`    | ✅ `image_urls: [...]`    |

## 测试验证

### 测试场景

1. **单张图片上传**

   - 选择一张图片
   - 输入文字"请分析这张图片"
   - 点击发送
   - 验证：图片上传成功，AI 返回分析结果

2. **多张图片上传**

   - 选择 3 张图片
   - 不输入文字
   - 点击发送
   - 验证：所有图片上传成功，AI 返回综合分析

3. **图片 + 文字混合**

   - 选择 2 张图片
   - 输入"这两道题有什么区别？"
   - 点击发送
   - 验证：AI 理解图片内容并回答问题

4. **删除图片**

   - 选择 3 张图片
   - 删除中间一张
   - 验证：剩余 2 张图片正确上传

5. **达到上限**

   - 选择 5 张图片
   - 尝试再添加第 6 张
   - 验证：提示"最多只能上传 5 张图片"

6. **上传失败处理**
   - 断网状态下选择图片
   - 点击发送
   - 验证：显示"图片上传失败，请重试"，消息不发送

## 关键技术细节

### 1. 为什么必须使用 `/files/upload-for-ai` 端点？

**端点对比**：

| 端点                               | 返回 URL 格式                                                        | AI 可访问性           |
| ---------------------------------- | -------------------------------------------------------------------- | --------------------- |
| `/files/upload-for-ai`             | `https://121.199.173.244/api/v1/files/ai/{filename}` 或 OSS 公开 URL | ✅ 公开可访问         |
| `/files/upload-image-for-learning` | `/api/v1/files/{file_id}/preview`                                    | ❌ 相对路径，需要认证 |

**后端实现差异**：

```python
# /files/upload-for-ai (正确)
async def upload_image_for_ai(...):
    result = await ai_image_service.upload_for_ai_analysis(...)
    return {
        "ai_accessible_url": "https://...",  # 完整公开 URL
        "storage_type": "oss_public",
    }

# /files/upload-image-for-learning (错误)
async def upload_image_for_learning(...):
    uploaded_image = await file_service.upload_learning_image(...)
    return {
        "image_url": f"{base_url}/api/v1/files/{file_id}/preview",  # 相对路径
    }
```

### 2. 为什么 AI 无法访问相对路径 URL？

阿里云百炼 AI 服务（Bailian）在处理图片时：

1. 会直接请求 `image_urls` 中的 URL
2. 不会携带用户的认证 Token
3. 需要 **公开可访问** 的 HTTP/HTTPS URL

相对路径 URL（如 `/api/v1/files/{id}/preview`）：

- ❌ 缺少协议（http/https）
- ❌ 缺少域名
- ❌ 需要认证（`Authorization: Bearer ...`）

### 3. 图片上传的完整数据流

```
用户选择图片
    ↓
chooseImage() → 获取 tempFilePath（微信临时路径）
    ↓
uploadImageToAI(tempFilePath)
    ↓
wx.uploadFile() → 上传到后端 /files/upload-for-ai
    ↓
后端保存到 OSS/本地 → 返回 ai_accessible_url
    ↓
存储到 uploadedImages[].aiUrl
    ↓
sendMessage() → 提取所有 aiUrl 到 image_urls 数组
    ↓
api.learning.askQuestion({ image_urls: [...] })
    ↓
后端调用 Bailian AI（传递 image_urls）
    ↓
AI 直接访问公开 URL → 多模态分析
    ↓
返回文本 + 图片理解结果
```

## 未来优化方向

1. **图片压缩**

   - Web 前端已实现自动压缩（移动端强制压缩）
   - 小程序可使用 `wx.compressImage()` API

2. **上传进度显示**

   - 显示每张图片的上传进度百分比
   - 支持取消上传

3. **图片预览增强**

   - 支持点击预览大图
   - 支持拖拽排序

4. **错误重试**

   - 单张图片上传失败时，支持单独重试
   - 避免全部重新上传

5. **本地缓存**
   - 上传成功的图片 URL 缓存到本地
   - 避免重复上传相同图片

## 总结

本次修复完全对齐了 Web 前端的实现，确保小程序的图片上传功能与 Web 保持一致。核心改进：

1. ✅ 使用正确的上传端点（`/files/upload-for-ai`）
2. ✅ 解析正确的响应字段（`ai_accessible_url`）
3. ✅ 实现批量上传和图片预览
4. ✅ 传递正确的 API 参数（`image_urls`）
5. ✅ AI 可以正常访问图片并进行多模态分析

用户现在可以在小程序中：

- ✅ 上传多张图片（最多 5 张）
- ✅ 预览和删除图片
- ✅ 与 AI 进行多模态对话（图片 + 文字）
- ✅ 获得准确的图片分析结果
