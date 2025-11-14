/**
 * 会话管理器
 * 处理会话过期、自动刷新、安全退出等功能
 */

const { authManager } = require('./auth.js');
const storage = require('./storage.js');
const config = require('../config/index.js');

/**
 * 会话管理器
 */
class SessionManager {
  constructor() {
    this.sessionKey = 'current_session';
    this.sessionHistoryKey = 'session_history';
    this.refreshAttemptKey = 'refresh_attempts';

    // 会话配置
    this.config = {
      sessionTimeout: 24 * 60 * 60 * 1000, // 24小时
      refreshThreshold: 2 * 60 * 60 * 1000, // 2小时内刷新
      maxRefreshAttempts: 3,
      refreshRetryDelay: 5000,
      heartbeatInterval: 5 * 60 * 1000, // 5分钟心跳
      maxConcurrentSessions: 3,
      sessionWarningTime: 5 * 60 * 1000, // 5分钟警告
      enableAutoRefresh: true,
      enableSessionWarning: true,
    };

    // 运行时状态
    this.currentSession = null;
    this.refreshTimer = null;
    this.heartbeatTimer = null;
    this.warningShown = false;
    this.isRefreshing = false;

    this.init();
  }

  /**
   * 初始化会话管理器
   */
  async init() {
    try {
      // 恢复会话状态
      await this.restoreSession();

      // 启动心跳检测
      this.startHeartbeat();

      console.log('[SessionManager] 会话管理器初始化完成');
    } catch (error) {
      console.error('[SessionManager] 初始化失败:', error);
    }
  }

