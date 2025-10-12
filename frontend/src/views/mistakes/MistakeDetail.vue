<template>
  <div class="mistake-detail-container">
    <el-card v-loading="loading" class="detail-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
            <h2>{{ mistake?.title }}</h2>
          </div>
          <div class="header-right">
            <el-tag :type="getStatusType(mistake?.mastery_status)">
              {{ getStatusText(mistake?.mastery_status) }}
            </el-tag>
          </div>
        </div>
      </template>

      <div v-if="mistake" class="detail-content">
        <!-- 基本信息 -->
        <el-descriptions :column="2" border class="section">
          <el-descriptions-item label="学科">
            <el-tag>{{ getSubjectName(mistake.subject) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="难度">
            <el-rate v-model="mistake.difficulty_level" disabled show-score text-color="#ff9900" />
          </el-descriptions-item>
          <el-descriptions-item label="错题来源">
            <el-tag :type="getSourceType(mistake.source)">
              {{ getSourceText(mistake.source) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(mistake.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="复习次数">
            {{ mistake.total_reviews }} 次
          </el-descriptions-item>
          <el-descriptions-item label="正确次数">
            {{ mistake.correct_count }} 次
          </el-descriptions-item>
          <el-descriptions-item label="下次复习">
            {{ mistake.next_review_date ? formatDate(mistake.next_review_date) : '无需复习' }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDate(mistake.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 知识点 -->
        <div v-if="mistake.knowledge_points && mistake.knowledge_points.length > 0" class="section">
          <h3>相关知识点</h3>
          <div class="knowledge-points">
            <el-tag
              v-for="point in mistake.knowledge_points"
              :key="point"
              type="info"
              effect="plain"
            >
              {{ point }}
            </el-tag>
          </div>
        </div>

        <!-- 题目内容 -->
        <div class="section">
          <h3>题目内容</h3>
          <div class="content-box">
            {{ mistake.question_content }}
          </div>
          <!-- 图片 -->
          <div v-if="mistake.image_urls && mistake.image_urls.length > 0" class="images">
            <el-image
              v-for="(url, index) in mistake.image_urls"
              :key="index"
              :src="url"
              :preview-src-list="mistake.image_urls"
              :initial-index="index"
              fit="contain"
              class="image-item"
            />
          </div>
        </div>

        <!-- 我的答案 -->
        <div v-if="mistake.student_answer" class="section">
          <h3>我的答案</h3>
          <div class="content-box error-answer">
            {{ mistake.student_answer }}
          </div>
        </div>

        <!-- 正确答案 -->
        <div v-if="mistake.correct_answer" class="section">
          <h3>正确答案</h3>
          <div class="content-box correct-answer">
            {{ mistake.correct_answer }}
          </div>
        </div>

        <!-- 解析 -->
        <div v-if="mistake.explanation" class="section">
          <h3>题目解析</h3>
          <div class="content-box explanation">
            {{ mistake.explanation }}
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="actions">
          <el-button type="primary" @click="startReview" v-if="canReview"> 开始复习 </el-button>
          <el-button type="danger" @click="handleDelete"> 删除错题 </el-button>
        </div>
      </div>
    </el-card>

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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getMistakeDetail, completeReview, deleteMistake } from '@/api/mistakes'
import type { MistakeDetail, ReviewCompleteRequest, MasteryStatus } from '@/types/mistake'
import { MistakeSource } from '@/types/mistake'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const mistake = ref<MistakeDetail | null>(null)
const reviewDialogVisible = ref(false)
const submitting = ref(false)

const reviewForm = ref<Omit<ReviewCompleteRequest, 'mistake_id'>>({
  is_correct: true,
  notes: '',
})

const mistakeId = computed(() => route.params.id as string)

// 是否可以复习
const canReview = computed(() => {
  if (!mistake.value) return false
  return mistake.value.mastery_status !== 'mastered'
})

// 加载错题详情
const loadDetail = async () => {
  loading.value = true
  try {
    mistake.value = await getMistakeDetail(mistakeId.value)
  } catch (error) {
    ElMessage.error('加载错题详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 开始复习
const startReview = () => {
  reviewForm.value = {
    is_correct: true,
    notes: '',
  }
  reviewDialogVisible.value = true
}

// 提交复习结果
const submitReview = async () => {
  if (!mistake.value) return

  submitting.value = true
  try {
    const request: ReviewCompleteRequest = {
      mistake_id: mistake.value.id,
      ...reviewForm.value,
    }

    const response = await completeReview(request)

    ElMessage.success(reviewForm.value.is_correct ? '复习完成！继续加油！' : '没关系,再接再厉！')

    // 更新状态
    mistake.value.mastery_status = response.mastery_status
    mistake.value.total_reviews += 1
    if (reviewForm.value.is_correct) {
      mistake.value.correct_count += 1
    }
    if (response.next_review_date) {
      mistake.value.next_review_date = response.next_review_date
    }

    reviewDialogVisible.value = false
  } catch (error) {
    ElMessage.error('提交失败,请重试')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

// 删除错题
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这道错题吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMistake(mistakeId.value)
    ElMessage.success('删除成功')
    router.push('/mistakes')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 返回
const goBack = () => {
  router.back()
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

const getStatusText = (status?: MasteryStatus) => {
  if (!status) return ''
  const map: Record<string, string> = {
    not_mastered: '未掌握',
    reviewing: '复习中',
    mastered: '已掌握',
  }
  return map[status] || status
}

const getStatusType = (status?: MasteryStatus) => {
  if (!status) return 'info'
  const map: Record<string, any> = {
    not_mastered: 'danger',
    reviewing: 'warning',
    mastered: 'success',
  }
  return map[status] || 'info'
}

const getSourceText = (source: MistakeSource) => {
  const map: Record<string, string> = {
    homework: '作业批改',
    learning: '学习问答',
    manual: '手动添加',
  }
  return map[source] || source
}

const getSourceType = (source: MistakeSource) => {
  const map: Record<string, any> = {
    homework: 'primary',
    learning: 'success',
    manual: 'info',
  }
  return map[source] || 'info'
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
  loadDetail()
})
</script>

<style scoped lang="scss">
.mistake-detail-container {
  padding: 20px;
}

.detail-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      h2 {
        margin: 0;
        font-size: 20px;
      }
    }
  }
}

.detail-content {
  .section {
    margin-bottom: 24px;

    h3 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: bold;
      color: #303133;
    }
  }

  .knowledge-points {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .content-box {
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 4px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;

    &.error-answer {
      background-color: #fef0f0;
      border-left: 4px solid #f56c6c;
    }

    &.correct-answer {
      background-color: #f0f9ff;
      border-left: 4px solid #67c23a;
    }

    &.explanation {
      background-color: #fdf6ec;
      border-left: 4px solid #e6a23c;
    }
  }

  .images {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 16px;

    .image-item {
      width: 100%;
      height: 200px;
      border-radius: 4px;
      cursor: pointer;
      transition: transform 0.2s;

      &:hover {
        transform: scale(1.05);
      }
    }
  }

  .actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    padding-top: 24px;
  }
}
</style>
