/**
 * 作业相关类型定义
 */

// 作业状态枚举
export enum HomeworkStatus {
  SUBMITTED = "submitted", // 已提交
  PROCESSING = "processing", // 处理中
  COMPLETED = "completed", // 已完成
  FAILED = "failed", // 失败
}

// 学科枚举
export enum Subject {
  MATH = "math",
  CHINESE = "chinese",
  ENGLISH = "english",
  PHYSICS = "physics",
  CHEMISTRY = "chemistry",
  BIOLOGY = "biology",
}

// 年级枚举
export enum GradeLevel {
  GRADE_1 = 1,
  GRADE_2 = 2,
  GRADE_3 = 3,
  GRADE_4 = 4,
  GRADE_5 = 5,
  GRADE_6 = 6,
  GRADE_7 = 7,
  GRADE_8 = 8,
  GRADE_9 = 9,
  GRADE_10 = 10,
  GRADE_11 = 11,
  GRADE_12 = 12,
}

// 文件上传接口
export interface FileUpload {
  file: File;
  url?: string;
  progress?: number;
  status?: "uploading" | "success" | "error";
}

// 作业提交请求
export interface HomeworkSubmitRequest {
  subject: Subject;
  grade_level: GradeLevel;
  title?: string;
  description?: string;
  images: File[];
}

// 批改结果接口
export interface HomeworkCorrectionResult {
  correction_id: string;
  is_correct: boolean;
  score: number; // 分数 (0-100)
  corrections: string[]; // 批改意见
  knowledge_points: string[]; // 涉及知识点
  difficulty_level: string; // 难度等级
  suggestions: string[]; // 学习建议
  error_analysis?: string; // 错误分析
  processing_time: number; // 处理时间(秒)
}

// 作业记录接口
export interface HomeworkRecord {
  id: string;
  user_id: string;
  subject: Subject;
  grade_level: GradeLevel;
  title?: string;
  description?: string;
  status: HomeworkStatus;
  original_images: string[]; // 原始图片URLs
  ocr_text?: string; // OCR识别文本
  correction_result?: HomeworkCorrectionResult;
  created_at: string;
  updated_at: string;
}

// 作业列表查询参数
export interface HomeworkQueryParams {
  page?: number;
  page_size?: number;
  subject?: Subject;
  grade_level?: GradeLevel;
  status?: HomeworkStatus;
  start_date?: string;
  end_date?: string;
  search?: string;
}

// 作业列表响应
export interface HomeworkListResponse {
  items: HomeworkRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 学科和年级选项
export interface SubjectOption {
  value: Subject;
  label: string;
}

export interface GradeLevelOption {
  value: GradeLevel;
  label: string;
}

// 常用选项数据
export const SUBJECT_OPTIONS: SubjectOption[] = [
  { value: Subject.MATH, label: "数学" },
  { value: Subject.CHINESE, label: "语文" },
  { value: Subject.ENGLISH, label: "英语" },
  { value: Subject.PHYSICS, label: "物理" },
  { value: Subject.CHEMISTRY, label: "化学" },
  { value: Subject.BIOLOGY, label: "生物" },
];

export const GRADE_LEVEL_OPTIONS: GradeLevelOption[] = [
  { value: GradeLevel.GRADE_1, label: "一年级" },
  { value: GradeLevel.GRADE_2, label: "二年级" },
  { value: GradeLevel.GRADE_3, label: "三年级" },
  { value: GradeLevel.GRADE_4, label: "四年级" },
  { value: GradeLevel.GRADE_5, label: "五年级" },
  { value: GradeLevel.GRADE_6, label: "六年级" },
  { value: GradeLevel.GRADE_7, label: "七年级" },
  { value: GradeLevel.GRADE_8, label: "八年级" },
  { value: GradeLevel.GRADE_9, label: "九年级" },
  { value: GradeLevel.GRADE_10, label: "高一" },
  { value: GradeLevel.GRADE_11, label: "高二" },
  { value: GradeLevel.GRADE_12, label: "高三" },
];

// 状态选项
export const STATUS_OPTIONS = [
  { value: HomeworkStatus.SUBMITTED, label: "已提交", color: "primary" },
  { value: HomeworkStatus.PROCESSING, label: "处理中", color: "warning" },
  { value: HomeworkStatus.COMPLETED, label: "已完成", color: "success" },
  { value: HomeworkStatus.FAILED, label: "失败", color: "danger" },
];
