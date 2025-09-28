<template>
  <div class="homework-page">
    <!-- 页面头部 -->
    <div class="page-header mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">作业批改</h1>
          <p class="text-gray-600">上传作业图片，获得AI智能批改反馈</p>
        </div>
        <div class="header-actions">
          <el-button @click="showHistory = !showHistory">
            <el-icon class="mr-2">
              <Document />
            </el-icon>
            批改历史
          </el-button>
          <el-button type="primary" @click="openUploadDialog">
            <el-icon class="mr-2">
              <Upload />
            </el-icon>
            上传作业
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="homework-content" :class="{ 'with-sidebar': showHistory }">
      <!-- 左侧：上传区域和批改结果 -->
      <div class="main-content">
        <!-- 文件上传组件 -->
        <el-card v-if="!currentHomework" class="upload-card mb-6">
          <FileUpload
            @upload-success="handleUploadSuccess"
            @upload-error="handleUploadError"
            :loading="uploading"
          />
        </el-card>

        <!-- 批改结果显示 -->
        <div v-if="currentHomework" class="homework-result">
          <el-card class="result-card">
            <template #header>
              <div class="result-header">
                <h3 class="result-title">批改结果</h3>
                <div class="result-actions">
                  <el-button size="small" @click="downloadResult">
                    <el-icon class="mr-1">
                      <Download />
                    </el-icon>
                    下载报告
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    @click="openUploadDialog"
                  >
                    <el-icon class="mr-1">
                      <Upload />
                    </el-icon>
                    重新上传
                  </el-button>
                </div>
              </div>
            </template>

            <div class="result-content">
              <!-- 作业信息 -->
              <div class="homework-info mb-6">
                <div class="info-grid">
                  <div class="info-item">
                    <span class="info-label">科目</span>
                    <span class="info-value">{{
                      currentHomework.subject
                    }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">类型</span>
                    <span class="info-value">{{ currentHomework.type }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">批改时间</span>
                    <span class="info-value">{{
                      formatDate(currentHomework.correctedAt)
                    }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">总分</span>
                    <span class="info-value score"
                      >{{ currentHomework.score }}/100</span
                    >
                  </div>
                </div>
              </div>

              <!-- 原图和批改结果对比 -->
              <div class="image-comparison mb-6">
                <div class="image-container">
                  <div class="original-image">
                    <h4 class="image-title">原图</h4>
                    <img
                      :src="currentHomework.originalImage"
                      alt="原作业图片"
                    />
                  </div>
                  <div class="corrected-image">
                    <h4 class="image-title">批改结果</h4>
                    <img
                      :src="currentHomework.correctedImage"
                      alt="批改后图片"
                    />
                  </div>
                </div>
              </div>

              <!-- 详细分析 -->
              <div class="detailed-analysis">
                <h4 class="analysis-title">详细分析</h4>

                <!-- 总体评价 -->
                <div class="overall-evaluation mb-4">
                  <el-alert
                    :title="currentHomework.overallEvaluation.title"
                    :description="currentHomework.overallEvaluation.description"
                    :type="currentHomework.overallEvaluation.type"
                    show-icon
                    :closable="false"
                  />
                </div>

                <!-- 逐题分析 -->
                <div class="question-analysis">
                  <div
                    v-for="(question, index) in currentHomework.questions"
                    :key="index"
                    class="question-item"
                  >
                    <div class="question-header">
                      <span class="question-number">第{{ index + 1 }}题</span>
                      <el-tag
                        :type="question.correct ? 'success' : 'danger'"
                        size="small"
                      >
                        {{ question.correct ? "正确" : "错误" }}
                      </el-tag>
                      <span class="question-score">{{ question.score }}分</span>
                    </div>

                    <div class="question-content">
                      <p class="question-text">{{ question.question }}</p>

                      <div class="answer-section" v-if="question.studentAnswer">
                        <div class="answer-item">
                          <span class="answer-label">学生答案:</span>
                          <span class="answer-text student-answer">{{
                            question.studentAnswer
                          }}</span>
                        </div>
                      </div>

                      <div class="answer-section" v-if="question.correctAnswer">
                        <div class="answer-item">
                          <span class="answer-label">正确答案:</span>
                          <span class="answer-text correct-answer">{{
                            question.correctAnswer
                          }}</span>
                        </div>
                      </div>

                      <div class="explanation" v-if="question.explanation">
                        <div class="explanation-header">
                          <el-icon><InfoFilled /></el-icon>
                          <span>解析</span>
                        </div>
                        <p class="explanation-text">
                          {{ question.explanation }}
                        </p>
                      </div>

                      <div
                        class="suggestions"
                        v-if="
                          question.suggestions && question.suggestions.length
                        "
                      >
                        <div class="suggestions-header">
                          <el-icon><InfoFilled /></el-icon>
                          <span>建议</span>
                        </div>
                        <ul class="suggestions-list">
                          <li
                            v-for="suggestion in question.suggestions"
                            :key="suggestion"
                          >
                            {{ suggestion }}
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 学习建议 -->
                <div
                  class="learning-suggestions"
                  v-if="currentHomework.learningSuggestions"
                >
                  <h4 class="suggestions-title">学习建议</h4>
                  <div class="suggestions-content">
                    <div
                      v-for="(
                        category, key
                      ) in currentHomework.learningSuggestions"
                      :key="key"
                      class="suggestion-category"
                    >
                      <div class="category-header">
                        <el-icon><Star /></el-icon>
                        <span class="category-title">{{
                          getSuggestionCategoryTitle(key)
                        }}</span>
                      </div>
                      <ul class="category-items">
                        <li v-for="item in category" :key="item">{{ item }}</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 右侧：历史记录 -->
      <div v-if="showHistory" class="sidebar">
        <el-card class="history-card">
          <template #header>
            <div class="history-header">
              <h3>批改历史</h3>
              <el-button size="small" text @click="refreshHistory">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <div class="history-content">
            <div class="history-filters mb-4">
              <el-select
                v-model="historyFilter.subject"
                placeholder="选择科目"
                size="small"
                @change="filterHistory"
              >
                <el-option label="全部" value="" />
                <el-option label="数学" value="数学" />
                <el-option label="语文" value="语文" />
                <el-option label="英语" value="英语" />
                <el-option label="物理" value="物理" />
              </el-select>
            </div>

            <div class="history-list">
              <div
                v-for="item in filteredHistory"
                :key="item.id"
                class="history-item"
                @click="loadHomework(item)"
              >
                <div class="item-header">
                  <span class="item-subject">{{ item.subject }}</span>
                  <span class="item-date">{{
                    formatDate(item.correctedAt)
                  }}</span>
                </div>
                <div class="item-score">{{ item.score }}分</div>
                <div class="item-preview">{{ item.type }}</div>
              </div>
            </div>

            <div v-if="filteredHistory.length === 0" class="empty-history">
              <el-empty description="暂无批改记录" :image-size="100" />
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传作业"
      width="600px"
      :close-on-click-modal="false"
    >
      <FileUpload
        @upload-success="handleDialogUploadSuccess"
        @upload-error="handleUploadError"
        :loading="uploading"
        :show-history="false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  Document,
  Upload,
  Download,
  Refresh,
  InfoFilled,
  Star,
} from "@element-plus/icons-vue";
import FileUpload from "@/components/FileUpload.vue";

// 响应式数据
const showHistory = ref(false);
const uploadDialogVisible = ref(false);
const uploading = ref(false);
// 定义作业结果类型
interface HomeworkResult {
  id: number;
  subject: string;
  type: string;
  score: number;
  correctedAt: Date;
  originalImage: string;
  correctedImage: string;
  overallEvaluation: {
    title: string;
    description: string;
    type: "success" | "warning" | "info" | "error";
  };
  questions: Array<{
    question: string;
    studentAnswer: string;
    correctAnswer: string;
    correct: boolean;
    score: number;
    explanation: string;
    suggestions: string[];
  }>;
  learningSuggestions: {
    strengths: string[];
    improvements: string[];
    practice: string[];
    resources: string[];
  };
}

const currentHomework = ref<HomeworkResult | null>(null);

// 历史记录相关
const homeworkHistory = ref([
  {
    id: 1,
    subject: "数学",
    type: "微积分练习",
    score: 92,
    correctedAt: new Date(2025, 0, 25),
    originalImage: "/api/placeholder/600/800",
    correctedImage: "/api/placeholder/600/800",
  },
  {
    id: 2,
    subject: "语文",
    type: "古诗词默写",
    score: 88,
    correctedAt: new Date(2025, 0, 24),
    originalImage: "/api/placeholder/600/800",
    correctedImage: "/api/placeholder/600/800",
  },
]);

const historyFilter = ref({
  subject: "",
});

// 计算属性
const filteredHistory = computed(() => {
  if (!historyFilter.value.subject) {
    return homeworkHistory.value;
  }
  return homeworkHistory.value.filter(
    (item) => item.subject === historyFilter.value.subject,
  );
});

// 方法
const openUploadDialog = () => {
  uploadDialogVisible.value = true;
};

const handleUploadSuccess = (result: any) => {
  uploading.value = false;
  currentHomework.value = mockCorrectionResult(result);
  ElMessage.success("作业上传成功，批改完成！");
};

const handleDialogUploadSuccess = (result: any) => {
  uploadDialogVisible.value = false;
  handleUploadSuccess(result);
};

const handleUploadError = (error: any) => {
  uploading.value = false;
  ElMessage.error("上传失败：" + error.message);
};

const loadHomework = (homework: any) => {
  currentHomework.value = mockDetailedResult(homework);
};

const downloadResult = () => {
  ElMessage.success("报告下载中...");
};

const refreshHistory = () => {
  ElMessage.info("刷新历史记录...");
};

const filterHistory = () => {
  // 过滤逻辑已通过计算属性实现
};

const formatDate = (date: Date) => {
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getSuggestionCategoryTitle = (key: string) => {
  const titles = {
    strengths: "优势项",
    improvements: "需要改进",
    practice: "练习建议",
    resources: "学习资源",
  };
  return titles[key as keyof typeof titles] || key;
};

// 模拟批改结果
const mockCorrectionResult = (uploadResult: any): HomeworkResult => {
  return {
    id: Date.now(),
    subject: "数学",
    type: "代数练习",
    score: 85,
    correctedAt: new Date(),
    originalImage: uploadResult.url,
    correctedImage: uploadResult.url,
    overallEvaluation: {
      title: "总体表现良好",
      description: "基础概念掌握较好，计算准确度需要提升",
      type: "success" as const,
    },
    questions: [
      {
        question: "解方程：2x + 5 = 13",
        studentAnswer: "x = 4",
        correctAnswer: "x = 4",
        correct: true,
        score: 10,
        explanation: "解题步骤正确，答案准确。",
        suggestions: [],
      },
      {
        question: "计算：(3x + 2)(x - 1)",
        studentAnswer: "3x² - x + 2",
        correctAnswer: "3x² - x - 2",
        correct: false,
        score: 6,
        explanation: "展开公式应用正确，但计算过程中符号错误。",
        suggestions: ["注意分配律计算时的符号变化", "建议多练习多项式乘法运算"],
      },
    ],
    learningSuggestions: {
      strengths: ["基础概念理解清晰", "解题思路正确"],
      improvements: ["计算准确度", "符号运算"],
      practice: ["多做类似的多项式运算题", "加强心算能力"],
      resources: ["《代数基础练习册》第3章", "在线练习平台代数模块"],
    },
  };
};

const mockDetailedResult = (homework: any): HomeworkResult => {
  return {
    ...homework,
    overallEvaluation: {
      title: "总体表现优秀",
      description: "解题思路清晰，基础扎实",
      type: "success" as const,
    },
    questions: [
      {
        question: "示例题目",
        studentAnswer: "学生答案",
        correctAnswer: "正确答案",
        correct: true,
        score: 10,
        explanation: "解题正确，步骤清晰。",
        suggestions: [],
      },
    ],
    learningSuggestions: {
      strengths: ["解题思路清晰"],
      improvements: ["可以提升解题速度"],
      practice: ["多做类似题型"],
      resources: ["相关学习资料"],
    },
  };
};

// 生命周期
onMounted(() => {
  // 初始化页面
});
</script>

<style scoped lang="scss">
.homework-page {
  padding: 24px;
  background-color: #f8fafc;
  min-height: 100vh;

  @media (max-width: 768px) {
    padding: 16px;
  }
}

.page-header {
  .header-actions {
    display: flex;
    gap: 12px;

    @media (max-width: 768px) {
      flex-direction: column;
      width: 100%;
      margin-top: 16px;
    }
  }
}

.homework-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;

  &.with-sidebar {
    grid-template-columns: 1fr 320px;

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;

      .sidebar {
        order: -1;
      }
    }
  }
}

