/**
 * 账号安全管理器
 * 实现账号绑定验证、异常登录检测、会话管理等安全功能
 */

const { authManager } = require('./auth.js');
const storage = require('./storage.js');
const config = require('../config/index.js');

/**
 * 账号绑定验证管理器
 */
class AccountBindingManager {
  constructor() {
    this.bindingStatusKey = 'account_binding_status';
    this.verificationDataKey = 'verification_data';
    this.bindingHistoryKey = 'binding_history';
  }

  /**
   * 检查微信账号绑定状态
   * @returns {Promise<Object>} 绑定状态信息
   */
  async checkWechatBinding() {
    try {
      const userInfo = await authManager.getUserInfo();
      
      if (!userInfo) {
        return {
          isBound: false,
          reason: 'user_not_logged_in',
          message: '用户未登录'
        };
      }

      // 检查是否有OpenID和UnionID
      const hasOpenId = !!(userInfo.wechatOpenId || userInfo.openid);
      const hasUnionId = !!(userInfo.wechatUnionId || userInfo.unionid);

      return {
        isBound: hasOpenId,
        hasOpenId,
        hasUnionId,
        openId: userInfo.wechatOpenId || userInfo.openid,
        unionId: userInfo.wechatUnionId || userInfo.unionid,
        bindTime: userInfo.bindTime,
        lastVerified: userInfo.lastVerified
      };

    } catch (error) {
      console.error('[AccountBinding] 检查微信绑定状态失败:', error);
      return {
        isBound: false,
        reason: 'check_failed',
        message: '检查绑定状态失败',
        error: error.message
      };
    }
  }

  /**
   * 验证微信账号绑定
   * @param {Object} options - 验证选项
   * @returns {Promise<Object>} 验证结果
   */
  async verifyWechatBinding(options = {}) {
    try {
      console.log('[AccountBinding] 开始验证微信账号绑定');

      // 1. 获取当前微信登录信息
      const wechatLoginResult = await this.getWechatLoginInfo();
      if (!wechatLoginResult.success) {
        return {
          success: false,
          reason: 'wechat_login_failed',
          message: '获取微信登录信息失败',
          error: wechatLoginResult.error
        };
      }

      // 2. 获取当前用户绑定状态
      const bindingStatus = await this.checkWechatBinding();
      
      // 3. 如果已绑定，验证一致性
      if (bindingStatus.isBound) {
        const isConsistent = await this.verifyBindingConsistency(
          wechatLoginResult.data,
          bindingStatus
        );

        if (!isConsistent.success) {
          return {
            success: false,
            reason: 'binding_inconsistent',
            message: '账号绑定信息不一致，请重新绑定',
            details: isConsistent.details
          };
        }

        // 更新最后验证时间
        await this.updateLastVerified();

        return {
          success: true,
          reason: 'already_bound',
          message: '账号已正确绑定',
          bindingInfo: bindingStatus
        };
      }

      // 4. 如果未绑定，执行绑定流程
      const bindingResult = await this.performAccountBinding(
        wechatLoginResult.data,
        options
      );

      return bindingResult;

    } catch (error) {
      console.error('[AccountBinding] 微信账号绑定验证失败:', error);
      return {
        success: false,
        reason: 'verification_failed',
        message: '账号绑定验证失败',
        error: error.message
      };
    }
  }

