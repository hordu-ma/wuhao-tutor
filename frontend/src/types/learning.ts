/**
 * 学习问答系统类型定义
 * 包含问答、会话、学习分析等相关类型
 */

// ========== 枚举类型 ==========

export enum QuestionType {
  CONCEPT = "concept",
  PROBLEM_SOLVING = "problem_solving",
  STUDY_GUIDANCE = "study_guidance",
  HOMEWORK_HELP = "homework_help",
  EXAM_PREPARATION = "exam_preparation",
  GENERAL_INQUIRY = "general_inquiry",
}

export enum SessionStatus {
  ACTIVE = "active",
  CLOSED = "closed",
  ARCHIVED = "archived",
}

export enum DifficultyLevel {
  VERY_EASY = 1,
  EASY = 2,
  MEDIUM = 3,
  HARD = 4,
  VERY_HARD = 5,
}

export enum SubjectType {
  MATH = "math",
  CHINESE = "chinese",
  ENGLISH = "english",
  PHYSICS = "physics",
  CHEMISTRY = "chemistry",
  BIOLOGY = "biology",
  HISTORY = "history",
  GEOGRAPHY = "geography",
  POLITICS = "politics",
}

// ========== 基础接口 ==========

export interface LearningContext {
  user_id?: string;
  subject?: SubjectType;
  grade_level?: string;
  session_id?: string;
  related_homework_ids?: string[];
  knowledge_points?: string[];
}

export interface Question {
  id: string;
  session_id: string;
  user_id: string;
  content: string;
  question_type: QuestionType;
  subject?: SubjectType;
  topic?: string;
  difficulty_level?: DifficultyLevel;
  image_urls?: string[];
  context_data?: Record<string, any>;
  is_processed: boolean;
  processing_time?: number;
  created_at: string;
  updated_at: string;
}

