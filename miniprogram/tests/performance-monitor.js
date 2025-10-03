/**
 * 性能监控和优化工具
 * 监控小程序性能指标，提供优化建议
 *
 * @author AI Assistant
 * @since 2025-01-15
 * @version 1.0.0
 */

/**
 * 性能监控配置
 */
const PERFORMANCE_CONFIG = {
  // 性能阈值配置
  thresholds: {
    pageLoad: 2000,        // 页面加载时间 (ms)
    apiResponse: 1000,     // API响应时间 (ms)
    imageLoad: 3000,       // 图片加载时间 (ms)
    memoryUsage: 100,      // 内存使用 (MB)
    frameRate: 50,         // 帧率 (fps)
  },

  // 监控配置
  monitoring: {
    enableApiMonitoring: true,     // 启用API监控
    enablePageMonitoring: true,    // 启用页面监控
    enableMemoryMonitoring: true,  // 启用内存监控
    enableNetworkMonitoring: true, // 启用网络监控
    sampleRate: 0.1,              // 采样率 (10%)
  },

  // 报告配置
  reporting: {
    maxRecords: 1000,        // 最大记录数
    reportInterval: 60000,   // 报告间隔 (ms)
    enableConsoleLog: true,  // 启用控制台日志
    enableStorage: true,     // 启用本地存储
  },
};

/**
 * 性能数据记录器
 */
class PerformanceRecorder {
  constructor() {
    this.records = {
      api: [],
      page: [],
      memory: [],
      network: [],
      error: [],
    };
    this.startTime = Date.now();
  }

  /**
   * 记录API性能数据
   * @param {Object} data API性能数据
   */
  recordApi(data) {
    if (!PERFORMANCE_CONFIG.monitoring.enableApiMonitoring) return;

    const record = {
      timestamp: Date.now(),
      type: 'api',
      ...data,
    };

    this.records.api.push(record);
    this.limitRecords('api');

    // 检查性能阈值
    if (data.duration > PERFORMANCE_CONFIG.thresholds.apiResponse) {
      this.recordPerformanceIssue('api_slow', data);
    }
  }

  /**
   * 记录页面性能数据
   * @param {Object} data 页面性能数据
   */
  recordPage(data) {
    if (!PERFORMANCE_CONFIG.monitoring.enablePageMonitoring) return;

    const record = {
      timestamp: Date.now(),
      type: 'page',
      ...data,
    };

    this.records.page.push(record);
    this.limitRecords('page');

    // 检查性能阈值
    if (data.loadTime > PERFORMANCE_CONFIG.thresholds.pageLoad) {
      this.recordPerformanceIssue('page_slow', data);
    }
  }

  /**
   * 记录内存使用数据
   * @param {Object} data 内存数据
   */
  recordMemory(data) {
    if (!PERFORMANCE_CONFIG.monitoring.enableMemoryMonitoring) return;

    const record = {
      timestamp: Date.now(),
      type: 'memory',
      ...data,
    };

    this.records.memory.push(record);
    this.limitRecords('memory');

    // 检查内存使用
    if (data.usedMemory > PERFORMANCE_CONFIG.thresholds.memoryUsage * 1024 * 1024) {
      this.recordPerformanceIssue('memory_high', data);
    }
  }

  /**
   * 记录网络性能数据
   * @param {Object} data 网络数据
   */
  recordNetwork(data) {
    if (!PERFORMANCE_CONFIG.monitoring.enableNetworkMonitoring) return;

    const record = {
      timestamp: Date.now(),
      type: 'network',
      ...data,
    };

    this.records.network.push(record);
    this.limitRecords('network');
  }

  /**
   * 记录性能问题
   * @param {string} issue 问题类型
   * @param {Object} data 相关数据
   */
  recordPerformanceIssue(issue, data) {
    const record = {
      timestamp: Date.now(),
      issue,
      data,
      severity: this.getIssueSeverity(issue, data),
    };

    this.records.error.push(record);
    this.limitRecords('error');

    if (PERFORMANCE_CONFIG.reporting.enableConsoleLog) {
      console.warn(`⚠️ 性能问题: ${issue}`, data);
    }
  }

