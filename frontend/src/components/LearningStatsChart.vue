<template>
  <div class="learning-stats-chart">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div
        v-for="stat in statsCards"
        :key="stat.key"
        class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="text-sm text-gray-600">{{ stat.label }}</div>
          <el-icon class="text-lg" :class="stat.color">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="text-2xl font-bold text-gray-900 mb-1">
          {{ stat.value }}
        </div>
        <div class="flex items-center text-xs">
          <span
            :class="
              stat.trend > 0 ? 'text-green-600' : stat.trend < 0 ? 'text-red-600' : 'text-gray-500'
            "
          >
            {{ stat.trend > 0 ? '↗' : stat.trend < 0 ? '↘' : '→' }}
            {{ Math.abs(stat.trend) }}%
          </span>
          <span class="text-gray-500 ml-1">vs 上周</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 学习时长趋势 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">学习时长趋势</h3>
          <el-select v-model="timeRange" size="small" @change="handleTimeRangeChange">
            <el-option label="最近7天" value="7d" />
            <el-option label="最近30天" value="30d" />
            <el-option label="最近90天" value="90d" />
          </el-select>
        </div>
        <div ref="studyTimeChart" class="w-full h-64"></div>
      </div>

      <!-- 学科分布 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">学科学习分布</h3>
        <div ref="subjectChart" class="w-full h-64"></div>
      </div>

      <!-- 学习效率分析 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">学习效率分析</h3>
        <div ref="efficiencyChart" class="w-full h-64"></div>
      </div>

      <!-- 知识点掌握度 -->
      <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">知识点掌握度</h3>
          <el-select v-model="selectedSubject" size="small" @change="handleSubjectChange">
            <el-option label="全部学科" value="" />
            <el-option
              v-for="subject in subjects"
              :key="subject"
              :label="subject"
              :value="subject"
            />
          </el-select>
        </div>
        <div ref="knowledgeChart" class="w-full h-64"></div>
      </div>
    </div>

    <!-- 学习热力图 -->
    <div class="mt-6 bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">学习活跃度热力图</h3>
        <el-select v-model="selectedYear" size="small" @change="handleYearChange">
          <el-option v-for="year in years" :key="year" :label="year" :value="year" />
        </el-select>
      </div>
      <div ref="heatmapChart" class="w-full h-40"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { useAnalyticsStore } from '../stores/analytics'
import { useAuthStore } from '../stores/auth'
import { Clock, Document, TrendCharts, Flag } from '@element-plus/icons-vue'
import type { ECharts } from 'echarts'
import dayjs from 'dayjs'

interface Props {
  height?: string
  autoRefresh?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  autoRefresh: false,
})

const analyticsStore = useAnalyticsStore()
const authStore = useAuthStore()

// 图表实例引用
const studyTimeChart = ref<HTMLDivElement>()
const subjectChart = ref<HTMLDivElement>()
const efficiencyChart = ref<HTMLDivElement>()
const knowledgeChart = ref<HTMLDivElement>()
const heatmapChart = ref<HTMLDivElement>()

// 图表实例
let studyTimeChartInstance: ECharts | null = null
let subjectChartInstance: ECharts | null = null
let efficiencyChartInstance: ECharts | null = null
let knowledgeChartInstance: ECharts | null = null
let heatmapChartInstance: ECharts | null = null

// 控制状态
const timeRange = ref('30d')
const selectedSubject = ref('')
const selectedYear = ref(new Date().getFullYear())

// 数据
const subjects = computed(() => {
  if (!analyticsStore.subjectStats || !Array.isArray(analyticsStore.subjectStats)) {
    return []
  }
  return Array.from(new Set(analyticsStore.subjectStats.map((s) => s.subject)))
})

const years = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 3 }, (_, i) => currentYear - i)
})

// 统计卡片数据
const statsCards = computed(() => [
  {
    key: 'studyTime',
    label: '总学习时长',
    value: analyticsStore.getFormattedStats.studyTime,
    icon: Clock,
    color: 'text-blue-500',
    trend: 12, // 模拟趋势数据
  },
  {
    key: 'homework',
    label: '完成作业',
    value: `${analyticsStore.learningStats?.completedHomework || 0}份`,
    icon: Document,
    color: 'text-green-500',
    trend: 8,
  },
  {
    key: 'score',
    label: '平均成绩',
    value: analyticsStore.getFormattedStats.averageScore,
    icon: TrendCharts,
    color: 'text-yellow-500',
    trend: 5,
  },
  {
    key: 'streak',
    label: '连续学习',
    value: analyticsStore.getFormattedStats.streak,
    icon: Flag,
    color: 'text-purple-500',
    trend: 0,
  },
])

