<!-- 学习日历热力图组件 -->
<template>
  <div class="learning-calendar bg-white rounded-lg p-6 shadow-sm border">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-900">学习日历</h3>
      <div class="flex items-center space-x-2">
        <el-button size="small" :icon="ArrowLeft" @click="previousMonth" circle />
        <span class="text-sm font-medium px-2 min-w-32 text-center">
          {{ currentMonth.format('YYYY年MM月') }}
        </span>
        <el-button
          size="small"
          :icon="ArrowRight"
          @click="nextMonth"
          :disabled="isCurrentMonth"
          circle
        />
      </div>
    </div>

    <!-- 日历热力图 -->
    <div class="calendar-grid">
      <!-- 星期标题 -->
      <div class="weekday-headers grid grid-cols-7 gap-2 mb-2">
        <div
          v-for="day in weekdays"
          :key="day"
          class="text-xs text-gray-500 text-center font-medium"
        >
          {{ day }}
        </div>
      </div>

      <!-- 日历天数 -->
      <div class="calendar-days grid grid-cols-7 gap-2">
        <div
          v-for="(day, index) in calendarDays"
          :key="index"
          class="calendar-day aspect-square rounded-lg transition-all cursor-pointer"
          :class="getDayClass(day)"
          @click="handleDayClick(day)"
        >
          <div class="w-full h-full flex flex-col items-center justify-center p-1">
            <span class="text-sm font-medium" :class="getDayTextClass(day)">
              {{ day.date }}
            </span>
            <div
              v-if="day.studyMinutes > 0"
              class="mt-1 text-xs"
              :class="getStudyTimeTextClass(day)"
            >
              {{ formatStudyTime(day.studyMinutes) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="legend mt-6 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <span class="text-xs text-gray-600">学习强度:</span>
        <div class="flex items-center space-x-2">
          <div
            v-for="level in intensityLevels"
            :key="level.label"
            class="flex items-center space-x-1"
          >
            <div class="w-4 h-4 rounded" :class="level.colorClass"></div>
            <span class="text-xs text-gray-600">{{ level.label }}</span>
          </div>
        </div>
      </div>
      <div class="text-xs text-gray-500">本月总计: {{ monthlyTotalMinutes }}分钟</div>
    </div>

    <!-- 每日详情对话框 -->
    <el-dialog
      v-model="showDayDetail"
      :title="`${selectedDay?.fullDate || ''} 学习详情`"
      width="500px"
    >
      <div v-if="selectedDay" class="day-detail-content">
        <!-- 学习时长 -->
        <div class="detail-section mb-4">
          <div class="flex items-center justify-between mb-2">
            <h4 class="text-sm font-semibold text-gray-900">学习时长</h4>
            <span class="text-lg font-bold text-blue-600">
              {{ formatStudyTime(selectedDay.studyMinutes) }}
            </span>
          </div>
          <el-progress
            :percentage="getStudyProgress(selectedDay.studyMinutes)"
            :color="getProgressColor(selectedDay.studyMinutes)"
            :stroke-width="8"
          />
        </div>

        <!-- 学习活动 -->
        <div class="detail-section mb-4">
          <h4 class="text-sm font-semibold text-gray-900 mb-3">学习活动</h4>
          <div class="space-y-2">
            <div
              v-for="activity in selectedDay.activities"
              :key="activity.id"
              class="activity-item flex items-center justify-between p-2 bg-gray-50 rounded"
            >
              <div class="flex items-center space-x-3">
                <el-icon :color="activity.color">
                  <component :is="activity.icon" />
                </el-icon>
                <div>
                  <div class="text-sm text-gray-800">{{ activity.name }}</div>
                  <div class="text-xs text-gray-500">{{ activity.subject }}</div>
                </div>
              </div>
              <span class="text-xs text-gray-600"> {{ activity.duration }}分钟 </span>
            </div>
          </div>
        </div>

        <!-- 完成情况 -->
        <div class="detail-section">
          <h4 class="text-sm font-semibold text-gray-900 mb-3">完成情况</h4>
          <div class="grid grid-cols-3 gap-3">
            <div class="stat-item text-center p-3 bg-green-50 rounded">
              <div class="text-2xl font-bold text-green-600">
                {{ selectedDay.completedTasks }}
              </div>
              <div class="text-xs text-gray-600 mt-1">已完成</div>
            </div>
            <div class="stat-item text-center p-3 bg-blue-50 rounded">
              <div class="text-2xl font-bold text-blue-600">
                {{ selectedDay.questions }}
              </div>
              <div class="text-xs text-gray-600 mt-1">提问数</div>
            </div>
            <div class="stat-item text-center p-3 bg-purple-50 rounded">
              <div class="text-2xl font-bold text-purple-600">
                {{ selectedDay.achievements }}
              </div>
              <div class="text-xs text-gray-600 mt-1">成就数</div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDayDetail = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ArrowLeft, ArrowRight, Document, ChatDotRound } from '@element-plus/icons-vue'
import dayjs, { Dayjs } from 'dayjs'
import { useAnalyticsStore } from '@/stores/analytics'

// 接口定义
interface CalendarDay {
  date: number
  fullDate: string
  isCurrentMonth: boolean
  isToday: boolean
  studyMinutes: number
  activities: Activity[]
  completedTasks: number
  questions: number
  achievements: number
}

interface Activity {
  id: string
  name: string
  subject: string
  duration: number
  icon: any
  color: string
}

// Props
interface Props {
  autoRefresh?: boolean
  showDetails?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: false,
  showDetails: true,
})