export interface Answer {
  id: string;
  question_id: string;
  content: string;
  confidence_score?: number;
  related_topics?: string[];
  suggested_questions?: string[];
  model_name?: string;
  tokens_used?: number;
  generation_time?: number;
  user_rating?: number;
  user_feedback?: string;
  is_helpful?: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  subject?: SubjectType;
  grade_level?: string;
  status: SessionStatus;
  context_enabled: boolean;
  question_count: number;
  total_tokens: number;
  last_active_at?: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionAnswerPair {
  question: Question;
  answer?: Answer;
}

// ========== 请求类型 ==========

export interface AskQuestionRequest {
  content: string;
  question_type?: QuestionType;
  subject?: SubjectType;
  topic?: string;
  difficulty_level?: DifficultyLevel;
  image_urls?: string[];
  context_data?: Record<string, any>;
  session_id?: string;
  use_context?: boolean;
  include_history?: boolean;
  max_history?: number;
}

export interface CreateSessionRequest {
  title: string;
  subject?: SubjectType;
  grade_level?: string;
  context_enabled?: boolean;
  initial_question?: string;
}

export interface UpdateSessionRequest {
  title?: string;
  status?: SessionStatus;
  context_enabled?: boolean;
}

export interface FeedbackRequest {
  question_id: string;
  rating: number;
  feedback?: string;
  is_helpful: boolean;
}

export interface SessionListQuery {
  status?: string;
  subject?: string;
  limit?: number;
  offset?: number;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface QuestionHistoryQuery {
  session_id?: string;
  subject?: string;
  question_type?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
  search?: string;
}

// ========== 响应类型 ==========

export interface AskQuestionResponse {
  question: Question;
  answer: Answer;
  session: ChatSession;
  processing_time: number;
  tokens_used: number;
}

export interface SessionListResponse {
  items: ChatSession[];
  total: number;
  has_more: boolean;
  next_offset?: number;
}

export interface QuestionHistoryResponse {
  items: QuestionAnswerPair[];
  total: number;
  has_more: boolean;
  next_offset?: number;
}

export interface LearningAnalytics {
  total_questions: number;
  total_sessions: number;
  avg_response_time: number;
  favorite_subjects: { subject: SubjectType; count: number }[];
  question_types_distribution: { type: QuestionType; count: number }[];
  weekly_activity: { date: string; questions: number }[];
  knowledge_points: { point: string; proficiency: number }[];
  recent_topics: string[];
}

export interface RecommendationResponse {
  suggested_topics: string[];
  recommended_questions: string[];
  study_plans: {
    title: string;
    description: string;
    estimated_time: number;
    difficulty: DifficultyLevel;
  }[];
  related_resources: {
    title: string;
    type: "article" | "video" | "exercise";
    url: string;
    description?: string;
  }[];
}

// ========== UI状态类型 ==========

export interface ChatMessage {
  id: string;
  type: "user" | "ai";
  content: string;
  timestamp: string;
  question_id?: string;
  answer_id?: string;
  question_type?: QuestionType;
  subject?: SubjectType;
  image_urls?: string[];
  is_processing?: boolean;
  error?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  currentSession?: ChatSession;
  sessions: ChatSession[];
  isTyping: boolean;
  isLoading: boolean;
  error?: string;
}

export interface LearningState {
  chatState: ChatState;
  analytics?: LearningAnalytics;
  recommendations?: RecommendationResponse;
  isLoadingAnalytics: boolean;
  isLoadingSessions: boolean;
  isLoadingRecommendations: boolean;
}

// ========== 常量和配置 ==========

export const QUESTION_TYPE_OPTIONS = [
  { label: "概念理解", value: QuestionType.CONCEPT, icon: "lightbulb" },
  {
    label: "解题指导",
    value: QuestionType.PROBLEM_SOLVING,
    icon: "calculator",
  },
  {
    label: "学习指导",
    value: QuestionType.STUDY_GUIDANCE,
    icon: "academic-cap",
  },
  { label: "作业帮助", value: QuestionType.HOMEWORK_HELP, icon: "book-open" },
  {
    label: "考试准备",
    value: QuestionType.EXAM_PREPARATION,
    icon: "clipboard-check",
  },
  {
    label: "一般咨询",
    value: QuestionType.GENERAL_INQUIRY,
    icon: "question-mark-circle",
  },
];

export const SUBJECT_OPTIONS = [
  { label: "数学", value: SubjectType.MATH, color: "#3B82F6" },
  { label: "语文", value: SubjectType.CHINESE, color: "#EF4444" },
  { label: "英语", value: SubjectType.ENGLISH, color: "#10B981" },
  { label: "物理", value: SubjectType.PHYSICS, color: "#8B5CF6" },
  { label: "化学", value: SubjectType.CHEMISTRY, color: "#F59E0B" },
  { label: "生物", value: SubjectType.BIOLOGY, color: "#06B6D4" },
  { label: "历史", value: SubjectType.HISTORY, color: "#84CC16" },
  { label: "地理", value: SubjectType.GEOGRAPHY, color: "#F97316" },
  { label: "政治", value: SubjectType.POLITICS, color: "#EC4899" },
];

export const DIFFICULTY_OPTIONS = [
  { label: "非常简单", value: DifficultyLevel.VERY_EASY, color: "#10B981" },
  { label: "简单", value: DifficultyLevel.EASY, color: "#84CC16" },
  { label: "中等", value: DifficultyLevel.MEDIUM, color: "#F59E0B" },
  { label: "困难", value: DifficultyLevel.HARD, color: "#EF4444" },
  { label: "非常困难", value: DifficultyLevel.VERY_HARD, color: "#7C2D12" },
];

export const SESSION_STATUS_MAP = {
  [SessionStatus.ACTIVE]: { label: "进行中", color: "#10B981" },
  [SessionStatus.CLOSED]: { label: "已结束", color: "#6B7280" },
  [SessionStatus.ARCHIVED]: { label: "已归档", color: "#8B5CF6" },
};
