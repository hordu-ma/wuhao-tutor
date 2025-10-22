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
    return request.post('api/v1/learning/sessions', params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取会话列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {string} [params.status_filter] - 会话状态筛选 (active/archived)
   * @param {string} [params.subject_filter] - 学科筛选
   * @param {string} [params.search] - 搜索关键词
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话列表响应 {total, page, size, pages, items}
   */
  getSessions(params = {}, config = {}) {
    const { page = 1, size = 10, status_filter, subject_filter, search } = params;

    const queryParams = {
      page,
      size,
    };

    if (status_filter) queryParams.status_filter = status_filter;
    if (subject_filter) queryParams.subject_filter = subject_filter;
    if (search) queryParams.search = search;

    return request.get('api/v1/learning/sessions', queryParams, {
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
      `api/v1/learning/sessions/${sessionId}`,
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
    return request.put(`api/v1/learning/sessions/${sessionId}`, params, {
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
      `api/v1/learning/sessions/${sessionId}`,
      {},
      {
        showLoading: true,
        loadingText: '删除中...',
        ...config,
      },
    );
  },

  /**
   * 向 AI 提问 - 对齐网页端实现
   * @param {Object} params - 提问参数
   * @param {string} params.content - 问题内容（对齐网页端字段名）
   * @param {string} [params.session_id] - 会话 ID
   * @param {string} [params.subject] - 学科
   * @param {string} [params.question_type] - 问题类型
   * @param {Array<string>} [params.image_urls] - 图片 URL 列表
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} AI 回答
   */
  askQuestion(params, config = {}) {
    if (!params || !params.content) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问题内容不能为空',
      });
    }

    return request.post('api/v1/learning/ask', params, {
      timeout: 60000, // 60秒超时 - 支持图片OCR和AI处理
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

    return request.get('api/v1/learning/questions', queryParams, {
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
      `api/v1/learning/questions/${questionId}`,
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

    return request.get('api/v1/learning/questions/search', queryParams, {
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
    return request.post(`api/v1/learning/questions/${questionId}/rate`, params, {
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
      `api/v1/learning/questions/${questionId}/favorite`,
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
      `api/v1/learning/questions/${questionId}/favorite`,
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
      'api/v1/files/upload',
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

    return request.get('api/v1/learning/recommendations', queryParams, {
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
      `api/v1/learning/questions/${questionId}/similar`,
      { limit },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  // ========== 聊天会话相关方法 (向后兼容) ==========

  /**
   * 获取 AI 服务状态
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} AI 服务状态
   */
  async getAIStatus(config = {}) {
    try {
      const response = await request.get(
        'api/v1/learning/health',
        {},
        {
          showLoading: false,
          ...config,
        },
      );

      // 适配后端返回格式 -> 前端期望格式
      // 后端返回: { status: "ok", module: "learning", ... }
      // 前端期望: { success: true, data: { online: true, capabilities: [...] } }
      return {
        success: response.status === 'ok',
        data: {
          online: response.status === 'ok',
          capabilities: [
            'text_qa', // 文本问答
            'image_upload', // 图片上传
            'context_aware', // 上下文感知
            'multi_subject', // 多学科支持
          ],
          module: response.module,
          timestamp: response.timestamp,
        },
      };
    } catch (error) {
      console.error('[getAIStatus] 获取AI状态失败:', error);
      // 返回离线状态
      return {
        success: false,
        data: {
          online: false,
          capabilities: [],
        },
      };
    }
  },

  /**
   * 获取会话消息列表
   * @param {Object} params - 查询参数
   * @param {string} params.sessionId - 会话 ID (也支持 session_id)
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=20] - 每页大小
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 消息列表
   */
  getMessages(params = {}, config = {}) {
    // 兼容两种参数命名：sessionId (驼峰) 和 session_id (下划线)
    const sessionId = params.sessionId || params.session_id;
    const { page = 1, size = 20 } = params;

    if (!sessionId) {
      console.error('[API错误] getMessages 缺少必需参数 sessionId');
      return Promise.reject(new Error('缺少会话ID'));
    }

    // 调试：验证sessionId在API调用前的状态
    console.log('调试 - getMessages API调用:');
    console.log('  接收到的sessionId:', sessionId);
    console.log('  sessionId长度:', sessionId.length);
    console.log('  sessionId类型:', typeof sessionId);

    const url = `api/v1/learning/sessions/${sessionId}/history`;
    console.log('  构建的URL:', url);
    console.log('  URL长度:', url.length);

    return request.get(
      url,
      { page, size },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取用户统计信息
   * @param {Object} params - 查询参数
   * @param {string} [params.date] - 日期 (YYYY-MM-DD)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 用户统计
   */
  getUserStats(params = {}, config = {}) {
    const { date } = params;

    return request.get('api/v1/learning/stats/daily', date ? { date } : {}, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 清除会话消息
   * @param {Object} params - 参数
   * @param {string} params.sessionId - 会话 ID (也支持 session_id)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 操作结果
   * @deprecated 后端未实现删除会话功能，返回模拟成功
   */
  clearMessages(params = {}, config = {}) {
    // 兼容两种参数命名：sessionId (驼峰) 和 session_id (下划线)
    const sessionId = params.sessionId || params.session_id;

    if (!sessionId) {
      console.error('[API错误] clearMessages 缺少必需参数 sessionId');
      return Promise.reject(new Error('缺少会话ID'));
    }

    // 注意：后端暂无删除会话接口，这里返回模拟成功
    console.warn('[API未实现] 清除消息功能待后端实现');
    return Promise.resolve({
      success: true,
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取推荐问题
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 推荐问题列表
   */
  getRecommendations(config = {}) {
    return request.get('api/v1/learning/recommendations', {}, config);
  },

  /**
   * 将学习问答中的题目加入错题本
   * @param {string} questionId - 问题 ID
   * @param {Object} params - 参数
   * @param {string} [params.student_answer] - 学生答案（可选，用于标记答错）
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 创建的错题详情
   */
  addQuestionToMistakes(questionId, params = {}, config = {}) {
    if (!questionId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问题ID不能为空',
      });
    }

    const { student_answer } = params;
    const queryParams = student_answer ? { student_answer } : {};

    return request.post(
      `api/v1/learning/questions/${questionId}/add-to-mistakes`,
      {},
      {
        params: queryParams, // query 参数
        showLoading: true,
        loadingText: '加入错题本中...',
        showError: true,
        ...config,
      },
    );
  },

  /**
   * 获取系统统计 - 使用日统计接口
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 系统统计信息
   */
  getSystemStats(config = {}) {
    return request.get('api/v1/learning/stats/daily', {}, config);
  },
};

module.exports = learningAPI;
