// 用户体验优化工具模块 - 续
// 操作反馈管理器和离线功能管理器

/**
 * 操作反馈管理器
 */
class FeedbackManager {
  constructor() {
    this.loadingStack = [];
    this.operationQueue = [];
  }

  /**
   * 显示加载状态
   */
  showLoading(title = '加载中...', options = {}) {
    const loadingId = `loading_${Date.now()}`;
    this.loadingStack.push(loadingId);

    wx.showLoading({
      title,
      mask: options.mask !== false,
      ...options,
    });

    return loadingId;
  }

  /**
   * 隐藏加载状态
   */
  hideLoading(loadingId) {
    if (loadingId) {
      this.loadingStack = this.loadingStack.filter(id => id !== loadingId);
    } else {
      this.loadingStack.pop();
    }

    if (this.loadingStack.length === 0) {
      wx.hideLoading();
    }
  }

  /**
   * 显示操作成功提示
   */
  showSuccess(title, options = {}) {
    wx.showToast({
      title,
      icon: 'success',
      duration: options.duration || 2000,
      mask: options.mask || false,
    });
  }

  /**
   * 显示操作失败提示
   */
  showError(title, options = {}) {
    wx.showToast({
      title,
      icon: 'error',
      duration: options.duration || 3000,
      mask: options.mask || false,
    });
  }

  /**
   * 显示确认对话框
   */
  showConfirm(title, content, options = {}) {
    return new Promise(resolve => {
      wx.showModal({
        title,
        content,
        showCancel: options.showCancel !== false,
        cancelText: options.cancelText || '取消',
        confirmText: options.confirmText || '确定',
        success: res => {
          resolve(res.confirm);
        },
        fail: () => {
          resolve(false);
        },
      });
    });
  }
}

/**
 * 离线功能管理器
 */
class OfflineManager {
  constructor() {
    this.isOnline = true;
    this.offlineQueue = [];
    this.offlineData = new Map();
    this.syncInProgress = false;
  }

  /**
   * 初始化离线管理器
   */
  init() {
    // 监听网络状态变化
    wx.onNetworkStatusChange(res => {
      const wasOffline = !this.isOnline;
      this.isOnline = res.isConnected;

      if (wasOffline && this.isOnline) {
        console.log('网络已恢复，开始同步离线数据');
        this.syncOfflineData();
      } else if (!this.isOnline) {
        console.log('网络已断开，启用离线模式');
        this.showOfflineNotice();
      }
    });

    // 检查当前网络状态
    wx.getNetworkType({
      success: res => {
        this.isOnline = res.networkType !== 'none';
      },
    });

    // 加载离线数据
    this.loadOfflineData();
  }

  /**
   * 显示离线提示
   */
  showOfflineNotice() {
    wx.showToast({
      title: '当前处于离线状态',
      icon: 'none',
      duration: 3000,
    });
  }

  /**
   * 加载离线数据
   */
  loadOfflineData() {
    try {
      const offlineData = wx.getStorageSync('offline_data');
      if (offlineData) {
        this.offlineData = new Map(JSON.parse(offlineData));
      }

      const offlineQueue = wx.getStorageSync('offline_queue');
      if (offlineQueue) {
        this.offlineQueue = JSON.parse(offlineQueue);
      }
    } catch (error) {
      console.warn('加载离线数据失败:', error);
    }
  }

  /**
   * 保存离线数据
   */
  saveOfflineData() {
    try {
      wx.setStorageSync('offline_data', JSON.stringify(Array.from(this.offlineData.entries())));
      wx.setStorageSync('offline_queue', JSON.stringify(this.offlineQueue));
    } catch (error) {
      console.warn('保存离线数据失败:', error);
    }
  }

  /**
   * 添加离线操作到队列
   */
  addOfflineOperation(operation) {
    this.offlineQueue.push({
      ...operation,
      timestamp: Date.now(),
      id: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    });

    this.saveOfflineData();
    console.log('添加离线操作:', operation);
  }

  /**
   * 同步离线数据
   */
  async syncOfflineData() {
    if (this.syncInProgress || !this.isOnline) {
      return;
    }

    this.syncInProgress = true;
    let syncedCount = 0;
    let failedCount = 0;

    try {
      wx.showLoading({ title: '同步数据中...' });

      for (const operation of this.offlineQueue) {
        try {
          await this.executeOfflineOperation(operation);
          syncedCount++;
        } catch (error) {
          console.error('同步操作失败:', operation, error);
          failedCount++;
        }
      }

      // 清空已同步的操作
      this.offlineQueue = [];
      this.saveOfflineData();

      wx.hideLoading();

      if (syncedCount > 0) {
        wx.showToast({
          title: `已同步 ${syncedCount} 条数据`,
          icon: 'success',
        });
      }

      if (failedCount > 0) {
        wx.showToast({
          title: `${failedCount} 条数据同步失败`,
          icon: 'none',
        });
      }
    } catch (error) {
      wx.hideLoading();
      console.error('数据同步失败:', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  /**
   * 执行离线操作
   */
  async executeOfflineOperation(operation) {
    const api = require('../api/index.js');

    switch (operation.type) {
      case 'homework_submit':
        return await api.homework.submit(operation.data);
      case 'qa_question':
        return await api.qa.askQuestion(operation.data);
      case 'feedback_submit':
        return await api.feedback.submit(operation.data);
      default:
        throw new Error(`未知的离线操作类型: ${operation.type}`);
    }
  }

  /**
   * 获取离线数据
   */
  getOfflineData(key) {
    return this.offlineData.get(key);
  }

  /**
   * 设置离线数据
   */
  setOfflineData(key, data) {
    this.offlineData.set(key, {
      data,
      timestamp: Date.now(),
    });
    this.saveOfflineData();
  }

  /**
   * 检查是否有离线数据
   */
  hasOfflineOperations() {
    return this.offlineQueue.length > 0;
  }
}

// 创建全局实例
const feedbackManager = new FeedbackManager();
const offlineManager = new OfflineManager();

// 初始化离线管理器
offlineManager.init();

// 导出类和实例
module.exports = {
  FeedbackManager,
  OfflineManager,
  feedbackManager,
  offlineManager,
};
