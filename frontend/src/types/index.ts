/**
 * 全局类型定义
 * 定义前端应用中使用的所有TypeScript类型
 */

// ============= 基础类型 =============

/** 通用响应格式 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error_code?: string
  timestamp?: string
}

/** 分页参数 */
export interface PaginationParams {
  page?: number
  size?: number
  total?: number
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

/** 通用ID类型 */
export type ID = string | number

/** 状态类型 */
export type Status = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'

// ============= 用户认证相关 =============

/** 用户信息 */
export interface User {
  id: ID
  username: string
  email?: string
  nickname?: string
  avatar?: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 用户角色 */
export type UserRole = 'student' | 'teacher' | 'admin'

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

/** 登录响应 */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

/** 注册请求 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
  nickname?: string
}

// ============= 作业批改相关 =============

/** 作业类型 */
export type HomeworkType = 'math' | 'chinese' | 'english' | 'science' | 'other'

/** 作业难度 */
export type HomeworkDifficulty = 'easy' | 'medium' | 'hard'

/** 批改状态 */
export type GradingStatus = 'pending' | 'grading' | 'completed' | 'failed'

/** 作业提交 */
export interface HomeworkSubmission {
  id: ID
  title: string
  type: HomeworkType
  difficulty: HomeworkDifficulty
  content?: string
  file_url?: string
  file_name?: string
  file_type?: string
  status: GradingStatus
  submitted_at: string
  graded_at?: string
  user_id: ID
}

/** 批改结果 */
export interface GradingResult {
  id: ID
  submission_id: ID
  score?: number
  max_score?: number
  feedback: string
  detailed_analysis: GradingAnalysis[]
  suggestions: string[]
  strengths: string[]
  weaknesses: string[]
  created_at: string
  grader_type: 'ai' | 'teacher'
}

/** 详细分析 */
export interface GradingAnalysis {
  question_number?: number
  question_text?: string
  student_answer?: string
  correct_answer?: string
  is_correct: boolean
  points_earned: number
  points_total: number
  feedback: string
  error_type?: string
}

/** 作业批改请求 */
export interface GradingRequest {
  title: string
  type: HomeworkType
  difficulty: HomeworkDifficulty
  content?: string
  file?: File
  instructions?: string
}

// ============= 学习问答相关 =============

/** 问题类型 */
export type QuestionType = 'text' | 'image' | 'voice'

/** 问答会话 */
export interface LearningSession {
  id: ID
  title: string
  subject?: string
  created_at: string
  updated_at: string
  message_count: number
  user_id: ID
}

/** 问答消息 */
export interface ChatMessage {
  id: ID
  session_id: ID
  content: string
  message_type: QuestionType
  role: 'user' | 'assistant'
  attachments?: MessageAttachment[]
  created_at: string
  is_helpful?: boolean
}

/** 消息附件 */
export interface MessageAttachment {
  id: ID
  filename: string
  file_type: string
  file_size: number
  file_url: string
  thumbnail_url?: string
}

/** 问答请求 */
export interface QuestionRequest {
  session_id?: ID
  content: string
  message_type: QuestionType
  file?: File
  context?: string
}

/** 问答响应 */
export interface QuestionResponse {
  answer: string
  session_id: ID
  message_id: ID
  confidence?: number
  sources?: string[]
  related_questions?: string[]
}

// ============= 文件管理相关 =============

/** 文件信息 */
export interface FileInfo {
  id: ID
  filename: string
  original_name: string
  file_type: string
  file_size: number
  mime_type: string
  file_url: string
  thumbnail_url?: string
  upload_time: string
  user_id: ID
}

/** 文件上传请求 */
export interface FileUploadRequest {
  file: File
  category?: string
  description?: string
}

// ============= 学情分析相关 =============

/** 学习统计 */
export interface LearningStats {
  total_submissions: number
  completed_submissions: number
  average_score: number
  total_questions: number
  total_study_time: number
  active_days: number
  current_streak: number
  subjects: SubjectStats[]
}

/** 学科统计 */
export interface SubjectStats {
  subject: string
  count: number
  average_score: number
  improvement_rate: number
  last_activity: string
}

/** 学习进度 */
export interface LearningProgress {
  date: string
  submissions: number
  questions: number
  study_time: number
  average_score: number
}

/** 错题分析 */
export interface ErrorAnalysis {
  error_type: string
  count: number
  percentage: number
  trend: 'increasing' | 'decreasing' | 'stable'
  suggestions: string[]
}

// ============= 系统配置相关 =============

/** 应用配置 */
export interface AppConfig {
  app_name: string
  version: string
  api_base_url: string
  file_upload_max_size: number
  supported_file_types: string[]
  features: FeatureFlags
}

/** 功能开关 */
export interface FeatureFlags {
  homework_grading: boolean
  learning_qa: boolean
  file_upload: boolean
  voice_input: boolean
  image_recognition: boolean
  progress_analytics: boolean
}

// ============= 组件props相关 =============

/** 加载状态 */
export interface LoadingState {
  loading: boolean
  error?: string
  empty?: boolean
}

/** 表格列配置 */
export interface TableColumn {
  key: string
  title: string
  dataIndex: string
  width?: number | string
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, record: any, index: number) => any
}

/** 表单字段 */
export interface FormField {
  name: string
  label: string
  type: 'input' | 'textarea' | 'select' | 'upload' | 'radio' | 'checkbox'
  placeholder?: string
  required?: boolean
  options?: { label: string; value: any }[]
  rules?: any[]
}

// ============= 路由相关 =============

/** 路由元信息 */
export interface RouteMeta {
  title?: string
  icon?: string
  requiresAuth?: boolean
  roles?: UserRole[]
  hidden?: boolean
  keepAlive?: boolean
}

/** 菜单项 */
export interface MenuItem {
  id: string
  title: string
  icon?: string
  path?: string
  children?: MenuItem[]
  meta?: RouteMeta
}

// ============= 工具类型 =============

/** 可选字段 */
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/** 必需字段 */
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

/** 深度可选 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/** 键值对 */
export type KeyValuePair<T = any> = Record<string, T>

/** 时间范围 */
export interface DateRange {
  start: string
  end: string
}

/** 排序参数 */
export interface SortParams {
  field: string
  order: 'asc' | 'desc'
}

/** 筛选参数 */
export interface FilterParams {
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in'
  value: any
}
