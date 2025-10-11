<template>
  <el-dialog
    v-model="visible"
    title="错题复习"
    width="700px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div v-if="errorQuestion" class="review-content">
      <!-- 题目展示 -->
      <div class="question-section">
        <h3 class="section-title">题目内容</h3>
        <div class="question-content">
          {{ errorQuestion.question_content }}
        </div>
        
        <div class="question-meta">
          <el-tag :type="subjectTagType" size="small">{{ errorQuestion.subject }}</el-tag>
          <el-tag type="warning" size="small">{{ errorQuestion.error_type }}</el-tag>
          <DifficultyStars :level="errorQuestion.difficulty_level" />
        </div>
      </div>

      <!-- 答案对比 -->
      <div class="answer-section" v-if="errorQuestion.student_answer || errorQuestion.correct_answer">
        <h3 class="section-title">答案对比</h3>
        
        <div class="answer-comparison">
          <div class="answer-item" v-if="errorQuestion.student_answer">
            <div class="answer-label error">原错误答案</div>
            <div class="answer-content">{{ errorQuestion.student_answer }}</div>
          </div>
          
          <div class="answer-item" v-if="errorQuestion.correct_answer">
            <div class="answer-label correct">正确答案</div>
            <div class="answer-content">{{ errorQuestion.correct_answer }}</div>
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

      <!-- 复习表单 -->
      <div class="review-form-section">
        <h3 class="section-title">复习记录</h3>
        
        <el-form
          ref="formRef"
          :model="reviewForm"
          :rules="reviewRules"
          label-width="100px"
        >
          <el-form-item label="复习结果" prop="review_result" required>
            <el-radio-group v-model="reviewForm.review_result">
              <el-radio value="correct">完全正确</el-radio>
              <el-radio value="partial">部分正确</el-radio>
              <el-radio value="incorrect">仍然错误</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="得分" prop="score" required>
            <el-slider
              v-model="reviewForm.score"
              :max="100"
              :min="0"
              :step="5"
              show-input
              input-size="small"
              style="width: 300px;"
            />
          </el-form-item>

          <el-form-item label="用时(分钟)" prop="time_spent">
            <el-input-number
              v-model="reviewForm.time_spent_minutes"
              :min="0"
              :max="120"
              :step="1"
              size="small"
            />
          </el-form-item>

          <el-form-item label="本次答案" prop="student_answer">
            <el-input
              v-model="reviewForm.student_answer"
              type="textarea"
              :rows="3"
              placeholder="记录这次的答题内容..."
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="复习笔记" prop="notes">
            <el-input
              v-model="reviewForm.notes"
              type="textarea"
              :rows="3"
              placeholder="记录复习心得、易错点提醒等..."
              maxlength="300"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 复习历史 -->
      <div class="history-section" v-if="showHistory && reviewHistory.length > 0">
        <h3 class="section-title">
          复习历史
          <el-button 
            type="text" 
            size="small" 
            @click="showHistory = !showHistory"
          >
            {{ showHistory ? '收起' : '展开' }}
          </el-button>
        </h3>
        
        <div class="history-list">
          <div 
            v-for="record in reviewHistory" 
            :key="record.id" 
            class="history-item"
          >
            <div class="history-meta">
              <span class="history-date">{{ formatDate(record.reviewed_at) }}</span>
              <el-tag 
                :type="getResultTagType(record.review_result)" 
                size="small"
              >
                {{ getResultText(record.review_result) }}
              </el-tag>
              <span class="history-score">{{ record.score }}分</span>
            </div>
            <div v-if="record.notes" class="history-notes">{{ record.notes }}</div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          v-if="reviewHistory.length > 0"
          type="info" 
          @click="showHistory = !showHistory"
        >
          {{ showHistory ? '隐藏历史' : '查看历史' }}
        </el-button>
        <el-button 
          type="primary" 
          :loading="submitting" 
          @click="handleSubmit"
        >
          完成复习
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import DifficultyStars from '@/components/DifficultyStars.vue'
import { errorBookApi } from '@/api/errorBook'
import type { ErrorQuestion, ReviewRecord, ReviewRecordCreate } from '@/types/errorBook'