  /**
   * 创建新会话
   * @param {Object} loginData - 登录数据
   * @returns {Promise<Object>} 会话信息
   */
  async createSession(loginData) {
    try {
      console.log('[SessionManager] 创建新会话');

      const sessionId = this.generateSessionId();
      const now = Date.now();

      const session = {
        sessionId,
        userId: loginData.userInfo?.id,
        token: loginData.token,
        refreshToken: loginData.refreshToken,
        role: loginData.role || 'student',
        deviceInfo: loginData.deviceInfo || (await this.getDeviceInfo()),
        createdAt: now,
        lastActiveAt: now,
        expiresAt: now + this.config.sessionTimeout,
        status: 'active',
        loginMethod: loginData.loginMethod || 'wechat',
        ipAddress: loginData.ipAddress,
        userAgent: loginData.userAgent,
      };

      // 保存会话
      await this.saveSession(session);

      // 记录会话历史
      await this.recordSessionHistory('created', session);

      // 启动刷新定时器
      this.scheduleTokenRefresh(session);

      this.currentSession = session;

      return {
        success: true,
        session,
        message: '会话创建成功',
      };
    } catch (error) {
      console.error('[SessionManager] 创建会话失败:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * 恢复会话状态
   */
  async restoreSession() {
    try {
      const session = await storage.get(this.sessionKey);

      if (!session) {
        console.log('[SessionManager] 没有找到保存的会话');
        return false;
      }

      // 检查会话是否过期
      if (this.isSessionExpired(session)) {
        console.log('[SessionManager] 会话已过期，清理会话数据');
        await this.clearSession();
        return false;
      }

      // 检查token是否即将过期
      if (this.needsRefresh(session)) {
        console.log('[SessionManager] Token需要刷新');
        await this.refreshSession();
      } else {
        // 恢复会话状态
        this.currentSession = session;
        this.scheduleTokenRefresh(session);

        // 更新最后活动时间
        await this.updateSessionActivity();
      }

      return true;
    } catch (error) {
      console.error('[SessionManager] 恢复会话失败:', error);
      return false;
    }
  }

  /**
   * 刷新会话
   * @returns {Promise<Object>} 刷新结果
   */
  async refreshSession() {
    if (this.isRefreshing) {
      console.log('[SessionManager] 正在刷新中，跳过重复请求');
      return { success: false, reason: 'already_refreshing' };
    }

    try {
      this.isRefreshing = true;
      console.log('[SessionManager] 开始刷新会话');

      const currentSession = this.currentSession || (await storage.get(this.sessionKey));

      if (!currentSession) {
        throw new Error('没有有效的会话可以刷新');
      }

      // 检查刷新尝试次数
      const attemptCount = await this.getRefreshAttemptCount();
      if (attemptCount >= this.config.maxRefreshAttempts) {
        throw new Error('刷新尝试次数过多，需要重新登录');
      }

      // 调用刷新API
      const refreshResult = await this.callRefreshAPI(currentSession);

      if (refreshResult.success) {
        // 更新会话信息
        const updatedSession = {
          ...currentSession,
          token: refreshResult.data.token,
          refreshToken: refreshResult.data.refreshToken || currentSession.refreshToken,
          lastActiveAt: Date.now(),
          expiresAt: Date.now() + this.config.sessionTimeout,
          refreshCount: (currentSession.refreshCount || 0) + 1,
        };

        await this.saveSession(updatedSession);
        await this.recordSessionHistory('refreshed', updatedSession);
        await this.clearRefreshAttempts();

        // 重新调度刷新
        this.scheduleTokenRefresh(updatedSession);

        this.currentSession = updatedSession;

        console.log('[SessionManager] 会话刷新成功');
        return {
          success: true,
          session: updatedSession,
          message: '会话刷新成功',
        };
      } else {
        await this.incrementRefreshAttempts();
        throw new Error(refreshResult.error || '会话刷新失败');
      }
    } catch (error) {
      console.error('[SessionManager] 会话刷新失败:', error);

      // 如果是认证错误，直接清理会话
      if (
        error.message.includes('认证') ||
        error.message.includes('授权') ||
        error.message.includes('登录')
      ) {
        await this.expireSession('authentication_failed');
      }

      return {
        success: false,
        error: error.message,
      };
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * 调用刷新API
   * @param {Object} session - 当前会话
   * @returns {Promise<Object>} API响应
   */
  async callRefreshAPI(session) {
    try {
      const { apiClient } = require('./api.js');

      const response = await apiClient.request({
        url: '/auth/refresh',
        method: 'POST',
        header: {
          Authorization: `Bearer ${session.token}`,
        },
        data: {
          refreshToken: session.refreshToken,
          sessionId: session.sessionId,
        },
        timeout: config.api.timeout || 10000,
      });

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response.data;
      } else {
        throw new Error(`HTTP ${response.statusCode}: ${response.data?.message || '刷新失败'}`);
      }
    } catch (error) {
      console.error('[SessionManager] 调用刷新API失败:', error);
      throw error;
    }
  }

  /**
   * 检查会话是否过期
   * @param {Object} session - 会话对象
   * @returns {boolean} 是否过期
   */
  isSessionExpired(session) {
    if (!session || !session.expiresAt) {
      return true;
    }

    return Date.now() > session.expiresAt;
  }

  /**
   * 检查是否需要刷新
   * @param {Object} session - 会话对象
   * @returns {boolean} 是否需要刷新
   */
  needsRefresh(session) {
    if (!session || !session.expiresAt) {
      return true;
    }

    const timeUntilExpiry = session.expiresAt - Date.now();
    return timeUntilExpiry < this.config.refreshThreshold;
  }

  /**
   * 调度Token刷新
   * @param {Object} session - 会话对象
   */
  scheduleTokenRefresh(session) {
    // 清除现有定时器
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (!this.config.enableAutoRefresh) {
      return;
    }

    const timeUntilRefresh = Math.max(
      0,
      session.expiresAt - Date.now() - this.config.refreshThreshold,
    );

    console.log(`[SessionManager] 调度Token刷新，${Math.round(timeUntilRefresh / 1000)}秒后执行`);

    this.refreshTimer = setTimeout(async () => {
      await this.refreshSession();
    }, timeUntilRefresh);
  }

  /**
   * 启动心跳检测
   */
  startHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    this.heartbeatTimer = setInterval(async () => {
      await this.performHeartbeat();
    }, this.config.heartbeatInterval);

    console.log('[SessionManager] 心跳检测已启动');
  }

  /**
   * 执行心跳检测
   */
  async performHeartbeat() {
    try {
      const session = this.currentSession || (await storage.get(this.sessionKey));

      if (!session) {
        return;
      }

      // 检查会话状态
      if (this.isSessionExpired(session)) {
        console.log('[SessionManager] 心跳检测发现会话过期');
        await this.expireSession('expired');
        return;
      }

      // 检查是否需要显示过期警告
      if (this.config.enableSessionWarning && !this.warningShown) {
        const timeUntilExpiry = session.expiresAt - Date.now();
        if (timeUntilExpiry <= this.config.sessionWarningTime) {
          this.showSessionWarning(timeUntilExpiry);
        }
      }

      // 更新活动时间
      await this.updateSessionActivity();

      console.log('[SessionManager] 心跳检测完成');
    } catch (error) {
      console.error('[SessionManager] 心跳检测失败:', error);
    }
  }

  /**
   * 显示会话过期警告
   * @param {number} timeUntilExpiry - 距离过期的时间
   */
  showSessionWarning(timeUntilExpiry) {
    this.warningShown = true;

    const minutes = Math.ceil(timeUntilExpiry / 60000);

    wx.showModal({
      title: '会话即将过期',
      content: `您的登录状态将在${minutes}分钟后过期，是否延长会话？`,
      confirmText: '延长',
      cancelText: '稍后',
      success: async res => {
        if (res.confirm) {
          const refreshResult = await this.refreshSession();
          if (refreshResult.success) {
            wx.showToast({
              title: '会话已延长',
              icon: 'success',
            });
            this.warningShown = false;
          } else {
            wx.showToast({
              title: '延长失败，请重新登录',
              icon: 'error',
            });
          }
        }
      },
    });
  }

  /**
   * 更新会话活动时间
   */
  async updateSessionActivity() {
    try {
      const session = this.currentSession || (await storage.get(this.sessionKey));

      if (session) {
        session.lastActiveAt = Date.now();
        await this.saveSession(session);
        this.currentSession = session;
      }
    } catch (error) {
      console.error('[SessionManager] 更新会话活动时间失败:', error);
    }
  }

  /**
   * 会话过期处理
   * @param {string} reason - 过期原因
   */
  async expireSession(reason = 'expired') {
    try {
      console.log(`[SessionManager] 会话过期: ${reason}`);

      const session = this.currentSession || (await storage.get(this.sessionKey));

      if (session) {
        session.status = 'expired';
        session.expiredAt = Date.now();
        session.expiredReason = reason;

        await this.recordSessionHistory('expired', session);
      }

      // 清理会话数据
      await this.clearSession();

      // 通知用户
      this.handleSessionExpiry(reason);
    } catch (error) {
      console.error('[SessionManager] 处理会话过期失败:', error);
    }
  }

  /**
   * 处理会话过期
   * @param {string} reason - 过期原因
   */
  handleSessionExpiry(reason) {
    let title = '登录已过期';
    let content = '您的登录状态已过期，请重新登录';

    switch (reason) {
      case 'authentication_failed':
        title = '认证失败';
        content = '身份验证失败，请重新登录';
        break;
      case 'security_violation':
        title = '安全验证';
        content = '检测到安全异常，请重新登录';
        break;
      case 'user_logout':
        title = '已退出登录';
        content = '您已成功退出登录';
        break;
    }

    wx.showModal({
      title,
      content,
      showCancel: false,
      confirmText: '重新登录',
      success: () => {
        wx.reLaunch({
          url: '/pages/login/index',
        });
      },
    });
  }

  /**
   * 清理会话
   */
  async clearSession() {
    try {
      // 停止定时器
      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
        this.refreshTimer = null;
      }

      if (this.heartbeatTimer) {
        clearInterval(this.heartbeatTimer);
        this.heartbeatTimer = null;
      }

      // 清理会话数据
      await storage.remove(this.sessionKey);
      await this.clearRefreshAttempts();

      // 重置状态
      this.currentSession = null;
      this.warningShown = false;
      this.isRefreshing = false;

      console.log('[SessionManager] 会话已清理');
    } catch (error) {
      console.error('[SessionManager] 清理会话失败:', error);
    }
  }

  /**
   * 保存会话
   * @param {Object} session - 会话对象
   */
  async saveSession(session) {
    try {
      await storage.set(this.sessionKey, session);
    } catch (error) {
      console.error('[SessionManager] 保存会话失败:', error);
      throw error;
    }
  }

  /**
   * 记录会话历史
   * @param {string} action - 操作类型
   * @param {Object} session - 会话对象
   */
  async recordSessionHistory(action, session) {
    try {
      const history = (await storage.get(this.sessionHistoryKey)) || [];

      const record = {
        id: Date.now().toString(),
        sessionId: session.sessionId,
        action,
        timestamp: Date.now(),
        userId: session.userId,
        deviceInfo: session.deviceInfo,
        reason: session.expiredReason,
      };

      history.push(record);

      // 只保留最近50条记录
      if (history.length > 50) {
        history.splice(0, history.length - 50);
      }

      await storage.set(this.sessionHistoryKey, history);
    } catch (error) {
      console.error('[SessionManager] 记录会话历史失败:', error);
    }
  }

  /**
   * 生成会话ID
   * @returns {string} 会话ID
   */
  generateSessionId() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 9);
    return `${timestamp}-${random}`;
  }

