<template>
  <div class="question-input bg-white">
    <!-- 高级设置展开按钮 -->
    <div class="flex items-center justify-between mb-3">
      <el-button
        type="text"
        size="small"
        @click="showAdvanced = !showAdvanced"
        class="text-gray-600 hover:text-blue-600"
      >
        <el-icon class="mr-1">
          <ArrowUp v-if="showAdvanced" />
          <ArrowDown v-else />
        </el-icon>
        {{ showAdvanced ? "简化模式" : "高级设置" }}
      </el-button>

      <!-- 字数统计 -->
      <div class="text-xs text-gray-500">{{ questionText.length }}/5000</div>
    </div>

    <!-- 高级设置面板 -->
    <el-collapse-transition>
      <div
        v-show="showAdvanced"
        class="advanced-settings mb-4 p-4 bg-gray-50 rounded-lg"
      >
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- 问题类型 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2"
              >问题类型</label
            >
            <el-select
              v-model="questionData.question_type"
              placeholder="选择问题类型"
              size="small"
              clearable
              class="w-full"
            >
              <el-option
                v-for="type in questionTypeOptions"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              >
                <div class="flex items-center">
                  <el-icon class="mr-2 text-gray-500">
                    <component :is="type.icon" />
                  </el-icon>
                  {{ type.label }}
                </div>
              </el-option>
            </el-select>
          </div>

          <!-- 学科选择 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2"
              >学科</label
            >
            <el-select
              v-model="questionData.subject"
              placeholder="选择学科"
              size="small"
              clearable
              class="w-full"
            >
              <el-option
                v-for="subject in subjectOptions"
                :key="subject.value"
                :label="subject.label"
                :value="subject.value"
              >
                <div class="flex items-center">
                  <div
                    class="w-3 h-3 rounded-full mr-2"
                    :style="{ backgroundColor: subject.color }"
                  />
                  {{ subject.label }}
                </div>
              </el-option>
            </el-select>
          </div>

          <!-- 难度级别 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2"
              >难度级别</label
            >
            <el-select
              v-model="questionData.difficulty_level"
              placeholder="选择难度"
              size="small"
              clearable
              class="w-full"
            >
              <el-option
                v-for="level in difficultyOptions"
                :key="level.value"
                :label="level.label"
                :value="level.value"
              >
                <div class="flex items-center justify-between w-full">
                  <span>{{ level.label }}</span>
                  <div class="flex">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="w-2 h-2 rounded-full ml-1"
                      :class="i <= level.value ? 'bg-current' : 'bg-gray-200'"
                      :style="{ color: level.color }"
                    />
                  </div>
                </div>
              </el-option>
            </el-select>
          </div>
        </div>

        <!-- 高级选项 -->
        <div class="mt-4 flex items-center space-x-6">
          <el-checkbox v-model="questionData.use_context" size="small">
            使用学习上下文
          </el-checkbox>
          <el-checkbox v-model="questionData.include_history" size="small">
            包含历史对话
          </el-checkbox>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-700">历史消息数:</span>
            <el-input-number
              v-model="questionData.max_history"
              :min="0"
              :max="50"
              :step="5"
              size="small"
              class="w-20"
            />
          </div>
        </div>

        <!-- 话题输入 -->
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >知识点/话题</label
          >
          <el-input
            v-model="questionData.topic"
            placeholder="如：二次函数、现在完成时、牛顿定律等"
            size="small"
            maxlength="100"
            show-word-limit
            clearable
          />
        </div>
      </div>
    </el-collapse-transition>

    <!-- 图片上传区域 -->
    <div v-if="imageFiles.length > 0" class="image-preview mb-3">
      <div class="flex flex-wrap gap-3">
        <div
          v-for="(file, index) in imageFiles"
          :key="index"
          class="relative group"
        >
          <img
            :src="file.preview"
            :alt="`图片 ${index + 1}`"
            class="w-20 h-20 object-cover rounded-lg border border-gray-200"
          />
          <el-button
            type="danger"
            size="small"
            circle
            @click="removeImage(index)"
            class="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <el-icon><Close /></el-icon>
          </el-button>
          <div
            v-if="file.uploading"
            class="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center"
          >
            <el-icon class="text-white animate-spin"><Loading /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 主输入区域 -->
    <div class="input-area">
      <div class="relative">
        <!-- 文本输入框 -->
        <el-input
          v-model="questionText"
          type="textarea"
          :rows="textareaRows"
          :maxlength="5000"
          :placeholder="inputPlaceholder"
          :disabled="disabled"
          resize="none"
          class="question-textarea"
          @keydown="handleKeyDown"
          @focus="handleFocus"
          @blur="handleBlur"
          @input="handleInput"
        />

        <!-- 工具栏 -->
        <div
          class="toolbar absolute bottom-3 right-3 flex items-center space-x-2"
        >
          <!-- 图片上传 -->
          <el-upload
            ref="imageUploadRef"
            :show-file-list="false"
            :before-upload="handleImageUpload"
            accept="image/*"
            multiple
            :limit="5"
          >
            <el-button type="text" size="small" :disabled="disabled">
              <el-icon class="text-gray-500 hover:text-blue-500">
                <Picture />
              </el-icon>
            </el-button>
          </el-upload>

          <!-- 发送按钮 -->
          <el-button
            type="primary"
            size="small"
            :disabled="!canSubmit"
            :loading="loading"
            @click="handleSubmit"
            class="send-button"
          >
            <el-icon v-if="!loading"><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
    </div>

    <!-- 输入提示 -->
    <div
      class="input-hints mt-2 text-xs text-gray-500 flex items-center justify-between"
    >
      <div class="flex items-center space-x-4">
        <span>Shift + Enter 换行</span>
        <span>Enter 发送</span>
        <span v-if="questionData.question_type">
          类型: {{ getQuestionTypeLabel(questionData.question_type) }}
        </span>
      </div>

      <div class="flex items-center space-x-2">
        <span v-if="imageFiles.length > 0">
          {{ imageFiles.length }}/5 张图片
        </span>
        <el-button
          v-if="questionText.trim() || imageFiles.length > 0"
          type="text"
          size="small"
          @click="clearAll"
          class="text-red-500 hover:text-red-700"
        >
          清空
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick } from "vue";
import { ElMessage, type UploadRawFile } from "element-plus";
import {
  ArrowUp,
  ArrowDown,
  Close,
  Loading,
  Picture,
  Promotion,
} from "@element-plus/icons-vue";

