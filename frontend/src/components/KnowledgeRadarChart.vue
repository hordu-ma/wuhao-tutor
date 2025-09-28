<template>
  <div class="knowledge-radar-chart">
    <div class="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">知识点掌握雷达图</h3>
        <div class="flex items-center space-x-3">
          <el-select v-model="selectedSubject" size="small" @change="handleSubjectChange">
            <el-option label="全部学科" value="" />
            <el-option
              v-for="subject in subjects"
              :key="subject"
              :label="subject"
              :value="subject"
            />
          </el-select>
          <el-button
            size="small"
            type="primary"
            :icon="Refresh"
            @click="refreshData"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </div>

      <div ref="radarChart" class="w-full" :style="{ height: chartHeight }"></div>

      <!-- 图例和说明 -->
      <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-green-500 rounded"></div>
          <span class="text-sm text-gray-600">优秀 (≥80%)</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-yellow-500 rounded"></div>
          <span class="text-sm text-gray-600">良好 (60-79%)</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-red-500 rounded"></div>
          <span class="text-sm text-gray-600">待提高 (<60%)</span>
        </div>
      </div>

      <!-- 详细数据表格 -->
      <div v-if="showDetail" class="mt-6">
        <el-divider>详细数据</el-divider>
        <el-table
          :data="tableData"
          size="small"
          :max-height="300"
          style="width: 100%"
        >
          <el-table-column prop="name" label="知识点" min-width="150" />
          <el-table-column prop="subject" label="学科" width="80" />
          <el-table-column prop="masteryLevel" label="掌握度" width="100">
            <template #default="{ row }">
              <el-progress
                :percentage="row.masteryLevel"
                :color="getProgressColor(row.masteryLevel)"
                :stroke-width="8"
                text-inside
              />
            </template>
          </el-table-column>
          <el-table-column prop="practiceCount" label="练习次数" width="100" />
          <el-table-column prop="correctRate" label="正确率" width="100">
            <template #default="{ row }">
              <span :class="getCorrectRateClass(row.correctRate)">
                {{ row.correctRate }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="difficulty" label="难度" width="80">
            <template #default="{ row }">
              <el-tag
                :type="getDifficultyType(row.difficulty)"
                size="small"
              >
                {{ getDifficultyText(row.difficulty) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="lastPracticeTime" label="最后练习" width="120">
            <template #default="{ row }">
              <span class="text-gray-600 text-xs">
                {{ formatTime(row.lastPracticeTime) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 操作按钮 -->
      <div class="mt-4 flex justify-between items-center">
        <el-button
          size="small"
          @click="showDetail = !showDetail"
        >
          {{ showDetail ? '隐藏详情' : '显示详情' }}
        </el-button>
        <div class="space-x-2">
          <el-button size="small" @click="exportData">导出数据</el-button>
          <el-button size="small" type="primary" @click="generateReport">
            生成报告
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { useAnalyticsStore } from '../stores/analytics'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { ECharts } from 'echarts'
import type { KnowledgePoint } from '../types/analytics'
import dayjs from 'dayjs'

interface Props {
  height?: string
  maxPoints?: number
  showComparison?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  maxPoints: 8,
  showComparison: false
})

const analyticsStore = useAnalyticsStore()

// 图表引用和实例
const radarChart = ref<HTMLDivElement>()
let radarChartInstance: ECharts | null = null

// 控制状态
const selectedSubject = ref('')
const showDetail = ref(false)
const loading = ref(false)

// 计算属性
const chartHeight = computed(() => props.height)

const subjects = computed(() => {
  return Array.from(new Set(analyticsStore.knowledgePoints.map(p => p.subject)))
})

const filteredKnowledgePoints = computed(() => {
  let points = analyticsStore.knowledgePoints

  if (selectedSubject.value) {
    points = points.filter(p => p.subject === selectedSubject.value)
  }

  // 按掌握度排序，优先显示薄弱的知识点
  return points
    .sort((a, b) => a.masteryLevel - b.masteryLevel)
    .slice(0, props.maxPoints)
})

const tableData = computed(() => {
  return filteredKnowledgePoints.value
})

// 雷达图配置数据
const radarData = computed(() => {
  const points = filteredKnowledgePoints.value

  // 雷达图指标配置
  const indicator = points.map(point => ({
    name: point.name.length > 6 ? point.name.substring(0, 6) + '...' : point.name,
    max: 100,
    axisLabel: {
      show: true,
      fontSize: 10
    }
  }))

  // 数据系列
  const seriesData = [{
    name: '掌握度',
    value: points.map(point => point.masteryLevel),
    areaStyle: {
      color: 'rgba(59, 130, 246, 0.2)'
    },
    lineStyle: {
      color: '#3b82f6',
      width: 2
    },
    symbol: 'circle',
    symbolSize: 6,
    itemStyle: {
      color: '#3b82f6'
    }
  }]

  // 如果显示对比，添加正确率数据
  if (props.showComparison) {
    seriesData.push({
      name: '正确率',
      value: points.map(point => point.correctRate),
      areaStyle: {
        color: 'rgba(16, 185, 129, 0.2)'
      },
      lineStyle: {
        color: '#10b981',
        width: 2
      },
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: {
        color: '#10b981'
      }
    })
  }

  return { indicator, seriesData }
})

// 初始化雷达图
const initRadarChart = () => {
  if (!radarChart.value) return

  radarChartInstance = echarts.init(radarChart.value)

  const { indicator, seriesData } = radarData.value

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const point = filteredKnowledgePoints.value[params.dataIndex]
        if (!point) return ''

        return `
          <div class="text-sm">
            <div class="font-medium mb-2">${point.name}</div>
            <div>学科: ${point.subject}</div>
            <div>掌握度: ${point.masteryLevel}%</div>
            <div>正确率: ${point.correctRate}%</div>
            <div>练习次数: ${point.practiceCount}次</div>
            <div>难度: ${getDifficultyText(point.difficulty)}</div>
          </div>
        `
      }
    },
    legend: {
      data: props.showComparison ? ['掌握度', '正确率'] : ['掌握度'],
      orient: 'horizontal',
      top: 'bottom',
      itemGap: 20
    },
    radar: {
      indicator: indicator,
      radius: '65%',
      center: ['50%', '50%'],
      startAngle: 90,
      splitNumber: 4,
      shape: 'polygon',
      splitArea: {
        areaStyle: {
          color: ['rgba(250, 250, 250, 0.1)', 'rgba(200, 200, 200, 0.1)']
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(200, 200, 200, 0.5)',
          width: 1
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(200, 200, 200, 0.5)'
        }
      },
      name: {
        textStyle: {
          fontSize: 11,
          color: '#666'
        }
      }
    },
    series: [{
      name: '知识点掌握度',
      type: 'radar',
      data: seriesData,
      emphasis: {
        areaStyle: {
          color: 'rgba(59, 130, 246, 0.4)'
        }
      }
    }]
  }

  radarChartInstance.setOption(option)

  // 添加点击事件
  radarChartInstance.on('click', (params) => {
    const point = filteredKnowledgePoints.value[params.dataIndex]
    if (point) {
      handlePointClick(point)
    }
  })
}

// 处理知识点点击
const handlePointClick = (point: KnowledgePoint) => {
  ElMessage.info(`点击了知识点: ${point.name}`)
  // 这里可以跳转到具体的知识点详情页面或弹出详情对话框
}

// 获取进度条颜色
const getProgressColor = (value: number) => {
  if (value >= 80) return '#10b981'
  if (value >= 60) return '#f59e0b'
  return '#ef4444'
}

// 获取正确率样式类
const getCorrectRateClass = (rate: number) => {
  if (rate >= 80) return 'text-green-600 font-medium'
  if (rate >= 60) return 'text-yellow-600 font-medium'
  return 'text-red-600 font-medium'
}

// 获取难度类型
const getDifficultyType = (difficulty: string) => {
  switch (difficulty) {
    case 'easy': return 'success'
    case 'medium': return 'warning'
    case 'hard': return 'danger'
    default: return 'info'
  }
}

// 获取难度文本
const getDifficultyText = (difficulty: string) => {
  switch (difficulty) {
    case 'easy': return '简单'
    case 'medium': return '中等'
    case 'hard': return '困难'
    default: return '未知'
  }
}

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format('MM-DD HH:mm')
}

