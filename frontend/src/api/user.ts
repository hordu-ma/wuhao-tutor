/**
 * 用户相关API
 */

import http from '@/api/http'

// 用户活动类型
export interface UserActivity {
  id: string
  type: 'question' | 'homework' | 'study'
  title: string
  time: string
  status: string
}

// 用户统计信息
export interface UserStats {
  totalPoints: number
  studyDays: number
  questions: number
  pendingHomework: number
}

/**
 * 用户API类
 */
export class UserAPI {
  /**
   * 获取用户最近活动
   */
  async getActivities(limit = 10): Promise<UserActivity[]> {
    const response = await http.get('/user/activities', {
      params: { limit },
      skipAuth: true, // 开发环境跳过认证
    })
    return response
  }

  /**
   * 获取用户统计信息
   */
  async getStats(): Promise<UserStats> {
    const response = await http.get('/user/stats', {
      skipAuth: true, // 开发环境跳过认证
    })
    return response
  }
}

// 导出实例
export const userAPI = new UserAPI()
export default userAPI
