<template>
  <div class="today-review-container">
    <el-card class="header-card">
      <div class="header-content">
        <h2>今日复习</h2>
        <div class="header-info">
          <el-tag type="info" size="large"> 今日待复习: {{ todayTasks.length }} 题 </el-tag>
          <el-tag type="success" size="large"> 已完成: {{ completedCount }} 题 </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-card v-if="todayTasks.length === 0 && !loading" class="empty-card">
      <el-empty description="今天没有需要复习的错题">
        <el-button type="primary" @click="goToMistakeList">查看错题手册</el-button>
      </el-empty>
    </el-card>

    <!-- 复习列表 -->
    <div v-else class="review-list">
      <el-card
        v-for="(task, index) in todayTasks"
        :key="task.mistake_id"
        class="review-card"
        :class="{ completed: isCompleted(task.mistake_id) }"
      >
        <div class="review-header">
          <div class="review-title">
            <span class="review-number">第 {{ index + 1 }} 题</span>
            <el-tag type="info">第 {{ task.review_round }} 轮复习</el-tag>
          </div>
          <el-tag v-if="isCompleted(task.mistake_id)" type="success">已完成</el-tag>
        </div>

        <div class="review-content">
          <div class="content-row">
            <span class="label">标题:</span>
            <span class="value">{{ task.title }}</span>
          </div>
          <div class="content-row">
            <span class="label">学科:</span>
            <el-tag size="small">{{ getSubjectName(task.subject) }}</el-tag>
          </div>
          <div class="content-row">
            <span class="label">到期时间:</span>
            <span class="value">{{ formatDate(task.due_date) }}</span>
          </div>
        </div>

        <div class="review-actions">
          <el-button type="primary" @click="viewDetail(task.mistake_id)"> 查看详情 </el-button>
          <el-button
            v-if="!isCompleted(task.mistake_id)"
            type="success"
            @click="showReviewDialog(task)"
          >
            开始复习
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 复习对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="完成复习"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="reviewForm" label-width="100px">
        <el-form-item label="是否答对">
          <el-radio-group v-model="reviewForm.is_correct">
            <el-radio :label="true">答对了</el-radio>
            <el-radio :label="false">答错了</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="复习笔记" v-if="reviewForm.is_correct === false">
          <el-input
            v-model="reviewForm.notes"
            type="textarea"
            :rows="4"
            placeholder="记录这次答错的原因或新的理解..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReview" :loading="submitting"> 提交 </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTodayReviewTasks, completeReview } from '@/api/mistakes'
import type { TodayReviewTask, ReviewCompleteRequest, TodayReviewResponse } from '@/types/mistake'

const router = useRouter()
const loading = ref(false)
const todayTasks = ref<TodayReviewTask[]>([])
const completedTasks = ref<Set<string>>(new Set())
const reviewDialogVisible = ref(false)
const submitting = ref(false)

const reviewForm = ref<Omit<ReviewCompleteRequest, 'mistake_id'>>({
  is_correct: true,
  notes: '',
})

const currentTask = ref<TodayReviewTask | null>(null)

// 已完成数量
const completedCount = computed(() => {
  return completedTasks.value.size
})

// 加载今日复习任务
const loadTodayTasks = async () => {
  loading.value = true
  try {
    const response: TodayReviewResponse = await getTodayReviewTasks()
    todayTasks.value = response.tasks
    completedTasks.value = new Set()
  } catch (error) {
    ElMessage.error('加载复习任务失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 显示复习对话框
const showReviewDialog = (task: TodayReviewTask) => {
  currentTask.value = task
  reviewForm.value = {
    is_correct: true,
    notes: '',
  }
  reviewDialogVisible.value = true
}

// 提交复习结果
const submitReview = async () => {
  if (!currentTask.value) return

  submitting.value = true
  try {
    const request: ReviewCompleteRequest = {
      mistake_id: currentTask.value.mistake_id,
      ...reviewForm.value,
    }

    await completeReview(request)

    ElMessage.success(reviewForm.value.is_correct ? '复习完成！继续加油！' : '没关系,再接再厉！')

    // 标记为已完成
    completedTasks.value.add(currentTask.value.mistake_id)

    reviewDialogVisible.value = false
  } catch (error) {
    ElMessage.error('提交失败,请重试')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

// 查看详情
const viewDetail = (mistakeId: string) => {
  router.push(`/mistakes/${mistakeId}`)
}

// 跳转到错题列表
const goToMistakeList = () => {
  router.push('/mistakes')
}

// 工具函数
const getSubjectName = (subject: string) => {
  const map: Record<string, string> = {
    math: '数学',
    chinese: '语文',
    english: '英语',
    physics: '物理',
    chemistry: '化学',
  }
  return map[subject] || subject
}

const isCompleted = (mistakeId: string) => {
  return completedTasks.value.has(mistakeId)
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadTodayTasks()
})
</script>

<style scoped lang="scss">
.today-review-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      margin: 0;
      font-size: 24px;
    }

    .header-info {
      display: flex;
      gap: 16px;
    }
  }
}

.empty-card {
  padding: 40px 0;
}

.review-list {
  display: grid;
  gap: 20px;
}

.review-card {
  transition: all 0.3s;

  &.completed {
    opacity: 0.7;
    background-color: #f5f7fa;
  }

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #ebeef5;

    .review-title {
      display: flex;
      align-items: center;
      gap: 12px;

      .review-number {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
      }
    }
  }

  .review-content {
    margin-bottom: 16px;

    .content-row {
      display: flex;
      align-items: center;
      margin-bottom: 12px;

      .label {
        width: 80px;
        color: #909399;
        font-size: 14px;
      }

      .value {
        flex: 1;
        color: #606266;
        font-size: 14px;
      }
    }
  }

  .review-actions {
    display: flex;
    gap: 12px;
  }
}
</style>
