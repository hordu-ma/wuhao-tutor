<template>
  <div class="analytics-page">
    <!-- 动态背景 -->
    <div class="analytics-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="page-title">
            <span class="title-icon">📊</span>
            智能学习进度
          </h1>
          <p class="page-subtitle">基于AI驱动的个性化学习数据洞察，让每一步学习都更精准</p>
        </div>
        <div class="header-controls">
          <div class="control-group">
            <el-select
              v-model="selectedTimeRange"
              size="large"
              @change="handleTimeRangeChange"
              class="time-selector"
            >
              <el-option label="最近7天" value="7d">
                <span class="option-content">
                  <i class="option-icon">📅</i>
                  最近7天
                </span>
              </el-option>
              <el-option label="最近30天" value="30d">
                <span class="option-content">
                  <i class="option-icon">📈</i>
                  最近30天
                </span>
              </el-option>
              <el-option label="最近90天" value="90d">
                <span class="option-content">
                  <i class="option-icon">📊</i>
                  最近90天
                </span>
              </el-option>
            </el-select>
          </div>

          <el-button
            type="primary"
            :icon="Refresh"
            @click="refreshAllData"
            :loading="loading"
            size="large"
            class="refresh-btn"
          >
            <span v-if="!loading">刷新数据</span>
            <span v-else>加载中...</span>
          </el-button>

          <el-dropdown @command="handleExport" class="export-dropdown">
            <el-button size="large" class="export-btn">
              <el-icon><Download /></el-icon>
              导出报告
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu class="export-menu">
                <el-dropdown-item command="pdf">
                  <i class="menu-icon">📄</i>
                  PDF完整报告
                </el-dropdown-item>
                <el-dropdown-item command="csv">
                  <i class="menu-icon">📊</i>
                  CSV数据表格
                </el-dropdown-item>
                <el-dropdown-item command="json">
                  <i class="menu-icon">💾</i>
                  JSON原始数据
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-container">
      <el-alert
        :title="error"
        type="error"
        effect="dark"
        show-icon
        closable
        @close="clearError"
        class="error-alert"
      >
        <template #title>
          <span class="error-title">
            <i class="error-icon">⚠️</i>
            数据加载失败
          </span>
        </template>
      </el-alert>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && !hasData" class="loading-container">
      <div class="loading-content">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <p class="loading-text">正在分析您的学习数据...</p>
      </div>
    </div>

    <!-- 主要内容 -->
    <div v-else class="analytics-content">
      <!-- 核心指标仪表盘 -->
      <div class="metrics-dashboard">
        <h2 class="section-title">
          <span class="title-decorator"></span>
          学习概览仪表盘
          <span class="title-badge">实时更新</span>
        </h2>

        <div class="metrics-grid">
          <div
            v-for="(stat, index) in overviewStats"
            :key="stat.key"
            class="metric-card"
            :style="{ '--delay': index * 0.1 + 's' }"
          >
            <div class="metric-header">
              <div class="metric-icon" :class="stat.colorClass">
                <el-icon :size="32">
                  <component :is="stat.icon" />
                </el-icon>
              </div>
              <div class="metric-trend" :class="stat.trendClass">
                <el-icon :size="16">
                  <component :is="stat.trendIcon" />
                </el-icon>
                <span class="trend-value">{{ Math.abs(stat.trend) }}%</span>
              </div>
            </div>

            <div class="metric-body">
              <div class="metric-value">{{ stat.value }}</div>
              <div class="metric-label">{{ stat.label }}</div>
            </div>

            <div class="metric-footer">
              <div class="progress-ring">
                <svg class="ring-svg" width="60" height="60">
                  <circle class="ring-bg" cx="30" cy="30" r="26" fill="none" stroke-width="4" />
                  <circle
                    class="ring-progress"
                    cx="30"
                    cy="30"
                    r="26"
                    fill="none"
                    stroke-width="4"
                    :stroke-dasharray="163.36"
                    :stroke-dashoffset="163.36 * (1 - (stat.progress || 0.75))"
                  />
                </svg>
                <div class="ring-text">{{ Math.round((stat.progress || 0.75) * 100) }}%</div>
              </div>
            </div>

            <div class="metric-glow"></div>
          </div>
        </div>
      </div>

      <!-- 智能图表分析区域 -->
      <div class="charts-analytics">
        <h2 class="section-title">
          <span class="title-decorator"></span>
          学习趋势分析
          <span class="title-badge">AI 驱动</span>
        </h2>

        <div class="charts-grid">
          <div class="chart-container main-chart">
            <div class="chart-header">
              <div class="chart-title">
                <span class="chart-icon">📈</span>
                学习进度趋势
              </div>
              <div class="chart-controls">
                <div class="chart-filters">
                  <button class="filter-btn active">学习时长</button>
                  <button class="filter-btn">正确率</button>
                  <button class="filter-btn">完成率</button>
                </div>
              </div>
            </div>
            <div class="chart-content">
              <LearningTrendChart :auto-refresh="true" :default-time-range="selectedTimeRange" />
            </div>
          </div>
        </div>
      </div>

      <!-- 知识雷达分析 -->
      <div class="knowledge-radar-section">
        <h2 class="section-title">
          <span class="title-decorator"></span>
          知识掌握雷达分析
          <span class="title-badge">360° 全景</span>
        </h2>

        <div class="radar-container">
          <div class="radar-chart">
            <div class="radar-header">
              <div class="radar-title">
                <span class="radar-icon">🎯</span>
                知识点掌握度分布
              </div>
              <div class="radar-legend">
                <div class="legend-item excellent">
                  <span class="legend-dot"></span>
                  优秀掌握 (≥80%)
                </div>
                <div class="legend-item good">
                  <span class="legend-dot"></span>
                  良好掌握 (60-79%)
                </div>
                <div class="legend-item weak">
                  <span class="legend-dot"></span>
                  需要提升 (<60%)
                </div>
              </div>
            </div>
            <div class="radar-content">
              <KnowledgeRadarChart :show-comparison="true" />
            </div>
          </div>

          <div class="knowledge-insights">
            <div class="insights-card mastery-summary">
              <div class="card-header">
                <h3 class="card-title">
                  <span class="card-icon">🏆</span>
                  掌握度总览
                </h3>
              </div>
              <div class="card-content">
                <div class="mastery-stats">
                  <div
                    v-for="category in knowledgeSummary"
                    :key="category.level"
                    class="mastery-item"
                    :class="category.level"
                  >
                    <div class="mastery-info">
                      <div class="mastery-label" :class="category.textClass">
                        {{ category.label }}
                      </div>
                      <div class="mastery-count">{{ category.count }}个知识点</div>
                    </div>
                    <div class="mastery-progress">
                      <div class="progress-circle">
                        <svg class="circle-svg" width="60" height="60">
                          <circle
                            class="circle-bg"
                            cx="30"
                            cy="30"
                            r="25"
                            fill="none"
                            stroke-width="5"
                          />
                          <circle
                            class="circle-progress"
                            :class="category.level"
                            cx="30"
                            cy="30"
                            r="25"
                            fill="none"
                            stroke-width="5"
                            :stroke-dasharray="157"
                            :stroke-dashoffset="157 * (1 - category.percentage / 100)"
                          />
                        </svg>
                        <div class="circle-text">{{ category.percentage }}%</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="insights-card weak-points">
              <div class="card-header">
                <h3 class="card-title">
                  <span class="card-icon">⚠️</span>
                  重点关注
                </h3>
                <div class="card-action">
                  <button class="action-btn">查看全部</button>
                </div>
              </div>
              <div class="card-content">
                <div class="weak-points-list">
                  <div
                    v-for="point in weakKnowledgePoints.slice(0, 6)"
                    :key="point.id"
                    class="weak-point"
                  >
                    <div class="point-info">
                      <div class="point-name">{{ point.name }}</div>
                      <div class="point-subject">{{ point.subject }}</div>
                    </div>
                    <div class="point-score">
                      <div class="score-value" :class="getScoreClass(point.masteryLevel)">
                        {{ point.masteryLevel }}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 学习建议和目标管理 -->
      <!-- TODO: 待后端实现推荐 API 后启用 -->
      <!-- <div class="recommendations-section mb-8">
        <h2 class="section-title">智能学习建议</h2>
        <LearningRecommendations />
      </div> -->

      <!-- 学习日历和成就系统 -->
      <!-- TODO: 待后端实现日历和成就 API 后启用 -->
      <!-- <div class="calendar-achievements-section mb-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LearningCalendar :auto-refresh="true" />
          <div class="achievements-section">
            <AchievementDisplay :max-display="6" :show-categories="false" :auto-refresh="true" />
          </div>
        </div>
      </div> -->

      <!-- AI 学习洞察 -->
      <div class="insights-section">
        <h2 class="section-title">
          <span class="title-decorator"></span>
          AI 智能学习洞察
          <span class="title-badge">个性化推荐</span>
        </h2>

        <div class="insights-container">
          <LearningInsights />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAnalyticsStore } from '../stores/analytics'
