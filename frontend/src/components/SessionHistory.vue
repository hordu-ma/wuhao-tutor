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
            :loading="isLoading"
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
              <el-dropdown-item command="active">活跃会话</el-dropdown-item>
              <el-dropdown-item command="archived">已归档</el-dropdown-item>
              <el-dropdown-item command="recent">最近7天</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <!-- 筛选标签 -->
      <div v-if="currentFilter !== 'all'" class="mt-2">
        <el-tag
          closable
          size="small"
          @close="currentFilter = 'all'"
          class="filter-tag"
        >
          {{ getFilterLabel(currentFilter) }}
        </el-tag>
      </div>
    </div>

    <!-- 会话列表 -->
    <div class="sessions-list flex-1 overflow-y-auto">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-container p-4">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 空状态 -->
      <div
        v-else-if="filteredSessions.length === 0"
        class="empty-state p-6 text-center"
      >
        <el-icon class="text-4xl text-gray-300 mb-3">
          <ChatDotRound />
        </el-icon>
        <p class="text-gray-500 mb-4">
          {{ searchKeyword ? "没有找到匹配的会话" : "还没有学习会话" }}
        </p>
        <el-button
          v-if="!searchKeyword"
          type="primary"
          @click="$emit('create-session')"
        >
          创建第一个会话
        </el-button>
      </div>

      <!-- 会话项列表 -->
      <div v-else class="sessions-container">
        <div
          v-for="session in filteredSessions"
          :key="session.id"
          class="session-item p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors"
          :class="{
            active: session.id === currentSessionId,
            archived: session.status === 'archived',
          }"
          @click="selectSession(session.id)"
        >
          <!-- 会话头部 -->
          <div class="session-header flex items-start justify-between mb-2">
            <div class="session-info flex-1 min-w-0">
              <h4
                class="session-title text-sm font-medium text-gray-900 truncate"
              >
                {{ session.title }}
              </h4>
              <div class="session-meta flex items-center space-x-2 mt-1">
                <span class="text-xs text-gray-500">
                  {{ formatTime(session.last_active_at || session.created_at) }}
                </span>
                <el-tag
                  v-if="session.subject"
                  size="small"
                  :color="getSubjectColor(session.subject)"
                  class="text-xs"
                >
                  {{ getSubjectLabel(session.subject) }}
                </el-tag>
              </div>
            </div>

            <!-- 会话状态 -->
            <div class="session-status flex items-center space-x-1">
              <el-icon
                v-if="session.status === 'archived'"
                class="text-gray-400"
                title="已归档"
              >
                <FolderOpened />
              </el-icon>
              <el-icon
                v-else-if="session.id === currentSessionId"
                class="text-green-500"
                title="当前会话"
              >
                <CircleCheckFilled />
              </el-icon>
              <el-dropdown
                @command="(cmd) => handleSessionAction(cmd, session)"
                trigger="click"
                placement="bottom-end"
              >
                <el-button type="text" size="small" class="session-menu">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-if="session.status !== 'archived'"
                      command="archive"
                    >
                      <el-icon><FolderOpened /></el-icon>
                      归档
                    </el-dropdown-item>
                    <el-dropdown-item
                      v-if="session.status === 'archived'"
                      command="unarchive"
                    >
                      <el-icon><FolderAdd /></el-icon>
                      取消归档
                    </el-dropdown-item>
                    <el-dropdown-item command="export">
                      <el-icon><Download /></el-icon>
                      导出
                    </el-dropdown-item>
                    <el-dropdown-item command="duplicate">
                      <el-icon><CopyDocument /></el-icon>
                      复制
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
          </div>

          <!-- 会话预览 -->
          <div v-if="session.question_count > 0" class="session-preview">
            <p class="text-xs text-gray-600 line-clamp-2">
              {{ session.question_count }} 个问题
            </p>
          </div>

          <!-- 会话统计 -->
          <div
            class="session-stats flex items-center justify-between mt-2 text-xs text-gray-500"
          >
            <span>{{ session.question_count || 0 }} 个问题</span>
            <span v-if="session.total_tokens"
              >{{ formatTokens(session.total_tokens) }} tokens</span
            >
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="footer p-4 border-t border-gray-200 bg-gray-50">
      <div class="flex items-center justify-between text-xs text-gray-500">
        <span>共 {{ sessions.length }} 个会话</span>
        <el-button
          type="text"
          size="small"
          @click="$emit('close-drawer')"
          class="text-gray-500"
        >
          <el-icon><Close /></el-icon>
          关闭
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search,
  Plus,
  Refresh,
  Filter,
  ChatDotRound,
  FolderOpened,
  FolderAdd,
  CircleCheckFilled,
  MoreFilled,
  Download,
  CopyDocument,
  Delete,
  Close,
} from "@element-plus/icons-vue";
import { useLearningStore } from "@/stores/learning";
import type { ChatSession } from "@/types/learning";
import { LEARNING_SUBJECT_OPTIONS, SessionStatus } from "@/types/learning";

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
const searchKeyword = ref("");
const currentFilter = ref("all");
const isLoading = ref(false);

