// utils/api.js
// API请求封装工具

const config = require('../config/index.js');
const auth = require('./auth.js');
const storage = require('./storage.js');

/**
 * HTTP请求封装类
 */
class ApiClient {
  constructor() {
    this.baseUrl = config.api.baseUrl;
    this.timeout = config.api.timeout;
    this.retryCount = config.api.retryCount;
    this.retryDelay = config.api.retryDelay;

    // 请求拦截器
    this.requestInterceptors = [];
    // 响应拦截器
    this.responseInterceptors = [];

    this.setupDefaultInterceptors();
  }

  /**
   * 设置默认拦截器
   */
  setupDefaultInterceptors() {
    // 请求拦截器 - 添加认证头
    this.addRequestInterceptor(async (config) => {
      try {
        const token = await auth.getToken();
        if (token) {
          config.header = {
            ...config.header,
            'Authorization': `Bearer ${token}`
          };
        }
      } catch (error) {
        console.warn('获取token失败', error);
      }
      return config;
    });

    // 请求拦截器 - 添加公共头部
    this.addRequestInterceptor((config) => {
      config.header = {
        'Content-Type': 'application/json',
        'X-Client-Type': 'miniprogram',
        'X-Client-Version': config.version,
        ...config.header
      };
      return config;
    });

    // 响应拦截器 - 统一错误处理
    this.addResponseInterceptor(
      (response) => response,
      async (error) => {
        // Token过期处理
        if (error.statusCode === 401) {
          try {
            await auth.refreshToken();
            // 重试原请求
            return this.request(error.config);
          } catch (refreshError) {
            // 刷新失败，跳转登录
            await auth.logout();
            wx.redirectTo({
              url: '/pages/login/index'
            });
            throw refreshError;
          }
        }
        throw error;
      }
    );
  }

  /**
   * 添加请求拦截器
   */
  addRequestInterceptor(fulfilled, rejected) {
    this.requestInterceptors.push({ fulfilled, rejected });
  }

  /**
   * 添加响应拦截器
   */
  addResponseInterceptor(fulfilled, rejected) {
    this.responseInterceptors.push({ fulfilled, rejected });
  }

  /**
   * 执行请求拦截器
   */
  async runRequestInterceptors(config) {
    let processedConfig = config;

    for (const interceptor of this.requestInterceptors) {
      try {
        if (interceptor.fulfilled) {
          processedConfig = await interceptor.fulfilled(processedConfig);
        }
      } catch (error) {
        if (interceptor.rejected) {
          throw await interceptor.rejected(error);
        }
        throw error;
      }
    }

    return processedConfig;
  }

  /**
   * 执行响应拦截器
   */
  async runResponseInterceptors(response, isError = false) {
    let processedResponse = response;

    for (const interceptor of this.responseInterceptors) {
      try {
        const handler = isError ? interceptor.rejected : interceptor.fulfilled;
        if (handler) {
          processedResponse = await handler(processedResponse);
        }
      } catch (error) {
        processedResponse = error;
        isError = true;
      }
    }

    if (isError) {
      throw processedResponse;
    }

    return processedResponse;
  }

  /**
   * 发送HTTP请求
   */
  async request(options) {
    let config = {
      url: '',
      method: 'GET',
      data: null,
      header: {},
      timeout: this.timeout,
      ...options
    };

    // 处理URL
    if (!config.url.startsWith('http')) {
      config.url = `${this.baseUrl}/api/${config.api.version}${config.url}`;
    }

    // 执行请求拦截器
    config = await this.runRequestInterceptors(config);

    // 带重试的请求执行
    return this.executeWithRetry(config);
  }

  /**
   * 带重试机制的请求执行
   */
  async executeWithRetry(config, currentRetry = 0) {
    try {
      const response = await this.executeRequest(config);
      return await this.runResponseInterceptors(response);
    } catch (error) {
      console.error(`请求失败 (第${currentRetry + 1}次尝试)`, error);

      // 判断是否需要重试
      if (currentRetry < this.retryCount && this.shouldRetry(error)) {
        await this.delay(this.retryDelay * Math.pow(2, currentRetry));
        return this.executeWithRetry(config, currentRetry + 1);
      }

      // 执行错误响应拦截器
      try {
        return await this.runResponseInterceptors(error, true);
      } catch (interceptorError) {
        throw interceptorError;
      }
    }
  }