  /**
   * 获取设备信息
   * @returns {Promise<Object>} 设备信息
   */
  async getDeviceInfo() {
    try {
      const systemInfo = wx.getSystemInfoSync();
      return {
        brand: systemInfo.brand,
        model: systemInfo.model,
        system: systemInfo.system,
        platform: systemInfo.platform,
      };
    } catch (error) {
      console.error('[SessionManager] 获取设备信息失败:', error);
      return {};
    }
  }

  /**
   * 获取刷新尝试次数
   * @returns {Promise<number>} 尝试次数
   */
  async getRefreshAttemptCount() {
    try {
      const data = await storage.get(this.refreshAttemptKey);
      return data?.count || 0;
    } catch (error) {
      return 0;
    }
  }

  /**
   * 增加刷新尝试次数
   */
  async incrementRefreshAttempts() {
    try {
      const data = (await storage.get(this.refreshAttemptKey)) || { count: 0 };
      data.count += 1;
      data.lastAttempt = Date.now();
      await storage.set(this.refreshAttemptKey, data);
    } catch (error) {
      console.error('[SessionManager] 增加刷新尝试次数失败:', error);
    }
  }

  /**
   * 清除刷新尝试次数
   */
  async clearRefreshAttempts() {
    try {
      await storage.remove(this.refreshAttemptKey);
    } catch (error) {
      console.error('[SessionManager] 清除刷新尝试次数失败:', error);
    }
  }