import LearningTrendChart from '../components/LearningTrendChart.vue'
import KnowledgeRadarChart from '../components/KnowledgeRadarChart.vue'
// TODO: 待后端 API 实现后启用这些组件
// import LearningRecommendations from '../components/LearningRecommendations.vue'
// import AchievementDisplay from '../components/AchievementDisplay.vue'
// import LearningProgressChart from '../components/LearningProgressChart.vue'
import LearningInsights from '../components/LearningInsights.vue'
// import LearningCalendar from '../components/LearningCalendar.vue'
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
    progress: 0.75,
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
    progress: 0.65,
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
    progress: 0.8,
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
    progress: 0.45,
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
const getScoreClass = (score: number) => {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  return 'weak'
}

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

  // TODO: 待后端实现成就 API 后启用
  // // 获取成就数据
  // if (analyticsStore.achievements.length === 0) {
  //   analyticsStore.fetchAchievements()
  // }
})
</script>

<style scoped>
/* ===== 全局样式重置和基础配置 ===== */
.analytics-page {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
  padding: 2rem;
  font-family:
    'Inter',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    sans-serif;
}

/* ===== 动态背景装饰 ===== */
.analytics-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.3;
  animation: float 6s ease-in-out infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #ff6b6b, #ee5a6f);
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.orb-2 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, #4ecdc4, #44a08d);
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, #feca57, #ff9ff3);
  bottom: 20%;
  left: 50%;
  animation-delay: 4s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.1);
  }
}