// 初始化学习时长趋势图
const initStudyTimeChart = () => {
  if (!studyTimeChart.value) return

  studyTimeChartInstance = echarts.init(studyTimeChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151',
        fontSize: 12,
      },
      formatter: (params: any) => {
        const data = params[0]
        const progressData = analyticsStore.learningProgress.find(
          (p) => dayjs(p.date).format('MM-DD') === data.axisValue
        )
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${data.axisValue}</div>
            <div style="color: #3b82f6; margin-bottom: 2px;">学习时长: ${data.value}分钟</div>
            ${
              progressData
                ? `
            <div style="color: #10b981; margin-bottom: 2px;">完成作业: ${progressData.homeworkCount}份</div>
            <div style="color: #f59e0b; margin-bottom: 2px;">提问次数: ${progressData.questionCount}次</div>
            <div style="color: #8b5cf6;">平均分: ${progressData.averageScore}分</div>
            `
                : ''
            }
          </div>
        `
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '8%',
      top: '5%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: (analyticsStore.learningProgress || []).map((p) => dayjs(p.date).format('MM-DD')),
      axisLabel: {
        fontSize: 11,
        color: '#6b7280',
        rotate: 45,
      },
      axisLine: {
        lineStyle: {
          color: '#e5e7eb',
        },
      },
      splitLine: {
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}min',
        fontSize: 11,
        color: '#6b7280',
      },
      axisLine: {
        show: false,
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed',
        },
      },
    },
    series: [
      {
        name: '学习时长',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: (analyticsStore.learningProgress || []).map((p) => p.studyTime),
        itemStyle: {
          color: '#3b82f6',
          borderWidth: 2,
          borderColor: '#ffffff',
        },
        lineStyle: {
          width: 3,
          color: '#3b82f6',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.25)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
            ],
          },
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(59, 130, 246, 0.3)',
          },
        },
      },
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
  }

  studyTimeChartInstance.setOption(option as any)
}

// 初始化学科分布图
const initSubjectChart = () => {
  if (!subjectChart.value) return

  subjectChartInstance = echarts.init(subjectChart.value)

  const data = (analyticsStore.subjectStats || []).map((s) => ({
    name: s.subject,
    value: s.studyTime,
  }))

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16']

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151',
        fontSize: 12,
      },
      formatter: (params: any) => {
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${params.name}</div>
            <div style="color: ${params.color}; margin-bottom: 2px;">学习时长: ${params.value}分钟</div>
            <div style="color: #6b7280;">占比: ${params.percent}%</div>
          </div>
        `
      },
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: {
        fontSize: 11,
        color: '#374151',
      },
    },
    series: [
      {
        name: '学习时长',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['65%', '50%'],
        data: data.map((item, index) => ({
          ...item,
          itemStyle: {
            color: colors[index % colors.length],
            borderRadius: 4,
            borderColor: '#ffffff',
            borderWidth: 2,
          },
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 15,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.15)',
            borderWidth: 3,
          },
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}: {d}%',
          fontSize: 11,
          color: '#374151',
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 10,
          smooth: true,
        },
      },
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
  }

  subjectChartInstance.setOption(option as any)
}

