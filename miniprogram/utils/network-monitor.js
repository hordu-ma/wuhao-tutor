// utils/network-monitor.js
// 网络状态监控器 - 五好伴学微信小程序

const storage = require('./storage.js');

/**
 * 网络状态监控器类
 */
class NetworkMonitor {
  constructor() {
    // 当前网络状态
    this.currentStatus = {
      isConnected: true,
      networkType: 'unknown',
      signalStrength: 0,
      latency: 0,
      bandwidth: 0,
      isMetered: false,
      lastCheckTime: 0
    };

    // 状态变化监听器
    this.listeners = [];

    // 监控配置
    this.config = {
      // 网络检查间隔(毫秒)
      checkInterval: 30000,
      // 延迟检测超时(毫秒)
      latencyTimeout: 5000,
      // 带宽检测超时(毫秒)
      bandwidthTimeout: 10000,
      // 延迟检测URL
      latencyTestUrl: 'https://www.baidu.com/favicon.ico',
      // 带宽检测数据大小(字节)
      bandwidthTestSize: 1024 * 100, // 100KB
      // 历史记录最大数量
      maxHistorySize: 100
    };

    // 网络历史记录
    this.history = [];

    // 定时器
    this.checkTimer = null;
    this.latencyTimer = null;

    // 初始化
    this.init();
  }

  /**
   * 初始化网络监控器
   */
  async init() {
    try {
      // 获取初始网络状态
      await this.updateNetworkStatus();

      // 监听网络状态变化
      this.setupNetworkListeners();

      // 启动定期检查
      this.startPeriodicCheck();

      // 恢复历史记录
      await this.loadHistory();

      console.log('网络监控器初始化成功', this.currentStatus);
    } catch (error) {
      console.error('网络监控器初始化失败', error);
    }
  }

  /**
   * 设置网络状态监听器
   */
  setupNetworkListeners() {
    // 监听网络状态变化
    wx.onNetworkStatusChange((res) => {
      console.log('网络状态发生变化', res);
      this.handleNetworkStatusChange(res);
    });

    // 小程序前台/后台切换时检查网络状态
    wx.onAppShow(() => {
      setTimeout(() => {
        this.updateNetworkStatus();
      }, 1000);
    });
  }

  /**
   * 处理网络状态变化
   */
  async handleNetworkStatusChange(res) {
    try {
      const oldStatus = { ...this.currentStatus };

      // 更新基础网络信息
      this.currentStatus.isConnected = res.isConnected;
      this.currentStatus.networkType = res.networkType || 'unknown';
      this.currentStatus.lastCheckTime = Date.now();

      // 如果网络重新连接，进行详细检测
      if (res.isConnected && !oldStatus.isConnected) {
        await this.performDetailedCheck();
      }

      // 记录历史
      this.addToHistory(this.currentStatus);

      // 通知监听器
      this.notifyListeners(this.currentStatus, oldStatus);

      console.log('网络状态已更新', this.currentStatus);
    } catch (error) {
      console.error('处理网络状态变化失败', error);
    }
  }

  /**
   * 更新网络状态
   */
  async updateNetworkStatus() {
    try {
      // 获取网络信息
      const networkInfo = await this.getNetworkInfo();

      const oldStatus = { ...this.currentStatus };

      // 更新基础信息
      this.currentStatus.isConnected = networkInfo.isConnected;
      this.currentStatus.networkType = networkInfo.networkType;
      this.currentStatus.lastCheckTime = Date.now();

      // 如果有网络连接，进行详细检测
      if (networkInfo.isConnected) {
        await this.performDetailedCheck();
      } else {
        // 无网络连接时重置指标
        this.currentStatus.signalStrength = 0;
        this.currentStatus.latency = 0;
        this.currentStatus.bandwidth = 0;
      }

      // 记录历史
      this.addToHistory(this.currentStatus);

      // 通知监听器
      this.notifyListeners(this.currentStatus, oldStatus);

    } catch (error) {
      console.error('更新网络状态失败', error);
    }
  }

