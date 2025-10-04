/**
 * 学习问答 API 客户端
 * 提供与学习问答系统相关的所有API方法
 */

import http from './http'
import type {
  AskQuestionRequest,
  AskQuestionResponse,
  CreateSessionRequest,
  UpdateSessionRequest,
  FeedbackRequest,
  SessionListQuery,
  QuestionHistoryQuery,
  SessionListResponse,
  QuestionHistoryResponse,
  ChatSession,
  LearningAnalytics,
  RecommendationResponse,
} from '@/types/learning'

const API_PREFIX = '/learning'

export class LearningAPI {
  /**
   * 向AI助手提问
   */
  static async askQuestion(request: AskQuestionRequest): Promise<AskQuestionResponse> {
    return http.post<AskQuestionResponse>(`${API_PREFIX}/ask`, request)
  }

  /**
   * 创建新的学习会话
   */
  static async createSession(request: CreateSessionRequest): Promise<ChatSession> {
    return http.post<ChatSession>(`${API_PREFIX}/sessions`, request)
  }

  /**
   * 获取会话列表
   */
  static async getSessionList(query: SessionListQuery = {}): Promise<SessionListResponse> {
    return http.get<SessionListResponse>(`${API_PREFIX}/sessions`, {
      params: query,
    })
  }

  /**
   * 获取单个会话详情
   */
  static async getSession(sessionId: string): Promise<ChatSession> {
    return http.get<ChatSession>(`${API_PREFIX}/sessions/${sessionId}`)
  }

  /**
   * 更新会话信息
   */
  static async updateSession(
    sessionId: string,
    request: UpdateSessionRequest
  ): Promise<ChatSession> {
    return http.patch<ChatSession>(`${API_PREFIX}/sessions/${sessionId}`, request)
  }

  /**
   * 删除会话
   */
  static async deleteSession(sessionId: string): Promise<void> {
    await http.delete(`${API_PREFIX}/sessions/${sessionId}`)
  }

  /**
   * 归档会话
   */
  static async archiveSession(sessionId: string): Promise<ChatSession> {
    return http.patch<ChatSession>(`${API_PREFIX}/sessions/${sessionId}/archive`)
  }

  /**
   * 恢复会话
   */
  static async activateSession(sessionId: string): Promise<ChatSession> {
    return http.patch<ChatSession>(`${API_PREFIX}/sessions/${sessionId}/activate`)
  }

  /**
   * 获取问题历史记录
   */
  static async getQuestionHistory(
    query: QuestionHistoryQuery = {}
  ): Promise<QuestionHistoryResponse> {
    return http.get<QuestionHistoryResponse>(`${API_PREFIX}/questions/history`, {
      params: query,
    })
  }

  /**
   * 获取会话的问答记录
   */
  static async getSessionQuestions(
    sessionId: string,
    limit = 50,
    offset = 0
  ): Promise<QuestionHistoryResponse> {
    return http.get<QuestionHistoryResponse>(`${API_PREFIX}/sessions/${sessionId}/questions`, {
      params: { limit, offset },
    })
  }

  /**
   * 提交答案反馈
   */
  static async submitFeedback(request: FeedbackRequest): Promise<void> {
    await http.post(`${API_PREFIX}/feedback`, request)
  }

  /**
   * 获取学习分析数据
   */
  static async getLearningAnalytics(): Promise<LearningAnalytics> {
    return http.get<LearningAnalytics>(`${API_PREFIX}/analytics`)
  }

  /**
   * 获取学习建议和推荐
   */
  static async getRecommendations(): Promise<RecommendationResponse> {
    return http.get<RecommendationResponse>(`${API_PREFIX}/recommendations`)
  }

  /**
   * 搜索历史问题
   */
  static async searchQuestions(
    keyword: string,
    filters: {
      subject?: string
      question_type?: string
      session_id?: string
      limit?: number
      offset?: number
    } = {}
  ): Promise<QuestionHistoryResponse> {
    return http.get<QuestionHistoryResponse>(`${API_PREFIX}/questions/search`, {
      params: {
        q: keyword,
        ...filters,
      },
    })
  }

  /**
   * 导出学习数据
   */
  static async exportData(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await http.get(`${API_PREFIX}/export`, {
      params: { format },
      responseType: 'blob',
    })
    return response
  }

  /**
   * 获取系统统计信息
   */
  static async getSystemStats(): Promise<{
    total_users: number
    total_questions: number
    total_sessions: number
    avg_response_time: number
    active_users_today: number
  }> {
    return http.get(`${API_PREFIX}/stats`)
  }

  /**
   * 批量操作会话
   */
  static async batchOperateSessions(
    sessionIds: string[],
    operation: 'archive' | 'activate' | 'delete'
  ): Promise<void> {
    await http.post(`${API_PREFIX}/sessions/batch`, {
      session_ids: sessionIds,
      operation,
    })
  }

  /**
   * 获取用户的学习偏好设置
   */
  static async getUserPreferences(): Promise<{
    default_subject?: string
    default_difficulty?: number
    auto_context?: boolean
    max_history?: number
    notification_enabled?: boolean
  }> {
    return http.get(`${API_PREFIX}/preferences`)
  }

  /**
   * 更新用户的学习偏好设置
   */
  static async updateUserPreferences(preferences: {
    default_subject?: string
    default_difficulty?: number
    auto_context?: boolean
    max_history?: number
    notification_enabled?: boolean
  }): Promise<void> {
    await http.put(`${API_PREFIX}/preferences`, preferences)
  }

  /**
   * 获取知识图谱数据
   */
  static async getKnowledgeGraph(subject?: string): Promise<{
    nodes: Array<{
      id: string
      label: string
      category: string
      level: number
      mastery?: number
    }>
    edges: Array<{
      source: string
      target: string
      relationship: string
      strength: number
    }>
  }> {
    return http.get(`${API_PREFIX}/knowledge-graph`, {
      params: subject ? { subject } : {},
    })
  }

  /**
   * 生成学习报告
   */
  static async generateReport(
    type: 'daily' | 'weekly' | 'monthly',
    date?: string
  ): Promise<{
    report_id: string
    report_url: string
    generated_at: string
  }> {
    return http.post(`${API_PREFIX}/reports`, {
      type,
      date,
    })
  }
}

export default LearningAPI
