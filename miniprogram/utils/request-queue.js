// utils/request-queue.js
// 请求队列管理器 - 五好伴学微信小程序

/**
 * 请求队列管理器类
 */
class RequestQueue {
  constructor() {
    // 请求队列
    this.queue = [];

    // 正在执行的请求
    this.activeRequests = new Map();

    // 队列配置
    this.config = {
      // 最大并发数
      maxConcurrency: 6,
      // 队列最大长度
      maxQueueSize: 100,
      // 请求超时时间(毫秒)
      timeout: 30000,
      // 是否启用优先级队列
      enablePriority: true,
      // 高优先级请求最大比例
      highPriorityRatio: 0.3,
      // 请求去重时间窗口(毫秒)
      deduplicationWindow: 1000
    };

    // 优先级常量
    this.Priority = {
      HIGH: 3,
      NORMAL: 2,
      LOW: 1
    };

    // 队列统计
    this.stats = {
      totalRequests: 0,
      completedRequests: 0,
      failedRequests: 0,
      queuedRequests: 0,
      activeRequests: 0,
      averageWaitTime: 0,
      averageExecuteTime: 0
    };

    // 请求去重映射
    this.deduplicationMap = new Map();

    // 清理定时器
    this.cleanupTimer = null;

    // 初始化
    this.init();
  }

  /**
   * 初始化队列管理器
   */
  init() {
    try {
      // 启动清理定时器
      this.startCleanup();

      console.log('请求队列管理器初始化成功');
    } catch (error) {
      console.error('请求队列管理器初始化失败', error);
    }
  }

  /**
   * 添加请求到队列
   */
  async enqueue(requestFunction, options = {}) {
    return new Promise((resolve, reject) => {
      const {
        priority = this.Priority.NORMAL,
        timeout = this.config.timeout,
        enableDeduplication = true,
        deduplicationKey = null,
        retryCount = 0,
        metadata = {}
      } = options;

      // 检查队列大小限制
      if (this.queue.length >= this.config.maxQueueSize) {
        reject(new Error('请求队列已满'));
        return;
      }

      // 生成请求ID
      const requestId = this.generateRequestId();

      // 检查请求去重
      if (enableDeduplication) {
        const dedupKey = deduplicationKey || this.generateDeduplicationKey(requestFunction);

        if (this.deduplicationMap.has(dedupKey)) {
          const existingPromise = this.deduplicationMap.get(dedupKey);
          resolve(existingPromise);
          return;
        }

        // 添加到去重映射
        this.deduplicationMap.set(dedupKey, { resolve, reject });

        // 设置去重过期
        setTimeout(() => {
          this.deduplicationMap.delete(dedupKey);
        }, this.config.deduplicationWindow);
      }

      // 创建队列项
      const queueItem = {
        id: requestId,
        requestFunction,
        priority,
        timeout,
        retryCount,
        currentRetry: 0,
        metadata,
        createTime: Date.now(),
        startTime: null,
        endTime: null,
        resolve,
        reject,
        deduplicationKey: enableDeduplication ? (deduplicationKey || this.generateDeduplicationKey(requestFunction)) : null
      };

      // 添加到队列
      this.addToQueue(queueItem);

      // 更新统计
      this.stats.totalRequests++;
      this.stats.queuedRequests++;

      // 尝试处理队列
      this.processQueue();
    });
  }

  /**
   * 将请求添加到队列（按优先级排序）
   */
  addToQueue(queueItem) {
    if (!this.config.enablePriority) {
      this.queue.push(queueItem);
      return;
    }

    // 找到插入位置（按优先级排序）
    let insertIndex = this.queue.length;

    for (let i = 0; i < this.queue.length; i++) {
      if (this.queue[i].priority < queueItem.priority) {
        insertIndex = i;
        break;
      }
    }

    this.queue.splice(insertIndex, 0, queueItem);
  }

