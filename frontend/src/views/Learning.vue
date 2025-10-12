<template>
  <div class="modern-learning-page">
    <!-- 主对话区域 -->
    <div class="chat-main-container">
      <!-- 顶部工具栏 -->
      <div class="top-toolbar">
        <div class="toolbar-left">
          <el-button
            circle
            :icon="showSidebar ? Close : Menu"
            @click="toggleSidebar"
            class="sidebar-toggle"
          />
          <h1 class="page-title">AI学习助手</h1>
        </div>
        <div class="toolbar-right">
          <el-button
            type="primary"
            :icon="Plus"
            @click="createNewSession"
            class="new-chat-button"
            size="large"
          >
            新建对话
          </el-button>
        </div>
      </div>

      <!-- 消息列表区域 -->
      <div ref="messageContainerRef" class="message-container" @scroll="handleScroll">
        <!-- 空状态 -->
        <div v-if="messages.length === 0 && !learningStore.chatState.isLoading" class="empty-state">
          <div class="empty-content">
            <div class="welcome-icon">
              <el-icon :size="64">
                <ChatDotRound />
              </el-icon>
            </div>
            <h2 class="welcome-title">你好！我是AI学习助手</h2>
            <p class="welcome-subtitle">我可以帮你解答学习问题、分析知识点、提供学习建议</p>

            <!-- 推荐问题卡片 -->
            <div class="suggested-questions">
              <button
                v-for="(question, index) in suggestedQuestions"
                :key="index"
                class="question-card"
                @click="handleQuickQuestion(question)"
              >
                <el-icon class="card-icon"><Promotion /></el-icon>
                <span class="card-text">{{ question }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="messages-list">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-wrapper"
            :class="{
              'user-message': message.type === 'user',
              'ai-message': message.type === 'ai',
            }"
          >
            <div class="message-content">
              <!-- 头像 -->
              <div class="avatar">
                <el-avatar :size="36" v-if="message.type === 'user'">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <el-avatar :size="36" class="ai-avatar" v-else>
                  <el-icon><ChatDotRound /></el-icon>
                </el-avatar>
              </div>

              <!-- 消息主体 -->
              <div class="message-body">
                <div class="message-header">
                  <span class="sender-name">{{ message.type === 'user' ? '你' : 'AI助手' }}</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="message-text" v-html="renderMarkdown(message.content)"></div>

                <!-- AI消息操作 -->
                <div v-if="message.type === 'ai' && !message.is_processing" class="message-actions">
                  <el-button text size="small" @click="copyMessage(message.content)">
                    <el-icon><CopyDocument /></el-icon> 复制
                  </el-button>
                  <el-button text size="small" @click="regenerateAnswer(message)">
                    <el-icon><Refresh /></el-icon> 重新生成
                  </el-button>
                </div>

                <!-- 处理中指示器 -->
                <div v-if="message.is_processing" class="processing-indicator">
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                </div>
              </div>
            </div>
          </div>

          <!-- AI思考中 -->
          <div v-if="learningStore.chatState.isTyping" class="message-wrapper ai-message">
            <div class="message-content">
              <div class="avatar">
                <el-avatar :size="36" class="ai-avatar">
                  <el-icon><ChatDotRound /></el-icon>
                </el-avatar>
              </div>
              <div class="message-body">
                <div class="message-header">
                  <span class="sender-name">AI助手</span>
                </div>
                <div class="thinking-indicator">
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                  <span class="thinking-text">正在思考...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 回到顶部按钮 -->
      <transition name="fade">
        <el-button
          v-show="showScrollToTop"
          circle
          size="large"
          class="scroll-to-top-button"
          @click="scrollToTop"
        >
          <el-icon :size="20"><Top /></el-icon>
        </el-button>
      </transition>

      <!-- 输入区域 -->
      <div class="input-container">
        <div class="input-wrapper">
          <!-- 图片预览 -->
          <div v-if="uploadedImages.length > 0" class="image-preview-row">
            <div v-for="(img, index) in uploadedImages" :key="index" class="image-preview-item">
              <img :src="img.preview" alt="上传图片" />
              <el-button
                circle
                :icon="Close"
                size="small"
                @click="removeImage(index)"
                class="remove-img-btn"
              />
            </div>
          </div>

          <!-- 输入框 -->
          <div class="input-box">
            <el-input
              v-model="inputText"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              placeholder="输入你的问题... (Shift + Enter 换行，Enter 发送)"
              :disabled="!canSend"
              @keydown="handleKeyDown"
              class="main-input"
            />

            <!-- 工具栏 -->
            <div class="input-toolbar">
              <div class="toolbar-left">
                <el-upload
                  :show-file-list="false"
                  :before-upload="handleImageUpload"
                  accept="image/*"
                  multiple
                  :limit="5"
                >
                  <el-button text :icon="Picture" :disabled="!canSend"> 图片 </el-button>
                </el-upload>
              </div>
              <div class="toolbar-right">
                <el-button
                  type="primary"
                  :icon="Promotion"
                  :loading="learningStore.isSubmittingQuestion"
                  :disabled="!canSend || !inputText.trim()"
                  @click="handleSend"
                  class="send-button"
                >
                  发送
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 会话历史侧边栏 (可折叠) -->
    <transition name="slide-left">
      <div v-show="showSidebar" class="sessions-sidebar">
        <div class="sidebar-header">
          <h3>会话历史</h3>
          <div class="header-actions">
            <el-button
              circle
              :icon="Plus"
              size="small"
              type="primary"
              @click="createNewSession"
              title="创建新会话"
            />
            <el-button circle :icon="Close" size="small" @click="toggleSidebar" />
          </div>
        </div>
        <div class="sidebar-content">
          <!-- 搜索框 -->
          <div class="search-box">
            <el-input
              v-model="sessionSearchQuery"
              placeholder="搜索会话..."
              :prefix-icon="Search"
              size="small"
              clearable
            />
          </div>

          <!-- 会话列表 -->
          <div class="session-list">
            <div v-if="filteredSessions.length === 0" class="empty-sessions">
              <p>暂无会话记录</p>
              <el-button type="primary" :icon="Plus" @click="createNewSession" size="small">
                创建第一个会话
              </el-button>
            </div>
            <div
              v-for="session in filteredSessions"
              :key="session.id"
              class="session-item"
              :class="{ active: session.id === currentSessionId }"
              @click="switchToSession(session.id)"
            >
              <div class="session-info">
                <div class="session-title">{{ session.title }}</div>
                <div class="session-meta">
                  {{ session.question_count }} 个问题 · {{ formatDate(session.updated_at) }}
                </div>
              </div>
              <div class="session-actions" @click.stop>
                <el-dropdown trigger="click">
                  <el-button circle size="small" :icon="MoreFilled" />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="renameSession(session)">
                        <el-icon><Edit /></el-icon> 重命名
                      </el-dropdown-item>
                      <el-dropdown-item @click="archiveSession(session.id)">
                        <el-icon><FolderOpened /></el-icon> 归档
                      </el-dropdown-item>
                      <el-dropdown-item @click="deleteSessionConfirm(session.id)" divided>
                        <el-icon><Delete /></el-icon> 删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  User,
  Promotion,
  Picture,
  Close,
  CopyDocument,
  Refresh,
  Menu,
  Plus,
  Search,
  MoreFilled,
  Edit,
  FolderOpened,
  Delete,
  Top,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { useLearningStore } from '@/stores/learning'
