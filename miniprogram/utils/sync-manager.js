// utils/sync-manager.js - 信息同步管理器

const { authManager } = require('./auth.js');
const { apiClient } = require('./api.js');
const { storage } = require('./storage.js');
const { networkMonitor } = require('./network-monitor.js');
const { profileErrorHandler } = require('./profile-error-handler.js');

/**
 * 同步状态枚举
 */
const SyncStatus = {
  IDLE: 'idle',
  SYNCING: 'syncing',
  SUCCESS: 'success',
  FAILED: 'failed',
  CONFLICT: 'conflict',
};

/**
 * 同步策略枚举
 */
const SyncStrategy = {
  LOCAL_FIRST: 'local_first', // 本地优先
  SERVER_FIRST: 'server_first', // 服务端优先
  MANUAL_RESOLVE: 'manual_resolve', // 手动解决冲突
  TIMESTAMP_BASED: 'timestamp_based', // 基于时间戳
};

/**
 * 信息同步管理器
 */
class SyncManager {
  constructor() {
    this.syncStatus = SyncStatus.IDLE;
    this.syncQueue = [];
    this.conflictQueue = [];
    this.lastSyncTime = 0;
    this.syncInterval = 30 * 60 * 1000; // 30分钟自动同步间隔（降低频率，减少失败）
    this.syncTimer = null;
    this.listeners = new Set();

    // 同步配置
    this.config = {
      enableAutoSync: true,
      syncStrategy: SyncStrategy.TIMESTAMP_BASED,
      conflictResolution: SyncStrategy.MANUAL_RESOLVE,
      maxRetries: 3,
      retryDelay: 2000,
      batchSize: 10,
    };

    this.initSyncManager();
  }

  /**
   * 初始化同步管理器
   */
  initSyncManager() {
    // 监听网络状态变化
    networkMonitor.addListener((currentStatus, previousStatus) => {
      if (!previousStatus.isConnected && currentStatus.isConnected) {
        // 网络恢复时自动同步
        console.log('网络恢复，开始自动同步');
        this.triggerSync();
      }
    });

    // 启动定时同步
    this.startAutoSync();

    // 监听应用生命周期
    this.setupAppLifecycleListeners();
  }

  /**
   * 设置应用生命周期监听
   */
  setupAppLifecycleListeners() {
    // 小程序显示时同步
    const originalOnShow = App.onShow;
    App.onShow = (...args) => {
      if (originalOnShow) {
        originalOnShow.apply(this, args);
      }
      this.onAppShow();
    };

    // 小程序隐藏时停止同步
    const originalOnHide = App.onHide;
    App.onHide = (...args) => {
      if (originalOnHide) {
        originalOnHide.apply(this, args);
      }
      this.onAppHide();
    };
  }

  /**
   * 应用显示时的处理
   */
  async onAppShow() {
    try {
      // 检查是否需要同步（超过5分钟）
      const now = Date.now();
      if (now - this.lastSyncTime > this.syncInterval) {
        await this.triggerSync();
      }
    } catch (error) {
      console.error('应用显示时同步失败:', error);
    }
  }

  /**
   * 应用隐藏时的处理
   */
  onAppHide() {
    // 停止自动同步定时器
    this.stopAutoSync();
  }

  /**
   * 启动自动同步
   */
  startAutoSync() {
    if (!this.config.enableAutoSync) {
      return;
    }

    this.stopAutoSync(); // 先停止已有的定时器

    this.syncTimer = setInterval(async () => {
      try {
        await this.triggerSync();
      } catch (error) {
        console.error('自动同步失败:', error);
      }
    }, this.syncInterval);

    console.log('自动同步已启动');
  }

