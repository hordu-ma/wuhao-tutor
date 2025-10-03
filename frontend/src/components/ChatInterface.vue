<template>
  <div class="chat-interface h-screen flex flex-col bg-gray-50">
    <!-- 头部工具栏 -->
    <div
      class="chat-header bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between"
    >
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <el-icon class="text-blue-500 text-2xl">
            <ChatDotRound />
          </el-icon>
          <h1 class="text-xl font-semibold text-gray-800">AI学习助手</h1>
        </div>

        <!-- 当前会话信息 -->
        <div
          v-if="learningStore.hasCurrentSession"
          class="flex items-center space-x-2 text-sm text-gray-600"
        >
          <el-divider direction="vertical" />
          <span>{{ learningStore.chatState.currentSession?.title }}</span>
          <el-tag
            v-if="learningStore.chatState.currentSession?.subject"
            size="small"
            :color="
              getSubjectColor(learningStore.chatState.currentSession.subject)
            "
          >
            {{
              getSubjectLabel(learningStore.chatState.currentSession.subject)
            }}
          </el-tag>
        </div>
      </div>

      <div class="flex items-center space-x-3">
        <!-- 会话操作 -->
        <el-dropdown
          v-if="learningStore.hasCurrentSession"
          @command="handleSessionCommand"
        >
          <el-button type="primary" text>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit-title">
                <el-icon><Edit /></el-icon>
                编辑标题
              </el-dropdown-item>
              <el-dropdown-item command="archive">
                <el-icon><FolderOpened /></el-icon>
                归档会话
              </el-dropdown-item>
              <el-dropdown-item command="export">
                <el-icon><Download /></el-icon>
                导出记录
              </el-dropdown-item>
              <el-dropdown-item divided command="delete" class="text-red-500">
                <el-icon><Delete /></el-icon>
                删除会话
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 新建会话 -->
        <el-button type="primary" @click="showNewSessionDialog = true">
          <el-icon><Plus /></el-icon>
          新建会话
        </el-button>

        <!-- 会话历史切换 -->
        <el-button type="default" @click="showSessionDrawer = true">
          <el-icon><List /></el-icon>
          会话历史
        </el-button>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="chat-body flex-1 flex overflow-hidden">
      <!-- 消息区域 -->
      <div class="chat-messages flex-1 flex flex-col">
        <!-- 消息列表 -->
        <div
          ref="messageContainer"
          class="message-list flex-1 overflow-y-auto px-6 py-4 space-y-4"
          @scroll="handleScroll"
        >
          <!-- 空状态 -->
          <div
            v-if="
              !learningStore.currentMessages.length &&
              !learningStore.chatState.isLoading
            "
            class="empty-state text-center py-20"
          >
            <el-icon class="text-6xl text-gray-300 mb-4">
              <ChatDotRound />
            </el-icon>
            <h3 class="text-lg font-medium text-gray-600 mb-2">
              开始新的学习对话
            </h3>
            <p class="text-gray-500 mb-6">
              向AI助手提问学习相关问题，获得专业的解答和指导
            </p>

            <!-- 快捷问题 -->
            <div class="quick-questions max-w-2xl mx-auto">
              <h4 class="text-sm font-medium text-gray-600 mb-3">快速开始</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <button
                  v-for="question in quickQuestions"
                  :key="question"
                  @click="handleQuickQuestion(question)"
                  class="quick-question-btn p-3 text-left bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 transform hover:scale-105"
                >
                  <el-icon class="text-blue-500 mb-2"
                    ><QuestionFilled
                  /></el-icon>
                  <div class="text-sm text-gray-700 font-medium">
                    {{ question }}
                  </div>
                </button>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div class="messages-container">
            <MessageItem
              v-for="(message, index) in learningStore.currentMessages"
              :key="message.id"
              :message="message"
              :show-timestamp="shouldShowTimestamp(message, index)"
              @feedback="handleFeedback"
              @copy="handleCopyMessage"
              @regenerate="handleRegenerateAnswer"
            />
          </div>

          <!-- AI正在思考指示器 -->
          <div
            v-if="learningStore.chatState.isTyping"
            class="ai-thinking py-4 flex justify-start"
          >
            <div class="flex items-center space-x-3">
              <div
                class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"
              >
                <el-icon class="text-white text-sm">
                  <ChatDotRound />
                </el-icon>
              </div>
              <div
                class="bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm"
              >
                <div class="flex items-center space-x-2">
                  <div class="typing-dots flex space-x-1">
                    <div
                      class="dot w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    ></div>
                    <div
                      class="dot w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style="animation-delay: 0.1s"
                    ></div>
                    <div
                      class="dot w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style="animation-delay: 0.2s"
                    ></div>
                  </div>
                  <span class="text-sm text-gray-500">AI正在思考中...</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载指示器 -->
          <div
            v-if="
              learningStore.chatState.isLoading &&
              !learningStore.chatState.isTyping
            "
            class="text-center py-8"
          >
            <div class="flex flex-col items-center space-y-3">
              <el-icon class="animate-spin text-blue-500 text-2xl"
                ><Loading
              /></el-icon>
              <span class="text-gray-500">正在加载历史记录...</span>
              <div class="text-xs text-gray-400">请稍候，这可能需要几秒钟</div>
            </div>
          </div>

          <!-- 连接错误提示 -->
          <div
            v-if="
              learningStore.chatState.error &&
              !learningStore.chatState.isLoading
            "
            class="text-center py-8"
          >
            <div class="flex flex-col items-center space-y-4">
              <el-icon class="text-red-500 text-3xl"><Warning /></el-icon>
              <div class="text-red-600 font-medium">连接失败</div>
              <div class="text-gray-500 text-sm max-w-md">
                {{ learningStore.chatState.error }}
              </div>
              <el-button
                type="primary"
                size="small"
                @click="handleRetryConnection"
              >
                <el-icon class="mr-1"><Refresh /></el-icon>
                重试连接
              </el-button>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input bg-white border-t border-gray-200 px-6 py-4">
          <QuestionInput
            :disabled="!learningStore.canSendMessage"
            :loading="learningStore.isSubmittingQuestion"
            :placeholder="inputPlaceholder"
            @submit="handleQuestionSubmit"
          />

          <!-- 提示信息 -->
          <div v-if="learningStore.chatState.error" class="error-tip mt-2">
            <el-alert
              :title="learningStore.chatState.error"
              type="error"
              :closable="true"
              @close="clearError"
            />
          </div>

          <div
            class="input-tips mt-2 flex items-center justify-between text-xs text-gray-500"
          >
            <div class="flex items-center space-x-4">
              <span>按 Shift + Enter 换行，Enter 发送</span>
              <span
                v-if="learningStore.hasCurrentSession"
                class="text-green-600"
              >
                <el-icon class="mr-1"><Select /></el-icon>
                已连接会话
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <span
                v-if="learningStore.currentMessages.length > 0"
                class="text-gray-400"
              >
                {{ learningStore.currentMessages.length }} 条消息
              </span>
              <span
                v-if="learningStore.chatState.isTyping"
                class="typing-indicator flex items-center text-blue-500"
              >
                <el-icon class="animate-pulse mr-1"><EditPen /></el-icon>
                AI正在输入...
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 会话历史侧边栏 -->
    <el-drawer
      v-model="showSessionDrawer"
      title="会话历史"
      direction="rtl"
      size="400px"
      class="session-drawer"
    >
      <SessionHistory
        @select-session="handleSessionSelect"
        @create-session="showNewSessionDialog = true"
        @close-drawer="showSessionDrawer = false"
      />
    </el-drawer>

    <!-- 新建会话对话框 -->
    <el-dialog
      v-model="showNewSessionDialog"
      title="新建学习会话"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="newSessionForm"
        :model="newSessionData"
        :rules="newSessionRules"
        label-width="80px"
        @submit.prevent="handleCreateSession"
      >
        <el-form-item label="会话标题" prop="title">
          <el-input
            v-model="newSessionData.title"
            placeholder="请输入会话标题"
            maxlength="100"
            show-word-limit
            clearable
          />
        </el-form-item>

        <el-form-item label="学科选择" prop="subject">
          <el-select
            v-model="newSessionData.subject"
            placeholder="请选择学科"
            clearable
            class="w-full"
          >
            <el-option
              v-for="subject in subjectOptions"
              :key="subject.value"
              :label="subject.label"
              :value="subject.value"
            >
              <div class="flex items-center">
                <div
                  class="w-3 h-3 rounded-full mr-2"
                  :style="{ backgroundColor: subject.color }"
                />
                {{ subject.label }}
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="学段选择">
          <el-select
            v-model="newSessionData.grade_level"
            placeholder="请选择学段"
            clearable
            class="w-full"
          >
            <el-option label="小学" value="primary" />
            <el-option label="初一" value="junior_1" />
            <el-option label="初二" value="junior_2" />
            <el-option label="初三" value="junior_3" />
            <el-option label="高一" value="senior_1" />
            <el-option label="高二" value="senior_2" />
            <el-option label="高三" value="senior_3" />
          </el-select>
        </el-form-item>

        <el-form-item label="初始问题">
          <el-input
            v-model="newSessionData.initial_question"
            type="textarea"
            :rows="3"
            placeholder="可选，输入您想要讨论的第一个问题"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="newSessionData.context_enabled">
            启用学习上下文（基于之前的学习记录提供个性化建议）
          </el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="flex justify-end space-x-3">
          <el-button @click="showNewSessionDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleCreateSession"
            :loading="isCreatingSession"
          >
            创建会话
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑会话标题对话框 -->
    <el-dialog
      v-model="showEditTitleDialog"
      title="编辑会话标题"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="editTitleData.title"
        placeholder="请输入新的会话标题"
        maxlength="100"
        show-word-limit
        @keyup.enter="handleUpdateTitle"
      />

      <template #footer>
        <div class="flex justify-end space-x-3">
          <el-button @click="showEditTitleDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleUpdateTitle"
            :loading="isUpdatingTitle"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, onUnmounted } from "vue";