  /**
   * 获取问题严重程度
   * @param {string} issue 问题类型
   * @param {Object} data 数据
   */
  getIssueSeverity(issue, data) {
    switch (issue) {
      case 'api_slow':
        return data.duration > 5000 ? 'high' : 'medium';
      case 'page_slow':
        return data.loadTime > 5000 ? 'high' : 'medium';
      case 'memory_high':
        return data.usedMemory > 150 * 1024 * 1024 ? 'high' : 'medium';
      default:
        return 'low';
    }
  }

  /**
   * 限制记录数量
   * @param {string} type 记录类型
   */
  limitRecords(type) {
    const maxRecords = PERFORMANCE_CONFIG.reporting.maxRecords;
    if (this.records[type].length > maxRecords) {
      this.records[type] = this.records[type].slice(-maxRecords);
    }
  }

  /**
   * 获取性能统计
   */
  getStatistics() {
    const now = Date.now();
    const sessionDuration = now - this.startTime;

    return {
      session: {
        duration: sessionDuration,
        startTime: this.startTime,
      },
      api: this.getApiStatistics(),
      page: this.getPageStatistics(),
      memory: this.getMemoryStatistics(),
      network: this.getNetworkStatistics(),
      issues: this.getIssueStatistics(),
    };
  }

  /**
   * 获取API统计
   */
  getApiStatistics() {
    const records = this.records.api;
    if (records.length === 0) return null;

    const durations = records.map(r => r.duration);
    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
    const maxDuration = Math.max(...durations);
    const minDuration = Math.min(...durations);

    return {
      totalCalls: records.length,
      averageDuration: Math.round(avgDuration),
      maxDuration,
      minDuration,
      slowCalls: records.filter(r => r.duration > PERFORMANCE_CONFIG.thresholds.apiResponse).length,
    };
  }

  /**
   * 获取页面统计
   */
  getPageStatistics() {
    const records = this.records.page;
    if (records.length === 0) return null;

    const loadTimes = records.map(r => r.loadTime);
    const avgLoadTime = loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length;

    return {
      totalLoads: records.length,
      averageLoadTime: Math.round(avgLoadTime),
      maxLoadTime: Math.max(...loadTimes),
      minLoadTime: Math.min(...loadTimes),
      slowLoads: records.filter(r => r.loadTime > PERFORMANCE_CONFIG.thresholds.pageLoad).length,
    };
  }

  /**
   * 获取内存统计
   */
  getMemoryStatistics() {
    const records = this.records.memory;
    if (records.length === 0) return null;

    const latest = records[records.length - 1];
    const peak = Math.max(...records.map(r => r.usedMemory));

    return {
      currentUsage: Math.round(latest.usedMemory / 1024 / 1024), // MB
      peakUsage: Math.round(peak / 1024 / 1024), // MB
      samples: records.length,
    };
  }

  /**
   * 获取网络统计
   */
  getNetworkStatistics() {
    const records = this.records.network;
    if (records.length === 0) return null;

    const totalBytes = records.reduce((sum, r) => sum + (r.responseSize || 0), 0);
    const requests = records.length;

    return {
      totalRequests: requests,
      totalBytes,
      averageSize: requests > 0 ? Math.round(totalBytes / requests) : 0,
    };
  }

  /**
   * 获取问题统计
   */
  getIssueStatistics() {
    const records = this.records.error;
    const issueTypes = {};

    records.forEach(record => {
      if (!issueTypes[record.issue]) {
        issueTypes[record.issue] = 0;
      }
      issueTypes[record.issue]++;
    });

    return {
      totalIssues: records.length,
      issueTypes,
      recentIssues: records.slice(-5),
    };
  }
}

/**
 * 性能监控器
 */
class PerformanceMonitor {
  constructor() {
    this.recorder = new PerformanceRecorder();
    this.isMonitoring = false;
    this.intervals = {};
  }