  /**
   * 停止自动同步
   */
  stopAutoSync() {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
      console.log('自动同步已停止');
    }
  }

  /**
   * 触发同步
   */
  async triggerSync(options = {}) {
    if (this.syncStatus === SyncStatus.SYNCING) {
      console.log('同步正在进行中，跳过此次触发');
      return { success: false, reason: 'syncing' };
    }

    // 检查网络状态
    const networkStatus = networkMonitor.getCurrentStatus();
    if (!networkStatus.isConnected) {
      console.log('网络未连接，跳过同步');
      return { success: false, reason: 'no_network' };
    }

    try {
      this.setSyncStatus(SyncStatus.SYNCING);

      await this.performSync(options);

      this.setSyncStatus(SyncStatus.SUCCESS);
      this.lastSyncTime = Date.now();

      console.log('同步完成');
      return { success: true };
    } catch (error) {
      console.error('同步失败:', error);
      this.setSyncStatus(SyncStatus.FAILED);
      // 静默失败，不抛出错误，避免影响页面加载
      return { success: false, reason: 'sync_error', error };
    }
  }

  /**
   * 执行同步
   */
  async performSync(options = {}) {
    const syncTasks = [];

    // 用户信息同步
    if (options.userInfo !== false) {
      syncTasks.push(this.syncUserInfo());
    }

    // 用户设置同步
    if (options.userSettings !== false) {
      syncTasks.push(this.syncUserSettings());
    }

    // 缓存数据同步
    if (options.cacheData !== false) {
      syncTasks.push(this.syncCacheData());
    }

    // 并行执行同步任务
    await Promise.allSettled(syncTasks);
  }

  /**
   * 同步用户信息
   */
  async syncUserInfo() {
    try {
      console.log('开始同步用户信息');

      // 防御性检查：确保 authManager 可用
      if (!authManager || typeof authManager.getUserInfo !== 'function') {
        console.warn('[Sync] authManager 不可用，跳过用户信息同步');
        return;
      }

      // 获取本地用户信息
      const localUserInfo = await authManager.getUserInfo();
      const localTimestamp = authManager.getUserInfoCacheTime();

      // 防御性检查：确保 apiClient 可用
      if (!apiClient || typeof apiClient.get !== 'function') {
        console.warn('[Sync] apiClient 不可用，使用本地缓存');
        return;
      }

      // 获取服务器用户信息
      const response = await apiClient.get('/auth/me');

      if (!response.success || !response.data) {
        // 静默失败，使用本地缓存
        console.warn('[Sync] 服务器用户信息获取失败，继续使用本地缓存');
        return;
      }

      const serverUserInfo = response.data;
      const serverTimestamp = new Date(
        serverUserInfo.updated_at || serverUserInfo.updatedAt,
      ).getTime();

      // 比较时间戳决定同步策略
      const syncResult = await this.resolveUserInfoConflict(
        localUserInfo,
        serverUserInfo,
        localTimestamp,
        serverTimestamp,
      );

      if (syncResult.needsUpdate) {
        await authManager.updateUserInfo(syncResult.mergedInfo);
        console.log('[Sync] 用户信息同步完成');
      } else {
        console.log('[Sync] 用户信息无需同步');
      }
    } catch (error) {
      // 完全静默失败，不调用复杂的错误处理器，避免二次错误
      // 只输出简单的警告日志，不影响页面加载
      console.warn('[Sync] 用户信息同步静默失败，使用本地缓存:', error.message || error);
      // 不抛出错误，不影响页面加载
    }
  }

  /**
   * 解决用户信息冲突
   */
  async resolveUserInfoConflict(localInfo, serverInfo, localTimestamp, serverTimestamp) {
    // 如果本地没有数据，直接使用服务器数据
    if (!localInfo) {
      return {
        needsUpdate: true,
        mergedInfo: this.normalizeUserInfo(serverInfo),
      };
    }

    // 如果服务器没有更新时间，使用本地数据
    if (!serverTimestamp) {
      return {
        needsUpdate: false,
        mergedInfo: localInfo,
      };
    }

    let mergedInfo;

    switch (this.config.syncStrategy) {
      case SyncStrategy.SERVER_FIRST:
        mergedInfo = this.normalizeUserInfo(serverInfo);
        break;

      case SyncStrategy.LOCAL_FIRST:
        mergedInfo = localInfo;
        break;

      case SyncStrategy.TIMESTAMP_BASED:
        if (serverTimestamp > localTimestamp) {
          // 服务器数据更新，使用服务器数据
          mergedInfo = this.normalizeUserInfo(serverInfo);
        } else {
          // 本地数据更新或相同，保持本地数据
          mergedInfo = localInfo;
        }
        break;

      default:
        mergedInfo = this.mergeUserInfo(localInfo, serverInfo);
    }

    return {
      needsUpdate: JSON.stringify(mergedInfo) !== JSON.stringify(localInfo),
      mergedInfo,
    };
  }

  /**
   * 合并用户信息
   */
  mergeUserInfo(localInfo, serverInfo) {
    return {
      ...serverInfo,
      // 保留本地的一些字段
      avatarUrl: localInfo.avatarUrl || serverInfo.avatar_url,
      // 确保时间戳更新
      lastUpdated: Date.now(),
    };
  }

  /**
   * 标准化用户信息格式
   */
  normalizeUserInfo(serverInfo) {
    return {
      id: serverInfo.id,
      name: serverInfo.name,
      nickname: serverInfo.nickname,
      phone: serverInfo.phone,
      role: serverInfo.role,
      school: serverInfo.school,
      grade_level: serverInfo.grade_level,
      class_name: serverInfo.class_name,
      parent_contact: serverInfo.parent_contact,
      institution: serverInfo.institution,
      avatarUrl: serverInfo.avatar_url,
      avatar_url: serverInfo.avatar_url, // 兼容字段
      is_active: serverInfo.is_active,
      is_verified: serverInfo.is_verified,
      created_at: serverInfo.created_at,
      updated_at: serverInfo.updated_at,
      lastUpdated: Date.now(),
    };
  }

  /**
   * 同步用户设置
   */
  async syncUserSettings() {
    try {
      console.log('[Sync] 开始同步用户设置');

      // TODO: 实现用户设置同步逻辑
      // 这里可以扩展同步用户偏好设置、应用配置等
    } catch (error) {
      // 静默失败
      console.warn('[Sync] 用户设置同步静默失败:', error.message || error);
    }
  }

  /**
   * 同步缓存数据
   */
  async syncCacheData() {
    try {
      console.log('[Sync] 开始同步缓存数据');

      // 防御性检查：确保 storage 可用
      if (!storage || typeof storage.get !== 'function') {
        console.warn('[Sync] storage 不可用，跳过缓存同步');
        return;
      }

      // 清理过期缓存
      await this.cleanExpiredCache();

      // TODO: 同步其他缓存数据
    } catch (error) {
      // 静默失败
      console.warn('[Sync] 缓存数据同步静默失败:', error.message || error);
    }
  }

  /**
   * 清理过期缓存
   */
  async cleanExpiredCache() {
    try {
      const now = Date.now();
      const cacheKeys = ['userInfo', 'userRole', 'appSettings'];

      for (const key of cacheKeys) {
        const data = await storage.get(key);
        if (data && data.expiredAt && data.expiredAt < now) {
          await storage.remove(key);
          console.log(`已清理过期缓存: ${key}`);
        }
      }
    } catch (error) {
      console.error('清理缓存失败:', error);
    }
  }

  /**
   * 手动同步用户信息
   */
  async manualSyncUserInfo() {
    return this.triggerSync({
      userInfo: true,
      userSettings: false,
      cacheData: false,
    });
  }

  /**
   * 强制重新同步
   */
  async forceSync() {
    this.lastSyncTime = 0; // 重置最后同步时间
    return this.triggerSync();
  }

  /**
   * 设置同步状态
   */
  setSyncStatus(status) {
    const previousStatus = this.syncStatus;
    this.syncStatus = status;

    // 通知监听器
    this.notifyListeners({
      type: 'statusChange',
      previousStatus,
      currentStatus: status,
      timestamp: Date.now(),
    });
  }

  /**
   * 添加同步监听器
   */
  addSyncListener(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * 通知监听器
   */
  notifyListeners(event) {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (error) {
        console.error('同步监听器执行失败:', error);
      }
    }
  }

  /**
   * 获取同步状态
   */
  getSyncStatus() {
    return {
      status: this.syncStatus,
      lastSyncTime: this.lastSyncTime,
      nextSyncTime: this.lastSyncTime + this.syncInterval,
      isAutoSyncEnabled: !!this.syncTimer,
    };
  }

  /**
   * 更新同步配置
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };

    // 如果修改了自动同步设置，重新启动
    if ('enableAutoSync' in newConfig) {
      if (newConfig.enableAutoSync) {
        this.startAutoSync();
      } else {
        this.stopAutoSync();
      }
    }
  }
}

// 创建单例实例
const syncManager = new SyncManager();

module.exports = {
  syncManager,
  SyncManager,
  SyncStatus,
  SyncStrategy,
};