  /**
   * 处理队列
   */
  async processQueue() {
    // 检查是否可以处理更多请求
    while (this.canProcessMore() && this.queue.length > 0) {
      const queueItem = this.getNextQueueItem();

      if (queueItem) {
        this.executeRequest(queueItem);
      }
    }
  }

  /**
   * 检查是否可以处理更多请求
   */
  canProcessMore() {
    const currentActive = this.activeRequests.size;

    if (currentActive >= this.config.maxConcurrency) {
      return false;
    }

    // 检查高优先级请求比例限制
    if (this.config.enablePriority) {
      const highPriorityActive = Array.from(this.activeRequests.values())
        .filter(item => item.priority === this.Priority.HIGH).length;

      const highPriorityRatio = currentActive > 0 ? highPriorityActive / currentActive : 0;

      // 如果高优先级请求比例过高，优先处理其他优先级请求
      if (highPriorityRatio > this.config.highPriorityRatio) {
        const nextItem = this.queue[0];
        if (nextItem && nextItem.priority === this.Priority.HIGH) {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * 获取下一个队列项
   */
  getNextQueueItem() {
    if (this.queue.length === 0) {
      return null;
    }

    // 移除并返回队列第一项
    const queueItem = this.queue.shift();
    this.stats.queuedRequests--;

    return queueItem;
  }

  /**
   * 执行请求
   */
  async executeRequest(queueItem) {
    try {
      // 记录开始时间
      queueItem.startTime = Date.now();

      // 添加到活跃请求
      this.activeRequests.set(queueItem.id, queueItem);
      this.stats.activeRequests++;

      // 计算等待时间
      const waitTime = queueItem.startTime - queueItem.createTime;
      this.updateAverageWaitTime(waitTime);

      // 创建超时处理
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
          reject(new Error('请求超时'));
        }, queueItem.timeout);
      });

      // 执行请求
      const requestPromise = queueItem.requestFunction();

      // 等待请求完成或超时
      const result = await Promise.race([requestPromise, timeoutPromise]);

      // 请求成功
      this.handleRequestSuccess(queueItem, result);

    } catch (error) {
      // 请求失败
      this.handleRequestError(queueItem, error);
    }
  }

  /**
   * 处理请求成功
   */
  handleRequestSuccess(queueItem, result) {
    try {
      // 记录结束时间
      queueItem.endTime = Date.now();

      // 计算执行时间
      const executeTime = queueItem.endTime - queueItem.startTime;
      this.updateAverageExecuteTime(executeTime);

      // 从活跃请求中移除
      this.activeRequests.delete(queueItem.id);
      this.stats.activeRequests--;
      this.stats.completedRequests++;

      // 处理去重
      if (queueItem.deduplicationKey && this.deduplicationMap.has(queueItem.deduplicationKey)) {
        const dedupItem = this.deduplicationMap.get(queueItem.deduplicationKey);
        if (dedupItem.resolve === queueItem.resolve) {
          this.deduplicationMap.delete(queueItem.deduplicationKey);
        }
      }

      // 解析Promise
      queueItem.resolve(result);

      // 继续处理队列
      this.processQueue();

    } catch (error) {
      console.error('处理请求成功回调失败', error);
    }
  }