import type { AskQuestionRequest } from '@/types/learning'
import { QuestionType } from '@/types/learning'
import FileAPI from '@/api/file'

// ========== Store ==========
const learningStore = useLearningStore()

// ========== 响应式状态 ==========
const inputText = ref('')
const uploadedImages = ref<{ file: File; preview: string }[]>([])
const showSidebar = ref(false) // 默认不展开会话历史，用户可点击按钮打开
const messageContainerRef = ref<HTMLElement>()
const sessionSearchQuery = ref('')
const showScrollToTop = ref(false) // 控制"回到顶部"按钮显示

// 推荐问题
const suggestedQuestions = [
  '如何理解二次函数的图像和性质？',
  '英语过去完成时的用法是什么？',
  '请解释牛顿第二定律的应用',
  '如何快速记忆化学元素周期表？',
]

// ========== 计算属性 ==========
const messages = computed(() => learningStore.currentMessages)
const currentSessionId = computed(() => learningStore.chatState.currentSession?.id)

const canSend = computed(() => {
  return learningStore.canSendMessage && !learningStore.chatState.isLoading
})

// 过滤后的会话列表
const filteredSessions = computed(() => {
  const sessions = learningStore.activeSessions
  if (!sessionSearchQuery.value) {
    return sessions
  }
  return sessions.filter((session: any) =>
    session.title.toLowerCase().includes(sessionSearchQuery.value.toLowerCase())
  )
})

