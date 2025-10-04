<!-- 图片预览组件 -->
<template>
  <el-dialog
    v-model="visible"
    :show-close="false"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    fullscreen
    class="image-preview-dialog"
    @closed="handleClosed"
  >
    <div class="image-preview-container h-full flex flex-col bg-black bg-opacity-95">
      <!-- 顶部工具栏 -->
      <div class="toolbar flex items-center justify-between px-6 py-4 bg-black bg-opacity-50">
        <div class="flex items-center space-x-4 text-white">
          <span class="text-sm">{{ currentIndex + 1 }} / {{ images.length }}</span>
          <span v-if="currentImage?.alt" class="text-sm text-gray-300">{{ currentImage.alt }}</span>
        </div>

        <div class="flex items-center space-x-2">
          <!-- 缩放控制 -->
          <el-button-group>
            <el-button type="info" @click="handleZoomOut" :disabled="scale <= 0.5">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button type="info" @click="handleZoomIn" :disabled="scale >= 3">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
            <el-button type="info" @click="handleResetZoom">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </el-button-group>

          <!-- 旋转 -->
          <el-button type="info" @click="handleRotate">
            <el-icon><RefreshRight /></el-icon>
          </el-button>

          <!-- 下载 -->
          <el-button type="info" @click="handleDownload">
            <el-icon><Download /></el-icon>
          </el-button>

          <!-- 关闭 -->
          <el-button type="info" @click="visible = false">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 图片展示区 -->
      <div class="image-display flex-1 flex items-center justify-center relative overflow-hidden">
        <!-- 左箭头 -->
        <div
          v-if="images.length > 1"
          class="nav-button left absolute left-4 z-10"
          @click="handlePrev"
        >
          <el-button circle size="large" type="info">
            <el-icon size="24"><ArrowLeft /></el-icon>
          </el-button>
        </div>

        <!-- 图片 -->
        <div
          class="image-wrapper transition-transform duration-300 ease-in-out"
          :style="imageStyle"
          @mousedown="handleMouseDown"
          @wheel="handleWheel"
        >
          <img
            :src="currentImage?.url"
            :alt="currentImage?.alt || `图片 ${currentIndex + 1}`"
            class="max-w-full max-h-full object-contain select-none"
            draggable="false"
            @load="handleImageLoad"
            @error="handleImageError"
          />
        </div>

        <!-- 右箭头 -->
        <div
          v-if="images.length > 1"
          class="nav-button right absolute right-4 z-10"
          @click="handleNext"
        >
          <el-button circle size="large" type="info">
            <el-icon size="24"><ArrowRight /></el-icon>
          </el-button>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
          <el-icon class="animate-spin text-white text-4xl"><Loading /></el-icon>
        </div>

        <!-- 错误状态 -->
        <div
          v-if="error"
          class="absolute inset-0 flex flex-col items-center justify-center text-white"
        >
          <el-icon class="text-5xl mb-4"><WarningFilled /></el-icon>
          <p class="text-lg">图片加载失败</p>
          <el-button type="primary" class="mt-4" @click="handleRetry"> 重试 </el-button>
        </div>
      </div>

      <!-- 底部缩略图（多图时显示） -->
      <div v-if="normalizedImages.length > 1" class="thumbnails px-6 py-4 bg-black bg-opacity-50">
        <div class="flex items-center justify-center space-x-2 overflow-x-auto">
          <div
            v-for="(image, index) in normalizedImages"
            :key="index"
            class="thumbnail cursor-pointer border-2 transition-all rounded"
            :class="
              index === currentIndex
                ? 'border-blue-500 scale-110'
                : 'border-transparent opacity-60 hover:opacity-100'
            "
            @click="handleThumbnailClick(index)"
          >
            <img
              :src="image.url"
              :alt="image.alt || `缩略图 ${index + 1}`"
              class="w-16 h-16 object-cover rounded"
            />
          </div>
        </div>
      </div>

      <!-- 快捷键提示 -->
      <div class="shortcuts absolute bottom-20 left-6 text-xs text-gray-400 space-y-1">
        <div>← → 切换图片</div>
        <div>滚轮 缩放</div>
        <div>ESC 关闭</div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Close,
  ZoomIn,
  ZoomOut,
  FullScreen,
  RefreshRight,
  Download,
  ArrowLeft,
  ArrowRight,
  Loading,
  WarningFilled,
} from '@element-plus/icons-vue'