  /**
   * 处理请求错误
   */
  async handleRequestError(queueItem, error) {
    try {
      // 记录结束时间
      queueItem.endTime = Date.now();

      // 检查是否需要重试
      if (queueItem.currentRetry < queueItem.retryCount && this.shouldRetry(error)) {
        // 重试请求
        queueItem.currentRetry++;
        queueItem.startTime = null;
        queueItem.endTime = null;

        // 重新加入队列（降低优先级）
        queueItem.priority = Math.max(queueItem.priority - 1, this.Priority.LOW);
        this.addToQueue(queueItem);
        this.stats.queuedRequests++;

        // 从活跃请求中移除
        this.activeRequests.delete(queueItem.id);
        this.stats.activeRequests--;

        // 继续处理队列
        this.processQueue();
        return;
      }

      // 不重试或重试次数用完
      this.activeRequests.delete(queueItem.id);
      this.stats.activeRequests--;
      this.stats.failedRequests++;

      // 处理去重
      if (queueItem.deduplicationKey && this.deduplicationMap.has(queueItem.deduplicationKey)) {
        const dedupItem = this.deduplicationMap.get(queueItem.deduplicationKey);
        if (dedupItem.reject === queueItem.reject) {
          this.deduplicationMap.delete(queueItem.deduplicationKey);
        }
      }

      // 拒绝Promise
      queueItem.reject(error);

      // 继续处理队列
      this.processQueue();

    } catch (processError) {
      console.error('处理请求错误回调失败', processError);
    }
  }

  /**
   * 判断是否应该重试
   */
  shouldRetry(error) {
    // 网络错误或服务器5xx错误可以重试
    if (error.statusCode === 0 || (error.statusCode >= 500 && error.statusCode < 600)) {
      return true;
    }

    // 超时错误可以重试
    if (error.message && error.message.includes('超时')) {
      return true;
    }

    return false;
  }

  /**
   * 生成请求ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 生成去重键
   */
  generateDeduplicationKey(requestFunction) {
    // 简单的函数字符串化作为去重键
    return `dedup_${requestFunction.toString().length}_${Date.now()}`;
  }

  /**
   * 更新平均等待时间
   */
  updateAverageWaitTime(waitTime) {
    const completedCount = this.stats.completedRequests + this.stats.failedRequests;
    if (completedCount === 0) {
      this.stats.averageWaitTime = waitTime;
    } else {
      this.stats.averageWaitTime = (this.stats.averageWaitTime * completedCount + waitTime) / (completedCount + 1);
    }
  }

  /**
   * 更新平均执行时间
   */
  updateAverageExecuteTime(executeTime) {
    const completedCount = this.stats.completedRequests;
    if (completedCount === 0) {
      this.stats.averageExecuteTime = executeTime;
    } else {
      this.stats.averageExecuteTime = (this.stats.averageExecuteTime * completedCount + executeTime) / (completedCount + 1);
    }
  }

  /**
   * 获取队列状态
   */
  getStatus() {
    return {
      queueLength: this.queue.length,
      activeRequests: this.activeRequests.size,
      stats: { ...this.stats },
      config: { ...this.config }
    };
  }

  /**
   * 获取队列中的请求列表
   */
  getQueuedRequests() {
    return this.queue.map(item => ({
      id: item.id,
      priority: item.priority,
      createTime: item.createTime,
      waitTime: Date.now() - item.createTime,
      retryCount: item.currentRetry,
      metadata: item.metadata
    }));
  }

  /**
   * 获取活跃请求列表
   */
  getActiveRequests() {
    return Array.from(this.activeRequests.values()).map(item => ({
      id: item.id,
      priority: item.priority,
      startTime: item.startTime,
      executeTime: item.startTime ? Date.now() - item.startTime : 0,
      retryCount: item.currentRetry,
      metadata: item.metadata
    }));
  }

  /**
   * 取消指定请求
   */
  cancelRequest(requestId) {
    // 取消队列中的请求
    const queueIndex = this.queue.findIndex(item => item.id === requestId);
    if (queueIndex > -1) {
      const queueItem = this.queue[queueIndex];
      this.queue.splice(queueIndex, 1);
      this.stats.queuedRequests--;

      queueItem.reject(new Error('请求已取消'));
      return true;
    }

    // 取消活跃请求（实际上无法取消正在执行的微信API，但可以忽略结果）
    if (this.activeRequests.has(requestId)) {
      const activeItem = this.activeRequests.get(requestId);
      this.activeRequests.delete(requestId);
      this.stats.activeRequests--;

      activeItem.reject(new Error('请求已取消'));
      return true;
    }

    return false;
  }