.upload-card {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-card {
  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .result-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #111827;
    }

    .result-actions {
      display: flex;
      gap: 8px;

      @media (max-width: 768px) {
        flex-direction: column;
      }
    }
  }
}

.homework-info {
  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;

    @media (max-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .info-item {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .info-label {
        font-size: 14px;
        color: #6b7280;
        font-weight: 500;
      }

      .info-value {
        font-size: 16px;
        color: #111827;
        font-weight: 600;

        &.score {
          color: #10b981;
          font-size: 18px;
        }
      }
    }
  }
}

.image-comparison {
  .image-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
      gap: 16px;
    }

    .original-image,
    .corrected-image {
      .image-title {
        font-size: 16px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 12px;
        text-align: center;
      }

      img {
        width: 100%;
        max-height: 500px;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      }
    }
  }
}

.detailed-analysis {
  .analysis-title {
    font-size: 18px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 16px;
  }

  .question-analysis {
    .question-item {
      background: #f9fafb;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;

      &:last-child {
        margin-bottom: 0;
      }

      .question-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;

        .question-number {
          font-weight: 600;
          color: #374151;
        }

        .question-score {
          margin-left: auto;
          font-weight: 600;
          color: #6b7280;
        }
      }

      .question-content {
        .question-text {
          font-size: 16px;
          color: #111827;
          margin-bottom: 12px;
          font-weight: 500;
        }

        .answer-section {
          margin-bottom: 12px;

          .answer-item {
            display: flex;
            gap: 8px;
            align-items: flex-start;

            @media (max-width: 768px) {
              flex-direction: column;
              gap: 4px;
            }

            .answer-label {
              font-weight: 500;
              color: #6b7280;
              min-width: 80px;
              flex-shrink: 0;
            }

            .answer-text {
              flex: 1;

              &.student-answer {
                color: #3b82f6;
              }

              &.correct-answer {
                color: #10b981;
              }
            }
          }
        }

        .explanation,
        .suggestions {
          background: white;
          border-radius: 6px;
          padding: 12px;
          margin-top: 12px;

          .explanation-header,
          .suggestions-header {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
            font-size: 14px;
          }

          .explanation-text {
            color: #6b7280;
            line-height: 1.6;
            margin: 0;
          }

          .suggestions-list {
            margin: 0;
            padding-left: 16px;
            color: #6b7280;

            li {
              margin-bottom: 4px;
              line-height: 1.5;
            }
          }
        }
      }
    }
  }

  .learning-suggestions {
    background: #f0f9ff;
    border-radius: 8px;
    padding: 20px;
    margin-top: 20px;

    .suggestions-title {
      font-size: 18px;
      font-weight: 600;
      color: #1e40af;
      margin-bottom: 16px;
    }

    .suggestion-category {
      margin-bottom: 16px;

      &:last-child {
        margin-bottom: 0;
      }

      .category-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;

        .category-title {
          font-weight: 600;
          color: #1e40af;
        }
      }

      .category-items {
        margin: 0;
        padding-left: 20px;
        color: #1e40af;

        li {
          margin-bottom: 4px;
          line-height: 1.5;
        }
      }
    }
  }
}

// 侧边栏样式
.sidebar {
  .history-card {
    height: fit-content;
    position: sticky;
    top: 24px;

    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }
  }

  .history-content {
    max-height: 600px;
    overflow-y: auto;

    .history-filters {
      .el-select {
        width: 100%;
      }
    }

    .history-list {
      .history-item {
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid #f3f4f6;

        &:hover {
          background-color: #f9fafb;
          border-color: #e5e7eb;
        }

        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;

          .item-subject {
            font-weight: 500;
            color: #374151;
          }

          .item-date {
            font-size: 12px;
            color: #9ca3af;
          }
        }

        .item-score {
          font-size: 18px;
          font-weight: 600;
          color: #10b981;
          margin-bottom: 4px;
        }

        .item-preview {
          font-size: 12px;
          color: #6b7280;
        }
      }
    }

    .empty-history {
      padding: 40px 0;
      text-align: center;
    }
  }
}
</style>