import { ElMessage, ElMessageBox, type FormInstance } from "element-plus";
import {
  ChatDotRound,
  MoreFilled,
  Edit,
  FolderOpened,
  Download,
  Delete,
  Plus,
  List,
  Loading,
  EditPen,
  QuestionFilled,
  Select,
  Warning,
  Refresh,
} from "@element-plus/icons-vue";

// 组件导入
import MessageItem from "./MessageItem.vue";
import QuestionInput from "./QuestionInput.vue";
import SessionHistory from "./SessionHistory.vue";

// Store和类型导入
import { useLearningStore } from "@/stores/learning";
import type {
  AskQuestionRequest,
  CreateSessionRequest,
  FeedbackRequest,
  LearningSubjectOption,
} from "@/types/learning";
import { LEARNING_SUBJECT_OPTIONS, QuestionType } from "@/types/learning";

// ========== 响应式数据 ==========

const learningStore = useLearningStore();

// UI状态
const showSessionDrawer = ref(false);
const showNewSessionDialog = ref(false);
const showEditTitleDialog = ref(false);
const isCreatingSession = ref(false);
const isUpdatingTitle = ref(false);

// DOM引用
const messageContainer = ref<HTMLElement>();
const newSessionForm = ref<FormInstance>();

// 表单数据
const newSessionData = reactive<CreateSessionRequest>({
  title: "",
  subject: undefined,
  grade_level: undefined,
  context_enabled: true,
  initial_question: undefined,
});

