<template>
  <div
    class="chat-message"
    :class="{
      'is-user': message.type === 'user',
      'is-ai': message.type === 'ai',
      'is-processing': message.status === 'sending',
      'is-failed': message.status === 'failed',
    }"
  >
    <!-- AI Avatar -->
    <div v-if="message.type === 'ai'" class="message-avatar">
      <div class="avatar-container ai-avatar">
        <el-icon><ChatDotRound /></el-icon>
      </div>
    </div>

    <!-- Message Content -->
    <div class="message-content-wrapper">
      <!-- Message Bubble -->
      <div class="message-bubble" :class="getBubbleClass()">
        <!-- Message Status Indicator -->
        <div v-if="showStatus" class="message-status">
          <el-icon
            v-if="message.status === 'sending'"
            class="status-icon sending"
          >
            <Loading />
          </el-icon>
          <el-icon
            v-else-if="message.status === 'sent'"
            class="status-icon sent"
          >
            <Select />
          </el-icon>
          <el-icon
            v-else-if="message.status === 'failed'"
            class="status-icon failed"
          >
            <Warning />
          </el-icon>
        </div>

        <!-- Message Content -->
        <div class="message-text">
          <!-- User Message -->
          <div v-if="message.type === 'user'" class="user-content">
            <p class="text-content">{{ message.content }}</p>
          </div>

          <!-- AI Message -->
          <div v-else-if="message.type === 'ai'" class="ai-content">
            <!-- Typing Animation -->
            <div v-if="isTyping" class="typing-container">
              <TypingIndicator
                :text="message.content"
                @complete="onTypingComplete"
              />
            </div>

            <!-- Rendered Content -->
            <div v-else class="rendered-content">
              <MarkdownRenderer :content="message.content" />
            </div>
          </div>
        </div>

        <!-- Message Metadata -->
        <div v-if="showMetadata" class="message-metadata">
          <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
          <el-tag
            v-if="message.subject"
            size="small"
            :color="getSubjectColor(message.subject)"
          >
            {{ getSubjectLabel(message.subject) }}
          </el-tag>
        </div>
      </div>

      <!-- Message Actions -->
      <div v-if="showActions && message.type === 'ai'" class="message-actions">
        <el-button type="text" size="small" @click="$emit('copy', message)">
          <el-icon><CopyDocument /></el-icon>
        </el-button>
        <el-button
          type="text"
          size="small"
          @click="$emit('regenerate', message)"
        >
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button type="text" size="small" @click="$emit('feedback', message)">
          <el-icon><Star /></el-icon>
        </el-button>
      </div>

      <!-- Retry Button for Failed Messages -->
      <div v-if="message.status === 'failed'" class="retry-section">
        <el-button type="primary" size="small" @click="$emit('retry', message)">
          <el-icon><Refresh /></el-icon>
          重试发送
        </el-button>
      </div>
    </div>

    <!-- User Avatar -->
    <div v-if="message.type === 'user'" class="message-avatar">
      <div class="avatar-container user-avatar">
        <el-icon><User /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/zh-cn";
import TypingIndicator from "./TypingIndicator.vue";
import MarkdownRenderer from "./MarkdownRenderer.vue";
import type { ChatMessage } from "@/types";

interface Props {
  message: ChatMessage;
  showTimestamp?: boolean;
  showActions?: boolean;
  isTyping?: boolean;
}

interface Emits {
  (e: "copy", message: ChatMessage): void;
  (e: "regenerate", message: ChatMessage): void;
  (e: "feedback", message: ChatMessage): void;
  (e: "retry", message: ChatMessage): void;
  (e: "typing-complete"): void;
}

const props = withDefaults(defineProps<Props>(), {
  showTimestamp: false,
  showActions: true,
  isTyping: false,
});

const emit = defineEmits<Emits>();

const showStatus = computed(() => {
  return props.message.type === "user" && props.message.status !== "sent";
});

const showMetadata = computed(() => {
  return props.showTimestamp || props.message.subject;
});

const showActions = computed(() => {
  return (
    props.showActions &&
    props.message.type === "ai" &&
    props.message.status === "sent" &&
    !props.isTyping
  );
});

const getBubbleClass = () => {
  const classes = [];

  if (props.message.type === "user") {
    classes.push("user-bubble");
  } else {
    classes.push("ai-bubble");
  }

  if (props.message.status === "sending") {
    classes.push("sending");
  } else if (props.message.status === "failed") {
    classes.push("failed");
  }

  return classes.join(" ");
};

const formatTime = (timestamp: Date) => {
  dayjs.extend(relativeTime);
  dayjs.locale("zh-cn");
  return dayjs(timestamp).fromNow();
};

const getSubjectColor = (subject: string) => {
  const colors: Record<string, string> = {
    math: "#f56565",
    chinese: "#48bb78",
    english: "#4299e1",
    physics: "#9f7aea",
    chemistry: "#ed8936",
    biology: "#38b2ac",
    history: "#ecc94b",
    geography: "#4fd1c7",
  };
  return colors[subject] || "#a0aec0";
};