// 接口定义
interface ImageItem {
  url: string
  alt?: string
}

// Props
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    images: ImageItem[] | string[]
    initialIndex?: number
  }>(),
  {
    modelValue: false,
    images: () => [],
    initialIndex: 0,
  }
)

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'change', index: number): void
}>()

// 状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const currentIndex = ref(props.initialIndex)
const scale = ref(1)
const rotation = ref(0)
const translateX = ref(0)
const translateY = ref(0)
const loading = ref(false)
const error = ref(false)

// 拖拽状态
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)

// 计算属性
const normalizedImages = computed<ImageItem[]>(() => {
  return props.images.map((img) => (typeof img === 'string' ? { url: img } : img))
})

const currentImage = computed(() => normalizedImages.value[currentIndex.value])

const imageStyle = computed(() => ({
  transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value}) rotate(${rotation.value}deg)`,
  cursor: isDragging.value ? 'grabbing' : 'grab',
}))

// 监听索引变化
watch(currentIndex, (newIndex) => {
  emit('change', newIndex)
  resetTransform()
})

watch(
  () => props.initialIndex,
  (newIndex) => {
    currentIndex.value = newIndex
  }
)

// 方法
const handlePrev = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  } else {
    currentIndex.value = normalizedImages.value.length - 1
  }
}

const handleNext = () => {
  if (currentIndex.value < normalizedImages.value.length - 1) {
    currentIndex.value++
  } else {
    currentIndex.value = 0
  }
}

const handleThumbnailClick = (index: number) => {
  currentIndex.value = index
}

const handleZoomIn = () => {
  if (scale.value < 3) {
    scale.value = Math.min(scale.value + 0.25, 3)
  }
}

const handleZoomOut = () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(scale.value - 0.25, 0.5)
  }
}

const handleResetZoom = () => {
  resetTransform()
}

const handleRotate = () => {
  rotation.value = (rotation.value + 90) % 360
}

const handleDownload = async () => {
  if (!currentImage.value) return

  try {
    const response = await fetch(currentImage.value.url)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = currentImage.value.alt || `image-${currentIndex.value + 1}.jpg`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('下载失败:', err)
    ElMessage.error('图片下载失败')
  }
}

const handleWheel = (e: WheelEvent) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(0.5, Math.min(3, scale.value + delta))
}

const handleMouseDown = (e: MouseEvent) => {
  if (scale.value === 1) return

  isDragging.value = true
  dragStartX.value = e.clientX - translateX.value
  dragStartY.value = e.clientY - translateY.value

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging.value) return
    translateX.value = e.clientX - dragStartX.value
    translateY.value = e.clientY - dragStartY.value
  }

  const handleMouseUp = () => {
    isDragging.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

const handleImageLoad = () => {
  loading.value = false
  error.value = false
}

const handleImageError = () => {
  loading.value = false
  error.value = true
}

const handleRetry = () => {
  loading.value = true
  error.value = false
  // 触发重新加载
  const img = new Image()
  img.onload = handleImageLoad
  img.onerror = handleImageError
  img.src = currentImage.value?.url || ''
}

const resetTransform = () => {
  scale.value = 1
  rotation.value = 0
  translateX.value = 0
  translateY.value = 0
}

const handleClosed = () => {
  resetTransform()
}

// 键盘快捷键
const handleKeydown = (e: KeyboardEvent) => {
  if (!visible.value) return

  switch (e.key) {
    case 'ArrowLeft':
      handlePrev()
      break
    case 'ArrowRight':
      handleNext()
      break
    case 'Escape':
      visible.value = false
      break
    case '+':
    case '=':
      handleZoomIn()
      break
    case '-':
      handleZoomOut()
      break
    case '0':
      handleResetZoom()
      break
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<script lang="ts">
import { defineComponent, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'

export default defineComponent({
  name: 'ImagePreview',
})
</script>

<style scoped lang="scss">
.image-preview-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
    height: 100vh;
  }

  .toolbar {
    backdrop-filter: blur(10px);
  }

  .nav-button {
    &:hover {
      opacity: 1;
    }
  }

  .thumbnail {
    flex-shrink: 0;

    &:hover {
      transform: scale(1.05);
    }
  }

  .shortcuts {
    backdrop-filter: blur(10px);
    background: rgba(0, 0, 0, 0.5);
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
  }
}
</style>
