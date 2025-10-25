// utils/error-handler.js
// 错误处理器 - 五好伴学微信小程序

const storage = require('./storage.js');

/**
 * 错误级别枚举
 */
const ErrorLevel = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  FATAL: 4,
};

/**
 * 错误分类枚举
 */
const ErrorCategory = {
  NETWORK: 'NETWORK',
  AUTH: 'AUTH',
  VALIDATION: 'VALIDATION',
  BUSINESS: 'BUSINESS',
  SYSTEM: 'SYSTEM',
  UI: 'UI',
  PERMISSION: 'PERMISSION',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN',
};

/**
 * 错误处理策略枚举
 */
const ErrorStrategy = {
  SILENT: 'SILENT', // 静默处理
  TOAST: 'TOAST', // 显示Toast
  MODAL: 'MODAL', // 显示模态框
  PAGE: 'PAGE', // 跳转错误页面
  RETRY: 'RETRY', // 自动重试
  REPORT: 'REPORT', // 上报错误
  FALLBACK: 'FALLBACK', // 降级处理
};

/**
 * 错误处理器类
 */
class ErrorHandler {
  constructor() {
    // 错误处理配置
    this.config = {
      // 是否启用错误处理
      enabled: true,
      // 是否显示错误详情
      showDetails: true,
      // 是否自动上报
      autoReport: true,
      // 错误日志存储键
      errorLogKey: 'error_logs',
      // 最大错误日志数量
      maxErrorLogs: 500,
      // 错误上报URL
      reportUrl: '/api/v1/errors/report',
      // 错误上报间隔(毫秒)
      reportInterval: 30000,
      // 批量上报数量
      reportBatchSize: 10,
      // 重试配置
      retry: {
        maxRetries: 3,
        baseDelay: 1000,
        maxDelay: 10000,
      },
    };

    // 错误日志队列
    this.errorLogs = [];

    // 待上报错误队列
    this.pendingReports = [];

    // 错误统计
    this.stats = {
      totalErrors: 0,
      networkErrors: 0,
      authErrors: 0,
      validationErrors: 0,
      businessErrors: 0,
      systemErrors: 0,
      handledErrors: 0,
      reportedErrors: 0,
      startTime: Date.now(),
    };

    // 错误处理规则
    this.rules = new Map();

    // 错误监听器
    this.listeners = [];

    // 上报定时器
    this.reportTimer = null;

    // 初始化
    this.init();
  }

  /**
   * 初始化错误处理器
   */
  async init() {
    try {
      // 加载错误日志
      await this.loadErrorLogs();

      // 设置默认错误处理规则
      this.setupDefaultRules();

      // 设置全局错误监听
      this.setupGlobalErrorHandling();

      // 启动错误上报
      this.startErrorReporting();

      console.log('错误处理器初始化成功');
    } catch (error) {
      console.error('错误处理器初始化失败', error);
    }
  }

  /**
   * 设置默认错误处理规则
   */
  setupDefaultRules() {
    // 网络错误
    this.addRule({
      category: ErrorCategory.NETWORK,
      condition: error => error.statusCode === 0 || error.type === 'NETWORK_ERROR',
      strategy: ErrorStrategy.TOAST,
      message: '网络连接失败，请检查网络设置',
      allowRetry: true,
      retryCount: 2,
    });

    // 认证错误
    this.addRule({
      category: ErrorCategory.AUTH,
      condition: error => error.statusCode === 401,
      strategy: ErrorStrategy.MODAL,
      message: '登录已过期，请重新登录',
      action: 'redirectToLogin',
    });

    // 权限错误
    this.addRule({
      category: ErrorCategory.PERMISSION,
      condition: error => error.statusCode === 403,
      strategy: ErrorStrategy.TOAST,
      message: '没有权限执行此操作',
      level: ErrorLevel.WARN,
    });

    // 参数验证错误
    this.addRule({
      category: ErrorCategory.VALIDATION,
      condition: error => error.statusCode === 422,
      strategy: ErrorStrategy.TOAST,
      message: error => error.data?.message || '请求参数有误',
      level: ErrorLevel.WARN,
    });

    // 业务错误
    this.addRule({
      category: ErrorCategory.BUSINESS,
      condition: error => error.statusCode >= 400 && error.statusCode < 500,
      strategy: ErrorStrategy.TOAST,
      message: error => error.data?.message || '操作失败',
      level: ErrorLevel.ERROR,
    });

    // 服务器错误
    this.addRule({
      category: ErrorCategory.SYSTEM,
      condition: error => error.statusCode >= 500,
      strategy: ErrorStrategy.MODAL,
      message: '服务器暂时不可用，请稍后重试',
      allowRetry: true,
      retryCount: 1,
      level: ErrorLevel.ERROR,
    });

    // 超时错误
    this.addRule({
      category: ErrorCategory.TIMEOUT,
      condition: error => error.message && error.message.includes('timeout'),
      strategy: ErrorStrategy.TOAST,
      message: '请求超时，请稍后重试',
      allowRetry: true,
      retryCount: 1,
    });

    // 默认错误处理
    this.addRule({
      category: ErrorCategory.UNKNOWN,
      condition: () => true,
      strategy: ErrorStrategy.TOAST,
      message: '操作失败，请稍后重试',
      level: ErrorLevel.ERROR,
    });
  }

