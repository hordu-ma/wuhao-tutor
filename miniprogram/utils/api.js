// utils/api.js
// 增强版API客户端 - 五好伴学微信小程序网络层架构

const config = require('../config/index.js');
const auth = require('./auth.js');
const storage = require('./storage.js');
const { networkMonitor } = require('./network-monitor.js');
const { cacheManager, CacheStrategy } = require('./cache-manager.js');
const { requestQueue, Priority } = require('./request-queue.js');
const { btoa } = require('./base64.js');

/**
 * 网络错误类型枚举
 */
const ErrorType = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  AUTH_ERROR: 'AUTH_ERROR',
  PERMISSION_ERROR: 'PERMISSION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  BUSINESS_ERROR: 'BUSINESS_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
};

/**
 * 重试策略枚举
 */
const RetryStrategy = {
  FIXED_DELAY: 'FIXED_DELAY',
  LINEAR_DELAY: 'LINEAR_DELAY',
  EXPONENTIAL_BACKOFF: 'EXPONENTIAL_BACKOFF',
  RANDOM_DELAY: 'RANDOM_DELAY',
};

/**
 * 增强版API客户端类
 */
class EnhancedApiClient {
  constructor() {
    this.baseUrl = config.api.baseUrl;
    this.timeout = config.api.timeout;
    this.version = config.api.version;

    // 请求拦截器
    this.requestInterceptors = [];
    // 响应拦截器
    this.responseInterceptors = [];

    // 请求统计
    this.stats = {
      totalRequests: 0,
      successRequests: 0,
      failedRequests: 0,
      cacheHits: 0,
      averageResponseTime: 0,
      startTime: Date.now(),
    };

    // 请求去重映射
    this.pendingRequests = new Map();

    // 事件监听器
    this.eventListeners = new Map();

    // 默认配置
    this.defaultConfig = {
      retry: {
        strategy: RetryStrategy.EXPONENTIAL_BACKOFF,
        maxRetries: 3,
        baseDelay: 1000,
        maxDelay: 10000,
        multiplier: 2,
        jitter: 0.1,
      },
      cache: {
        strategy: CacheStrategy.MEMORY_CACHE,
        ttl: 5 * 60 * 1000,
        enableCache: false,
      },
      queue: {
        enableQueue: true,
        priority: Priority.NORMAL,
        enableDeduplication: true,
      },
    };

    this.setupDefaultInterceptors();
    this.setupNetworkMonitoring();
  }

  /**
   * 设置默认拦截器
   */
  setupDefaultInterceptors() {
    // 请求拦截器 - 添加认证头
    this.addRequestInterceptor(async config => {
      try {
        if (!config.skipAuth) {
          const token = await auth.getToken();
          if (token) {
            config.header = {
              ...config.header,
              Authorization: `Bearer ${token}`,
            };
          }
        }
      } catch (error) {
        console.warn('获取token失败', error);
      }
      return config;
    });

    // 请求拦截器 - 添加公共头部
    this.addRequestInterceptor(config => {
      config.header = {
        'Content-Type': 'application/json',
        'X-Client-Type': 'miniprogram',
        'X-Client-Version': this.version,
        'X-Request-ID': this.generateRequestId(),
        'X-Timestamp': Date.now().toString(),
        ...config.header,
      };
      return config;
    });

    // 响应拦截器 - 统一错误处理
    this.addResponseInterceptor(
      response => response,
      async error => {
        // Token过期处理
        if (error.statusCode === 401) {
          try {
            await auth.refreshToken();
            // 重试原请求
            return this.request(error.config);
          } catch (refreshError) {
            // 刷新失败，跳转登录
            await auth.logout();
            this.emit('auth:logout');
            throw refreshError;
          }
        }

        // 限流处理
        if (error.statusCode === 429) {
          const retryAfter = error.header?.['retry-after'] || 1;
          await this.delay(retryAfter * 1000);
          return this.request(error.config);
        }

        throw error;
      },
    );
  }

  /**
   * 设置网络监控
   */
  setupNetworkMonitoring() {
    networkMonitor.addListener((currentStatus, previousStatus) => {
      this.emit('network:change', { currentStatus, previousStatus });

      // 网络从断开到连接时，重试失败的请求
      if (!previousStatus.isConnected && currentStatus.isConnected) {
        this.emit('network:reconnect');
      }

      // 网络质量变化时的处理
      const currentQuality = networkMonitor.getNetworkQuality();
      this.emit('network:quality', currentQuality);
    });
  }

