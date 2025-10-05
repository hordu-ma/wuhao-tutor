<!--
  作业上传页面
-->
<template>
  <div class="homework-upload-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Edit /></el-icon>
          上传作业
        </h1>
        <p class="page-description">拍照或选择作业图片，AI将自动批改并提供学习建议</p>
      </div>
    </div>

    <div class="upload-container">
      <el-card class="upload-card">
        <template #header>
          <div class="card-header">
            <span>作业信息</span>
          </div>
        </template>

        <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="upload-form">
          <!-- 基本信息 -->
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="学科" prop="subject">
                <el-select v-model="form.subject" placeholder="请选择学科" style="width: 100%">
                  <el-option
                    v-for="option in HOMEWORK_SUBJECT_OPTIONS"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="年级" prop="grade_level">
                <el-select v-model="form.grade_level" placeholder="请选择年级" style="width: 100%">
                  <el-option
                    v-for="option in GRADE_LEVEL_OPTIONS"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="24">
              <el-form-item label="标题">
                <el-input
                  v-model="form.title"
                  placeholder="请输入作业标题（可选）"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row>
            <el-col :span="24">
              <el-form-item label="描述">
                <el-input
                  v-model="form.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入作业描述或注意事项（可选）"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 文件上传 -->
          <el-form-item label="作业图片" prop="images">
            <FileUpload
              ref="fileUploadRef"
              accept="image/*"
              :multiple="true"
              :max-count="9"
              :max-size="10 * 1024 * 1024"
              :auto-upload="false"
              :before-upload="handleBeforeUpload"
              @change="handleFileChange"
            />
          </el-form-item>

          <!-- 上传按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="homeworkStore.submitLoading"
              :disabled="!canSubmit"
              @click="handleSubmit"
            >
              <el-icon v-if="!homeworkStore.submitLoading"><Upload /></el-icon>
              {{ homeworkStore.submitLoading ? '上传中...' : '提交作业' }}
            </el-button>
            <el-button size="large" @click="resetForm"> 重置 </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 上传提示 -->
      <el-card class="tips-card">
        <template #header>
          <span
            ><el-icon><InfoFilled /></el-icon> 上传提示</span
          >
        </template>
        <div class="tips-content">
          <ul class="tips-list">
            <li>支持JPG、PNG、WEBP等图片格式</li>
            <li>单张图片不超过10MB，最多上传9张图片</li>
            <li>请确保图片清晰，字迹工整，光线充足</li>
            <li>建议将题目和答案分别拍照，便于AI准确识别</li>
            <li>上传后AI将自动进行OCR识别和智能批改</li>
          </ul>
        </div>
      </el-card>
    </div>

    <!-- 最近上传 -->
    <div v-if="recentHomework.length > 0" class="recent-homework">
      <el-card>
        <template #header>
          <span
            ><el-icon><Clock /></el-icon> 最近上传</span
          >
        </template>
        <div class="recent-list">
          <div
            v-for="homework in recentHomework"
            :key="homework.id"
            class="recent-item"
            @click="viewHomework(homework.id)"
          >
            <div class="recent-preview">
              <img
                v-if="homework.original_images?.[0]"
                :src="homework.original_images[0]"
                alt="作业预览"
              />
              <el-icon v-else><Document /></el-icon>
            </div>
            <div class="recent-info">
              <div class="recent-title">
                {{ homework.title || '未命名作业' }}
              </div>
              <div class="recent-meta">
                <span class="subject">{{ getSubjectLabel(homework.subject) }}</span>
                <span class="time">{{ formatTime(homework.created_at) }}</span>
                <el-tag :type="getStatusTagType(homework.status)" size="small">
                  {{ getStatusLabel(homework.status) }}
                </el-tag>
              </div>
            </div>
            <el-icon class="arrow-right"><ArrowRight /></el-icon>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Edit, Upload, InfoFilled, Clock, Document, ArrowRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

import FileUpload from '@/components/FileUpload.vue'
import type { FileUploadItem } from '@/components/FileUpload.vue'
import { useHomeworkStore } from '@/stores/homework'
import {
  HOMEWORK_SUBJECT_OPTIONS,
  GRADE_LEVEL_OPTIONS,
  STATUS_OPTIONS,
  type HomeworkSubmitRequest,
  type Subject,
  type GradeLevel,
  type HomeworkStatus,
  type SubjectOption,
} from '@/types/homework'

const router = useRouter()
const homeworkStore = useHomeworkStore()

// 表单引用
const formRef = ref<FormInstance>()
const fileUploadRef = ref()

// 表单数据
const form = reactive<HomeworkSubmitRequest>({
  subject: '' as Subject,
  grade_level: 0 as GradeLevel,
  title: '',
  description: '',
  images: [],
})