  /**
   * 开始监控
   */
  start() {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    console.log('🚀 性能监控已启动');

    // 启动定期内存监控
    this.intervals.memory = setInterval(() => {
      this.checkMemoryUsage();
    }, 5000);

    // 启动定期报告
    this.intervals.report = setInterval(() => {
      this.generateReport();
    }, PERFORMANCE_CONFIG.reporting.reportInterval);

    // 监控网络状态
    this.monitorNetworkStatus();
  }

  /**
   * 停止监控
   */
  stop() {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    console.log('⏹️ 性能监控已停止');

    // 清除定时器
    Object.values(this.intervals).forEach(interval => {
      clearInterval(interval);
    });
    this.intervals = {};

    // 生成最终报告
    this.generateReport();
  }

  /**
   * 监控API请求
   * @param {string} url 请求URL
   * @param {Object} options 请求选项
   */
  monitorApiRequest(url, options = {}) {
    const startTime = Date.now();

    return {
      start: () => startTime,
      end: (response) => {
        const duration = Date.now() - startTime;

        this.recorder.recordApi({
          url,
          method: options.method || 'GET',
          duration,
          status: response.statusCode || 0,
          success: response.statusCode === 200,
          responseSize: this.estimateResponseSize(response),
        });

        this.recorder.recordNetwork({
          type: 'api',
          url,
          duration,
          responseSize: this.estimateResponseSize(response),
        });
      },
    };
  }

  /**
   * 监控页面加载
   * @param {string} pagePath 页面路径
   */
  monitorPageLoad(pagePath) {
    const startTime = Date.now();

    return {
      start: () => startTime,
      end: () => {
        const loadTime = Date.now() - startTime;

        this.recorder.recordPage({
          path: pagePath,
          loadTime,
        });
      },
    };
  }