  /**
   * 添加请求拦截器
   */
  addRequestInterceptor(fulfilled, rejected) {
    const interceptor = { fulfilled, rejected };
    this.requestInterceptors.push(interceptor);
    return () => {
      const index = this.requestInterceptors.indexOf(interceptor);
      if (index > -1) {
        this.requestInterceptors.splice(index, 1);
      }
    };
  }

  /**
   * 添加响应拦截器
   */
  addResponseInterceptor(fulfilled, rejected) {
    const interceptor = { fulfilled, rejected };
    this.responseInterceptors.push(interceptor);
    return () => {
      const index = this.responseInterceptors.indexOf(interceptor);
      if (index > -1) {
        this.responseInterceptors.splice(index, 1);
      }
    };
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
    // 合并默认配置
    let config = this.mergeConfig(options);

    // 生成请求ID
    config.requestId = config.requestId || this.generateRequestId();
    config.startTime = Date.now();

    try {
      // 检查网络状态
      await this.checkNetworkStatus(config);

      // 检查缓存
      if (config.enableCache && config.method === 'GET') {
        const cachedResponse = await this.getCachedResponse(config);
        if (cachedResponse) {
          this.stats.cacheHits++;
          this.updateStats(config, true);
          return cachedResponse;
        }
      }

      // 执行请求拦截器
      config = await this.runRequestInterceptors(config);

      // 处理URL
      if (!config.url.startsWith('http')) {
        // 检查URL是否已经包含/api/前缀
        if (config.url.startsWith('/api/')) {
          config.url = `${this.baseUrl}${config.url}`;
        } else {
          config.url = `${this.baseUrl}/api/${this.version}${config.url}`;
        }
      }

      // 请求去重检查
      if (config.enableDeduplication && config.method === 'GET') {
        const deduplicationKey = this.generateDeduplicationKey(config);
        if (this.pendingRequests.has(deduplicationKey)) {
          return this.pendingRequests.get(deduplicationKey);
        }
      }

      // 发送请求
      const responsePromise = this.executeRequest(config);

      // 添加到去重映射
      if (config.enableDeduplication && config.method === 'GET') {
        const deduplicationKey = this.generateDeduplicationKey(config);
        this.pendingRequests.set(deduplicationKey, responsePromise);
        responsePromise.finally(() => {
          this.pendingRequests.delete(deduplicationKey);
        });
      }

      const response = await responsePromise;

      // 缓存响应
      if (
        config.enableCache &&
        config.method === 'GET' &&
        response.statusCode >= 200 &&
        response.statusCode < 300
      ) {
        await this.cacheResponse(config, response);
      }

      // 更新统计
      this.updateStats(config, true);

      return response;
    } catch (error) {
      this.updateStats(config, false);
      throw this.normalizeError(error, config);
    }
  }

  /**
   * 执行请求
   */
  async executeRequest(config) {
    if (config.enableQueue) {
      // 使用队列执行请求
      return requestQueue.enqueue(() => this.performRequest(config), {
        priority: config.priority,
        timeout: config.timeout,
        retryCount: config.retry.maxRetries,
        metadata: { url: config.url, method: config.method },
      });
    } else {
      // 直接执行请求
      return this.performRequestWithRetry(config);
    }
  }

  /**
   * 带重试的请求执行
   */
  async performRequestWithRetry(config, currentRetry = 0) {
    try {
      return await this.performRequest(config);
    } catch (error) {
      // 判断是否需要重试
      if (currentRetry < config.retry.maxRetries && this.shouldRetry(error)) {
        const delay = this.calculateRetryDelay(config.retry, currentRetry);
        await this.delay(delay);
        return this.performRequestWithRetry(config, currentRetry + 1);
      }
      throw error;
    }
  }

  /**
   * 执行单次请求
   */
  performRequest(config) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const requestConfig = {
        url: config.url,
        method: config.method,
        data: config.data,
        header: config.header,
        timeout: config.timeout,
        dataType: config.dataType || 'json',
        responseType: config.responseType || 'text',
        success: res => {
          const endTime = Date.now();
          const duration = endTime - startTime;

          resolve({
            data: res.data,
            statusCode: res.statusCode,
            header: res.header,
            config,
            timestamp: endTime,
            duration,
          });
        },
        fail: error => {
          const endTime = Date.now();
          const duration = endTime - startTime;

          reject({
            statusCode: 0,
            message: error.errMsg || '网络请求失败',
            config,
            originalError: error,
            timestamp: endTime,
            duration,
            type: ErrorType.NETWORK_ERROR,
          });
        },
      };

