<!--
  作业详情页面
-->
<template>
  <div class="homework-detail-page">
    <!-- 加载状态 -->
    <div v-if="homeworkStore.detailLoading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 作业详情 -->
    <div v-else-if="homework" class="detail-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <el-button type="text" :icon="ArrowLeft" @click="goBack">
          返回
        </el-button>
        <div class="header-info">
          <h1 class="homework-title">
            {{ homework.title || "未命名作业" }}
          </h1>
          <div class="homework-meta">
            <el-tag :type="getStatusTagType(homework.status)">
              {{ getStatusLabel(homework.status) }}
            </el-tag>
            <span class="subject">{{ getSubjectLabel(homework.subject) }}</span>
            <span class="grade">{{ getGradeLabel(homework.grade_level) }}</span>
            <span class="time">{{ formatTime(homework.created_at) }}</span>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            v-if="homework.status === 'failed'"
            type="primary"
            :loading="homeworkStore.correctLoading"
            @click="retryCorrection"
          >
            重新批改
          </el-button>
          <el-button
            v-else-if="homework.status === 'submitted'"
            type="primary"
            :loading="homeworkStore.correctLoading"
            @click="startCorrection"
          >
            开始批改
          </el-button>
          <el-dropdown trigger="click">
            <el-button type="text" :icon="MoreFilled" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="downloadImages"
                  >下载图片</el-dropdown-item
                >
                <el-dropdown-item @click="exportResult"
                  >导出结果</el-dropdown-item
                >
                <el-dropdown-item divided @click="deleteHomework"
                  >删除作业</el-dropdown-item
                >
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 主要内容 -->
      <div class="main-content">
        <!-- 左侧：原始图片和OCR结果 -->
        <div class="left-panel">
          <!-- 原始图片 -->
          <el-card class="images-card">
            <template #header>
              <span
                ><el-icon><Picture /></el-icon> 作业图片 ({{
                  homework.original_images?.length || 0
                }}张)</span
              >
            </template>
            <div
              v-if="homework.original_images?.length"
              class="images-container"
            >
              <div
                v-for="(image, index) in homework.original_images"
                :key="index"
                class="image-item"
                @click="previewImage(image, index)"
              >
                <img :src="image" :alt="`作业图片 ${index + 1}`" />
                <div class="image-overlay">
                  <el-icon><ZoomIn /></el-icon>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无图片" />
          </el-card>

          <!-- OCR识别结果 -->
          <el-card v-if="homework.ocr_text" class="ocr-card">
            <template #header>
              <span
                ><el-icon><Document /></el-icon> OCR识别文本</span
              >
              <el-button
                type="text"
                size="small"
                @click="copyText(homework.ocr_text)"
              >
                复制
              </el-button>
            </template>
            <div class="ocr-content">
              <pre>{{ homework.ocr_text }}</pre>
            </div>
          </el-card>
        </div>

        <!-- 右侧：批改结果 -->
        <div class="right-panel">
          <!-- 处理中状态 -->
          <div v-if="homework.status === 'processing'" class="processing-state">
            <el-card>
              <div class="processing-content">
                <el-icon class="processing-icon"><Loading /></el-icon>
                <h3>AI正在批改中...</h3>
                <p>请耐心等待，通常需要1-3分钟</p>
                <el-progress
                  :percentage="processingProgress"
                  :show-text="false"
                />
              </div>
            </el-card>
          </div>

          <!-- 批改结果 -->
          <div
            v-else-if="homework.correction_result"
            class="correction-results"
          >
            <!-- 总体评分 -->
            <el-card class="score-card">
              <div class="score-display">
                <div class="score-circle">
                  <el-progress
                    type="circle"
                    :width="120"
                    :percentage="homework.correction_result.score"
                    :color="getScoreColor(homework.correction_result.score)"
                  >
                    <span class="score-text"
                      >{{ homework.correction_result.score }}分</span
                    >
                  </el-progress>
                </div>
                <div class="score-info">
                  <div class="correct-status">
                    <el-icon
                      :class="
                        homework.correction_result.is_correct
                          ? 'correct-icon'
                          : 'incorrect-icon'
                      "
                    >
                      <component
                        :is="
                          homework.correction_result.is_correct
                            ? CircleCheck
                            : CircleClose
                        "
                      />
                    </el-icon>
                    <span class="status-text">
                      {{
                        homework.correction_result.is_correct
                          ? "答案正确"
                          : "答案有误"
                      }}
                    </span>
                  </div>
                  <div class="difficulty">
                    难度等级：{{ homework.correction_result.difficulty_level }}
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 批改意见 -->
            <el-card
              v-if="homework.correction_result.corrections?.length"
              class="corrections-card"
            >
              <template #header>
                <span
                  ><el-icon><Edit /></el-icon> 批改意见</span
                >
              </template>
              <div class="corrections-list">
                <div
                  v-for="(correction, index) in homework.correction_result
                    .corrections"
                  :key="index"
                  class="correction-item"
                >
                  <el-icon class="item-icon"><Right /></el-icon>
                  <span>{{ correction }}</span>
                </div>
              </div>
            </el-card>

            <!-- 错误分析 -->
            <el-card
              v-if="homework.correction_result.error_analysis"
              class="error-card"
            >
              <template #header>
                <span
                  ><el-icon><Warning /></el-icon> 错误分析</span
                >
              </template>
              <div class="error-content">
                {{ homework.correction_result.error_analysis }}
              </div>
            </el-card>

            <!-- 知识点分析 -->
            <el-card
              v-if="homework.correction_result.knowledge_points?.length"
              class="knowledge-card"
            >
              <template #header>
                <span
                  ><el-icon><Collection /></el-icon> 涉及知识点</span
                >
              </template>
              <div class="knowledge-tags">
                <el-tag
                  v-for="point in homework.correction_result.knowledge_points"
                  :key="point"
                  type="info"
                  class="knowledge-tag"
                >
                  {{ point }}
                </el-tag>
              </div>
            </el-card>

            <!-- 学习建议 -->
            <el-card
              v-if="homework.correction_result.suggestions?.length"
              class="suggestions-card"
            >
              <template #header>
                <span
                  ><el-icon><Star /></el-icon> 学习建议</span
                >
              </template>
              <div class="suggestions-list">
                <div
                  v-for="(suggestion, index) in homework.correction_result
                    .suggestions"
                  :key="index"
                  class="suggestion-item"
                >
                  <el-icon class="item-icon"><Star /></el-icon>
                  <span>{{ suggestion }}</span>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 等待批改状态 -->
          <div
            v-else-if="homework.status === 'submitted'"
            class="waiting-state"
          >
            <el-card>
              <div class="waiting-content">
                <el-icon class="waiting-icon"><Clock /></el-icon>
                <h3>等待批改</h3>
                <p>点击"开始批改"按钮开始AI智能批改</p>
                <el-button type="primary" @click="startCorrection">
                  开始批改
                </el-button>
              </div>
            </el-card>
          </div>

          <!-- 失败状态 -->
          <div v-else-if="homework.status === 'failed'" class="error-state">
            <el-card>
              <div class="error-content">
                <el-icon class="error-icon"><CircleClose /></el-icon>
                <h3>批改失败</h3>
                <p>很抱歉，AI批改过程中出现了问题，请重试</p>
                <el-button type="primary" @click="retryCorrection">
                  重新批改
                </el-button>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </div>

    <!-- 404状态 -->
    <div v-else class="not-found">
      <el-result
        icon="warning"
        title="作业不存在"
        sub-title="该作业可能已被删除或不存在"
      >
        <template #extra>
          <el-button type="primary" @click="goBack">返回</el-button>
        </template>
      </el-result>
    </div>

    <!-- 图片预览 -->
    <el-image-viewer
      v-if="showImageViewer"
      :url-list="homework?.original_images || []"
      :initial-index="currentImageIndex"
      @close="closeImageViewer"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  ArrowLeft,
  MoreFilled,
  Picture,
  Document,
  Loading,
  Edit,
  Warning,
  Collection,
  Right,
  Star,
  Clock,
  CircleCheck,
  CircleClose,
  ZoomIn,
} from "@element-plus/icons-vue";
import dayjs from "dayjs";

