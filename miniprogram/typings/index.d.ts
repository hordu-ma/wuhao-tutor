// typings/index.d.ts - 全局类型声明文件

// 用户角色类型
declare type UserRole = 'student' | 'parent' | 'teacher'

// 用户信息类型
declare interface UserInfo {
  id: string
  nickName: string
  avatarUrl: string
  gender: number
  country: string
  province: string
  city: string
  language: string
  openid: string
  unionid?: string
  role: UserRole
  profile?: UserProfile
}

// 用户详细信息
declare interface UserProfile {
  realName?: string
  phone?: string
  email?: string
  school?: string
  grade?: string
  className?: string
  studentId?: string
  parentId?: string
  teacherId?: string
  subjects?: string[]
}

// 应用实例类型
declare interface IAppOption {
  globalData: {
    userInfo?: UserInfo
    token?: string
    role?: UserRole
    systemInfo?: WechatMiniprogram.SystemInfo
  }
  userInfoReadyCallback?: (userInfo: WechatMiniprogram.UserInfo) => void
  initApp(): void
  checkUpdate(): void
  initUserInfo(): void
  setUserInfo(userInfo: UserInfo, token: string): void
  clearUserInfo(): void
  getUserInfo(): UserInfo | undefined
  getToken(): string | undefined
  getUserRole(): UserRole | undefined
  isLoggedIn(): boolean
}

// API响应基础类型
declare interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
  }
}

// 分页响应类型
declare interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination?: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

// 作业相关类型
declare interface HomeworkInfo {
  id: string
  title: string
  subject: string
  description: string
  dueDate: string
  status: HomeworkStatus
  submittedAt?: string
  score?: number
  feedback?: string
  attachments?: AttachmentInfo[]
  questions?: QuestionInfo[]
}

declare type HomeworkStatus = 'pending' | 'submitted' | 'graded' | 'overdue'

// 问题类型
declare interface QuestionInfo {
  id: string
  content: string
  type: QuestionType
  options?: string[]
  correctAnswer?: string
  userAnswer?: string
  score?: number
  analysis?: string
}

declare type QuestionType = 'choice' | 'fill' | 'essay' | 'calculation'

// 附件类型
declare interface AttachmentInfo {
  id: string
  name: string
  url: string
  type: AttachmentType
  size: number
  uploadedAt: string
}

declare type AttachmentType = 'image' | 'document' | 'audio' | 'video'

// 聊天相关类型
declare interface ChatSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messages: ChatMessage[]
  status: ChatStatus
}

declare interface ChatMessage {
  id: string
  content: string
  type: MessageType
  sender: MessageSender
  timestamp: string
  attachments?: AttachmentInfo[]
}

declare type MessageType = 'text' | 'image' | 'voice' | 'system'
declare type MessageSender = 'user' | 'ai' | 'system'
declare type ChatStatus = 'active' | 'ended' | 'archived'

// 学情分析类型
declare interface LearningReport {
  id: string
  studentId: string
  subject: string
  period: ReportPeriod
  generatedAt: string
  summary: ReportSummary
  details: ReportDetail[]
}

declare interface ReportSummary {
  totalScore: number
  averageScore: number
  improvement: number
  rank?: number
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
}

declare interface ReportDetail {
  topic: string
  knowledgePoints: KnowledgePoint[]
  performance: Performance
}

declare interface KnowledgePoint {
  name: string
  masteryLevel: number // 0-100
  practiceCount: number
  correctRate: number
}

declare interface Performance {
  score: number
  accuracy: number
  speed: number
  consistency: number
}

declare type ReportPeriod = 'weekly' | 'monthly' | 'semester' | 'custom'

// 通知类型
declare interface NotificationInfo {
  id: string
  title: string
  content: string
  type: NotificationType
  sender: string
  recipient: string
  isRead: boolean
  createdAt: string
  data?: any
}

declare type NotificationType = 'homework' | 'grade' | 'announcement' | 'reminder' | 'system'

// 配置类型
declare interface AppConfig {
  apiBaseUrl: string
  ossBaseUrl: string
  environment: 'development' | 'staging' | 'production'
  version: string
  debug: boolean
  features: {
    voiceInput: boolean
    imageUpload: boolean
    offlineMode: boolean
    push: boolean
  }
}

// 页面参数类型
declare interface PageQuery {
  [key: string]: string | undefined
}

// 组件属性类型
declare interface ComponentProps {
  [key: string]: any
}

// 存储键名常量
declare const enum StorageKeys {
  USER_INFO = 'user_info',
  TOKEN = 'token',
  ROLE = 'user_role',
  SETTINGS = 'app_settings',
  CACHE_PREFIX = 'cache_'
}

// 事件类型
declare interface CustomEvent<T = any> {
  type: string
  detail: T
  timeStamp: number
}

// 错误类型
declare interface AppError {
  code: string
  message: string
  details?: any
  timestamp: string
}

// 上传文件类型
declare interface UploadFile {
  path: string
  name: string
  type: string
  size: number
}

// 工具函数类型
declare interface Utils {
  formatDate: (date: Date | string, format?: string) => string
  debounce: <T extends (...args: any[]) => any>(fn: T, delay: number) => T
  throttle: <T extends (...args: any[]) => any>(fn: T, delay: number) => T
  showToast: (title: string, icon?: 'success' | 'error' | 'loading' | 'none') => void
  showModal: (title: string, content: string) => Promise<boolean>
  navigateTo: (url: string, params?: any) => void
  redirectTo: (url: string, params?: any) => void
  switchTab: (url: string) => void
}

// 扩展全局声明
declare global {
  const __DEV__: boolean
  const __VERSION__: string

  interface Wx {
    utils?: Utils
  }

  function getApp(): WechatMiniprogram.App.Instance<IAppOption>
}