// 响应式处理
const handleResize = () => {
  radarChartInstance?.resize()
}

// 事件处理
const handleSubjectChange = () => {
  analyticsStore.fetchKnowledgePoints(selectedSubject.value || undefined)
}

const refreshData = async () => {
  loading.value = true
  try {
    await analyticsStore.fetchKnowledgePoints(selectedSubject.value || undefined)
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const exportData = () => {
  // 导出CSV格式数据
  const csvContent = [
    ['知识点', '学科', '掌握度(%)', '练习次数', '正确率(%)', '难度', '最后练习时间'],
    ...tableData.value.map(item => [
      item.name,
      item.subject,
      item.masteryLevel,
      item.practiceCount,
      item.correctRate,
      getDifficultyText(item.difficulty),
      formatTime(item.lastPracticeTime)
    ])
  ].map(row => row.join(',')).join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `知识点掌握度_${dayjs().format('YYYY-MM-DD')}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  ElMessage.success('数据导出成功')
}

const generateReport = () => {
  // 生成学习报告
  ElMessage.info('正在生成学习报告...')
  // 这里可以调用API生成详细的学习报告
}

// 监听数据变化
watch(() => analyticsStore.knowledgePoints, () => {
  if (radarChartInstance) {
    initRadarChart()
  }
}, { deep: true })

watch(() => selectedSubject.value, () => {
  if (radarChartInstance) {
    initRadarChart()
  }
})

onMounted(() => {
  setTimeout(() => {
    initRadarChart()
  }, 100)

  window.addEventListener('resize', handleResize)

  // 初始化数据
  if (analyticsStore.knowledgePoints.length === 0) {
    analyticsStore.fetchKnowledgePoints()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChartInstance?.dispose()
})
</script>

<style scoped>
.knowledge-radar-chart {
  @apply w-full;
}

.knowledge-radar-chart :deep(.el-select) {
  min-width: 120px;
}

.knowledge-radar-chart :deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

.knowledge-radar-chart :deep(.el-table th) {
  background-color: #f9fafb;
}

.knowledge-radar-chart :deep(.el-progress-bar__inner) {
  border-radius: 4px;
}

.knowledge-radar-chart :deep(.el-divider__text) {
  @apply text-gray-700 font-medium;
}
</style>