// 初始化效率分析图
const initEfficiencyChart = () => {
  if (!efficiencyChart.value) return

  efficiencyChartInstance = echarts.init(efficiencyChart.value)

  // 计算一周效率数据
  const weekData = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const totalTimeData = [120, 90, 150, 80, 130, 110, 95]
  const effectiveTimeData = [100, 75, 120, 65, 110, 90, 80]

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151',
        fontSize: 12,
      },
      formatter: (params: any) => {
        const day = params[0].axisValue
        const total = params[0].value
        const effective = params[1].value
        const efficiency = Math.round((effective / total) * 100)
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${day}</div>
            <div style="color: #e5e7eb; margin-bottom: 2px;">总时长: ${total}分钟</div>
            <div style="color: #3b82f6; margin-bottom: 2px;">有效时长: ${effective}分钟</div>
            <div style="color: #10b981;">学习效率: ${efficiency}%</div>
          </div>
        `
      },
    },
    legend: {
      data: ['总时长', '有效时长'],
      top: 'top',
      right: 'right',
      textStyle: {
        fontSize: 11,
        color: '#374151',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: weekData,
      axisLabel: {
        fontSize: 11,
        color: '#6b7280',
      },
      axisLine: {
        lineStyle: {
          color: '#e5e7eb',
        },
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}min',
        fontSize: 11,
        color: '#6b7280',
      },
      axisLine: {
        show: false,
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed',
        },
      },
    },
    series: [
      {
        name: '总时长',
        type: 'bar',
        data: totalTimeData,
        itemStyle: {
          color: '#e5e7eb',
          borderRadius: [4, 4, 0, 0],
        },
        emphasis: {
          itemStyle: {
            color: '#d1d5db',
          },
        },
        barWidth: '60%',
      },
      {
        name: '有效时长',
        type: 'bar',
        data: effectiveTimeData,
        itemStyle: {
          color: '#3b82f6',
          borderRadius: [4, 4, 0, 0],
        },
        emphasis: {
          itemStyle: {
            color: '#2563eb',
            shadowBlur: 10,
            shadowColor: 'rgba(59, 130, 246, 0.3)',
          },
        },
        barWidth: '60%',
      },
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
  }

  efficiencyChartInstance.setOption(option as any)
}

// 初始化知识点掌握度图
const initKnowledgeChart = () => {
  if (!knowledgeChart.value) return

  knowledgeChartInstance = echarts.init(knowledgeChart.value)

  const filteredPoints = selectedSubject.value
    ? (analyticsStore.knowledgePoints || []).filter((p) => p.subject === selectedSubject.value)
    : (analyticsStore.knowledgePoints || []).slice(0, 10)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151',
        fontSize: 12,
      },
      formatter: (params: any) => {
        const pointName = params[0].name
        const point = filteredPoints.find((p) => p.name === pointName)
        if (!point) return ''
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${point.name}</div>
            <div style="color: ${params[0].color}; margin-bottom: 2px;">掌握度: ${point.masteryLevel}%</div>
            <div style="color: #6b7280; margin-bottom: 2px;">练习次数: ${point.practiceCount}次</div>
            <div style="color: #6b7280; margin-bottom: 2px;">正确率: ${point.correctRate}%</div>
            <div style="color: #6b7280;">学科: ${point.subject}</div>
          </div>
        `
      },
    },
    grid: {
      left: '20%',
      right: '4%',
      bottom: '3%',
      top: '5%',
      containLabel: false,
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%',
        fontSize: 11,
        color: '#6b7280',
      },
      axisLine: {
        show: false,
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed',
        },
      },
    },
    yAxis: {
      type: 'category',
      data: (filteredPoints || []).map((p) =>
        p.name.length > 8 ? p.name.substring(0, 8) + '...' : p.name
      ),
      axisLabel: {
        fontSize: 10,
        color: '#374151',
        fontWeight: '500',
      },
      axisLine: {
        lineStyle: {
          color: '#e5e7eb',
        },
      },
      axisTick: {
        show: false,
      },
    },
    series: [
      {
        name: '掌握度',
        type: 'bar',
        barWidth: '60%',
        data: (filteredPoints || []).map((p) => ({
          value: p.masteryLevel,
          itemStyle: {
            color: p.masteryLevel >= 80 ? '#10b981' : p.masteryLevel >= 60 ? '#f59e0b' : '#ef4444',
            borderRadius: [0, 4, 4, 0],
          },
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.15)',
          },
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          fontSize: 10,
          color: '#374151',
          fontWeight: '500',
        },
      },
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
  }

  knowledgeChartInstance.setOption(option as any)
}

