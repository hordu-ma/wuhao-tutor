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

    // 映射时间范围参数到后端格式
    let timeRange = 'all';
    if (days <= 7) timeRange = '7d';
    else if (days <= 30) timeRange = '30d';
    else if (days <= 90) timeRange = '90d';

    return request.get(
      'api/v1/analytics/learning-stats',
      { time_range: timeRange },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取活跃度时间分布
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {string} [params.granularity='day'] - 时间粒度 (暂不支持，使用默认)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 活跃度数据
   */
  getActivity(params = {}, config = {}) {
    const { days = 30 } = params;

    // 映射时间范围参数
    let timeRange = 'all';
    if (days <= 7) timeRange = '7d';
    else if (days <= 30) timeRange = '30d';
    else if (days <= 90) timeRange = '90d';

    // 注意: 后端learning-stats包含study_trend，可用于活跃度展示
    // granularity参数暂时不支持，使用后端默认粒度
    return request
      .get(
        'api/v1/analytics/learning-stats',
        { time_range: timeRange },
        {
          showLoading: false,
          ...config,
        },
      )
      .then(response => {
        // 提取活跃度相关数据
        if (response.success && response.data) {
          return {
            success: true,
            data: {
              study_trend: response.data.study_trend || [],
              total_study_days: response.data.total_study_days || 0,
            },
            message: response.message,
          };
        }
        return response;
      });
  },

  /**
   * 获取知识点掌握推断
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选
   * @param {string} [params.grade] - 年级筛选 (暂不支持)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 知识点掌握数据
   */
  getMastery(params = {}, config = {}) {
    const { subject } = params;
    // 注意: grade参数后端暂不支持

    const queryParams = {};
    if (subject) queryParams.subject = subject;

    return request.get('api/v1/analytics/knowledge-map', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取个性化学习建议
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选 (暂不支持)
   * @param {string} [params.focus] - 关注领域 (暂不支持)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习建议数据
   */
  getRecommendations(params = {}, config = {}) {
    // 注意: 后端learning/recommendations暂不支持subject和focus参数
    // 返回通用学习建议

    return request.get(
      'learning/recommendations',
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取学习趋势
   * @param {Object} params - 查询参数
   * @param {string} params.metric - 指标类型 (score/frequency/duration/mastery)
   * @param {number} [params.days=30] - 统计天数
   * @param {string} [params.subject] - 学科筛选 (暂不支持)
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

    const { days = 30 } = params;
    // 注意: metric和subject参数后端暂不支持
    // 使用learning-stats的study_trend数据

    let timeRange = 'all';
    if (days <= 7) timeRange = '7d';
    else if (days <= 30) timeRange = '30d';
    else if (days <= 90) timeRange = '90d';

    return request
      .get(
        'analytics/learning-stats',
        { time_range: timeRange },
        {
          showLoading: false,
          ...config,
        },
      )
      .then(response => {
        if (response.success && response.data) {
          return {
            success: true,
            data: {
              trend: response.data.study_trend || [],
              metric: params.metric,
            },
            message: response.message,
          };
        }
        return response;
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

    return request.get(
      'learning/analytics',
      { days },
      {
        showLoading: true,
        loadingText: '加载数据中...',
        ...config,
      },
    );
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

    let timeRange = '7d';
    if (days <= 7) timeRange = '7d';
    else if (days <= 30) timeRange = '30d';
    else if (days <= 90) timeRange = '90d';
    else timeRange = 'all';

    return request.get(
      'analytics/learning-stats',
      { time_range: timeRange },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取学习历史记录
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=20] - 每页数量
   * @param {string} [params.type] - 类型筛选 (暂不支持)
   * @param {number} [params.days=90] - 统计天数 (暂不支持)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习历史数据
   */
  getHistory(params = {}, config = {}) {
    const { page = 1, size = 20 } = params;
    // 注意: type和days参数后端暂不支持

    const queryParams = {
      limit: size,
      offset: (page - 1) * size,
    };

    return request.get('learning/questions/history', queryParams, {
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
   * @deprecated 后端未实现，功能开发中
   */
  getGoals(params = {}, config = {}) {
    console.warn('[API未实现] learning/goals - 学习目标功能待后端实现');
    return Promise.resolve({
      success: true,
      data: {
        items: [],
        total: 0,
      },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取学习洞察（AI 生成的分析）
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习洞察数据
   * @deprecated 后端未实现，功能开发中
   */
  getInsights(params = {}, config = {}) {
    console.warn('[API未实现] analysis/insights - 学习洞察功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { insights: [] },
      message: '功能开发中，敬请期待',
    });
  },

  // ==================== 以下功能待后端实现 ====================
  // 这些方法暂时返回友好提示，避免调用时报错

  /**
   * 创建学习目标 (待实现)
   * @deprecated 后端未实现
   */
  createGoal(params, config = {}) {
    console.warn('[API未实现] POST learning/goals - 学习目标功能待后端实现');
    return Promise.reject({
      code: 'NOT_IMPLEMENTED',
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 更新学习目标 (待实现)
   * @deprecated 后端未实现
   */
  updateGoal(goalId, params, config = {}) {
    console.warn('[API未实现] PUT learning/goals - 学习目标功能待后端实现');
    return Promise.reject({
      code: 'NOT_IMPLEMENTED',
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 删除学习目标 (待实现)
   * @deprecated 后端未实现
   */
  deleteGoal(goalId, config = {}) {
    console.warn('[API未实现] DELETE learning/goals - 学习目标功能待后端实现');
    return Promise.reject({
      code: 'NOT_IMPLEMENTED',
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取学科分析 (待实现)
   * @deprecated 后端未实现
   */
  getSubjects(params = {}, config = {}) {
    console.warn('[API未实现] analysis/subjects - 学科分析功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { subjects: [] },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取学习模式分析 (待实现)
   * @deprecated 后端未实现
   */
  getPatterns(params = {}, config = {}) {
    console.warn('[API未实现] analysis/patterns - 学习模式分析待后端实现');
    return Promise.resolve({
      success: true,
      data: { patterns: [] },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取改进建议 (待实现)
   * @deprecated 后端未实现
   */
  getImprovements(params = {}, config = {}) {
    console.warn('[API未实现] analysis/improvements - 改进建议功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { improvements: [] },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取知识缺口分析 (待实现)
   * @deprecated 后端未实现
   */
  getGaps(params = {}, config = {}) {
    console.warn('[API未实现] analysis/gaps - 知识缺口分析待后端实现');
    return Promise.resolve({
      success: true,
      data: { gaps: [] },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 生成学情报告 (待实现)
   * @deprecated 后端未实现
   */
  generateReport(params, config = {}) {
    console.warn('[API未实现] POST analysis/report - 学情报告生成待后端实现');
    return Promise.reject({
      code: 'NOT_IMPLEMENTED',
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取排名信息 (待实现)
   * @deprecated 后端未实现
   */
  getRanking(params = {}, config = {}) {
    console.warn('[API未实现] analysis/ranking - 排名功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { ranking: [] },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取学习成就 (待实现)
   * @deprecated 后端未实现
   */
  getAchievements(config = {}) {
    console.warn('[API未实现] learning/achievements - 成就系统待后端实现');
    return Promise.resolve({
      success: true,
      data: { achievements: [] },
      message: '功能开发中，敬请期待',
    });
  },
};

module.exports = analysisAPI;