// 类型导入
import type { AskQuestionRequest } from "@/types/learning";
import {
  QUESTION_TYPE_OPTIONS,
  LEARNING_SUBJECT_OPTIONS,
  DIFFICULTY_OPTIONS,
  QuestionType,
} from "@/types/learning";

// ========== 接口定义 ==========

interface ImageFile {
  file: File;
  preview: string;
  url?: string;
  uploading: boolean;
}

interface Props {
  disabled?: boolean;
  loading?: boolean;
}

interface Emits {
  (e: "submit", request: AskQuestionRequest): void;
}

// ========== Props和Emits ==========

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  loading: false,
});

const emit = defineEmits<Emits>();

// ========== 响应式数据 ==========

const questionText = ref("");
const showAdvanced = ref(false);
const isFocused = ref(false);
const imageUploadRef = ref();

// 问题数据
const questionData = reactive<Partial<AskQuestionRequest>>({
  question_type: undefined,
  subject: undefined,
  difficulty_level: undefined,
  topic: "",
  use_context: true,
  include_history: true,
  max_history: 10,
});

// 图片文件
const imageFiles = ref<ImageFile[]>([]);

// 选项数据
const questionTypeOptions = QUESTION_TYPE_OPTIONS;
const subjectOptions = LEARNING_SUBJECT_OPTIONS;
const difficultyOptions = DIFFICULTY_OPTIONS;

// ========== 计算属性 ==========

const inputPlaceholder = computed(() => {
  if (props.disabled) return "正在处理中，请稍候...";
  if (props.loading) return "AI正在思考中...";

  const examples = [
    "请解释一下这个数学概念...",
    "帮我分析这道题的解题思路...",
    "这个英语语法该如何理解？",
    "请帮我检查作业中的错误...",
  ];

  return examples[Math.floor(Math.random() * examples.length)];
});

const textareaRows = computed(() => {
  const lines = questionText.value.split("\n").length;
  const minRows = 2;
  const maxRows = 8;
  return Math.min(maxRows, Math.max(minRows, lines));
});

const canSubmit = computed(() => {
  return (
    !props.disabled &&
    !props.loading &&
    (questionText.value.trim().length > 0 || imageFiles.value.length > 0) &&
    questionText.value.length <= 5000
  );
});

// ========== 工具函数 ==========

const getQuestionTypeLabel = (type: string) => {
  const option = questionTypeOptions.find((opt) => opt.value === type);
  return option?.label || type;
};

const generatePreviewUrl = (file: File): Promise<string> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.readAsDataURL(file);
  });
};

// ========== 事件处理 ==========

const handleKeyDown = (event: Event | KeyboardEvent) => {
  if (
    event instanceof KeyboardEvent &&
    event.key === "Enter" &&
    !event.shiftKey
  ) {
    event.preventDefault();
    if (canSubmit.value) {
      handleSubmit();
    }
  }
};

const handleFocus = () => {
  isFocused.value = true;
};

const handleBlur = () => {
  isFocused.value = false;
};