// Store
const analyticsStore = useAnalyticsStore()

// 响应式数据
const currentMonth = ref(dayjs())
const showDayDetail = ref(false)
const selectedDay = ref<CalendarDay | null>(null)

// 常量
const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const intensityLevels = [
  { label: '无', colorClass: 'bg-gray-100' },
  { label: '少', colorClass: 'bg-green-100' },
  { label: '中', colorClass: 'bg-green-300' },
  { label: '多', colorClass: 'bg-green-500' },
  { label: '极多', colorClass: 'bg-green-700' },
]

// 计算属性
const isCurrentMonth = computed(() => {
  return currentMonth.value.isSame(dayjs(), 'month')
})

const calendarDays = computed(() => {
  const days: CalendarDay[] = []
  const firstDay = currentMonth.value.startOf('month')
  const lastDay = currentMonth.value.endOf('month')
  const startWeekday = firstDay.day()
  const totalDays = lastDay.date()

  // 添加上个月的填充日期
  const prevMonthLastDay = firstDay.subtract(1, 'day')
  for (let i = startWeekday - 1; i >= 0; i--) {
    const date = prevMonthLastDay.subtract(i, 'day')
    days.push(createCalendarDay(date, false))
  }

  // 添加当月日期
  for (let i = 1; i <= totalDays; i++) {
    const date = firstDay.date(i)
    days.push(createCalendarDay(date, true))
  }

  // 添加下个月的填充日期
  const remainingDays = 7 - (days.length % 7)
  if (remainingDays < 7) {
    for (let i = 1; i <= remainingDays; i++) {
      const date = lastDay.add(i, 'day')
      days.push(createCalendarDay(date, false))
    }
  }

  return days
})

const monthlyTotalMinutes = computed(() => {
  return calendarDays.value
    .filter((day) => day.isCurrentMonth)
    .reduce((total, day) => total + day.studyMinutes, 0)
})

// 方法
const createCalendarDay = (date: Dayjs, isCurrentMonth: boolean): CalendarDay => {
  const studyData = getStudyDataForDate(date)

  return {
    date: date.date(),
    fullDate: date.format('YYYY-MM-DD'),
    isCurrentMonth,
    isToday: date.isSame(dayjs(), 'day'),
    studyMinutes: studyData.minutes,
    activities: studyData.activities,
    completedTasks: studyData.completedTasks,
    questions: studyData.questions,
    achievements: studyData.achievements,
  }
}

