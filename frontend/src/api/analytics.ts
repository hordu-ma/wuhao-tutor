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
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as LearningProgress[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<LearningProgress[]>)
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
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as SubjectStats[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<SubjectStats[]>)
}

// 获取学习建议 (TODO: 后端待实现)
export const getLearningRecommendations = (_limit: number = 10) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as LearningRecommendation[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<LearningRecommendation[]>)
}

// 获取学习目标 (TODO: 后端待实现)
export const getLearningGoals = (_status?: string) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as LearningGoal[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<LearningGoal[]>)
}

// 创建学习目标 (TODO: 后端待实现)
export const createLearningGoal = (
  _goal: Omit<LearningGoal, 'id' | 'createdAt' | 'currentValue'>
) => {
  return Promise.reject(new Error('功能开发中'))
}

// 更新学习目标 (TODO: 后端待实现)
export const updateLearningGoal = (_id: string, _updates: Partial<LearningGoal>) => {
  return Promise.reject(new Error('功能开发中'))
}

// 删除学习目标 (TODO: 后端待实现)
export const deleteLearningGoal = (_id: string) => {
  return Promise.reject(new Error('功能开发中'))
}

// 获取错题分析 (TODO: 后端待实现)
export const getErrorAnalysis = (_subject?: string, _limit: number = 20) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as ErrorAnalysis[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<ErrorAnalysis[]>)
}

// 获取学习报告 (TODO: 后端待实现)
export const getLearningReport = (_type: 'daily' | 'weekly' | 'monthly', _date?: string) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: {} as LearningReport,
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<LearningReport>)
}

// 生成学习报告 (TODO: 后端待实现)
export const generateLearningReport = (
  _type: 'daily' | 'weekly' | 'monthly',
  _startDate: string,
  _endDate: string
) => {
  return Promise.reject(new Error('功能开发中'))
}

// 获取学习时间分布 (TODO: 后端待实现)
export const getTimeDistribution = (_timeRange: string = '7d') => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as TimeDistribution[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<TimeDistribution[]>)
}

// 获取学习热力图数据 (TODO: 后端待实现)
export const getStudyHeatmap = (_year: number) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as HeatmapData[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<HeatmapData[]>)
}

// 获取知识点网络关系 (TODO: 后端待实现)
export const getKnowledgeNetwork = (_subject?: string) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: { nodes: [], links: [], edges: [] } as KnowledgeNetwork,
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<KnowledgeNetwork>)
}

// 获取学习效率分析 (TODO: 后端待实现)
export const getEfficiencyAnalysis = (_timeRange: string = '30d') => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: {} as EfficiencyAnalysis,
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<EfficiencyAnalysis>)
}

// 获取成就列表 (TODO: 后端待实现)
export const getAchievements = (_type?: string) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [] as Achievement[],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<Achievement[]>)
}

// 获取学习模式分析 (TODO: 后端待实现)
export const getStudyPatternAnalysis = (_timeRange: string = '30d') => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: {} as StudyPatternAnalysis,
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<StudyPatternAnalysis>)
}

// 获取学习排行榜 (TODO: 后端待实现)
export const getLeaderboard = (
  _type: 'study_time' | 'homework_count' | 'avg_score' | 'streak',
  _period: string = 'week'
) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<
    {
      rank: number
      userId: string
      username: string
      avatar?: string
      value: number
      improvement: number
    }[]
  >)
}

// 获取个人学习洞察 (TODO: 后端待实现)
export const getPersonalInsights = () => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: {
      strengths: [],
      weaknesses: [],
      trends: [],
      suggestions: [],
    },
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<{
    strengths: string[]
    weaknesses: string[]
    trends: string[]
    suggestions: string[]
  }>)
}

// 导出学习数据 (TODO: 后端待实现)
export const exportLearningData = (_format: 'csv' | 'json' | 'pdf', _timeRange: string = '30d') => {
  return Promise.reject(new Error('功能开发中'))
}

// 获取学习日历数据 (TODO: 后端待实现)
export const getStudyCalendar = (_year: number, _month: number) => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<
    {
      date: string
      studyTime: number
      homeworkCount: number
      events: {
        type: 'homework' | 'goal' | 'achievement'
        title: string
        time?: string
      }[]
    }[]
  >)
}

// 设置学习提醒 (TODO: 后端待实现)
export const setStudyReminder = (_reminder: {
  type: 'daily' | 'weekly' | 'goal'
  time: string
  message: string
  enabled: boolean
}) => {
  return Promise.reject(new Error('功能开发中'))
}

// 获取学习提醒设置 (TODO: 后端待实现)
export const getStudyReminders = () => {
  return Promise.resolve({
    code: 200,
    success: true,
    data: [],
    message: '功能开发中',
    timestamp: new Date().toISOString(),
  } as AnalyticsResponse<
    {
      id: string
      type: 'daily' | 'weekly' | 'goal'
      time: string
      message: string
      enabled: boolean
    }[]
  >)
}

// 更新学习提醒 (TODO: 后端待实现)
export const updateStudyReminder = (
  _id: string,
  _updates: {
    time?: string
    message?: string
    enabled?: boolean
  }
) => {
  return Promise.reject(new Error('功能开发中'))
}

// 删除学习提醒 (TODO: 后端待实现)
export const deleteStudyReminder = (_id: string) => {
  return Promise.reject(new Error('功能开发中'))
}