const handleInput = () => {
  // 自动调整高度在computed中处理
};

const handleImageUpload = async (file: UploadRawFile): Promise<boolean> => {
  // 验证文件类型
  if (!file.type.startsWith("image/")) {
    ElMessage.error("只能上传图片文件");
    return false;
  }

  // 验证文件大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error("图片大小不能超过 10MB");
    return false;
  }

  // 检查数量限制
  if (imageFiles.value.length >= 5) {
    ElMessage.error("最多只能上传 5 张图片");
    return false;
  }

  try {
    // 生成预览URL
    const preview = await generatePreviewUrl(file);

    // 添加到图片列表
    const imageFile: ImageFile = {
      file,
      preview,
      uploading: true,
    };
    imageFiles.value.push(imageFile);

    // 模拟上传过程
    setTimeout(async () => {
      try {
        // TODO: 实际的图片上传逻辑
        // const uploadedUrl = await uploadImage(file)
        // imageFile.url = uploadedUrl
        imageFile.uploading = false;
        ElMessage.success("图片上传成功");
      } catch (error) {
        console.error("上传图片失败:", error);
        ElMessage.error("图片上传失败");
        removeImageByFile(imageFile);
      }
    }, 1500);
  } catch (error) {
    console.error("处理图片失败:", error);
    ElMessage.error("处理图片失败");
  }

  return false; // 阻止默认上传行为
};

const removeImage = (index: number) => {
  imageFiles.value.splice(index, 1);
};

const removeImageByFile = (imageFile: ImageFile) => {
  const index = imageFiles.value.indexOf(imageFile);
  if (index > -1) {
    imageFiles.value.splice(index, 1);
  }
};

const clearAll = () => {
  questionText.value = "";
  imageFiles.value = [];

  // 重置高级设置为默认值
  Object.assign(questionData, {
    question_type: undefined,
    subject: undefined,
    difficulty_level: undefined,
    topic: "",
    use_context: true,
    include_history: true,
    max_history: 10,
  });
};

const handleSubmit = async () => {
  if (!canSubmit.value) return;

  const trimmedText = questionText.value.trim();
  if (!trimmedText && imageFiles.value.length === 0) {
    ElMessage.warning("请输入问题内容或上传图片");
    return;
  }

  // 检查是否有图片还在上传中
  if (imageFiles.value.some((img) => img.uploading)) {
    ElMessage.warning("请等待图片上传完成");
    return;
  }

  try {
    // 构建请求数据
    const request: AskQuestionRequest = {
      content: trimmedText,
      question_type: questionData.question_type || QuestionType.GENERAL_INQUIRY,
      subject: questionData.subject,
      topic: questionData.topic || undefined,
      difficulty_level: questionData.difficulty_level,
      image_urls: imageFiles.value
        .map((img) => img.url)
        .filter(Boolean) as string[],
      use_context: questionData.use_context,
      include_history: questionData.include_history,
      max_history: questionData.max_history,
    };

    // 发射提交事件
    emit("submit", request);

    // 清空输入内容
    questionText.value = "";
    imageFiles.value = [];

    // 收起高级设置
    showAdvanced.value = false;
  } catch (error) {
    console.error("提交问题失败:", error);
    ElMessage.error("提交失败，请重试");
  }
};

// ========== 暴露的方法 ==========

defineExpose({
  clearAll,
  focus: () => {
    nextTick(() => {
      const textarea = document.querySelector(
        ".question-textarea textarea",
      ) as HTMLElement;
      textarea?.focus();
    });
  },
});
</script>

<style scoped lang="scss">
.question-input {
  .question-textarea {
    :deep(.el-textarea__inner) {
      padding: 12px 80px 12px 12px;
      border-radius: 12px;
      border: 1px solid #e5e7eb;
      font-size: 14px;
      line-height: 1.5;
      resize: none;
      transition: all 0.2s ease;

      &:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
      }

      &::placeholder {
        color: #9ca3af;
      }
    }
  }

  .toolbar {
    .send-button {
      border-radius: 8px;
      padding: 6px 12px;
      font-size: 12px;

      &:not(:disabled):hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
      }
    }
  }

  .advanced-settings {
    border: 1px solid #e5e7eb;

    .el-select,
    .el-input {
      :deep(.el-input__inner) {
        border-radius: 6px;
        border: 1px solid #d1d5db;
      }
    }
  }

  .image-preview {
    img {
      transition: all 0.2s ease;

      &:hover {
        transform: scale(1.05);
      }
    }
  }

  .input-hints {
    span {
      &:not(:last-child) {
        position: relative;

        &::after {
          content: "•";
          margin-left: 8px;
          color: #d1d5db;
        }
      }
    }
  }
}

// 动画
.el-collapse-transition {
  transition: all 0.3s ease;
}
</style>
