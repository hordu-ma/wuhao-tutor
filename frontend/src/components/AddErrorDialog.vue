<template>
  <el-dialog
    v-model="visible"
    title="添加错题"
    width="600px"
    :before-close="handleClose"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      label-position="left"
    >
      <el-form-item label="学科" prop="subject" required>
        <el-select v-model="form.subject" placeholder="请选择学科" style="width: 100%">
          <el-option v-for="subject in subjects" :key="subject.value" :label="subject.label" :value="subject.value" />
        </el-select>
      </el-form-item>

      <el-form-item label="题目内容" prop="question_content" required>
        <el-input
          v-model="form.question_content"
          type="textarea"
          :rows="4"
          placeholder="请输入题目内容..."
          maxlength="1000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="学生答案" prop="student_answer">
        <el-input
          v-model="form.student_answer"
          type="textarea"
          :rows="3"
          placeholder="请输入学生的错误答案..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="正确答案" prop="correct_answer">
        <el-input
          v-model="form.correct_answer"
          type="textarea"
          :rows="3"
          placeholder="请输入正确答案..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="错误类型" prop="error_type">
        <el-select v-model="form.error_type" placeholder="请选择错误类型" style="width: 100%">
          <el-option label="理解错误" value="理解错误" />
          <el-option label="方法错误" value="方法错误" />
          <el-option label="计算错误" value="计算错误" />
          <el-option label="表达错误" value="表达错误" />
        </el-select>
      </el-form-item>

      <el-form-item label="知识点" prop="knowledge_points">
        <el-select
          v-model="form.knowledge_points"
          multiple
          filterable
          allow-create
          placeholder="请选择或输入知识点"
          style="width: 100%"
        >
          <el-option v-for="point in commonKnowledgePoints" :key="point" :label="point" :value="point" />
        </el-select>
      </el-form-item>

      <el-form-item label="难度等级" prop="difficulty_level">
        <el-rate
          v-model="form.difficulty_level"
          :max="5"
          allow-half
          show-text
          :texts="difficultyTexts"
        />
      </el-form-item>

      <el-form-item label="标签" prop="tags">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          placeholder="添加自定义标签"
          style="width: 100%"
        >
          <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-checkbox v-model="form.is_starred">标为重点</el-checkbox>
      </el-form-item>
    </el-form>

    <!-- AI分析建议 -->
    <div v-if="aiAnalysis" class="ai-analysis">
      <el-divider>AI分析建议</el-divider>
      <div class="analysis-content">
        <p><strong>错误类型：</strong>{{ aiAnalysis.error_type }}</p>
        <p><strong>分析：</strong>{{ aiAnalysis.analysis }}</p>
        <div v-if="aiAnalysis.suggestions.length">
          <strong>改进建议：</strong>
          <ul>
            <li v-for="suggestion in aiAnalysis.suggestions" :key="suggestion">{{ suggestion }}</li>
          </ul>
        </div>
        <div class="analysis-actions">
          <el-button size="small" @click="applyAiSuggestions">应用建议</el-button>
          <el-button size="small" type="text" @click="aiAnalysis = null">忽略</el-button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="info" 
          :loading="analyzing"
          @click="analyzeWithAI"
          :disabled="!canAnalyze"
        >
          AI分析
        </el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          添加错题
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { errorBookApi } from '@/api/errorBook'
import type { ErrorQuestionCreate, ErrorAnalysisResponse } from '@/types/errorBook'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 表单引用和状态
const formRef = ref<FormInstance>()
const submitting = ref(false)
const analyzing = ref(false)
const aiAnalysis = ref<ErrorAnalysisResponse | null>(null)

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 表单数据
const form = reactive<ErrorQuestionCreate>({
  subject: '',
  question_content: '',
  student_answer: '',
  correct_answer: '',
  error_type: '理解错误',
  knowledge_points: [],
  difficulty_level: 2,
  tags: [],
  is_starred: false
})

// 表单验证规则
const rules: FormRules = {
  subject: [
    { required: true, message: '请选择学科', trigger: 'change' }
  ],
  question_content: [
    { required: true, message: '请输入题目内容', trigger: 'blur' },
    { min: 10, message: '题目内容至少10个字符', trigger: 'blur' }
  ]
}

// 选项数据
const subjects = [
  { label: '数学', value: '数学' },
  { label: '语文', value: '语文' },
  { label: '英语', value: '英语' },
  { label: '物理', value: '物理' },
  { label: '化学', value: '化学' },
  { label: '生物', value: '生物' },
  { label: '历史', value: '历史' },
  { label: '地理', value: '地理' },
  { label: '政治', value: '政治' }
]

const difficultyTexts = ['极简单', '简单', '中等', '困难', '极困难']

const commonKnowledgePoints = [
  '函数', '方程', '几何', '概率', '统计',
  '语法', '阅读理解', '写作', '古诗词',
  '化学方程式', '分子结构', '化学反应',
  '力学', '电学', '光学', '热学'
]

const commonTags = [
  '易错点', '重点', '考试常考', '基础知识', '难点攻克'
]

// 计算属性
const canAnalyze = computed(() => {
  return form.question_content.trim().length > 10 && 
         (form.student_answer?.trim() || form.correct_answer?.trim())
})

// 方法
const handleClose = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  formRef.value?.resetFields()
  aiAnalysis.value = null
  Object.assign(form, {
    subject: '',
    question_content: '',
    student_answer: '',
    correct_answer: '',
    error_type: '理解错误',
    knowledge_points: [],
    difficulty_level: 2,
    tags: [],
    is_starred: false
  })
}

const analyzeWithAI = async () => {
  if (!canAnalyze.value) {
    ElMessage.warning('请先填写题目内容和答案')
    return
  }

  try {
    analyzing.value = true
    
    const analysisData = {
      question_content: form.question_content,
      student_answer: form.student_answer || '',
      correct_answer: form.correct_answer || '',
      subject: form.subject
    }
    
    aiAnalysis.value = await errorBookApi.analyzeError(analysisData)
    ElMessage.success('AI分析完成')
    
  } catch (error) {
    console.error('AI分析失败:', error)
    ElMessage.error('AI分析失败，请稍后重试')
  } finally {
    analyzing.value = false
  }
}

const applyAiSuggestions = () => {
  if (!aiAnalysis.value) return
  
  // 应用AI建议
  form.error_type = aiAnalysis.value.error_type
  
  if (aiAnalysis.value.knowledge_points.length > 0) {
    form.knowledge_points = [...new Set([...form.knowledge_points, ...aiAnalysis.value.knowledge_points])]
  }
  
  ElMessage.success('已应用AI建议')
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    await errorBookApi.createErrorQuestion({
      ...form,
      source_type: 'manual'
    })
    
    ElMessage.success('错题添加成功')
    emit('success')
    handleClose()
    
  } catch (error) {
    console.error('添加错题失败:', error)
    ElMessage.error('添加错题失败')
  } finally {
    submitting.value = false
  }
}

// 监听对话框关闭，重置表单
watch(visible, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})
</script>

<style scoped>
.ai-analysis {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #f8f9fa;
}

.analysis-content p {
  margin: 8px 0;
  color: #606266;
}

.analysis-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.analysis-content li {
  margin: 4px 0;
  color: #606266;
}

.analysis-actions {
  margin-top: 12px;
  text-align: right;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-textarea__inner) {
  resize: vertical;
}
</style>