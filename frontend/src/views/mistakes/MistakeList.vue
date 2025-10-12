<template>
  <div class="mistake-list-container">
    <el-card class="header-card">
      <div class="header-content">
        <h2>错题手册</h2>
        <el-button type="primary" @click="refreshList">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">总错题数</div>
            <div class="stat-value">{{ statistics?.total_mistakes || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">未掌握</div>
            <div class="stat-value warning">{{ statistics?.not_mastered || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">复习中</div>
            <div class="stat-value primary">{{ statistics?.reviewing || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">已掌握</div>
            <div class="stat-value success">{{ statistics?.mastered || 0 }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="学科">
          <el-select
            v-model="filterForm.subject"
            placeholder="全部学科"
            clearable
            style="width: 150px"
          >
            <el-option label="数学" value="math" />
            <el-option label="语文" value="chinese" />
            <el-option label="英语" value="english" />
            <el-option label="物理" value="physics" />
            <el-option label="化学" value="chemistry" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.mastery_status"
            placeholder="全部状态"
            clearable
            style="width: 150px"
          >
            <el-option label="未掌握" value="not_mastered" />
            <el-option label="复习中" value="reviewing" />
            <el-option label="已掌握" value="mastered" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="搜索错题"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 错题列表 -->
    <el-card class="list-card">
      <el-table v-loading="loading" :data="mistakes" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="subject" label="学科" width="100">
          <template #default="{ row }">
            <el-tag>{{ getSubjectName(row.subject) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mastery_status" label="掌握状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.mastery_status)">
              {{ getStatusText(row.mastery_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="correct_count" label="正确次数" width="100" align="center" />
        <el-table-column prop="total_reviews" label="总复习次数" width="120" align="center" />
        <el-table-column prop="next_review_date" label="下次复习" width="120">
          <template #default="{ row }">
            {{ row.next_review_date ? formatDate(row.next_review_date) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">查看</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getMistakeList, getMistakeStatistics, deleteMistake } from '@/api/mistakes'
import type { MistakeListItem, MistakeStatistics } from '@/types/mistake'

const router = useRouter()
const loading = ref(false)
const mistakes = ref<MistakeListItem[]>([])
const statistics = ref<MistakeStatistics | null>(null)

const filterForm = ref({
  subject: '',
  mastery_status: '',
  search: '',
})

const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

// 加载错题列表
const loadMistakes = async () => {
  loading.value = true
  try {
    const response = await getMistakeList({
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      ...filterForm.value,
    })
    mistakes.value = response.items
    pagination.value.total = response.total
  } catch (error) {
    ElMessage.error('加载错题列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    statistics.value = await getMistakeStatistics()
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 筛选
const handleFilter = () => {
  pagination.value.page = 1
  loadMistakes()
}

// 重置
const handleReset = () => {
  filterForm.value = {
    subject: '',
    mastery_status: '',
    search: '',
  }
  pagination.value.page = 1
  loadMistakes()
}

// 刷新
const refreshList = () => {
  loadMistakes()
  loadStatistics()
}

// 分页变化
const handlePageChange = () => {
  loadMistakes()
}

const handleSizeChange = () => {
  pagination.value.page = 1
  loadMistakes()
}

// 查看详情
const viewDetail = (id: string) => {
  router.push(`/mistakes/${id}`)
}

// 删除错题
const handleDelete = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这道错题吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMistake(id)
    ElMessage.success('删除成功')
    loadMistakes()
    loadStatistics()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
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

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    not_mastered: '未掌握',
    reviewing: '复习中',
    mastered: '已掌握',
  }
  return map[status] || status
}

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    not_mastered: 'danger',
    reviewing: 'warning',
    mastered: 'success',
  }
  return map[status] || 'info'
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
  loadMistakes()
  loadStatistics()
})
</script>

<style scoped lang="scss">
.mistake-list-container {
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
  }
}

.stats-row {
  margin-bottom: 20px;

  .stat-card {
    .stat-content {
      text-align: center;

      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 28px;
        font-weight: bold;

        &.primary {
          color: #409eff;
        }

        &.success {
          color: #67c23a;
        }

        &.warning {
          color: #e6a23c;
        }
      }
    }
  }
}

.filter-card {
  margin-bottom: 20px;
}

.list-card {
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