// ========== 计算属性 ==========
const sessions = computed(() => learningStore.chatState.sessions || []);
const currentSessionId = computed(
  () => learningStore.chatState.currentSession?.id,
);

const filteredSessions = computed(() => {
  let result = sessions.value;

  // 搜索过滤
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(
      (session: ChatSession) =>
        session.title.toLowerCase().includes(keyword) ||
        session.subject?.toLowerCase().includes(keyword),
    );
  }

  // 状态过滤
  switch (currentFilter.value) {
    case "active":
      result = result.filter(
        (session: ChatSession) => session.status !== "archived",
      );
      break;
    case "archived":
      result = result.filter(
        (session: ChatSession) => session.status === "archived",
      );
      break;
    case "recent":
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      result = result.filter(
        (session: ChatSession) =>
          new Date(session.updated_at || session.created_at) > weekAgo,
      );
      break;
  }

  // 按更新时间倒序排列
  return [...result].sort(
    (a: ChatSession, b: ChatSession) =>
      new Date(b.updated_at || b.created_at).getTime() -
      new Date(a.updated_at || a.created_at).getTime(),
  );
});

// ========== 工具函数 ==========
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
      hour: "2-digit",
      minute: "2-digit",
    });
  }
};

const formatTokens = (tokens: number) => {
  if (tokens < 1000) return `${tokens}`;
  if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}K`;
  return `${(tokens / 1000000).toFixed(1)}M`;
};

const getSubjectColor = (subject: string) => {
  const option = LEARNING_SUBJECT_OPTIONS.find((opt) => opt.value === subject);
  return option?.color || "#gray";
};

const getSubjectLabel = (subject: string) => {
  const option = LEARNING_SUBJECT_OPTIONS.find((opt) => opt.value === subject);
  return option?.label || subject;
};

const getFilterLabel = (filter: string) => {
  const labels: Record<string, string> = {
    active: "活跃会话",
    archived: "已归档",
    recent: "最近7天",
  };
  return labels[filter] || filter;
};

// ========== 事件处理 ==========
const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
};

const handleRefresh = async () => {
  isLoading.value = true;
  try {
    await learningStore.loadSessions();
  } catch (error) {
    console.error("刷新会话列表失败:", error);
    ElMessage.error("刷新失败");
  } finally {
    isLoading.value = false;
  }
};

const handleFilterCommand = (command: string) => {
  currentFilter.value = command;
};

const selectSession = (sessionId: string) => {
  emit("select-session", sessionId);
};

const handleSessionAction = async (action: string, session: ChatSession) => {
  try {
    switch (action) {
      case "archive":
        await learningStore.archiveSession(session.id);
        ElMessage.success("会话已归档");
        break;

      case "unarchive":
        await learningStore.updateSession(session.id, {
          status: SessionStatus.ACTIVE,
        });
        ElMessage.success("已取消归档");
        break;

      case "export":
        // TODO: 实现导出功能
        ElMessage.info("导出功能开发中...");
        break;

      case "duplicate":
        // TODO: 实现复制功能
        ElMessage.info("复制功能开发中...");
        break;

      case "delete":
        await ElMessageBox.confirm(
          `确定要删除会话"${session.title}"吗？删除后无法恢复。`,
          "确认删除",
          { type: "error" },
        );
        await learningStore.deleteSession(session.id);
        ElMessage.success("会话已删除");
        break;
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("操作失败:", error);
      ElMessage.error("操作失败");
    }
  }
};

// ========== 生命周期 ==========
onMounted(async () => {
  if (sessions.value.length === 0) {
    await handleRefresh();
  }
});
</script>

<style scoped lang="scss">
.session-history {
  .filter-tag {
    background-color: #e1f5fe;
    color: #0277bd;
    border-color: #81d4fa;
  }

  .sessions-list {
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
    position: relative;
    transition: all 0.2s ease;

    &:hover {
      transform: translateX(2px);
      box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
    }

    &.active {
      background-color: #eff6ff;
      border-left: 3px solid #3b82f6;

      .session-title {
        color: #1d4ed8;
        font-weight: 600;
      }
    }

    &.archived {
      opacity: 0.7;

      .session-title {
        text-decoration: line-through;
        color: #6b7280;
      }
    }

    .session-menu {
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    &:hover .session-menu {
      opacity: 1;
    }
  }

  .session-title {
    line-height: 1.4;
  }

  .session-preview {
    p {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      line-clamp: 2;
      overflow: hidden;
    }
  }

  .empty-state {
    .el-icon {
      animation: float 3s ease-in-out infinite;
    }
  }

  .footer {
    background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
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

// 响应式设计
@media (max-width: 400px) {
  .session-history {
    .header {
      padding: 0.75rem;
    }

    .session-item {
      padding: 0.75rem;
    }

    .session-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }
}
</style>
