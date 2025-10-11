<template>
  <div class="error-book-container">
    <!-- 页面标题和统计卡片 -->
    <div class="page-header">
      <div class="title-section">
        <h1><el-icon><Collection /></el-icon> 错题本</h1>
        <p class="subtitle">智能错题管理，针对性复习</p>
      </div>
      
      <!-- 统计卡片区 -->
      <div class="stats-cards" v-if="stats">
        <el-card class="stats-card">
          <div class="stat-item">
            <span class="stat-value">{{ stats.overview.total_errors }}</span>
            <span class="stat-label">总错题数</span>
          </div>
        </el-card>
        
        <el-card class="stats-card">
          <div class="stat-item">
            <span class="stat-value">{{ pendingReviews }}</span>
            <span class="stat-label">待复习</span>
          </div>
        </el-card>
        
        <el-card class="stats-card">
          <div class="stat-item">
            <span class="stat-value">{{ masteryRate }}%</span>
            <span class="stat-label">掌握率</span>
          </div>
        </el-card>
        
        <el-card class="stats-card">
          <div class="stat-item">
            <span class="stat-value">{{ stats.overview.weekly_new }}</span>
            <span class="stat-label">本周新增</span>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-toolbar">
      <div class="filter-left">
        <el-select v-model="filters.subject" placeholder="选择学科" clearable @change="handleFilterChange">
          <el-option v-for="subject in subjects" :key="subject.value" :label="subject.label" :value="subject.value" />
        </el-select>
        
        <el-select v-model="filters.status" placeholder="掌握状态" clearable @change="handleFilterChange">
          <el-option label="学习中" value="learning" />
          <el-option label="复习中" value="reviewing" />
          <el-option label="已掌握" value="mastered" />
        </el-select>
        
        <el-select v-model="filters.category" placeholder="错误类型" clearable @change="handleFilterChange">
          <el-option label="理解错误" value="理解错误" />
          <el-option label="方法错误" value="方法错误" />
          <el-option label="计算错误" value="计算错误" />
          <el-option label="表达错误" value="表达错误" />
        </el-select>
        
        <el-select v-model="filters.difficulty" placeholder="难度" clearable @change="handleFilterChange">
          <el-option v-for="i in 5" :key="i" :label="`${i}星`" :value="i" />
        </el-select>
      </div>
      
      <div class="filter-right">
        <el-select v-model="sortConfig.sort" @change="handleSortChange">
          <el-option label="按创建时间" value="created_at" />
          <el-option label="按复习次数" value="review_count" />
          <el-option label="按错误次数" value="error_count" />
        </el-select>
        
        <el-select v-model="sortConfig.order" @change="handleSortChange">
          <el-option label="降序" value="desc" />
          <el-option label="升序" value="asc" />
        </el-select>
        
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon> 添加错题
        </el-button>
      </div>
    </div>

    <!-- 错题列表 -->
    <div class="error-list" v-loading="loading">
      <div v-if="errorQuestions.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无错题记录">
          <el-button type="primary" @click="showAddDialog = true">添加第一道错题</el-button>
        </el-empty>
      </div>
      
      <div v-else class="error-grid">
        <ErrorQuestionCard 
          v-for="question in errorQuestions" 
          :key="question.id"
          :error-question="question"
          @review="handleReview"
          @edit="handleEdit"
          @delete="handleDelete"
          @view-detail="handleViewDetail"
        />
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="pagination.total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.limit"
        :page-sizes="[10, 20, 30, 50]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handlePageSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 添加错题对话框 -->
    <AddErrorDialog 
      v-model="showAddDialog"
      @success="handleAddSuccess"
    />

    <!-- 复习对话框 -->
    <ReviewDialog 
      v-model="showReviewDialog"
      :error-question="selectedQuestion"
      @success="handleReviewSuccess"
    />

    <!-- 错题详情对话框 -->
    <ErrorDetailDialog 
      v-model="showDetailDialog"
      :error-question-id="selectedQuestionId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Collection, Plus } from '@element-plus/icons-vue'
