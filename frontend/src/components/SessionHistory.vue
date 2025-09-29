<template>
  <div class="session-history h-full flex flex-col bg-white">
    <!-- 搜索和操作栏 -->
    <div class="header px-4 py-4 border-b border-gray-200">
      <!-- 搜索框 -->
      <el-input
        v-model="searchKeyword"
        placeholder="搜索会话..."
        size="small"
        clearable
        class="mb-3"
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <!-- 操作按钮 -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <el-button
            type="primary"
            size="small"
            @click="$emit('create-session')"
          >
            <el-icon><Plus /></el-icon>
            新建会话
          </el-button>

          <!-- 刷新按钮 -->
          <el-button
            type="default"
            size="small"
            @click="handleRefresh"
            :loading="learningStore.isLoadingSessions"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>

        <!-- 筛选下拉 -->
        <el-dropdown @command="handleFilterCommand" size="small">
          <el-button type="text" size="small">
            <el-icon><Filter /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="all">全部会话</el-dropdown-item>
              <el-dropdown-item command="active">进行中</el-dropdown-item>
              <el-dropdown-item command="archived">已归档</el-dropdown-item>
              <el-dropdown-item divided command="today">今天</el-dropdown-item>
              <el-dropdown-item command="week">本周</el-dropdown-item>
              <el-dropdown-item command="month">本月</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <!-- 筛选标签 -->
      <div v-if="currentFilter !== 'all'" class="mt-2">
        <el-tag
          size="small"
          closable
          @close="
            currentFilter = 'all';
            applyFilter();
          "
        >
          {{ getFilterLabel(currentFilter) }}
        </el-tag>
      </div>
    </div>

    <!-- 会话列表 -->
    <div class="session-list flex-1 overflow-y-auto">
      <!-- 空状态 -->
      <div
        v-if="!filteredSessions.length && !learningStore.isLoadingSessions"
        class="empty-state text-center py-12 px-4"
      >
        <el-icon class="text-4xl text-gray-300 mb-4">
          <ChatDotRound />
        </el-icon>
        <p class="text-gray-500 text-sm">
          {{ searchKeyword ? "未找到匹配的会话" : "还没有任何会话" }}
        </p>
        <el-button
          v-if="!searchKeyword"
          type="primary"
          size="small"
          @click="$emit('create-session')"
          class="mt-3"
        >
          创建第一个会话
        </el-button>
      </div>

      <!-- 会话项列表 -->
      <div v-else class="space-y-1 p-2">
        <div
          v-for="session in filteredSessions"
          :key="session.id"
          class="session-item p-3 rounded-lg cursor-pointer border border-transparent transition-all hover:bg-gray-50 hover:border-gray-200"
          :class="{
            'bg-blue-50 border-blue-200':
              session.id === learningStore.chatState.currentSession?.id,
            'opacity-60': session.status === 'archived',
          }"
          @click="handleSessionSelect(session)"
        >
          <!-- 会话头部 -->
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-2 flex-1 min-w-0">
              <!-- 状态图标 -->
              <div
                class="w-2 h-2 rounded-full flex-shrink-0"
                :class="{
                  'bg-green-500': session.status === 'active',
                  'bg-gray-400': session.status === 'closed',
                  'bg-yellow-500': session.status === 'archived',
                }"
              />

              <!-- 会话标题 -->
              <h4
                class="text-sm font-medium text-gray-800 truncate"
                :title="session.title"
              >
                {{ session.title }}
              </h4>
            </div>

            <!-- 操作菜单 -->
            <el-dropdown
              @command="(cmd) => handleSessionCommand(cmd, session)"
              @click.stop
              trigger="click"
              size="small"
            >
              <el-button
                type="text"
                size="small"
                class="text-gray-400 hover:text-gray-600"
              >
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-if="session.status === 'active'"
                    command="archive"
                  >
                    <el-icon><FolderOpened /></el-icon>
                    归档
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="session.status === 'archived'"
                    command="activate"
                  >
                    <el-icon><FolderRemove /></el-icon>
                    恢复
                  </el-dropdown-item>
                  <el-dropdown-item command="edit">
                    <el-icon><Edit /></el-icon>
                    重命名
                  </el-dropdown-item>
                  <el-dropdown-item
                    divided
                    command="delete"
                    class="text-red-500"
                  >
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <!-- 会话信息 -->
          <div class="text-xs text-gray-500 space-y-1">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <!-- 学科标签 -->
                <el-tag
                  v-if="session.subject"
                  size="small"
                  :color="getSubjectColor(session.subject)"
                  class="!text-xs !px-1 !py-0"
                >
                  {{ getSubjectLabel(session.subject) }}
                </el-tag>

                <!-- 问题数量 -->
                <span>{{ session.question_count }} 个问题</span>
              </div>

              <!-- 最后活动时间 -->
              <span>{{
                formatTime(session.last_active_at || session.updated_at)
              }}</span>
            </div>

            <!-- Token使用情况 -->
            <div v-if="session.total_tokens > 0" class="text-right">
              <span class="text-orange-500"
                >{{ session.total_tokens }} tokens</span
              >
            </div>
          </div>

          <!-- 进度条（如果正在处理） -->
          <div v-if="session.id === processingSessionId" class="mt-2">
            <el-progress
              :percentage="100"
              :show-text="false"
              :stroke-width="2"
              status="success"
            />
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div
        v-if="learningStore.sessionPagination.hasMore"
        class="text-center p-4"
      >
        <el-button
          type="text"
          size="small"
          @click="handleLoadMore"
          :loading="learningStore.sessionPagination.loading"
        >
          加载更多
        </el-button>
      </div>

      <!-- 加载指示器 -->
      <div
        v-if="learningStore.isLoadingSessions && !filteredSessions.length"
        class="text-center p-8"
      >
        <el-icon class="text-2xl text-gray-400 animate-spin mb-2">
          <Loading />
        </el-icon>
        <p class="text-sm text-gray-500">加载中...</p>
      </div>
    </div>

    <!-- 底部统计 -->
    <div
      class="footer px-4 py-3 border-t border-gray-100 bg-gray-50 text-xs text-gray-600"
    >
      <div class="flex items-center justify-between">
        <span>共 {{ learningStore.sessionPagination.total }} 个会话</span>
        <span>活跃: {{ activeSessions.length }}</span>
      </div>
    </div>

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="showRenameDialog"
      title="重命名会话"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="renameData.title"
        placeholder="请输入新的会话名称"
        maxlength="100"
        show-word-limit
        @keyup.enter="handleRename"
        ref="renameInputRef"
      />

      <template #footer>
        <div class="flex justify-end space-x-3">
          <el-button @click="showRenameDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleRename"
            :loading="isRenaming"
            :disabled="!renameData.title.trim()"
          >
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, watch } from "vue";
import { ElMessage, ElMessageBox, type ElInput } from "element-plus";
import {
  Search,
  Plus,
  Refresh,
  Filter,
  ChatDotRound,
  MoreFilled,
  FolderOpened,
  FolderRemove,
  Edit,
  Delete,
  Loading,
} from "@element-plus/icons-vue";

