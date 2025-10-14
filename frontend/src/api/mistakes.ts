/**
 * 错题手册 API
 */

import http from './http'
import type {
  MistakeListResponse,
  MistakeDetail,
  TodayReviewResponse,
  ReviewCompleteRequest,
  ReviewCompleteResponse,
  MistakeStatistics,
} from '@/types/mistake'

/**
 * 获取今日复习任务
 */
/**
 * 获取今日复习任务
 */
export const getTodayReviewTasks = (): Promise<TodayReviewResponse> => {
  return http.get<TodayReviewResponse>('/mistakes/today-review')
}

/**
 * 获取错题列表
 */
export function getMistakeList(params?: {
  page?: number
  page_size?: number
  subject?: string
  mastery_status?: string
  search?: string
}): Promise<MistakeListResponse> {
  return http.get('/mistakes', { params })
}

/**
 * 获取错题详情
 */
export function getMistakeDetail(id: string): Promise<MistakeDetail> {
  return http.get(`/mistakes/${id}`)
}

/**
 * 完成复习
 */
export const completeReview = (data: ReviewCompleteRequest): Promise<ReviewCompleteResponse> => {
  return http.post<ReviewCompleteResponse>(`/mistakes/${data.mistake_id}/review`, data)
}

/**
 * 获取错题统计
 */
export function getMistakeStatistics(): Promise<MistakeStatistics> {
  return http.get('/mistakes/statistics')
}

/**
 * 手动添加错题
 */
export function createMistake(data: {
  title: string
  question_content: string
  student_answer?: string
  correct_answer?: string
  explanation?: string
  subject: string
  difficulty_level?: number
  knowledge_points?: string[]
  image_urls?: string[]
}): Promise<MistakeDetail> {
  return http.post('/mistakes', data)
}

/**
 * 删除错题
 */
export function deleteMistake(id: string): Promise<void> {
  return http.delete(`/mistakes/${id}`)
}

export default {
  getTodayReviewTasks,
  getMistakeList,
  getMistakeDetail,
  completeReview,
  getMistakeStatistics,
  createMistake,
  deleteMistake,
}