  /**
   * 设置全局错误监听
   */
  setupGlobalErrorHandling() {
    // 监听小程序错误
    wx.onError(error => {
      this.handleError({
        type: 'SYSTEM_ERROR',
        message: error,
        category: ErrorCategory.SYSTEM,
        level: ErrorLevel.ERROR,
        stack: error,
        context: {
          source: 'wx.onError',
          timestamp: Date.now(),
        },
      });
    });

    // 监听未处理的Promise拒绝
    wx.onUnhandledRejection(event => {
      // ✅ 过滤组件生命周期相关错误
      const reason = event.reason;
      const reasonStr = typeof reason === 'string' ? reason : JSON.stringify(reason);

      if (
        reasonStr.includes('stopPropagation') ||
        reasonStr.includes('regeneratorRuntime') ||
        reasonStr.includes('MiniProgramError') ||
        reasonStr.includes('is not a function')
      ) {
        console.warn('[已忽略Promise拒绝]', reasonStr);
        return;
      }

      this.handleError({
        type: 'UNHANDLED_REJECTION',
        message: event.reason?.message || 'Unhandled promise rejection',
        category: ErrorCategory.SYSTEM,
        level: ErrorLevel.ERROR,
        originalError: event.reason,
        stack: event.reason?.stack,
        context: {
          source: 'wx.onUnhandledRejection',
          timestamp: Date.now(),
        },
      });
    });
  }

