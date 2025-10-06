// 性能优化工具模块
// 提供页面加载优化、内存管理、网络请求优化等功能

/**
 * 页面预加载管理器
 * 实现关键页面的预加载，提升用户体验
 */
class PreloadManager {
  constructor() {
    this.preloadedPages = new Map();
    this.preloadQueue = [];
    this.maxPreloadSize = 3; // 最大预加载页面数
  }

  /**
   * 预加载页面
   * @param {string} path 页面路径
   * @param {object} options 预加载选项
   */
  async preloadPage(path, options = {}) {
    if (this.preloadedPages.has(path)) {
      console.log(`页面已预加载: ${path}`);
      return;
    }

    try {
      console.log(`开始预加载页面: ${path}`);
      
      // 预加载页面数据
      if (options.data && typeof options.data === 'function') {
        const data = await options.data();
        this.preloadedPages.set(path, {
          data,
          timestamp: Date.now(),
          ttl: options.ttl || 300000, // 默认5分钟过期
        });
      }

      // 预加载页面组件
      if (options.components) {
        await this.preloadComponents(options.components);
      }

      console.log(`页面预加载完成: ${path}`);
    } catch (error) {
      console.error(`页面预加载失败: ${path}`, error);
    }
  }

  /**
   * 预加载组件
   * @param {Array} components 组件列表
   */
  async preloadComponents(components) {
    const promises = components.map(async component => {
      try {
        // 预加载组件资源
        return await require(component);
      } catch (error) {
        console.warn(`组件预加载失败: ${component}`, error);
        return null;
      }
    });

    await Promise.allSettled(promises);
  }

  /**
   * 获取预加载的页面数据
   * @param {string} path 页面路径
   */
  getPreloadedData(path) {
    const cached = this.preloadedPages.get(path);
    if (!cached) return null;

    // 检查数据是否过期
    if (Date.now() - cached.timestamp > cached.ttl) {
      this.preloadedPages.delete(path);
      return null;
    }

    return cached.data;
  }

  /**
   * 清理过期的预加载数据
   */
  cleanup() {
    const now = Date.now();
    for (const [path, cached] of this.preloadedPages) {
      if (now - cached.timestamp > cached.ttl) {
        this.preloadedPages.delete(path);
        console.log(`清理过期预加载数据: ${path}`);
      }
    }
  }

  /**
   * 智能预加载
   * 根据用户行为模式预测并预加载可能访问的页面
   */
  intelligentPreload(currentPath, userBehavior = {}) {
    const preloadRules = {
      '/pages/homework/list/index': [
        '/pages/homework/detail/index',
        '/pages/homework/result/index'
      ],
      '/pages/qa/chat/index': [
        '/pages/qa/history/index'
      ],
      '/pages/analysis/overview/index': [
        '/pages/analysis/report/index'
      ]
    };

    const candidatePages = preloadRules[currentPath] || [];
    
    // 基于用户行为优化预加载优先级
    candidatePages.forEach(page => {
      if (this.preloadedPages.size < this.maxPreloadSize) {
        this.preloadPage(page, {
          data: this.getPageDataLoader(page),
          ttl: 600000 // 10分钟
        });
      }
    });
  }

  /**
   * 获取页面数据加载器
   * @param {string} pagePath 页面路径
   */
  getPageDataLoader(pagePath) {
    const loaderMap = {
      '/pages/homework/detail/index': () => this.preloadHomeworkDetail(),
      '/pages/analysis/report/index': () => this.preloadAnalysisReport(),
    };

    return loaderMap[pagePath] || null;
  }

  /**
   * 预加载作业详情数据
   */
  async preloadHomeworkDetail() {
    const api = require('../api/index.js');
    try {
      // 预加载最近的作业列表
      const result = await api.homework.getList({ limit: 5 });
      return result.data;
    } catch (error) {
      console.warn('预加载作业详情失败', error);
      return null;
    }
  }

  /**
   * 预加载分析报告数据
   */
  async preloadAnalysisReport() {
    const api = require('../api/index.js');
    try {
      // 预加载基础分析数据
      const result = await api.analysis.getOverview({ days: 30 });
      return result.data;
    } catch (error) {
      console.warn('预加载分析报告失败', error);
      return null;
    }
  }
}

/**
 * 内存优化管理器
 * 管理页面栈、数据缓存，避免内存泄漏
 */
class MemoryManager {
  constructor() {
    this.pageStack = [];
    this.dataCache = new Map();
    this.maxCacheSize = 50; // 最大缓存项数
    this.maxPageStack = 10; // 最大页面栈深度
  }

