<template>
  <div class="learning-recommendations">
    <!-- 学习建议卡片 -->
    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 flex items-center">
          <el-icon class="text-blue-500 mr-2">
            <BellFilled />
          </el-icon>
          个性化学习建议
        </h3>
        <el-button
          size="small"
          type="primary"
          :icon="Refresh"
          @click="refreshRecommendations"
          :loading="loading"
        >
          刷新建议
        </el-button>
      </div>

      <div
        v-if="recommendations.length === 0 && !loading"
        class="text-center py-8"
      >
        <el-icon class="text-gray-400 text-4xl mb-2">
          <InfoFilled />
        </el-icon>
        <p class="text-gray-500">暂无个性化学习建议</p>
        <el-button
          type="primary"
          size="small"
          @click="refreshRecommendations"
          class="mt-2"
        >
          获取建议
        </el-button>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="recommendation in recommendations"
          :key="recommendation.id"
          class="recommendation-card p-4 rounded-lg border hover:shadow-md transition-all duration-200"
          :class="getPriorityCardClass(recommendation.priority)"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center space-x-2">
              <el-icon :class="getPriorityIconClass(recommendation.priority)">
                <Document />
              </el-icon>
              <div>
                <h4 class="font-medium text-gray-900">
                  {{ recommendation.title }}
                </h4>
                <div class="flex items-center space-x-3 mt-1">
                  <el-tag
                    :type="getPriorityType(recommendation.priority)"
                    size="small"
                  >
                    {{ getPriorityText(recommendation.priority) }}
                  </el-tag>
                  <span class="text-xs text-gray-500">
                    预计 {{ recommendation.estimatedTime }} 分钟
                  </span>
                  <span
                    v-if="recommendation.subject"
                    class="text-xs text-blue-600"
                  >
                    {{ recommendation.subject }}
                  </span>
                </div>
              </div>
            </div>
            <el-button
              type="text"
              :icon="MoreFilled"
              size="small"
              @click="acceptRecommendation(recommendation)"
            />
          </div>

          <p class="text-gray-700 text-sm leading-relaxed mb-3">
            {{ recommendation.description }}
          </p>

          <div
            v-if="recommendation.knowledgePoints?.length"
            class="flex flex-wrap gap-1 mb-3"
          >
            <el-tag
              v-for="point in recommendation.knowledgePoints"
              :key="point"
              size="small"
              effect="plain"
              type="info"
            >
              {{ point }}
            </el-tag>
          </div>

          <div class="flex items-center justify-between text-xs text-gray-500">
            <span>{{ formatTime(recommendation.createdAt) }}</span>
            <el-button
              size="small"
              type="primary"
              @click="acceptRecommendation(recommendation)"
            >
              开始学习
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 学习目标管理 -->
    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 flex items-center">
          <el-icon class="text-green-500 mr-2">
            <Flag />
          </el-icon>
          学习目标管理
        </h3>
        <el-button
          size="small"
          type="success"
          @click="showCreateGoalDialog = true"
        >
          <el-icon><Plus /></el-icon>
          新增目标
        </el-button>
      </div>

      <!-- 目标统计 -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="text-center p-3 bg-blue-50 rounded-lg">
          <div class="text-2xl font-bold text-blue-600">
            {{ activeGoals.length }}
          </div>
          <div class="text-sm text-gray-600">进行中</div>
        </div>
        <div class="text-center p-3 bg-green-50 rounded-lg">
          <div class="text-2xl font-bold text-green-600">
            {{ completedGoals.length }}
          </div>
          <div class="text-sm text-gray-600">已完成</div>
        </div>
        <div class="text-center p-3 bg-yellow-50 rounded-lg">
          <div class="text-2xl font-bold text-yellow-600">
            {{ completionRate }}%
          </div>
          <div class="text-sm text-gray-600">完成率</div>
        </div>
      </div>

      <!-- 目标列表 -->
      <div class="space-y-3">
        <div
          v-for="goal in displayGoals"
          :key="goal.id"
          class="goal-card p-4 border rounded-lg hover:shadow-sm transition-shadow"
          :class="getGoalCardClass(goal.status)"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex-1">
              <h4 class="font-medium text-gray-900 mb-1">{{ goal.title }}</h4>
              <p class="text-sm text-gray-600 mb-2">{{ goal.description }}</p>
              <div class="flex items-center space-x-4 text-xs text-gray-500">
                <span>{{ getGoalTypeText(goal.type) }}</span>
                <span>截止: {{ formatDate(goal.deadline) }}</span>
                <el-tag :type="getGoalStatusType(goal.status)" size="small">
                  {{ getGoalStatusText(goal.status) }}
                </el-tag>
              </div>
            </div>
          </div>

          <!-- 进度条 -->
          <div class="mb-2">
            <div class="flex justify-between text-xs text-gray-600 mb-1">
              <span>进度</span>
              <span
                >{{ goal.currentValue }}/{{ goal.targetValue }}
                {{ goal.unit }}</span
              >
            </div>
            <el-progress
              :percentage="getGoalProgress(goal)"
              :color="getProgressColor(goal.status)"
              :stroke-width="6"
            />
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="goals.length > displayGoals.length" class="text-center mt-4">
        <el-button type="text" @click="loadMoreGoals">查看更多目标</el-button>
      </div>
    </div>

    <!-- 创建目标对话框 -->
    <el-dialog
      v-model="showCreateGoalDialog"
      title="创建学习目标"
      width="500px"
      @close="resetGoalForm"
    >
      <el-form
        ref="goalFormRef"
        :model="goalForm"
        :rules="goalFormRules"
        label-width="80px"
      >
        <el-form-item label="目标标题" prop="title">
          <el-input
            v-model="goalForm.title"
            placeholder="请输入目标标题"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="目标描述" prop="description">
          <el-input
            v-model="goalForm.description"
            type="textarea"
            placeholder="请描述您的学习目标"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="目标类型" prop="type">
          <el-select v-model="goalForm.type" placeholder="请选择目标类型">
            <el-option label="每日目标" value="daily" />
            <el-option label="每周目标" value="weekly" />
            <el-option label="每月目标" value="monthly" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>

        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="目标值" prop="targetValue">
            <el-input-number
              v-model="goalForm.targetValue"
              :min="1"
              :max="10000"
              controls-position="right"
            />
          </el-form-item>

          <el-form-item label="单位" prop="unit">
            <el-select v-model="goalForm.unit" placeholder="选择单位">
              <el-option label="分钟" value="分钟" />
              <el-option label="小时" value="小时" />
              <el-option label="题目" value="题目" />
              <el-option label="章节" value="章节" />
              <el-option label="次数" value="次数" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="截止日期" prop="deadline">
          <el-date-picker
            v-model="goalForm.deadline"
            type="date"
            placeholder="选择截止日期"
            :disabled-date="disabledDate"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateGoalDialog = false">取消</el-button>
          <el-button type="primary" @click="submitGoal" :loading="submitting">
            创建目标
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useAnalyticsStore } from "../stores/analytics";
import {
  BellFilled,
  InfoFilled,
  Refresh,
  MoreFilled,
  Flag,
  Plus,
  Document,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import type { LearningRecommendation, LearningGoal } from "../types/analytics";
import dayjs from "dayjs";

const analyticsStore = useAnalyticsStore();

// 响应式数据
const loading = ref(false);
const showCreateGoalDialog = ref(false);
const submitting = ref(false);
const displayGoalCount = ref(5);

// 表单相关
const goalFormRef = ref<FormInstance>();
const goalForm = ref({
  title: "",
  description: "",
  type: "weekly",
  targetValue: 1,
  unit: "小时",
  deadline: "",
});

const goalFormRules: FormRules = {
  title: [
    { required: true, message: "请输入目标标题", trigger: "blur" },
    { min: 2, max: 50, message: "标题长度应在 2-50 字符", trigger: "blur" },
  ],
  description: [
    { required: true, message: "请输入目标描述", trigger: "blur" },
    { max: 200, message: "描述不能超过 200 字符", trigger: "blur" },
  ],
  type: [{ required: true, message: "请选择目标类型", trigger: "change" }],
  targetValue: [
    { required: true, message: "请输入目标值", trigger: "blur" },
    { type: "number", min: 1, message: "目标值必须大于 0", trigger: "blur" },
  ],
  unit: [{ required: true, message: "请选择单位", trigger: "change" }],
  deadline: [{ required: true, message: "请选择截止日期", trigger: "change" }],
};

// 计算属性
const recommendations = computed(() => analyticsStore.learningRecommendations);
const goals = computed(() => analyticsStore.learningGoals);
const activeGoals = computed(() => analyticsStore.activeGoals);
const completedGoals = computed(() => analyticsStore.completedGoals);

const displayGoals = computed(() => {
  return goals.value.slice(0, displayGoalCount.value);
});

const completionRate = computed(() => {
  const total = goals.value.length;
  if (total === 0) return 0;
  return Math.round((completedGoals.value.length / total) * 100);
});

// 获取优先级相关样式和文本
const getPriorityCardClass = (priority: string) => {
  switch (priority) {
    case "high":
      return "border-red-200 bg-red-50";
    case "medium":
      return "border-yellow-200 bg-yellow-50";
    case "low":
      return "border-blue-200 bg-blue-50";
    default:
      return "border-gray-200 bg-gray-50";
  }
};

const getPriorityIconClass = (priority: string) => {
  switch (priority) {
    case "high":
      return "text-red-500";
    case "medium":
      return "text-yellow-500";
    case "low":
      return "text-blue-500";
    default:
      return "text-gray-500";
  }
};

const getPriorityType = (priority: string) => {
  switch (priority) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    case "low":
      return "primary";
    default:
      return "info";
  }
};