      // 发出请求事件
      this.emit('request:start', { config, startTime });

      wx.request(requestConfig);
    });
  }

  /**
   * 检查网络状态
   */
  async checkNetworkStatus(config) {
    const networkStatus = networkMonitor.getCurrentStatus();

    if (!networkStatus.isConnected) {
      throw {
        type: ErrorType.NETWORK_ERROR,
        message: '网络未连接',
        statusCode: 0,
        config,
      };
    }

    // 检查网络是否适合当前操作
    const operationType = this.getOperationType(config);
    const suitability = networkMonitor.isNetworkSuitableFor(operationType);

    if (!suitability.suitable) {
      console.warn('网络状况不佳', suitability.reason);
      // 如果是非关键操作，可以考虑延迟或取消
      if (config.priority === Priority.LOW) {
        throw {
          type: ErrorType.NETWORK_ERROR,
          message: suitability.reason,
          statusCode: 0,
          config,
        };
      }
    }
  }

  /**
   * 获取操作类型
   */
  getOperationType(config) {
    if (config.url.includes('/upload')) {
      return config.data && this.calculateSize(config.data) > 1024 * 1024
        ? 'large_download'
        : 'image_upload';
    }
    if (config.url.includes('/chat')) {
      return 'chat';
    }
    if (config.method === 'POST' || config.method === 'PUT') {
      return 'file_upload';
    }
    return 'chat';
  }

  /**
   * 获取缓存响应
   */
  async getCachedResponse(config) {
    try {
      const cacheKey = this.generateCacheKey(config);
      const cachedData = await cacheManager.get(cacheKey, {
        strategy: config.cache.strategy,
      });

      if (cachedData) {
        return {
          data: cachedData,
          statusCode: 200,
          header: {},
          config,
          timestamp: Date.now(),
          duration: 0,
          fromCache: true,
        };
      }
    } catch (error) {
      console.warn('获取缓存失败', error);
    }
    return null;
  }

  /**
   * 缓存响应
   */
  async cacheResponse(config, response) {
    try {
      const cacheKey = this.generateCacheKey(config);
      await cacheManager.set(cacheKey, response.data, {
        strategy: config.cache.strategy,
        ttl: config.cache.ttl,
        tags: config.cache.tags || [],
      });
    } catch (error) {
      console.warn('缓存响应失败', error);
    }
  }

  /**
   * 生成缓存键
   */
  generateCacheKey(config) {
    const url = config.url;
    const params = config.data ? JSON.stringify(config.data) : '';
    const userRole = auth.getUserRole?.() || 'anonymous';
    // 使用微信小程序兼容的 btoa 替代浏览器 API
    return `api_${userRole}_${btoa(url + params).replace(/[^a-zA-Z0-9]/g, '')}`;
  }

  /**
   * 生成去重键
   */
  generateDeduplicationKey(config) {
    return this.generateCacheKey(config);
  }

  /**
   * 判断是否应该重试
   */
  shouldRetry(error) {
    // 网络错误重试
    if (error.statusCode === 0 || error.type === ErrorType.NETWORK_ERROR) {
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

    // 超时错误重试
    if (error.type === ErrorType.TIMEOUT_ERROR) {
      return true;
    }

    return false;
  }

  /**
   * 计算重试延迟
   */
  calculateRetryDelay(retryConfig, currentRetry) {
    let delay;

    switch (retryConfig.strategy) {
      case RetryStrategy.FIXED_DELAY:
        delay = retryConfig.baseDelay;
        break;
      case RetryStrategy.LINEAR_DELAY:
        delay = retryConfig.baseDelay * (currentRetry + 1);
        break;
      case RetryStrategy.EXPONENTIAL_BACKOFF:
        delay = retryConfig.baseDelay * Math.pow(retryConfig.multiplier, currentRetry);
        break;
      case RetryStrategy.RANDOM_DELAY:
        delay = retryConfig.baseDelay + Math.random() * retryConfig.baseDelay;
        break;
      default:
        delay = retryConfig.baseDelay;
    }

    // 添加抖动
    if (retryConfig.jitter > 0) {
      const jitterAmount = delay * retryConfig.jitter;
      delay += (Math.random() * 2 - 1) * jitterAmount;
    }

    // 限制最大延迟
    return Math.min(delay, retryConfig.maxDelay);
  }

  /**
   * 合并配置
   */
  mergeConfig(options) {
    return {
      url: '',
      method: 'GET',
      data: null,
      header: {},
      timeout: this.timeout,
      skipAuth: false,
      enableCache: this.defaultConfig.cache.enableCache,
      enableQueue: this.defaultConfig.queue.enableQueue,
      enableDeduplication: this.defaultConfig.queue.enableDeduplication,
      priority: this.defaultConfig.queue.priority,
      retry: { ...this.defaultConfig.retry },
      cache: { ...this.defaultConfig.cache },
      ...options,
    };
  }

  /**
   * 标准化错误
   */
  normalizeError(error, config) {
    const normalizedError = {
      type: error.type || ErrorType.UNKNOWN_ERROR,
      message: error.message || '未知错误',
      statusCode: error.statusCode || 0,
      data: error.data,
      config,
      timestamp: Date.now(),
      originalError: error,
    };

    // 根据状态码确定错误类型
    if (normalizedError.statusCode === 401) {
      normalizedError.type = ErrorType.AUTH_ERROR;
    } else if (normalizedError.statusCode === 403) {
      normalizedError.type = ErrorType.PERMISSION_ERROR;
    } else if (normalizedError.statusCode >= 400 && normalizedError.statusCode < 500) {
      normalizedError.type = ErrorType.VALIDATION_ERROR;
    } else if (normalizedError.statusCode >= 500) {
      normalizedError.type = ErrorType.SERVER_ERROR;
    }

    // 发出错误事件
    this.emit('request:error', normalizedError);

    return normalizedError;
  }

  /**
   * 更新统计信息
   */
  updateStats(config, success) {
    this.stats.totalRequests++;

    if (success) {
      this.stats.successRequests++;
    } else {
      this.stats.failedRequests++;
    }

    // 更新平均响应时间
    if (config.startTime) {
      const responseTime = Date.now() - config.startTime;
      const totalResponses = this.stats.successRequests + this.stats.failedRequests;
      this.stats.averageResponseTime =
        (this.stats.averageResponseTime * (totalResponses - 1) + responseTime) / totalResponses;
    }
  }

  /**
   * 事件发射
   */
  emit(eventType, data) {
    const listeners = this.eventListeners.get(eventType) || [];
    listeners.forEach(listener => {
      try {
        listener(data);
      } catch (error) {
        console.error('事件监听器执行失败', error);
      }
    });
  }

  /**
   * 添加事件监听器
   */
  on(eventType, listener) {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    this.eventListeners.get(eventType).push(listener);

    return () => {
      const listeners = this.eventListeners.get(eventType) || [];
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }

  /**
   * 移除事件监听器
   */
  off(eventType, listener) {
    const listeners = this.eventListeners.get(eventType) || [];
    const index = listeners.indexOf(listener);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  /**
   * 生成请求ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 延迟函数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 计算数据大小
   */
  calculateSize(data) {
    try {
      const str = typeof data === 'string' ? data : JSON.stringify(data);
      return new Blob([str]).size;
    } catch (error) {
      const str = typeof data === 'string' ? data : JSON.stringify(data);
      return str.length * 2;
    }
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
      ...options,
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
      ...options,
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
      ...options,
    });
  }

  /**
   * DELETE请求
   */
  delete(url, options = {}) {
    return this.request({
      url,
      method: 'DELETE',
      ...options,
    });
  }

  /**
   * PATCH请求
   */
  patch(url, data = {}, options = {}) {
    return this.request({
      url,
      method: 'PATCH',
      data,
      ...options,
    });
  }

  /**
   * 构建查询字符串
   */
  buildQueryString(params) {
    const queryParts = [];

    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => {
            queryParts.push(`${encodeURIComponent(key)}[]=${encodeURIComponent(item)}`);
          });
        } else {
          queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
        }
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
        // 检查网络状态
        const networkStatus = networkMonitor.getCurrentStatus();
        if (!networkStatus.isConnected) {
          reject({
            type: ErrorType.NETWORK_ERROR,
            message: '网络未连接',
            statusCode: 0,
          });
          return;
        }

        // 检查文件路径
        if (!filePath) {
          reject({
            type: ErrorType.VALIDATION_ERROR,
            message: '文件路径不能为空',
            statusCode: 400,
          });
          return;
        }

        // 获取认证头
        const token = await auth.getToken();
        const header = {
          'X-Client-Type': 'miniprogram',
          'X-Client-Version': this.version,
          'X-Request-ID': this.generateRequestId(),
          ...options.header,
        };

        if (token && !options.skipAuth) {
          header['Authorization'] = `Bearer ${token}`;
        }

        const uploadConfig = {
          url: url.startsWith('http') ? url : `${this.baseUrl}/api/${this.version}${url}`,
          filePath,
          name: options.name || 'file',
          formData: options.formData || {},
          header,
          success: res => {
            if (res.statusCode >= 200 && res.statusCode < 300) {
              try {
                const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
                resolve({
                  data,
                  statusCode: res.statusCode,
                  header: res.header,
                  timestamp: Date.now(),
                });
              } catch (parseError) {
                resolve({
                  data: res.data,
                  statusCode: res.statusCode,
                  header: res.header,
                  timestamp: Date.now(),
                });
              }
            } else {
              reject({
                statusCode: res.statusCode,
                data: res.data,
                message: `HTTP ${res.statusCode}`,
                type: ErrorType.SERVER_ERROR,
              });
            }
          },
          fail: error => {
            reject({
              statusCode: 0,
              message: error.errMsg || '文件上传失败',
              originalError: error,
              type: ErrorType.NETWORK_ERROR,
            });
          },
        };

        // 上传进度回调
        if (options.onProgress) {
          const uploadTask = wx.uploadFile(uploadConfig);
          uploadTask.onProgressUpdate(res => {
            options.onProgress({
              loaded: res.totalBytesSent,
              total: res.totalBytesExpectedToSend,
              progress: res.progress,
              speed: 0, // 微信小程序API不提供速度信息
              timeRemaining: 0,
            });
          });
        } else {
          wx.uploadFile(uploadConfig);
        }
      } catch (error) {
        reject(this.normalizeError(error));
      }
    });
  }

  /**
   * 下载文件
   */
  download(url, options = {}) {
    return new Promise(async (resolve, reject) => {
      try {
        // 检查网络状态
        const networkStatus = networkMonitor.getCurrentStatus();
        if (!networkStatus.isConnected) {
          reject({
            type: ErrorType.NETWORK_ERROR,
            message: '网络未连接',
            statusCode: 0,
          });
          return;
        }

        // 获取认证头
        const token = await auth.getToken();
        const header = {
          'X-Client-Type': 'miniprogram',
          'X-Client-Version': this.version,
          'X-Request-ID': this.generateRequestId(),
          ...options.header,
        };

        if (token && !options.skipAuth) {
          header['Authorization'] = `Bearer ${token}`;
        }

        const downloadConfig = {
          url: url.startsWith('http') ? url : `${this.baseUrl}/api/${this.version}${url}`,
          filePath: options.filePath,
          header,
          success: res => {
            resolve({
              tempFilePath: res.tempFilePath,
              statusCode: res.statusCode,
              header: res.header,
              timestamp: Date.now(),
            });
          },
          fail: error => {
            reject({
              statusCode: 0,
              message: error.errMsg || '文件下载失败',
              originalError: error,
              type: ErrorType.NETWORK_ERROR,
            });
          },
        };

        // 无论是否有进度回调，都保存 downloadTask 引用，防止任务被 unbind
        const downloadTask = wx.downloadFile(downloadConfig);

        // 如果有进度回调，注册监听器
        if (options.onProgress) {
          downloadTask.onProgressUpdate(res => {
            options.onProgress({
              loaded: res.totalBytesWritten,
              total: res.totalBytesExpectedToWrite,
              progress: res.progress,
              speed: 0, // 微信小程序API不提供速度信息
              timeRemaining: 0,
            });
          });
        }
      } catch (error) {
        reject(this.normalizeError(error));
      }
    });
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      ...this.stats,
      uptime: Date.now() - this.stats.startTime,
      successRate:
        this.stats.totalRequests > 0
          ? ((this.stats.successRequests / this.stats.totalRequests) * 100).toFixed(2)
          : '0.00',
      cacheHitRate:
        this.stats.totalRequests > 0
          ? ((this.stats.cacheHits / this.stats.totalRequests) * 100).toFixed(2)
          : '0.00',
      queueStatus: requestQueue.getStatus(),
      networkStatus: networkMonitor.getCurrentStatus(),
    };
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      totalRequests: 0,
      successRequests: 0,
      failedRequests: 0,
      cacheHits: 0,
      averageResponseTime: 0,
      startTime: Date.now(),
    };
  }

  /**
   * 设置默认配置
   */
  setDefaults(config) {
    this.defaultConfig = { ...this.defaultConfig, ...config };
  }

  /**
   * 清理资源
   */
  destroy() {
    this.requestInterceptors = [];
    this.responseInterceptors = [];
    this.pendingRequests.clear();
    this.eventListeners.clear();
    console.log('API客户端已销毁');
  }
}