  /**
   * 页面进入时的内存管理
   * @param {string} path 页面路径
   * @param {object} data 页面数据
   */
  onPageEnter(path, data = {}) {
    // 管理页面栈
    this.pageStack.push({
      path,
      timestamp: Date.now(),
      dataSize: this.calculateDataSize(data)
    });

    // 限制页面栈深度
    if (this.pageStack.length > this.maxPageStack) {
      const removed = this.pageStack.shift();
      console.log(`移除页面栈底页面: ${removed.path}`);
      this.cleanupPageData(removed.path);
    }

    // 内存警告检查
    this.checkMemoryUsage();
  }

  /**
   * 页面离开时的内存清理
   * @param {string} path 页面路径
   */
  onPageLeave(path) {
    // 清理非关键页面数据
    if (!this.isCriticalPage(path)) {
      this.cleanupPageData(path);
    }

    // 从页面栈中移除
    this.pageStack = this.pageStack.filter(page => page.path !== path);
  }

  /**
   * 计算数据大小（粗略估算）
   * @param {*} data 数据对象
   */
  calculateDataSize(data) {
    try {
      return JSON.stringify(data).length;
    } catch (error) {
      return 0;
    }
  }

  /**
   * 判断是否为关键页面
   * @param {string} path 页面路径
   */
  isCriticalPage(path) {
    const criticalPages = [
      '/pages/index/index',
      '/pages/homework/list/index',
      '/pages/qa/chat/index'
    ];
    return criticalPages.includes(path);
  }

  /**
   * 清理页面数据
   * @param {string} path 页面路径
   */
  cleanupPageData(path) {
    // 清理相关缓存
    for (const key of this.dataCache.keys()) {
      if (key.startsWith(path)) {
        this.dataCache.delete(key);
      }
    }

    // 触发垃圾回收（如果支持）
    if (wx.triggerGC) {
      wx.triggerGC();
    }
  }

  /**
   * 检查内存使用情况
   */
  checkMemoryUsage() {
    const totalDataSize = this.pageStack.reduce((sum, page) => sum + page.dataSize, 0);
    const cacheSize = this.dataCache.size;

    // 内存使用警告
    if (totalDataSize > 1024 * 1024) { // 1MB
      console.warn('页面数据使用过多内存，考虑清理');
      this.performMemoryCleanup();
    }

    if (cacheSize > this.maxCacheSize) {
      console.warn('缓存项过多，执行清理');
      this.performCacheCleanup();
    }
  }

  /**
   * 执行内存清理
   */
  performMemoryCleanup() {
    // 清理最老的非关键页面
    const oldPages = this.pageStack
      .filter(page => !this.isCriticalPage(page.path))
      .sort((a, b) => a.timestamp - b.timestamp);

    if (oldPages.length > 0) {
      const pageToClean = oldPages[0];
      this.cleanupPageData(pageToClean.path);
      console.log(`执行内存清理: ${pageToClean.path}`);
    }
  }

  /**
   * 执行缓存清理
   */
  performCacheCleanup() {
    // 清理最老的缓存项
    const entries = Array.from(this.dataCache.entries());
    entries.sort((a, b) => (a[1].timestamp || 0) - (b[1].timestamp || 0));
    
    const itemsToRemove = entries.slice(0, Math.floor(this.maxCacheSize * 0.3));
    itemsToRemove.forEach(([key]) => {
      this.dataCache.delete(key);
    });

    console.log(`清理缓存项: ${itemsToRemove.length} 个`);
  }

  /**
   * 设置缓存数据
   * @param {string} key 缓存键
   * @param {*} data 缓存数据
   * @param {number} ttl 生存时间(ms)
   */
  setCache(key, data, ttl = 300000) {
    this.dataCache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });

    // 检查缓存大小
    if (this.dataCache.size > this.maxCacheSize) {
      this.performCacheCleanup();
    }
  }

  /**
   * 获取缓存数据
   * @param {string} key 缓存键
   */
  getCache(key) {
    const cached = this.dataCache.get(key);
    if (!cached) return null;

    // 检查是否过期
    if (Date.now() - cached.timestamp > cached.ttl) {
      this.dataCache.delete(key);
      return null;
    }

    return cached.data;
  }
}

/**
 * 网络请求优化管理器
 * 实现请求去重、批量请求、智能重试等功能
 */
