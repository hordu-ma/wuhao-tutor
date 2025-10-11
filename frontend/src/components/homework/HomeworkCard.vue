<!-- 作业卡片组件 - 优化的卡片式展示 -->
<template>
  <div
    class="homework-card"
    :class="{
      'card-selected': selected,
      'card-clickable': !disableClick,
    }"
    @click="handleCardClick"
  >
    <!-- 选择框 -->
    <div v-if="showCheckbox" class="card-checkbox" @click.stop>
      <el-checkbox :model-value="selected" @change="handleSelect" />
    </div>

    <!-- 卡片内容 -->
    <div class="card-body">
      <!-- 图片预览区 -->
      <div class="image-preview" @click.stop="handleImageClick">
        <div v-if="homework.original_images?.length" class="image-wrapper">
          <img
            :src="homework.original_images[0]"
            :alt="homework.title || '作业图片'"
            class="preview-image"
          />
          <div class="image-count" v-if="homework.original_images.length > 1">
            <el-icon><Picture /></el-icon>
            {{ homework.original_images.length }}
          </div>
          <div class="image-overlay">
            <el-icon class="zoom-icon"><ZoomIn /></el-icon>
          </div>
        </div>
        <div v-else class="no-image">
          <el-icon class="placeholder-icon"><Document /></el-icon>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="card-content">
        <!-- 标题和状态 -->
        <div class="content-header">
          <h3 class="homework-title" :title="homework.title || '未命名作业'">
            {{ homework.title || '未命名作业' }}
          </h3>
          <el-tag :type="statusType" size="small" effect="dark">
            {{ statusLabel }}
          </el-tag>
        </div>

        <!-- 元信息 -->
        <div class="metadata">
          <div class="meta-item">
            <el-icon class="meta-icon"><Collection /></el-icon>
            <span>{{ subjectLabel }}</span>
          </div>
          <div class="meta-item">
            <el-icon class="meta-icon"><School /></el-icon>
            <span>{{ gradeLabel }}</span>
          </div>
          <div class="meta-item">
            <el-icon class="meta-icon"><Clock /></el-icon>
            <span>{{ formattedTime }}</span>
          </div>
        </div>

        <!-- 描述 -->
        <p v-if="homework.description" class="description" :title="homework.description">
          {{ homework.description }}
        </p>

        <!-- 批改结果摘要 -->
        <div v-if="homework.correction_result" class="correction-summary">
          <div class="score-badge" :class="scoreClass">
            <el-icon class="score-icon">
              <component
                :is="homework.correction_result.is_correct ? 'CircleCheck' : 'CircleClose'"
              />
            </el-icon>
            <span class="score-value">{{ homework.correction_result.score }}分</span>
          </div>

          <div v-if="homework.correction_result.knowledge_points?.length" class="knowledge-tags">
            <el-tag
              v-for="point in homework.correction_result.knowledge_points.slice(0, 2)"
              :key="point"
              size="small"
              type="info"
            >
              {{ point }}
            </el-tag>
            <span
              v-if="homework.correction_result.knowledge_points.length > 2"
              class="more-indicator"
            >
              +{{ homework.correction_result.knowledge_points.length - 2 }}
            </span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions" @click.stop>
        <el-button
          v-if="homework.status === 'submitted'"
          type="primary"
          size="small"
          @click="$emit('start-correction', homework.id)"
        >
          开始批改
        </el-button>
        <el-button
          v-else-if="homework.status === 'failed'"
          type="warning"
          size="small"
          @click="$emit('retry-correction', homework.id)"
        >
          重新批改
        </el-button>
        <el-button v-else type="default" size="small" @click="$emit('view-detail', homework.id)">
          查看详情
        </el-button>

        <el-dropdown trigger="click" @command="handleCommand">
          <el-button type="text" size="small" :icon="MoreFilled" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="view">
                <el-icon><View /></el-icon>
                查看详情
              </el-dropdown-item>
              <el-dropdown-item command="edit">
                <el-icon><Edit /></el-icon>
                编辑信息
              </el-dropdown-item>
              <el-dropdown-item command="rename">
                <el-icon><EditPen /></el-icon>
                重命名
              </el-dropdown-item>
              <el-dropdown-item command="download">
                <el-icon><Download /></el-icon>
                下载图片
              </el-dropdown-item>
              <el-dropdown-item divided command="delete">
                <el-icon class="text-red-500"><Delete /></el-icon>
                <span class="text-red-500">删除</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Picture,
  Document,
  Collection,
  Clock,
  ZoomIn,
  MoreFilled,
  View,
  Edit,
  EditPen,
  Download,
  Delete,
  School,
} from '@element-plus/icons-vue'
import {
  HOMEWORK_SUBJECT_OPTIONS,
  GRADE_LEVEL_OPTIONS,
  type HomeworkRecord,
} from '@/types/homework'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