const editTitleData = reactive({
  title: "",
});

// 表单验证规则
const newSessionRules = {
  title: [
    { required: true, message: "请输入会话标题", trigger: "blur" },
    {
      min: 2,
      max: 100,
      message: "标题长度应在 2-100 个字符之间",
      trigger: "blur",
    },
  ],
};

// 选项数据
const subjectOptions = LEARNING_SUBJECT_OPTIONS;

// 快捷问题
const quickQuestions = [
  "数学题目解答",
  "英语语法讲解",
  "物理概念解释",
  "化学实验分析",
  "语文阅读理解",
  "历史事件梳理",
];

// ========== 计算属性和工具函数 ==========

const inputPlaceholder = computed(() => {
  if (!learningStore.hasCurrentSession) {
    return "请先创建会话开始学习对话...";
  }
  if (learningStore.chatState.isLoading) {
    return "正在加载中，请稍候...";
  }
  if (learningStore.currentMessages.length === 0) {
    return "开始提问吧！描述你的问题越详细，AI回答越准确...";
  }
  return "继续提问，或询问相关知识点...";
});

const getSubjectColor = (subject: string) => {
  const option = subjectOptions.find(
    (opt: LearningSubjectOption) => opt.value === subject,
  );
  return option?.color || "#gray";
};