import ErrorQuestionCard from '@/components/ErrorQuestionCard.vue'
import AddErrorDialog from '@/components/AddErrorDialog.vue'
import ReviewDialog from '@/components/ReviewDialog.vue'
import ErrorDetailDialog from '@/components/ErrorDetailDialog.vue'
import { errorBookApi } from '@/api/errorBook'
import type { ErrorQuestion, ErrorBookStats } from '@/types/errorBook'

// 响应式数据
const loading = ref(false)
const errorQuestions = ref<ErrorQuestion[]>([])
const stats = ref<ErrorBookStats | null>(null)

// 筛选和排序
const filters = reactive({
  subject: '',
  status: '',
  category: '',
  difficulty: null as number | null
})

const sortConfig = reactive({
  sort: 'created_at',
  order: 'desc'
})

// 分页
const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

// 对话框控制
const showAddDialog = ref(false)
const showReviewDialog = ref(false)
const showDetailDialog = ref(false)
const selectedQuestion = ref<ErrorQuestion | null>(null)
const selectedQuestionId = ref<string>('')

// 学科选项
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

// 计算属性
const pendingReviews = computed(() => {
  if (!stats.value) return 0
  return stats.value.overview.total_errors - stats.value.overview.mastered
})

const masteryRate = computed(() => {
  if (!stats.value) return 0
  return Math.round(stats.value.overview.mastery_rate * 100)
})

// 方法
const loadErrorQuestions = async () => {
  try {
    loading.value = true
    
    const queryParams = {
      subject: filters.subject || undefined,
      status: filters.status || undefined,
      category: filters.category || undefined,
      difficulty: filters.difficulty || undefined,
      sort: sortConfig.sort,
      order: sortConfig.order,
      page: pagination.page,
      limit: pagination.limit
    }

    const response = await errorBookApi.getErrorQuestions(queryParams)
    
    errorQuestions.value = response.items
    pagination.total = response.total
    
  } catch (error) {
    console.error('加载错题列表失败:', error)
    ElMessage.error('加载错题列表失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    stats.value = await errorBookApi.getStats()
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  loadErrorQuestions()
}

const handleSortChange = () => {
  pagination.page = 1
  loadErrorQuestions()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadErrorQuestions()
}

const handlePageSizeChange = (size: number) => {
  pagination.limit = size
  pagination.page = 1
  loadErrorQuestions()
}

const handleReview = (question: ErrorQuestion) => {
  selectedQuestion.value = question
  showReviewDialog.value = true
}

const handleEdit = (question: ErrorQuestion) => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中...')
}

const handleDelete = async (question: ErrorQuestion) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这道错题吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await errorBookApi.deleteErrorQuestion(question.id)
    ElMessage.success('删除成功')
    
    // 重新加载数据
    await loadErrorQuestions()
    await loadStats()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除错题失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleViewDetail = (question: ErrorQuestion) => {
  selectedQuestionId.value = question.id
  showDetailDialog.value = true
}

const handleAddSuccess = () => {
  loadErrorQuestions()
  loadStats()
}

const handleReviewSuccess = () => {
  loadErrorQuestions()
  loadStats()
}

// 生命周期
onMounted(() => {
  loadErrorQuestions()
  loadStats()
})
</script>

<style scoped>
.error-book-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.title-section {
  margin-bottom: 20px;
}

.title-section h1 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 28px;
  color: #303133;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stats-card {
  text-align: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-left {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.error-list {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.error-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .error-book-container {
    padding: 15px;
  }
  
  .filter-toolbar {
    flex-direction: column;
    gap: 15px;
  }
  
  .filter-left,
  .filter-right {
    width: 100%;
  }
  
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .error-grid {
    grid-template-columns: 1fr;
  }
}
</style>