const getSubjectLabel = (subject: string) => {
  const labels: Record<string, string> = {
    math: "数学",
    chinese: "语文",
    english: "英语",
    physics: "物理",
    chemistry: "化学",
    biology: "生物",
    history: "历史",
    geography: "地理",
  };
  return labels[subject] || subject;
};

const onTypingComplete = () => {
  emit("typing-complete");
};
</script>

<style scoped lang="scss">
.chat-message {
  /* @apply flex items-end space-x-3 mb-4; */
  display: flex;
  align-items: flex-end;
  margin-bottom: 1rem;
  animation: messageSlideIn 0.3s ease-out;

  &.is-user {
    /* @apply flex-row-reverse space-x-reverse; */
    flex-direction: row-reverse;
  }

  &.is-processing {
    /* @apply opacity-75; */
    opacity: 0.75;
  }
}

.message-avatar {
  /* @apply flex-shrink-0; */
  flex-shrink: 0;

  .avatar-container {
    /* @apply w-10 h-10 rounded-full flex items-center justify-center text-white text-lg; */
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.125rem;

    &.ai-avatar {
      /* @apply bg-gradient-to-br from-blue-500 to-purple-600; */
      background: linear-gradient(to bottom right, #3b82f6, #9333ea);
    }

    &.user-avatar {
      /* @apply bg-gradient-to-br from-green-500 to-blue-500; */
      background: linear-gradient(to bottom right, #10b981, #3b82f6);
    }
  }
}

.message-content-wrapper {
  /* @apply flex-1 max-w-3xl; */
  flex: 1;
  max-width: 48rem;
}

.message-bubble {
  /* @apply relative rounded-2xl px-4 py-3 shadow-sm transition-all duration-200; */
  position: relative;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;

  &.user-bubble {
    /* @apply bg-blue-500 text-white ml-12; */
    background-color: #3b82f6;
    color: white;
    margin-left: 3rem;
    border-bottom-right-radius: 0.375rem;
  }

  &.ai-bubble {
    /* @apply bg-white border border-gray-200 mr-12; */
    background-color: white;
    border: 1px solid #e5e7eb;
    margin-right: 3rem;
    border-bottom-left-radius: 0.375rem;

    &:hover {
      /* @apply border-gray-300 shadow-md; */
      border-color: #d1d5db;
      box-shadow:
        0 4px 6px -1px rgba(0, 0, 0, 0.1),
        0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
  }

  &.sending {
    /* @apply animate-pulse; */
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  &.failed {
    /* @apply border-red-300 bg-red-50; */
    border-color: #fca5a5;
    background-color: #fef2f2;
  }
}

.message-status {
  /* @apply absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-xs; */
  position: absolute;
  top: -0.25rem;
  right: -0.25rem;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;

  .status-icon {
    /* @apply w-4 h-4; */
    width: 1rem;
    height: 1rem;

    &.sending {
      /* @apply text-blue-500 animate-spin; */
      color: #3b82f6;
      animation: spin 1s linear infinite;
    }

    &.sent {
      /* @apply text-green-500; */
      color: #22c55e;
    }

    &.failed {
      /* @apply text-red-500; */
      color: #ef4444;
    }
  }
}

.message-text {
  /* @apply w-full; */
  width: 100%;
}

.user-content {
  .text-content {
    /* @apply text-white text-sm leading-relaxed; */
    color: white;
    font-size: 0.875rem;
    line-height: 1.625;
    word-wrap: break-word;
  }
}

.ai-content {
  /* @apply text-gray-800; */
  color: #1f2937;
}

.typing-container {
  /* @apply min-h-6; */
  min-height: 1.5rem;
}

.rendered-content {
  /* @apply prose prose-sm max-w-none; */
  max-width: none;
}

.message-metadata {
  /* @apply flex items-center justify-between mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500; */
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f3f4f6;
  font-size: 0.75rem;
  color: #6b7280;

  .timestamp {
    /* @apply text-gray-400; */
    color: #9ca3af;
  }
}

.message-actions {
  /* @apply flex items-center space-x-2 mt-2 opacity-0 transition-opacity duration-200; */
  display: flex;
  align-items: center;
  margin-top: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease;

  .chat-message:hover & {
    /* @apply opacity-100; */
    opacity: 1;
  }

  .el-button {
    /* @apply text-gray-400 hover:text-gray-600; */
    color: #9ca3af;
  }

  .el-button:hover {
    color: #4b5563;
  }
}

.retry-section {
  /* @apply mt-2 flex justify-center; */
  margin-top: 0.5rem;
  display: flex;
  justify-content: center;
}

@keyframes messageSlideIn {
  from {
    transform: translateY(10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

// 移动端适配
@media (max-width: 768px) {
  .message-bubble {
    &.user-bubble {
      /* @apply ml-6; */
      margin-left: 1.5rem;
    }

    &.ai-bubble {
      /* @apply mr-6; */
      margin-right: 1.5rem;
    }
  }

  .message-avatar {
    .avatar-container {
      /* @apply w-8 h-8 text-base; */
      width: 2rem;
      height: 2rem;
      font-size: 1rem;
    }
  }
}
</style>