// ========== 方法 ==========
const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

const handleQuickQuestion = async (question: string) => {
  inputText.value = question
  await handleSend()
}

const handleKeyDown = (event: Event) => {
  const keyEvent = event as KeyboardEvent
  if (keyEvent.key === 'Enter' && !keyEvent.shiftKey) {
    event.preventDefault()
    if (canSend.value && inputText.value.trim()) {
      handleSend()
    }
  }
}

const handleImageUpload = (file: File) => {
  console.log('🖼️ [DEBUG] handleImageUpload 被调用:', {
    fileName: file.name,
    fileType: file.type,
    fileSize: file.size,
    currentImageCount: uploadedImages.value.length,
  })

  if (!file.type.startsWith('image/')) {
    console.error('❌ [DEBUG] 文件类型错误:', file.type)
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    console.error('❌ [DEBUG] 文件过大:', file.size)
    ElMessage.error('图片大小不能超过10MB')
    return false
  }
  if (uploadedImages.value.length >= 5) {
    console.error('❌ [DEBUG] 图片数量已达上限')
    ElMessage.error('最多只能上传5张图片')
    return false
  }

  console.log('✅ [DEBUG] 开始读取图片文件...')
  const reader = new FileReader()
  reader.onload = (e) => {
    const preview = e.target?.result as string
    console.log('✅ [DEBUG] 图片读取成功，添加到预览列表:', {
      previewLength: preview.length,
      currentCount: uploadedImages.value.length,
    })
    uploadedImages.value.push({
      file,
      preview,
    })
    console.log('✅ [DEBUG] 图片已添加，当前总数:', uploadedImages.value.length)
  }
  reader.onerror = (error) => {
    console.error('❌ [DEBUG] 图片读取失败:', error)
    ElMessage.error('图片读取失败')
  }
  reader.readAsDataURL(file)

  console.log('🔄 [DEBUG] FileReader.readAsDataURL 已调用，等待异步读取完成...')
  return false // 阻止自动上传
}

const removeImage = (index: number) => {
  uploadedImages.value.splice(index, 1)
}

