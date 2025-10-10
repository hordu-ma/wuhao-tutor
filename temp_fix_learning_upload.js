/**
 * 临时修复：使用稳定的学习图片上传端点
 *
 * 这是一个临时解决方案，直到OSS配置问题解决
 *
 * 使用方法：
 * 1. 备份原文件：cp frontend/src/views/Learning.vue frontend/src/views/Learning.vue.backup
 * 2. 应用此修复：替换Learning.vue中的图片上传逻辑
 * 3. 重新构建前端：cd frontend && npm run build
 * 4. 部署到生产环境
 */

// 在 Learning.vue 中的 handleSend 方法，替换图片上传部分：

const handleSend = async () => {
  if (!inputText.value.trim()) return

  // 保存输入内容和图片，用于错误恢复
  const questionText = inputText.value.trim()
  const imagesToUpload = [...uploadedImages.value]

  console.log('🚀 [DEBUG] 开始发送问题:', {
    questionText,
    imageCount: imagesToUpload.length,
  })

  try {
    // 1. 首先上传图片（如果有的话）
    let imageUrls: string[] = []
    if (imagesToUpload.length > 0) {
      ElMessage.info(`正在上传${imagesToUpload.length}张图片...`)
      console.log('📤 [DEBUG] 开始上传图片...', imagesToUpload.length)

      try {
        // 临时修复：使用稳定的学习图片上传端点
        const uploadPromises = imagesToUpload.map((img) => FileAPI.uploadLearningImage(img.file))
        const uploadResults = await Promise.all(uploadPromises)
        imageUrls = uploadResults.map((result) => result.image_url)
        console.log('✅ [DEBUG] 图片上传成功:', imageUrls)
        ElMessage.success(`图片上传成功！`)
      } catch (uploadError) {
        console.error('❌ [DEBUG] 图片上传失败:', uploadError)
        ElMessage.error('图片上传失败，请重试')
        return
      }
    } else {
      console.log('ℹ️ [DEBUG] 无图片上传')
    }

    // 2. 构建问答请求
    const request: AskQuestionRequest = {
      content: questionText,
      question_type: QuestionType.GENERAL_INQUIRY,
      image_urls: imageUrls.length > 0 ? imageUrls : undefined,
      use_context: true,
      include_history: true,
      max_history: 10,
    }
    console.log('📝 [DEBUG] 构建请求:', request)

    // 3. 清空输入（在发送前清空，避免重复发送）
    inputText.value = ''
    uploadedImages.value = []

    // 4. 发送到学习服务
    await learningStore.askQuestion(request)
    console.log('✅ [DEBUG] 问题发送成功')
  } catch (error) {
    console.error('❌ [DEBUG] 发送失败:', error)

    // 发生错误时恢复输入内容
    inputText.value = questionText
    uploadedImages.value = imagesToUpload

    ElMessage.error('发送失败，请重试')
  }
}