  /**
   * 执行单次请求
   */
  executeRequest(config) {
    return new Promise((resolve, reject) => {
      const requestConfig = {
        ...config,
        success: (res) => {
          // 检查HTTP状态码
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve({
              data: res.data,
              statusCode: res.statusCode,
              header: res.header,
              config
            });
          } else {
            reject({
              statusCode: res.statusCode,
              data: res.data,
              header: res.header,
              config,
              message: `HTTP ${res.statusCode}`
            });
          }
        },
        fail: (error) => {
          reject({
            statusCode: 0,
            message: error.errMsg || '网络请求失败',
            config,
            originalError: error
          });
        }
      };

      wx.request(requestConfig);
    });
  }

  /**
   * 判断是否应该重试
   */
  shouldRetry(error) {
    // 网络错误重试
    if (error.statusCode === 0) {
      return true;
    }

    // 服务器5xx错误重试
    if (error.statusCode >= 500) {
      return true;
    }

    // 429限流错误重试
    if (error.statusCode === 429) {
      return true;
    }

    return false;
  }

  /**
   * 延迟函数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * GET请求
   */
  get(url, params = {}, options = {}) {
    const queryString = this.buildQueryString(params);
    const fullUrl = queryString ? `${url}?${queryString}` : url;

    return this.request({
      url: fullUrl,
      method: 'GET',
      ...options
    });
  }

  /**
   * POST请求
   */
  post(url, data = {}, options = {}) {
    return this.request({
      url,
      method: 'POST',
      data,
      ...options
    });
  }

  /**
   * PUT请求
   */
  put(url, data = {}, options = {}) {
    return this.request({
      url,
      method: 'PUT',
      data,
      ...options
    });
  }

  /**
   * DELETE请求
   */
  delete(url, options = {}) {
    return this.request({
      url,
      method: 'DELETE',
      ...options
    });
  }

  /**
   * 构建查询字符串
   */
  buildQueryString(params) {
    const queryParts = [];

    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') {
        queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
      }
    }

    return queryParts.join('&');
  }

  /**
   * 上传文件
   */
  upload(url, filePath, options = {}) {
    return new Promise(async (resolve, reject) => {
      try {
        // 获取认证头
        const token = await auth.getToken();
        const header = {
          'X-Client-Type': 'miniprogram',
          'X-Client-Version': config.version,
          ...options.header
        };

        if (token) {
          header['Authorization'] = `Bearer ${token}`;
        }

        const uploadConfig = {
          url: url.startsWith('http') ? url : `${this.baseUrl}/api/${config.api.version}${url}`,
          filePath,
          name: options.name || 'file',
          formData: options.formData || {},
          header,
          success: (res) => {
            if (res.statusCode >= 200 && res.statusCode < 300) {
              try {
                const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
                resolve({
                  data,
                  statusCode: res.statusCode,
                  header: res.header
                });
              } catch (parseError) {
                resolve({
                  data: res.data,
                  statusCode: res.statusCode,
                  header: res.header
                });
              }
            } else {
              reject({
                statusCode: res.statusCode,
                data: res.data,
                message: `HTTP ${res.statusCode}`
              });
            }
          },
          fail: (error) => {
            reject({
              statusCode: 0,
              message: error.errMsg || '文件上传失败',
              originalError: error
            });
          }
        };

        wx.uploadFile(uploadConfig);
      } catch (error) {
        reject(error);
      }
    });
  }
}

// 创建API客户端实例
const apiClient = new ApiClient();

/**
 * API接口定义
 */