const getSubjectLabel = (subject: string) => {
  const option = subjectOptions.find(
    (opt: LearningSubjectOption) => opt.value === subject,
  );
  return option?.label || subject;
};

const shouldShowTimestamp = (message: any, index: number) => {
  // 第一条消息总是显示时间戳
  if (index === 0) return true;

  const prevMessage = learningStore.currentMessages[index - 1];
  if (!prevMessage) return true;

  const currentTime = new Date(message.timestamp);
  const prevTime = new Date(prevMessage.timestamp);
  const diffInMinutes =
    (currentTime.getTime() - prevTime.getTime()) / (1000 * 60);

  // 不同用户类型之间的消息显示时间戳
  if (message.type !== prevMessage.type) {
    return diffInMinutes > 1; // 不同类型消息间隔1分钟显示时间戳
  }

  // 同类型消息超过5分钟显示时间戳
  // 或者是错误消息/重要消息总是显示时间戳
  return diffInMinutes > 5 || message.error || message.is_important;
};

// ========== 事件处理 ==========

/**
 * 处理问题提交
 */
const handleQuestionSubmit = async (request: AskQuestionRequest) => {
  try {
    // 如果没有当前会话，先创建一个默认会话
    if (!learningStore.hasCurrentSession) {
      const session = await learningStore.createSession({
        title: `学习会话 ${new Date().toLocaleString()}`,
        subject: request.subject,
        context_enabled: true,
      });
      await learningStore.switchSession(session.id);
    }

    await learningStore.askQuestion(request);

    // 滚动到底部
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error("提交问题失败:", error);
    ElMessage.error("发送消息失败，请稍后重试");
  }
};

/**
 * 处理快捷问题点击
 */
const handleQuickQuestion = async (question: string) => {
  const request: AskQuestionRequest = {
    content: question,
    question_type: QuestionType.GENERAL_INQUIRY,
    use_context: true,
    include_history: true,
  };

  await handleQuestionSubmit(request);
};

/**
 * 处理会话命令
 */
const handleSessionCommand = async (command: string) => {
  const currentSession = learningStore.chatState.currentSession;
  if (!currentSession) return;

  switch (command) {
    case "edit-title":
      editTitleData.title = currentSession.title;
      showEditTitleDialog.value = true;
      break;

    case "archive":
      try {
        await ElMessageBox.confirm(
          "确定要归档此会话吗？归档后可以在历史记录中找到。",
          "确认归档",
          {
            type: "warning",
          },
        );
        await learningStore.archiveSession(currentSession.id);
        ElMessage.success("会话已归档");
      } catch (error) {
        if (error !== "cancel") {
          console.error("归档会话失败:", error);
        }
      }
      break;

    case "export":
      // TODO: 实现导出功能
      ElMessage.info("导出功能开发中...");
      break;

    case "delete":
      try {
        await ElMessageBox.confirm(
          `确定要删除会话「${currentSession.title}」吗？\n\n此操作将永久删除：\n• 会话中的所有对话记录\n• 相关的学习数据和反馈\n• 无法恢复已删除的内容\n\n建议先归档会话以保留数据。`,
          "⚠️ 危险操作：删除会话",
          {
            type: "error",
            confirmButtonText: "确认删除",
            cancelButtonText: "取消",
            confirmButtonClass: "el-button--danger",
            showClose: false,
            closeOnClickModal: false,
            closeOnPressEscape: false,
          },
        );

        ElMessage.info("正在删除会话...");
        await learningStore.deleteSession(currentSession.id);
        ElMessage.success("会话已删除");
      } catch (error) {
        if (error !== "cancel") {
          console.error("删除会话失败:", error);
          ElMessage.error("删除会话失败，请重试");
        }
      }
      break;
  }
};

/**
 * 处理会话选择
 */
const handleSessionSelect = async (session: any) => {
  try {
    showSessionDrawer.value = false;

    // 显示切换中状态
    ElMessage.info({
      message: `正在切换到「${session.title}」...`,
      duration: 1000,
    });

    await learningStore.switchSession(session.id);
    await nextTick();
    scrollToBottom();

    // 显示成功反馈
    ElMessage.success({
      message: `已切换到「${session.title}」`,
      duration: 2000,
    });
  } catch (error) {
    console.error("切换会话失败:", error);
    ElMessage.error("切换会话失败，请重试");
  }
};

