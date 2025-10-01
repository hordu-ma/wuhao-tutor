/**
 * 安全退出管理器
 * 处理安全退出、会话清理、数据销毁等功能
 */

const { authManager } = require('./auth.js');
const { sessionManager } = require('./session-manager.js');
const { accountBindingManager } = require('./account-security-manager.js');
const { abnormalLoginDetector } = require('./abnormal-login-detector.js');
const storage = require('./storage.js');

/**
 * 安全退出管理器
 */
class SecureLogoutManager {
  constructor() {
    this.logoutHistoryKey = 'logout_history';
    this.tempDataKey = 'temp_logout_data';
    
    // 退出配置
    this.config = {
      enableLogoutConfirmation: true,
      enableDataCleanup: true,
      enableLogoutAll: true,
      enableRemoteLogout: true,
      cleanupTimeout: 30000, // 30秒超时
      retryAttempts: 3,
      logoutMethods: ['normal', 'security', 'forced', 'expired']
    };
  }

  /**
   * 执行安全退出
   * @param {Object} options - 退出选项
   * @returns {Promise<Object>} 退出结果
   */
  async performSecureLogout(options = {}) {
    try {
      console.log('[SecureLogout] 开始执行安全退出', options);

      const {
        method = 'normal',
        logoutAllDevices = false,
        reason = 'user_initiated',
        skipConfirmation = false,
        cleanupLevel = 'standard'
      } = options;

      // 1. 退出确认
      if (this.config.enableLogoutConfirmation && !skipConfirmation) {
        const confirmed = await this.showLogoutConfirmation(method, logoutAllDevices);
        if (!confirmed) {
          return {
            success: false,
            reason: 'user_cancelled',
            message: '用户取消退出'
          };
        }
      }

      // 2. 记录退出开始
      const logoutSession = await this.startLogoutSession(method, reason, options);

      // 3. 执行退出步骤
      const logoutResult = await this.executeLogoutSteps(logoutSession);

      // 4. 完成退出记录
      await this.completeLogoutSession(logoutSession, logoutResult);

      return logoutResult;

    } catch (error) {
      console.error('[SecureLogout] 安全退出失败:', error);
      return {
        success: false,
        reason: 'logout_error',
        message: '退出过程发生错误',
        error: error.message
      };
    }
  }

  /**
   * 显示退出确认对话框
   * @param {string} method - 退出方式
   * @param {boolean} logoutAllDevices - 是否退出所有设备
   * @returns {Promise<boolean>} 是否确认退出
   */
  async showLogoutConfirmation(method, logoutAllDevices) {
    return new Promise((resolve) => {
      let title = '确认退出';
      let content = '确定要退出登录吗？';

      if (logoutAllDevices) {
        content = '确定要退出所有设备的登录吗？这将使您在其他设备上的登录失效。';
      }

      switch (method) {
        case 'security':
          title = '安全退出';
          content = '检测到安全异常，建议立即退出登录。确定要继续吗？';
          break;
        case 'forced':
          title = '强制退出';
          content = '系统将强制退出您的登录，确定要继续吗？';
          break;
      }

      wx.showModal({
        title,
        content,
        confirmText: '确定退出',
        cancelText: '取消',
        confirmColor: '#fa5151',
        success: (res) => {
          resolve(res.confirm);
        },
        fail: () => {
          resolve(false);
        }
      });
    });
  }

  /**
   * 开始退出会话
   * @param {string} method - 退出方式
   * @param {string} reason - 退出原因
   * @param {Object} options - 退出选项
   * @returns {Promise<Object>} 退出会话
   */
  async startLogoutSession(method, reason, options) {
    try {
      const currentSession = await sessionManager.getCurrentSession();
      const userInfo = await authManager.getUserInfo();

      const logoutSession = {
        id: Date.now().toString(),
        sessionId: currentSession?.sessionId,
        userId: userInfo?.id,
        method,
        reason,
        startTime: Date.now(),
        options,
        steps: [],
        status: 'in_progress',
        deviceInfo: await this.getDeviceInfo()
      };

      // 保存临时退出数据
      await storage.set(this.tempDataKey, logoutSession);

      return logoutSession;

    } catch (error) {
      console.error('[SecureLogout] 创建退出会话失败:', error);
      throw error;
    }
  }

