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
          <el-select v-model="selectedTimeRange" size="small" @change="handleTimeRangeChange">
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
        <h2 class="section-title">学习统计图表</h2>
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div>
            <LearningTrendChart :auto-refresh="true" :default-time-range="selectedTimeRange" />
          </div>
          <div>
            <LearningProgressChart :default-metric="selectedTimeRange" />
          </div>
        </div>
      </div>

      <!-- 知识点掌握雷达图 -->
      <div class="knowledge-section mb-8">
        <h2 class="section-title">知识掌握雷达分析</h2>
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div class="xl:col-span-2">
            <KnowledgeRadarChart :show-comparison="true" />
          </div>
          <div class="knowledge-summary bg-white rounded-lg p-6 shadow-sm border">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">掌握度总结</h3>
            <div class="space-y-4">
              <div v-for="category in knowledgeSummary" :key="category.level" class="summary-item">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium" :class="category.textClass">
                    {{ category.label }}
                  </span>
                  <span class="text-sm text-gray-600"> {{ category.count }}个知识点 </span>
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
              <h4 class="text-md font-medium text-gray-900 mb-3">需要重点关注</h4>
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
        <h2 class="section-title">智能学习建议</h2>
        <LearningRecommendations />
      </div>

      <!-- 学习日历和成就系统 -->
      <div class="calendar-achievements-section mb-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 学习日历 -->
          <LearningCalendar :auto-refresh="true" />

          <!-- 成就系统 -->
          <div class="achievements-section">
            <AchievementDisplay :max-display="6" :show-categories="false" :auto-refresh="true" />
          </div>
        </div>
      </div>

      <!-- 智能学习洞察 -->
      <div class="insights-section mt-8">
        <h2 class="section-title">智能学习洞察</h2>
        <LearningInsights />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAnalyticsStore } from '../stores/analytics'