// Store和类型导入
import { useLearningStore } from "@/stores/learning";
import type { ChatSession } from "@/types/learning";
import {
  LEARNING_SUBJECT_OPTIONS,
  SessionStatus,
  type LearningSubjectOption,
} from "@/types/learning";

// ========== 接口定义 ==========

interface Emits {
  (e: "select-session", sessionId: string): void;
  (e: "create-session"): void;
  (e: "close-drawer"): void;
}

// ========== Props和Emits ==========

const emit = defineEmits<Emits>();

// ========== 响应式数据 ==========

const learningStore = useLearningStore();

// 搜索和筛选
const searchKeyword = ref("");
const currentFilter = ref<string>("all");
const processingSessionId = ref<string>();

// 对话框状态
const showRenameDialog = ref(false);
const isRenaming = ref(false);
const renameInputRef = ref<InstanceType<typeof ElInput>>();

// 重命名数据
const renameData = reactive({
  sessionId: "",
  title: "",
});

// ========== 计算属性 ==========

const activeSessions = computed(() =>
  learningStore.chatState.sessions.filter(
    (session) => session.status === SessionStatus.ACTIVE,
  ),
);

const filteredSessions = computed(() => {
  let sessions = [...learningStore.chatState.sessions];

  // 搜索过滤
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase();
    sessions = sessions.filter(
      (session) =>
        session.title.toLowerCase().includes(keyword) ||
        (session.subject &&
          getSubjectLabel(session.subject).toLowerCase().includes(keyword)),
    );
  }

  // 状态筛选
  switch (currentFilter.value) {
    case "active":
      sessions = sessions.filter(
        (session) => session.status === SessionStatus.ACTIVE,
      );
      break;
    case "archived":
      sessions = sessions.filter(
        (session) => session.status === SessionStatus.ARCHIVED,
      );
      break;
    case "today":
      sessions = sessions.filter((session) => {
        const sessionDate = new Date(
          session.last_active_at || session.updated_at,
        );
        const today = new Date();
        return sessionDate.toDateString() === today.toDateString();
      });
      break;
    case "week":
      sessions = sessions.filter((session) => {
        const sessionDate = new Date(
          session.last_active_at || session.updated_at,
        );
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
        return sessionDate >= oneWeekAgo;
      });
      break;
    case "month":
      sessions = sessions.filter((session) => {
        const sessionDate = new Date(
          session.last_active_at || session.updated_at,
        );
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
        return sessionDate >= oneMonthAgo;
      });
      break;
  }

  // 按最后活动时间排序
  return sessions.sort((a, b) => {
    const dateA = new Date(a.last_active_at || a.updated_at);
    const dateB = new Date(b.last_active_at || b.updated_at);
    return dateB.getTime() - dateA.getTime();
  });
});

