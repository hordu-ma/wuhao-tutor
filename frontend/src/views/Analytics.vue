<template>
  <div class="analytics-page">
    <!-- 页面头部 -->
    <div class="page-header mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">学情分析</h1>
          <p class="text-gray-600">全面了解您的学习状况，获得个性化学习建议</p>
        </div>
        <div class="flex items-center space-x-3">
          <el-select
            v-model="selectedTimeRange"
            size="small"
            @change="handleTimeRangeChange"
          >
            <el-option label="最近7天" value="7d" />
            <el-option label="最近30天" value="30d" />
            <el-option label="最近90天" value="90d" />
          </el-select>
          <el-button
            type="primary"
            :icon="Refresh"
            @click="refreshAllData"
            :loading="loading"
            size="small"
          >
            刷新数据
          </el-button>
          <el-dropdown @command="handleExport">
            <el-button size="small">
              <el-icon><Download /></el-icon>
              导出报告
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="pdf">PDF报告</el-dropdown-item>
                <el-dropdown-item command="csv">CSV数据</el-dropdown-item>
                <el-dropdown-item command="json">JSON数据</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      @close="clearError"
      class="mb-4"
    />

    <!-- 加载状态 -->
    <div v-if="loading && !hasData" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 主要内容 -->
    <div v-else class="analytics-content">
      <!-- 概览统计卡片 -->
      <div class="overview-section mb-8">
        <h2 class="section-title">学习概览</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div
            v-for="stat in overviewStats"
            :key="stat.key"
            class="stat-card bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow"
          >
            <div class="flex items-center justify-between mb-4">
              <div class="stat-icon" :class="stat.colorClass">
                <el-icon :size="24">
                  <component :is="stat.icon" />
                </el-icon>
              </div>
              <div class="trend-indicator" :class="stat.trendClass">
                <el-icon :size="14">
                  <component :is="stat.trendIcon" />
                </el-icon>
                <span class="text-xs ml-1">{{ Math.abs(stat.trend) }}%</span>
              </div>
            </div>
            <div class="stat-value text-2xl font-bold text-gray-900 mb-1">
              {{ stat.value }}
            </div>
            <div class="stat-label text-sm text-gray-600">{{ stat.label }}</div>
          </div>
        </div>
      </div>

      <!-- 学习统计图表区域 -->
      <div class="charts-section mb-8">
        <h2 class="section-title">学习统计</h2>
        <LearningStatsChart :auto-refresh="true" />
      </div>

      <!-- 知识点掌握雷达图 -->
      <div class="knowledge-section mb-8">
        <h2 class="section-title">知识掌握分析</h2>
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div class="xl:col-span-2">
            <KnowledgeRadarChart :show-comparison="true" />
          </div>
          <div
            class="knowledge-summary bg-white rounded-lg p-6 shadow-sm border"
          >
            <h3 class="text-lg font-semibold text-gray-900 mb-4">掌握度总结</h3>
            <div class="space-y-4">
              <div
                v-for="category in knowledgeSummary"
                :key="category.level"
                class="summary-item"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium" :class="category.textClass">
                    {{ category.label }}
                  </span>
                  <span class="text-sm text-gray-600">
                    {{ category.count }}个知识点
                  </span>
                </div>
                <el-progress
                  :percentage="category.percentage"
                  :color="category.color"
                  :stroke-width="8"
                />
              </div>
            </div>

            <!-- 薄弱知识点列表 -->
            <div class="mt-6">
              <h4 class="text-md font-medium text-gray-900 mb-3">
                需要重点关注
              </h4>
              <div class="space-y-2">
                <div
                  v-for="point in weakKnowledgePoints.slice(0, 5)"
                  :key="point.id"
                  class="weak-point-item p-2 rounded-lg bg-red-50 border border-red-100"
                >
                  <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-800">{{ point.name }}</span>
                    <span class="text-xs text-red-600 font-medium">
                      {{ point.masteryLevel }}%
                    </span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    {{ point.subject }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 学习建议和目标管理 -->
      <div class="recommendations-section mb-8">
        <h2 class="section-title">学习建议与目标</h2>
        <LearningRecommendations />
      </div>

      <!-- 学习日历和成就 -->
      <div class="calendar-achievements-section">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 学习日历 -->
          <div class="calendar-card bg-white rounded-lg p-6 shadow-sm border">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">学习日历</h3>
              <div class="flex items-center space-x-2">
                <el-button
                  size="small"
                  :icon="ArrowLeft"
                  @click="previousMonth"
                  :disabled="loading"
                />
                <span class="text-sm font-medium px-2">
                  {{ currentMonth.format("YYYY年MM月") }}
                </span>
                <el-button
                  size="small"
                  :icon="ArrowRight"
                  @click="nextMonth"
                  :disabled="loading"
                />
              </div>
            </div>
            <div ref="calendarContainer" class="calendar-container">
              <!-- 这里可以集成一个日历组件显示学习活动 -->
              <div class="calendar-placeholder text-center py-8 text-gray-500">
                <el-icon :size="48" class="mb-2">
                  <Calendar />
                </el-icon>
                <p>学习日历功能开发中</p>
              </div>
            </div>
          </div>

          <!-- 成就系统 -->
          <div
            class="achievements-card bg-white rounded-lg p-6 shadow-sm border"
          >
            <h3 class="text-lg font-semibold text-gray-900 mb-4">学习成就</h3>
            <div class="achievements-grid grid grid-cols-3 gap-3">
              <div
                v-for="achievement in recentAchievements"
                :key="achievement.id"
                class="achievement-item"
                :class="achievement.unlocked ? 'unlocked' : 'locked'"
              >
                <div class="achievement-icon mb-2">
                  <el-icon :size="32">
                    <Trophy v-if="achievement.unlocked" />
                    <Lock v-else />
                  </el-icon>
                </div>
                <div class="achievement-name text-xs text-center font-medium">
                  {{ achievement.name }}
                </div>
                <div class="achievement-progress mt-1">
                  <el-progress
                    :percentage="Math.min(achievement.progress * 100, 100)"
                    :stroke-width="4"
                    :show-text="false"
                    :color="achievement.unlocked ? '#10b981' : '#d1d5db'"
                  />
                </div>
              </div>
            </div>
            <div class="achievements-footer mt-4 pt-4 border-t">
              <div class="flex justify-between text-sm text-gray-600">
                <span>已解锁: {{ unlockedCount }}/{{ totalAchievements }}</span>
                <el-button
                  type="text"
                  size="small"
                  @click="showAllAchievements"
                >
                  查看全部
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 学习洞察 -->
      <div class="insights-section mt-8">
        <h2 class="section-title">个人学习洞察</h2>
        <div class="bg-white rounded-lg p-6 shadow-sm border">
          <div v-if="personalInsights" class="insights-content">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="strengths">
                <h4
                  class="text-md font-semibold text-green-600 mb-3 flex items-center"
                >
                  <el-icon class="mr-2"><Check /></el-icon>
                  您的优势
                </h4>
                <ul class="space-y-2">
                  <li
                    v-for="strength in personalInsights.strengths"
                    :key="strength"
                    class="text-sm text-gray-700 flex items-start"
                  >
                    <span
                      class="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"
                    ></span>
                    {{ strength }}
                  </li>
                </ul>
              </div>
              <div class="improvements">
                <h4
                  class="text-md font-semibold text-yellow-600 mb-3 flex items-center"
                >
                  <el-icon class="mr-2"><Warning /></el-icon>
                  改进建议
                </h4>
                <ul class="space-y-2">
                  <li
                    v-for="suggestion in personalInsights.suggestions"
                    :key="suggestion"
                    class="text-sm text-gray-700 flex items-start"
                  >
                    <span
                      class="w-2 h-2 bg-yellow-500 rounded-full mt-2 mr-3 flex-shrink-0"
                    ></span>
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="trends mt-6 pt-6 border-t">
              <h4
                class="text-md font-semibold text-blue-600 mb-3 flex items-center"
              >
                <el-icon class="mr-2"><TrendCharts /></el-icon>
                学习趋势
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div
                  v-for="trend in personalInsights.trends"
                  :key="trend"
                  class="trend-item p-3 bg-blue-50 rounded-lg"
                >
                  <p class="text-sm text-gray-700">{{ trend }}</p>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="insights-placeholder text-center py-8">
            <el-icon :size="48" class="text-gray-400 mb-2">
              <DataAnalysis />
            </el-icon>
            <p class="text-gray-500">正在分析您的学习数据...</p>
            <el-button
              type="primary"
              size="small"
              @click="generateInsights"
              class="mt-2"
            >
              生成洞察报告
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useAnalyticsStore } from "../stores/analytics";
import LearningStatsChart from "../components/LearningStatsChart.vue";
import KnowledgeRadarChart from "../components/KnowledgeRadarChart.vue";
import LearningRecommendations from "../components/LearningRecommendations.vue";
import {
  Refresh,
  Download,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Calendar,
  Trophy,
  Lock,
  Check,
  Warning,
  TrendCharts,
  DataAnalysis,
  Clock,
  Document,
  Flag,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import dayjs from "dayjs";

const analyticsStore = useAnalyticsStore();

// 响应式数据
const selectedTimeRange = ref("30d");
const currentMonth = ref(dayjs());
const calendarContainer = ref<HTMLDivElement>();

// 计算属性
const loading = computed(() => analyticsStore.loading);
const error = computed(() => analyticsStore.error);
const hasData = computed(() => analyticsStore.learningStats !== null);
const weakKnowledgePoints = computed(() => analyticsStore.weakKnowledgePoints);
const personalInsights = computed(() => analyticsStore.personalInsights);

// 概览统计数据
const overviewStats = computed(() => [
  {
    key: "studyTime",
    label: "总学习时长",
    value: analyticsStore.getFormattedStats.studyTime,
    icon: Clock,
    colorClass: "text-blue-500 bg-blue-50",
    trend: 12,
    trendIcon: TrendCharts,
    trendClass: "text-green-600",
  },
  {
    key: "homework",
    label: "完成作业",
    value: `${analyticsStore.learningStats?.completedHomework || 0}份`,
    icon: Document,
    colorClass: "text-green-500 bg-green-50",
    trend: 8,
    trendIcon: TrendCharts,
    trendClass: "text-green-600",
  },
  {
    key: "score",
    label: "平均成绩",
    value: analyticsStore.getFormattedStats.averageScore,
    icon: TrendCharts,
    colorClass: "text-yellow-500 bg-yellow-50",
    trend: 5,
    trendIcon: TrendCharts,
    trendClass: "text-green-600",
  },
  {
    key: "streak",
    label: "连续学习",
    value: analyticsStore.getFormattedStats.streak,
    icon: Flag,
    colorClass: "text-purple-500 bg-purple-50",
    trend: 0,
    trendIcon: TrendCharts,
    trendClass: "text-gray-500",
  },
]);

// 知识掌握度总结
const knowledgeSummary = computed(() => {
  const points = analyticsStore.knowledgePoints;
  const total = points.length;

  if (total === 0) return [];

  const excellent = points.filter((p) => p.masteryLevel >= 80).length;
  const good = points.filter(
    (p) => p.masteryLevel >= 60 && p.masteryLevel < 80,
  ).length;
  const weak = points.filter((p) => p.masteryLevel < 60).length;

  return [
    {
      level: "excellent",
      label: "优秀掌握",
      count: excellent,
      percentage: Math.round((excellent / total) * 100),
      color: "#10b981",
      textClass: "text-green-600",
    },
    {
      level: "good",
      label: "良好掌握",
      count: good,
      percentage: Math.round((good / total) * 100),
      color: "#f59e0b",
      textClass: "text-yellow-600",
    },
    {
      level: "weak",
      label: "需要提升",
      count: weak,
      percentage: Math.round((weak / total) * 100),
      color: "#ef4444",
      textClass: "text-red-600",
    },
  ];
});

// 最近成就
const recentAchievements = computed(() => {
  return analyticsStore.achievements.slice(0, 6);
});

const unlockedCount = computed(() => {
  return analyticsStore.unlockedAchievements.length;
});

const totalAchievements = computed(() => {
  return analyticsStore.achievements.length;
});

// 方法
const handleTimeRangeChange = () => {
  analyticsStore.setTimeRange(selectedTimeRange.value);
  refreshAllData();
};

const refreshAllData = async () => {
  try {
    await analyticsStore.initializeDashboard(selectedTimeRange.value);
    ElMessage.success("数据刷新成功");
  } catch (error) {
    ElMessage.error("数据刷新失败");
  }
};

const clearError = () => {
  analyticsStore.clearError();
};

const handleExport = (command: string) => {
  ElMessage.info(`正在导出${command.toUpperCase()}格式报告...`);
  // 这里调用导出API
};

const previousMonth = () => {
  currentMonth.value = currentMonth.value.subtract(1, "month");
  fetchCalendarData();
};

const nextMonth = () => {
  currentMonth.value = currentMonth.value.add(1, "month");
  fetchCalendarData();
};

const fetchCalendarData = () => {
  analyticsStore.fetchStudyCalendar(
    currentMonth.value.year(),
    currentMonth.value.month() + 1,
  );
};

const showAllAchievements = () => {
  ElMessage.info("查看全部成就功能开发中");
};

const generateInsights = async () => {
  try {
    await analyticsStore.fetchPersonalInsights();
    ElMessage.success("洞察报告生成成功");
  } catch (error) {
    ElMessage.error("生成失败，请稍后重试");
  }
};

// 监听路由和数据变化
watch(
  () => selectedTimeRange.value,
  () => {
    analyticsStore.setTimeRange(selectedTimeRange.value);
  },
);

onMounted(async () => {
  // 初始化数据
  await analyticsStore.initializeDashboard(selectedTimeRange.value);

  // 获取个人洞察
  if (!personalInsights.value) {
    analyticsStore.fetchPersonalInsights();
  }

  // 获取成就数据
  if (analyticsStore.achievements.length === 0) {
    analyticsStore.fetchAchievements();
  }

  // 获取日历数据
  fetchCalendarData();
});
</script>

<style scoped>
.analytics-page {
  @apply max-w-7xl mx-auto px-4 py-6;
}

.section-title {
  @apply text-xl font-semibold text-gray-900 mb-4 flex items-center;
}

.section-title::before {
  content: "";
  @apply w-1 h-6 bg-blue-500 rounded-full mr-3;
}

.stat-card {
  transition: all 0.2s ease-in-out;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  @apply w-12 h-12 rounded-lg flex items-center justify-center;
}

.trend-indicator {
  @apply flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.knowledge-summary .summary-item {
  @apply p-3 rounded-lg bg-gray-50;
}

.weak-point-item {
  transition: all 0.2s ease-in-out;
}

.weak-point-item:hover {
  @apply bg-red-100 border-red-200;
}

.calendar-placeholder,
.insights-placeholder {
  @apply border-2 border-dashed border-gray-200 rounded-lg;
}

.achievements-grid .achievement-item {
  @apply p-3 rounded-lg text-center transition-all duration-200;
}

.achievements-grid .achievement-item.unlocked {
  @apply bg-green-50 border border-green-200;
}

.achievements-grid .achievement-item.locked {
  @apply bg-gray-50 border border-gray-200 opacity-60;
}

.achievements-grid .achievement-item:hover {
  transform: translateY(-1px);
  @apply shadow-sm;
}

.achievement-icon {
  @apply flex items-center justify-center;
}

.insights-content .trend-item {
  transition: all 0.2s ease-in-out;
}

.insights-content .trend-item:hover {
  @apply bg-blue-100;
}

.loading-container {
  @apply bg-white rounded-lg p-6 shadow-sm border;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .analytics-page {
    @apply px-2 py-4;
  }

  .section-title {
    @apply text-lg;
  }

  .stat-card {
    @apply p-4;
  }

  .stat-value {
    @apply text-xl;
  }
}

/* 深色主题支持 */
@media (prefers-color-scheme: dark) {
  .analytics-page {
    @apply bg-gray-900 text-white;
  }

  .stat-card,
  .bg-white {
    @apply bg-gray-800 border-gray-700;
  }

  .text-gray-900 {
    @apply text-white;
  }

  .text-gray-600 {
    @apply text-gray-300;
  }

  .text-gray-500 {
    @apply text-gray-400;
  }
}

/* 动画效果 */
.analytics-content > div {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.analytics-content > div:nth-child(1) {
  animation-delay: 0.1s;
}
.analytics-content > div:nth-child(2) {
  animation-delay: 0.2s;
}
.analytics-content > div:nth-child(3) {
  animation-delay: 0.3s;
}
.analytics-content > div:nth-child(4) {
  animation-delay: 0.4s;
}
.analytics-content > div:nth-child(5) {
  animation-delay: 0.5s;
}
.analytics-content > div:nth-child(6) {
  animation-delay: 0.6s;
}
</style>
