/**
 * 错题手册类型定义
 */

// 错题来源类型
export enum MistakeSource {
  HOMEWORK = 'homework',
  LEARNING = 'learning',
  MANUAL = 'manual',
}

// 掌握状态
export enum MasteryStatus {
  NOT_MASTERED = 'not_mastered', // 未掌握
  REVIEWING = 'reviewing', // 复习中
  MASTERED = 'mastered', // 已掌握
}

// 错题列表项
export interface MistakeListItem {
  id: string
  title: string
  subject: string
  difficulty_level?: number
  source: MistakeSource
  source_id?: string
  mastery_status: MasteryStatus
  correct_count: number
  total_reviews: number
  next_review_date?: string
  created_at: string
  knowledge_points?: string[]
}

// 错题列表响应
export interface MistakeListResponse {
  items: MistakeListItem[]
  total: number
  page: number
  page_size: number
}

// 错题详情
export interface MistakeDetail {
  id: string
  title: string
  description: string
  subject: string
  difficulty_level?: number
  source: MistakeSource
  source_id?: string
  question_content: string
  student_answer?: string
  correct_answer?: string
  explanation?: string
  knowledge_points?: string[]
  mastery_status: MasteryStatus
  correct_count: number
  total_reviews: number
  next_review_date?: string
  created_at: string
  updated_at: string
  image_urls?: string[]
}

// 今日复习任务
export interface TodayReviewTask {
  id: string
  mistake_id: string
  title: string
  subject: string
  review_round: number
  due_date: string
  question_content: string
  image_urls?: string[]
}

// 今日复习响应
export interface TodayReviewResponse {
  tasks: TodayReviewTask[]
  total_count: number
  completed_count: number
}

// 复习完成请求
export interface ReviewCompleteRequest {
  mistake_id: string
  is_correct: boolean
  time_spent?: number
  notes?: string
}

// 复习完成响应
export interface ReviewCompleteResponse {
  success: boolean
  message: string
  mastery_status: MasteryStatus
  next_review_date?: string
}

// 错题统计
export interface MistakeStatistics {
  total_mistakes: number
  not_mastered: number
  reviewing: number
  mastered: number
  by_subject: Record<string, number>
  by_difficulty: Record<string, number>
  review_streak_days: number
  this_week_reviews: number
}