  /**
   * 获取网络信息
   */
  getNetworkInfo() {
    return new Promise((resolve) => {
      wx.getNetworkType({
        success: (res) => {
          resolve({
            isConnected: res.networkType !== 'none',
            networkType: res.networkType
          });
        },
        fail: () => {
          resolve({
            isConnected: false,
            networkType: 'none'
          });
        }
      });
    });
  }

  /**
   * 执行详细网络检测
   */
  async performDetailedCheck() {
    try {
      // 并行执行延迟和带宽检测
      const [latency, bandwidth] = await Promise.allSettled([
        this.measureLatency(),
        this.measureBandwidth()
      ]);

      // 更新延迟
      if (latency.status === 'fulfilled') {
        this.currentStatus.latency = latency.value;
      }

      // 更新带宽
      if (bandwidth.status === 'fulfilled') {
        this.currentStatus.bandwidth = bandwidth.value;
      }

      // 更新信号强度（基于延迟和网络类型估算）
      this.currentStatus.signalStrength = this.calculateSignalStrength();

      // 判断是否为计费网络
      this.currentStatus.isMetered = this.isMeteredNetwork();

    } catch (error) {
      console.error('详细网络检测失败', error);
    }
  }

  /**
   * 测量网络延迟
   */
  measureLatency() {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const timer = setTimeout(() => {
        reject(new Error('延迟检测超时'));
      }, this.config.latencyTimeout);

      wx.request({
        url: this.config.latencyTestUrl,
        method: 'HEAD',
        success: () => {
          clearTimeout(timer);
          const latency = Date.now() - startTime;
          resolve(latency);
        },
        fail: (error) => {
          clearTimeout(timer);
          reject(new Error('延迟检测失败: ' + error.errMsg));
        }
      });
    });
  }

  /**
   * 测量网络带宽
   */
  measureBandwidth() {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      let loaded = 0;

      const timer = setTimeout(() => {
        reject(new Error('带宽检测超时'));
      }, this.config.bandwidthTimeout);

      // 构造一个用于测试的URL（实际项目中需要替换为真实的测试文件）
      const testUrl = `${this.config.latencyTestUrl}?t=${Date.now()}&size=${this.config.bandwidthTestSize}`;

      wx.request({
        url: testUrl,
        method: 'GET',
        success: (res) => {
          clearTimeout(timer);
          const duration = Date.now() - startTime;

          // 估算下载的数据大小
          const dataSize = JSON.stringify(res.data || '').length || this.config.bandwidthTestSize;

          // 计算带宽 (Mbps)
          const bandwidth = (dataSize * 8) / (duration / 1000) / 1024 / 1024;
          resolve(Math.round(bandwidth * 100) / 100);
        },
        fail: (error) => {
          clearTimeout(timer);
          reject(new Error('带宽检测失败: ' + error.errMsg));
        }
      });
    });
  }

  /**
   * 计算信号强度
   */
  calculateSignalStrength() {
    const { latency, networkType } = this.currentStatus;

    // 基于网络类型的基础分数
    const baseScore = {
      'wifi': 90,
      '5g': 85,
      '4g': 75,
      '3g': 50,
      '2g': 20,
      'unknown': 60,
      'none': 0
    }[networkType] || 60;

    // 基于延迟调整分数
    let latencyScore = 100;
    if (latency > 0) {
      if (latency < 50) latencyScore = 100;
      else if (latency < 100) latencyScore = 90;
      else if (latency < 200) latencyScore = 75;
      else if (latency < 500) latencyScore = 50;
      else if (latency < 1000) latencyScore = 25;
      else latencyScore = 10;
    }

    // 综合计算信号强度
    const signalStrength = Math.round((baseScore * 0.6 + latencyScore * 0.4));
    return Math.max(0, Math.min(100, signalStrength));
  }

  /**
   * 判断是否为计费网络
   */
  isMeteredNetwork() {
    const { networkType } = this.currentStatus;
    return ['2g', '3g', '4g', '5g'].includes(networkType);
  }

  /**
   * 启动定期检查
   */
  startPeriodicCheck() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
    }

    this.checkTimer = setInterval(() => {
      this.updateNetworkStatus();
    }, this.config.checkInterval);

    console.log('网络状态定期检查已启动');
  }

  /**
   * 停止定期检查
   */
  stopPeriodicCheck() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
      console.log('网络状态定期检查已停止');
    }
  }

  /**
   * 添加状态变化监听器
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
   * 移除状态变化监听器
   */
  removeListener(listener) {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  /**
   * 通知所有监听器
   */
  notifyListeners(currentStatus, previousStatus) {
    this.listeners.forEach(listener => {
      try {
        listener(currentStatus, previousStatus);
      } catch (error) {
        console.error('网络状态监听器执行失败', error);
      }
    });
  }

  /**
   * 添加到历史记录
   */
  addToHistory(status) {
    const historyItem = {
      ...status,
      timestamp: Date.now()
    };

    this.history.push(historyItem);

    // 限制历史记录数量
    if (this.history.length > this.config.maxHistorySize) {
      this.history.shift();
    }

    // 保存到本地存储
    this.saveHistory();
  }

  /**
   * 保存历史记录
   */
  async saveHistory() {
    try {
      await storage.set('network_history', this.history);
    } catch (error) {
      console.error('保存网络历史记录失败', error);
    }
  }

  /**
   * 加载历史记录
   */
  async loadHistory() {
    try {
      const history = await storage.get('network_history');
      if (Array.isArray(history)) {
        this.history = history;
      }
    } catch (error) {
      console.error('加载网络历史记录失败', error);
      this.history = [];
    }
  }

  /**
   * 获取当前网络状态
   */
  getCurrentStatus() {
    return { ...this.currentStatus };
  }

  /**
   * 获取网络历史记录
   */
  getHistory(limit = 50) {
    return this.history.slice(-limit).map(item => ({ ...item }));
  }

  /**
   * 获取网络质量评级
   */
  getNetworkQuality() {
    const { isConnected, latency, bandwidth, signalStrength } = this.currentStatus;

    if (!isConnected) {
      return {
        grade: 'F',
        score: 0,
        description: '无网络连接'
      };
    }

    // 计算综合分数
    let score = 0;

    // 信号强度权重 40%
    score += signalStrength * 0.4;

    // 延迟权重 35%
    if (latency > 0) {
      let latencyScore = 100;
      if (latency < 50) latencyScore = 100;
      else if (latency < 100) latencyScore = 90;
      else if (latency < 200) latencyScore = 75;
      else if (latency < 500) latencyScore = 50;
      else latencyScore = 25;

      score += latencyScore * 0.35;
    }

    // 带宽权重 25%
    if (bandwidth > 0) {
      let bandwidthScore = 100;
      if (bandwidth >= 10) bandwidthScore = 100;
      else if (bandwidth >= 5) bandwidthScore = 90;
      else if (bandwidth >= 2) bandwidthScore = 75;
      else if (bandwidth >= 1) bandwidthScore = 50;
      else bandwidthScore = 25;

      score += bandwidthScore * 0.25;
    }

    // 确定等级
    let grade, description;
    if (score >= 90) {
      grade = 'A';
      description = '网络质量优秀';
    } else if (score >= 80) {
      grade = 'B';
      description = '网络质量良好';
    } else if (score >= 70) {
      grade = 'C';
      description = '网络质量一般';
    } else if (score >= 60) {
      grade = 'D';
      description = '网络质量较差';
    } else {
      grade = 'F';
      description = '网络质量很差';
    }

    return {
      grade,
      score: Math.round(score),
      description
    };
  }

  /**
   * 检查网络是否适合某种操作
   */
  isNetworkSuitableFor(operation) {
    const { isConnected, networkType, latency, bandwidth } = this.currentStatus;

    if (!isConnected) {
      return {
        suitable: false,
        reason: '无网络连接'
      };
    }

    const requirements = {
      // 文本聊天
      'chat': {
        minLatency: 1000,
        minBandwidth: 0.1,
        allowedNetworks: ['wifi', '5g', '4g', '3g', '2g']
      },
      // 图片上传
      'image_upload': {
        minLatency: 500,
        minBandwidth: 1,
        allowedNetworks: ['wifi', '5g', '4g', '3g']
      },
      // 文件上传
      'file_upload': {
        minLatency: 300,
        minBandwidth: 2,
        allowedNetworks: ['wifi', '5g', '4g']
      },
      // 视频通话
      'video_call': {
        minLatency: 200,
        minBandwidth: 5,
        allowedNetworks: ['wifi', '5g', '4g']
      },
      // 大文件下载
      'large_download': {
        minLatency: 500,
        minBandwidth: 3,
        allowedNetworks: ['wifi', '5g', '4g']
      }
    };

    const requirement = requirements[operation];
    if (!requirement) {
      return {
        suitable: true,
        reason: '未知操作类型，默认允许'
      };
    }

    // 检查网络类型
    if (!requirement.allowedNetworks.includes(networkType)) {
      return {
        suitable: false,
        reason: `当前网络类型 ${networkType} 不适合进行${operation}操作`
      };
    }

    // 检查延迟
    if (latency > 0 && latency > requirement.minLatency) {
      return {
        suitable: false,
        reason: `网络延迟过高 (${latency}ms > ${requirement.minLatency}ms)`
      };
    }

    // 检查带宽
    if (bandwidth > 0 && bandwidth < requirement.minBandwidth) {
      return {
        suitable: false,
        reason: `网络带宽不足 (${bandwidth}Mbps < ${requirement.minBandwidth}Mbps)`
      };
    }

    return {
      suitable: true,
      reason: '网络状况良好'
    };
  }

  /**
   * 强制刷新网络状态
   */
  async refresh() {
    console.log('强制刷新网络状态');
    await this.updateNetworkStatus();
    return this.getCurrentStatus();
  }

  /**
   * 清理资源
   */
  destroy() {
    this.stopPeriodicCheck();
    this.listeners = [];
    this.history = [];
    console.log('网络监控器已销毁');
  }

  /**
   * 获取网络统计信息
   */
  getStatistics() {
    if (this.history.length === 0) {
      return null;
    }

    const recentHistory = this.history.slice(-20); // 最近20次记录

    const latencies = recentHistory.filter(h => h.latency > 0).map(h => h.latency);
    const bandwidths = recentHistory.filter(h => h.bandwidth > 0).map(h => h.bandwidth);
    const signalStrengths = recentHistory.map(h => h.signalStrength);

    const calculateStats = (values) => {
      if (values.length === 0) return { min: 0, max: 0, avg: 0 };

      const min = Math.min(...values);
      const max = Math.max(...values);
      const avg = values.reduce((sum, val) => sum + val, 0) / values.length;

      return { min, max, avg: Math.round(avg * 100) / 100 };
    };

    return {
      latency: calculateStats(latencies),
      bandwidth: calculateStats(bandwidths),
      signalStrength: calculateStats(signalStrengths),
      sampleCount: recentHistory.length,
      timeRange: {
        start: recentHistory[0]?.timestamp,
        end: recentHistory[recentHistory.length - 1]?.timestamp
      }
    };
  }
}

// 创建单例实例
const networkMonitor = new NetworkMonitor();

module.exports = {
  networkMonitor,

  // 导出常用方法
  getCurrentStatus: () => networkMonitor.getCurrentStatus(),
  addListener: (listener) => networkMonitor.addListener(listener),
  removeListener: (listener) => networkMonitor.removeListener(listener),
  getNetworkQuality: () => networkMonitor.getNetworkQuality(),
  isNetworkSuitableFor: (operation) => networkMonitor.isNetworkSuitableFor(operation),
  refresh: () => networkMonitor.refresh(),
  getHistory: (limit) => networkMonitor.getHistory(limit),
  getStatistics: () => networkMonitor.getStatistics(),

  // 工具方法
  isConnected: () => networkMonitor.getCurrentStatus().isConnected,
  isWifi: () => networkMonitor.getCurrentStatus().networkType === 'wifi',
  isMobile: () => ['2g', '3g', '4g', '5g'].includes(networkMonitor.getCurrentStatus().networkType),
  isHighSpeed: () => ['wifi', '5g', '4g'].includes(networkMonitor.getCurrentStatus().networkType),
  isMetered: () => networkMonitor.getCurrentStatus().isMetered
};
