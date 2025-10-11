<template>
  <el-dialog
    v-model="visible"
    title="错题详情"
    width="800px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div v-loading="loading" class="detail-content">
      <div v-if="errorQuestion">
        <!-- 基本信息 -->
        <div class="info-section">
          <div class="info-header">
            <div class="info-tags">
              <el-tag :type="subjectTagType" size="small">{{ errorQuestion.subject }}</el-tag>
              <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
              <el-tag :type="errorTypeTagType" size="small">{{ errorQuestion.error_type }}</el-tag>
            </div>
            <div class="info-stars">
              <DifficultyStars :level="errorQuestion.difficulty_level" />
            </div>
          </div>
        </div>

        <!-- 题目内容 -->
        <div class="content-section">
          <h3 class="section-title">题目内容</h3>
          <div class="question-content">
            {{ errorQuestion.question_content }}
          </div>
        </div>

        <!-- 答案对比 -->
        <div class="answer-section" v-if="errorQuestion.student_answer || errorQuestion.correct_answer">
          <h3 class="section-title">答案对比</h3>
          <div class="answer-grid">
            <div class="answer-item" v-if="errorQuestion.student_answer">
              <div class="answer-label error">学生答案</div>
              <div class="answer-content">{{ errorQuestion.student_answer }}</div>
            </div>
            <div class="answer-item" v-if="errorQuestion.correct_answer">
              <div class="answer-label correct">正确答案</div>
              <div class="answer-content">{{ errorQuestion.correct_answer }}</div>
            </div>
          </div>
        </div>

        <!-- 错误分析 -->
        <div class="analysis-section">
          <h3 class="section-title">错误分析</h3>
          <div class="analysis-grid">
            <div class="analysis-item">
              <span class="analysis-label">错误类型:</span>
              <span class="analysis-value">{{ errorQuestion.error_type }}</span>
            </div>
            <div class="analysis-item" v-if="errorQuestion.error_subcategory">
              <span class="analysis-label">子分类:</span>
              <span class="analysis-value">{{ errorQuestion.error_subcategory }}</span>
            </div>
            <div class="analysis-item">
              <span class="analysis-label">来源:</span>
              <span class="analysis-value">{{ sourceText }}</span>
            </div>
          </div>
        </div>

        <!-- 知识点 -->
        <div class="knowledge-section" v-if="errorQuestion.knowledge_points?.length">
          <h3 class="section-title">相关知识点</h3>
          <div class="knowledge-points">
            <el-tag 
              v-for="point in errorQuestion.knowledge_points" 
              :key="point" 
              type="info" 
              size="small"
            >
              {{ point }}
            </el-tag>
          </div>
        </div>

        <!-- 学习统计 -->
        <div class="stats-section">
          <h3 class="section-title">学习统计</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ errorQuestion.review_count }}</div>
              <div class="stat-label">复习次数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ errorQuestion.correct_count }}</div>
              <div class="stat-label">答对次数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ masteryRate }}%</div>
              <div class="stat-label">掌握率</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ daysSinceCreated }}</div>
              <div class="stat-label">收录天数</div>
            </div>
          </div>
        </div>

        <!-- 复习计划 -->
        <div class="schedule-section">
          <h3 class="section-title">复习计划</h3>
          <div class="schedule-info">
            <div class="schedule-item">
              <span class="schedule-label">最后复习:</span>
              <span class="schedule-value">
                {{ errorQuestion.last_review_at ? formatTime(errorQuestion.last_review_at) : '未复习' }}
              </span>
            </div>
            <div class="schedule-item">
              <span class="schedule-label">下次复习:</span>
              <span class="schedule-value" :class="{ 'overdue': errorQuestion.is_overdue }">
                {{ errorQuestion.next_review_at ? formatTime(errorQuestion.next_review_at) : '未安排' }}
                <el-tag v-if="errorQuestion.is_overdue" type="danger" size="small">逾期{{ errorQuestion.overdue_days }}天</el-tag>
              </span>
            </div>
          </div>
        </div>

        <!-- 标签 -->
        <div class="tags-section" v-if="errorQuestion.tags?.length || errorQuestion.is_starred">
          <h3 class="section-title">标签</h3>
          <div class="tags-content">
            <el-tag v-if="errorQuestion.is_starred" type="warning" size="small">
              <el-icon><Star /></el-icon>
              重点
            </el-tag>
            <el-tag 
              v-for="tag in errorQuestion.tags" 
              :key="tag" 
              size="small"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>

        <!-- 时间信息 -->
        <div class="time-section">
          <div class="time-info">
            <span class="time-item">创建时间: {{ formatTime(errorQuestion.created_at) }}</span>
            <span class="time-item">更新时间: {{ formatTime(errorQuestion.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button 
          v-if="errorQuestion && errorQuestion.mastery_status !== 'mastered'"
          type="primary" 
          @click="startReview"
        >
          开始复习
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Star } from '@element-plus/icons-vue'
import { formatDistanceToNow, differenceInDays } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import DifficultyStars from '@/components/DifficultyStars.vue'
import { errorBookApi } from '@/api/errorBook'
import type { ErrorQuestion } from '@/types/errorBook'

interface Props {
  modelValue: boolean
  errorQuestionId: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'start-review', question: ErrorQuestion): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 状态
const loading = ref(false)
const errorQuestion = ref<ErrorQuestion | null>(null)

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 计算属性
const statusText = computed(() => {
  if (!errorQuestion.value) return ''
  const statusMap = {
    'learning': '学习中',
    'reviewing': '复习中',
    'mastered': '已掌握'
  }
  return statusMap[errorQuestion.value.mastery_status as keyof typeof statusMap] || '未知'
})

const statusTagType = computed(() => {
  if (!errorQuestion.value) return 'info'
  const typeMap = {
    'learning': 'danger',
    'reviewing': 'warning',
    'mastered': 'success'
  }
  return typeMap[errorQuestion.value.mastery_status as keyof typeof typeMap] || 'info'
})

const subjectTagType = computed(() => {
  if (!errorQuestion.value) return 'default'
  const subjectColors = {
    '数学': 'primary',
    '语文': 'success',
    '英语': 'warning',
    '物理': 'danger',
    '化学': 'info'
  }
  return subjectColors[errorQuestion.value.subject as keyof typeof subjectColors] || 'default'
})

const errorTypeTagType = computed(() => {
  if (!errorQuestion.value) return 'default'
  const typeColors = {
    '理解错误': 'danger',
    '方法错误': 'warning',
    '计算错误': 'info',
    '表达错误': 'success'
  }
  return typeColors[errorQuestion.value.error_type as keyof typeof typeColors] || 'default'
})

const sourceText = computed(() => {
  if (!errorQuestion.value) return ''
  return errorQuestion.value.source_type === 'homework' ? '作业批改' : '手动添加'
})

const masteryRate = computed(() => {
  if (!errorQuestion.value) return 0
  return Math.round(errorQuestion.value.mastery_rate * 100)
})

const daysSinceCreated = computed(() => {
  if (!errorQuestion.value) return 0
  return differenceInDays(new Date(), new Date(errorQuestion.value.created_at))
})

// 方法
const handleClose = () => {
  visible.value = false
  errorQuestion.value = null
}

const loadErrorQuestion = async () => {
  if (!props.errorQuestionId) return

  try {
    loading.value = true
    errorQuestion.value = await errorBookApi.getErrorQuestion(props.errorQuestionId)
  } catch (error) {
    console.error('加载错题详情失败:', error)
    ElMessage.error('加载错题详情失败')
    handleClose()
  } finally {
    loading.value = false
  }
}

const startReview = () => {
  if (errorQuestion.value) {
    emit('start-review', errorQuestion.value)
    handleClose()
  }
}

const formatTime = (time: string) => {
  return formatDistanceToNow(new Date(time), { locale: zhCN, addSuffix: true })
}

// 监听对话框打开，加载数据
watch(visible, (newVal) => {
  if (newVal && props.errorQuestionId) {
    loadErrorQuestion()
  }
})

watch(() => props.errorQuestionId, (newId) => {
  if (visible.value && newId) {
    loadErrorQuestion()
  }
})
</script>

<style scoped>
.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.section-title {
  font-size: 16px;
  color: #303133;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
  font-weight: 600;
}

.info-section {
  margin-bottom: 24px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
}

.info-tags {
  display: flex;
  gap: 8px;
}

.content-section {
  margin-bottom: 24px;
}

.question-content {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
  color: #303133;
  line-height: 1.8;
  font-size: 15px;
}

.answer-section {
  margin-bottom: 24px;
}

.answer-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.answer-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.answer-label {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
}

.answer-label.error {
  background: #fef0f0;
  color: #f56c6c;
}

.answer-label.correct {
  background: #f0f9ff;
  color: #409eff;
}

.answer-content {
  padding: 16px;
  color: #303133;
  line-height: 1.6;
  min-height: 60px;
}

.analysis-section {
  margin-bottom: 24px;
}

.analysis-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.analysis-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 6px;
}

.analysis-label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.analysis-value {
  color: #303133;
}

.knowledge-section {
  margin-bottom: 24px;
}

.knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stats-section {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}

.schedule-section {
  margin-bottom: 24px;
}

.schedule-info {
  display: grid;
  gap: 12px;
}

.schedule-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 6px;
}

.schedule-label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.schedule-value {
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.schedule-value.overdue {
  color: #f56c6c;
}

.tags-section {
  margin-bottom: 24px;
}

.tags-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.time-section {
  margin-bottom: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.time-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #909399;
}

.time-item {
  flex: 1;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .info-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .answer-grid {
    grid-template-columns: 1fr;
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .time-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style>