/* ===== 页面头部样式 ===== */
.page-header {
  position: relative;
  z-index: 10;
  margin-bottom: 3rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-text {
  flex: 1;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #2d3748;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.title-icon {
  font-size: 2.5rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.page-subtitle {
  font-size: 1.125rem;
  color: #718096;
  margin: 0;
  line-height: 1.6;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.time-selector {
  min-width: 140px;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.option-icon {
  font-size: 1rem;
}

.refresh-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(102, 126, 234, 0.6);
}

.export-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 12px 20px;
  color: #4a5568;
  font-weight: 500;
  transition: all 0.3s ease;
}

.export-btn:hover {
  background: white;
  transform: translateY(-1px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.export-menu {
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.menu-icon {
  margin-right: 8px;
  font-size: 1rem;
}

/* ===== 错误和加载状态 ===== */
.error-container {
  position: relative;
  z-index: 10;
  margin-bottom: 2rem;
}

.error-alert {
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.error-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.error-icon {
  font-size: 1.25rem;
}

.loading-container {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  margin-bottom: 2rem;
}

.loading-content {
  text-align: center;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0 auto 1rem auto;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring:nth-child(1) {
  animation-delay: 0s;
}
.spinner-ring:nth-child(2) {
  animation-delay: 0.1s;
  opacity: 0.8;
}
.spinner-ring:nth-child(3) {
  animation-delay: 0.2s;
  opacity: 0.6;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #718096;
  font-weight: 500;
  font-size: 1.125rem;
}

/* ===== 主要内容区域 ===== */
.analytics-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

/* ===== 通用标题样式 ===== */
.section-title {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  margin-bottom: 1.5rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title-decorator {
  width: 4px;
  height: 2rem;
  background: linear-gradient(45deg, #ff6b6b, #feca57);
  border-radius: 2px;
  box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
}

.title-badge {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* ===== 指标仪表盘 ===== */
.metrics-dashboard {
  position: relative;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.metric-card {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  animation: slideInUp 0.6s ease-out var(--delay);
  overflow: hidden;
}

.metric-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.2);
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.metric-icon.text-blue-500 {
  background: linear-gradient(135deg, #3b82f6, #1e40af);
  color: white;
}

.metric-icon.text-green-500 {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.metric-icon.text-yellow-500 {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.metric-icon.text-purple-500 {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.metric-body {
  margin-bottom: 1.5rem;
}

.metric-value {
  font-size: 2.25rem;
  font-weight: 800;
  color: #1a202c;
  line-height: 1.2;
  margin-bottom: 0.5rem;
}

.metric-label {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

.metric-footer {
  display: flex;
  justify-content: center;
}

.progress-ring {
  position: relative;
  width: 60px;
  height: 60px;
}

.ring-svg {
  transform: rotate(-90deg);
}

.ring-bg {
  stroke: #e2e8f0;
}

.ring-progress {
  stroke: #667eea;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.8s ease-in-out;
}

.ring-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.75rem;
  font-weight: 600;
  color: #4a5568;
}

.metric-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.metric-card:hover .metric-glow {
  opacity: 1;
}

/* ===== 图表分析区域 ===== */
.charts-analytics {
  position: relative;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

.chart-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.chart-container:hover {
  transform: translateY(-4px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
}

.chart-icon {
  font-size: 1.5rem;
}

.chart-filters {
  display: flex;
  gap: 0.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  background: white;
  color: #718096;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.filter-btn.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: #667eea;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.chart-content {
  min-height: 300px;
}

/* ===== 知识雷达分析 ===== */
.knowledge-radar-section {
  position: relative;
}

.radar-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

.radar-chart {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.radar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.radar-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
}

.radar-icon {
  font-size: 1.5rem;
}

.radar-legend {
  display: flex;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item.excellent .legend-dot {
  background: #10b981;
}
.legend-item.good .legend-dot {
  background: #f59e0b;
}
.legend-item.weak .legend-dot {
  background: #ef4444;
}

.radar-content {
  min-height: 400px;
}

.knowledge-insights {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.insights-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.insights-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #2d3748;
}

.card-icon {
  font-size: 1.25rem;
}

.action-btn {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: white;
  color: #667eea;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: #667eea;
  color: white;
}

.mastery-stats {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.mastery-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 12px;
  background: #f8fafc;
  transition: all 0.3s ease;
}

.mastery-item:hover {
  background: #f1f5f9;
  transform: scale(1.02);
}

.mastery-info {
  flex: 1;
}

.mastery-label {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.mastery-count {
  font-size: 0.75rem;
  color: #718096;
}

.progress-circle {
  position: relative;
  width: 60px;
  height: 60px;
}

.circle-svg {
  transform: rotate(-90deg);
}

.circle-bg {
  stroke: #e2e8f0;
}

.circle-progress {
  stroke-linecap: round;
  transition: stroke-dashoffset 0.8s ease-in-out;
}

.circle-progress.excellent {
  stroke: #10b981;
}
.circle-progress.good {
  stroke: #f59e0b;
}
.circle-progress.weak {
  stroke: #ef4444;
}

.circle-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.75rem;
  font-weight: 600;
  color: #4a5568;
}

.weak-points-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.weak-point {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #fef3f2 0%, #fdf2f8 100%);
  border: 1px solid rgba(239, 68, 68, 0.1);
  transition: all 0.3s ease;
}

.weak-point:hover {
  background: linear-gradient(135deg, #fee2e2 0%, #fce7f3 100%);
  border-color: rgba(239, 68, 68, 0.2);
  transform: translateX(4px);
}

.point-info {
  flex: 1;
}

.point-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 0.25rem;
}

.point-subject {
  font-size: 0.75rem;
  color: #718096;
}

.point-score {
  display: flex;
  align-items: center;
}

.score-value {
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.score-value.excellent {
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
}

.score-value.good {
  background: rgba(245, 158, 11, 0.1);
  color: #92400e;
}

.score-value.weak {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

/* ===== AI 学习洞察 ===== */
.insights-section {
  position: relative;
}

.insights-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.insights-container:hover {
  transform: translateY(-4px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}

/* ===== 响应式设计 ===== */
@media (max-width: 1024px) {
  .radar-container {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    gap: 1.5rem;
    align-items: flex-start;
  }

  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 768px) {
  .analytics-page {
    padding: 1rem;
  }

  .page-title {
    font-size: 2rem;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .header-controls {
    flex-direction: column;
    gap: 1rem;
  }

  .chart-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .radar-legend {
    flex-direction: column;
    gap: 0.5rem;
  }
}

@media (max-width: 480px) {
  .analytics-page {
    padding: 0.5rem;
  }

  .header-content {
    padding: 1.5rem;
  }

  .page-title {
    font-size: 1.75rem;
  }

  .page-subtitle {
    font-size: 1rem;
  }

  .metric-card,
  .chart-container,
  .insights-card {
    padding: 1.5rem;
  }
}

/* ===== 深色模式支持 ===== */
@media (prefers-color-scheme: dark) {
  .analytics-page {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  }

  .header-content,
  .metric-card,
  .chart-container,
  .insights-card {
    background: rgba(30, 30, 46, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .page-title,
  .chart-title,
  .card-title,
  .metric-value {
    color: #f7fafc;
  }

  .page-subtitle,
  .metric-label {
    color: #a0aec0;
  }

  .filter-btn {
    background: rgba(45, 55, 72, 0.8);
    border-color: rgba(255, 255, 255, 0.1);
    color: #a0aec0;
  }
}

/* ===== 访问性增强 ===== */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  .gradient-orb {
    animation: none;
  }
}

/* ===== 打印样式 ===== */
@media print {
  .analytics-page {
    background: white;
    color: black;
  }

  .analytics-background,
  .header-controls,
  .chart-controls,
  .action-btn {
    display: none;
  }

  .metric-card,
  .chart-container,
  .insights-card {
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: none;
  }
}
</style>