// 初始化热力图
const initHeatmapChart = () => {
  if (!heatmapChart.value) return

  heatmapChartInstance = echarts.init(heatmapChart.value)

  // 生成模拟热力图数据
  const generateHeatmapData = () => {
    const data = []
    const startDate = dayjs(`${selectedYear.value}-01-01`)
    const endDate = dayjs(`${selectedYear.value}-12-31`)

    let currentDate = startDate
    while (currentDate.isBefore(endDate) || currentDate.isSame(endDate)) {
      const value = Math.floor(Math.random() * 4) // 0-3的随机值
      data.push([currentDate.format('YYYY-MM-DD'), value])
      currentDate = currentDate.add(1, 'day')
    }
    return data
  }

  const option = {
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151',
        fontSize: 12,
      },
      formatter: (params: any) => {
        const date = dayjs(params.data[0]).format('YYYY年MM月DD日')
        const intensity = params.data[1]
        const level =
          intensity === 0
            ? '无学习'
            : intensity === 1
              ? '轻度学习'
              : intensity === 2
                ? '中度学习'
                : '高强度学习'
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${date}</div>
            <div style="color: ${params.color}; margin-bottom: 2px;">学习强度: ${level}</div>
            <div style="color: #6b7280;">强度值: ${intensity}</div>
          </div>
        `
      },
    },
    visualMap: {
      min: 0,
      max: 3,
      type: 'piecewise',
      orient: 'horizontal',
      left: 'center',
      top: 5,
      pieces: [
        { min: 0, max: 0, color: '#ebedf0', label: '无学习' },
        { min: 1, max: 1, color: '#c6e48b', label: '轻度' },
        { min: 2, max: 2, color: '#7bc96f', label: '中度' },
        { min: 3, max: 3, color: '#239a3b', label: '高强度' },
      ],
      textStyle: {
        fontSize: 10,
        color: '#374151',
      },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 8,
    },
    calendar: {
      top: 60,
      left: 30,
      right: 30,
      bottom: 20,
      range: selectedYear.value,
      cellSize: ['auto', 15],
      splitLine: {
        show: true,
        lineStyle: {
          color: '#f3f4f6',
          width: 1,
        },
      },
      itemStyle: {
        borderWidth: 1,
        borderColor: '#ffffff',
        borderRadius: 2,
      },
      yearLabel: {
        show: false,
      },
      monthLabel: {
        nameMap: 'cn',
        fontSize: 12,
        color: '#374151',
        fontWeight: '500',
      },
      dayLabel: {
        nameMap: 'cn',
        fontSize: 10,
        color: '#6b7280',
      },
    },
    series: [
      {
        type: 'heatmap',
        coordinateSystem: 'calendar',
        data: generateHeatmapData(),
        emphasis: {
          itemStyle: {
            borderColor: '#3b82f6',
            borderWidth: 2,
          },
        },
      },
    ],
    animation: true,
    animationDuration: 800,
  }

  heatmapChartInstance.setOption(option as any)
}

// 响应式处理
const handleResize = () => {
  studyTimeChartInstance?.resize()
  subjectChartInstance?.resize()
  efficiencyChartInstance?.resize()
  knowledgeChartInstance?.resize()
  heatmapChartInstance?.resize()
}

// 事件处理
const handleTimeRangeChange = () => {
  if (!authStore.isAuthenticated) return
  analyticsStore.fetchLearningStats(timeRange.value)
  analyticsStore.fetchLearningProgress(
    dayjs().subtract(parseInt(timeRange.value), 'day').format('YYYY-MM-DD'),
    dayjs().format('YYYY-MM-DD')
  )
}

const handleSubjectChange = () => {
  if (!authStore.isAuthenticated) return
  analyticsStore.fetchKnowledgePoints(selectedSubject.value || undefined)
}

const handleYearChange = () => {
  if (!authStore.isAuthenticated) return
  analyticsStore.fetchStudyHeatmap(selectedYear.value)
}

// 初始化所有图表
const initAllCharts = () => {
  setTimeout(() => {
    initStudyTimeChart()
    initSubjectChart()
    initEfficiencyChart()
    initKnowledgeChart()
    initHeatmapChart()
  }, 100)
}

// 监听数据变化
watch(
  () => analyticsStore.learningProgress,
  () => {
    if (studyTimeChartInstance) {
      initStudyTimeChart()
    }
  },
  { deep: true }
)

watch(
  () => analyticsStore.subjectStats,
  () => {
    if (subjectChartInstance) {
      initSubjectChart()
    }
  },
  { deep: true }
)

watch(
  () => analyticsStore.knowledgePoints,
  () => {
    if (knowledgeChartInstance) {
      initKnowledgeChart()
    }
  },
  { deep: true }
)

onMounted(() => {
  initAllCharts()
  window.addEventListener('resize', handleResize)

  // 初始化数据 - 需要检查用户是否已登录
  if (authStore.isAuthenticated) {
    analyticsStore.initializeDashboard(timeRange.value)
  }

  // 自动刷新
  if (props.autoRefresh) {
    const interval = setInterval(() => {
      if (authStore.isAuthenticated) {
        analyticsStore.refreshAllData()
      }
    }, 60000) // 每分钟刷新

    onUnmounted(() => {
      clearInterval(interval)
    })
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  studyTimeChartInstance?.dispose()
  subjectChartInstance?.dispose()
  efficiencyChartInstance?.dispose()
  knowledgeChartInstance?.dispose()
  heatmapChartInstance?.dispose()
})
</script>

<style scoped>
.learning-stats-chart {
  width: 100%;
}

.learning-stats-chart :deep(.el-select) {
  min-width: 120px;
}

.learning-stats-chart :deep(.el-card__body) {
  padding: 0;
}
</style>
