<!--
  作业列表页面
-->
<template>
  <div class="homework-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon><Notebook /></el-icon>
          我的作业
        </h1>
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-number">{{ stats?.total || 0 }}</div>
            <div class="stat-label">总数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ stats?.completed || 0 }}</div>
            <div class="stat-label">已完成</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ stats?.processing || 0 }}</div>
            <div class="stat-label">处理中</div>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="goToUpload">
          <el-icon><Plus /></el-icon>
          上传作业
        </el-button>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card>
        <el-form
          :model="filterForm"
          :inline="true"
          class="filter-form"
          @submit.prevent="handleSearch"
        >
          <el-form-item label="学科">
            <el-select
              v-model="filterForm.subject"
              placeholder="全部学科"
              clearable
              style="width: 120px"
            >
              <el-option
                v-for="option in HOMEWORK_SUBJECT_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="年级">
            <el-select
              v-model="filterForm.grade_level"
              placeholder="全部年级"
              clearable
              style="width: 120px"
            >
              <el-option
                v-for="option in GRADE_LEVEL_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="状态">
            <el-select
              v-model="filterForm.status"
              placeholder="全部状态"
              clearable
              style="width: 120px"
            >
              <el-option
                v-for="option in STATUS_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="时间">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 240px"
            />
          </el-form-item>

          <el-form-item>
            <el-input
              v-model="filterForm.search"
              placeholder="搜索作业标题或描述"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            >
              <template #suffix>
                <el-icon class="search-icon"><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button
              type="text"
              :disabled="selectedHomework.length === 0"
              @click="handleBatchDelete"
            >
              批量删除 ({{ selectedHomework.length }})
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 作业列表 -->
    <div class="homework-list">
      <el-card>
        <!-- 加载状态 -->
        <div
          v-if="homeworkStore.listLoading && (!homeworkList || homeworkList.length === 0)"
          class="loading-state"
        >
          <el-skeleton :rows="5" animated />
        </div>

        <!-- 空状态 -->
        <div
          v-else-if="!homeworkStore.listLoading && (!homeworkList || homeworkList.length === 0)"
          class="empty-state"
        >
          <el-empty description="暂无作业数据">
            <el-button type="primary" @click="goToUpload">上传第一个作业</el-button>
          </el-empty>
        </div>

        <!-- 列表内容 -->
        <div v-else class="list-content">
          <!-- 列表头部 -->
          <div class="list-header">
            <el-checkbox
              v-model="selectAll"
              :indeterminate="isIndeterminate"
              @change="handleSelectAll"
            >
              全选
            </el-checkbox>
            <span class="total-info">
              共 {{ pagination.total }} 条记录，第 {{ pagination.page }} /
              {{ pagination.total_pages }} 页
            </span>
          </div>

          <!-- 作业项 -->
          <div class="homework-items">
            <HomeworkCard
              v-for="homework in homeworkList"
              :key="homework.id"
              :homework="homework"
              :selected="selectedHomework.includes(homework.id)"
              :show-checkbox="true"
              @select="handleSelectItem(homework.id, $event)"
              @click="viewHomework(homework.id)"
              @view-detail="viewHomework"
              @edit="editHomework"
              @rename="handleRenameHomework"
              @delete="deleteHomework"
              @start-correction="startCorrection"
              @retry-correction="retryCorrection"
            />
          </div>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :total="pagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="handlePageChange"
              @size-change="handleSizeChange"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑作业信息"
      width="500px"
      @close="closeEditDialog"
    >
      <el-form v-if="editingHomework" ref="editFormRef" :model="editForm" label-width="80px">
        <el-form-item label="标题">
          <el-input
            v-model="editForm.title"
            placeholder="请输入作业标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入作业描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveEdit">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Notebook, Plus, Search } from '@element-plus/icons-vue'

import { useHomeworkStore } from '@/stores/homework'
import HomeworkCard from '@/components/homework/HomeworkCard.vue'
import {
  HOMEWORK_SUBJECT_OPTIONS,
  GRADE_LEVEL_OPTIONS,
  STATUS_OPTIONS,
  type HomeworkQueryParams,
  type HomeworkRecord,
} from '@/types/homework'

const router = useRouter()
const homeworkStore = useHomeworkStore()

// 表单引用
const editFormRef = ref<FormInstance>()

// 筛选表单
const filterForm = reactive<HomeworkQueryParams>({
  page: 1,
  page_size: 20,
})

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 选中的作业
const selectedHomework = ref<string[]>([])

// 编辑对话框
const editDialogVisible = ref(false)
const editingHomework = ref<HomeworkRecord | null>(null)
const editForm = reactive({
  title: '',
  description: '',
})

// 计算属性
const homeworkList = computed(() => homeworkStore.homeworkList)
const pagination = computed(() => homeworkStore.pagination)
const stats = computed(() => homeworkStore.stats)

// 全选状态
const selectAll = computed({
  get: () =>
    selectedHomework.value.length === homeworkList.value.length && homeworkList.value.length > 0,
  set: (value: boolean) => {
    if (value) {
      selectedHomework.value = homeworkList.value.map((item) => item.id)
    } else {
      selectedHomework.value = []
    }
  },
})

// 半选状态
const isIndeterminate = computed(() => {
  const selectedCount = selectedHomework.value.length
  return selectedCount > 0 && selectedCount < homeworkList.value.length
})