// 创建单例实例
const apiClient = new EnhancedApiClient();

/**
 * API接口定义
 */
const api = {
  // 用户认证相关
  auth: {
    // 微信登录
    wechatLogin: data => apiClient.post('/auth/wechat-login', data),
    // 刷新Token
    refreshToken: data => apiClient.post('/auth/refresh-token', data),
    // 登出
    logout: () => apiClient.post('/auth/logout'),
    // 获取用户信息
    getUserInfo: () =>
      apiClient.get('/auth/user-info', {}, { enableCache: true, cache: { ttl: 10 * 60 * 1000 } }),
    // 更新用户信息
    updateUserInfo: data => apiClient.put('/auth/user-info', data),
  },

  // 作业相关
  homework: {
    // 获取作业列表
    getList: params =>
      apiClient.get('/homework', params, {
        enableCache: true,
        cache: { ttl: 2 * 60 * 1000, tags: ['homework'] },
      }),
    // 获取作业详情
    getDetail: id =>
      apiClient.get(
        `/homework/${id}`,
        {},
        {
          enableCache: true,
          cache: { ttl: 5 * 60 * 1000, tags: ['homework', `homework:${id}`] },
        },
      ),
    // 提交作业
    submit: (id, data) =>
      apiClient.post(`/homework/${id}/submit`, data, {
        priority: Priority.HIGH,
        retry: { maxRetries: 2 },
      }),
    // 创建作业（教师）
    create: data => apiClient.post('/homework', data, { priority: Priority.HIGH }),
    // 更新作业（教师）
    update: (id, data) => apiClient.put(`/homework/${id}`, data),
    // 删除作业（教师）
    delete: id => apiClient.delete(`/homework/${id}`),
    // 批改作业（教师）
    grade: (id, data) => apiClient.post(`/homework/${id}/grade`, data, { priority: Priority.HIGH }),
  },

  // AI问答相关
  chat: {
    // 发送消息
    sendMessage: data =>
      apiClient.post('/chat/message', data, {
        priority: Priority.HIGH,
        timeout: 30000,
        retry: { maxRetries: 1 },
      }),
    // 获取对话历史
    getHistory: params =>
      apiClient.get('/chat/history', params, {
        enableCache: true,
        cache: { ttl: 1 * 60 * 1000, tags: ['chat'] },
      }),
    // 获取对话详情
    getSession: sessionId =>
      apiClient.get(
        `/chat/session/${sessionId}`,
        {},
        {
          enableCache: true,
          cache: { ttl: 5 * 60 * 1000, tags: ['chat', `session:${sessionId}`] },
        },
      ),
    // 创建新对话
    createSession: data => apiClient.post('/chat/session', data),
    // 删除对话
    deleteSession: sessionId => apiClient.delete(`/chat/session/${sessionId}`),
  },

  // 学情分析相关
  analysis: {
    // 获取学习报告
    getReport: params =>
      apiClient.get('/analysis/report', params, {
        enableCache: true,
        cache: { ttl: 10 * 60 * 1000, tags: ['analysis'] },
      }),
    // 获取学习进度
    getProgress: params =>
      apiClient.get('/analysis/progress', params, {
        enableCache: true,
        cache: { ttl: 5 * 60 * 1000, tags: ['analysis'] },
      }),
    // 获取知识点掌握情况
    getKnowledgePoints: params =>
      apiClient.get('/analysis/knowledge-points', params, {
        enableCache: true,
        cache: { ttl: 10 * 60 * 1000, tags: ['analysis'] },
      }),
    // 获取学习统计
    getStatistics: params =>
      apiClient.get('/analysis/statistics', params, {
        enableCache: true,
        cache: { ttl: 15 * 60 * 1000, tags: ['analysis'] },
      }),
  },

  // 文件上传相关
  upload: {
    // 上传图片
    image: (filePath, options = {}) =>
      apiClient.upload('/upload/image', filePath, {
        name: 'image',
        priority: Priority.NORMAL,
        ...options,
      }),
    // 上传文件
    file: (filePath, options = {}) =>
      apiClient.upload('/upload/file', filePath, {
        name: 'file',
        priority: Priority.NORMAL,
        ...options,
      }),
  },

  // 用户设置相关
  settings: {
    // 获取设置

    get: () =>
      apiClient.get(
        '/settings',
        {},
        {
          enableCache: true,
          cache: { ttl: 30 * 60 * 1000, tags: ['settings'] },
        },
      ),
    // 更新设置
    update: data => apiClient.put('/settings', data),
    // 获取消息设置
    getNotification: () =>
      apiClient.get(
        '/settings/notification',
        {},
        {
          enableCache: true,
          cache: { ttl: 30 * 60 * 1000, tags: ['settings'] },
        },
      ),
    // 更新消息设置
    updateNotification: data => apiClient.put('/settings/notification', data),
  },

  // 反馈相关
  feedback: {
    // 提交反馈
    submit: data => apiClient.post('/feedback', data, { priority: Priority.LOW }),
    // 获取反馈列表
    getList: params => apiClient.get('/feedback', params, { priority: Priority.LOW }),
  },

  // 系统相关
  system: {
    // 获取系统信息
    getInfo: () =>
      apiClient.get(
        '/system/info',
        {},
        {
          enableCache: true,
          cache: { ttl: 60 * 60 * 1000, tags: ['system'] },
        },
      ),
    // 检查更新
    checkUpdate: () => apiClient.get('/system/update'),
    // 获取公告
    getNotices: params =>
      apiClient.get('/system/notices', params, {
        enableCache: true,
        cache: { ttl: 10 * 60 * 1000, tags: ['system'] },
      }),
  },
};

