<!-- MessageItem Component for Chat Messages -->
<template>
  <div
    class="message-item mb-6 flex"
    :class="{
      'justify-end': message.type === 'user',
      'justify-start': message.type === 'ai',
      'opacity-75': message.is_processing,
      'animate-pulse': message.is_processing,
    }"
  >
    <!-- AI头像 -->
    <div v-if="message.type === 'ai'" class="avatar flex-shrink-0 mr-3">
      <div
        class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-md"
      >
        <el-icon class="text-white">
          <ChatDotSquare />
        </el-icon>
      </div>
    </div>

    <!-- 消息内容 -->
    <div
      class="message-content max-w-4xl rounded-2xl shadow-sm transition-all hover:shadow-md"
      :class="{
        'bg-gradient-to-br from-blue-500 to-blue-600 text-white': message.type === 'user',
        'bg-white border border-gray-200': message.type === 'ai',
      }"
    >
      <!-- 消息头部信息 -->
      <div
        v-if="showMessageInfo || showTimestamp"
        class="message-header px-4 py-2.5 border-b border-gray-100 text-xs flex items-center justify-between"
        :class="message.type === 'user' ? 'text-blue-100' : 'text-gray-500'"
      >
        <div class="flex items-center space-x-3">
          <span v-if="showTimestamp || showMessageInfo" class="timestamp">
            {{ formatTime(message.timestamp) }}
          </span>

          <!-- 问题类型标签 -->
          <el-tag v-if="message.question_type && message.type === 'user'" size="small" type="info">
            {{ getQuestionTypeLabel(message.question_type) }}
          </el-tag>

          <!-- 学科标签 -->
          <el-tag v-if="message.subject" size="small" :color="getSubjectColor(message.subject)">
            {{ getSubjectLabel(message.subject) }}
          </el-tag>
        </div>

        <!-- 处理状态 -->
        <div v-if="message.is_processing" class="flex items-center text-blue-500 animate-pulse">
          <el-icon class="animate-spin mr-1"><Loading /></el-icon>
          <span>AI正在思考...</span>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="message.error" class="flex items-center text-red-500">
          <el-icon class="mr-1"><Warning /></el-icon>
          <span>{{ message.error }}</span>
          <el-button
            type="text"
            size="small"
            @click="$emit('retry', message.id)"
            class="ml-2 text-red-500 hover:text-red-600"
          >
            重试
          </el-button>
        </div>

        <!-- 发送状态 -->
        <div v-else-if="message.type === 'user'" class="flex items-center text-green-500">
          <el-icon class="mr-1"><Select /></el-icon>
          <span>已发送</span>
        </div>
      </div>

      <!-- 消息主体内容 -->
      <div class="message-body p-4">
        <!-- 图片内容 -->
        <div v-if="message.image_urls && message.image_urls.length > 0" class="message-images mb-3">
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
              <div
                class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-lg transition-all flex items-center justify-center"
              >
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
          class="message-text relative"
          :class="{
            'text-white': message.type === 'user',
            'text-gray-800': message.type === 'ai',
          }"
        >
          <!-- 用户消息 -->
          <div v-if="message.type === 'user'" class="user-message">
            <div class="whitespace-pre-wrap font-sans leading-relaxed">
              {{
                isCollapsed ? message.content.slice(0, maxCollapsedLength) + '...' : message.content
              }}
            </div>
            <!-- 展开/收起按钮 -->
            <div v-if="message.content.length > maxCollapsedLength" class="mt-2">
              <el-button
                type="text"
                size="small"
                class="text-blue-100 hover:text-white"
                @click="isCollapsed = !isCollapsed"
              >
                {{ isCollapsed ? '展开全部' : '收起' }}
                <el-icon class="ml-1">
                  <component :is="isCollapsed ? 'ArrowDown' : 'ArrowUp'" />
                </el-icon>
              </el-button>
            </div>
          </div>

          <!-- AI回答 -->
          <div v-else class="ai-message">
            <!-- 打字机效果 -->
            <div v-if="isTyping && !renderedContent" class="typing-animation">
              <span
                v-for="(char, index) in displayedContent"
                :key="index"
                :style="{ animationDelay: `${index * 30}ms` }"
                class="typed-char"
                >{{ char }}</span
              >
              <span v-if="showCursor" class="typing-cursor animate-pulse">|</span>
            </div>

            <!-- Markdown渲染 -->
            <div
              v-else-if="renderedContent"
              class="prose prose-sm max-w-none markdown-content"
              :class="{ 'line-clamp-content': isCollapsed }"
            >
              <div v-html="renderedContent" />

              <!-- 展开/收起按钮 -->
              <div v-if="isLongMessage" class="mt-3 text-center">
                <el-button
                  type="text"
                  size="small"
                  class="text-blue-500 hover:text-blue-600"
                  @click="isCollapsed = !isCollapsed"
                >
                  {{ isCollapsed ? '展开全部' : '收起' }}
                  <el-icon class="ml-1">
                    <component :is="isCollapsed ? 'ArrowDown' : 'ArrowUp'" />
                  </el-icon>
                </el-button>
              </div>
            </div>

            <!-- 纯文本fallback -->
            <pre v-else class="whitespace-pre-wrap font-sans leading-relaxed">{{
              isCollapsed ? message.content.slice(0, maxCollapsedLength) + '...' : message.content
            }}</pre>
          </div>
        </div>
      </div>

      <!-- 消息操作栏 -->
      <div
        v-if="!message.is_processing && message.type === 'ai' && !message.error"
        class="message-actions px-4 py-2 border-t border-gray-100 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
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
            :class="
              quickFeedback === true ? 'text-green-500' : 'text-gray-400 hover:text-green-500'
            "
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
    <div v-if="message.type === 'user'" class="avatar flex-shrink-0 ml-3">
      <div
        class="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center"
      >
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

    <!-- 图片预览组件 -->
    <ImagePreview
      v-model="showImagePreview"
      :images="previewImages"
      :initial-index="currentImageIndex"
      @change="handleImageChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import ImagePreview from './Chat/ImagePreview.vue'
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
} from '@element-plus/icons-vue'

