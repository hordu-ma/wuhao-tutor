/**
 * 学情分析 API 接口
 */

import http from './http'
import type {
  AnalyticsResponse,
  LearningStats,
  LearningProgress,
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

/**
 * 统一的未实现 API 响应处理函数
 * @param defaultData 默认返回的数据
 * @param functionName 函数名称，用于控制台警告
 * @returns 标准的 AnalyticsResponse 格式
 */
function unavailableAPI<T>(defaultData: T, functionName: string): Promise<AnalyticsResponse<T>> {
  console.warn(`${functionName}: 功能开发中，返回默认数据`)
  return Promise.resolve({
    code: 200,
    success: true,
    data: defaultData,
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<T>)
}

// 获取学习统计数据 (使用后端实际端点)
export const getLearningStats = (timeRange: string = '30d') => {
  return http.get<AnalyticsResponse<LearningStats>>('/analytics/learning-stats', {
    params: { time_range: timeRange },
  })
}

// 获取用户统计数据 (使用后端实际端点)
export const getUserStats = () => {
  return http.get<AnalyticsResponse<any>>('/analytics/user/stats')
}

// 获取知识图谱 (使用后端实际端点)
export const getKnowledgeMap = (subject?: string) => {
  return http.get<AnalyticsResponse<any>>('/analytics/knowledge-map', {
    params: { subject },
  })
}

// 获取学习进度数据 (TODO: 后端待实现，暂时返回空数据)
export const getLearningProgress = (_startDate: string, _endDate: string) => {
  return unavailableAPI([] as LearningProgress[], 'getLearningProgress')
}

// 获取知识点掌握情况 (TODO: 后端待实现，使用 knowledge-map 替代)
export const getKnowledgePoints = (subject?: string) => {
  return getKnowledgeMap(subject).then((res) => ({
    ...res,
    data: res.data?.knowledge_points || [],
  }))
}

// 获取学科统计数据 (TODO: 后端待实现，暂时返回空数据)
export const getSubjectStats = (_timeRange: string = '30d') => {
  return unavailableAPI([] as SubjectStats[], 'getSubjectStats')
}

// 获取学习建议 (TODO: 后端待实现)
export const getLearningRecommendations = (_limit: number = 10) => {
  return unavailableAPI([] as LearningRecommendation[], 'getLearningRecommendations')
}

// 获取学习目标 (TODO: 后端待实现)
export const getLearningGoals = (_status?: string) => {
  return unavailableAPI([] as LearningGoal[], 'getLearningGoals')
}

// 创建学习目标 (TODO: 后端待实现)
export const createLearningGoal = (
  goal: Omit<LearningGoal, 'id' | 'createdAt' | 'currentValue'>
) => {
  const mockGoal: LearningGoal = {
    id: Date.now().toString(),
    createdAt: new Date().toISOString(),
    currentValue: 0,
    ...goal,
  }
  return unavailableAPI(mockGoal, 'createLearningGoal')
}

// 更新学习目标 (TODO: 后端待实现)
export const updateLearningGoal = (id: string, updates: Partial<LearningGoal>) => {
  const mockUpdated = { id, ...updates } as LearningGoal
  return unavailableAPI(mockUpdated, 'updateLearningGoal')
}

// 删除学习目标 (TODO: 后端待实现)
export const deleteLearningGoal = (id: string) => {
  return unavailableAPI({ deleted: true, id }, 'deleteLearningGoal')
}

// 获取错题分析 (TODO: 后端待实现)
export const getErrorAnalysis = (_subject?: string, _limit: number = 20) => {
  return unavailableAPI([] as ErrorAnalysis[], 'getErrorAnalysis')
}

// 获取学习报告 (TODO: 后端待实现)
export const getLearningReport = (_type: 'daily' | 'weekly' | 'monthly', _date?: string) => {
  return unavailableAPI({} as LearningReport, 'getLearningReport')
}

// 生成学习报告 (TODO: 后端待实现)
export const generateLearningReport = (
  type: 'daily' | 'weekly' | 'monthly',
  startDate: string,
  endDate: string
) => {
  const mockReport = {
    type,
    period: `${startDate} - ${endDate}`,
    generated: true,
    reportId: Date.now().toString(),
  }
  return unavailableAPI(mockReport, 'generateLearningReport')
}

// 获取学习时间分布 (TODO: 后端待实现)
export const getTimeDistribution = (_timeRange: string = '7d') => {
  return unavailableAPI([] as TimeDistribution[], 'getTimeDistribution')
}

// 获取学习热力图数据 (TODO: 后端待实现)
export const getStudyHeatmap = (_year: number) => {
  return unavailableAPI([] as HeatmapData[], 'getStudyHeatmap')
}

// 获取知识点网络关系 (TODO: 后端待实现)
export const getKnowledgeNetwork = (_subject?: string) => {
  return unavailableAPI(
    { nodes: [], links: [], edges: [] } as KnowledgeNetwork,
    'getKnowledgeNetwork'
  )
}

// 获取学习效率分析 (TODO: 后端待实现)
export const getEfficiencyAnalysis = (_timeRange: string = '30d') => {
  return unavailableAPI({} as EfficiencyAnalysis, 'getEfficiencyAnalysis')
}

// 获取成就列表 (TODO: 后端待实现)
export const getAchievements = (_type?: string) => {
  return unavailableAPI([] as Achievement[], 'getAchievements')
}

// 获取学习模式分析 (TODO: 后端待实现)
export const getStudyPatternAnalysis = (_timeRange: string = '30d') => {
  return unavailableAPI({} as StudyPatternAnalysis, 'getStudyPatternAnalysis')
}

// 获取学习排行榜 (TODO: 后端待实现)
export const getLeaderboard = (
  _type: 'study_time' | 'homework_count' | 'avg_score' | 'streak',
  _period: string = 'week'
) => {
  return unavailableAPI(
    [] as {
      rank: number
      userId: string
      username: string
      avatar?: string
      value: number
      improvement: number
    }[],
    'getLeaderboard'
  )
}

// 获取个人学习洞察 (TODO: 后端待实现)
export const getPersonalInsights = () => {
  return unavailableAPI(
    {
      strengths: [],
      weaknesses: [],
      trends: [],
      suggestions: [],
    },
    'getPersonalInsights'
  )
}

// 导出学习数据 (TODO: 后端待实现)
export const exportLearningData = (format: 'csv' | 'json' | 'pdf', timeRange: string = '30d') => {
  const mockExport = {
    format,
    timeRange,
    downloadUrl: '#',
    exportId: Date.now().toString(),
  }
  return unavailableAPI(mockExport, 'exportLearningData')
}

// 获取学习日历数据 (TODO: 后端待实现)
export const getStudyCalendar = (_year: number, _month: number) => {
  return unavailableAPI(
    [] as {
      date: string
      studyTime: number
      homeworkCount: number
      events: {
        type: 'homework' | 'goal' | 'achievement'
        title: string
        time?: string
      }[]
    }[],
    'getStudyCalendar'
  )
}

// 设置学习提醒 (TODO: 后端待实现)
export const setStudyReminder = (reminder: {
  type: 'daily' | 'weekly' | 'goal'
  time: string
  message: string
  enabled: boolean
}) => {
  const mockReminder = {
    id: Date.now().toString(),
    ...reminder,
  }
  return unavailableAPI(mockReminder, 'setStudyReminder')
}

// 获取学习提醒设置 (TODO: 后端待实现)
export const getStudyReminders = () => {
  return unavailableAPI(
    [] as {
      id: string
      type: 'daily' | 'weekly' | 'goal'
      time: string
      message: string
      enabled: boolean
    }[],
    'getStudyReminders'
  )
}

// 更新学习提醒 (TODO: 后端待实现)
export const updateStudyReminder = (
  id: string,
  updates: {
    time?: string
    message?: string
    enabled?: boolean
  }
) => {
  const mockUpdated = { id, ...updates }
  return unavailableAPI(mockUpdated, 'updateStudyReminder')
}

// 删除学习提醒 (TODO: 后端待实现)
export const deleteStudyReminder = (id: string) => {
  return unavailableAPI({ deleted: true, id }, 'deleteStudyReminder')
}