class NetworkOptimizer {
  constructor() {
    this.pendingRequests = new Map();
    this.requestQueue = [];
    this.batchTimer = null;
    this.retryDelays = [1000, 2000, 5000]; // 重试延迟配置
  }

  /**
   * 优化后的请求方法
   * @param {string} url 请求URL
   * @param {object} options 请求选项
   */
  async request(url, options = {}) {
    const requestKey = this.generateRequestKey(url, options);

    // 请求去重
    if (this.pendingRequests.has(requestKey)) {
      console.log(`复用进行中的请求: ${url}`);
      return this.pendingRequests.get(requestKey);
    }

    const requestPromise = this.executeRequest(url, options);
    this.pendingRequests.set(requestKey, requestPromise);

    try {
      const result = await requestPromise;
      return result;
    } finally {
      this.pendingRequests.delete(requestKey);
    }
  }

  /**
   * 执行网络请求
   * @param {string} url 请求URL
   * @param {object} options 请求选项
   */
  async executeRequest(url, options) {
    const { retries = 3, timeout = 10000, ...requestOptions } = options;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        console.log(`请求尝试 ${attempt + 1}/${retries + 1}: ${url}`);
        
        const result = await this.performRequest(url, {
          ...requestOptions,
          timeout
        });

        // 请求成功
        if (attempt > 0) {
          console.log(`请求重试成功: ${url}`);
        }
        
        return result;
      } catch (error) {
        console.warn(`请求失败 (${attempt + 1}/${retries + 1}): ${url}`, error);

        // 如果是最后一次尝试，抛出错误
        if (attempt === retries) {
          throw error;
        }

        // 根据错误类型决定是否重试
        if (!this.shouldRetry(error)) {
          throw error;
        }

        // 等待重试延迟
        if (attempt < retries) {
          const delay = this.retryDelays[attempt] || this.retryDelays[this.retryDelays.length - 1];
          await this.delay(delay);
        }
      }
    }
  }

  /**
   * 执行单个网络请求
   * @param {string} url 请求URL
   * @param {object} options 请求选项
   */
  performRequest(url, options) {
    return new Promise((resolve, reject) => {
      const requestOptions = {
        url,
        method: options.method || 'GET',
        data: options.data,
        header: options.header || {},
        timeout: options.timeout || 10000,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${res.data?.message || '请求失败'}`));
          }
        },
        fail: (error) => {
          reject(new Error(error.errMsg || '网络请求失败'));
        }
      };

      wx.request(requestOptions);
    });
  }

  /**
   * 判断是否应该重试
   * @param {Error} error 错误对象
   */
  shouldRetry(error) {
    // 网络错误重试
    if (error.message.includes('timeout') || 
        error.message.includes('fail') ||
        error.message.includes('500') ||
        error.message.includes('502') ||
        error.message.includes('503')) {
      return true;
    }

    // 客户端错误不重试
    return false;
  }

  /**
   * 生成请求键
   * @param {string} url 请求URL
   * @param {object} options 请求选项
   */
  generateRequestKey(url, options) {
    const keyData = {
      url,
      method: options.method || 'GET',
      data: options.data
    };
    return JSON.stringify(keyData);
  }

  /**
   * 延迟函数
   * @param {number} ms 延迟毫秒数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 批量请求
   * @param {Array} requests 请求列表
   */
  async batchRequest(requests) {
    console.log(`执行批量请求: ${requests.length} 个`);
    
    const promises = requests.map(req => 
      this.request(req.url, req.options).catch(error => ({
        error,
        url: req.url
      }))
    );

    const results = await Promise.allSettled(promises);
    
    // 分离成功和失败的结果
    const successful = [];
    const failed = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && !result.value.error) {
        successful.push({
          index,
          data: result.value,
          url: requests[index].url
        });
      } else {
        failed.push({
          index,
          error: result.value?.error || result.reason,
          url: requests[index].url
        });
      }
    });

    console.log(`批量请求完成: 成功 ${successful.length}, 失败 ${failed.length}`);
    
    return { successful, failed };
  }
}

// 创建全局实例
const preloadManager = new PreloadManager();
const memoryManager = new MemoryManager();
const networkOptimizer = new NetworkOptimizer();

// 定期清理
setInterval(() => {
  preloadManager.cleanup();
  memoryManager.performCacheCleanup();
}, 60000); // 每分钟清理一次

module.exports = {
  PreloadManager,
  MemoryManager,
  NetworkOptimizer,
  preloadManager,
  memoryManager,
  networkOptimizer
};