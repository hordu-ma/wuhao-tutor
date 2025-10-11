/**
 * 错题本相关API接口
 */

import { http } from '@/utils/http'
import type { 
  ErrorQuestion, 
  ErrorQuestionListResponse, 
  ErrorBookStats,
  ErrorQuestionCreate,
  ReviewRecordCreate,
  ReviewRecord
} from '@/types/errorBook'

interface ErrorQuestionQuery {
  subject?: string
  status?: string
  category?: string
  difficulty?: number
  sort?: string
  order?: string
  page?: number
  limit?: number
}

export const errorBookApi = {
  /**
   * 获取错题列表
   */
  async getErrorQuestions(params?: ErrorQuestionQuery): Promise<ErrorQuestionListResponse> {
    const response = await http.get('/api/v1/error-book', { params })
    return response.data
  },

  /**
   * 获取错题详情
   */
  async getErrorQuestion(id: string): Promise<ErrorQuestion> {
    const response = await http.get(`/api/v1/error-book/${id}`)
    return response.data
  },

  /**
   * 创建错题
   */
  async createErrorQuestion(data: ErrorQuestionCreate): Promise<ErrorQuestion> {
    const response = await http.post('/api/v1/error-book', data)
    return response.data
  },

  /**
   * 更新错题
   */
  async updateErrorQuestion(id: string, data: Partial<ErrorQuestionCreate>): Promise<ErrorQuestion> {
    const response = await http.put(`/api/v1/error-book/${id}`, data)
    return response.data
  },

  /**
   * 删除错题
   */
  async deleteErrorQuestion(id: string): Promise<void> {
    await http.delete(`/api/v1/error-book/${id}`)
  },

  /**
   * 记录复习
   */
  async createReviewRecord(errorQuestionId: string, data: ReviewRecordCreate): Promise<ReviewRecord> {
    const response = await http.post(`/api/v1/error-book/${errorQuestionId}/review`, data)
    return response.data
  },

  /**
   * 获取错题本统计
   */
  async getStats(): Promise<ErrorBookStats> {
    const response = await http.get('/api/v1/error-book/stats')
    return response.data
  },

  /**
   * 获取复习推荐
   */
  async getReviewRecommendations(limit?: number) {
    const response = await http.get('/api/v1/error-book/recommendations', {
      params: { limit }
    })
    return response.data
  },

  /**
   * 批量更新掌握状态
   */
  async batchUpdateStatus(errorQuestionIds: string[], status: string) {
    const response = await http.post('/api/v1/error-book/batch', {
      error_question_ids: errorQuestionIds,
      action: 'update_status',
      data: { status }
    })
    return response.data
  },

  /**
   * AI错题分析
   */
  async analyzeError(data: {
    question_content: string
    student_answer: string
    correct_answer?: string
    subject?: string
  }) {
    const response = await http.post('/api/v1/error-book/analyze', data)
    return response.data
  }
}