// 兼容性封装
const compatApi = {
  // 作业相关 - 兼容旧版本调用方式
  getHomeworkList: api.homework.getList,
  getHomeworkDetail: api.homework.getDetail,
  submitHomework: data => api.homework.submit(data.homeworkId, data),
  createHomework: api.homework.create,
  updateHomework: data => api.homework.update(data.id, data),
  deleteHomework: api.homework.delete,
  gradeHomework: data => api.homework.grade(data.homeworkId, data),

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
  // 核心类和实例
  EnhancedApiClient,
  apiClient,

  // 接口定义
  api,

  // 兼容性接口
  ...compatApi,

  // 常量
  ErrorType,
  RetryStrategy,
  Priority,
  CacheStrategy,

  // 工具方法
  addRequestInterceptor: (fulfilled, rejected) =>
    apiClient.addRequestInterceptor(fulfilled, rejected),
  addResponseInterceptor: (fulfilled, rejected) =>
    apiClient.addResponseInterceptor(fulfilled, rejected),
  setDefaults: config => apiClient.setDefaults(config),
  getStats: () => apiClient.getStats(),
  resetStats: () => apiClient.resetStats(),
  on: (eventType, listener) => apiClient.on(eventType, listener),
  off: (eventType, listener) => apiClient.off(eventType, listener),

  // 便捷方法
  get: (url, params, options) => apiClient.get(url, params, options),
  post: (url, data, options) => apiClient.post(url, data, options),
  put: (url, data, options) => apiClient.put(url, data, options),
  delete: (url, options) => apiClient.delete(url, options),
  patch: (url, data, options) => apiClient.patch(url, data, options),
  upload: (url, filePath, options) => apiClient.upload(url, filePath, options),
  download: (url, options) => apiClient.download(url, options),

  // 缓存管理
  clearCache: tags => cacheManager.deleteByTags(tags),
  clearAllCache: () => cacheManager.clear(),

  // 队列管理
  getQueueStatus: () => requestQueue.getStatus(),
  pauseQueue: () => requestQueue.pause(),
  resumeQueue: () => requestQueue.resume(),
  clearQueue: () => requestQueue.clear(),

  // 网络监控
  getNetworkStatus: () => networkMonitor.getCurrentStatus(),
  getNetworkQuality: () => networkMonitor.getNetworkQuality(),
  refreshNetworkStatus: () => networkMonitor.refresh(),
};