const handleSend = async () => {
  console.log('🔥 [DEBUG] handleSend 被调用')
  console.log('📊 [DEBUG] 当前状态:', {
    inputText: inputText.value,
    uploadedImagesCount: uploadedImages.value.length,
    canSend: canSend.value,
    isLoading: learningStore.chatState.isLoading,
    isSubmitting: learningStore.isSubmittingQuestion,
  })

  if (!inputText.value.trim()) {
    console.warn('⚠️ [DEBUG] 输入为空，中止发送')
    return
  }

  // 保存输入内容和图片，用于错误恢复
  const questionText = inputText.value.trim()
  const imagesToUpload = [...uploadedImages.value]

  console.log('🚀 [DEBUG] 开始发送问题:', {
    questionText,
    imageCount: imagesToUpload.length,
    images: imagesToUpload.map((img) => ({
      fileName: img.file.name,
      fileSize: img.file.size,
      fileType: img.file.type,
      previewLength: img.preview.length,
    })),
  })

  try {
    // 1. 首先上传图片（如果有的话）
    let imageUrls: string[] = []
    if (imagesToUpload.length > 0) {
      console.log('📤 [DEBUG] 准备上传图片，数量:', imagesToUpload.length)
      console.log(
        '📤 [DEBUG] 图片详情:',
        imagesToUpload.map((img, idx) => ({
          index: idx,
          file: {
            name: img.file.name,
            size: img.file.size,
            type: img.file.type,
            lastModified: img.file.lastModified,
          },
        }))
      )

      ElMessage.info(`正在上传${imagesToUpload.length}张图片...`)

      try {
        console.log('📤 [DEBUG] 调用 FileAPI.uploadImageForAI...')
        // 使用新的AI图片上传端点
        const uploadPromises = imagesToUpload.map((img, idx) => {
          console.log(`📤 [DEBUG] 创建上传 Promise ${idx + 1}/${imagesToUpload.length}`)
          return FileAPI.uploadImageForAI(img.file)
        })
        console.log('📤 [DEBUG] 等待所有上传完成，Promise 数量:', uploadPromises.length)
        const uploadResults = await Promise.all(uploadPromises)
        console.log('✅ [DEBUG] 所有图片上传完成，结果:', uploadResults)
        imageUrls = uploadResults.map((result) => result.ai_accessible_url)
        console.log('✅ [DEBUG] 提取的图片 URL:', imageUrls)
        ElMessage.success(`图片上传成功！`)
      } catch (uploadError: any) {
        console.error('❌ [DEBUG] 图片上传失败')
        console.error('❌ [DEBUG] 错误详情:', uploadError)
        console.error('❌ [DEBUG] 错误信息:', uploadError?.message)
        console.error('❌ [DEBUG] 错误响应:', uploadError?.response)
        console.error('❌ [DEBUG] 完整错误栈:', uploadError?.stack)
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

    // 4. 发送问答请求
    await learningStore.askQuestion(request)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送失败:', error)
    // 恢复输入内容
    inputText.value = questionText
    uploadedImages.value = imagesToUpload
    ElMessage.error('发送失败，请重试')
  }
}

const switchToSession = async (sessionId: string) => {
  try {
    await learningStore.switchSession(sessionId)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('切换会话失败:', error)
  }
}

const createNewSession = async () => {
  try {
    await learningStore.createNewSession()
  } catch (error) {
    console.error('创建新会话失败:', error)
  }
}

const renameSession = async (session: any) => {
  try {
    const { value: newTitle } = await ElMessageBox.prompt('请输入新的会话标题：', '重命名会话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: session.title || '',
      inputPlaceholder: '请输入会话标题',
      inputValidator: (value: string) => {
        if (!value || value.trim().length === 0) {
          return '标题不能为空'
        }
        if (value.length > 100) {
          return '标题长度不能超过100个字符'
        }
        return true
      },
    })

    if (newTitle && newTitle.trim() !== session.title) {
      await learningStore.renameSession(session.id, newTitle.trim())
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重命名会话失败:', error)
    }
  }
}

const archiveSession = async (sessionId: string) => {
  try {
    await learningStore.archiveSession(sessionId)
    ElMessage.success('会话已归档')
  } catch (error) {
    console.error('归档会话失败:', error)
  }
}

const deleteSessionConfirm = async (sessionId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个会话吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await learningStore.deleteSession(sessionId)
    ElMessage.success('会话已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
    }
  }
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const regenerateAnswer = async (_message: any) => {
  ElMessage.info('重新生成功能开发中...')
}

// 配置 marked 支持 KaTeX 数学公式
const configureMarked = () => {
  marked.use({
    extensions: [
      // 行内公式 $...$
      {
        name: 'inlineMath',
        level: 'inline',
        start(src: string) {
          return src.indexOf('$')
        },
        tokenizer(src: string) {
          const match = src.match(/^\$+([^$\n]+?)\$+/)
          if (match) {
            return {
              type: 'inlineMath',
              raw: match[0],
              text: match[1].trim(),
            }
          }
        },
        renderer(token: any) {
          try {
            return katex.renderToString(token.text, { throwOnError: false })
          } catch (e) {
            console.error('KaTeX inline render error:', e)
            return token.text
          }
        },
      },
      // 块级公式 $$...$$
      {
        name: 'blockMath',
        level: 'block',
        start(src: string) {
          return src.indexOf('$$')
        },
        tokenizer(src: string) {
          const match = src.match(/^\$\$+\n?([\s\S]+?)\n?\$\$+/)
          if (match) {
            return {
              type: 'blockMath',
              raw: match[0],
              text: match[1].trim(),
            }
          }
        },
        renderer(token: any) {
          try {
            return `<div class="katex-block">${katex.renderToString(token.text, {
              throwOnError: false,
              displayMode: true,
            })}</div>`
          } catch (e) {
            console.error('KaTeX block render error:', e)
            return `<pre>${token.text}</pre>`
          }
        },
      },
    ],
  })
}

// 初始化 marked 配置
configureMarked()

const renderMarkdown = (content: string) => {
  return marked(content)
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDate = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

  if (diffInHours < 24) {
    return '今天'
  } else if (diffInHours < 48) {
    return '昨天'
  } else {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }
}

const scrollToBottom = () => {
  if (messageContainerRef.value) {
    messageContainerRef.value.scrollTop = messageContainerRef.value.scrollHeight
  }
}

const scrollToTop = () => {
  if (messageContainerRef.value) {
    messageContainerRef.value.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }
}

const handleScroll = () => {
  if (messageContainerRef.value) {
    showScrollToTop.value = messageContainerRef.value.scrollTop > 300
  }
  // 未来可扩展：滚动加载更多历史消息
}

// ========== 生命周期 ==========
onMounted(async () => {
  await learningStore.initialize()

  // 如果有最新会话，自动加载
  if (learningStore.latestActiveSession) {
    await learningStore.switchSession(learningStore.latestActiveSession.id)
  }
})

defineOptions({
  name: 'ModernLearningPage',
})
</script>

<style scoped lang="scss">
// 注意：variables 和 mixins 已通过 vite.config.ts 全局注入，无需再导入

// 淡入淡出动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.modern-learning-page {
  width: 100%;
  height: 100vh;
  display: flex;
  background: var(--color-bg-secondary, #f7f8fc);
  overflow: hidden;
}

// 主对话区域
.chat-main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

// 顶部工具栏
.top-toolbar {
  height: 64px;
  padding: 0 $spacing-xl;
  background: var(--color-bg-primary, #fff);
  border-bottom: 1px solid var(--color-border, #e5e7eb);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;

  .toolbar-left,
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: $spacing-base;
  }

  .toolbar-left {
    flex: 1;
  }

  .new-chat-button {
    padding: $spacing-md $spacing-2xl;
    border-radius: $border-radius-lg;
    font-weight: $font-weight-semibold;
    font-size: $font-size-base;
    box-shadow: $box-shadow-sm;
    transition: all $transition-duration-fast;

    &:hover {
      transform: translateY(-2px);
      box-shadow: $box-shadow-md;
    }
  }

  .page-title {
    font-size: $font-size-large;
    font-weight: $font-weight-semibold;
    color: var(--color-text-primary);
    margin: 0;
  }

  .sidebar-toggle {
    &:hover {
      background: var(--color-bg-secondary);
    }
  }
}

// 消息容器
.message-container {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-xl;

  @include scrollbar-style(6px, rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.15));
}

// 空状态
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;

  .empty-content {
    text-align: center;
    max-width: 600px;

    .welcome-icon {
      margin-bottom: $spacing-xl;
      color: $color-primary;
      animation: float 3s ease-in-out infinite;
    }

    .welcome-title {
      font-size: $font-size-extra-large;
      font-weight: $font-weight-bold;
      color: var(--color-text-primary);
      margin-bottom: $spacing-base;
    }

    .welcome-subtitle {
      font-size: $font-size-base;
      color: var(--color-text-secondary);
      margin-bottom: $spacing-2xl;
    }
  }
}