import { useHomeworkStore } from "@/stores/homework";
import {
  HOMEWORK_SUBJECT_OPTIONS,
  GRADE_LEVEL_OPTIONS,
  STATUS_OPTIONS,
  type HomeworkStatus,
  type SubjectOption,
} from "@/types/homework";

const route = useRoute();
const router = useRouter();
const homeworkStore = useHomeworkStore();

// 响应式数据
const showImageViewer = ref(false);
const currentImageIndex = ref(0);
const processingProgress = ref(0);
let processingInterval: NodeJS.Timeout | null = null;

// 计算属性
const homework = computed(() => homeworkStore.currentHomework);

// 生命周期
onMounted(async () => {
  const homeworkId = route.params.id as string;
  await homeworkStore.getHomeworkDetail(homeworkId);

  // 如果作业在处理中，开始模拟进度
  if (homework.value?.status === "processing") {
    startProcessingAnimation();
  }
});

onUnmounted(() => {
  if (processingInterval) {
    clearInterval(processingInterval);
  }
});

// 开始处理动画
const startProcessingAnimation = () => {
  processingProgress.value = 10;
  processingInterval = setInterval(() => {
    if (processingProgress.value < 90) {
      processingProgress.value += Math.random() * 10;
    }
  }, 1000);
};

// 返回
const goBack = () => {
  router.go(-1);
};