  /**
   * 取消所有请求
   */
  cancelAllRequests() {
    let canceledCount = 0;

    // 取消队列中的请求
    while (this.queue.length > 0) {
      const queueItem = this.queue.shift();
      queueItem.reject(new Error('请求已取消'));
      canceledCount++;
    }
    this.stats.queuedRequests = 0;

    // 取消活跃请求
    for (const activeItem of this.activeRequests.values()) {
      activeItem.reject(new Error('请求已取消'));
      canceledCount++;
    }
    this.activeRequests.clear();
    this.stats.activeRequests = 0;

    return canceledCount;
  }

  /**
   * 暂停队列处理
   */
  pause() {
    this.config.maxConcurrency = 0;
  }

  /**
   * 恢复队列处理
   */
  resume(maxConcurrency = 6) {
    this.config.maxConcurrency = maxConcurrency;
    this.processQueue();
  }

  /**
   * 清空队列
   */
  clear() {
    this.cancelAllRequests();
    this.deduplicationMap.clear();
    this.resetStats();
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      totalRequests: 0,
      completedRequests: 0,
      failedRequests: 0,
      queuedRequests: 0,
      activeRequests: 0,
      averageWaitTime: 0,
      averageExecuteTime: 0
    };
  }

  /**
   * 设置队列配置
   */
  setConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * 启动清理定时器
   */
  startCleanup() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    // 每分钟清理一次过期的去重映射
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, 60000);
  }

  /**
   * 停止清理定时器
   */
  stopCleanup() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  /**
   * 清理过期数据
   */
  cleanup() {
    // 清理过期的去重映射
    const now = Date.now();
    for (const [key, value] of this.deduplicationMap.entries()) {
      if (now - value.createTime > this.config.deduplicationWindow) {
        this.deduplicationMap.delete(key);
      }
    }
  }

  /**
   * 销毁队列管理器
   */
  destroy() {
    this.stopCleanup();
    this.clear();
    console.log('请求队列管理器已销毁');
  }
}

// 创建单例实例
const requestQueue = new RequestQueue();

module.exports = {
  requestQueue,

  // 优先级常量
  Priority: requestQueue.Priority,

  // 导出常用方法
  enqueue: (requestFunction, options) => requestQueue.enqueue(requestFunction, options),
  getStatus: () => requestQueue.getStatus(),
  getQueuedRequests: () => requestQueue.getQueuedRequests(),
  getActiveRequests: () => requestQueue.getActiveRequests(),
  cancelRequest: (requestId) => requestQueue.cancelRequest(requestId),
  cancelAllRequests: () => requestQueue.cancelAllRequests(),
  pause: () => requestQueue.pause(),
  resume: (maxConcurrency) => requestQueue.resume(maxConcurrency),
  clear: () => requestQueue.clear(),
  setConfig: (config) => requestQueue.setConfig(config),

  // 便捷方法
  enqueueHigh: (requestFunction, options = {}) => {
    return requestQueue.enqueue(requestFunction, {
      ...options,
      priority: requestQueue.Priority.HIGH
    });
  },

  enqueueNormal: (requestFunction, options = {}) => {
    return requestQueue.enqueue(requestFunction, {
      ...options,
      priority: requestQueue.Priority.NORMAL
    });
  },

  enqueueLow: (requestFunction, options = {}) => {
    return requestQueue.enqueue(requestFunction, {
      ...options,
      priority: requestQueue.Priority.LOW
    });
  },

  // 队列装饰器
  queued: (priority = requestQueue.Priority.NORMAL, options = {}) => {
    return function (target, propertyKey, descriptor) {
      const originalMethod = descriptor.value;

      descriptor.value = function (...args) {
        return requestQueue.enqueue(() => {
          return originalMethod.apply(this, args);
        }, { priority, ...options });
      };

      return descriptor;
    };
  }
};