// 推荐问题卡片
.suggested-questions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: $spacing-md;
  margin-top: $spacing-xl;

  .question-card {
    background: $color-bg-white;
    padding: $spacing-lg;
    text-align: left;
    border: 1px solid var(--color-border);
    border-radius: $border-radius-md;
    cursor: pointer;
    transition: $transition-all;

    &:hover {
      transform: translateY(-2px);
      border-color: $color-primary;
      box-shadow: $box-shadow-md;
    }

    .card-icon {
      color: $color-primary;
      margin-bottom: $spacing-sm;
    }

    .card-text {
      font-size: $font-size-small;
      color: var(--color-text-primary);
      font-weight: $font-weight-medium;
    }
  }
}

// 消息列表
.messages-list {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.message-wrapper {
  margin-bottom: $spacing-xl;
  animation: fadeInUp 0.4s ease-out;

  &.user-message {
    .message-content {
      justify-content: flex-end;
    }
  }

  .message-content {
    display: flex;
    gap: $spacing-base;
    align-items: flex-start;
  }

  .avatar {
    flex-shrink: 0;

    .ai-avatar {
      background: $color-primary-light-8;
    }
  }

  .message-body {
    flex: 1;
    min-width: 0;

    .message-header {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      margin-bottom: $spacing-sm;

      .sender-name {
        font-size: $font-size-small;
        font-weight: $font-weight-semibold;
        color: var(--color-text-primary);
      }

      .message-time {
        font-size: $font-size-extra-small;
        color: var(--color-text-secondary);
      }
    }

    .message-text {
      background: var(--color-bg-primary);
      padding: $spacing-md;
      border-radius: $border-radius-lg;
      font-size: $font-size-base;
      line-height: $line-height-large;
      color: var(--color-text-primary);
      word-wrap: break-word;

      :deep(pre) {
        background: $color-bg-light;
        padding: $spacing-base;
        border-radius: $border-radius-base;
        overflow-x: auto;
      }

      :deep(code) {
        font-family: $font-family-mono;
        font-size: 0.9em;
      }

      // KaTeX 公式样式
      :deep(.katex) {
        font-size: 1.1em;
      }

      :deep(.katex-block) {
        margin: $spacing-md 0;
        padding: $spacing-md;
        background: var(--color-bg-secondary);
        border-radius: $border-radius-base;
        overflow-x: auto;
        text-align: center;

        .katex-display {
          margin: 0;
        }
      }

      // Markdown 标题样式
      :deep(h1),
      :deep(h2),
      :deep(h3),
      :deep(h4) {
        margin-top: $spacing-md;
        margin-bottom: $spacing-sm;
        font-weight: $font-weight-semibold;
      }

      :deep(h1) {
        font-size: 1.5em;
      }
      :deep(h2) {
        font-size: 1.3em;
      }
      :deep(h3) {
        font-size: 1.1em;
      }
      :deep(h4) {
        font-size: 1em;
      }

      // 列表样式
      :deep(ul),
      :deep(ol) {
        padding-left: $spacing-lg;
        margin: $spacing-sm 0;
      }

      :deep(li) {
        margin: $spacing-xs 0;
      }

      // 链接样式
      :deep(a) {
        color: $color-primary;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }

      // 引用块样式
      :deep(blockquote) {
        border-left: 4px solid $color-primary;
        padding-left: $spacing-md;
        margin: $spacing-md 0;
        color: var(--color-text-secondary);
        font-style: italic;
      }

      // 表格样式
      :deep(table) {
        width: 100%;
        border-collapse: collapse;
        margin: $spacing-md 0;

        th,
        td {
          border: 1px solid var(--color-border);
          padding: $spacing-sm;
          text-align: left;
        }

        th {
          background: var(--color-bg-secondary);
          font-weight: $font-weight-semibold;
        }
      }
    }

    .message-actions {
      display: flex;
      gap: $spacing-sm;
      margin-top: $spacing-sm;
    }
  }
}

// 思考指示器
.thinking-indicator,
.processing-indicator {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-base;

  .typing-dot {
    width: 8px;
    height: 8px;
    border-radius: $border-radius-circle;
    background: $color-primary;
    animation: typing 1.4s ease-in-out infinite;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }

  .thinking-text {
    font-size: $font-size-small;
    color: var(--color-text-secondary);
    margin-left: $spacing-sm;
  }
}

// 输入容器
.input-container {
  flex-shrink: 0;
  background: #ebeef5; // 加深背景色，更明显的区分
  border-top: 2px solid #d8dce5; // 加深边框颜色
  padding: $spacing-md $spacing-xl 0; // 移除底部 padding
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.08); // 增强阴影深度
  position: relative;

  // 顶部渐变遮罩，增强层次感
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(0, 0, 0, 0.1) 50%, transparent);
  }

  .input-wrapper {
    max-width: 900px;
    margin: 0 auto;
  }

  .image-preview-row {
    display: flex;
    gap: $spacing-base;
    margin-bottom: $spacing-base;

    .image-preview-item {
      position: relative;
      width: 80px;
      height: 80px;
      border-radius: $border-radius-base;
      overflow: hidden;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .remove-img-btn {
        position: absolute;
        top: -8px;
        right: -8px;
      }
    }
  }

  .input-box {
    background: #ffffff; // 纯白背景，与外层对比
    border-radius: $border-radius-lg;
    padding: $spacing-base;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); // 添加轻微阴影，增加浮起感
    border: 1px solid #e4e7ed; // 添加边框
    transition: all 0.3s ease; // 平滑过渡效果

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12); // hover时阴影加深
      border-color: #d0d4d9;
    }

    &:focus-within {
      box-shadow: 0 4px 16px rgba(64, 158, 255, 0.15); // 聚焦时蓝色阴影
      border-color: var(--el-color-primary);
    }

    .main-input {
      :deep(.el-textarea__inner) {
        background: transparent;
        border: none;
        box-shadow: none;
        resize: none;
        font-size: $font-size-base;
        line-height: $line-height-base;

        &:focus {
          box-shadow: none;
        }
      }
    }

    .input-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: $spacing-sm;
      padding-top: $spacing-sm;
      border-top: 1px solid var(--color-border);

      .send-button {
        padding: $spacing-sm $spacing-xl;
        border-radius: $border-radius-circle;
      }
    }
  }
}

