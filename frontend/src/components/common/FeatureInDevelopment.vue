<template>
  <div class="feature-dev-container" :class="sizeClass">
    <div class="dev-icon">
      <el-icon :size="iconSize">
        <Tools />
      </el-icon>
    </div>
    <div class="dev-content">
      <h3 class="dev-title">{{ title }}</h3>
      <p class="dev-description">{{ description }}</p>
      <div v-if="showProgress" class="dev-progress">
        <el-progress :percentage="progressPercentage" :stroke-width="6" />
        <span class="progress-text">开发进度 {{ progressPercentage }}%</span>
      </div>
      <div v-if="showActions" class="dev-actions">
        <el-button type="primary" size="small" @click="handleNotify"> 通知我完成时 </el-button>
        <el-button type="default" size="small" @click="handleFeedback"> 提交需求反馈 </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Tools } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  title?: string
  description?: string
  size?: 'small' | 'medium' | 'large'
  showProgress?: boolean
  progressPercentage?: number
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '功能开发中',
  description: '我们正在加紧开发这个功能，敬请期待！',
  size: 'medium',
  showProgress: false,
  progressPercentage: 60,
  showActions: true,
})

const sizeClass = computed(() => `dev-${props.size}`)
const iconSize = computed(() => {
  switch (props.size) {
    case 'small':
      return 20
    case 'large':
      return 40
    default:
      return 30
  }
})

const handleNotify = () => {
  ElMessage.success('已添加到通知列表，功能完成时将通知您')
}

const handleFeedback = () => {
  ElMessage.info('反馈功能正在开发中，您可以通过客服联系我们')
}
</script>

<style scoped>
.feature-dev-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.feature-dev-container:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.dev-small {
  padding: 1rem;
  gap: 0.75rem;
}

.dev-large {
  padding: 2rem;
  gap: 1.5rem;
}

.dev-icon {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  animation: pulse 2s infinite;
}

.dev-small .dev-icon {
  width: 40px;
  height: 40px;
}

.dev-large .dev-icon {
  width: 80px;
  height: 80px;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.dev-content {
  flex: 1;
  min-width: 0;
}

.dev-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 0.5rem 0;
}

.dev-small .dev-title {
  font-size: 1rem;
}

.dev-large .dev-title {
  font-size: 1.25rem;
}

.dev-description {
  font-size: 0.875rem;
  color: #718096;
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

.dev-small .dev-description {
  font-size: 0.75rem;
  margin-bottom: 0.75rem;
}

.dev-large .dev-description {
  font-size: 1rem;
  margin-bottom: 1.5rem;
}

.dev-progress {
  margin-bottom: 1rem;
}

.progress-text {
  font-size: 0.75rem;
  color: #718096;
  margin-top: 0.5rem;
  display: block;
}

.dev-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.dev-small .dev-actions {
  gap: 0.5rem;
}

.dev-large .dev-actions {
  gap: 1rem;
}

/* 响应式设计 */
@media (max-width: 640px) {
  .feature-dev-container {
    flex-direction: column;
    text-align: center;
  }

  .dev-actions {
    justify-content: center;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .feature-dev-container {
    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
    border-color: #4a5568;
  }

  .feature-dev-container:hover {
    border-color: #667eea;
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
  }

  .dev-title {
    color: #f7fafc;
  }

  .dev-description {
    color: #cbd5e1;
  }
}
</style>