// 监听日期范围变化
watch(dateRange, (newRange) => {
  if (newRange) {
    filterForm.start_date = newRange[0]
    filterForm.end_date = newRange[1]
  } else {
    delete filterForm.start_date
    delete filterForm.end_date
  }
})

// 生命周期
onMounted(async () => {
  await Promise.all([homeworkStore.getHomeworkList(filterForm), homeworkStore.getHomeworkStats()])
})

// 搜索
const handleSearch = () => {
  filterForm.page = 1
  homeworkStore.getHomeworkList(filterForm)
}

// 重置筛选
const handleReset = () => {
  Object.keys(filterForm).forEach((key) => {
    if (key !== 'page' && key !== 'page_size') {
      delete filterForm[key as keyof HomeworkQueryParams]
    }
  })
  filterForm.page = 1
  dateRange.value = null
  homeworkStore.getHomeworkList(filterForm)
}

// 页面变化
const handlePageChange = (page: number) => {
  filterForm.page = page
  homeworkStore.getHomeworkList(filterForm)
}

// 页大小变化
const handleSizeChange = (size: number) => {
  filterForm.page = 1
  filterForm.page_size = size
  homeworkStore.getHomeworkList(filterForm)
}

// 全选处理
const handleSelectAll = (checked: boolean | string | number) => {
  selectAll.value = Boolean(checked)
}

// 选择单项
const handleSelectItem = (id: string, checked: boolean | string | number) => {
  const isChecked = Boolean(checked)
  if (isChecked) {
    selectedHomework.value.push(id)
  } else {
    const index = selectedHomework.value.indexOf(id)
    if (index > -1) {
      selectedHomework.value.splice(index, 1)
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedHomework.value.length === 0) {
    ElMessage.warning('请选择要删除的作业')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedHomework.value.length} 个作业吗？删除后无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await homeworkStore.batchDeleteHomework(selectedHomework.value)
    selectedHomework.value = []

    // 重新获取统计数据
    homeworkStore.getHomeworkStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
    }
  }
}

// 跳转到上传页面
const goToUpload = () => {
  router.push({ name: 'HomeworkUpload' })
}

// 查看作业详情
const viewHomework = (homeworkId: string) => {
  router.push({
    name: 'HomeworkDetail',
    params: { id: homeworkId },
  })
}

// 编辑作业
const editHomework = (homework: HomeworkRecord) => {
  editingHomework.value = homework
  editForm.title = homework.title || ''
  editForm.description = homework.description || ''
  editDialogVisible.value = true
}

// 重命名作业
const handleRenameHomework = async (homework: HomeworkRecord) => {
  try {
    const { value: newTitle } = await ElMessageBox.prompt('请输入新的作业标题：', '重命名作业', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: homework.title || '',
      inputPlaceholder: '请输入作业标题',
      inputValidator: (value: string) => {
        if (!value || value.trim().length === 0) {
          return '标题不能为空'
        }
        if (value.length > 200) {
          return '标题长度不能超过200个字符'
        }
        return true
      },
    })

    if (newTitle && newTitle.trim() !== homework.title) {
      await homeworkStore.renameHomework(homework.id, newTitle.trim())
      ElMessage.success('重命名成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重命名失败:', error)
      ElMessage.error('重命名失败')
    }
  }
}

// 关闭编辑对话框
const closeEditDialog = () => {
  editingHomework.value = null
  editForm.title = ''
  editForm.description = ''
}

// 保存编辑
const saveEdit = async () => {
  if (!editingHomework.value) return

  try {
    await homeworkStore.updateHomework(editingHomework.value.id, {
      title: editForm.title,
      description: editForm.description,
    })

    editDialogVisible.value = false
    ElMessage.success('编辑成功')
  } catch (error) {
    console.error('编辑失败:', error)
    ElMessage.error('编辑失败')
  }
}

// 开始批改
const startCorrection = async (homeworkId: string) => {
  await homeworkStore.correctHomework(homeworkId)
}

// 重新批改
const retryCorrection = async (homeworkId: string) => {
  await homeworkStore.retryCorrection(homeworkId)
}

// 删除作业
const deleteHomework = async (homeworkId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个作业吗？删除后无法恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await homeworkStore.deleteHomework(homeworkId)

    // 重新获取统计数据
    homeworkStore.getHomeworkStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}
</script>

<style scoped lang="scss">
.homework-list-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;

    .header-left {
      flex: 1;

      .page-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 28px;
        font-weight: 700;
        color: #303133;
        margin: 0 0 20px 0;

        .el-icon {
          font-size: 32px;
          color: #409eff;
        }
      }

      .stats-cards {
        display: flex;
        gap: 16px;

        .stat-card {
          padding: 12px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 12px;
          color: white;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);

          .stat-number {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
          }

          .stat-label {
            font-size: 13px;
            opacity: 0.9;
          }

          &:nth-child(2) {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
          }

          &:nth-child(3) {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
          }
        }
      }
    }
  }

  .filter-section {
    margin-bottom: 24px;

    .filter-form {
      margin-bottom: -18px;
    }
  }

  .main-content {
    .list-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid #e4e7ed;
      margin-bottom: 16px;

      .total-info {
        font-size: 14px;
        color: #606266;
      }
    }

    .homework-items {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }

    .pagination-container {
      display: flex;
      justify-content: center;
      margin-top: 32px;
    }
  }
}
</style>
