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

    return request.get('api/v1/mistakes', queryParams, {
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
      `api/v1/mistakes/${mistakeId}`,
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

    return request.post('api/v1/mistakes', params, {
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

    return request.put(`api/v1/mistakes/${mistakeId}`, params, {
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
      `api/v1/mistakes/${mistakeId}`,
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
      'api/v1/mistakes/today-review',
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

    return request.post(`api/v1/mistakes/${mistakeId}/complete-review`, params, {
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

    return request.get('api/v1/mistakes/statistics', queryParams, {
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

    return request.get('api/v1/mistakes/review-calendar', queryParams, {
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

    return request.post('api/v1/mistakes/batch-import', params, {
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

    return request.get('api/v1/mistakes/export', queryParams, {
      showLoading: true,
      loadingText: '导出中...',
      showError: true,
      timeout: 30000, // 30秒超时
      ...config,
    });
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

    return request.post(
      `api/v1/mistakes/from-question/${questionId}`,
      params,
      {
        showLoading: true,
        loadingText: '添加中...',
        showError: true,
        ...config,
      },
    );
  },
};

module.exports = mistakesAPI;
