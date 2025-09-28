<template>
  <div 
    class="message-item mb-6 flex"
    :class="{ 
      'justify-end': message.type === 'user',
      'justify-start': message.type === 'ai',
      'opacity-50': message.is_processing 
    }"
  >
    <!-- AI头像 -->
    <div
      v-if="message.type === 'ai'"
      class="avatar flex-shrink-0 mr-3"
    >
      <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <el-icon class="text-white text-sm">
          <ChatDotSquare />
        </el-icon>
      </div>
    </div>

    <!-- 消息内容 -->
    <div
      class="message-content max-w-4xl"
      :class="{
        'bg-blue-500 text-white': message.type === 'user',
        'bg-white border border-gray-200': message.type === 'ai'
      }"
    >
      <!-- 消息头部信息 -->
      <div
        v-if="showMessageInfo"
        class="message-header px-4 py-2 border-b border-gray-100 text-xs text-gray-500 flex items-center justify-between"
      >
        <div class="flex items-center space-x-3">
          <span>{{ formatTime(message.timestamp) }}</span>
          
          <!-- 问题类型标签 -->
          <el-tag
            v-if="message.question_type && message.type === 'user'"
            size="small"
            type="info"
          >
            {{ getQuestionTypeLabel(message.question_type) }}
          </el-tag>
          
          <!-- 学科标签 -->
          <el-tag
            v-if="message.subject"
            size="small"
            :color="getSubjectColor(message.subject)"
          >
            {{ getSubjectLabel(message.subject) }}
          </el-tag>
        </div>

        <!-- 处理状态 -->
        <div v-if="message.is_processing" class="flex items-center text-blue-500">
          <el-icon class="animate-spin mr-1"><Loading /></el-icon>
          <span>处理中...</span>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="message.error" class="flex items-center text-red-500">
          <el-icon class="mr-1"><Warning /></el-icon>
          <span>{{ message.error }}</span>
        </div>
      </div>

      <!-- 消息主体内容 -->
      <div class="message-body p-4">
        <!-- 图片内容 -->
        <div
          v-if="message.image_urls && message.image_urls.length > 0"
          class="message-images mb-3"
        >
          <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
            <div
              v-for="(imageUrl, index) in message.image_urls"
              :key="index"
              class="relative group cursor-pointer"
              @click="previewImage(imageUrl, index)"
            >
              <img
                :src="imageUrl"
                :alt="`图片 ${index + 1}`"
                class="w-full h-24 object-cover rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
              />
              <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-lg transition-all flex items-center justify-center">
                <el-icon class="text-white opacity-0 group-hover:opacity-100 transition-opacity">
                  <ZoomIn />
                </el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- 文本内容 -->
        <div
          v-if="message.content"
          class="message-text"
          :class="{
            'text-white': message.type === 'user',
            'text-gray-800': message.type === 'ai'
          }"
        >
          <!-- 用户消息 -->
          <div v-if="message.type === 'user'" class="user-message">
            <pre class="whitespace-pre-wrap font-sans">{{ message.content }}</pre>
          </div>

          <!-- AI回答 */
          <div v-else class="ai-message">
            <!-- Markdown渲染 -->
            <div
              v-if="renderedContent"
              class="prose prose-sm max-w-none"
              v-html="renderedContent"
            />
            
            <!-- 纯文本fallback -->
            <pre
              v-else
              class="whitespace-pre-wrap font-sans leading-relaxed"
            >{{ message.content }}</pre>
          </div>
        </div>
      </div>

      <!-- 消息操作栏 -->
      <div
        v-if="!message.is_processing && message.type === 'ai'"
        class="message-actions px-4 py-2 border-t border-gray-100 flex items-center justify-between"
      >
        <div class="flex items-center space-x-2">
          <!-- 复制按钮 -->
          <el-button
            type="text"
            size="small"
            @click="handleCopy"
            class="text-gray-500 hover:text-blue-500"
          >
            <el-icon class="mr-1"><CopyDocument /></el-icon>
            复制
          </el-button>

          <!-- 重新生成按钮 -->
          <el-button
            type="text"
            size="small"
            @click="handleRegenerate"
            class="text-gray-500 hover:text-green-500"
          >
            <el-icon class="mr-1"><Refresh /></el-icon>
            重新生成
          </el-button>

          <!-- 反馈按钮 -->
          <el-button
            type="text"
            size="small"
            @click="showFeedback = true"
            class="text-gray-500 hover:text-orange-500"
          >
            <el-icon class="mr-1"><Star /></el-icon>
            评价
          </el-button>
        </div>

        <!-- 快速反馈 -->
        <div class="flex items-center space-x-1">
          <el-button
            type="text"
            size="small"
            @click="submitQuickFeedback(true)"
            :class="quickFeedback === true ? 'text-green-500' : 'text-gray-400 hover:text-green-500'"
          >
            <el-icon><Select /></el-icon>
          </el-button>
          <el-button
            type="text"
            size="small"
            @click="submitQuickFeedback(false)"
            :class="quickFeedback === false ? 'text-red-500' : 'text-gray-400 hover:text-red-500'"
          >
            <el-icon><CloseBold /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 用户头像 -->
    <div
      v-if="message.type === 'user'"
      class="avatar flex-shrink-0 ml-3"
    >
      <div class="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center">
        <el-icon class="text-white text-sm">
          <User />
        </el-icon>
      </div>
    </div>

    <!-- 反馈对话框 -->
    <el-dialog
      v-model="showFeedback"
      title="评价回答质量"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="feedbackForm" label-width="80px">
        <el-form-item label="评分">
          <el-rate
            v-model="feedbackForm.rating"
            :max="5"
            show-text
            :texts="['很差', '一般', '还行', '不错', '很好']"
          />
        </el-form-item>

        <el-form-item label="是否有帮助">
          <el-radio-group v-model="feedbackForm.is_helpful">
            <el-radio :label="true">有帮助</el-radio>
            <el-radio :label="false">没帮助</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="具体反馈">
          <el-input
            v-model="feedbackForm.feedback"
            type="textarea"
            :rows="3"
            placeholder="请描述具体的问题或建议（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="flex justify-end space-x-3">
          <el-button @click="showFeedback = false">取消</el-button>
          <el-button type="primary" @click="submitFeedback" :loading="isSubmittingFeedback">
            提交反馈
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="showImagePreview"
      :title="`图片预览 (${currentImageIndex + 1}/${message.image_urls?.length || 0})`"
      width="80%"
      align-center
      class="image-preview-dialog"
    >
      <div class="text-center">
        <img
          v-if="previewImageUrl"
          :src="previewImageUrl"
          :alt="'预览图片'"
          class="max-w-full max-h-96 object-contain rounded-lg"
        />
      </div>
      
      <template #footer>
        <div class="flex justify-center space-x-3">
          <el-button
            :disabled="currentImageIndex === 0"
            @click="switchPreviewImage(-1)"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一张
          </el-button>
          <el-button
            :disabled="currentImageIndex >= (message.image_urls?.length || 0) - 1"
            @click="switchPreviewImage(1)"
          >
            下一张
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  ChatDotSquare,
  User,
  Loading,
  Warning,
  ZoomIn,
  CopyDocument,
  Refresh,
  Star,
  Select,
  CloseBold,
  ArrowLeft,
  ArrowRight
} from '@element-plus/icons-vue'

