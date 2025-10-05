<template>
  <div class="api-status-monitor">
    <div class="status-header">
      <el-icon :size="16" class="status-icon">
        <Warning />
      </el-icon>
      <span class="status-title">API 状态监控</span>
      <el-badge :value="failedCount" :hidden="failedCount === 0" type="danger" />
    </div>

    <div class="status-list">
      <div
        v-for="(status, key) in apiStatuses"
        :key="key"
        class="status-item"
        :class="status.status"
      >
        <div class="status-indicator">
          <div class="indicator-dot" :class="status.status"></div>
        </div>
        <div class="status-info">
          <span class="api-name">{{ status.name }}</span>
          <span class="api-message">{{ status.message }}</span>
        </div>
        <div class="status-actions">
          <el-button
            v-if="status.status === 'error'"
            size="small"
            type="text"
            @click="retryApi(key)"
            :loading="status.retrying"
          >
            重试
          </el-button>
        </div>
      </div>
    </div>

    <div v-if="showGlobalActions" class="global-actions">
      <el-button type="primary" size="small" @click="retryAllFailed">
        重试所有失败的 API
      </el-button>
      <el-button type="default" size="small" @click="clearErrors"> 清除错误 </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface ApiStatus {
  name: string
  status: 'success' | 'error' | 'loading' | 'development'
  message: string
  retrying?: boolean
  lastTried?: Date
}

interface Props {
  statuses: Record<string, ApiStatus>
  showGlobalActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showGlobalActions: true,
})

const emit = defineEmits<{
  retry: [apiKey: string]
  retryAll: []
  clearErrors: []
}>()

const apiStatuses = ref<Record<string, ApiStatus>>({ ...props.statuses })

const failedCount = computed(
  () => Object.values(apiStatuses.value).filter((status) => status.status === 'error').length
)

// 监听外部状态变化
watch(
  () => props.statuses,
  (newStatuses) => {
    apiStatuses.value = { ...newStatuses }
  },
  { deep: true }
)

const retryApi = async (apiKey: string) => {
  const status = apiStatuses.value[apiKey]
  if (status) {
    status.retrying = true
    status.lastTried = new Date()

    try {
      emit('retry', apiKey)
      // 模拟重试延迟
      await new Promise((resolve) => setTimeout(resolve, 1000))

      status.status = 'success'
      status.message = '重试成功'
      ElMessage.success(`${status.name} 重试成功`)
    } catch (error) {
      status.status = 'error'
      status.message = '重试失败'
      ElMessage.error(`${status.name} 重试失败`)
    } finally {
      status.retrying = false
    }
  }
}

const retryAllFailed = () => {
  const failedApis = Object.entries(apiStatuses.value)
    .filter(([, status]) => status.status === 'error')
    .map(([key]) => key)

  failedApis.forEach((key) => retryApi(key))
  emit('retryAll')
}

const clearErrors = () => {
  Object.values(apiStatuses.value).forEach((status) => {
    if (status.status === 'error') {
      status.status = 'development'
      status.message = '功能开发中'
    }
  })
  emit('clearErrors')
}
</script>

<style scoped>
.api-status-monitor {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.status-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.status-icon {
  color: #f59e0b;
}

.status-title {
  font-weight: 600;
  color: #2d3748;
}

.status-list {
  max-height: 300px;
  overflow-y: auto;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f7fafc;
  transition: background-color 0.2s ease;
}

.status-item:hover {
  background: #f8fafc;
}

.status-item:last-child {
  border-bottom: none;
}

.status-indicator {
  flex-shrink: 0;
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.indicator-dot.success {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
}

.indicator-dot.error {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.indicator-dot.loading {
  background: #3b82f6;
  animation: pulse 1.5s infinite;
}

.indicator-dot.development {
  background: #f59e0b;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.2);
  }
}

.status-info {
  flex: 1;
  min-width: 0;
}

.api-name {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #2d3748;
}

.api-message {
  display: block;
  font-size: 0.75rem;
  color: #718096;
  margin-top: 0.25rem;
}

.status-actions {
  flex-shrink: 0;
}

.global-actions {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .api-status-monitor {
    background: rgba(45, 55, 72, 0.95);
    border-color: #4a5568;
  }

  .status-header,
  .global-actions {
    background: #2d3748;
    border-color: #4a5568;
  }

  .status-title,
  .api-name {
    color: #f7fafc;
  }

  .api-message {
    color: #cbd5e1;
  }

  .status-item:hover {
    background: #374151;
  }
}
</style>