// 类型导入
import type { ChatMessage, FeedbackRequest, LearningSubjectOption } from '@/types/learning'
import { QUESTION_TYPE_OPTIONS, LEARNING_SUBJECT_OPTIONS } from '@/types/learning'

// ========== 接口定义 ==========

interface Props {
  message: ChatMessage
  showMessageInfo?: boolean
  showTimestamp?: boolean
}

interface Emits {
  (e: 'feedback', feedback: FeedbackRequest): void
  (e: 'copy', content: string): void
  (e: 'regenerate', questionId: string): void
  (e: 'retry', messageId: string): void
}

// ========== Props和Emits ==========

const props = withDefaults(defineProps<Props>(), {
  showMessageInfo: true,
  showTimestamp: false,
})

const emit = defineEmits<Emits>()

// ========== 响应式数据 ==========

const showFeedback = ref(false)
const showImagePreview = ref(false)
const currentImageIndex = ref(0)
const isSubmittingFeedback = ref(false)
const quickFeedback = ref<boolean | null>(null)
const renderedContent = ref('')
const isTyping = ref(false)
const displayedContent = ref('')
const showCursor = ref(true)
const isCollapsed = ref(true) // 长消息默认折叠
const maxCollapsedLength = 300 // 折叠阈值（字符数）

// 反馈表单数据
const feedbackForm = reactive({
  rating: 5,
  is_helpful: true,
  feedback: '',
})

// ========== 计算属性 ==========

// 判断是否为长消息
const isLongMessage = computed(() => {
  return (props.message.content?.length || 0) > maxCollapsedLength
})

// 图片预览相关
const previewImages = computed(() => {
  return (props.message.image_urls || []).map((url) => ({
    url,
    alt: `图片 - ${props.message.content?.substring(0, 50) || '消息图片'}`,
  }))
})

const getQuestionTypeLabel = (type: string) => {
  const option = QUESTION_TYPE_OPTIONS.find((opt) => opt.value === type)
  return option?.label || type
}

const getSubjectColor = (subject: string) => {
  const option = LEARNING_SUBJECT_OPTIONS.find(
    (opt: LearningSubjectOption) => opt.value === subject
  )
  return option?.color || '#gray'
}