interface Props {
  homework: HomeworkRecord
  selected?: boolean
  showCheckbox?: boolean
  disableClick?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selected: false,
  showCheckbox: false,
  disableClick: false,
})

// Emits
const emit = defineEmits<{
  (e: 'select', value: boolean): void
  (e: 'click'): void
  (e: 'view-detail', id: string): void
  (e: 'edit', homework: HomeworkRecord): void
  (e: 'rename', homework: HomeworkRecord): void
  (e: 'delete', id: string): void
  (e: 'download', id: string): void
  (e: 'preview-image', url: string, index: number): void
  (e: 'start-correction', id: string): void
  (e: 'retry-correction', id: string): void
}>()

// 计算属性
const statusType = computed(() => {
  const typeMap: Record<string, any> = {
    submitted: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return typeMap[props.homework.status] || 'info'
})

const statusLabel = computed(() => {
  const labelMap: Record<string, string> = {
    submitted: '待批改',
    processing: '批改中',
    completed: '已完成',
    failed: '失败',
  }
  return labelMap[props.homework.status] || '未知'
})

const subjectLabel = computed(() => {
  const option = HOMEWORK_SUBJECT_OPTIONS.find((opt) => opt.value === props.homework.subject)
  return option?.label || props.homework.subject
})

const gradeLabel = computed(() => {
  const gradeNum = Number(props.homework.grade_level)
  const option = GRADE_LEVEL_OPTIONS.find((opt) => opt.value === gradeNum)
  return option?.label || `${props.homework.grade_level}年级`
})

const formattedTime = computed(() => {
  return dayjs(props.homework.created_at).fromNow()
})

const scoreClass = computed(() => {
  if (!props.homework.correction_result) return ''
  const score = props.homework.correction_result.score
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-pass'
  return 'score-fail'
})

// 方法
const handleSelect = (value: boolean | string | number) => {
  emit('select', Boolean(value))
}

const handleCardClick = () => {
  if (!props.disableClick) {
    emit('click')
  }
}

const handleImageClick = () => {
  if (props.homework.original_images?.length) {
    emit('preview-image', props.homework.original_images[0], 0)
  }
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'view':
      emit('view-detail', props.homework.id)
      break
    case 'edit':
      emit('edit', props.homework)
      break
    case 'rename':
      emit('rename', props.homework)
      break
    case 'download':
      emit('download', props.homework.id)
      break
    case 'delete':
      emit('delete', props.homework.id)
      break
  }
}
</script>

<style scoped lang="scss">
.homework-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;

  &.card-clickable {
    cursor: pointer;

    &:hover {
      border-color: #3b82f6;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
      transform: translateY(-2px);
    }
  }

  &.card-selected {
    border-color: #3b82f6;
    background: #eff6ff;
  }

  .card-checkbox {
    position: absolute;
    top: 12px;
    left: 12px;
    z-index: 10;
  }

  .card-body {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .image-preview {
    position: relative;
    width: 100%;
    height: 180px;
    background: #f3f4f6;
    overflow: hidden;

    .image-wrapper {
      position: relative;
      width: 100%;
      height: 100%;

      .preview-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .image-count {
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .image-overlay {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s;

        .zoom-icon {
          font-size: 32px;
          color: white;
        }
      }

      &:hover .image-overlay {
        opacity: 1;
      }
    }

    .no-image {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;

      .placeholder-icon {
        font-size: 48px;
        color: #9ca3af;
      }
    }
  }

  .card-content {
    padding: 16px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;

    .content-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;

      .homework-title {
        flex: 1;
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .metadata {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        color: #6b7280;

        .meta-icon {
          font-size: 14px;
        }
      }
    }

    .description {
      font-size: 14px;
      color: #6b7280;
      line-height: 1.5;
      margin: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      line-clamp: 2;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .correction-summary {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-top: 12px;
      border-top: 1px solid #e5e7eb;

      .score-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;

        &.score-excellent {
          background: #d1fae5;
          color: #065f46;
        }

        &.score-good {
          background: #dbeafe;
          color: #1e40af;
        }

        &.score-pass {
          background: #fef3c7;
          color: #92400e;
        }

        &.score-fail {
          background: #fee2e2;
          color: #991b1b;
        }

        .score-icon {
          font-size: 16px;
        }
      }

      .knowledge-tags {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 6px;
        overflow: hidden;

        .more-indicator {
          font-size: 12px;
          color: #6b7280;
          white-space: nowrap;
        }
      }
    }
  }

  .card-actions {
    padding: 12px 16px;
    border-top: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    background: #f9fafb;
  }
}

@media (max-width: 768px) {
  .homework-card {
    .image-preview {
      height: 140px;
    }

    .card-content {
      padding: 12px;

      .homework-title {
        font-size: 14px;
      }

      .metadata {
        flex-direction: column;
        gap: 6px;
      }
    }
  }
}
</style>
