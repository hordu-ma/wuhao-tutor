/**
 * 错题手册 API 模块
 * @description 封装错题手册相关的后端 API 调用
 * @module api/mistakes
 */

const { request } = require('../utils/request.js');

/**
 * 错题手册 API
 */
const mistakesAPI = {
  /**
   * 获取错题列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=20] - 每页数量
   * @param {string} [params.mastery_status] - 掌握状态: not_mastered|reviewing|mastered
   * @param {string} [params.subject] - 学科筛选
   * @param {number} [params.difficulty_level] - 难度等级: 1简单|2中等|3困难
   * @param {string} [params.keyword] - 搜索关键词
   * @param {string} [params.category] - 🎯 错题类型: empty_question|wrong_answer|hard_question
   * @param {string} [params.source] - 🎯 来源: learning|manual|homework
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 错题列表
   */
  getMistakeList(params = {}, config = {}) {
    const queryParams = {
      page: params.page || 1,
      page_size: params.page_size || 20,
    };

    if (params.mastery_status) queryParams.mastery_status = params.mastery_status;
    if (params.subject) queryParams.subject = params.subject;
    if (params.difficulty_level) queryParams.difficulty_level = params.difficulty_level;
    if (params.keyword) queryParams.keyword = params.keyword;
    if (params.category) queryParams.category = params.category; // 🎯 错题类型筛选
    if (params.source) queryParams.source = params.source; // 🎯 来源筛选

    return request.get('mistakes', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取错题详情
   * @param {string} mistakeId - 错题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 错题详情
   */
  getMistakeDetail(mistakeId, config = {}) {
    if (!mistakeId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '错题 ID 不能为空',
      });
    }

    return request.get(
      `mistakes/${mistakeId}`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 创建错题记录
   * @param {Object} params - 错题数据
   * @param {string} params.subject - 学科
   * @param {number} params.difficulty_level - 难度等级
   * @param {string} params.question_content - 题目内容
   * @param {string} [params.student_answer] - 学生答案
   * @param {string} params.correct_answer - 正确答案
   * @param {string} [params.explanation] - 解析
   * @param {Array<string>} [params.knowledge_points] - 知识点列表
   * @param {string} [params.question_id] - 关联的问答 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 创建的错题信息
   */
  createMistake(params, config = {}) {
    if (!params || !params.subject || !params.question_content || !params.correct_answer) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '科目、题目内容和正确答案不能为空',
      });
    }

    return request.post('mistakes', params, {
      showLoading: true,
      loadingText: '添加中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 更新错题记录
   * @param {string} mistakeId - 错题 ID
   * @param {Object} params - 更新的数据
   * @param {string} [params.subject] - 学科
   * @param {number} [params.difficulty_level] - 难度等级
   * @param {string} [params.question_content] - 题目内容
   * @param {string} [params.student_answer] - 学生答案
   * @param {string} [params.correct_answer] - 正确答案
   * @param {string} [params.explanation] - 解析
   * @param {Array<string>} [params.knowledge_points] - 知识点列表
   * @param {string} [params.mastery_status] - 掌握状态
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新后的错题信息
   */
  updateMistake(mistakeId, params, config = {}) {
    if (!mistakeId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '错题 ID 不能为空',
      });
    }

    return request.put(`mistakes/${mistakeId}`, params, {
      showLoading: true,
      loadingText: '更新中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 删除错题记录
   * @param {string} mistakeId - 错题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 删除结果
   */
  deleteMistake(mistakeId, config = {}) {
    if (!mistakeId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '错题 ID 不能为空',
      });
    }

    return request.delete(
      `mistakes/${mistakeId}`,
      {},
      {
        showLoading: true,
        loadingText: '删除中...',
        showError: true,
        ...config,
      },
    );
  },

  /**
   * 获取今日复习任务
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 今日需要复习的错题列表
   */
  getTodayReview(config = {}) {
    return request.get(
      'mistakes/today-review',
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 完成复习
   * @param {string} mistakeId - 错题 ID
   * @param {Object} params - 复习数据
   * @param {boolean} params.is_correct - 是否答对
   * @param {string} [params.review_notes] - 复习笔记
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 复习结果
   */
  completeReview(mistakeId, params, config = {}) {
    if (!mistakeId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '错题 ID 不能为空',
      });
    }

    if (params.is_correct === undefined || params.is_correct === null) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '请标记是否答对',
      });
    }

    return request.post(`mistakes/${mistakeId}/complete-review`, params, {
      showLoading: true,
      loadingText: '提交中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 获取错题统计数据
   * @param {Object} params - 查询参数
   * @param {string} [params.start_date] - 开始日期
   * @param {string} [params.end_date] - 结束日期
   * @param {string} [params.subject] - 学科筛选
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 统计数据
   */
  getMistakeStatistics(params = {}, config = {}) {
    const queryParams = {};

    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;
    if (params.subject) queryParams.subject = params.subject;

    return request.get('mistakes/statistics', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取复习日历数据
   * @param {Object} params - 查询参数
   * @param {string} [params.year] - 年份
   * @param {string} [params.month] - 月份
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 复习日历数据
   */
  getReviewCalendar(params = {}, config = {}) {
    const queryParams = {};

    if (params.year) queryParams.year = params.year;
    if (params.month) queryParams.month = params.month;

    return request.get('mistakes/review-calendar', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 批量导入错题
   * @param {Object} params - 导入参数
   * @param {Array<Object>} params.mistakes - 错题列表
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 导入结果
   */
  batchImportMistakes(params, config = {}) {
    if (!params || !params.mistakes || !Array.isArray(params.mistakes)) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '错题列表不能为空',
      });
    }

    return request.post('mistakes/batch-import', params, {
      showLoading: true,
      loadingText: '导入中...',
      showError: true,
      timeout: 60000, // 60秒超时
      ...config,
    });
  },

  /**
   * 导出错题数据
   * @param {Object} params - 导出参数
   * @param {string} [params.format] - 导出格式: pdf|excel|json
   * @param {string} [params.mastery_status] - 掌握状态筛选
   * @param {string} [params.subject] - 学科筛选
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 导出文件信息
   */
  exportMistakes(params = {}, config = {}) {
    const queryParams = {
      format: params.format || 'pdf',
    };

    if (params.mastery_status) queryParams.mastery_status = params.mastery_status;
    if (params.subject) queryParams.subject = params.subject;

    return request.get('mistakes/export', queryParams, {
      showLoading: true,
      loadingText: '导出中...',
      showError: true,
      timeout: 30000, // 30秒超时
      ...config,
    });
  },

  /**
   * 🎯 获取学习洞察报告
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习洞察数据
   */
  getLearningInsights(config = {}) {
    return request.get(
      'mistakes/learning-insights',
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 从问答记录创建错题
   * @param {string} questionId - 问答 ID
   * @param {Object} params - 错题补充信息
   * @param {string} [params.student_answer] - 学生答案
   * @param {string} [params.correct_answer] - 正确答案
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 创建的错题信息
   */
  createFromQuestion(questionId, params = {}, config = {}) {
    if (!questionId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问答 ID 不能为空',
      });
    }

    return request.post(`mistakes/from-question/${questionId}`, params, {
      showLoading: true,
      loadingText: '添加中...',
      showError: true,
      ...config,
    });
  },

  // ===== 知识图谱相关 API =====

  /**
   * 获取错题的知识点分析
   * @param {string} mistakeId - 错题ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 知识点分析数据
   */
  getMistakeKnowledgePoints(mistakeId, config = {}) {
    if (!mistakeId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '错题ID不能为空',
      });
    }

    return request.get(
      `knowledge-graph/mistakes/${mistakeId}/knowledge-points`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取知识点列表（用于筛选）
   * @param {Object} params - 查询参数
   * @param {string} params.subject - 学科
   * @param {number} [params.min_count=1] - 最小错题数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Array>} 知识点列表
   */
  getKnowledgePointList(params, config = {}) {
    if (!params || !params.subject) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '学科不能为空',
      });
    }

    const queryParams = {
      subject: params.subject,
    };
    if (params.min_count) queryParams.min_count = params.min_count;

    return request.get('knowledge-graph/knowledge-points', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取知识图谱数据（实时）
   * @param {Object} params - 查询参数
   * @param {string} params.subject - 学科
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 知识点掌握度数据
   */
  getKnowledgeGraphSnapshot(params, config = {}) {
    if (!params || !params.subject) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '学科不能为空',
      });
    }

    return request.get(
      'knowledge-graph/mastery',
      { subject: params.subject },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取薄弱知识链
   * @param {Object} params - 查询参数
   * @param {string} params.subject - 学科
   * @param {number} [params.limit=5] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Array>} 薄弱知识链列表
   */
  getWeakKnowledgeChains(params, config = {}) {
    if (!params || !params.subject) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '学科不能为空',
      });
    }

    const queryParams = {
      subject: params.subject,
      limit: params.limit || 5,
    };

    return request.get('knowledge-graph/weak-chains', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取智能复习推荐
   * @param {Object} params - 查询参数
   * @param {string} params.subject - 学科
   * @param {number} [params.limit=10] - 推荐数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Array>} 复习推荐列表
   */
  getReviewRecommendations(params, config = {}) {
    if (!params || !params.subject) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '学科不能为空',
      });
    }

    const queryParams = {
      subject: params.subject,
      limit: params.limit || 10,
    };

    return request.get('knowledge-graph/review/recommendations', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 🎯 开始复习会话（三阶段递进式复习）
   * @param {string} mistakeId - 错题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 复习会话信息
   * @example
   * const session = await mistakesAPI.startReviewSession(mistakeId);
   * // 返回: { session_id, stage, stage_name, question_content, correct_answer, knowledge_points }
   */
  startReviewSession(mistakeId, config = {}) {
    if (!mistakeId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '错题 ID 不能为空',
      });
    }

    return request.post(
      'reviews/', // 添加尾斜杠避免 307 重定向丢失 body
      { mistake_id: mistakeId },
      {
        showLoading: true,
        loadingText: '正在准备复习...',
        ...config,
      },
    );
  },

  /**
   * 🎯 获取复习会话状态
   * @param {string} sessionId - 会话 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话状态信息
   */
  getReviewSession(sessionId, config = {}) {
    if (!sessionId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '会话 ID 不能为空',
      });
    }

    return request.get(
      `reviews/${sessionId}`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 🎯 提交复习答案（AI判断版本）
   * @param {string} sessionId - 会话 ID
   * @param {Object} params - 答案数据
   * @param {string} params.answer - 用户答案
   * @param {boolean} params.skip - 是否跳过（不会做）
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 提交结果（包含下一阶段信息或反馈）
   * @example
   * // 提交答案AI判断
   * const result = await mistakesAPI.submitReviewAnswer(sessionId, {
   *   answer: '用户的答案',
   *   skip: false
   * });
   * // 跳过（不会做）
   * const result = await mistakesAPI.submitReviewAnswer(sessionId, {
   *   answer: '',
   *   skip: true
   * });
   */
  submitReviewAnswer(sessionId, params, config = {}) {
    if (!sessionId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '会话 ID 不能为空',
      });
    }

    if (!params || typeof params.skip !== 'boolean') {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '答案数据不完整',
      });
    }

    return request.post(`reviews/${sessionId}/submit`, params, {
      showLoading: true,
      loadingText: params.skip ? '加载答案中...' : 'AI判题中...',
      ...config,
    });
  },
};

module.exports = mistakesAPI;
