# 生产环境图片识别解决方案

## 🎯 问题分析

**核心问题**: 阿里云百炼 AI 要求图片 URL 必须是公网可直接访问的 HTTPS URL，当前的预览 URL 需要 JWT 认证。

**用户场景**: 用户拍照试题 → 上传图片 → AI 识别分析 → 返回解答

## ✅ 解决方案

### 方案 A: 阿里云 OSS 公开访问 (推荐)

#### 1. **技术架构**

```
用户拍照 → 上传API → OSS公开存储 → 生成公开URL → AI识别
```

#### 2. **核心特性**

- **公开访问**: 图片设置为 public-read，无需认证
- **安全控制**: 使用随机文件名，防止恶意访问
- **自动清理**: 定期清理过期的 AI 分析图片
- **双重保护**: 同时支持公开 URL 和签名 URL

#### 3. **实现步骤**

##### 步骤 1: 修改文件上传服务

在 `src/services/file_service.py` 中添加 AI 专用上传方法：

```python
async def upload_image_for_ai_analysis(
    self,
    user_id: str,
    file: UploadFile
) -> dict:
    """专门为AI分析上传图片，生成公开访问URL"""

    # 1. 验证和处理文件
    content = await file.read()
    self._validate_image_file(file, content)

    # 2. 生成OSS对象名（使用随机ID保证安全）
    file_ext = Path(file.filename).suffix if file.filename else '.jpg'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_id = uuid.uuid4().hex[:12]
    object_name = f"ai_analysis/{user_id[:8]}/{timestamp}_{random_id}{file_ext}"

    # 3. 上传到OSS并设置公开访问
    if self.oss_storage and self.oss_storage.is_available():
        # 上传时设置公开读取权限
        result = self.oss_storage.bucket.put_object(
            object_name,
            content,
            headers={'x-oss-object-acl': 'public-read'}
        )

        if result.status == 200:
            public_url = f"https://{self.oss_storage.bucket_name}.{self.oss_storage.endpoint}/{object_name}"

            return {
                "ai_accessible_url": public_url,  # AI服务使用
                "object_name": object_name,
                "file_size": len(content),
                "file_type": file.content_type
            }

    # 4. 降级到本地存储（开发环境）
    return await self._upload_to_local_for_ai(user_id, file, content)
```

##### 步骤 2: 修改学习服务

在 `src/services/learning_service.py` 中修改消息构建：

```python
def _build_conversation_messages(
    self,
    request: AskQuestionRequest,
    history: List[Tuple[str, str]] = None
) -> List[ChatMessage]:
    """构建对话消息，支持AI可访问的图片URL"""

    # 确保image_urls是AI可直接访问的公开URL
    ai_accessible_urls = []
    if request.image_urls:
        for url in request.image_urls:
            # 检查是否是内部API URL，如果是则转换为OSS公开URL
            if "/api/v1/files/" in url and "/preview" in url:
                # 从内部URL提取文件ID，然后获取对应的OSS公开URL
                file_id = self._extract_file_id_from_url(url)
                oss_url = await self._get_oss_public_url(file_id)
                if oss_url:
                    ai_accessible_urls.append(oss_url)
            else:
                # 已经是外部可访问URL
                ai_accessible_urls.append(url)

    # 构建用户消息
    user_message = ChatMessage(
        role=MessageRole.USER,
        content=request.content,
        image_urls=ai_accessible_urls  # 使用AI可访问的URL
    )

    return [user_message]
```

##### 步骤 3: 修改前端上传流程

在 `frontend/src/views/Learning.vue` 中：

```typescript
const handleSend = async () => {
  try {
    let aiAccessibleImageUrls: string[] = []

    // 上传图片并获取AI可访问的URL
    if (selectedImages.value.length > 0) {
      for (const imageFile of selectedImages.value) {
        const uploadResult = await FileAPI.uploadImageForAI(imageFile)
        aiAccessibleImageUrls.push(uploadResult.ai_accessible_url)
      }
    }

    // 发送问题（使用AI可访问的URL）
    const response = await LearningAPI.askQuestion({
      content: question.value,
      image_urls: aiAccessibleImageUrls, // AI可直接访问
      // ... 其他参数
    })

    // 处理响应...
  } catch (error) {
    // 错误处理...
  }
}
```

#### 4. **安全控制措施**

##### 文件名安全

```python
# 使用随机ID + 时间戳，防止文件名被猜测
object_name = f"ai_analysis/{user_hash}/{timestamp}_{random_id}{ext}"
```

##### 访问控制

```python
# OSS Bucket策略设置
{
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["oss:GetObject"],
      "Resource": ["acs:oss:*:*:bucket-name/ai_analysis/*"],
      "Condition": {
        "StringLike": {
          "oss:Referer": ["https://yourdomain.com/*", "https://dashscope.aliyuncs.com/*"]
        }
      }
    }
  ]
}
```

##### 定期清理

```python
# 定时任务：清理超过24小时的AI分析图片
async def cleanup_ai_analysis_images():
    """清理过期的AI分析图片"""
    cutoff_time = datetime.now() - timedelta(hours=24)

    # 删除OSS中过期的ai_analysis/目录下的文件
    for obj in oss_bucket.list_objects(prefix="ai_analysis/"):
        if obj.last_modified < cutoff_time:
            oss_bucket.delete_object(obj.key)
```

### 方案 B: 预签名 URL (备选方案)

如果不想设置公开访问，可以使用 OSS 预签名 URL：

```python
def generate_ai_accessible_url(self, object_name: str) -> str:
    """生成AI可访问的预签名URL（有效期4小时）"""
    return self.oss_storage.bucket.sign_url(
        'GET',
        object_name,
        4 * 3600,  # 4小时过期
        slash_safe=True
    )
```

## 🚀 部署建议

### 1. **开发环境配置**

```bash
# .env文件
OSS_BUCKET_NAME=wuhao-tutor-dev
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your_key_id
OSS_ACCESS_KEY_SECRET=your_key_secret
```

### 2. **生产环境配置**

```bash
# OSS Bucket设置
- 创建专门的ai_analysis目录
- 设置公开读取权限
- 配置CDN加速（可选）
- 设置生命周期规则（自动删除过期文件）
```

### 3. **监控和日志**

```python
# 添加监控指标
logger.info(f"AI图片上传: user={user_id}, size={file_size}, url={public_url}")

# 统计AI图片使用量
metrics.increment("ai_image_uploads", tags={"user_type": "student"})
```

## ✅ 预期效果

实施后的完整流程：

1. 用户拍照试题 📱
2. 前端上传到专用 AI 图片接口 ⬆️
3. 后端保存到 OSS 并设置公开访问 ☁️
4. 返回公开 URL 给前端 🔗
5. 前端调用学习问答 API，传入公开 URL 💭
6. 后端将公开 URL 传给阿里云百炼 AI ✨
7. AI 成功识别图片并回答问题 🎯
8. 定期清理过期的 AI 分析图片 🧹

**核心优势**：

- ✅ AI 可以直接访问图片，无需认证
- ✅ 安全性高，使用随机文件名
- ✅ 性能好，直接 OSS 访问
- ✅ 成本低，自动清理过期文件
- ✅ 用户体验好，拍照即可识别
