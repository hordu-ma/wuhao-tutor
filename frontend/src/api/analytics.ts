/**
 * 学情分析 API 接口
 */

import http from './http'
import type {
  AnalyticsResponse,
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

// 获取学习统计数据
export const getLearningStats = (timeRange: string = '30d') => {
  return http.get<AnalyticsResponse<LearningStats>>('/analytics/stats', {
    params: { timeRange },
  })
}

// 获取学习进度数据
export const getLearningProgress = (startDate: string, endDate: string) => {
  return http.get<AnalyticsResponse<LearningProgress[]>>('/analytics/progress', {
    params: { startDate, endDate },
  })
}

// 获取知识点掌握情况
export const getKnowledgePoints = (subject?: string) => {
  return http.get<AnalyticsResponse<KnowledgePoint[]>>('/analytics/knowledge-points', {
    params: { subject },
  })
}

// 获取学科统计数据
export const getSubjectStats = (timeRange: string = '30d') => {
  return http.get<AnalyticsResponse<SubjectStats[]>>('/analytics/subjects', {
    params: { timeRange },
  })
}

// 获取学习建议
export const getLearningRecommendations = (limit: number = 10) => {
  return http.get<AnalyticsResponse<LearningRecommendation[]>>('/analytics/recommendations', {
    params: { limit },
  })
}

// 获取学习目标
export const getLearningGoals = (status?: string) => {
  return http.get<AnalyticsResponse<LearningGoal[]>>('/analytics/goals', {
    params: { status },
  })
}

// 创建学习目标
export const createLearningGoal = (
  goal: Omit<LearningGoal, 'id' | 'createdAt' | 'currentValue'>
) => {
  return http.post<AnalyticsResponse<LearningGoal>>('/analytics/goals', goal)
}

// 更新学习目标
export const updateLearningGoal = (id: string, updates: Partial<LearningGoal>) => {
  return http.put<AnalyticsResponse<LearningGoal>>(`/analytics/goals/${id}`, updates)
}

// 删除学习目标
export const deleteLearningGoal = (id: string) => {
  return http.delete<AnalyticsResponse<void>>(`/analytics/goals/${id}`)
}

// 获取错题分析
export const getErrorAnalysis = (subject?: string, limit: number = 20) => {
  return http.get<AnalyticsResponse<ErrorAnalysis[]>>('/analytics/errors', {
    params: { subject, limit },
  })
}

// 获取学习报告
export const getLearningReport = (type: 'daily' | 'weekly' | 'monthly', date?: string) => {
  return http.get<AnalyticsResponse<LearningReport>>('/analytics/report', {
    params: { type, date },
  })
}

// 生成学习报告
export const generateLearningReport = (
  type: 'daily' | 'weekly' | 'monthly',
  startDate: string,
  endDate: string
) => {
  return http.post<AnalyticsResponse<LearningReport>>('/analytics/report/generate', {
    type,
    startDate,
    endDate,
  })
}

// 获取学习时间分布
export const getTimeDistribution = (timeRange: string = '7d') => {
  return http.get<AnalyticsResponse<TimeDistribution[]>>('/analytics/time-distribution', {
    params: { timeRange },
  })
}

// 获取学习热力图数据
export const getStudyHeatmap = (year: number) => {
  return http.get<AnalyticsResponse<HeatmapData[]>>('/analytics/heatmap', {
    params: { year },
  })
}

// 获取知识点网络关系
export const getKnowledgeNetwork = (subject?: string) => {
  return http.get<AnalyticsResponse<KnowledgeNetwork>>('/analytics/knowledge-network', {
    params: { subject },
  })
}

// 获取学习效率分析
export const getEfficiencyAnalysis = (timeRange: string = '30d') => {
  return http.get<AnalyticsResponse<EfficiencyAnalysis>>('/analytics/efficiency', {
    params: { timeRange },
  })
}

// 获取成就列表
export const getAchievements = (type?: string) => {
  return http.get<AnalyticsResponse<Achievement[]>>('/analytics/achievements', {
    params: { type },
  })
}

// 获取学习模式分析
export const getStudyPatternAnalysis = (timeRange: string = '30d') => {
  return http.get<AnalyticsResponse<StudyPatternAnalysis>>('/analytics/study-pattern', {
    params: { timeRange },
  })
}

// 获取学习排行榜
export const getLeaderboard = (
  type: 'study_time' | 'homework_count' | 'avg_score' | 'streak',
  period: string = 'week'
) => {
  return http.get<
    AnalyticsResponse<
      {
        rank: number
        userId: string
        username: string
        avatar?: string
        value: number
        improvement: number
      }[]
    >
  >('/analytics/leaderboard', {
    params: { type, period },
  })
}

// 获取个人学习洞察
export const getPersonalInsights = () => {
  return http.get<
    AnalyticsResponse<{
      strengths: string[]
      weaknesses: string[]
      trends: string[]
      suggestions: string[]
    }>
  >('/analytics/insights')
}

// 导出学习数据
export const exportLearningData = (format: 'csv' | 'json' | 'pdf', timeRange: string = '30d') => {
  return http.get(`/analytics/export`, {
    params: { format, timeRange },
    responseType: 'blob',
  })
}

// 获取学习日历数据
export const getStudyCalendar = (year: number, month: number) => {
  return http.get<
    AnalyticsResponse<
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
    >
  >('/analytics/calendar', {
    params: { year, month },
  })
}

// 设置学习提醒
export const setStudyReminder = (reminder: {
  type: 'daily' | 'weekly' | 'goal'
  time: string
  message: string
  enabled: boolean
}) => {
  return http.post<AnalyticsResponse<void>>('/analytics/reminders', reminder)
}

// 获取学习提醒设置
export const getStudyReminders = () => {
  return http.get<
    AnalyticsResponse<
      {
        id: string
        type: 'daily' | 'weekly' | 'goal'
        time: string
        message: string
        enabled: boolean
        createdAt: string
      }[]
    >
  >('/analytics/reminders')
}

// 更新学习提醒
export const updateStudyReminder = (
  id: string,
  updates: {
    time?: string
    message?: string
    enabled?: boolean
  }
) => {
  return http.put<AnalyticsResponse<void>>(`/analytics/reminders/${id}`, updates)
}

// 删除学习提醒
export const deleteStudyReminder = (id: string) => {
  return http.delete<AnalyticsResponse<void>>(`/analytics/reminders/${id}`)
}