// 类型导入
import type { ChatMessage, FeedbackRequest } from '@/types/learning'
import {
  QUESTION_TYPE_OPTIONS,
  SUBJECT_OPTIONS
} from '@/types/learning'

// ========== 接口定义 ==========

interface Props {
  message: ChatMessage
  showMessageInfo?: boolean
}

interface Emits {
  (e: 'feedback', feedback: FeedbackRequest): void
  (e: 'copy', content: string): void
  (e: 'regenerate', questionId: string): void
}

// ========== Props和Emits ==========

const props = withDefaults(defineProps<Props>(), {
  showMessageInfo: true
})

const emit = defineEmits<Emits>()

// ========== 响应式数据 ==========

const showFeedback = ref(false)
const showImagePreview = ref(false)
const previewImageUrl = ref('')
const currentImageIndex = ref(0)
const isSubmittingFeedback = ref(false)
const quickFeedback = ref<boolean | null>(null)
const renderedContent = ref('')

// 反馈表单数据
const feedbackForm = reactive({
  rating: 5,
  is_helpful: true,
  feedback: ''
})

// ========== 计算属性 ==========

const getQuestionTypeLabel = (type: string) => {
  const option = QUESTION_TYPE_OPTIONS.find(opt => opt.value === type)
  return option?.label || type
}

const getSubjectColor = (subject: string) => {
  const option = SUBJECT_OPTIONS.find(opt => opt.value === subject)
  return option?.color || '#6b7280'
}