// 开始批改
const startCorrection = async () => {
  if (!homework.value) return;

  const result = await homeworkStore.correctHomework(homework.value.id);
  if (result) {
    ElMessage.success("批改完成！");
  }
};

// 重新批改
const retryCorrection = async () => {
  if (!homework.value) return;

  const result = await homeworkStore.retryCorrection(homework.value.id);
  if (result) {
    ElMessage.success("重新批改完成！");
  }
};

// 删除作业
const deleteHomework = async () => {
  if (!homework.value) return;

  try {
    await ElMessageBox.confirm(
      "确定要删除这个作业吗？删除后无法恢复。",
      "确认删除",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    await homeworkStore.deleteHomework(homework.value.id);
    ElMessage.success("作业删除成功");
    goBack();
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除作业失败:", error);
    }
  }
};

// 预览图片
const previewImage = (_image: string, index: number) => {
  currentImageIndex.value = index;
  showImageViewer.value = true;
};

// 关闭图片预览
const closeImageViewer = () => {
  showImageViewer.value = false;
};

// 复制文本
const copyText = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success("复制成功");
  } catch (error) {
    ElMessage.error("复制失败");
  }
};

// 下载图片
const downloadImages = () => {
  if (!homework.value?.original_images?.length) {
    ElMessage.warning("暂无图片可下载");
    return;
  }

  homework.value.original_images.forEach((url, index) => {
    const link = document.createElement("a");
    link.href = url;
    link.download = `作业图片_${index + 1}.jpg`;
    link.click();
  });
};

// 导出结果
const exportResult = () => {
  // TODO: 实现导出功能
  ElMessage.info("导出功能开发中...");
};

// 获取学科标签
const getSubjectLabel = (subject: string): string => {
  const option = HOMEWORK_SUBJECT_OPTIONS.find(
    (opt: SubjectOption) => opt.value === subject,
  );
  return option?.label || subject;
};

// 获取年级标签
const getGradeLabel = (grade: number): string => {
  const option = GRADE_LEVEL_OPTIONS.find((opt) => opt.value === grade);
  return option?.label || `${grade}年级`;
};

// 获取状态标签
const getStatusLabel = (status: HomeworkStatus): string => {
  const option = STATUS_OPTIONS.find((opt) => opt.value === status);
  return option?.label || status;
};

// 获取状态标签类型
const getStatusTagType = (
  status: HomeworkStatus,
): "success" | "primary" | "warning" | "info" | "danger" => {
  const typeMap: Record<
    HomeworkStatus,
    "success" | "primary" | "warning" | "info" | "danger"
  > = {
    submitted: "info",
    processing: "warning",
    completed: "success",
    failed: "danger",
  };
  return typeMap[status] || "info";
};

// 获取分数颜色
const getScoreColor = (score: number): string => {
  if (score >= 90) return "#67c23a";
  if (score >= 80) return "#e6a23c";
  if (score >= 60) return "#f56c6c";
  return "#909399";
};

// 格式化时间
const formatTime = (time: string): string => {
  return dayjs(time).format("YYYY-MM-DD HH:mm:ss");
};
</script>