// 侧边栏
.sessions-sidebar {
  width: 340px;
  background: var(--color-bg-primary);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: all $transition-duration-base;

  .sidebar-header {
    height: 64px;
    padding: 0 $spacing-lg;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--color-border);
    background: linear-gradient(to bottom, var(--color-bg-primary), var(--color-bg-secondary));

    h3 {
      font-size: $font-size-large;
      font-weight: $font-weight-bold;
      margin: 0;
      color: var(--color-text-primary);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
    }
  }

  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    padding: $spacing-base;

    @include scrollbar-style(6px, rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.15));
  }
}

.session-item {
  padding: $spacing-md $spacing-base;
  margin-bottom: $spacing-xs;
  border-radius: $border-radius-lg;
  cursor: pointer;
  transition: all $transition-duration-fast;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  border: 1px solid transparent;

  &:hover {
    background: var(--color-bg-secondary);
    border-color: var(--color-border);
    transform: translateX(-2px);
    box-shadow: $box-shadow-sm;

    .session-actions {
      opacity: 1;
    }
  }

  &.active {
    background: linear-gradient(to right, rgba($color-primary, 0.08), transparent);
    border-left: 3px solid $color-primary;
    box-shadow: $box-shadow-sm;

    .session-title {
      color: $color-primary;
      font-weight: $font-weight-semibold;
    }
  }

  .session-info {
    flex: 1;
    min-width: 0;
  }

  .session-title {
    font-size: $font-size-base;
    font-weight: $font-weight-medium;
    color: var(--color-text-primary);
    margin-bottom: $spacing-xs;
    @include text-ellipsis;
  }

  .session-meta {
    font-size: $font-size-extra-small;
    color: var(--color-text-secondary);
    display: flex;
    align-items: center;
    gap: $spacing-xs;
  }

  .session-actions {
    opacity: 0;
    transition: opacity $transition-duration-fast;
    margin-left: $spacing-sm;
  }
}

