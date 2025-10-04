/**
 * 学习问答 API 模块
 * @description 封装学习问答相关的后端 API 调用
 * @module api/learning
 */

const { request } = require('../utils/request.js');

/**
 * 学习问答 API
 */
const learningAPI = {
  /**
   * 创建学习会话
   * @param {Object} params - 会话参数
   * @param {string} [params.title] - 会话标题
   * @param {string} [params.subject] - 学科
   * @param {string} [params.grade] - 年级
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话信息
   */
  createSession(params = {}, config = {}) {
    return request.post('learning/sessions', params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取会话列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {string} [params.status] - 会话状态 (active/archived)
   * @param {string} [params.subject] - 学科筛选
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话列表
   */
  getSessions(params = {}, config = {}) {
    const { page = 1, size = 10, status, subject } = params;

    const queryParams = {
      limit: size,
      offset: (page - 1) * size,
    };

    if (status) queryParams.status = status;
    if (subject) queryParams.subject = subject;

    return request.get('learning/sessions', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取会话详情
   * @param {string} sessionId - 会话 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话详情
   */
  getSessionDetail(sessionId, config = {}) {
    return request.get(
      `learning/sessions/${sessionId}`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 更新会话
   * @param {string} sessionId - 会话 ID
   * @param {Object} params - 更新参数
   * @param {string} [params.title] - 会话标题
   * @param {string} [params.status] - 会话状态
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新后的会话信息
   */
  updateSession(sessionId, params, config = {}) {
    return request.put(`learning/sessions/${sessionId}`, params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 删除会话
   * @param {string} sessionId - 会话 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 删除结果
   */
  deleteSession(sessionId, config = {}) {
    return request.delete(
      `learning/sessions/${sessionId}`,
      {},
      {
        showLoading: true,
        loadingText: '删除中...',
        ...config,
      },
    );
  },

  /**
   * 向 AI 提问
   * @param {Object} params - 提问参数
   * @param {string} params.question - 问题内容
   * @param {string} [params.session_id] - 会话 ID（不提供则自动创建新会话）
   * @param {string} [params.subject] - 学科
   * @param {string} [params.grade] - 年级
   * @param {string} [params.difficulty] - 难度等级
   * @param {Array<string>} [params.image_urls] - 图片 URL 列表
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} AI 回答
   */
  askQuestion(params, config = {}) {
    if (!params || !params.question) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问题内容不能为空',
      });
    }

    return request.post('learning/ask', params, {
      timeout: 30000, // 30秒超时
      showLoading: true,
      loadingText: 'AI 思考中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 获取问题列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {string} [params.session_id] - 会话 ID 筛选
   * @param {string} [params.subject] - 学科筛选
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 问题列表
   */
  getQuestions(params = {}, config = {}) {
    const { page = 1, size = 10, session_id, subject } = params;

    const queryParams = {
      limit: size,
      offset: (page - 1) * size,
    };

    if (session_id) queryParams.session_id = session_id;
    if (subject) queryParams.subject = subject;

    return request.get('learning/questions', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取单个问题和回答
   * @param {string} questionId - 问题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 问题详情
   */
  getQuestionDetail(questionId, config = {}) {
    return request.get(
      `learning/questions/${questionId}`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 搜索问题
   * @param {Object} params - 搜索参数
   * @param {string} params.q - 搜索关键词
   * @param {string} [params.subject] - 学科筛选
   * @param {number} [params.limit=20] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 搜索结果
   */
  searchQuestions(params, config = {}) {
    if (!params || !params.q) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '搜索关键词不能为空',
      });
    }

    const { q, subject, limit = 20 } = params;

    const queryParams = { q, limit };
    if (subject) queryParams.subject = subject;

    return request.get('learning/questions/search', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 对答案评价（点赞/点踩）
   * @param {string} questionId - 问题 ID
   * @param {Object} params - 评价参数
   * @param {boolean} params.helpful - 是否有帮助
   * @param {string} [params.feedback] - 反馈内容
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 评价结果
   */
  rateAnswer(questionId, params, config = {}) {
    return request.post(`learning/questions/${questionId}/rate`, params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 收藏问题
   * @param {string} questionId - 问题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 收藏结果
   */
  favoriteQuestion(questionId, config = {}) {
    return request.post(
      `learning/questions/${questionId}/favorite`,
      {},
      {
        showLoading: false,
        showError: true,
        ...config,
      },
    );
  },

  /**
   * 取消收藏问题
   * @param {string} questionId - 问题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 取消收藏结果
   */
  unfavoriteQuestion(questionId, config = {}) {
    return request.delete(
      `learning/questions/${questionId}/favorite`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取收藏的问题列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 收藏列表
   * @deprecated 后端未实现，功能开发中
   */
  getFavorites(params = {}, config = {}) {
    console.warn('[API未实现] learning/favorites - 收藏功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { items: [], total: 0 },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取学习洞察（频次等统计）
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习洞察数据
   * @deprecated 后端未实现，功能开发中
   */
  getInsights(params = {}, config = {}) {
    console.warn('[API未实现] learning/insights - 学习见解功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { insights: [] },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 上传图片用于提问
   * @param {string} filePath - 本地文件路径
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 上传结果（包含图片 URL）
   */
  uploadQuestionImage(filePath, config = {}) {
    return request.upload(
      'files/upload',
      filePath,
      'file',
      { category: 'question' },
      {
        showLoading: true,
        loadingText: '上传图片中...',
        ...config,
      },
    );
  },

  /**
   * 批量上传图片用于提问
   * @param {Array<string>} filePaths - 本地文件路径列表
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Array<Object>>} 上传结果列表
   */
  async uploadQuestionImages(filePaths, config = {}) {
    if (!Array.isArray(filePaths) || filePaths.length === 0) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '文件路径列表不能为空',
      });
    }

    const results = [];
    const errors = [];

    for (let i = 0; i < filePaths.length; i++) {
      try {
        const result = await this.uploadQuestionImage(filePaths[i], {
          ...config,
          loadingText: `上传图片 ${i + 1}/${filePaths.length}`,
        });

        if (result.success && result.data) {
          results.push(result.data);
        } else {
          errors.push({
            index: i,
            path: filePaths[i],
            error: result.error || '上传失败',
          });
        }
      } catch (error) {
        errors.push({
          index: i,
          path: filePaths[i],
          error: error.message || '上传失败',
        });
      }
    }

    if (errors.length > 0) {
      console.warn('部分图片上传失败:', errors);
    }

    return {
      success: true,
      data: results,
      errors: errors.length > 0 ? errors : undefined,
    };
  },

  /**
   * 获取推荐问题
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科
   * @param {string} [params.grade] - 年级
   * @param {number} [params.limit=5] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 推荐问题列表
   */
  getRecommendedQuestions(params = {}, config = {}) {
    const { subject, grade, limit = 5 } = params;

    const queryParams = { limit };
    if (subject) queryParams.subject = subject;
    if (grade) queryParams.grade = grade;

    return request.get('learning/recommendations', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取热门问题
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选
   * @param {number} [params.days=7] - 统计天数
   * @param {number} [params.limit=10] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 热门问题列表
   * @deprecated 后端未实现，功能开发中
   */
  getPopularQuestions(params = {}, config = {}) {
    console.warn('[API未实现] learning/popular - 热门问题功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { items: [], total: 0 },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取相似问题
   * @param {string} questionId - 问题 ID
   * @param {Object} params - 查询参数
   * @param {number} [params.limit=5] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 相似问题列表
   */
  getSimilarQuestions(questionId, params = {}, config = {}) {
    const { limit = 5 } = params;

    return request.get(
      `learning/questions/${questionId}/similar`,
      { limit },
      {
        showLoading: false,
        ...config,
      },
    );
  },
};

module.exports = learningAPI;
