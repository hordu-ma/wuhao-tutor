/**
 * 学情分析 Pinia Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import dayjs from 'dayjs'
import type {
  LearningStats,
  LearningProgress,
  KnowledgePoint,
  SubjectStats,
  LearningRecommendation,
  LearningGoal,
  ErrorAnalysis,
  LearningReport,
  TimeDistribution,
  KnowledgeNetwork,
  EfficiencyAnalysis,
  Achievement,
  StudyPatternAnalysis,
  HeatmapData,
} from '../types/analytics'
import {
  getLearningStats,
  getLearningProgress,
  getKnowledgePoints,
  getSubjectStats,
  getLearningRecommendations,
  getLearningGoals,
  deleteLearningGoal,
  getErrorAnalysis,
  getLearningReport,
  getTimeDistribution,
  getStudyHeatmap,
  getKnowledgeNetwork,
  getEfficiencyAnalysis,
  getAchievements,
  getStudyPatternAnalysis,
  getLeaderboard,
  getPersonalInsights,
  getStudyCalendar,
} from '../api/analytics'

export const useAnalyticsStore = defineStore('analytics', () => {
  // 基础状态
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 学习统计数据
  const learningStats = ref<LearningStats | null>(null)
  const learningProgress = ref<LearningProgress[]>([])
  const knowledgePoints = ref<KnowledgePoint[]>([])
  const subjectStats = ref<SubjectStats[]>([])
  const learningRecommendations = ref<LearningRecommendation[]>([])
  const learningGoals = ref<LearningGoal[]>([])
  const errorAnalysis = ref<ErrorAnalysis[]>([])
  const learningReports = ref<Record<string, LearningReport>>({})
  const timeDistribution = ref<TimeDistribution[]>([])
  const studyHeatmap = ref<HeatmapData[]>([])
  const knowledgeNetwork = ref<KnowledgeNetwork | null>(null)
  const efficiencyAnalysis = ref<EfficiencyAnalysis | null>(null)
  const achievements = ref<Achievement[]>([])
  const studyPattern = ref<StudyPatternAnalysis | null>(null)
  const leaderboard = ref<any[]>([])
  const personalInsights = ref<any>(null)
  const studyCalendar = ref<any[]>([])

  // 过滤和设置
  const selectedTimeRange = ref('30d')
  const selectedSubject = ref<string | undefined>()
  const showOnlyWeakPoints = ref(false)
  const chartTheme = ref<'light' | 'dark'>('light')

  // Computed
  const totalStudyHours = computed(() => {
    return learningStats.value ? Math.round(learningStats.value.totalStudyTime / 60) : 0
  })

  const completionRate = computed(() => {
    if (!learningStats.value || learningStats.value.totalHomework === 0) return 0
    return Math.round(
      (learningStats.value.completedHomework / learningStats.value.totalHomework) * 100
    )
  })

  const weakKnowledgePoints = computed(() => {
    return knowledgePoints.value
      .filter((point) => point.masteryLevel < 60)
      .sort((a, b) => a.masteryLevel - b.masteryLevel)
      .slice(0, 10)
  })

  const topSubjects = computed(() => {
    return subjectStats.value.sort((a, b) => b.averageScore - a.averageScore).slice(0, 5)
  })

  const activeGoals = computed(() => {
    return learningGoals.value.filter((goal) => goal.status === 'active')
  })

  const completedGoals = computed(() => {
    return learningGoals.value.filter((goal) => goal.status === 'completed')
  })

  const unlockedAchievements = computed(() => {
    return achievements.value.filter((achievement) => achievement.unlocked)
  })

  const availableAchievements = computed(() => {
    return achievements.value.filter((achievement) => !achievement.unlocked)
  })

  const studyStreak = computed(() => {
    return learningStats.value?.streak || 0
  })

  const learningEfficiency = computed(() => {
    return efficiencyAnalysis.value?.efficiency || 0
  })

  // 错误处理
  const handleError = (err: any) => {
    console.error('Analytics store error:', err)
    error.value = err.response?.data?.message || err.message || '操作失败'
  }

  // 清除错误
  const clearError = () => {
    error.value = null
  }

  // 设置加载状态
  const setLoading = (isLoading: boolean) => {
    loading.value = isLoading
  }

  // 获取学习统计数据
  const fetchLearningStats = async (timeRange: string = '30d') => {
    try {
      setLoading(true)
      selectedTimeRange.value = timeRange
      const response = await getLearningStats(timeRange)
      learningStats.value = response.data
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  // 获取学习进度数据
  const fetchLearningProgress = async (startDate: string, endDate: string) => {
    try {
      setLoading(true)
      const response = await getLearningProgress(startDate, endDate)
      learningProgress.value = response.data
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  // 获取知识点数据
  const fetchKnowledgePoints = async (subject?: string) => {
    try {
      setLoading(true)
      selectedSubject.value = subject
      const response = await getKnowledgePoints(subject)
      knowledgePoints.value = response.data
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  // 获取学科统计
  const fetchSubjectStats = async (timeRange: string = '30d') => {
    try {
      setLoading(true)
      const response = await getSubjectStats(timeRange)
      subjectStats.value = response.data
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  // 获取学习建议
  const fetchRecommendations = async (limit: number = 10) => {
    try {
      const response = await getLearningRecommendations(limit)
      learningRecommendations.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取学习目标
  const fetchGoals = async (status?: string) => {
    try {
      const response = await getLearningGoals(status)
      learningGoals.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 创建目标 - TODO: 待后端实现
  const createGoal = async (_goal: Omit<LearningGoal, 'id' | 'createdAt' | 'currentValue'>) => {
    console.warn('createGoal: 后端 API 未实现')
    return null
  }

  // 更新目标 - TODO: 待后端实现
  const updateGoal = async (_id: string, _updates: Partial<LearningGoal>) => {
    console.warn('updateGoal: 后端 API 未实现')
    return null
  }

  // 删除目标
  const deleteGoal = async (id: string) => {
    try {
      setLoading(true)
      await deleteLearningGoal(id)
      learningGoals.value = learningGoals.value.filter((goal) => goal.id !== id)
    } catch (err) {
      handleError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // 获取错题分析
  const fetchErrorAnalysis = async (subject?: string, limit: number = 20) => {
    try {
      const response = await getErrorAnalysis(subject, limit)
      errorAnalysis.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取学习报告
  const fetchLearningReport = async (type: 'daily' | 'weekly' | 'monthly', date?: string) => {
    try {
      setLoading(true)
      const response = await getLearningReport(type, date)
      const reportKey = `${type}-${date || dayjs().format('YYYY-MM-DD')}`
      learningReports.value[reportKey] = response.data
      return response.data
    } catch (err) {
      handleError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // 获取时间分布
  const fetchTimeDistribution = async (timeRange: string = '7d') => {
    try {
      const response = await getTimeDistribution(timeRange)
      timeDistribution.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取学习热力图
  const fetchStudyHeatmap = async (year: number) => {
    try {
      const response = await getStudyHeatmap(year)
      studyHeatmap.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取知识点网络
  const fetchKnowledgeNetwork = async (subject?: string) => {
    try {
      setLoading(true)
      const response = await getKnowledgeNetwork(subject)
      knowledgeNetwork.value = response.data
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  // 获取效率分析
  const fetchEfficiencyAnalysis = async (timeRange: string = '30d') => {
    try {
      const response = await getEfficiencyAnalysis(timeRange)
      efficiencyAnalysis.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取成就
  const fetchAchievements = async (type?: string) => {
    try {
      const response = await getAchievements(type)
      achievements.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取学习模式分析
  const fetchStudyPattern = async (timeRange: string = '30d') => {
    try {
      const response = await getStudyPatternAnalysis(timeRange)
      studyPattern.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取排行榜
  const fetchLeaderboard = async (type: string, period: string = 'week') => {
    try {
      const response = await getLeaderboard(type as any, period)
      leaderboard.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取个人洞察
  const fetchPersonalInsights = async () => {
    try {
      const response = await getPersonalInsights()
      personalInsights.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 获取学习日历
  const fetchStudyCalendar = async (year: number, month: number) => {
    try {
      const response = await getStudyCalendar(year, month)
      studyCalendar.value = response.data
    } catch (err) {
      handleError(err)
    }
  }

  // 初始化仪表板数据
  const initializeDashboard = async (timeRange: string = '30d') => {
    try {
      setLoading(true)
      // 仅调用后端已实现的 API
      // TODO: 其他功能待后端实现后启用
      await Promise.allSettled([
        fetchLearningStats(timeRange),
        fetchKnowledgePoints(), // 使用 getKnowledgeMap API
      ])
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  // 刷新所有数据
  const refreshAllData = async () => {
    await initializeDashboard(selectedTimeRange.value)
  }

  // 重置状态
  const resetState = () => {
    learningStats.value = null
    learningProgress.value = []
    knowledgePoints.value = []
    subjectStats.value = []
    learningRecommendations.value = []
    learningGoals.value = []
    errorAnalysis.value = []
    learningReports.value = {}
    timeDistribution.value = []
    studyHeatmap.value = []
    knowledgeNetwork.value = null
    efficiencyAnalysis.value = null
    achievements.value = []
    studyPattern.value = null
    leaderboard.value = []
    personalInsights.value = null
    studyCalendar.value = []
    error.value = null
    loading.value = false
  }

  // 设置过滤器
  const setTimeRange = (range: string) => {
    selectedTimeRange.value = range
  }

  const setSubject = (subject: string | undefined) => {
    selectedSubject.value = subject
  }

  const setShowOnlyWeakPoints = (show: boolean) => {
    showOnlyWeakPoints.value = show
  }

  const setChartTheme = (theme: 'light' | 'dark') => {
    chartTheme.value = theme
  }

  // 获取格式化的统计数据
  const getFormattedStats = computed(() => ({
    studyTime: `${totalStudyHours.value}小时`,
    completionRate: `${completionRate.value}%`,
    averageScore: learningStats.value?.averageScore
      ? `${learningStats.value.averageScore}分`
      : '0分',
    streak: `${studyStreak.value}天`,
    totalHomework: learningStats.value?.totalHomework || 0,
    totalQuestions: learningStats.value?.totalQuestions || 0,
  }))

  return {
    // 状态
    loading,
    error,
    learningStats,
    learningProgress,
    knowledgePoints,
    subjectStats,
    learningRecommendations,
    learningGoals,
    errorAnalysis,
    learningReports,
    timeDistribution,
    studyHeatmap,
    knowledgeNetwork,
    efficiencyAnalysis,
    achievements,
    studyPattern,
    leaderboard,
    personalInsights,
    studyCalendar,
    selectedTimeRange,
    selectedSubject,
    showOnlyWeakPoints,
    chartTheme,

    // Computed
    totalStudyHours,
    completionRate,
    weakKnowledgePoints,
    topSubjects,
    activeGoals,
    completedGoals,
    unlockedAchievements,
    availableAchievements,
    studyStreak,
    learningEfficiency,
    getFormattedStats,

    // Actions
    clearError,
    fetchLearningStats,
    fetchLearningProgress,
    fetchKnowledgePoints,
    fetchSubjectStats,
    fetchRecommendations,
    fetchGoals,
    createGoal,
    updateGoal,
    deleteGoal,
    fetchErrorAnalysis,
    fetchLearningReport,
    fetchTimeDistribution,
    fetchStudyHeatmap,
    fetchKnowledgeNetwork,
    fetchEfficiencyAnalysis,
    fetchAchievements,
    fetchStudyPattern,
    fetchLeaderboard,
    fetchPersonalInsights,
    fetchStudyCalendar,
    initializeDashboard,
    refreshAllData,
    resetState,
    setTimeRange,
    setSubject,
    setShowOnlyWeakPoints,
    setChartTheme,
  }
})