const api = {
  // 用户认证相关
  auth: {
    // 微信登录
    wechatLogin: (data) => apiClient.post('/auth/wechat-login', data),
    // 刷新Token
    refreshToken: (data) => apiClient.post('/auth/refresh-token', data),
    // 登出
    logout: () => apiClient.post('/auth/logout'),
    // 获取用户信息
    getUserInfo: () => apiClient.get('/auth/user-info'),
    // 更新用户信息
    updateUserInfo: (data) => apiClient.put('/auth/user-info', data),
  },

  // 作业相关
  homework: {
    // 获取作业列表
    getList: (params) => apiClient.get('/homework', params),
    // 获取作业详情
    getDetail: (id) => apiClient.get(`/homework/${id}`),
    // 提交作业
    submit: (id, data) => apiClient.post(`/homework/${id}/submit`, data),
    // 创建作业（教师）
    create: (data) => apiClient.post('/homework', data),
    // 更新作业（教师）
    update: (id, data) => apiClient.put(`/homework/${id}`, data),
    // 删除作业（教师）
    delete: (id) => apiClient.delete(`/homework/${id}`),
    // 批改作业（教师）
    grade: (id, data) => apiClient.post(`/homework/${id}/grade`, data),
  },

  // AI问答相关
  chat: {
    // 发送消息
    sendMessage: (data) => apiClient.post('/chat/message', data),
    // 获取对话历史
    getHistory: (params) => apiClient.get('/chat/history', params),
    // 获取对话详情
    getSession: (sessionId) => apiClient.get(`/chat/session/${sessionId}`),
    // 创建新对话
    createSession: (data) => apiClient.post('/chat/session', data),
    // 删除对话
    deleteSession: (sessionId) => apiClient.delete(`/chat/session/${sessionId}`),
  },

  // 学情分析相关
  analysis: {
    // 获取学习报告
    getReport: (params) => apiClient.get('/analysis/report', params),
    // 获取学习进度
    getProgress: (params) => apiClient.get('/analysis/progress', params),
    // 获取知识点掌握情况
    getKnowledgePoints: (params) => apiClient.get('/analysis/knowledge-points', params),
    // 获取学习统计
    getStatistics: (params) => apiClient.get('/analysis/statistics', params),
  },

  // 文件上传相关
  upload: {
    // 上传图片
    image: (filePath, options = {}) => apiClient.upload('/upload/image', filePath, {
      name: 'image',
      ...options
    }),
    // 上传文件
    file: (filePath, options = {}) => apiClient.upload('/upload/file', filePath, {
      name: 'file',
      ...options
    }),
  },

  // 用户设置相关
  settings: {
    // 获取设置
    get: () => apiClient.get('/settings'),
    // 更新设置
    update: (data) => apiClient.put('/settings', data),
    // 获取消息设置
    getNotification: () => apiClient.get('/settings/notification'),
    // 更新消息设置
    updateNotification: (data) => apiClient.put('/settings/notification', data),
  },

  // 反馈相关
  feedback: {
    // 提交反馈
    submit: (data) => apiClient.post('/feedback', data),
    // 获取反馈列表
    getList: (params) => apiClient.get('/feedback', params),
  },

  // 系统相关
  system: {
    // 获取系统信息
    getInfo: () => apiClient.get('/system/info'),
    // 检查更新
    checkUpdate: () => apiClient.get('/system/update'),
    // 获取公告
    getNotices: (params) => apiClient.get('/system/notices', params),
  },
};

// 兼容性封装
const compatApi = {
  // 作业相关 - 兼容旧版本调用方式
  getHomeworkList: api.homework.getList,
  getHomeworkDetail: api.homework.getDetail,
  submitHomework: (data) => api.homework.submit(data.homeworkId, data),
  createHomework: api.homework.create,
  updateHomework: (data) => api.homework.update(data.id, data),
  deleteHomework: api.homework.delete,
  gradeHomework: (data) => api.homework.grade(data.homeworkId, data),

  // 认证相关 - 兼容旧版本调用方式
  wechatLogin: api.auth.wechatLogin,
  refreshToken: api.auth.refreshToken,
  logout: api.auth.logout,
  getUserInfo: api.auth.getUserInfo,
  updateUserInfo: api.auth.updateUserInfo,

  // 聊天相关 - 兼容旧版本调用方式
  sendChatMessage: api.chat.sendMessage,
  getChatHistory: api.chat.getHistory,
  getChatSession: api.chat.getSession,
  createChatSession: api.chat.createSession,
  deleteChatSession: api.chat.deleteSession,

  // 分析相关 - 兼容旧版本调用方式
  getLearningReport: api.analysis.getReport,
  getLearningProgress: api.analysis.getProgress,
  getKnowledgePoints: api.analysis.getKnowledgePoints,
  getLearningStatistics: api.analysis.getStatistics,

  // 上传相关 - 兼容旧版本调用方式
  uploadImage: api.upload.image,
  uploadFile: api.upload.file,
};

// 导出API客户端和接口
module.exports = {
  apiClient,
  api,
  ...compatApi
};
