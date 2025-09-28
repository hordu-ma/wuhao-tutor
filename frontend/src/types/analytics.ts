/**
 * 学情分析相关类型定义
 */

// 学习统计数据
export interface LearningStats {
  totalStudyTime: number; // 总学习时长（分钟）
  totalHomework: number; // 总作业数
  completedHomework: number; // 已完成作业数
  averageScore: number; // 平均分数
  totalQuestions: number; // 总提问数
  studyDays: number; // 学习天数
  streak: number; // 连续学习天数
}

// 学习进度数据
export interface LearningProgress {
  date: string; // 日期 YYYY-MM-DD
  studyTime: number; // 学习时长（分钟）
  homeworkCount: number; // 作业完成数量
  questionCount: number; // 提问数量
  averageScore: number; // 当日平均分数
}

// 知识点掌握度数据
export interface KnowledgePoint {
  id: string;
  name: string; // 知识点名称
  subject: string; // 学科
  masteryLevel: number; // 掌握度 0-100
  practiceCount: number; // 练习次数
  correctRate: number; // 正确率 0-100
  lastPracticeTime: string; // 最后练习时间
  difficulty: 'easy' | 'medium' | 'hard'; // 难度级别
  tags: string[]; // 标签
}

// 学科统计数据
export interface SubjectStats {
  subject: string; // 学科名称
  totalHomework: number; // 总作业数
  averageScore: number; // 平均分数
  studyTime: number; // 学习时长
  knowledgePoints: number; // 知识点数量
  masteryRate: number; // 掌握率
  weakPoints: string[]; // 薄弱知识点
}

// 学习建议
export interface LearningRecommendation {
  id: string;
  type: 'knowledge' | 'practice' | 'review' | 'method'; // 建议类型
  title: string; // 建议标题
  description: string; // 详细描述
  priority: 'high' | 'medium' | 'low'; // 优先级
  subject?: string; // 相关学科
  knowledgePoints?: string[]; // 相关知识点
  estimatedTime: number; // 预估时间（分钟）
  createdAt: string; // 创建时间
}

// 学习目标
export interface LearningGoal {
  id: string;
  title: string; // 目标标题
  description: string; // 目标描述
  type: 'daily' | 'weekly' | 'monthly' | 'custom'; // 目标类型
  targetValue: number; // 目标值
  currentValue: number; // 当前值
  unit: string; // 单位
  deadline: string; // 截止日期
  status: 'active' | 'completed' | 'paused' | 'expired'; // 状态
  createdAt: string; // 创建时间
  completedAt?: string; // 完成时间
}

// 错题分析
export interface ErrorAnalysis {
  id: string;
  homeworkId: string; // 作业ID
  subject: string; // 学科
  knowledgePoint: string; // 知识点
  errorType: string; // 错误类型
  frequency: number; // 错误频率
  lastErrorTime: string; // 最后错误时间
  suggestion: string; // 改进建议
}

// 学习报告
export interface LearningReport {
  id: string;
  userId: string;
  reportType: 'daily' | 'weekly' | 'monthly'; // 报告类型
  startDate: string; // 开始日期
  endDate: string; // 结束日期
  stats: LearningStats; // 统计数据
  progress: LearningProgress[]; // 进度数据
  subjectStats: SubjectStats[]; // 学科统计
  knowledgePoints: KnowledgePoint[]; // 知识点分析
  recommendations: LearningRecommendation[]; // 学习建议
  goals: LearningGoal[]; // 学习目标
  errorAnalysis: ErrorAnalysis[]; // 错题分析
  insights: string[]; // 学习洞察
  generatedAt: string; // 生成时间
}

// API 响应类型
export interface AnalyticsResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

// 图表数据类型
export interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}

// 时间序列图表数据
export interface TimeSeriesData {
  time: string;
  value: number;
  category?: string;
}

// 雷达图数据
export interface RadarData {
  name: string;
  max: number;
  value: number;
}

// 热力图数据
export interface HeatmapData {
  date: string;
  value: number;
  level: number; // 0-4，表示不同的强度级别
}

// 学习时间分布
export interface TimeDistribution {
  hour: number; // 小时 0-23
  count: number; // 学习次数
  duration: number; // 学习时长（分钟）
}

// 知识点网络关系
export interface KnowledgeNetwork {
  nodes: {
    id: string;
    name: string;
    category: string;
    value: number; // 掌握度
    symbolSize: number; // 节点大小
  }[];
  links: {
    source: string;
    target: string;
    value: number; // 关联强度
  }[];
}

// 学习效率分析
export interface EfficiencyAnalysis {
  period: string; // 时间段
  totalTime: number; // 总时间
  effectiveTime: number; // 有效时间
  efficiency: number; // 效率百分比
  peakHours: number[]; // 高效时段
  suggestions: string[]; // 效率建议
}

// 成就系统
export interface Achievement {
  id: string;
  name: string; // 成就名称
  description: string; // 成就描述
  icon: string; // 图标
  type: 'study' | 'homework' | 'streak' | 'improvement' | 'special'; // 成就类型
  condition: {
    type: string; // 条件类型
    value: number; // 目标值
  };
  progress: number; // 当前进度
  unlocked: boolean; // 是否解锁
  unlockedAt?: string; // 解锁时间
  rarity: 'common' | 'rare' | 'epic' | 'legendary'; // 稀有度
}

// 学习模式分析
export interface StudyPatternAnalysis {
  preferredTime: {
    morning: number; // 上午偏好度
    afternoon: number; // 下午偏好度
    evening: number; // 晚上偏好度
  };
  studyDuration: {
    short: number; // 短时学习（<30分钟）
    medium: number; // 中等时长（30-60分钟）
    long: number; // 长时间学习（>60分钟）
  };
  subjectPreference: {
    subject: string;
    score: number; // 偏好分数
  }[];
  learningStyle: 'visual' | 'auditory' | 'kinesthetic' | 'mixed'; // 学习风格
}
