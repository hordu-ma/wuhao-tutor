/**
 * 学情分析 API 模块
 * @description 封装学情分析相关的后端 API 调用
 * @module api/analysis
 */

const { request } = require('../utils/request.js');

/**
 * 学情分析 API
 */
const analysisAPI = {
  /**
   * 获取学情总览
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学情总览数据
   */
  getOverview(params = {}, config = {}) {
    const { days = 30 } = params;

    return request.get('analysis/overview', { days }, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取活跃度时间分布
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {string} [params.granularity='day'] - 时间粒度 (hour/day/week/month)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 活跃度数据
   */
  getActivity(params = {}, config = {}) {
    const { days = 30, granularity = 'day' } = params;

    return request.get('analysis/activity', { days, granularity }, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取知识点掌握推断
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选
   * @param {string} [params.grade] - 年级筛选
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 知识点掌握数据
   */
  getMastery(params = {}, config = {}) {
    const { subject, grade } = params;

    const queryParams = {};
    if (subject) queryParams.subject = subject;
    if (grade) queryParams.grade = grade;

    return request.get('analysis/mastery', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取个性化学习建议
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选
   * @param {string} [params.focus] - 关注领域 (weak/strong/balanced)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习建议数据
   */
  getRecommendations(params = {}, config = {}) {
    const { subject, focus } = params;

    const queryParams = {};
    if (subject) queryParams.subject = subject;
    if (focus) queryParams.focus = focus;

    return request.get('analysis/recommendations', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取学习趋势
   * @param {Object} params - 查询参数
   * @param {string} params.metric - 指标类型 (score/frequency/duration/mastery)
   * @param {number} [params.days=30] - 统计天数
   * @param {string} [params.subject] - 学科筛选
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 趋势数据
   */
  getTrends(params, config = {}) {
    if (!params || !params.metric) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '指标类型不能为空',
      });
    }

    const { metric, days = 30, subject } = params;

    const queryParams = { metric, days };
    if (subject) queryParams.subject = subject;

    return request.get('analysis/trends', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取学习统计数据（用于学情报告）
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 综合统计数据
   */
  getAnalytics(params = {}, config = {}) {
    const { days = 30 } = params;

    return request.get('learning/analytics', { days }, {
      showLoading: true,
      loadingText: '加载数据中...',
      ...config,
    });
  },

  /**
   * 获取学习进度统计
   * @param {Object} params - 查询参数
   * @param {number} [params.days=7] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习进度数据
   */
  getProgress(params = {}, config = {}) {
    const { days = 7 } = params;

    return request.get('learning/progress', { days }, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取学习历史记录
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=20] - 每页数量
   * @param {string} [params.type] - 类型筛选 (homework/question/achievement)
   * @param {number} [params.days=90] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习历史数据
   */
  getHistory(params = {}, config = {}) {
    const { page = 1, size = 20, type, days = 90 } = params;

    const queryParams = {
      limit: size,
      offset: (page - 1) * size,
      days,
    };

    if (type) queryParams.type = type;

    return request.get('learning/history', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取学习目标列表
   * @param {Object} params - 查询参数
   * @param {string} [params.status] - 状态筛选 (active/completed/overdue)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习目标列表
   */
  getGoals(params = {}, config = {}) {
    const { status } = params;

    const queryParams = {};
    if (status) queryParams.status = status;

    return request.get('learning/goals', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 创建学习目标
   * @param {Object} params - 目标参数
   * @param {string} params.title - 目标标题
   * @param {string} params.description - 目标描述
   * @param {string} params.target_date - 目标日期 (ISO 8601)
   * @param {string} [params.subject] - 相关学科
   * @param {number} [params.target_value] - 目标值
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 创建的目标信息
   */
  createGoal(params, config = {}) {
    if (!params || !params.title || !params.target_date) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '目标标题和目标日期不能为空',
      });
    }

    return request.post('learning/goals', params, {
      showLoading: true,
      loadingText: '创建中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 更新学习目标
   * @param {string} goalId - 目标 ID
   * @param {Object} params - 更新参数
   * @param {string} [params.title] - 目标标题
   * @param {string} [params.description] - 目标描述
   * @param {string} [params.target_date] - 目标日期
   * @param {string} [params.status] - 目标状态
   * @param {number} [params.progress] - 进度百分比
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新后的目标信息
   */
  updateGoal(goalId, params, config = {}) {
    return request.put(`learning/goals/${goalId}`, params, {
      showLoading: true,
      loadingText: '更新中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 删除学习目标
   * @param {string} goalId - 目标 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 删除结果
   */
  deleteGoal(goalId, config = {}) {
    return request.delete(`learning/goals/${goalId}`, {}, {
      showLoading: true,
      loadingText: '删除中...',
      ...config,
    });
  },

  /**
   * 更新目标进度
   * @param {string} goalId - 目标 ID
   * @param {Object} params - 进度参数
   * @param {number} params.progress - 进度百分比 (0-100)
   * @param {string} [params.note] - 进度说明
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新结果
   */
  updateGoalProgress(goalId, params, config = {}) {
    if (!params || typeof params.progress !== 'number') {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '进度值不能为空',
      });
    }

    return request.post(`learning/goals/${goalId}/progress`, params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取学科统计
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学科统计数据
   */
  getSubjectStats(params = {}, config = {}) {
    const { days = 30 } = params;

    return request.get('analysis/subjects', { days }, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取学习模式分析
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习模式数据（活跃时段、星期分布等）
   */
  getLearningPatterns(params = {}, config = {}) {
    const { days = 30 } = params;

    return request.get('analysis/patterns', { days }, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取改进建议
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选
   * @param {string} [params.priority] - 优先级筛选 (high/medium/low)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 改进建议列表
   */
  getImprovements(params = {}, config = {}) {
    const { subject, priority } = params;

    const queryParams = {};
    if (subject) queryParams.subject = subject;
    if (priority) queryParams.priority = priority;

    return request.get('analysis/improvements', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取知识缺口分析
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选
   * @param {number} [params.threshold=0.6] - 掌握度阈值（低于此值视为缺口）
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 知识缺口数据
   */
  getKnowledgeGaps(params = {}, config = {}) {
    const { subject, threshold = 0.6 } = params;

    const queryParams = { threshold };
    if (subject) queryParams.subject = subject;

    return request.get('analysis/gaps', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 生成学习报告（可导出）
   * @param {Object} params - 报告参数
   * @param {number} [params.days=30] - 统计天数
   * @param {string} [params.format='json'] - 报告格式 (json/pdf)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习报告数据或下载链接
   */
  generateReport(params = {}, config = {}) {
    const { days = 30, format = 'json' } = params;

    return request.post('analysis/report', { days, format }, {
      showLoading: true,
      loadingText: '生成报告中...',
      ...config,
    });
  },

  /**
   * 获取学习排名（班级/年级）
   * @param {Object} params - 查询参数
   * @param {string} [params.scope='class'] - 排名范围 (class/grade/school)
   * @param {string} [params.metric='score'] - 排名指标 (score/frequency/improvement)
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 排名数据
   */
  getRanking(params = {}, config = {}) {
    const { scope = 'class', metric = 'score', days = 30 } = params;

    return request.get('analysis/ranking', { scope, metric, days }, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取成就徽章
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 成就徽章列表
   */
  getAchievements(config = {}) {
    return request.get('learning/achievements', {}, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取学习洞察（AI 生成的分析）
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习洞察数据
   */
  getInsights(params = {}, config = {}) {
    const { days = 30 } = params;

    return request.get('analysis/insights', { days }, {
      showLoading: false,
      ...config,
    });
  },
};

module.exports = analysisAPI;