  /**
   * 获取当前会话
   * @returns {Promise<Object>} 当前会话
   */
  async getCurrentSession() {
    if (this.currentSession) {
      return this.currentSession;
    }

    try {
      const session = await storage.get(this.sessionKey);
      return session;
    } catch (error) {
      console.error('[SessionManager] 获取当前会话失败:', error);
      return null;
    }
  }

  /**
   * 获取会话历史
   * @returns {Promise<Array>} 会话历史
   */
  async getSessionHistory() {
    try {
      return (await storage.get(this.sessionHistoryKey)) || [];
    } catch (error) {
      console.error('[SessionManager] 获取会话历史失败:', error);
      return [];
    }
  }

  /**
   * 检查会话健康状态
   * @returns {Promise<Object>} 健康状态
   */
  async getSessionHealth() {
    try {
      const session = await this.getCurrentSession();

      if (!session) {
        return {
          status: 'no_session',
          message: '没有活动会话',
        };
      }

      if (this.isSessionExpired(session)) {
        return {
          status: 'expired',
          message: '会话已过期',
          expiredAt: session.expiresAt,
        };
      }

      const timeUntilExpiry = session.expiresAt - Date.now();
      const needsRefresh = this.needsRefresh(session);

      return {
        status: 'healthy',
        sessionId: session.sessionId,
        expiresAt: session.expiresAt,
        timeUntilExpiry,
        needsRefresh,
        lastActiveAt: session.lastActiveAt,
      };
    } catch (error) {
      console.error('[SessionManager] 检查会话健康状态失败:', error);
      return {
        status: 'error',
        message: error.message,
      };
    }
  }

  /**
   * 销毁会话管理器
   */
  destroy() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    this.currentSession = null;
    this.warningShown = false;
    this.isRefreshing = false;

    console.log('[SessionManager] 会话管理器已销毁');
  }
}

// 创建单例实例
const sessionManager = new SessionManager();

module.exports = {
  sessionManager,
  SessionManager,
};
