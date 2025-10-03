// utils/request.js
// 五好伴学小程序 - 网络请求统一封装模块

const config = require('../config/index.js');
const auth = require('./auth.js');
const { networkMonitor } = require('./network-monitor.js');

/**
 * 请求配置接口
 * @typedef {Object} RequestConfig
 * @property {string} url - 请求路径（相对路径或完整URL）
 * @property {string} [method='GET'] - 请求方法
 * @property {Object} [data] - 请求数据
 * @property {Object} [header] - 请求头
 * @property {number} [timeout] - 超时时间（毫秒）
 * @property {boolean} [skipAuth=false] - 是否跳过认证
 * @property {boolean} [showLoading=false] - 是否显示加载提示
 * @property {string} [loadingText='加载中...'] - 加载提示文字
 * @property {boolean} [showError=true] - 是否显示错误提示
 * @property {number} [retryCount=0] - 重试次数
 * @property {number} [retryDelay=1000] - 重试延迟（毫秒）
 */

/**
 * 响应数据接口
 * @typedef {Object} ResponseData
 * @property {boolean} success - 请求是否成功
 * @property {*} data - 响应数据
 * @property {string} [message] - 响应消息
 * @property {Object} [error] - 错误信息
 * @property {string} [error.code] - 错误代码
 * @property {string} [error.message] - 错误消息
 */

/**
 * 网络请求类
 */
class Request {
  constructor() {
    this.baseUrl = config.api.baseUrl;
    this.timeout = config.api.timeout;
    this.version = config.api.version;

    // 请求拦截器队列
    this.requestInterceptors = [];
    // 响应拦截器队列
    this.responseInterceptors = [];

    // 请求队列（用于去重）
    this.pendingRequests = new Map();

    // 统计信息
    this.stats = {
      totalRequests: 0,
      successRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
    };

    // 初始化默认拦截器
    this.setupDefaultInterceptors();
  }