// 表单验证规则
const rules: FormRules = {
  subject: [{ required: true, message: '请选择学科', trigger: 'change' }],
  grade_level: [{ required: true, message: '请选择年级', trigger: 'change' }],
  images: [{ required: true, message: '请上传作业图片', trigger: 'change' }],
}

// 文件列表
const fileList = ref<FileUploadItem[]>([])

// 计算属性
const canSubmit = computed(() => {
  return (
    form.subject &&
    form.grade_level &&
    fileList.value.length > 0 &&
    fileList.value.some((item) => item.status === 'success' || item.status === 'waiting')
  )
})

// 最近的作业
const recentHomework = computed(() => {
  return homeworkStore.homeworkList?.slice(0, 5) || []
})

// 生命周期
onMounted(() => {
  // 获取最近的作业
  homeworkStore.getHomeworkList({ page: 1, page_size: 5 })
})

// 文件上传前的处理
const handleBeforeUpload = (file: File): boolean => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }

  const isLt10M = file.size < 10 * 1024 * 1024
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过10MB!')
    return false
  }

  return true
}

// 文件变化处理
const handleFileChange = (files: FileUploadItem[]) => {
  fileList.value = files
  form.images = files.map((item) => item.file)
}

// 提交作业
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    // 验证表单
    await formRef.value.validate()

    // 确认提交
    await ElMessageBox.confirm('确认提交作业吗？提交后将开始AI批改。', '确认提交', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
    })

    // 提交作业
    const homework = await homeworkStore.submitHomework(form)

    if (homework) {
      ElMessage.success('作业提交成功，正在进行AI批改...')

      // 跳转到作业详情页面
      router.push({
        name: 'HomeworkDetail',
        params: { id: homework.id },
      })
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交作业失败:', error)
    }
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  fileUploadRef.value?.clearFiles()
  fileList.value = []
  form.images = []
}

// 查看作业详情
const viewHomework = (homeworkId: string) => {
  router.push({
    name: 'HomeworkDetail',
    params: { id: homeworkId },
  })
}

// 获取学科标签
const getSubjectLabel = (subject: Subject) => {
  const option = HOMEWORK_SUBJECT_OPTIONS.find((opt: SubjectOption) => opt.value === subject)
  return option?.label || subject
}

// 获取状态标签
const getStatusLabel = (status: HomeworkStatus): string => {
  const option = STATUS_OPTIONS.find((opt) => opt.value === status)
  return option?.label || status
}

// 获取状态标签类型
const getStatusTagType = (
  status: HomeworkStatus
): 'success' | 'primary' | 'warning' | 'info' | 'danger' => {
  const typeMap: Record<HomeworkStatus, 'success' | 'primary' | 'warning' | 'info' | 'danger'> = {
    submitted: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return typeMap[status] || 'info'
}

// 格式化时间
const formatTime = (time: string): string => {
  return dayjs(time).format('MM-DD HH:mm')
}
</script>

<style scoped lang="scss">
.homework-upload-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;

  .page-header {
    margin-bottom: 24px;

    .header-content {
      text-align: center;

      .page-title {
        font-size: 28px;
        color: #303133;
        margin: 0 0 12px 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
      }

      .page-description {
        font-size: 16px;
        color: #606266;
        margin: 0;
      }
    }
  }

  .upload-container {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    margin-bottom: 32px;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }

    .upload-card {
      .card-header {
        font-size: 18px;
        font-weight: 500;
      }

      .upload-form {
        .el-form-item {
          margin-bottom: 20px;
        }
      }
    }

    .tips-card {
      .tips-content {
        .tips-list {
          margin: 0;
          padding-left: 20px;
          color: #606266;

          li {
            margin-bottom: 8px;
            line-height: 1.5;
          }
        }
      }
    }
  }

  .recent-homework {
    .recent-list {
      .recent-item {
        display: flex;
        align-items: center;
        padding: 12px;
        border-radius: 6px;
        cursor: pointer;
        transition: background-color 0.3s;

        &:hover {
          background-color: #f5f7fa;
        }

        &:not(:last-child) {
          margin-bottom: 8px;
        }

        .recent-preview {
          width: 60px;
          height: 60px;
          border-radius: 4px;
          overflow: hidden;
          margin-right: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f5f5;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }

          .el-icon {
            font-size: 24px;
            color: #909399;
          }
        }

        .recent-info {
          flex: 1;
          min-width: 0;

          .recent-title {
            font-size: 14px;
            color: #303133;
            margin-bottom: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .recent-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: #909399;

            .subject {
              color: #409eff;
            }
          }
        }

        .arrow-right {
          color: #c0c4cc;
          margin-left: 8px;
        }
      }
    }
  }
}
</style>
