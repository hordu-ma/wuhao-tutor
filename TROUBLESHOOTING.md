# 图片识别问题排查和解决方案

## 问题现象

AI 响应"虽然我目前无法直接查看图片内容"，无法分析上传的图片。

## 根本原因

用户登录后 token 未正确保存/使用，导致图片上传失败（401 Unauthorized）。

## 完整解决步骤

### 方案 1：清除缓存并重新登录（推荐）

1. **完全清除浏览器缓存**

   - Chrome/Edge: 访问 `chrome://settings/clearBrowserData`
   - 选择"全部时间"
   - 勾选：
     - ✅ Cookie 和其他网站数据
     - ✅ 缓存的图片和文件
   - 点击"清除数据"

2. **重新访问网站**

   ```
   https://121.199.173.244/learning
   ```

3. **重新登录并勾选"记住我"**

   - 确保勾选"记住我"选项
   - 登录成功后，在 Console 验证：
     ```javascript
     localStorage.getItem('access_token')
     ```
   - 应该返回一个长字符串（JWT token）

4. **上传图片测试**
   - 点击输入框旁的 📎 图标
   - 选择图片
   - 输入问题并发送
   - AI 应该能分析图片内容

### 方案 2：使用 sessionStorage（临时）

如果 localStorage 被阻止，token 会保存在 sessionStorage 中：

1. 登录后在 Console 检查：

   ```javascript
   sessionStorage.getItem('access_token')
   ```

2. 如果有值，说明登录成功，直接上传图片测试

### 方案 3：检查 Network 请求

1. 打开 DevTools Network 面板
2. 上传图片
3. 查找`upload-for-ai`请求
4. 检查状态码：
   - ✅ 200 OK → 上传成功
   - ❌ 401 Unauthorized → token 问题，重新登录
   - ❌ 500 Internal Server Error → 后端问题，查看 Response

## 验证修复

成功的标志：

1. Network 面板中`upload-for-ai`返回 200
2. Response 包含`ai_accessible_url`字段
3. AI 开始分析图片内容，不再说"无法查看"

## 已修复的后端问题

1. ✅ OSS 对象级 ACL 权限问题（commit 5878f02）
2. ✅ ChatMessage schema 缺少 image_urls 字段（commit cadc223）
3. ✅ 增强调试日志（commit 506b64d）

## 技术细节

### Token 存储位置

- **记住我**：localStorage.access_token
- **不记住**：sessionStorage.access_token

### 图片上传流程

```
1. Frontend: FileAPI.uploadImageForAI(file)
   ↓ Authorization: Bearer <token>
2. Backend: POST /api/v1/files/upload-for-ai
   ↓ 验证token → 上传OSS
3. Response: {ai_accessible_url: "https://..."}
   ↓
4. Frontend: 构建AskQuestionRequest{image_urls: [...]}
   ↓
5. Backend: POST /api/v1/learning/ask
   ↓ 检测到image_urls → 使用VL模型
6. AI: 分析图片并生成答案
```

### 调试命令

查看服务器日志：

```bash
ssh root@121.199.173.244 "journalctl -u wuhao-tutor -f | grep -E '🖼️|📤|图片|upload-for-ai'"
```

测试 token 有效性：

```bash
curl -k -H "Authorization: Bearer <YOUR_TOKEN>" \
  https://121.199.173.244/api/v1/auth/me
```

## 联系信息

如果问题仍未解决，请提供：

1. Network 面板中 upload-for-ai 请求的完整信息
2. Console 中 localStorage.getItem('access_token')的结果
3. 服务器日志中的相关错误信息