  /**
   * 添加错误处理规则
   */
  addRule(rule) {
    if (!rule.category || !rule.condition || !rule.strategy) {
      throw new Error('错误处理规则必须包含category、condition和strategy');
    }

    const ruleId = rule.id || `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    this.rules.set(ruleId, {
      id: ruleId,
      priority: rule.priority || 0,
      ...rule,
    });

    return ruleId;
  }

  /**
   * 移除错误处理规则
   */
  removeRule(ruleId) {
    return this.rules.delete(ruleId);
  }

  /**
   * 处理错误
   */
  async handleError(error, context = {}) {
    try {
      if (!this.config.enabled) {
        return;
      }

      // 标准化错误对象
      const normalizedError = this.normalizeError(error, context);

      // 记录错误日志
      this.logError(normalizedError);

      // 更新统计
      this.updateStats(normalizedError);

      // 查找匹配的处理规则
      const rule = this.findMatchingRule(normalizedError);

      if (rule) {
        // 执行错误处理策略
        await this.executeStrategy(normalizedError, rule);
      }

      // 通知监听器
      this.notifyListeners(normalizedError, rule);

      // 自动上报错误
      if (this.config.autoReport && this.shouldReport(normalizedError)) {
        this.queueErrorReport(normalizedError);
      }
    } catch (handlingError) {
      console.error('错误处理失败', handlingError);

      // 降级处理：显示通用错误信息
      this.showFallbackError();
    }
  }

  /**
   * 标准化错误对象
   */
  normalizeError(error, context = {}) {
    const normalized = {
      id: this.generateErrorId(),
      timestamp: Date.now(),
      type: error.type || 'UNKNOWN_ERROR',
      category: error.category || ErrorCategory.UNKNOWN,
      level: error.level || ErrorLevel.ERROR,
      message: error.message || '未知错误',
      statusCode: error.statusCode || 0,
      data: error.data,
      stack: error.stack,
      context: {
        ...context,
        ...error.context,
        userAgent: this.getUserAgent(),
        page: this.getCurrentPage(),
        route: this.getCurrentRoute(),
        scene: this.getScene(),
      },
      originalError: error.originalError || error,
    };

    // 自动分类错误
    if (normalized.category === ErrorCategory.UNKNOWN) {
      normalized.category = this.categorizeError(normalized);
    }

    return normalized;
  }

  /**
   * 自动分类错误
   */
  categorizeError(error) {
    if (error.statusCode === 0 || error.type === 'NETWORK_ERROR') {
      return ErrorCategory.NETWORK;
    }
    if (error.statusCode === 401 || error.type === 'AUTH_ERROR') {
      return ErrorCategory.AUTH;
    }
    if (error.statusCode === 403) {
      return ErrorCategory.PERMISSION;
    }
    if (error.statusCode === 422 || error.type === 'VALIDATION_ERROR') {
      return ErrorCategory.VALIDATION;
    }
    if (error.statusCode >= 400 && error.statusCode < 500) {
      return ErrorCategory.BUSINESS;
    }
    if (error.statusCode >= 500) {
      return ErrorCategory.SYSTEM;
    }
    if (error.message && error.message.includes('timeout')) {
      return ErrorCategory.TIMEOUT;
    }
    if (error.type && error.type.includes('UI')) {
      return ErrorCategory.UI;
    }
    return ErrorCategory.UNKNOWN;
  }

  /**
   * 查找匹配的错误处理规则
   */
  findMatchingRule(error) {
    const rules = Array.from(this.rules.values()).sort(
      (a, b) => (b.priority || 0) - (a.priority || 0),
    );

    for (const rule of rules) {
      try {
        if (typeof rule.condition === 'function' && rule.condition(error)) {
          return rule;
        }
      } catch (conditionError) {
        console.warn('错误处理规则条件检查失败', conditionError);
      }
    }

    return null;
  }

  /**
   * 执行错误处理策略
   */
  async executeStrategy(error, rule) {
    try {
      switch (rule.strategy) {
        case ErrorStrategy.SILENT:
          // 静默处理，不做任何UI展示
          break;

        case ErrorStrategy.TOAST:
          this.showToast(error, rule);
          break;

        case ErrorStrategy.MODAL:
          this.showModal(error, rule);
          break;

        case ErrorStrategy.PAGE:
          this.navigateToErrorPage(error, rule);
          break;

        case ErrorStrategy.RETRY:
          await this.retryOperation(error, rule);
          break;

        case ErrorStrategy.REPORT:
          this.queueErrorReport(error);
          break;

        case ErrorStrategy.FALLBACK:
          this.executeFallback(error, rule);
          break;

        default:
          console.warn('未知的错误处理策略', rule.strategy);
      }

      // 执行自定义操作
      if (rule.action) {
        await this.executeCustomAction(error, rule);
      }
    } catch (strategyError) {
      console.error('执行错误处理策略失败', strategyError);
      this.showFallbackError();
    }
  }

  /**
   * 显示Toast错误信息
   */
  showToast(error, rule) {
    const message = this.getMessage(error, rule);

    wx.showToast({
      title: message,
      icon: 'error',
      duration: 3000,
      mask: false,
    });
  }

  /**
   * 显示模态框错误信息
   */
  showModal(error, rule) {
    const message = this.getMessage(error, rule);
    const title = rule.title || '操作失败';

    wx.showModal({
      title,
      content: message,
      showCancel: rule.allowRetry || false,
      confirmText: rule.allowRetry ? '重试' : '确定',
      cancelText: '取消',
      success: res => {
        if (res.confirm && rule.allowRetry) {
          this.retryOperation(error, rule);
        }
      },
    });
  }

  /**
   * 跳转到错误页面
   */
  navigateToErrorPage(error, rule) {
    const errorPage = rule.errorPage || '/pages/error/index';
    const errorInfo = encodeURIComponent(
      JSON.stringify({
        message: this.getMessage(error, rule),
        code: error.statusCode,
        type: error.type,
      }),
    );

    wx.navigateTo({
      url: `${errorPage}?error=${errorInfo}`,
      fail: () => {
        // 降级到Modal显示
        this.showModal(error, { ...rule, strategy: ErrorStrategy.MODAL });
      },
    });
  }

  /**
   * 重试操作
   */
  async retryOperation(error, rule) {
    if (!error.retryContext) {
      console.warn('错误缺少重试上下文');
      return;
    }

    const maxRetries = rule.retryCount || this.config.retry.maxRetries;
    const currentRetry = error.retryContext.currentRetry || 0;

    if (currentRetry >= maxRetries) {
      console.warn('重试次数已达上限');
      this.showToast(error, { message: '重试失败，请稍后再试' });
      return;
    }

    try {
      // 计算重试延迟
      const delay = this.calculateRetryDelay(currentRetry);

      await this.delay(delay);

      // 执行重试操作
      if (typeof error.retryContext.retryFunction === 'function') {
        error.retryContext.currentRetry = currentRetry + 1;
        await error.retryContext.retryFunction();
      }
    } catch (retryError) {
      console.error('重试操作失败', retryError);

      // 递归重试或显示最终错误
      if (currentRetry + 1 < maxRetries) {
        this.retryOperation(retryError, rule);
      } else {
        this.showModal(retryError, {
          ...rule,
          strategy: ErrorStrategy.MODAL,
          message: '操作失败，请稍后重试',
        });
      }
    }
  }

  /**
   * 执行降级处理
   */
  executeFallback(error, rule) {
    if (typeof rule.fallbackFunction === 'function') {
      try {
        rule.fallbackFunction(error);
      } catch (fallbackError) {
        console.error('降级处理失败', fallbackError);
        this.showFallbackError();
      }
    } else {
      this.showFallbackError();
    }
  }

  /**
   * 执行自定义操作
   */
  async executeCustomAction(error, rule) {
    switch (rule.action) {
      case 'redirectToLogin':
        wx.redirectTo({
          url: '/pages/login/index',
          fail: () => {
            wx.reLaunch({ url: '/pages/login/index' });
          },
        });
        break;

      case 'goBack':
        wx.navigateBack({
          fail: () => {
            wx.reLaunch({ url: '/pages/index/index' });
          },
        });
        break;

      case 'refresh':
        // 刷新当前页面
        const pages = getCurrentPages();
        const currentPage = pages[pages.length - 1];
        if (currentPage && typeof currentPage.onLoad === 'function') {
          currentPage.onLoad(currentPage.options);
        }
        break;

      default:
        if (typeof rule.customAction === 'function') {
          await rule.customAction(error);
        }
    }
  }

  /**
   * 获取错误消息
   */
  getMessage(error, rule) {
    if (typeof rule.message === 'function') {
      return rule.message(error);
    }

    if (typeof rule.message === 'string') {
      return rule.message;
    }

    // 默认消息
    return error.message || '操作失败，请稍后重试';
  }

  /**
   * 显示降级错误信息
   */
  showFallbackError() {
    wx.showToast({
      title: '系统繁忙，请稍后重试',
      icon: 'error',
      duration: 2000,
    });
  }

  /**
   * 记录错误日志
   */
  logError(error) {
    try {
      this.errorLogs.push(error);

      // 限制日志数量
      if (this.errorLogs.length > this.config.maxErrorLogs) {
        this.errorLogs.shift();
      }

      // 保存到本地存储
      this.saveErrorLogs();

      // 控制台输出
      if (this.config.showDetails) {
        console.error('错误详情:', error);
      }
    } catch (logError) {
      console.error('记录错误日志失败', logError);
    }
  }

  /**
   * 更新错误统计
   */
  updateStats(error) {
    this.stats.totalErrors++;
    this.stats.handledErrors++;

    switch (error.category) {
      case ErrorCategory.NETWORK:
        this.stats.networkErrors++;
        break;
      case ErrorCategory.AUTH:
        this.stats.authErrors++;
        break;
      case ErrorCategory.VALIDATION:
        this.stats.validationErrors++;
        break;
      case ErrorCategory.BUSINESS:
        this.stats.businessErrors++;
        break;
      case ErrorCategory.SYSTEM:
        this.stats.systemErrors++;
        break;
    }
  }

  /**
   * 判断是否应该上报错误
   */
  shouldReport(error) {
    // 只上报ERROR和FATAL级别的错误
    if (error.level < ErrorLevel.ERROR) {
      return false;
    }

    // 不上报网络错误（避免循环）
    if (error.category === ErrorCategory.NETWORK) {
      return false;
    }

    // 不上报用户取消操作
    if (error.message && error.message.includes('cancel')) {
      return false;
    }

    return true;
  }

  /**
   * 将错误加入上报队列
   */
  queueErrorReport(error) {
    this.pendingReports.push({
      ...error,
      reportTime: Date.now(),
    });

    // 达到批量上报数量时立即上报
    if (this.pendingReports.length >= this.config.reportBatchSize) {
      this.reportErrors();
    }
  }

  /**
   * 启动错误上报
   */
  startErrorReporting() {
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
    }

    this.reportTimer = setInterval(() => {
      if (this.pendingReports.length > 0) {
        this.reportErrors();
      }
    }, this.config.reportInterval);
  }

  /**
   * 停止错误上报
   */
  stopErrorReporting() {
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
      this.reportTimer = null;
    }
  }

  /**
   * 上报错误
   */
  async reportErrors() {
    if (this.pendingReports.length === 0) {
      return;
    }

    try {
      const reportData = {
        errors: this.pendingReports.splice(0, this.config.reportBatchSize),
        clientInfo: {
          platform: 'miniprogram',
          version: wx.getSystemInfoSync().version,
          model: wx.getSystemInfoSync().model,
          timestamp: Date.now(),
        },
      };

      await wx.request({
        url: this.config.reportUrl,
        method: 'POST',
        data: reportData,
        header: {
          'Content-Type': 'application/json',
        },
        success: () => {
          this.stats.reportedErrors += reportData.errors.length;
        },
        fail: error => {
          console.warn('错误上报失败', error);
          // 将失败的错误重新加入队列
          this.pendingReports.unshift(...reportData.errors);
        },
      });
    } catch (reportError) {
      console.error('错误上报异常', reportError);
    }
  }

  /**
   * 添加错误监听器
   */
  addListener(listener) {
    if (typeof listener === 'function') {
      this.listeners.push(listener);
      return () => {
        const index = this.listeners.indexOf(listener);
        if (index > -1) {
          this.listeners.splice(index, 1);
        }
      };
    }
    return null;
  }

  /**
   * 通知监听器
   */
  notifyListeners(error, rule) {
    this.listeners.forEach(listener => {
      try {
        listener(error, rule);
      } catch (listenerError) {
        console.error('错误监听器执行失败', listenerError);
      }
    });
  }

  /**
   * 保存错误日志
   */
  async saveErrorLogs() {
    try {
      await storage.set(this.config.errorLogKey, this.errorLogs);
    } catch (error) {
      console.error('保存错误日志失败', error);
    }
  }

  /**
   * 加载错误日志
   */
  async loadErrorLogs() {
    try {
      const logs = await storage.get(this.config.errorLogKey);
      if (Array.isArray(logs)) {
        this.errorLogs = logs;
      }
    } catch (error) {
      console.error('加载错误日志失败', error);
      this.errorLogs = [];
    }
  }

  /**
   * 获取错误日志
   */
  getErrorLogs(limit = 50) {
    return this.errorLogs.slice(-limit).map(log => ({ ...log }));
  }

  /**
   * 清空错误日志
   */
  async clearErrorLogs() {
    this.errorLogs = [];
    await this.saveErrorLogs();
  }

  /**
   * 获取错误统计
   */
  getStats() {
    return {
      ...this.stats,
      uptime: Date.now() - this.stats.startTime,
      errorRate:
        this.stats.totalErrors > 0
          ? ((this.stats.totalErrors / (Date.now() - this.stats.startTime)) * 1000 * 60).toFixed(2)
          : '0.00', // 每分钟错误数
      pendingReports: this.pendingReports.length,
    };
  }

  /**
   * 重置统计
   */
  resetStats() {
    this.stats = {
      totalErrors: 0,
      networkErrors: 0,
      authErrors: 0,
      validationErrors: 0,
      businessErrors: 0,
      systemErrors: 0,
      handledErrors: 0,
      reportedErrors: 0,
      startTime: Date.now(),
    };
  }

  /**
   * 计算重试延迟
   */
  calculateRetryDelay(retryCount) {
    const baseDelay = this.config.retry.baseDelay;
    const maxDelay = this.config.retry.maxDelay;
    const delay = baseDelay * Math.pow(2, retryCount);
    return Math.min(delay, maxDelay);
  }

  /**
   * 延迟函数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 生成错误ID
   */
  generateErrorId() {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 获取用户代理信息
   */
  getUserAgent() {
    try {
      const systemInfo = wx.getSystemInfoSync();
      return `${systemInfo.brand} ${systemInfo.model} ${systemInfo.system}`;
    } catch (error) {
      return 'Unknown';
    }
  }

  /**
   * 获取当前页面
   */
  getCurrentPage() {
    try {
      const pages = getCurrentPages();
      const currentPage = pages[pages.length - 1];
      return currentPage ? currentPage.route : 'Unknown';
    } catch (error) {
      return 'Unknown';
    }
  }

  /**
   * 获取当前路由
   */
  getCurrentRoute() {
    try {
      const pages = getCurrentPages();
      const currentPage = pages[pages.length - 1];
      if (currentPage && currentPage.options) {
        const query = Object.keys(currentPage.options)
          .map(key => `${key}=${currentPage.options[key]}`)
          .join('&');
        return query ? `${currentPage.route}?${query}` : currentPage.route;
      }
      return currentPage ? currentPage.route : 'Unknown';
    } catch (error) {
      return 'Unknown';
    }
  }

  /**
   * 获取场景值
   */
  getScene() {
    try {
      const launchOptions = wx.getLaunchOptionsSync();
      return launchOptions.scene || 'Unknown';
    } catch (error) {
      return 'Unknown';
    }
  }

  /**
   * 设置配置
   */
  setConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * 销毁错误处理器
   */
  destroy() {
    this.stopErrorReporting();
    this.rules.clear();
    this.listeners = [];
    this.errorLogs = [];
    this.pendingReports = [];
    console.log('错误处理器已销毁');
  }
}

// 创建单例实例

const errorHandler = new ErrorHandler();

module.exports = {
  errorHandler,

  // 常量导出
  ErrorLevel,
  ErrorCategory,
  ErrorStrategy,

  // 常用方法
  handleError: (error, context) => errorHandler.handleError(error, context),
  addRule: rule => errorHandler.addRule(rule),
  removeRule: ruleId => errorHandler.removeRule(ruleId),
  addListener: listener => errorHandler.addListener(listener),
  getErrorLogs: limit => errorHandler.getErrorLogs(limit),
  clearErrorLogs: () => errorHandler.clearErrorLogs(),
  getStats: () => errorHandler.getStats(),
  resetStats: () => errorHandler.resetStats(),
  setConfig: config => errorHandler.setConfig(config),

  // 便捷方法
  handleNetworkError: (error, context) =>
    errorHandler.handleError(
      {
        ...error,
        category: ErrorCategory.NETWORK,
      },
      context,
    ),

  handleAuthError: (error, context) =>
    errorHandler.handleError(
      {
        ...error,
        category: ErrorCategory.AUTH,
      },
      context,
    ),

  handleValidationError: (error, context) =>
    errorHandler.handleError(
      {
        ...error,
        category: ErrorCategory.VALIDATION,
      },
      context,
    ),

  handleBusinessError: (error, context) =>
    errorHandler.handleError(
      {
        ...error,
        category: ErrorCategory.BUSINESS,
      },
      context,
    ),

  handleSystemError: (error, context) =>
    errorHandler.handleError(
      {
        ...error,
        category: ErrorCategory.SYSTEM,
      },
      context,
    ),

  // 错误处理装饰器
  withErrorHandling: (category = ErrorCategory.UNKNOWN, level = ErrorLevel.ERROR) => {
    return function (target, propertyKey, descriptor) {
      const originalMethod = descriptor.value;

      descriptor.value = async function (...args) {
        try {
          return await originalMethod.apply(this, args);
        } catch (error) {
          errorHandler.handleError({
            ...error,
            category,
            level,
            context: {
              method: propertyKey,
              args: args.length,
              timestamp: Date.now(),
            },
          });
          throw error;
        }
      };

      return descriptor;
    };
  },
};