  /**
   * 执行退出步骤
   * @param {Object} logoutSession - 退出会话
   * @returns {Promise<Object>} 退出结果
   */
  async executeLogoutSteps(logoutSession) {
    const steps = [];
    let overallSuccess = true;
    let lastError = null;

    try {
      // 步骤1: 通知服务器退出
      if (this.config.enableRemoteLogout) {
        const serverLogoutResult = await this.performServerLogout(logoutSession);
        steps.push({
          step: 'server_logout',
          success: serverLogoutResult.success,
          timestamp: Date.now(),
          message: serverLogoutResult.message,
          error: serverLogoutResult.error
        });

        if (!serverLogoutResult.success) {
          overallSuccess = false;
          lastError = serverLogoutResult.error;
        }
      }

      // 步骤2: 清理本地会话
      const sessionCleanupResult = await this.cleanupLocalSession(logoutSession);
      steps.push({
        step: 'session_cleanup',
        success: sessionCleanupResult.success,
        timestamp: Date.now(),
        message: sessionCleanupResult.message,
        error: sessionCleanupResult.error
      });

      if (!sessionCleanupResult.success) {
        overallSuccess = false;
        lastError = sessionCleanupResult.error;
      }

      // 步骤3: 清理用户数据
      if (this.config.enableDataCleanup) {
        const dataCleanupResult = await this.cleanupUserData(logoutSession);
        steps.push({
          step: 'data_cleanup',
          success: dataCleanupResult.success,
          timestamp: Date.now(),
          message: dataCleanupResult.message,
          error: dataCleanupResult.error
        });

        if (!dataCleanupResult.success) {
          // 数据清理失败不影响整体退出
          console.warn('[SecureLogout] 数据清理失败，但继续退出流程');
        }
      }

      // 步骤4: 清理安全数据
      const securityCleanupResult = await this.cleanupSecurityData(logoutSession);
      steps.push({
        step: 'security_cleanup',
        success: securityCleanupResult.success,
        timestamp: Date.now(),
        message: securityCleanupResult.message,
        error: securityCleanupResult.error
      });

      // 步骤5: 重置应用状态
      const appResetResult = await this.resetApplicationState(logoutSession);
      steps.push({
        step: 'app_reset',
        success: appResetResult.success,
        timestamp: Date.now(),
        message: appResetResult.message,
        error: appResetResult.error
      });

      return {
        success: overallSuccess,
        steps,
        message: overallSuccess ? '安全退出成功' : '退出过程中遇到问题',
        error: lastError,
        completedAt: Date.now()
      };

    } catch (error) {
      console.error('[SecureLogout] 执行退出步骤失败:', error);
      
      steps.push({
        step: 'execution_error',
        success: false,
        timestamp: Date.now(),
        error: error.message
      });

      return {
        success: false,
        steps,
        message: '退出执行失败',
        error: error.message,
        completedAt: Date.now()
      };
    }
  }

