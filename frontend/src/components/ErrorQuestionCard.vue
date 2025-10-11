<template>
  <el-card class="error-question-card" :class="statusClass" shadow="hover">
    <!-- 卡片头部 -->
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <el-tag :type="subjectTagType" size="small">{{ errorQuestion.subject }}</el-tag>
          <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand" trigger="click">
            <el-icon class="more-icon"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="review" :disabled="errorQuestion.mastery_status === 'mastered'">
                  <el-icon><Refresh /></el-icon>
                  开始复习
                </el-dropdown-item>
                <el-dropdown-item command="detail">
                  <el-icon><View /></el-icon>
                  查看详情
                </el-dropdown-item>
                <el-dropdown-item command="edit">
                  <el-icon><Edit /></el-icon>
                  编辑错题
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon>
                  删除错题
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </template>

    <!-- 卡片内容 -->
    <div class="card-content">
      <!-- 题目预览 -->
      <div class="question-preview">
        <h4 class="question-title">题目内容</h4>
        <div class="question-text" :title="errorQuestion.question_content">
          {{ questionPreview }}
        </div>
      </div>

      <!-- 错误分析 -->
      <div class="error-analysis">
        <div class="analysis-item">
          <span class="label">错误类型:</span>
          <el-tag size="small" :type="errorTypeTagType">{{ errorQuestion.error_type }}</el-tag>
        </div>
        
        <div class="analysis-item" v-if="errorQuestion.knowledge_points?.length">
          <span class="label">知识点:</span>
          <div class="knowledge-points">
            <el-tag 
              v-for="point in errorQuestion.knowledge_points.slice(0, 3)" 
              :key="point" 
              size="small" 
              type="info"
            >
              {{ point }}
            </el-tag>
            <span v-if="errorQuestion.knowledge_points.length > 3" class="more-points">
              +{{ errorQuestion.knowledge_points.length - 3 }}
            </span>
          </div>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-section">
        <div class="stat-item">
          <el-icon><RefreshRight /></el-icon>
          <span>复习{{ errorQuestion.review_count }}次</span>
        </div>
        
        <div class="stat-item">
          <el-icon><Trophy /></el-icon>
          <span>正确率{{ masteryRate }}%</span>
        </div>
        
        <div class="stat-item">
          <DifficultyStars :level="errorQuestion.difficulty_level" />
        </div>
      </div>

      <!-- 复习提醒 -->
      <div class="review-reminder" v-if="showReviewReminder">
        <div class="reminder-content" :class="reminderClass">
          <el-icon class="reminder-icon">
            <component :is="reminderIcon" />
          </el-icon>
          <span class="reminder-text">{{ reminderText }}</span>
        </div>
      </div>
    </div>

    <!-- 卡片底部操作 -->
    <template #footer>
      <div class="card-footer">
        <div class="footer-left">
          <span class="created-time">{{ formatTime(errorQuestion.created_at) }}</span>
        </div>
        
        <div class="footer-right">
          <el-button 
            v-if="errorQuestion.mastery_status !== 'mastered'" 
            type="primary" 
            size="small"
            @click="$emit('review', errorQuestion)"
          >
            开始复习
          </el-button>
          
          <el-button 
            size="small"
            @click="$emit('view-detail', errorQuestion)"
          >
            查看详情
          </el-button>
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  MoreFilled, 
  Refresh, 
  View, 
  Edit, 
  Delete, 
  RefreshRight, 
  Trophy,
  Clock,
  Warning,
  CircleCheck
} from '@element-plus/icons-vue'
import DifficultyStars from '@/components/DifficultyStars.vue'
import type { ErrorQuestion } from '@/types/errorBook'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface Props {
  errorQuestion: ErrorQuestion
}