  /**
   * 设置默认拦截器
   */
  setupDefaultInterceptors() {
    // 请求拦截器：添加认证 Token
    this.addRequestInterceptor(async (config) => {
      if (!config.skipAuth) {
        const token = await auth.getToken();
        if (token) {
          config.header = config.header || {};
          config.header.Authorization = `Bearer ${token}`;
        }
      }
      return config;
    });

    // 请求拦截器：添加通用请求头
    this.addRequestInterceptor(async (config) => {
      config.header = {
        'Content-Type': 'application/json',
        'X-Client-Type': 'miniprogram',
        'X-Client-Version': config.version || '1.0.0',
        ...config.header,
      };
      return config;
    });

    // 响应拦截器：统一错误处理
    this.addResponseInterceptor(
      (response) => {
        // 成功响应
        return response;
      },
      (error) => {
        // 错误响应
        console.error('请求错误:', error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * 添加请求拦截器
   * @param {Function} onFulfilled - 成功处理函数
   * @param {Function} onRejected - 失败处理函数
   */
  addRequestInterceptor(onFulfilled, onRejected) {
    this.requestInterceptors.push({
      onFulfilled,
      onRejected,
    });
  }

  /**
   * 添加响应拦截器
   * @param {Function} onFulfilled - 成功处理函数
   * @param {Function} onRejected - 失败处理函数
   */
  addResponseInterceptor(onFulfilled, onRejected) {
    this.responseInterceptors.push({
      onFulfilled,
      onRejected,
    });
  }

  /**
   * 运行请求拦截器
   * @param {RequestConfig} config - 请求配置
   * @returns {Promise<RequestConfig>}
   */
  async runRequestInterceptors(config) {
    let chain = Promise.resolve(config);

    for (const interceptor of this.requestInterceptors) {
      chain = chain.then(
        interceptor.onFulfilled,
        interceptor.onRejected
      );
    }

    return chain;
  }

  /**
   * 运行响应拦截器
   * @param {*} response - 响应数据
   * @returns {Promise<*>}
   */
  async runResponseInterceptors(response) {
    let chain = Promise.resolve(response);

    for (const interceptor of this.responseInterceptors) {
      chain = chain.then(
        interceptor.onFulfilled,
        interceptor.onRejected
      );
    }

    return chain;
  }

  /**
   * 构建完整 URL
   * @param {string} url - 请求路径
   * @returns {string} 完整 URL
   */
  buildUrl(url) {
    // 如果是完整 URL，直接返回
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }

    // 移除开头的斜杠
    const path = url.startsWith('/') ? url.slice(1) : url;

    // 构建完整 URL
    return `${this.baseUrl}/api/${this.version}/${path}`;
  }

  /**
   * 生成请求唯一标识
   * @param {RequestConfig} config - 请求配置
   * @returns {string} 请求标识
   */
  generateRequestKey(config) {
    const { url, method = 'GET', data } = config;
    return `${method}:${url}:${JSON.stringify(data || {})}`;
  }

  /**
   * 显示加载提示
   * @param {string} title - 提示文字
   */
  showLoading(title = '加载中...') {
    wx.showLoading({
      title,
      mask: true,
    });
  }

  /**
   * 隐藏加载提示
   */
  hideLoading() {
    wx.hideLoading();
  }

  /**
   * 显示错误提示
   * @param {string} message - 错误消息
   */
  showError(message) {
    wx.showToast({
      title: message || '请求失败',
      icon: 'error',
      duration: 2000,
    });
  }

  /**
   * 核心请求方法
   * @param {RequestConfig} config - 请求配置
   * @returns {Promise<ResponseData>}
   */
  async request(config) {
    // 记录请求开始时间
    const startTime = Date.now();

    // 更新统计信息
    this.stats.totalRequests++;

    try {
      // 运行请求拦截器
      const processedConfig = await this.runRequestInterceptors(config);

      // 构建完整 URL
      const fullUrl = this.buildUrl(processedConfig.url);

      // 显示加载提示
      if (processedConfig.showLoading) {
        this.showLoading(processedConfig.loadingText);
      }

      // 检查网络状态
      const networkStatus = await this.checkNetworkStatus();
      if (!networkStatus.isConnected) {
        throw {
          code: 'NETWORK_ERROR',
          message: '网络连接失败，请检查网络设置',
        };
      }

      // 请求去重检查
      const requestKey = this.generateRequestKey(processedConfig);
      if (this.pendingRequests.has(requestKey)) {
        console.log('请求去重:', requestKey);
        return this.pendingRequests.get(requestKey);
      }

      // 发起请求
      const requestPromise = this.performRequest({
        ...processedConfig,
        url: fullUrl,
      });

      // 添加到请求队列
      this.pendingRequests.set(requestKey, requestPromise);

      // 等待请求完成
      const response = await requestPromise;

      // 从请求队列移除
      this.pendingRequests.delete(requestKey);

      // 隐藏加载提示
      if (processedConfig.showLoading) {
        this.hideLoading();
      }

      // 运行响应拦截器
      const processedResponse = await this.runResponseInterceptors(response);

      // 更新统计信息
      this.stats.successRequests++;
      const responseTime = Date.now() - startTime;
      this.stats.averageResponseTime =
        (this.stats.averageResponseTime * (this.stats.successRequests - 1) +
          responseTime) /
        this.stats.successRequests;

      return processedResponse;
    } catch (error) {
      // 从请求队列移除
      const requestKey = this.generateRequestKey(config);
      this.pendingRequests.delete(requestKey);

      // 隐藏加载提示
      if (config.showLoading) {
        this.hideLoading();
      }

      // 更新统计信息
      this.stats.failedRequests++;

      // 处理错误
      const normalizedError = this.normalizeError(error);

      // 显示错误提示
      if (config.showError !== false) {
        this.showError(normalizedError.message);
      }

      // 重试逻辑
      if (config.retryCount && config.retryCount > 0) {
        console.log(`请求失败，准备重试 (剩余 ${config.retryCount} 次)`);
        await this.delay(config.retryDelay || 1000);
        return this.request({
          ...config,
          retryCount: config.retryCount - 1,
        });
      }

      throw normalizedError;
    }
  }

  /**
   * 执行实际的网络请求
   * @param {RequestConfig} config - 请求配置
   * @returns {Promise<ResponseData>}
   */
  performRequest(config) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: config.url,
        method: config.method || 'GET',
        data: config.data,
        header: config.header,
        timeout: config.timeout || this.timeout,
        success: (res) => {
          // 检查 HTTP 状态码
          if (res.statusCode >= 200 && res.statusCode < 300) {
            // 检查业务状态码
            const data = res.data;
            if (data && typeof data === 'object') {
              // 后端返回统一格式 { success, data, message, error }
              if (data.success === false) {
                // 业务错误
                reject({
                  code: data.error?.code || 'BUSINESS_ERROR',
                  message: data.error?.message || data.message || '请求失败',
                  details: data.error,
                });
              } else {
                // 成功响应
                resolve(data);
              }
            } else {
              // 非标准响应格式，直接返回
              resolve({ success: true, data: res.data });
            }
          } else {
            // HTTP 错误
            reject({
              code: `HTTP_${res.statusCode}`,
              message: this.getHttpErrorMessage(res.statusCode),
              statusCode: res.statusCode,
            });
          }
        },
        fail: (error) => {
          // 网络错误
          reject({
            code: 'NETWORK_ERROR',
            message: error.errMsg || '网络请求失败',
            details: error,
          });
        },
      });
    });
  }

  /**
   * 检查网络状态
   * @returns {Promise<{isConnected: boolean, networkType: string}>}
   */
  checkNetworkStatus() {
    return new Promise((resolve) => {
      wx.getNetworkType({
        success: (res) => {
          resolve({
            isConnected: res.networkType !== 'none',
            networkType: res.networkType,
          });
        },
        fail: () => {
          resolve({
            isConnected: true, // 默认假设网络可用
            networkType: 'unknown',
          });
        },
      });
    });
  }

  /**
   * 标准化错误对象
   * @param {*} error - 错误对象
   * @returns {Object} 标准化的错误对象
   */
  normalizeError(error) {
    if (typeof error === 'object' && error.code && error.message) {
      return error;
    }

    if (typeof error === 'string') {
      return {
        code: 'UNKNOWN_ERROR',
        message: error,
      };
    }

    return {
      code: 'UNKNOWN_ERROR',
      message: error?.errMsg || error?.message || '未知错误',
      details: error,
    };
  }

  /**
   * 获取 HTTP 错误消息
   * @param {number} statusCode - HTTP 状态码
   * @returns {string} 错误消息
   */
  getHttpErrorMessage(statusCode) {
    const errorMessages = {
      400: '请求参数错误',
      401: '未授权，请重新登录',
      403: '没有权限访问',
      404: '请求的资源不存在',
      408: '请求超时',
      413: '请求数据过大',
      429: '请求过于频繁，请稍后再试',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务暂时不可用',
      504: '网关超时',
    };

    return errorMessages[statusCode] || `请求失败 (${statusCode})`;
  }

  /**
   * 延迟执行
   * @param {number} ms - 延迟时间（毫秒）
   * @returns {Promise<void>}
   */
  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * GET 请求
   * @param {string} url - 请求路径
   * @param {Object} params - 查询参数
   * @param {RequestConfig} config - 其他配置
   * @returns {Promise<ResponseData>}
   */
  get(url, params = {}, config = {}) {
    // 构建查询字符串
    const queryString = Object.keys(params)
      .filter((key) => params[key] !== undefined && params[key] !== null)
      .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join('&');

    const fullUrl = queryString ? `${url}?${queryString}` : url;

    return this.request({
      url: fullUrl,
      method: 'GET',
      ...config,
    });
  }

  /**
   * POST 请求
   * @param {string} url - 请求路径
   * @param {Object} data - 请求数据
   * @param {RequestConfig} config - 其他配置
   * @returns {Promise<ResponseData>}
   */
  post(url, data = {}, config = {}) {
    return this.request({
      url,
      method: 'POST',
      data,
      ...config,
    });
  }

  /**
   * PUT 请求
   * @param {string} url - 请求路径
   * @param {Object} data - 请求数据
   * @param {RequestConfig} config - 其他配置
   * @returns {Promise<ResponseData>}
   */
  put(url, data = {}, config = {}) {
    return this.request({
      url,
      method: 'PUT',
      data,
      ...config,
    });
  }

  /**
   * DELETE 请求
   * @param {string} url - 请求路径
   * @param {Object} params - 查询参数
   * @param {RequestConfig} config - 其他配置
   * @returns {Promise<ResponseData>}
   */
  delete(url, params = {}, config = {}) {
    const queryString = Object.keys(params)
      .filter((key) => params[key] !== undefined && params[key] !== null)
      .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join('&');

    const fullUrl = queryString ? `${url}?${queryString}` : url;

    return this.request({
      url: fullUrl,
      method: 'DELETE',
      ...config,
    });
  }

  /**
   * 文件上传
   * @param {string} url - 上传地址
   * @param {string} filePath - 本地文件路径
   * @param {string} [name='file'] - 文件对应的 key
   * @param {Object} [formData] - 额外的表单数据
   * @param {RequestConfig} [config] - 其他配置
   * @returns {Promise<ResponseData>}
   */
  upload(url, filePath, name = 'file', formData = {}, config = {}) {
    return new Promise(async (resolve, reject) => {
      try {
        // 运行请求拦截器
        const processedConfig = await this.runRequestInterceptors({
          url,
          ...config,
        });

        const fullUrl = this.buildUrl(processedConfig.url);

        // 显示加载提示
        if (config.showLoading) {
          this.showLoading(config.loadingText || '上传中...');
        }

        const uploadTask = wx.uploadFile({
          url: fullUrl,
          filePath,
          name,
          formData,
          header: processedConfig.header,
          success: (res) => {
            if (config.showLoading) {
              this.hideLoading();
            }

            if (res.statusCode >= 200 && res.statusCode < 300) {
              try {
                const data = JSON.parse(res.data);
                resolve(data);
              } catch (error) {
                resolve({ success: true, data: res.data });
              }
            } else {
              reject({
                code: `HTTP_${res.statusCode}`,
                message: this.getHttpErrorMessage(res.statusCode),
              });
            }
          },
          fail: (error) => {
            if (config.showLoading) {
              this.hideLoading();
            }
            reject({
              code: 'UPLOAD_ERROR',
              message: error.errMsg || '上传失败',
            });
          },
        });

        // 支持上传进度回调
        if (config.onProgress) {
          uploadTask.onProgressUpdate(config.onProgress);
        }
      } catch (error) {
        if (config.showLoading) {
          this.hideLoading();
        }
        reject(error);
      }
    });
  }

  /**
   * 获取统计信息
   * @returns {Object} 统计信息
   */
  getStats() {
    return { ...this.stats };
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      totalRequests: 0,
      successRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
    };
  }
}

// 创建单例实例
const request = new Request();

// 导出实例和类
module.exports = {
  request,
  Request,
};