  /**
   * 执行服务器退出
   * @param {Object} logoutSession - 退出会话
   * @returns {Promise<Object>} 服务器退出结果
   */
  async performServerLogout(logoutSession) {
    try {
      console.log('[SecureLogout] 执行服务器退出');

      const { apiClient } = require('./api.js');
      const token = await authManager.getToken();

      if (!token) {
        return {
          success: true,
          message: '没有有效token，跳过服务器退出'
        };
      }

      const response = await apiClient.request({
        url: '/auth/logout',
        method: 'POST',
        data: {
          sessionId: logoutSession.sessionId,
          logoutAllDevices: logoutSession.options.logoutAllDevices || false,
          reason: logoutSession.reason
        },
        timeout: this.config.cleanupTimeout
      });

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return {
          success: true,
          message: '服务器退出成功',
          data: response.data
        };
      } else {
        throw new Error(`HTTP ${response.statusCode}: ${response.data?.message || '服务器退出失败'}`);
      }

    } catch (error) {
      console.error('[SecureLogout] 服务器退出失败:', error);
      
      // 网络错误不应阻止本地退出
      if (error.message.includes('网络') || error.message.includes('timeout')) {
        return {
          success: true,
          message: '网络错误，但继续本地退出',
          warning: error.message
        };
      }

      return {
        success: false,
        message: '服务器退出失败',
        error: error.message
      };
    }
  }

  /**
   * 清理本地会话
   * @param {Object} logoutSession - 退出会话
   * @returns {Promise<Object>} 清理结果
   */
  async cleanupLocalSession(logoutSession) {
    try {
      console.log('[SecureLogout] 清理本地会话');

      // 清理认证管理器
      await authManager.clearUserSession();

      // 清理会话管理器
      await sessionManager.clearSession();

      return {
        success: true,
        message: '本地会话清理成功'
      };

    } catch (error) {
      console.error('[SecureLogout] 本地会话清理失败:', error);
      return {
        success: false,
        message: '本地会话清理失败',
        error: error.message
      };
    }
  }

  /**
   * 清理用户数据
   * @param {Object} logoutSession - 退出会话
   * @returns {Promise<Object>} 清理结果
   */
  async cleanupUserData(logoutSession) {
    try {
      console.log('[SecureLogout] 清理用户数据');

      const cleanupLevel = logoutSession.options.cleanupLevel || 'standard';
      const dataKeys = [];

      // 根据清理级别确定要清理的数据
      switch (cleanupLevel) {
        case 'minimal':
          dataKeys.push('userToken', 'userInfo', 'currentRole');
          break;
        
        case 'standard':
          dataKeys.push(
            'userToken', 'userInfo', 'currentRole',
            'userPreferences', 'recentSearches', 'cachedData'
          );
          break;
        
        case 'complete':
          // 清理所有用户相关数据
          const allKeys = await this.getAllStorageKeys();
          dataKeys.push(...allKeys.filter(key => 
            key.includes('user') || 
            key.includes('cache') || 
            key.includes('temp')
          ));
          break;
      }

      // 执行数据清理
      const cleanupPromises = dataKeys.map(key => storage.remove(key));
      await Promise.allSettled(cleanupPromises);

      return {
        success: true,
        message: `用户数据清理成功 (级别: ${cleanupLevel})`,
        cleanedKeys: dataKeys.length
      };

    } catch (error) {
      console.error('[SecureLogout] 用户数据清理失败:', error);
      return {
        success: false,
        message: '用户数据清理失败',
        error: error.message
      };
    }
  }

  /**
   * 清理安全数据
   * @param {Object} logoutSession - 退出会话
   * @returns {Promise<Object>} 清理结果
   */
  async cleanupSecurityData(logoutSession) {
    try {
      console.log('[SecureLogout] 清理安全数据');

      // 清理账号绑定数据（可选）
      if (logoutSession.options.clearBindingData) {
        await accountBindingManager.clearBindingData();
      }

      // 清理登录检测历史（保留部分用于安全分析）
      const securityEvents = await abnormalLoginDetector.getSecurityEvents();
      if (securityEvents.length > 10) {
        // 只保留最近10个安全事件
        const recentEvents = securityEvents.slice(-10);
        await storage.set('security_events', recentEvents);
      }

      // 清理临时安全令牌
      await storage.remove('temp_security_token');
      await storage.remove('verification_codes');

      return {
        success: true,
        message: '安全数据清理成功'
      };

    } catch (error) {
      console.error('[SecureLogout] 安全数据清理失败:', error);
      return {
        success: false,
        message: '安全数据清理失败',
        error: error.message
      };
    }
  }

  /**
   * 重置应用状态
   * @param {Object} logoutSession - 退出会话
   * @returns {Promise<Object>} 重置结果
   */
  async resetApplicationState(logoutSession) {
    try {
      console.log('[SecureLogout] 重置应用状态');

      // 重置全局状态
      if (typeof getApp === 'function') {
        const app = getApp();
        if (app.globalData) {
          app.globalData.userInfo = null;
          app.globalData.isLoggedIn = false;
          app.globalData.currentRole = null;
        }
      }

      // 清理页面栈中的敏感数据
      const pages = getCurrentPages();
      pages.forEach(page => {
        if (page.data && typeof page.setData === 'function') {
          page.setData({
            userInfo: null,
            isLoggedIn: false
          });
        }
      });

      return {
        success: true,
        message: '应用状态重置成功'
      };

    } catch (error) {
      console.error('[SecureLogout] 应用状态重置失败:', error);
      return {
        success: false,
        message: '应用状态重置失败',
        error: error.message
      };
    }
  }

  /**
   * 完成退出会话
   * @param {Object} logoutSession - 退出会话
   * @param {Object} logoutResult - 退出结果
   */
  async completeLogoutSession(logoutSession, logoutResult) {
    try {
      logoutSession.status = logoutResult.success ? 'completed' : 'failed';
      logoutSession.endTime = Date.now();
      logoutSession.duration = logoutSession.endTime - logoutSession.startTime;
      logoutSession.result = logoutResult;

      // 记录退出历史
      await this.recordLogoutHistory(logoutSession);

      // 清理临时数据
      await storage.remove(this.tempDataKey);

      // 显示退出结果
      this.showLogoutResult(logoutResult);

      // 跳转到登录页
      if (logoutResult.success) {
        setTimeout(() => {
          wx.reLaunch({
            url: '/pages/login/index'
          });
        }, 1000);
      }

    } catch (error) {
      console.error('[SecureLogout] 完成退出会话失败:', error);
    }
  }

  /**
   * 显示退出结果
   * @param {Object} logoutResult - 退出结果
   */
  showLogoutResult(logoutResult) {
    if (logoutResult.success) {
      wx.showToast({
        title: '退出成功',
        icon: 'success',
        duration: 2000
      });
    } else {
      wx.showModal({
        title: '退出异常',
        content: logoutResult.message || '退出过程中遇到问题，但本地登录状态已清除',
        showCancel: false,
        confirmText: '知道了'
      });
    }
  }

  /**
   * 记录退出历史
   * @param {Object} logoutSession - 退出会话
   */
  async recordLogoutHistory(logoutSession) {
    try {
      const history = await storage.get(this.logoutHistoryKey) || [];

      const record = {
        id: logoutSession.id,
        sessionId: logoutSession.sessionId,
        userId: logoutSession.userId,
        method: logoutSession.method,
        reason: logoutSession.reason,
        timestamp: logoutSession.startTime,
        duration: logoutSession.duration,
        success: logoutSession.status === 'completed',
        deviceInfo: logoutSession.deviceInfo,
        stepsCompleted: logoutSession.result.steps.filter(step => step.success).length,
        totalSteps: logoutSession.result.steps.length
      };

      history.push(record);

      // 只保留最近30条退出记录
      if (history.length > 30) {
        history.splice(0, history.length - 30);
      }

      await storage.set(this.logoutHistoryKey, history);

    } catch (error) {
      console.error('[SecureLogout] 记录退出历史失败:', error);
    }
  }

  /**
   * 强制退出（用于安全场景）
   * @param {string} reason - 强制退出原因
   * @returns {Promise<Object>} 退出结果
   */
  async forceLogout(reason = 'security_violation') {
    console.log(`[SecureLogout] 执行强制退出: ${reason}`);

    return await this.performSecureLogout({
      method: 'forced',
      reason,
      skipConfirmation: true,
      cleanupLevel: 'complete',
      logoutAllDevices: true
    });
  }

  /**
   * 获取所有存储键
   * @returns {Promise<Array>} 存储键数组
   */
  async getAllStorageKeys() {
    try {
      return new Promise((resolve) => {
        wx.getStorageInfo({
          success: (res) => {
            resolve(res.keys || []);
          },
          fail: () => {
            resolve([]);
          }
        });
      });
    } catch (error) {
      console.error('[SecureLogout] 获取存储键失败:', error);
      return [];
    }
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
        platform: systemInfo.platform
      };
    } catch (error) {
      console.error('[SecureLogout] 获取设备信息失败:', error);
      return {};
    }
  }

  /**
   * 获取退出历史
   * @returns {Promise<Array>} 退出历史
   */
  async getLogoutHistory() {
    try {
      return await storage.get(this.logoutHistoryKey) || [];
    } catch (error) {
      console.error('[SecureLogout] 获取退出历史失败:', error);
      return [];
    }
  }

  /**
   * 清理退出历史
   */
  async clearLogoutHistory() {
    try {
      await storage.remove(this.logoutHistoryKey);
      console.log('[SecureLogout] 退出历史已清理');
    } catch (error) {
      console.error('[SecureLogout] 清理退出历史失败:', error);
    }
  }

  /**
   * 检查是否有未完成的退出会话
   * @returns {Promise<Object|null>} 未完成的退出会话
   */
  async getIncompleteLogoutSession() {
    try {
      return await storage.get(this.tempDataKey);
    } catch (error) {
      console.error('[SecureLogout] 检查未完成退出会话失败:', error);
      return null;
    }
  }

  /**
   * 恢复中断的退出流程
   */
  async recoverInterruptedLogout() {
    try {
      const incompleteSession = await this.getIncompleteLogoutSession();
      
      if (incompleteSession) {
        console.log('[SecureLogout] 发现中断的退出流程，尝试恢复');
        
        // 继续执行退出流程
        const logoutResult = await this.executeLogoutSteps(incompleteSession);
        await this.completeLogoutSession(incompleteSession, logoutResult);
      }

    } catch (error) {
      console.error('[SecureLogout] 恢复中断退出失败:', error);
      // 清理临时数据
      await storage.remove(this.tempDataKey);
    }
  }
}

// 创建单例实例
const secureLogoutManager = new SecureLogoutManager();

module.exports = {
  secureLogoutManager,
  SecureLogoutManager
};