interface Emits {
  (e: 'review', question: ErrorQuestion): void
  (e: 'edit', question: ErrorQuestion): void
  (e: 'delete', question: ErrorQuestion): void
  (e: 'view-detail', question: ErrorQuestion): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算属性
const statusClass = computed(() => {
  return `status-${props.errorQuestion.mastery_status}`
})

const statusText = computed(() => {
  const statusMap = {
    'learning': '学习中',
    'reviewing': '复习中',
    'mastered': '已掌握'
  }
  return statusMap[props.errorQuestion.mastery_status as keyof typeof statusMap] || '未知'
})

const statusTagType = computed(() => {
  const typeMap = {
    'learning': 'danger',
    'reviewing': 'warning',
    'mastered': 'success'
  }
  return typeMap[props.errorQuestion.mastery_status as keyof typeof typeMap] || 'info'
})

const subjectTagType = computed(() => {
  const subjectColors = {
    '数学': 'primary',
    '语文': 'success',
    '英语': 'warning',
    '物理': 'danger',
    '化学': 'info'
  }
  return subjectColors[props.errorQuestion.subject as keyof typeof subjectColors] || 'default'
})

const errorTypeTagType = computed(() => {
  const typeColors = {
    '理解错误': 'danger',
    '方法错误': 'warning',
    '计算错误': 'info',
    '表达错误': 'success'
  }
  return typeColors[props.errorQuestion.error_type as keyof typeof typeColors] || 'default'
})

const questionPreview = computed(() => {
  const content = props.errorQuestion.question_content
  return content.length > 120 ? content.substring(0, 120) + '...' : content
})

const masteryRate = computed(() => {
  return Math.round(props.errorQuestion.mastery_rate * 100)
})

const showReviewReminder = computed(() => {
  return props.errorQuestion.is_overdue || props.errorQuestion.next_review_at
})

const reminderClass = computed(() => {
  if (props.errorQuestion.is_overdue) return 'overdue'
  if (props.errorQuestion.next_review_at) return 'scheduled'
  return ''
})

const reminderIcon = computed(() => {
  if (props.errorQuestion.is_overdue) return Warning
  if (props.errorQuestion.mastery_status === 'mastered') return CircleCheck
  return Clock
})

const reminderText = computed(() => {
  if (props.errorQuestion.is_overdue) {
    return `逾期${props.errorQuestion.overdue_days}天`
  }
  if (props.errorQuestion.next_review_at) {
    const nextReviewDate = new Date(props.errorQuestion.next_review_at)
    return `下次复习: ${formatDistanceToNow(nextReviewDate, { locale: zhCN, addSuffix: true })}`
  }
  return ''
})

// 方法
const handleCommand = (command: string) => {
  switch (command) {
    case 'review':
      emit('review', props.errorQuestion)
      break
    case 'detail':
      emit('view-detail', props.errorQuestion)
      break
    case 'edit':
      emit('edit', props.errorQuestion)
      break
    case 'delete':
      emit('delete', props.errorQuestion)
      break
  }
}

const formatTime = (time: string) => {
  return formatDistanceToNow(new Date(time), { locale: zhCN, addSuffix: true })
}
</script>

<style scoped>
.error-question-card {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.error-question-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.status-learning {
  border-left: 4px solid #f56c6c;
}

.status-reviewing {
  border-left: 4px solid #e6a23c;
}

.status-mastered {
  border-left: 4px solid #67c23a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: -10px 0;
}

.header-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.more-icon {
  cursor: pointer;
  color: #909399;
  transition: color 0.3s;
}

.more-icon:hover {
  color: #409eff;
}

.card-content {
  padding: 0;
}

.question-preview {
  margin-bottom: 16px;
}

.question-title {
  font-size: 14px;
  color: #909399;
  margin: 0 0 8px 0;
  font-weight: normal;
}

.question-text {
  font-size: 15px;
  color: #303133;
  line-height: 1.6;
  word-break: break-word;
}

.error-analysis {
  margin-bottom: 16px;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.analysis-item:last-child {
  margin-bottom: 0;
}

.label {
  font-size: 13px;
  color: #606266;
  min-width: 70px;
}

.knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.more-points {
  font-size: 12px;
  color: #909399;
}

.stats-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.review-reminder {
  margin-bottom: 8px;
}

.reminder-content {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.reminder-content.overdue {
  background: #fef0f0;
  color: #f56c6c;
}

.reminder-content.scheduled {
  background: #f0f9ff;
  color: #409eff;
}

.reminder-icon {
  font-size: 14px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: -10px 0;
}

.created-time {
  font-size: 12px;
  color: #909399;
}

.footer-right {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .stats-section {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .card-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .footer-right {
    justify-content: center;
  }
}
</style>