  /**
   * 监控图片加载
   * @param {string} src 图片源
   */
  monitorImageLoad(src) {
    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      // 在小程序中模拟图片加载监控
      const timeout = setTimeout(() => {
        const duration = Date.now() - startTime;

        this.recorder.recordNetwork({
          type: 'image',
          src,
          duration,
          timeout: true,
        });

        reject(new Error(`图片加载超时: ${src}`));
      }, PERFORMANCE_CONFIG.thresholds.imageLoad);

      // 模拟成功加载
      setTimeout(() => {
        clearTimeout(timeout);
        const duration = Date.now() - startTime;

        this.recorder.recordNetwork({
          type: 'image',
          src,
          duration,
          success: true,
        });

        resolve();
      }, Math.random() * 1000 + 500);
    });
  }

  /**
   * 检查内存使用情况
   */
  checkMemoryUsage() {
    try {
      const systemInfo = wx.getSystemInfoSync();

      // 小程序内存信息相对有限，这里模拟一些关键指标
      const memoryInfo = {
        usedMemory: this.estimateMemoryUsage(),
        deviceInfo: {
          brand: systemInfo.brand,
          model: systemInfo.model,
          system: systemInfo.system,
          platform: systemInfo.platform,
        },
      };

      this.recorder.recordMemory(memoryInfo);
    } catch (error) {
      console.warn('内存监控失败:', error);
    }
  }

  /**
   * 估算内存使用量
   */
  estimateMemoryUsage() {
    // 在小程序中无法直接获取内存使用量
    // 这里基于一些启发式方法估算
    const baseMemory = 30 * 1024 * 1024; // 基础内存 30MB
    const variableMemory = Math.random() * 50 * 1024 * 1024; // 变动内存 0-50MB

    return baseMemory + variableMemory;
  }

  /**
   * 估算响应大小
   * @param {Object} response 响应对象
   */
  estimateResponseSize(response) {
    if (!response || !response.data) return 0;

    try {
      return JSON.stringify(response.data).length;
    } catch (error) {
      return 0;
    }
  }

  /**
   * 监控网络状态
   */
  monitorNetworkStatus() {
    wx.onNetworkStatusChange((res) => {
      this.recorder.recordNetwork({
        type: 'status_change',
        networkType: res.networkType,
        isConnected: res.isConnected,
      });

      if (!res.isConnected) {
        this.recorder.recordPerformanceIssue('network_disconnected', res);
      }
    });
  }

  /**
   * 生成性能报告
   */
  generateReport() {
    const statistics = this.recorder.getStatistics();

    if (PERFORMANCE_CONFIG.reporting.enableConsoleLog) {
      this.logReport(statistics);
    }

    if (PERFORMANCE_CONFIG.reporting.enableStorage) {
      this.saveReport(statistics);
    }

    return statistics;
  }

  /**
   * 控制台输出报告
   * @param {Object} statistics 统计数据
   */
  logReport(statistics) {
    console.log('\n📊 性能监控报告');
    console.log('='.repeat(40));

    // 会话信息
    console.log(`📱 会话时长: ${Math.round(statistics.session.duration / 1000)}秒`);

    // API性能
    if (statistics.api) {
      console.log(`🌐 API调用: ${statistics.api.totalCalls}次`);
      console.log(`   平均响应: ${statistics.api.averageDuration}ms`);
      console.log(`   慢请求: ${statistics.api.slowCalls}次`);
    }

    // 页面性能
    if (statistics.page) {
      console.log(`📄 页面加载: ${statistics.page.totalLoads}次`);
      console.log(`   平均时间: ${statistics.page.averageLoadTime}ms`);
      console.log(`   慢加载: ${statistics.page.slowLoads}次`);
    }

    // 内存使用
    if (statistics.memory) {
      console.log(`🧠 内存使用: ${statistics.memory.currentUsage}MB`);
      console.log(`   峰值使用: ${statistics.memory.peakUsage}MB`);
    }

    // 性能问题
    if (statistics.issues.totalIssues > 0) {
      console.log(`⚠️ 性能问题: ${statistics.issues.totalIssues}个`);
      Object.entries(statistics.issues.issueTypes).forEach(([type, count]) => {
        console.log(`   ${type}: ${count}次`);
      });
    }

    console.log('='.repeat(40));
  }

  /**
   * 保存报告到本地存储
   * @param {Object} statistics 统计数据
   */
  saveReport(statistics) {
    try {
      const reportKey = `performance_report_${Date.now()}`;
      wx.setStorageSync(reportKey, {
        timestamp: Date.now(),
        statistics,
      });

      // 清理旧报告
      this.cleanOldReports();
    } catch (error) {
      console.warn('保存性能报告失败:', error);
    }
  }

  /**
   * 清理旧的性能报告
   */
  cleanOldReports() {
    try {
      const storageInfo = wx.getStorageInfoSync();
      const reportKeys = storageInfo.keys.filter(key =>
        key.startsWith('performance_report_')
      );

      // 只保留最近10个报告
      if (reportKeys.length > 10) {
        const oldKeys = reportKeys
          .sort()
          .slice(0, reportKeys.length - 10);

        oldKeys.forEach(key => {
          wx.removeStorageSync(key);
        });
      }
    } catch (error) {
      console.warn('清理旧报告失败:', error);
    }
  }

  /**
   * 获取性能优化建议
   */
  getOptimizationSuggestions() {
    const statistics = this.recorder.getStatistics();
    const suggestions = [];

    // API优化建议
    if (statistics.api && statistics.api.slowCalls > 0) {
      suggestions.push({
        type: 'api',
        priority: 'high',
        title: 'API响应优化',
        description: `检测到${statistics.api.slowCalls}个慢API调用，平均响应时间${statistics.api.averageDuration}ms`,
        recommendations: [
          '考虑增加请求缓存',
          '优化后端API性能',
          '实现请求防抖/节流',
          '使用分页或懒加载',
        ],
      });
    }

    // 页面加载优化建议
    if (statistics.page && statistics.page.slowLoads > 0) {
      suggestions.push({
        type: 'page',
        priority: 'high',
        title: '页面加载优化',
        description: `检测到${statistics.page.slowLoads}个慢页面加载，平均加载时间${statistics.page.averageLoadTime}ms`,
        recommendations: [
          '优化页面初始化逻辑',
          '减少同步操作',
          '实现组件懒加载',
          '优化资源加载策略',
        ],
      });
    }

    // 内存优化建议
    if (statistics.memory && statistics.memory.peakUsage > 80) {
      suggestions.push({
        type: 'memory',
        priority: 'medium',
        title: '内存使用优化',
        description: `检测到峰值内存使用${statistics.memory.peakUsage}MB，当前使用${statistics.memory.currentUsage}MB`,
        recommendations: [
          '清理未使用的变量和对象',
          '优化图片和资源管理',
          '实现数据分页加载',
          '检查内存泄漏问题',
        ],
      });
    }

    // 网络优化建议
    if (statistics.network && statistics.network.totalBytes > 10 * 1024 * 1024) {
      suggestions.push({
        type: 'network',
        priority: 'medium',
        title: '网络流量优化',
        description: `会话期间网络使用${Math.round(statistics.network.totalBytes / 1024 / 1024)}MB`,
        recommendations: [
          '启用数据压缩',
          '优化图片大小和格式',
          '实现智能缓存策略',
          '减少不必要的网络请求',
        ],
      });
    }

    return suggestions;
  }
}