<style scoped lang="scss">
.homework-detail-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;

  .loading-container {
    padding: 40px;
  }

  .detail-container {
    .page-header {
      display: flex;
      align-items: center;
      margin-bottom: 24px;
      padding: 20px 0;
      border-bottom: 1px solid #ebeef5;

      .header-info {
        flex: 1;
        margin: 0 20px;

        .homework-title {
          font-size: 24px;
          color: #303133;
          margin: 0 0 8px 0;
        }

        .homework-meta {
          display: flex;
          align-items: center;
          gap: 16px;
          font-size: 14px;
          color: #606266;

          .subject {
            color: #409eff;
            font-weight: 500;
          }
        }
      }

      .header-actions {
        display: flex;
        gap: 12px;
      }
    }

    .main-content {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;

      @media (max-width: 1024px) {
        grid-template-columns: 1fr;
      }

      .left-panel {
        .images-card {
          margin-bottom: 24px;

          .images-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 16px;

            .image-item {
              position: relative;
              aspect-ratio: 1;
              border-radius: 8px;
              overflow: hidden;
              cursor: pointer;
              transition: transform 0.3s;

              &:hover {
                transform: scale(1.02);

                .image-overlay {
                  opacity: 1;
                }
              }

              img {
                width: 100%;
                height: 100%;
                object-fit: cover;
              }

              .image-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.3s;

                .el-icon {
                  font-size: 24px;
                  color: white;
                }
              }
            }
          }
        }

        .ocr-card {
          .ocr-content {
            pre {
              white-space: pre-wrap;
              word-wrap: break-word;
              font-family: inherit;
              font-size: 14px;
              line-height: 1.6;
              color: #606266;
              background: #f5f7fa;
              padding: 16px;
              border-radius: 4px;
              margin: 0;
            }
          }
        }
      }

      .right-panel {
        .processing-state,
        .waiting-state,
        .error-state {
          .processing-content,
          .waiting-content,
          .error-content {
            text-align: center;
            padding: 40px 20px;

            .processing-icon,
            .waiting-icon,
            .error-icon {
              font-size: 48px;
              margin-bottom: 16px;
            }

            .processing-icon {
              color: #409eff;
              animation: spin 1s linear infinite;
            }

            .waiting-icon {
              color: #909399;
            }

            .error-icon {
              color: #f56c6c;
            }

            h3 {
              color: #303133;
              margin: 0 0 8px 0;
            }

            p {
              color: #606266;
              margin: 0 0 20px 0;
            }
          }
        }

        .correction-results {
          .score-card {
            margin-bottom: 24px;

            .score-display {
              display: flex;
              align-items: center;
              gap: 24px;

              .score-circle {
                .score-text {
                  font-size: 18px;
                  font-weight: 600;
                }
              }

              .score-info {
                .correct-status {
                  display: flex;
                  align-items: center;
                  gap: 8px;
                  margin-bottom: 8px;

                  .correct-icon {
                    color: #67c23a;
                    font-size: 20px;
                  }

                  .incorrect-icon {
                    color: #f56c6c;
                    font-size: 20px;
                  }

                  .status-text {
                    font-size: 16px;
                    font-weight: 500;
                  }
                }

                .difficulty {
                  color: #606266;
                  font-size: 14px;
                }
              }
            }
          }

          .corrections-card,
          .suggestions-card {
            margin-bottom: 24px;

            .corrections-list,
            .suggestions-list {
              .correction-item,
              .suggestion-item {
                display: flex;
                align-items: flex-start;
                gap: 8px;
                padding: 8px 0;
                line-height: 1.6;

                &:not(:last-child) {
                  border-bottom: 1px solid #f0f0f0;
                }

                .item-icon {
                  color: #409eff;
                  margin-top: 2px;
                  flex-shrink: 0;
                }
              }
            }
          }

          .error-card {
            margin-bottom: 24px;

            .error-content {
              line-height: 1.6;
              color: #606266;
              background: #fef0f0;
              padding: 16px;
              border-radius: 4px;
              border-left: 4px solid #f56c6c;
            }
          }

          .knowledge-card {
            margin-bottom: 24px;

            .knowledge-tags {
              display: flex;
              flex-wrap: wrap;
              gap: 8px;

              .knowledge-tag {
                margin: 0;
              }
            }
          }
        }
      }
    }
  }

  .not-found {
    padding: 60px 20px;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