const getPriorityText = (priority: string) => {
  switch (priority) {
    case "high":
      return "高优先级";
    case "medium":
      return "中优先级";
    case "low":
      return "低优先级";
    default:
      return "普通";
  }
};

// 获取目标相关样式和文本
const getGoalCardClass = (status: string) => {
  switch (status) {
    case "completed":
      return "border-green-200 bg-green-50";
    case "paused":
      return "border-gray-200 bg-gray-50";
    case "expired":
      return "border-red-200 bg-red-50";
    default:
      return "border-blue-200 bg-blue-50";
  }
};

const getGoalStatusType = (status: string) => {
  switch (status) {
    case "active":
      return "primary";
    case "completed":
      return "success";
    case "paused":
      return "info";
    case "expired":
      return "danger";
    default:
      return "info";
  }
};

const getGoalStatusText = (status: string) => {
  switch (status) {
    case "active":
      return "进行中";
    case "completed":
      return "已完成";
    case "paused":
      return "已暂停";
    case "expired":
      return "已过期";
    default:
      return "未知";
  }
};

const getGoalTypeText = (type: string) => {
  switch (type) {
    case "daily":
      return "每日目标";
    case "weekly":
      return "每周目标";
    case "monthly":
      return "每月目标";
    case "custom":
      return "自定义";
    default:
      return "未知";
  }
};