// ========== 工具函数 ==========

const getSubjectColor = (subject: string): string => {
  const option = LEARNING_SUBJECT_OPTIONS.find(
    (opt: LearningSubjectOption) => opt.value === subject,
  );
  return option?.color || "#6b7280";
};

const getSubjectLabel = (subject: string): string => {
  const option = LEARNING_SUBJECT_OPTIONS.find(
    (opt: LearningSubjectOption) => opt.value === subject,
  );
  return option?.label || subject;
};

const getFilterLabel = (filter: string) => {
  const labels: Record<string, string> = {
    all: "全部会话",
    active: "进行中",
    archived: "已归档",
    today: "今天",
    week: "本周",
    month: "本月",
  };
  return labels[filter] || filter;
};

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

  if (diffInHours < 1) {
    const diffInMinutes = Math.floor(diffInHours * 60);
    return diffInMinutes <= 0 ? "刚刚" : `${diffInMinutes}分钟前`;
  } else if (diffInHours < 24) {
    return `${Math.floor(diffInHours)}小时前`;
  } else if (diffInHours < 24 * 7) {
    return `${Math.floor(diffInHours / 24)}天前`;
  } else {
    return date.toLocaleDateString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
    });
  }
};

// ========== 事件处理 ==========

const handleSearch = () => {
  // 搜索逻辑在computed中处理
};

const handleRefresh = async () => {
  try {
    await learningStore.loadSessions();
  } catch (error) {
    console.error("刷新会话列表失败:", error);
  }
};

const handleFilterCommand = (command: string) => {
  currentFilter.value = command;
  applyFilter();
};

const applyFilter = () => {
  // 筛选逻辑在computed中处理
};

const handleLoadMore = async () => {
  try {
    await learningStore.loadMoreSessions();
  } catch (error) {
    console.error("加载更多会话失败:", error);
  }
};

const handleSessionSelect = (session: ChatSession) => {
  processingSessionId.value = session.id;
  emit("select-session", session.id);

  // 清除处理状态
  setTimeout(() => {
    processingSessionId.value = undefined;
    emit("close-drawer");
  }, 500);
};

const handleSessionCommand = async (command: string, session: ChatSession) => {
  switch (command) {
    case "edit":
      renameData.sessionId = session.id;
      renameData.title = session.title;
      showRenameDialog.value = true;

      // 聚焦输入框
      await nextTick();
      renameInputRef.value?.focus();
      break;

    case "archive":
      try {
        await learningStore.archiveSession(session.id);
      } catch (error) {
        console.error("归档会话失败:", error);
      }
      break;

    case "activate":
      try {
        await learningStore.activateSession(session.id);
      } catch (error) {
        console.error("恢复会话失败:", error);
      }
      break;

    case "delete":
      try {
        await ElMessageBox.confirm(
          "确定要删除此会话吗？删除后无法恢复。",
          "确认删除",
          {
            type: "error",
            confirmButtonText: "删除",
            cancelButtonText: "取消",
          },
        );
        await learningStore.deleteSession(session.id);
      } catch (error) {
        if (error !== "cancel") {
          console.error("删除会话失败:", error);
        }
      }
      break;
  }
};

const handleRename = async () => {
  if (!renameData.title.trim()) return;

  isRenaming.value = true;
  try {
    await learningStore.updateSession(renameData.sessionId, {
      title: renameData.title.trim(),
    });

    showRenameDialog.value = false;
    ElMessage.success("会话重命名成功");
  } catch (error) {
    console.error("重命名会话失败:", error);
  } finally {
    isRenaming.value = false;
  }
};

// ========== 监听器 ==========

watch(showRenameDialog, (show) => {
  if (!show) {
    // 重置重命名数据
    Object.assign(renameData, {
      sessionId: "",
      title: "",
    });
  }
});
</script>

<style scoped lang="scss">
.session-history {
  .session-list {
    scrollbar-width: thin;
    scrollbar-color: #d1d5db #f9fafb;

    &::-webkit-scrollbar {
      width: 4px;
    }

    &::-webkit-scrollbar-track {
      background: #f9fafb;
    }

    &::-webkit-scrollbar-thumb {
      background-color: #d1d5db;
      border-radius: 2px;

      &:hover {
        background-color: #9ca3af;
      }
    }
  }

  .session-item {
    &:hover {
      transform: translateX(2px);
    }

    &.active {
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
    }
  }

  .empty-state {
    .el-button {
      transform: translateY(0);
      transition: transform 0.2s ease;

      &:hover {
        transform: translateY(-1px);
      }
    }
  }

  .footer {
    font-size: 11px;
    letter-spacing: 0.5px;
  }
}

// 进度条动画
.el-progress {
  :deep(.el-progress-bar__outer) {
    background-color: rgba(59, 130, 246, 0.1);
  }
}
</style>
