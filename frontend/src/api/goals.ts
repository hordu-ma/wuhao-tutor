/**
 * 每日目标相关API
 */

import http from '@/api/http'

// 每日目标数据类型
export interface DailyGoal {
  id: number
  title: string
  type: 'review_mistakes' | 'questions' | 'study_time' | 'record_mistakes'
  target: number
  current: number
  completed: boolean
  progress: number
  action_link?: string
  description?: string
}

/**
 * 目标API类
 */
export class GoalAPI {
  /**
   * 获取每日目标
   */
  async getDailyGoals(): Promise<DailyGoal[]> {
    const response = await http.get('/goals/daily-goals', {
      skipAuth: true, // 开发环境跳过认证
    })
    return response
  }
}

// 导出实例
export const goalAPI = new GoalAPI()
export default goalAPI