  /**
   * 获取微信登录信息
   * @returns {Promise<Object>} 微信登录信息
   */
  async getWechatLoginInfo() {
    try {
      // 获取微信登录code
      const loginCode = await new Promise((resolve, reject) => {
        wx.login({
          success: (res) => {
            if (res.code) {
              resolve(res.code);
            } else {
              reject(new Error('获取微信登录code失败'));
            }
          },
          fail: (error) => {
            reject(new Error(error.errMsg || '微信登录失败'));
          }
        });
      });

      // 获取用户信息
      const userProfile = await this.getWechatUserProfile();

      return {
        success: true,
        data: {
          code: loginCode,
          userInfo: userProfile.userInfo,
          signature: userProfile.signature,
          encryptedData: userProfile.encryptedData,
          iv: userProfile.iv,
          timestamp: Date.now()
        }
      };

    } catch (error) {
      console.error('[AccountBinding] 获取微信登录信息失败:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 获取微信用户信息
   * @returns {Promise<Object>} 用户信息
   */
  async getWechatUserProfile() {
    return new Promise((resolve, reject) => {
      wx.getUserProfile({
        desc: '用于账号安全验证',
        success: (res) => {
          resolve(res);
        },
        fail: (error) => {
          // 如果用户拒绝授权，尝试使用已有信息
          if (error.errMsg && error.errMsg.includes('cancel')) {
            console.warn('[AccountBinding] 用户取消授权，使用已有信息');
            resolve({
              userInfo: null,
              signature: null,
              encryptedData: null,
              iv: null
            });
          } else {
            reject(new Error(error.errMsg || '获取用户信息失败'));
          }
        }
      });
    });
  }

  /**
   * 验证绑定一致性
   * @param {Object} currentWechatInfo - 当前微信信息
   * @param {Object} storedBinding - 存储的绑定信息
   * @returns {Promise<Object>} 验证结果
   */
  async verifyBindingConsistency(currentWechatInfo, storedBinding) {
    try {
      const inconsistencies = [];

      // 验证OpenID一致性（如果有的话）
      if (currentWechatInfo.userInfo && storedBinding.openId) {
        const currentOpenId = currentWechatInfo.userInfo.openId;
        if (currentOpenId && currentOpenId !== storedBinding.openId) {
          inconsistencies.push({
            field: 'openId',
            stored: storedBinding.openId,
            current: currentOpenId
          });
        }
      }

      // 验证UnionID一致性（如果有的话）
      if (currentWechatInfo.userInfo && storedBinding.unionId) {
        const currentUnionId = currentWechatInfo.userInfo.unionId;
        if (currentUnionId && currentUnionId !== storedBinding.unionId) {
          inconsistencies.push({
            field: 'unionId',
            stored: storedBinding.unionId,
            current: currentUnionId
          });
        }
      }

      if (inconsistencies.length > 0) {
        return {
          success: false,
          details: inconsistencies,
          message: '账号绑定信息不一致'
        };
      }

      return {
        success: true,
        message: '账号绑定信息一致'
      };

    } catch (error) {
      console.error('[AccountBinding] 验证绑定一致性失败:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 执行账号绑定
   * @param {Object} wechatInfo - 微信信息
   * @param {Object} options - 绑定选项
   * @returns {Promise<Object>} 绑定结果
   */
  async performAccountBinding(wechatInfo, options = {}) {
    try {
      console.log('[AccountBinding] 开始执行账号绑定');

      // 调用后端绑定API
      const bindingResult = await this.callBindingAPI(wechatInfo, options);

      if (bindingResult.success) {
        // 保存绑定信息到本地
        await this.saveBindingInfo(bindingResult.data);

        // 记录绑定历史
        await this.recordBindingHistory('bind', bindingResult.data);

        // 更新用户信息
        const userInfo = await authManager.getUserInfo();
        const updatedUserInfo = {
          ...userInfo,
          ...bindingResult.data,
          bindTime: Date.now(),
          lastVerified: Date.now()
        };

        await authManager.updateUserInfo(updatedUserInfo);

        return {
          success: true,
          reason: 'binding_completed',
          message: '账号绑定成功',
          bindingInfo: bindingResult.data
        };
      } else {
        return {
          success: false,
          reason: 'api_binding_failed',
          message: bindingResult.message || '账号绑定失败',
          error: bindingResult.error
        };
      }

    } catch (error) {
      console.error('[AccountBinding] 执行账号绑定失败:', error);
      return {
        success: false,
        reason: 'binding_error',
        message: '账号绑定过程出错',
        error: error.message
      };
    }
  }

  /**
   * 调用后端绑定API
   * @param {Object} wechatInfo - 微信信息
   * @param {Object} options - 选项
   * @returns {Promise<Object>} API响应
   */
  async callBindingAPI(wechatInfo, options) {
    try {
      const { apiClient } = require('./api.js');
      
      const response = await apiClient.request({
        url: '/auth/bind-wechat',
        method: 'POST',
        data: {
          code: wechatInfo.code,
          userInfo: wechatInfo.userInfo,
          signature: wechatInfo.signature,
          encryptedData: wechatInfo.encryptedData,
          iv: wechatInfo.iv,
          ...options
        },
        timeout: config.api.timeout || 10000
      });

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response.data;
      } else {
        throw new Error(`HTTP ${response.statusCode}: ${response.data?.message || '请求失败'}`);
      }

    } catch (error) {
      console.error('[AccountBinding] 调用绑定API失败:', error);
      throw error;
    }
  }

  /**
   * 保存绑定信息
   * @param {Object} bindingData - 绑定数据
   */
  async saveBindingInfo(bindingData) {
    try {
      const bindingInfo = {
        openId: bindingData.wechatOpenId || bindingData.openid,
        unionId: bindingData.wechatUnionId || bindingData.unionid,
        bindTime: Date.now(),
        lastVerified: Date.now(),
        bindingStatus: 'active'
      };

      await storage.set(this.bindingStatusKey, bindingInfo);
      console.log('[AccountBinding] 绑定信息已保存');

    } catch (error) {
      console.error('[AccountBinding] 保存绑定信息失败:', error);
      throw error;
    }
  }

  /**
   * 记录绑定历史
   * @param {string} action - 操作类型
   * @param {Object} data - 相关数据
   */
  async recordBindingHistory(action, data) {
    try {
      const history = await storage.get(this.bindingHistoryKey) || [];
      
      const record = {
        id: Date.now().toString(),
        action,
        timestamp: Date.now(),
        data: {
          openId: data.wechatOpenId || data.openid,
          unionId: data.wechatUnionId || data.unionid
        },
        deviceInfo: await this.getDeviceInfo()
      };

      history.push(record);

      // 只保留最近20条记录
      if (history.length > 20) {
        history.splice(0, history.length - 20);
      }

      await storage.set(this.bindingHistoryKey, history);
      console.log('[AccountBinding] 绑定历史已记录');

    } catch (error) {
      console.error('[AccountBinding] 记录绑定历史失败:', error);
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
        version: systemInfo.version,
        platform: systemInfo.platform,
        wechatVersion: systemInfo.version
      };
    } catch (error) {
      console.warn('[AccountBinding] 获取设备信息失败:', error);
      return {};
    }
  }

  /**
   * 更新最后验证时间
   */
  async updateLastVerified() {
    try {
      const bindingInfo = await storage.get(this.bindingStatusKey);
      if (bindingInfo) {
        bindingInfo.lastVerified = Date.now();
        await storage.set(this.bindingStatusKey, bindingInfo);
      }
    } catch (error) {
      console.error('[AccountBinding] 更新验证时间失败:', error);
    }
  }

  /**
   * 解除账号绑定
   * @param {string} reason - 解绑原因
   * @returns {Promise<Object>} 解绑结果
   */
  async unbindAccount(reason = 'user_request') {
    try {
      console.log('[AccountBinding] 开始解除账号绑定');

      // 调用后端解绑API
      const { apiClient } = require('./api.js');
      
      const response = await apiClient.request({
        url: '/auth/unbind-wechat',
        method: 'POST',
        data: { reason },
        timeout: config.api.timeout || 10000
      });

      if (response.statusCode >= 200 && response.statusCode < 300 && response.data.success) {
        // 清理本地绑定信息
        await storage.remove(this.bindingStatusKey);
        
        // 记录解绑历史
        await this.recordBindingHistory('unbind', { reason });

        // 更新用户信息
        const userInfo = await authManager.getUserInfo();
        if (userInfo) {
          const updatedUserInfo = {
            ...userInfo,
            wechatOpenId: null,
            wechatUnionId: null,
            openid: null,
            unionid: null,
            bindTime: null
          };
          await authManager.updateUserInfo(updatedUserInfo);
        }

        return {
          success: true,
          message: '账号解绑成功'
        };
      } else {
        throw new Error(response.data?.message || '账号解绑失败');
      }

    } catch (error) {
      console.error('[AccountBinding] 解除账号绑定失败:', error);
      return {
        success: false,
        message: '账号解绑失败',
        error: error.message
      };
    }
  }

  /**
   * 获取绑定历史
   * @returns {Promise<Array>} 绑定历史记录
   */
  async getBindingHistory() {
    try {
      return await storage.get(this.bindingHistoryKey) || [];
    } catch (error) {
      console.error('[AccountBinding] 获取绑定历史失败:', error);
      return [];
    }
  }

  /**
   * 清理绑定数据
   */
  async clearBindingData() {
    try {
      await Promise.all([
        storage.remove(this.bindingStatusKey),
        storage.remove(this.verificationDataKey),
        storage.remove(this.bindingHistoryKey)
      ]);
      console.log('[AccountBinding] 绑定数据已清理');
    } catch (error) {
      console.error('[AccountBinding] 清理绑定数据失败:', error);
    }
  }

  /**
   * 检查绑定是否需要重新验证
   * @returns {boolean} 是否需要重新验证
   */
  async needsReVerification() {
    try {
      const bindingInfo = await storage.get(this.bindingStatusKey);
      
      if (!bindingInfo || !bindingInfo.lastVerified) {
        return true;
      }

      // 7天内验证过的不需要重新验证
      const sevenDays = 7 * 24 * 60 * 60 * 1000;
      const timeSinceLastVerification = Date.now() - bindingInfo.lastVerified;

      return timeSinceLastVerification > sevenDays;

    } catch (error) {
      console.error('[AccountBinding] 检查重新验证需求失败:', error);
      return true;
    }
  }
}

// 创建单例实例
const accountBindingManager = new AccountBindingManager();

module.exports = {
  accountBindingManager,
  AccountBindingManager
};