/**
 * 处理创建会话
 */
const handleCreateSession = async () => {
  if (!newSessionForm.value) return;

  try {
    await newSessionForm.value.validate();
    isCreatingSession.value = true;

    const session = await learningStore.createSession(newSessionData);

    // 切换到新会话
    await learningStore.switchSession(session.id);

    // 如果有初始问题，自动发送
    if (newSessionData.initial_question?.trim()) {
      await handleQuestionSubmit({
        content: newSessionData.initial_question,
        question_type: QuestionType.GENERAL_INQUIRY,
        subject: newSessionData.subject,
        use_context: newSessionData.context_enabled,
        include_history: false,
      });
    }

    // 重置表单
    Object.assign(newSessionData, {
      title: "",
      subject: undefined,
      grade_level: undefined,
      context_enabled: true,
      initial_question: undefined,
    });

    showNewSessionDialog.value = false;
    ElMessage.success("会话创建成功");
  } catch (error) {
    console.error("创建会话失败:", error);
  } finally {
    isCreatingSession.value = false;
  }
};

/**
 * 处理更新标题
 */
const handleUpdateTitle = async () => {
  if (!editTitleData.title.trim()) return;

  const currentSession = learningStore.chatState.currentSession;
  if (!currentSession) return;

  try {
    isUpdatingTitle.value = true;

    const oldTitle = currentSession.title;
    const newTitle = editTitleData.title.trim();

    if (oldTitle === newTitle) {
      showEditTitleDialog.value = false;
      ElMessage.info("标题未发生变化");
      return;
    }

    ElMessage.info("正在更新标题...");

    await learningStore.updateSession(currentSession.id, {
      title: newTitle,
    });

    showEditTitleDialog.value = false;
    ElMessage.success({
      message: `标题已更新为「${newTitle}」`,
      duration: 3000,
    });
  } catch (error) {
    console.error("更新标题失败:", error);

    let errorMessage = "更新失败，请重试";
    if (typeof error === "string") {
      errorMessage = error;
    } else if (error && typeof error === "object" && "message" in error) {
      errorMessage = error.message as string;
    }

    ElMessage.error({
      message: errorMessage,
      duration: 5000,
    });
  } finally {
    isUpdatingTitle.value = false;
  }
};

/**
 * 处理反馈
 */
const handleFeedback = async (feedback: FeedbackRequest) => {
  try {
    await learningStore.submitFeedback(feedback);
  } catch (error) {
    console.error("提交反馈失败:", error);
  }
};

/**
 * 处理复制消息
 */
const handleCopyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content);
    ElMessage.success("内容已复制到剪贴板");
  } catch (error) {
    console.error("复制失败:", error);
    ElMessage.error("复制失败");
  }
};

/**
 * 处理重新生成答案
 */
const handleRegenerateAnswer = async (_questionId: string) => {
  // TODO: 实现重新生成功能
  ElMessage.info("重新生成功能开发中...");
};

/**
 * 清除错误信息
 */
const clearError = () => {
  learningStore.clearError();
};

/**
 * 处理重试连接
 */
const handleRetryConnection = async () => {
  try {
    learningStore.clearError();
    // 如果有当前会话，重新切换到当前会话（会重新加载消息）
    if (
      learningStore.hasCurrentSession &&
      learningStore.chatState.currentSession?.id
    ) {
      await learningStore.switchSession(
        learningStore.chatState.currentSession.id,
      );
    } else {
      // 否则重新加载会话列表
      await learningStore.loadSessions();
    }
    ElMessage.success("连接已恢复");
  } catch (error) {
    console.error("重试连接失败:", error);
    ElMessage.error("连接失败，请检查网络后重试");
  }
};

/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
  }
};

/**
 * 处理滚动事件
 */
const handleScroll = (event: Event) => {
  const container = event.target as HTMLElement;
  if (!container) return;

  // 检查是否滚动到顶部，加载更多历史消息
  if (container.scrollTop === 0 && learningStore.hasCurrentSession) {
    // TODO: 实现滚动加载更多历史消息
    console.log("滚动到顶部，可以加载更多历史消息");
  }
};

