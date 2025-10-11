/**
 * 错题本相关类型定义
 */

export interface ErrorQuestion {
  id: string
  user_id: string
  subject: string
  question_content: string
  student_answer?: string
  correct_answer?: string
  error_type: string
  error_subcategory?: string
  knowledge_points: string[]
  difficulty_level: number
  source_type: 'homework' | 'manual'
  source_id?: string
  mastery_status: 'learning' | 'reviewing' | 'mastered'
  review_count: number
  correct_count: number
  last_review_at?: string
  next_review_at?: string
  is_starred: boolean
  tags: string[]
  created_at: string
  updated_at: string
  
  // 计算属性
  mastery_rate: number
  is_overdue: boolean
  overdue_days: number
}

export interface ErrorQuestionCreate {
  subject: string
  question_content: string
  student_answer?: string
  correct_answer?: string
  error_type?: string
  error_subcategory?: string
  knowledge_points?: string[]
  difficulty_level?: number
  source_type?: 'homework' | 'manual'
  source_id?: string
  is_starred?: boolean
  tags?: string[]
}

export interface ErrorQuestionUpdate {
  subject?: string
  question_content?: string
  student_answer?: string
  correct_answer?: string
  error_type?: string
  error_subcategory?: string
  knowledge_points?: string[]
  difficulty_level?: number
  mastery_status?: 'learning' | 'reviewing' | 'mastered'
  is_starred?: boolean
  tags?: string[]
}

export interface ReviewRecord {
  id: string
  error_question_id: string
  user_id: string
  review_result: 'correct' | 'incorrect' | 'partial'
  score: number
  time_spent?: number
  student_answer?: string
  notes?: string
  reviewed_at: string
  next_review_at?: string
  performance_score: number
  created_at: string
  updated_at: string
}

export interface ReviewRecordCreate {
  review_result: 'correct' | 'incorrect' | 'partial'
  score: number
  time_spent?: number
  student_answer?: string
  notes?: string
}

export interface ErrorQuestionListResponse {
  items: ErrorQuestion[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface ErrorBookStats {
  overview: {
    total_errors: number
    weekly_new: number
    mastery_rate: number
    mastered: number
    reviewing: number
    learning: number
  }
  by_subject: Array<{
    subject: string
    count: number
    percentage: number
  }>
  by_category: Array<{
    category: string
    count: number
    percentage: number
  }>
}

export interface WeakAreaRecommendation {
  knowledge_point: string
  error_count: number
  mastery_rate: number
  suggestion: string
}

export interface ReviewRecommendation {
  error_question_id: string
  question_preview: string
  subject: string
  overdue_days: number
  importance_score: number
  difficulty_level: number
}

export interface DailyReviewPlan {
  target_count: number
  estimated_time: number
  subjects: string[]
  priority_items: string[]
}

export interface ReviewRecommendations {
  urgent_reviews: ReviewRecommendation[]
  daily_plan: DailyReviewPlan
  weak_areas: WeakAreaRecommendation[]
}

export interface ErrorAnalysisResponse {
  error_type: string
  error_subcategory?: string
  confidence: number
  analysis: string
  suggestions: string[]
  knowledge_points: string[]
}