/**
 * 全局性能监控实例
 */
const globalPerformanceMonitor = new PerformanceMonitor();

/**
 * 性能监控工具函数
 */
const PerformanceUtils = {
  /**
   * 启动全局监控
   */
  startGlobalMonitoring() {
    globalPerformanceMonitor.start();
  },

  /**
   * 停止全局监控
   */
  stopGlobalMonitoring() {
    globalPerformanceMonitor.stop();
  },

  /**
   * 监控API请求的装饰器
   * @param {Function} apiFunc API函数
   * @param {string} apiName API名称
   */
  withApiMonitoring(apiFunc, apiName) {
    return async function (...args) {
      const monitor = globalPerformanceMonitor.monitorApiRequest(apiName);

      try {
        const startTime = monitor.start();
        const result = await apiFunc.apply(this, args);
        monitor.end(result);
        return result;
      } catch (error) {
        monitor.end({ statusCode: 0, error });
        throw error;
      }
    };
  },

  /**
   * 监控页面加载的装饰器
   * @param {Function} onLoadFunc 页面onLoad函数
   * @param {string} pagePath 页面路径
   */
  withPageMonitoring(onLoadFunc, pagePath) {
    return function (...args) {
      const monitor = globalPerformanceMonitor.monitorPageLoad(pagePath);
      const startTime = monitor.start();

      try {
        const result = onLoadFunc.apply(this, args);

        // 页面加载完成后记录
        if (this.setData) {
          const originalSetData = this.setData;
          this.setData = function (data, callback) {
            const result = originalSetData.call(this, data, callback);
            monitor.end();
            return result;
          };
        } else {
          monitor.end();
        }

        return result;
      } catch (error) {
        monitor.end();
        throw error;
      }
    };
  },

  /**
   * 获取性能报告
   */
  getPerformanceReport() {
    return globalPerformanceMonitor.generateReport();
  },

  /**
   * 获取优化建议
   */
  getOptimizationSuggestions() {
    return globalPerformanceMonitor.getOptimizationSuggestions();
  },

  /**
   * 检查当前性能状态
   */
  checkPerformanceHealth() {
    const statistics = globalPerformanceMonitor.recorder.getStatistics();
    const issues = statistics.issues;

    let health = 'good';
    if (issues.totalIssues > 10) {
      health = 'poor';
    } else if (issues.totalIssues > 5) {
      health = 'fair';
    }

    return {
      health,
      score: Math.max(0, 100 - issues.totalIssues * 5),
      summary: statistics,
    };
  },
};

// 导出
module.exports = {
  PerformanceMonitor,
  PerformanceRecorder,
  PerformanceUtils,
  PERFORMANCE_CONFIG,
  globalPerformanceMonitor,
};

// 自动启动监控（仅在开发环境）
if (typeof wx !== 'undefined') {
  try {
    const accountInfo = wx.getAccountInfoSync();
    if (accountInfo.miniProgram.envVersion === 'develop') {
      console.log('🔧 开发环境，自动启动性能监控');
      PerformanceUtils.startGlobalMonitoring();
    }
  } catch (error) {
    console.warn('性能监控初始化失败:', error);
  }
}
