<!-- 学习进度趋势图组件 -->
<template>
  <div class="learning-trend-chart bg-white rounded-lg p-6 shadow-sm border">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-900">学习趋势分析</h3>
      <div class="flex items-center space-x-2">
        <el-select v-model="selectedMetric" size="small" @change="updateChart">
          <el-option label="学习时长" value="studyTime" />
          <el-option label="完成作业" value="homework" />
          <el-option label="提问次数" value="questions" />
          <el-option label="正确率" value="accuracy" />
        </el-select>
        <el-select v-model="timeRange" size="small" @change="updateChart">
          <el-option label="最近7天" value="7d" />
          <el-option label="最近30天" value="30d" />
          <el-option label="最近90天" value="90d" />
        </el-select>
        <el-button size="small" :icon="Refresh" @click="refreshData" :loading="loading" circle />
      </div>
    </div>

    <!-- 图表容器 -->
    <div ref="chartContainer" class="w-full" :style="{ height: chartHeight }"></div>

    <!-- 统计摘要 -->
    <div class="stats-summary mt-4 grid grid-cols-4 gap-4">
      <div
        v-for="stat in summaryStats"
        :key="stat.key"
        class="stat-item text-center p-3 rounded-lg"
        :class="stat.bgClass"
      >
        <div class="text-xs text-gray-600 mb-1">{{ stat.label }}</div>
        <div class="text-xl font-bold" :class="stat.textClass">
          {{ stat.value }}
        </div>
        <div
          v-if="stat.trend"
          class="text-xs mt-1"
          :class="stat.trend > 0 ? 'text-green-600' : 'text-red-600'"
        >
          {{ stat.trend > 0 ? '↑' : '↓' }} {{ Math.abs(stat.trend) }}%
        </div>
      </div>
    </div>

    <!-- 数据表格（可选） -->
    <div v-if="showTable" class="data-table mt-4">
      <el-divider>详细数据</el-divider>
      <el-table :data="tableData" size="small" :max-height="200">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="value" :label="getMetricLabel(selectedMetric)" width="100">
          <template #default="{ row }">
            <span :class="getValueClass(row.value)">{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="change" label="环比" width="80">
          <template #default="{ row }">
            <span :class="row.change >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ row.change >= 0 ? '+' : '' }}{{ row.change }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" />
      </el-table>
    </div>

    <!-- 操作按钮 -->
    <div class="actions mt-4 flex justify-between items-center">
      <el-button size="small" @click="showTable = !showTable">
        {{ showTable ? '隐藏数据' : '显示数据' }}
      </el-button>
      <div class="space-x-2">
        <el-button size="small" @click="exportChart">导出图表</el-button>
        <el-button size="small" type="primary" @click="shareReport">分享报告</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { ECharts } from 'echarts'
import dayjs from 'dayjs'

// 接口定义
interface TrendData {
  date: string
  value: number
  change: number
  note?: string
}

interface Props {
  height?: string
  defaultMetric?: string
  defaultTimeRange?: string
  autoRefresh?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  defaultMetric: 'studyTime',
  defaultTimeRange: '30d',
  autoRefresh: false,
})

// 响应式数据
const chartContainer = ref<HTMLDivElement>()
let chartInstance: ECharts | null = null

const selectedMetric = ref(props.defaultMetric)
const timeRange = ref(props.defaultTimeRange)
const loading = ref(false)
const showTable = ref(false)

// 计算属性
const chartHeight = computed(() => props.height)

const summaryStats = computed(() => {
  return [
    {
      key: 'average',
      label: '平均值',
      value: '85',
      bgClass: 'bg-blue-50',
      textClass: 'text-blue-600',
      trend: 5,
    },
    {
      key: 'max',
      label: '最高值',
      value: '120',
      bgClass: 'bg-green-50',
      textClass: 'text-green-600',
      trend: 12,
    },
    {
      key: 'min',
      label: '最低值',
      value: '45',
      bgClass: 'bg-yellow-50',
      textClass: 'text-yellow-600',
      trend: -8,
    },
    {
      key: 'total',
      label: '总计',
      value: '2550',
      bgClass: 'bg-purple-50',
      textClass: 'text-purple-600',
      trend: 15,
    },
  ]
})

const tableData = computed<TrendData[]>(() => {
  const days = getDaysCount()
  const data: TrendData[] = []

  for (let i = 0; i < days; i++) {
    const date = dayjs().subtract(i, 'day').format('MM-DD')
    const value = Math.floor(Math.random() * 100) + 20
    const change = Math.floor(Math.random() * 40) - 20

    data.unshift({
      date,
      value,
      change,
      note: value > 80 ? '表现优秀' : value < 40 ? '需要加强' : '',
    })
  }

  return data
})

// 方法
const getDaysCount = () => {
  switch (timeRange.value) {
    case '7d':
      return 7
    case '30d':
      return 30
    case '90d':
      return 90
    default:
      return 30
  }
}

const getMetricLabel = (metric: string) => {
  const labels: Record<string, string> = {
    studyTime: '学习时长(分钟)',
    homework: '作业数量',
    questions: '提问次数',
    accuracy: '正确率(%)',
  }
  return labels[metric] || metric
}

const getValueClass = (value: number) => {
  if (value > 80) return 'text-green-600 font-semibold'
  if (value < 40) return 'text-red-600 font-semibold'
  return 'text-gray-700'
}

const initChart = () => {
  if (!chartContainer.value) return

  chartInstance = echarts.init(chartContainer.value)
  updateChart()

  // 响应式调整
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chartInstance) return

  const days = getDaysCount()
  const dates: string[] = []
  const values: number[] = []

  for (let i = days - 1; i >= 0; i--) {
    dates.push(dayjs().subtract(i, 'day').format('MM-DD'))
    values.push(Math.floor(Math.random() * 100) + 20)
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151',
      },
      formatter: (params: any) => {
        const data = params[0]
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${data.name}</div>
            <div style="color: #3b82f6;">${getMetricLabel(selectedMetric.value)}: ${data.value}</div>
          </div>
        `
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: '#e5e7eb',
        },
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11,
      },
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11,
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
        name: getMetricLabel(selectedMetric.value),
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: values,
        lineStyle: {
          width: 3,
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: '#3b82f6' },
              { offset: 1, color: '#8b5cf6' },
            ],
          },
        },
        itemStyle: {
          color: '#3b82f6',
          borderWidth: 2,
          borderColor: '#fff',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
            ],
          },
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: '#2563eb',
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(59, 130, 246, 0.5)',
          },
        },
      },
    ],
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance?.resize()
}

const refreshData = async () => {
  loading.value = true
  try {
    // 模拟数据加载
    await new Promise((resolve) => setTimeout(resolve, 500))
    updateChart()
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const exportChart = () => {
  if (!chartInstance) return

  const url = chartInstance.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff',
  })

  const link = document.createElement('a')
  link.download = `学习趋势-${dayjs().format('YYYY-MM-DD')}.png`
  link.href = url
  link.click()

  ElMessage.success('图表已导出')
}

const shareReport = () => {
  ElMessage.info('分享功能开发中...')
}

// 生命周期
onMounted(() => {
  initChart()

  if (props.autoRefresh) {
    setInterval(refreshData, 60000) // 每分钟刷新
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

// 监听变化
watch([selectedMetric, timeRange], () => {
  updateChart()
})
</script>

<style scoped lang="scss">
.learning-trend-chart {
  .stat-item {
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
  }
}
</style>