interface Props {
  modelValue: boolean
  errorQuestion: ErrorQuestion | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 状态
const formRef = ref<FormInstance>()
const submitting = ref(false)
const showHistory = ref(false)
const reviewHistory = ref<ReviewRecord[]>([])

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 复习表单
const reviewForm = reactive<ReviewRecordCreate & { time_spent_minutes?: number }>({
  review_result: 'correct',
  score: 100,
  time_spent_minutes: undefined,
  student_answer: '',
  notes: ''
})

// 表单验证规则
const reviewRules: FormRules = {
  review_result: [
    { required: true, message: '请选择复习结果', trigger: 'change' }
  ],
  score: [
    { required: true, message: '请输入得分', trigger: 'blur' },
    { type: 'number', min: 0, max: 100, message: '得分范围为0-100', trigger: 'blur' }
  ]
}

// 计算属性
const subjectTagType = computed(() => {
  if (!props.errorQuestion) return 'default'
  
  const subjectColors = {
    '数学': 'primary',
    '语文': 'success',
    '英语': 'warning',
    '物理': 'danger',
    '化学': 'info'
  }
  return subjectColors[props.errorQuestion.subject as keyof typeof subjectColors] || 'default'
})

// 方法
const handleClose = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(reviewForm, {
    review_result: 'correct',
    score: 100,
    time_spent_minutes: undefined,
    student_answer: '',
    notes: ''
  })
  showHistory.value = false
  reviewHistory.value = []
}

const handleSubmit = async () => {
  if (!formRef.value || !props.errorQuestion) return

  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    // 准备提交数据
    const submitData: ReviewRecordCreate = {
      review_result: reviewForm.review_result,
      score: reviewForm.score,
      time_spent: reviewForm.time_spent_minutes ? reviewForm.time_spent_minutes * 60 : undefined,
      student_answer: reviewForm.student_answer || undefined,
      notes: reviewForm.notes || undefined
    }
    
    await errorBookApi.createReviewRecord(props.errorQuestion.id, submitData)
    
    ElMessage.success('复习记录保存成功')
    emit('success')
    handleClose()
    
  } catch (error) {
    console.error('保存复习记录失败:', error)
    ElMessage.error('保存复习记录失败')
  } finally {
    submitting.value = false
  }
}

const loadReviewHistory = async () => {
  if (!props.errorQuestion) return
  
  try {
    // 这里需要实现获取复习历史的API
    // reviewHistory.value = await errorBookApi.getReviewHistory(props.errorQuestion.id)
    reviewHistory.value = [] // 暂时为空，等待API实现
  } catch (error) {
    console.error('加载复习历史失败:', error)
  }
}

const formatDate = (dateString: string) => {
  return format(new Date(dateString), 'yyyy-MM-dd HH:mm', { locale: zhCN })
}

const getResultTagType = (result: string) => {
  const typeMap = {
    'correct': 'success',
    'partial': 'warning',
    'incorrect': 'danger'
  }
  return typeMap[result as keyof typeof typeMap] || 'info'
}

const getResultText = (result: string) => {
  const textMap = {
    'correct': '完全正确',
    'partial': '部分正确',
    'incorrect': '仍然错误'
  }
  return textMap[result as keyof typeof textMap] || '未知'
}

// 根据复习结果自动调整得分
watch(() => reviewForm.review_result, (newResult) => {
  if (newResult === 'correct') {
    reviewForm.score = 100
  } else if (newResult === 'partial') {
    reviewForm.score = 60
  } else if (newResult === 'incorrect') {
    reviewForm.score = 0
  }
})

// 监听对话框打开，加载数据
watch(visible, (newVal) => {
  if (newVal && props.errorQuestion) {
    loadReviewHistory()
  } else if (!newVal) {
    resetForm()
  }
})
</script>

<style scoped>
.review-content {
  max-height: 70vh;
  overflow-y: auto;
}

.section-title {
  font-size: 16px;
  color: #303133;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.question-section {
  margin-bottom: 24px;
}

.question-content {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  color: #303133;
  line-height: 1.6;
  margin-bottom: 12px;
}

.question-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.answer-section {
  margin-bottom: 24px;
}

.answer-comparison {
  display: grid;
  gap: 16px;
}

.answer-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

.answer-label {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
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
  padding: 12px;
  color: #303133;
  line-height: 1.5;
}

.knowledge-section {
  margin-bottom: 24px;
}

.knowledge-points {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.review-form-section {
  margin-bottom: 24px;
}

.history-section {
  margin-bottom: 16px;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 8px;
  background: #fafafa;
}

.history-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}

.history-date {
  font-size: 13px;
  color: #909399;
}

.history-score {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.history-notes {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-slider) {
  margin-right: 16px;
}
</style>