// ========== 生命周期 ==========

onMounted(async () => {
  try {
    await learningStore.initialize();

    // 如果有最新活跃会话，自动切换过去
    if (learningStore.latestActiveSession) {
      await learningStore.switchSession(learningStore.latestActiveSession.id);
    }
  } catch (error) {
    console.error("初始化聊天界面失败:", error);
  }
});

onUnmounted(() => {
  // 清理资源
});
</script>

<style scoped lang="scss">
.chat-interface {
  .message-list {
    scrollbar-width: thin;
    scrollbar-color: #d1d5db #f9fafb;
    scroll-behavior: smooth;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f9fafb;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background-color: #d1d5db;
      border-radius: 3px;
      transition: background-color 0.2s ease;

      &:hover {
        background-color: #9ca3af;
      }
    }
  }

  .quick-question-btn {
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 2px solid transparent;

    &::before {
      content: "";
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(59, 130, 246, 0.1),
        transparent
      );
      transition: left 0.6s ease;
    }

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
      border-color: rgba(59, 130, 246, 0.2);

      &::before {
        left: 100%;
      }
    }

    &:active {
      transform: translateY(0);
      transition: transform 0.1s ease;
    }
  }

  .ai-thinking {
    animation: fadeInUp 0.4s ease-out;

    .typing-dots {
      .dot {
        animation: typing 1.4s ease-in-out infinite;

        &:nth-child(2) {
          animation-delay: 0.2s;
        }

        &:nth-child(3) {
          animation-delay: 0.4s;
        }
      }
    }
  }

  .messages-container {
    .message-item {
      animation: slideInFromBottom 0.4s ease-out;
      animation-fill-mode: both;

      &:nth-child(n) {
        animation-delay: calc(var(--index, 0) * 0.1s);
      }
    }
  }

  .typing-indicator {
    color: #3b82f6;
    font-weight: 500;

    .el-icon {
      animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
  }

  .error-tip {
    animation: shakeX 0.6s ease-in-out;

    :deep(.el-alert) {
      border-radius: 8px;
      border-left: 4px solid #ef4444;
    }
  }

  .chat-header {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .chat-input {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    backdrop-filter: blur(10px);
    border-top: 1px solid rgba(226, 232, 240, 0.8);
    box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.05);
  }

  .empty-state {
    .el-icon {
      animation: float 3s ease-in-out infinite;
    }

    h3,
    p {
      animation: fadeInUp 0.6s ease-out;
      animation-delay: 0.2s;
      animation-fill-mode: both;
    }

    .quick-questions {
      animation: fadeInUp 0.6s ease-out;
      animation-delay: 0.4s;
      animation-fill-mode: both;
    }
  }

  .input-tips {
    span {
      transition: all 0.2s ease;

      &:hover {
        color: #3b82f6;
      }
    }
  }
}

.session-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
    background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  }

  :deep(.el-drawer__header) {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  }
}

// 自定义动画
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

@keyframes slideInFromBottom {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes shakeX {
  0%,
  100% {
    transform: translateX(0);
  }
  10%,
  30%,
  50%,
  70%,
  90% {
    transform: translateX(-5px);
  }
  20%,
  40%,
  60%,
  80% {
    transform: translateX(5px);
  }
}

// 响应式设计优化
@media (max-width: 768px) {
  .chat-interface {
    .chat-header {
      padding: 1rem;

      .flex {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;

        &:first-child {
          width: 100%;
        }
      }
    }

    .message-list {
      padding: 1rem;
    }

    .chat-input {
      padding: 1rem;
    }

    .quick-questions {
      .grid {
        grid-template-columns: 1fr;
      }
    }

    .input-tips {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }
}

// 暗色主题支持
@media (prefers-color-scheme: dark) {
  .chat-interface {
    background-color: #0f172a;

    .chat-header,
    .chat-input {
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border-color: rgba(71, 85, 105, 0.3);
    }

    .quick-question-btn {
      background-color: #1e293b;
      border-color: #334155;
      color: #e2e8f0;

      &:hover {
        background-color: #334155;
        border-color: rgba(59, 130, 246, 0.3);
      }
    }

    .ai-thinking {
      .bg-white {
        background-color: #1e293b !important;
        border-color: #334155 !important;
      }
    }
  }
}
</style>
