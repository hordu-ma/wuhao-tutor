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
              <h4 class="text-sm font-medium text-gray-600 mb-3">常见问题</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <button
                  v-for="question in quickQuestions"
                  :key="question"
                  @click="handleQuickQuestion(question)"
                  class="quick-question-btn p-3 text-left bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <span class="text-sm text-gray-700">{{ question }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <MessageItem
            v-for="message in learningStore.currentMessages"
            :key="message.id"
            :message="message"
            @feedback="handleFeedback"
            @copy="handleCopyMessage"
            @regenerate="handleRegenerateAnswer"
          />

          <!-- 加载指示器 -->
          <div
            v-if="learningStore.chatState.isLoading"
            class="text-center py-4"
          >
            <el-icon class="animate-spin text-blue-500"><Loading /></el-icon>
            <span class="ml-2 text-gray-500">正在加载历史记录...</span>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input bg-white border-t border-gray-200 px-6 py-4">
          <QuestionInput
            :disabled="!learningStore.canSendMessage"
            :loading="learningStore.isSubmittingQuestion"
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
            <span>按 Shift + Enter 换行，Enter 发送</span>
            <span
              v-if="learningStore.chatState.isTyping"
              class="typing-indicator flex items-center"
            >
              <el-icon class="animate-pulse mr-1"><EditPen /></el-icon>
              AI正在思考中...
            </span>
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
} from "@/types/learning";
import {
  LEARNING_SUBJECT_OPTIONS,
  LearningSubjectOption,
} from "@/types/learning";

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
const subjectOptions = SUBJECT_OPTIONS;

// 快捷问题
const quickQuestions = [
  "解释一下二次函数的性质",
  "如何提高英语阅读理解能力？",
  "请帮我分析这道数学题",
  "化学元素周期表的规律",
  "古诗词鉴赏的方法",
  "物理电路分析步骤",
];

// ========== 计算属性和工具函数 ==========

const getSubjectColor = (subject: string) => {
  const option = subjectOptions.find((opt) => opt.value === subject);
  return option?.color || "#gray";
};

const getSubjectLabel = (subject: string) => {
  const option = subjectOptions.find((opt) => opt.value === subject);
  return option?.label || subject;
};

// ========== 事件处理 ==========

/**
 * 处理问题提交
 */
const handleQuestionSubmit = async (request: AskQuestionRequest) => {
  try {
    await learningStore.askQuestion(request);

    // 滚动到底部
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error("提交问题失败:", error);
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
          "确定要删除此会话吗？删除后无法恢复。",
          "确认删除",
          {
            type: "error",
          },
        );
        await learningStore.deleteSession(currentSession.id);
      } catch (error) {
        if (error !== "cancel") {
          console.error("删除会话失败:", error);
        }
      }
      break;
  }
};

/**
 * 处理会话选择
 */
const handleSessionSelect = async (sessionId: string) => {
  try {
    showSessionDrawer.value = false;
    await learningStore.switchSession(sessionId);

    // 滚动到底部
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error("切换会话失败:", error);
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
  const currentSession = learningStore.chatState.currentSession;
  if (!currentSession || !editTitleData.title.trim()) return;

  try {
    isUpdatingTitle.value = true;
    await learningStore.updateSession(currentSession.id, {
      title: editTitleData.title.trim(),
    });

    showEditTitleDialog.value = false;
    ElMessage.success("标题更新成功");
  } catch (error) {
    console.error("更新标题失败:", error);
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
const handleScroll = () => {
  // TODO: 实现滚动加载更多历史消息
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

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: #f9fafb;
    }

    &::-webkit-scrollbar-thumb {
      background-color: #d1d5db;
      border-radius: 3px;

      &:hover {
        background-color: #9ca3af;
      }
    }
  }

  .quick-question-btn {
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
  }

  .typing-indicator {
    color: #3b82f6;
  }

  .error-tip {
    :deep(.el-alert) {
      border-radius: 8px;
    }
  }
}

.session-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
  }
}
</style>
