<!--
  文件上传组件
  支持拖拽上传、多文件选择、预览、进度显示
-->
<template>
  <div class="file-upload-container">
    <!-- 上传区域 -->
    <div
      class="upload-area"
      :class="{
        'upload-area--dragover': isDragover,
        'upload-area--disabled': disabled,
      }"
      @drop.prevent="handleDrop"
      @dragover.prevent="handleDragover"
      @dragleave.prevent="handleDragleave"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        :accept="accept"
        :multiple="multiple"
        :disabled="disabled"
        style="display: none"
        @change="handleFileSelect"
      />

      <div class="upload-content">
        <el-icon class="upload-icon">
          <UploadFilled />
        </el-icon>
        <div class="upload-text">
          <div class="upload-title">
            {{ isDragover ? "释放文件开始上传" : "点击或拖拽文件到此处上传" }}
          </div>
          <div class="upload-hint">
            支持 {{ acceptText }} 格式，单个文件不超过
            {{ formatFileSize(maxSize) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list">
      <div v-for="(file, index) in fileList" :key="index" class="file-item">
        <!-- 图片预览 -->
        <div class="file-preview">
          <img
            v-if="file.file.type.startsWith('image/')"
            :src="file.url || getFilePreviewUrl(file.file)"
            :alt="file.file.name"
            class="preview-image"
          />
          <el-icon v-else class="file-icon">
            <Document />
          </el-icon>
        </div>

        <!-- 文件信息 -->
        <div class="file-info">
          <div class="file-name" :title="file.file.name">
            {{ file.file.name }}
          </div>
          <div class="file-meta">
            <span class="file-size">{{ formatFileSize(file.file.size) }}</span>
            <span class="file-status" :class="`status-${file.status}`">
              {{ getStatusText(file.status) }}
            </span>
          </div>

          <!-- 上传进度 -->
          <div v-if="file.status === 'uploading'" class="upload-progress">
            <el-progress
              :percentage="file.progress || 0"
              :stroke-width="4"
              :show-text="false"
            />
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="file-actions">
          <el-tooltip content="删除" placement="top">
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              circle
              @click="removeFile(index)"
            />
          </el-tooltip>
        </div>
      </div>
    </div>

    <!-- 上传按钮 -->
    <div v-if="fileList.length > 0 && !autoUpload" class="upload-actions">
      <el-button
        type="primary"
        :loading="uploading"
        :disabled="!hasValidFiles"
        @click="startUpload"
      >
        {{ uploading ? "上传中..." : `上传 ${validFileCount} 个文件` }}
      </el-button>
      <el-button @click="clearFiles">清空</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { ElMessage } from "element-plus";
import { UploadFilled, Document, Delete } from "@element-plus/icons-vue";

// 文件上传项接口
export interface FileUploadItem {
  file: File;
  status: "waiting" | "uploading" | "success" | "error";
  progress?: number;
  url?: string;
  response?: any;
}

// 组件Props
interface Props {
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // 字节
  maxCount?: number;
  disabled?: boolean;
  autoUpload?: boolean;
  beforeUpload?: (file: File) => boolean | Promise<boolean>;
  onUpload?: (files: File[]) => Promise<string[]>;
}

const props = withDefaults(defineProps<Props>(), {
  accept: "image/*",
  multiple: true,
  maxSize: 10 * 1024 * 1024, // 10MB
  maxCount: 9,
  disabled: false,
  autoUpload: false,
});

// 组件Events
const emit = defineEmits<{
  change: [files: FileUploadItem[]];
  success: [files: FileUploadItem[]];
  error: [error: Error];
}>();

// 响应式数据
const fileInputRef = ref<HTMLInputElement>();
const fileList = ref<FileUploadItem[]>([]);
const isDragover = ref(false);
const uploading = ref(false);

// 计算属性
const acceptText = computed(() => {
  if (props.accept === "image/*") return "图片";
  if (props.accept.includes("image/")) return "图片";
  return "文件";
});

const hasValidFiles = computed(() => {
  return fileList.value.some((file) => file.status === "waiting");
});

const validFileCount = computed(() => {
  return fileList.value.filter((file) => file.status === "waiting").length;
});

// 监听文件列表变化
watch(
  fileList,
  () => {
    emit("change", fileList.value);
  },
  { deep: true }
);

// 文件大小格式化
const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
};

// 获取状态文本
const getStatusText = (status: FileUploadItem["status"]): string => {
  const statusMap = {
    waiting: "等待上传",
    uploading: "上传中",
    success: "上传成功",
    error: "上传失败",
  };
  return statusMap[status];
};

// 获取文件预览URL
const getFilePreviewUrl = (file: File): string => {
  return URL.createObjectURL(file);
};

// 验证文件
const validateFile = (file: File): boolean => {
  // 检查文件类型
  if (
    props.accept !== "*" &&
    !file.type.match(props.accept.replace("*", ".*"))
  ) {
    ElMessage.error(`文件格式不支持，请选择 ${acceptText.value} 文件`);
    return false;
  }

  // 检查文件大小
  if (file.size > props.maxSize) {
    ElMessage.error(`文件大小不能超过 ${formatFileSize(props.maxSize)}`);
    return false;
  }

  // 检查文件数量
  if (fileList.value.length >= props.maxCount) {
    ElMessage.error(`最多只能上传 ${props.maxCount} 个文件`);
    return false;
  }

  return true;
};

// 添加文件到列表
const addFiles = async (files: File[]) => {
  for (const file of files) {
    if (!validateFile(file)) continue;

    // 执行beforeUpload钩子
    if (props.beforeUpload) {
      try {
        const result = await props.beforeUpload(file);
        if (!result) continue;
      } catch (error) {
        console.error("beforeUpload error:", error);
        continue;
      }
    }

    const uploadItem: FileUploadItem = {
      file,
      status: "waiting",
      progress: 0,
    };

    fileList.value.push(uploadItem);

    // 自动上传
    if (props.autoUpload) {
      uploadSingleFile(uploadItem);
    }
  }
};

// 上传单个文件
const uploadSingleFile = async (item: FileUploadItem) => {
  if (!props.onUpload) {
    ElMessage.error("未配置上传处理函数");
    return;
  }

  try {
    item.status = "uploading";
    item.progress = 0;

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (item.progress! < 90) {
        item.progress = item.progress! + Math.random() * 20;
      }
    }, 200);

    const urls = await props.onUpload([item.file]);

    clearInterval(progressInterval);
    item.status = "success";
    item.progress = 100;
    item.url = urls[0];
  } catch (error) {
    item.status = "error";
    console.error("Upload error:", error);
    ElMessage.error(`文件 ${item.file.name} 上传失败`);
  }
};