const getSubjectLabel = (subject: string) => {
  const option = LEARNING_SUBJECT_OPTIONS.find(
    (opt: LearningSubjectOption) => opt.value === subject
  )
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
      minute: '2-digit',
    })
  }
}

const renderMarkdown = (content: string): string => {
  if (!content) return ''

  try {
    console.log('原始内容:', content)
    let html = content

    // 1. 处理LaTeX数学公式（块级公式）
    html = html.replace(/\$\$\n?([\s\S]*?)\n?\$\$/g, (_match, formula) => {
      const cleanFormula = formula.trim()
      console.log('发现块级数学公式:', cleanFormula)
      return `<div class="math-block text-center my-4"><span class="math-formula bg-gray-50 border rounded-lg px-4 py-2 inline-block font-mono text-blue-800">${cleanFormula}</span></div>`
    })

    // 2. 处理LaTeX数学公式（行内公式）
    html = html.replace(/\$([^$\n]+)\$/g, (_match, formula) => {
      const cleanFormula = formula.trim()
      console.log('发现行内数学公式:', cleanFormula)
      return `<span class="math-inline bg-blue-50 border border-blue-200 rounded px-2 py-1 font-mono text-blue-800">${cleanFormula}</span>`
    })

    // 处理不带$$符号的数学公式（特殊情况处理）
    html = html.replace(/(y\s*=\s*ax\^?2?\s*\+\s*bx\s*\+\s*c)/gi, (match) => {
      console.log('发现未标记的数学公式:', match)
      return `<span class="math-inline bg-blue-50 border border-blue-200 rounded px-2 py-1 font-mono text-blue-800">${match}</span>`
    })

    // 3. 代码块（支持语法高亮）
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (_match, lang, code) => {
      const language = lang || 'plaintext'
      const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      return `<pre class="code-block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-3"><code class="language-${language}">${escapedCode}</code></pre>`
    })

    // 4. 行内代码
    html = html.replace(
      /`([^`]+)`/g,
      '<code class="inline-code bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>'
    )

    // 5. 标题
    html = html.replace(
      /^### (.*?)$/gm,
      '<h3 class="text-lg font-semibold mt-4 mb-2 text-gray-800">$1</h3>'
    )
    html = html.replace(
      /^## (.*?)$/gm,
      '<h2 class="text-xl font-bold mt-5 mb-3 text-gray-900">$1</h2>'
    )
    html = html.replace(
      /^# (.*?)$/gm,
      '<h1 class="text-2xl font-bold mt-6 mb-4 text-gray-900">$1</h1>'
    )

    // 6. 列表
    html = html.replace(/^\* (.*?)$/gm, '<li class="ml-4 mb-1">$1</li>')
    html = html.replace(/^- (.*?)$/gm, '<li class="ml-4 mb-1">$1</li>')
    html = html.replace(/^(\d+)\. (.*?)$/gm, '<li class="ml-4 mb-1">$2</li>')

    // 包装列表项
    html = html.replace(
      /(<li class="ml-4 mb-1">.*?<\/li>\n?)+/g,
      '<ul class="list-disc list-inside my-2 space-y-1">$&</ul>'
    )

    // 7. 引用块
    html = html.replace(
      /^> (.*?)$/gm,
      '<blockquote class="border-l-4 border-blue-500 pl-4 py-2 my-2 bg-blue-50 italic text-gray-700">$1</blockquote>'
    )

    // 8. 粗体
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong class='font-semibold'>$1</strong>")

    // 9. 斜体
    html = html.replace(/\*(.*?)\*/g, "<em class='italic'>$1</em>")

    // 10. 链接
    html = html.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">$1</a>'
    )

    // 11. 水平线
    html = html.replace(/^---$/gm, '<hr class="my-4 border-gray-300">')

    // 12. 换行
    html = html.replace(/\n\n/g, "</p><p class='my-2'>")
    html = html.replace(/\n/g, '<br>')

    // 包装段落
    html = `<p class='my-2'>${html}</p>`

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
    feedback: isHelpful ? '有帮助' : '没帮助',
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
      feedback: feedbackForm.feedback.trim() || undefined,
    }

    emit('feedback', feedback)

    // 重置表单并关闭对话框
    Object.assign(feedbackForm, {
      rating: 5,
      is_helpful: true,
      feedback: '',
    })
    showFeedback.value = false
  } catch (error) {
    console.error('提交反馈失败:', error)
  } finally {
    isSubmittingFeedback.value = false
  }
}

const previewImage = (_imageUrl: string, index: number) => {
  currentImageIndex.value = index
  showImagePreview.value = true
}

const handleImageChange = (index: number) => {
  currentImageIndex.value = index
}

// 打字机效果
const startTypingEffect = () => {
  if (props.message.type !== 'ai' || !props.message.content) return

  isTyping.value = true
  displayedContent.value = ''
  let index = 0
  const content = props.message.content

  const typeInterval = setInterval(() => {
    if (index < content.length) {
      displayedContent.value += content[index]
      index++
    } else {
      clearInterval(typeInterval)
      isTyping.value = false
      // 打字完成后渲染Markdown
      const html = renderMarkdown(content)
      renderedContent.value = html
    }
  }, 30)

  // 光标闪烁
  const cursorInterval = setInterval(() => {
    showCursor.value = !showCursor.value
  }, 500)

  // 清理
  setTimeout(
    () => {
      clearInterval(cursorInterval)
      showCursor.value = false
    },
    content.length * 30 + 1000
  )
}

// ========== 生命周期 ==========

onMounted(async () => {
  // 渲染AI消息的Markdown内容
  if (props.message.type === 'ai' && props.message.content) {
    // 如果是新消息，使用打字机效果
    if (
      props.message.timestamp &&
      new Date(props.message.timestamp).getTime() > Date.now() - 5000
    ) {
      startTypingEffect()
    } else {
      // 历史消息直接渲染
      renderedContent.value = renderMarkdown(props.message.content)
    }
  }
})
</script>

<style scoped lang="scss">
.message-item {
  .message-content {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: messageSlideIn 0.4s ease-out;

    &:hover {
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
      transform: translateY(-1px);
    }
  }

  .timestamp {
    font-weight: 500;
    padding: 2px 6px;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
  }

  .typing-animation {
    .typed-char {
      animation: fadeInChar 0.1s ease-out forwards;
      opacity: 0;
    }

    .typing-cursor {
      color: #3b82f6;
      font-weight: bold;
    }
  }

  .markdown-content {
    animation: fadeIn 0.3s ease-out;

    // 长消息折叠样式
    &.line-clamp-content {
      max-height: 300px;
      overflow: hidden;
      position: relative;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 80px;
        background: linear-gradient(transparent, white);
      }
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
    line-height: 1.7;

    :deep(pre) {
      background-color: #1e293b;
      color: #e2e8f0;
      border-radius: 0.5rem;
      padding: 1rem;
      margin: 0.75rem 0;
      overflow-x: auto;
    }

    :deep(code) {
      color: #e11d48;
      background-color: #fef2f2;
      padding: 0.125rem 0.375rem;
      border-radius: 0.25rem;
      font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
      font-size: 0.875em;
    }

    :deep(pre code) {
      color: inherit;
      background-color: transparent;
      padding: 0;
    }

    :deep(a) {
      color: #3b82f6;
      text-decoration: none;
      transition: color 0.2s;

      &:hover {
        color: #2563eb;
        text-decoration: underline;
      }
    }

    :deep(strong) {
      font-weight: 600;
      color: #1f2937;
    }

    :deep(em) {
      font-style: italic;
    }

    :deep(h1),
    :deep(h2),
    :deep(h3) {
      font-weight: 600;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      line-height: 1.3;
    }

    :deep(ul),
    :deep(ol) {
      margin: 0.5rem 0;
      padding-left: 1.5rem;
    }

    :deep(li) {
      margin: 0.25rem 0;
    }

    :deep(blockquote) {
      border-left: 4px solid #3b82f6;
      padding-left: 1rem;
      margin: 1rem 0;
      color: #6b7280;
      font-style: italic;
    }

    :deep(hr) {
      margin: 1.5rem 0;
      border: none;
      border-top: 1px solid #e5e7eb;
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
  animation: messageSlideIn 0.4s ease-out;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes fadeInChar {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