const getStudyDataForDate = (_date: Dayjs) => {
  // 这里应该从 store 获取真实数据，现在使用模拟数据
  const randomMinutes = Math.floor(Math.random() * 240)

  return {
    minutes: randomMinutes,
    activities:
      randomMinutes > 0
        ? [
            {
              id: '1',
              name: '作业批改',
              subject: '数学',
              duration: Math.floor(randomMinutes * 0.4),
              icon: Document,
              color: '#3b82f6',
            },
            {
              id: '2',
              name: '学习问答',
              subject: '英语',
              duration: Math.floor(randomMinutes * 0.6),
              icon: ChatDotRound,
              color: '#10b981',
            },
          ]
        : [],
    completedTasks: Math.floor(randomMinutes / 30),
    questions: Math.floor(randomMinutes / 20),
    achievements: Math.floor(randomMinutes / 60),
  }
}

const getDayClass = (day: CalendarDay) => {
  const classes = []

  if (!day.isCurrentMonth) {
    classes.push('bg-gray-50 opacity-50')
  } else if (day.isToday) {
    classes.push('ring-2 ring-blue-500 bg-blue-50')
  } else if (day.studyMinutes === 0) {
    classes.push('bg-gray-100 hover:bg-gray-200')
  } else if (day.studyMinutes < 30) {
    classes.push('bg-green-100 hover:bg-green-200')
  } else if (day.studyMinutes < 60) {
    classes.push('bg-green-300 hover:bg-green-400')
  } else if (day.studyMinutes < 120) {
    classes.push('bg-green-500 hover:bg-green-600 text-white')
  } else {
    classes.push('bg-green-700 hover:bg-green-800 text-white')
  }

  return classes.join(' ')
}

const getDayTextClass = (day: CalendarDay) => {
  if (day.studyMinutes >= 60) {
    return 'text-white'
  }
  if (!day.isCurrentMonth) {
    return 'text-gray-400'
  }
  if (day.isToday) {
    return 'text-blue-600 font-bold'
  }
  return 'text-gray-700'
}

const getStudyTimeTextClass = (day: CalendarDay) => {
  return day.studyMinutes >= 60 ? 'text-white' : 'text-gray-600'
}

const formatStudyTime = (minutes: number) => {
  if (minutes === 0) return '0分'
  if (minutes < 60) return `${minutes}分`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}时${mins}分` : `${hours}时`
}

const getStudyProgress = (minutes: number) => {
  // 假设每天目标120分钟
  const target = 120
  return Math.min(100, Math.round((minutes / target) * 100))
}

const getProgressColor = (minutes: number) => {
  if (minutes >= 120) return '#10b981' // green
  if (minutes >= 60) return '#3b82f6' // blue
  if (minutes >= 30) return '#f59e0b' // yellow
  return '#ef4444' // red
}

const previousMonth = () => {
  currentMonth.value = currentMonth.value.subtract(1, 'month')
}

const nextMonth = () => {
  if (!isCurrentMonth.value) {
    currentMonth.value = currentMonth.value.add(1, 'month')
  }
}

const handleDayClick = (day: CalendarDay) => {
  if (!day.isCurrentMonth || day.studyMinutes === 0) return

  selectedDay.value = day
  showDayDetail.value = true
}

// 生命周期
onMounted(async () => {
  if (props.autoRefresh) {
    // 加载日历数据
    await analyticsStore.fetchLearningStats('30d')
  }
})

// 监听月份变化
watch(currentMonth, async () => {
  // 加载新月份的数据
  await analyticsStore.fetchLearningStats('30d')
})
</script>

<style scoped lang="scss">
.learning-calendar {
  .calendar-day {
    min-height: 60px;

    @media (max-width: 768px) {
      min-height: 48px;
    }
  }

  .activity-item {
    &:hover {
      background-color: #e5e7eb;
    }
  }
}
</style>