const getGoalProgress = (goal: LearningGoal) => {
  if (goal.targetValue === 0) return 0;
  return Math.min(
    Math.round((goal.currentValue / goal.targetValue) * 100),
    100,
  );
};

const getProgressColor = (status: string) => {
  switch (status) {
    case "completed":
      return "#10b981";
    case "active":
      return "#3b82f6";
    case "paused":
      return "#6b7280";
    case "expired":
      return "#ef4444";
    default:
      return "#3b82f6";
  }
};

// 时间格式化
const formatTime = (time: string) => {
  return dayjs(time).format("MM-DD HH:mm");
};

const formatDate = (date: string) => {
  return dayjs(date).format("YYYY-MM-DD");
};

const disabledDate = (time: Date) => {
  return time.getTime() < Date.now() - 24 * 60 * 60 * 1000;
};

// 事件处理方法
const refreshRecommendations = async () => {
  loading.value = true;
  try {
    await analyticsStore.fetchRecommendations(10);
    ElMessage.success("建议刷新成功");
  } catch (error) {
    ElMessage.error("建议刷新失败");
  } finally {
    loading.value = false;
  }
};

const acceptRecommendation = (recommendation: LearningRecommendation) => {
  ElMessage.success(`开始执行: ${recommendation.title}`);
};

const loadMoreGoals = () => {
  displayGoalCount.value += 5;
};

const submitGoal = () => {
  if (!goalFormRef.value) return;

  goalFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true;
      try {
        await analyticsStore.createGoal({
          ...goalForm.value,
          status: "active",
          deadline: dayjs(goalForm.value.deadline).toISOString(),
        } as any);
        ElMessage.success("目标创建成功");
        showCreateGoalDialog.value = false;
        resetGoalForm();
      } catch (error) {
        ElMessage.error("目标创建失败");
      } finally {
        submitting.value = false;
      }
    }
  });
};

const resetGoalForm = () => {
  goalForm.value = {
    title: "",
    description: "",
    type: "weekly",
    targetValue: 1,
    unit: "小时",
    deadline: "",
  };
  goalFormRef.value?.resetFields();
};

onMounted(() => {
  // 初始化数据
  if (recommendations.value.length === 0) {
    analyticsStore.fetchRecommendations();
  }
  if (goals.value.length === 0) {
    analyticsStore.fetchGoals();
  }
});
</script>

<style scoped>
.learning-recommendations {
  width: 100%;
}

.recommendation-card {
  transition: all 0.2s ease-in-out;
}

.recommendation-card:hover {
  transform: translateY(-1px);
}

.goal-card {
  transition: all 0.2s ease-in-out;
}

.goal-card:hover {
  transform: translateY(-1px);
}

.learning-recommendations :deep(.el-progress-bar__inner) {
  border-radius: 3px;
}

.learning-recommendations :deep(.el-tag) {
  border-radius: 4px;
}

.learning-recommendations :deep(.el-dialog__body) {
  padding: 20px 25px;
}
</style>