// 开始上传
const startUpload = async () => {
  if (!props.onUpload) {
    ElMessage.error("未配置上传处理函数");
    return;
  }

  const waitingFiles = fileList.value.filter(
    (item) => item.status === "waiting"
  );
  if (waitingFiles.length === 0) return;

  try {
    uploading.value = true;

    for (const item of waitingFiles) {
      await uploadSingleFile(item);
    }

    const successFiles = fileList.value.filter(
      (item) => item.status === "success"
    );
    emit("success", successFiles);
  } catch (error) {
    emit("error", error as Error);
  } finally {
    uploading.value = false;
  }
};

// 移除文件
const removeFile = (index: number) => {
  fileList.value.splice(index, 1);
};

// 清空文件
const clearFiles = () => {
  fileList.value = [];
};

// 触发文件选择
const triggerFileInput = () => {
  if (props.disabled) return;
  fileInputRef.value?.click();
};

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    addFiles(Array.from(target.files));
    target.value = ""; // 清空input，允许重复选择同一文件
  }
};

// 处理拖拽
const handleDragover = (event: DragEvent) => {
  event.preventDefault();
  isDragover.value = true;
};

const handleDragleave = (event: DragEvent) => {
  event.preventDefault();
  isDragover.value = false;
};

const handleDrop = (event: DragEvent) => {
  event.preventDefault();
  isDragover.value = false;

  if (props.disabled) return;

  const files = Array.from(event.dataTransfer?.files || []);
  if (files.length > 0) {
    addFiles(files);
  }
};

// 暴露给父组件的方法
defineExpose({
  startUpload,
  clearFiles,
  getFiles: () => fileList.value,
  getValidFiles: () =>
    fileList.value.filter((item) => item.status === "success"),
});
</script>

<style scoped lang="scss">
.file-upload-container {
  .upload-area {
    border: 2px dashed #d9d9d9;
    border-radius: 8px;
    background: #fafafa;
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;

    &:hover:not(.upload-area--disabled) {
      border-color: #409eff;
      background: #f0f9ff;
    }

    &.upload-area--dragover {
      border-color: #409eff;
      background: #f0f9ff;
    }

    &.upload-area--disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }
  }

  .upload-content {
    .upload-icon {
      font-size: 48px;
      color: #c0c4cc;
      margin-bottom: 16px;
    }

    .upload-title {
      font-size: 16px;
      color: #606266;
      margin-bottom: 8px;
    }

    .upload-hint {
      font-size: 14px;
      color: #909399;
    }
  }

  .file-list {
    margin-top: 16px;
  }

  .file-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    margin-bottom: 8px;
    background: #fff;

    .file-preview {
      width: 60px;
      height: 60px;
      margin-right: 12px;
      border-radius: 4px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f5f5;

      .preview-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .file-icon {
        font-size: 24px;
        color: #909399;
      }
    }

    .file-info {
      flex: 1;
      min-width: 0;

      .file-name {
        font-size: 14px;
        color: #303133;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .file-meta {
        display: flex;
        align-items: center;
        font-size: 12px;
        color: #909399;

        .file-size {
          margin-right: 12px;
        }

        .file-status {
          &.status-waiting {
            color: #909399;
          }

          &.status-uploading {
            color: #409eff;
          }

          &.status-success {
            color: #67c23a;
          }

          &.status-error {
            color: #f56c6c;
          }
        }
      }

      .upload-progress {
        margin-top: 8px;
      }
    }

    .file-actions {
      margin-left: 12px;
    }
  }

  .upload-actions {
    margin-top: 16px;
    text-align: center;

    .el-button + .el-button {
      margin-left: 12px;
    }
  }
}
</style>