import LearningTrendChart from '../components/LearningTrendChart.vue'
import KnowledgeRadarChart from '../components/KnowledgeRadarChart.vue'
import LearningRecommendations from '../components/LearningRecommendations.vue'
import AchievementDisplay from '../components/AchievementDisplay.vue'
import LearningProgressChart from '../components/LearningProgressChart.vue'
import LearningInsights from '../components/LearningInsights.vue'
import LearningCalendar from '../components/LearningCalendar.vue'
import {
  Refresh,
  Download,
  ArrowDown,
  Clock,
  Document,
  Flag,
  TrendCharts,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const analyticsStore = useAnalyticsStore()

// 响应式数据
const selectedTimeRange = ref('30d')

// 计算属性
const loading = computed(() => analyticsStore.loading)
const error = computed(() => analyticsStore.error)
const hasData = computed(() => analyticsStore.learningStats !== null)
const weakKnowledgePoints = computed(() => analyticsStore.weakKnowledgePoints)

// 概览统计数据
const overviewStats = computed(() => [
  {
    key: 'studyTime',
    label: '总学习时长',
    value: analyticsStore.getFormattedStats.studyTime,
    icon: Clock,
    colorClass: 'text-blue-500 bg-blue-50',
    trend: 12,
    trendIcon: TrendCharts,
    trendClass: 'text-green-600',
  },
  {
    key: 'homework',
    label: '完成作业',
    value: `${analyticsStore.learningStats?.completedHomework || 0}份`,
    icon: Document,
    colorClass: 'text-green-500 bg-green-50',
    trend: 8,
    trendIcon: TrendCharts,
    trendClass: 'text-green-600',
  },
  {
    key: 'score',
    label: '平均成绩',
    value: analyticsStore.getFormattedStats.averageScore,
    icon: TrendCharts,
    colorClass: 'text-yellow-500 bg-yellow-50',
    trend: 5,
    trendIcon: TrendCharts,
    trendClass: 'text-green-600',
  },
  {
    key: 'streak',
    label: '连续学习',
    value: analyticsStore.getFormattedStats.streak,
    icon: Flag,
    colorClass: 'text-purple-500 bg-purple-50',
    trend: 0,
    trendIcon: TrendCharts,
    trendClass: 'text-gray-500',
  },
])

// 知识掌握度总结
const knowledgeSummary = computed(() => {
  const points = analyticsStore.knowledgePoints
  const total = points.length

  if (total === 0) return []

  const excellent = points.filter((p) => p.masteryLevel >= 80).length
  const good = points.filter((p) => p.masteryLevel >= 60 && p.masteryLevel < 80).length
  const weak = points.filter((p) => p.masteryLevel < 60).length

  return [
    {
      level: 'excellent',
      label: '优秀掌握',
      count: excellent,
      percentage: Math.round((excellent / total) * 100),
      color: '#10b981',
      textClass: 'text-green-600',
    },
    {
      level: 'good',
      label: '良好掌握',
      count: good,
      percentage: Math.round((good / total) * 100),
      color: '#f59e0b',
      textClass: 'text-yellow-600',
    },
    {
      level: 'weak',
      label: '需要提升',
      count: weak,
      percentage: Math.round((weak / total) * 100),
      color: '#ef4444',
      textClass: 'text-red-600',
    },
  ]
})

// 方法
const handleTimeRangeChange = () => {
  analyticsStore.setTimeRange(selectedTimeRange.value)
  refreshAllData()
}

const refreshAllData = async () => {
  try {
    await analyticsStore.initializeDashboard(selectedTimeRange.value)
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  }
}

const clearError = () => {
  analyticsStore.clearError()
}

const handleExport = (command: string) => {
  ElMessage.info(`正在导出${command.toUpperCase()}格式报告...`)
  // 这里调用导出API
}

onMounted(async () => {
  // 初始化数据
  await analyticsStore.initializeDashboard(selectedTimeRange.value)

  // 获取成就数据
  if (analyticsStore.achievements.length === 0) {
    analyticsStore.fetchAchievements()
  }
})
</script>

<style scoped>
.analytics-page {
  max-width: 80rem;
  margin-left: auto;
  margin-right: auto;
  padding-left: 1rem;
  padding-right: 1rem;
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

.section-title {
  font-size: 1.25rem;
  line-height: 1.75rem;
  font-weight: 600;
  color: rgb(17, 24, 39);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.section-title::before {
  content: '';
  width: 0.25rem;
  height: 1.5rem;
  background-color: rgb(59, 130, 246);
  border-radius: 9999px;
  margin-right: 0.75rem;
}

.stat-card {
  transition: all 0.2s ease-in-out;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trend-indicator {
  display: flex;
  align-items: center;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  line-height: 1rem;
  font-weight: 500;
}

.knowledge-summary .summary-item {
  padding: 0.75rem;
  border-radius: 0.5rem;
  background-color: rgb(249, 250, 251);
}

.weak-point-item {
  transition: all 0.2s ease-in-out;
}

.weak-point-item:hover {
  background-color: rgb(254, 226, 226);
  border-color: rgb(254, 202, 202);
}

.calendar-placeholder,
.insights-placeholder {
  border-width: 2px;
  border-style: dashed;
  border-color: rgb(229, 231, 235);
  border-radius: 0.5rem;
}

.achievements-grid .achievement-item {
  padding: 0.75rem;
  border-radius: 0.5rem;
  text-align: center;
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 200ms;
}

.achievements-grid .achievement-item.unlocked {
  background-color: rgb(240, 253, 244);
  border-width: 1px;
  border-color: rgb(187, 247, 208);
}

.achievements-grid .achievement-item.locked {
  background-color: rgb(249, 250, 251);
  border-width: 1px;
  border-color: rgb(229, 231, 235);
  opacity: 0.6;
}

.achievements-grid .achievement-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.achievement-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.insights-content .trend-item {
  transition: all 0.2s ease-in-out;
}

.insights-content .trend-item:hover {
  background-color: rgb(219, 234, 254);
}

.loading-container {
  background-color: rgb(255, 255, 255);
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  border-width: 1px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .analytics-page {
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    padding-top: 1rem;
    padding-bottom: 1rem;
  }

  .section-title {
    font-size: 1.125rem;
    line-height: 1.75rem;
  }

  .stat-card {
    padding: 1rem;
  }

  .stat-value {
    font-size: 1.25rem;
    line-height: 1.75rem;
  }
}

/* 深色主题支持 */
@media (prefers-color-scheme: dark) {
  .analytics-page {
    background-color: rgb(17, 24, 39);
    color: rgb(255, 255, 255);
  }

  .stat-card,
  .bg-white {
    background-color: rgb(31, 41, 55);
    border-color: rgb(55, 65, 81);
  }

  .text-gray-900 {
    color: rgb(255, 255, 255);
  }

  .text-gray-600 {
    color: rgb(209, 213, 219);
  }

  .text-gray-500 {
    color: rgb(156, 163, 175);
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
  animation-delay: 1s;
}

/* 日历样式优化 */
.calendar-heatmap {
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.calendar-heatmap .grid {
  max-width: 280px;
  margin: 0 auto;
}

/* 成就展示区域样式 */
.achievements-card {
  background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 10%, #f59e0b 100%);
  color: #78350f;
}

.achievements-card .achievement-item.unlocked {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #fbbf24;
  transform: scale(1.02);
}

.achievements-card .achievement-item.locked {
  background: rgba(255, 255, 255, 0.5);
  border: 2px solid #d1d5db;
  opacity: 0.7;
}
</style>