// 搜索框样式
.search-box {
  padding: $spacing-md $spacing-base;
  margin-bottom: $spacing-sm;

  :deep(.el-input__wrapper) {
    border-radius: $border-radius-lg;
    box-shadow: $box-shadow-sm;
    transition: all $transition-duration-fast;

    &:hover,
    &.is-focus {
      box-shadow: $box-shadow-md;
    }
  }
}

// 空状态样式
.empty-sessions {
  text-align: center;
  padding: $spacing-2xl;
  color: var(--color-text-secondary);

  p {
    margin-bottom: $spacing-lg;
  }
}

// 过渡动画
.slide-left-enter-active,
.slide-left-leave-active {
  transition:
    transform $transition-duration-base $transition-timing-function-ease-out,
    opacity $transition-duration-base;
}

.slide-left-enter-from,
.slide-left-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

// 响应式设计
@media (max-width: 1024px) {
  .sessions-sidebar {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .modern-learning-page {
    .sessions-sidebar {
      position: fixed;
      top: 0;
      bottom: 0;
      left: 0;
      z-index: $z-index-fixed;
      box-shadow: $box-shadow-xl;
      width: 320px;
    }
  }

  // 回到顶部按钮
  .scroll-to-top-button {
    position: fixed;
    right: 40px;
    bottom: 100px;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    background: var(--el-color-primary);
    border-color: var(--el-color-primary);
    color: white;

    &:hover {
      background: var(--el-color-primary-light-3);
      border-color: var(--el-color-primary-light-3);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    &:active {
      transform: translateY(0);
    }
  }

  .top-toolbar {
    padding: 0 $spacing-md;

    .page-title {
      font-size: $font-size-base;
    }

    .new-chat-button {
      padding: $spacing-sm $spacing-lg;
      font-size: $font-size-small;
    }
  }

  .message-container {
    padding: $spacing-md;
  }

  .suggested-questions {
    grid-template-columns: 1fr;
  }
}
</style>