const getSubjectLabel = (subject: string) => {
  const option = SUBJECT_OPTIONS.find(opt => opt.value === subject)
  return option?.label || subject
}

// ========== 工具函数 ==========

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
  
  if (diffInHours < 1) {
    const diffInMinutes = Math.floor(diffInHours * 60)
    return diffInMinutes <= 0 ? '刚刚' : `${diffInMinutes}分钟前`
  } else if (diffInHours < 24) {
    return `${Math.floor(diffInHours)}小时前`
  } else {
    return date.toLocaleDateString('zh-CN', { 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }
}

const renderMarkdown = async (content: string) => {
  try {
    // 简单的Markdown渲染，实际项目中可以使用marked或markdown-it
    let html = content
    
    // 代码块
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="bg-gray-100 p-3 rounded-lg overflow-x-auto"><code class="language-$1">$2</code></pre>')
    
    // 行内代码
    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>')
    
    // 粗体
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    
    // 斜体
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
    
    // 链接
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:underline" target="_blank">$1</a>')
    
    // 换行
    html = html.replace(/\n/g, '<br>')
    
    return html
  } catch (error) {
    console.error('渲染Markdown失败:', error)
    return ''
  }
}

// ========== 事件处理 ==========

const handleCopy = () => {
  emit('copy', props.message.content)
}

const handleRegenerate = () => {
  if (props.message.question_id) {
    emit('regenerate', props.message.question_id)
  }
}

const submitQuickFeedback = async (isHelpful: boolean) => {
  if (!props.message.question_id) return
  
  quickFeedback.value = isHelpful
  
  const feedback: FeedbackRequest = {
    question_id: props.message.question_id,
    rating: isHelpful ? 5 : 2,
    is_helpful: isHelpful,
    feedback: isHelpful ? '有帮助' : '没帮助'
  }
  
  emit('feedback', feedback)
}

const submitFeedback = async () => {
  if (!props.message.question_id) return
  
  isSubmittingFeedback.value = true
  try {
    const feedback: FeedbackRequest = {
      question_id: props.message.question_id,
      rating: feedbackForm.rating,
      is_helpful: feedbackForm.is_helpful,
      feedback: feedbackForm.feedback.trim() || undefined
    }
    
    emit('feedback', feedback)
    
    // 重置表单并关闭对话框
    Object.assign(feedbackForm, {
      rating: 5,
      is_helpful: true,
      feedback: ''
    })
    showFeedback.value = false
    
  } catch (error) {
    console.error('提交反馈失败:', error)
  } finally {
    isSubmittingFeedback.value = false
  }
}

const previewImage = (imageUrl: string, index: number) => {
  previewImageUrl.value = imageUrl
  currentImageIndex.value = index
  showImagePreview.value = true
}

const switchPreviewImage = (direction: number) => {
  const imageUrls = props.message.image_urls
  if (!imageUrls) return
  
  const newIndex = currentImageIndex.value + direction
  if (newIndex >= 0 && newIndex < imageUrls.length) {
    currentImageIndex.value = newIndex
    previewImageUrl.value = imageUrls[newIndex]
  }
}

// ========== 生命周期 ==========

onMounted(async () => {
  // 渲染AI消息的Markdown内容
  if (props.message.type === 'ai' && props.message.content) {
    renderedContent.value = await renderMarkdown(props.message.content)
  }
})
</script>

<style scoped lang="scss">
.message-item {
  .message-content {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: all 0.2s ease;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
  }

  .user-message {
    .message-content {
      border-radius: 12px 4px 12px 12px;
    }
  }

  .ai-message {
    .message-content {
      border-radius: 4px 12px 12px 12px;
    }
  }

  .message-actions {
    background: #f8f9fa;
    
    .el-button {
      &:hover {
        background: transparent;
      }
    }
  }

  .message-images {
    img {
      transition: all 0.2s ease;
      
      &:hover {
        transform: scale(1.02);
      }
    }
  }

  .prose {
    color: inherit;
    
    :deep(pre) {
      background-color: #f3f4f6;
      color: #374151;
    }
    
    :deep(code) {
      color: #e11d48;
      background-color: #fef2f2;
    }
    
    :deep(a) {
      color: #3b82f6;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
    
    :deep(strong) {
      font-weight: 600;
    }
    
    :deep(em) {
      font-style: italic;
    }
  }
}

.image-preview-dialog {
  :deep(.el-dialog__body) {
    padding: 20px;
  }
}

// 动画
.message-item {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>