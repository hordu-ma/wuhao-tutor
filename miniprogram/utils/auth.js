// utils/auth.js
// 用户认证管理工具

const config = require('../config/index.js');
const storage = require('./storage.js');

// 延迟加载 API 客户端以避免循环依赖
let apiClient = null;
function getApiClient() {
  if (!apiClient) {
    const { apiClient: client } = require('./api.js');
    apiClient = client;
  }
  return apiClient;
}

// 延迟加载安全系统以避免循环依赖
let securitySystem = null;
function getSecuritySystem() {
  if (!securitySystem) {
    const { accountSecuritySystem } = require('./account-security-system.js');
    securitySystem = accountSecuritySystem;
  }
  return securitySystem;
}

/**
 * 认证管理类
 */
class AuthManager {
  constructor() {
    this.tokenKey = config.auth.tokenKey;
    this.refreshTokenKey = config.auth.refreshTokenKey || 'refreshToken';
    this.userInfoKey = config.auth.userInfoKey;
    this.roleKey = config.auth.roleKey;
    this.sessionIdKey = config.auth.sessionIdKey || 'sessionId';
    this.checkInterval = config.auth.checkInterval;

    // 当前用户信息缓存
    this.currentUser = null;
    this.currentToken = null;
    this.currentRefreshToken = null;
    this.currentRole = null;
    this.currentSessionId = null;

    // Token检查定时器
    this.checkTimer = null;
    // 自动刷新状态
    this.isRefreshing = false;
    this.refreshPromise = null;

    // 初始化
    this.init();
  }

  /**
   * 初始化认证管理器
   */
  async init() {
    try {
      // 从本地存储恢复用户信息
      await this.restoreUserSession();

      // 启动Token检查定时器
      this.startTokenCheck();

      console.log('认证管理器初始化成功');
    } catch (error) {
      console.error('认证管理器初始化失败', error);
    }
  }

  /**
   * 从本地存储恢复用户会话
   */
  async restoreUserSession() {
    try {
      const token = await storage.get(this.tokenKey);
      const refreshToken = await storage.get(this.refreshTokenKey);
      const userInfo = await storage.get(this.userInfoKey);
      const role = await storage.get(this.roleKey);
      const sessionId = await storage.get(this.sessionIdKey);

      if (token && userInfo) {
        this.currentToken = token;
        this.currentRefreshToken = refreshToken;
        this.currentUser = userInfo;
        this.currentRole = role || 'student';
        this.currentSessionId = sessionId;

        console.log('用户会话恢复成功', {
          userId: userInfo.id,
          role: this.currentRole,
          hasRefreshToken: !!refreshToken,
        });

        // 检查Token是否需要刷新
        const isValid = await this.isTokenValid();
        if (!isValid && refreshToken) {
          console.log('Access token过期，尝试自动刷新');
          try {
            await this.refreshToken();
          } catch (error) {
            console.warn('自动刷新Token失败，需要重新登录', error);
          }
        }

        return true;
      }

      return false;
    } catch (error) {
      console.error('恢复用户会话失败', error);
      return false;
    }
  }

  /**
   * 微信登录（带用户信息）
   * @param {Object} userProfile - 已获取的用户信息
   */
  async wechatLoginWithProfile(userProfile) {
    try {
      // 1. 获取微信登录code
      const loginResult = await this.getWechatLoginCode();

      // 2. 准备登录数据
      const loginData = {
        code: loginResult.code,
        userInfo: userProfile.userInfo,
        signature: userProfile.signature,
        encryptedData: userProfile.encryptedData,
        iv: userProfile.iv,
        deviceInfo: await this.getDeviceInfo(),
        loginMethod: 'wechat',
        timestamp: Date.now(),
      };

      // 3. 调用后端登录接口
      const response = await this.callLoginAPI(loginData);

      if (response.success) {
        const { access_token, refresh_token, user, session_id } = response.data;
        const userInfo = user;
        const role = user.role || 'student';

        // 4. 执行安全登录流程
        const securitySystem = getSecuritySystem();
        const secureLoginResult = await securitySystem.performSecureLogin({
          token: access_token,
          userInfo,
          role,
          refreshToken: refresh_token,
          sessionId: session_id,
          deviceInfo: loginData.deviceInfo,
          loginMethod: 'wechat',
        });

        if (!secureLoginResult.success) {
          throw new Error(secureLoginResult.message || '安全验证失败');
        }

        // 5. 保存登录信息
        await this.saveUserSession(access_token, refresh_token, userInfo, role, session_id);

        console.log('微信登录成功', { userId: userInfo.id, role });

        return {
          success: true,
          data: {
            access_token,
            refresh_token,
            user: userInfo,
            role,
            session_id,
          },
          securityInfo: secureLoginResult.securityInfo,
        };
      } else {
        throw new Error(response.error?.message || '登录失败');
      }
    } catch (error) {
      console.error('微信登录失败', error);

      return {
        success: false,
        error: {
          code: error.code || 'LOGIN_FAILED',
          message: error.message || '登录失败，请重试',
        },
      };
    }
  }

  /**
   * 微信登录（旧方法，保留以兼容）
   * @deprecated 请使用 wechatLoginWithProfile 方法
   */
  async wechatLogin() {
    try {
      // 1. 获取微信登录code
      const loginResult = await this.getWechatLoginCode();

      // 2. 获取用户信息授权
      const userProfile = await this.getUserProfile();

      // 3. 准备登录数据
      const loginData = {
        code: loginResult.code,
        userInfo: userProfile.userInfo,
        signature: userProfile.signature,
        encryptedData: userProfile.encryptedData,
        iv: userProfile.iv,
        deviceInfo: await this.getDeviceInfo(),
        loginMethod: 'wechat',
        timestamp: Date.now(),
      };

      // 4. 调用后端登录接口
      const response = await this.callLoginAPI(loginData);

      if (response.success) {
        const { access_token, refresh_token, user, session_id } = response.data;
        const userInfo = user;
        const role = user.role || 'student';

        // 5. 执行安全登录流程
        const securitySystem = getSecuritySystem();
        const secureLoginResult = await securitySystem.performSecureLogin({
          token: access_token,
          userInfo,
          role,
          refreshToken: refresh_token,
          sessionId: session_id,
          deviceInfo: loginData.deviceInfo,
          loginMethod: 'wechat',
        });

        if (!secureLoginResult.success) {
          throw new Error(secureLoginResult.message || '安全验证失败');
        }

        // 6. 保存登录信息
        await this.saveUserSession(access_token, refresh_token, userInfo, role, session_id);

        console.log('微信登录成功', { userId: userInfo.id, role });

        return {
          success: true,
          data: {
            access_token,
            refresh_token,
            user: userInfo,
            role,
            session_id,
          },
          securityInfo: secureLoginResult.securityInfo,
        };
      } else {
        throw new Error(response.error?.message || '登录失败');
      }
    } catch (error) {
      console.error('微信登录失败', error);

      return {
        success: false,
        error: {
          code: error.code || 'LOGIN_FAILED',
          message: error.message || '登录失败，请重试',
        },
      };
    }
  }

  /**
   * 获取微信登录code
   */
  getWechatLoginCode() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: res => {
          if (res.code) {
            resolve(res);
          } else {
            reject(new Error('获取登录code失败'));
          }
        },
        fail: error => {
          reject(new Error(error.errMsg || '微信登录失败'));
        },
      });
    });
  }

  /**
   * 获取用户信息授权
   */
  getUserProfile() {
    return new Promise((resolve, reject) => {
      wx.getUserProfile({
        desc: '用于完善用户资料',
        success: res => {
          resolve(res);
        },
        fail: error => {
          // 用户拒绝授权的情况
          if (error.errMsg && error.errMsg.includes('cancel')) {
            reject(new Error('用户取消授权'));
          } else {
            reject(new Error(error.errMsg || '获取用户信息失败'));
          }
        },
      });
    });
  }

  /**
   * 调用后端登录API
   */
  async callLoginAPI(loginData) {
    try {
      const response = await getApiClient().request({
        url: '/api/v1/auth/wechat-login',
        method: 'POST',
        data: loginData,
        skipAuth: true, // 登录请求不需要认证头
        timeout: config.api.timeout || 10000,
      });

      return response;
    } catch (error) {
      console.error('调用登录API失败:', error);
      throw new Error('调用登录API失败: ' + error.message);
    }
  }

  /**
   * 保存用户会话信息
   */
  async saveUserSession(accessToken, refreshToken, userInfo, role = 'student', sessionId) {
    try {
      console.log('开始保存用户会话', {
        userId: userInfo?.id,
        role,
        hasToken: !!accessToken,
        hasRefreshToken: !!refreshToken,
      });

      // 保存到内存
      this.currentToken = accessToken;
      this.currentRefreshToken = refreshToken;
      this.currentUser = userInfo;
      this.currentRole = role;
      this.currentSessionId = sessionId;

      // 保存到本地存储
      const savePromises = [
        storage.set(this.tokenKey, accessToken),
        storage.set(this.userInfoKey, userInfo),
        storage.set(this.roleKey, role),
      ];

      if (refreshToken) {
        savePromises.push(storage.set(this.refreshTokenKey, refreshToken));
      }

      if (sessionId) {
        savePromises.push(storage.set(this.sessionIdKey, sessionId));
      }

      await Promise.all(savePromises);

      console.log('✅ 用户会话保存成功', {
        userId: userInfo?.id,
        role,
        keys: [this.tokenKey, this.userInfoKey, this.roleKey],
      });
    } catch (error) {
      console.error('❌ 保存用户会话失败', error);
      throw error;
    }
  }

  /**
   * 获取当前Token
   */
  async getToken() {
    if (this.currentToken) {
      console.log('从内存获取Token');
      return this.currentToken;
    }

    try {
      const token = await storage.get(this.tokenKey);
      console.log('从存储获取Token', { hasToken: !!token, key: this.tokenKey });
      this.currentToken = token;
      return token;
    } catch (error) {
      console.error('❌ 获取Token失败', error);
      return null;
    }
  }

  /**
   * 获得刷新Token
   */
  async getRefreshToken() {
    if (this.currentRefreshToken) {
      return this.currentRefreshToken;
    }

    try {
      const refreshToken = await storage.get(this.refreshTokenKey);
      this.currentRefreshToken = refreshToken;
      return refreshToken;
    } catch (error) {
      console.error('获取刷新Token失败', error);
      return null;
    }
  }

  /**
   * 获得会话ID
   */
  async getSessionId() {
    if (this.currentSessionId) {
      return this.currentSessionId;
    }

    try {
      const sessionId = await storage.get(this.sessionIdKey);
      this.currentSessionId = sessionId;
      return sessionId;
    } catch (error) {
      console.error('获取会话ID失败', error);
      return null;
    }
  }

  /**
   * 获取当前用户信息
   */
  async getUserInfo() {
    if (this.currentUser) {
      console.log('从内存获取用户信息', { userId: this.currentUser?.id });
      return this.currentUser;
    }

    try {
      const userInfo = await storage.get(this.userInfoKey);
      console.log('从存储获取用户信息', {
        hasUserInfo: !!userInfo,
        userId: userInfo?.id,
        key: this.userInfoKey,
      });
      this.currentUser = userInfo;
      return userInfo;
    } catch (error) {
      console.error('❌ 获取用户信息失败', error);
      return null;
    }
  }

  /**
   * 获取当前用户角色 - 简化版，固定返回student
   */
  async getUserRole() {
    // 简化逻辑：所有用户都是学生角色
    return 'student';
  }

  /**
   * 更新用户信息
   */
  async updateUserInfo(newUserInfo) {
    try {
      // 合并新的用户信息
      const updatedUserInfo = {
        ...this.currentUser,
        ...newUserInfo,
      };

      // 更新内存和本地存储
      this.currentUser = updatedUserInfo;
      await storage.set(this.userInfoKey, updatedUserInfo);

      console.log('用户信息更新成功');
      return updatedUserInfo;
    } catch (error) {
      console.error('更新用户信息失败', error);
      throw error;
    }
  }

  /**
   * 检查是否需要角色选择
   */
  async needsRoleSelection() {
    try {
      const isLoggedIn = await this.isLoggedIn();
      if (!isLoggedIn) {
        return false;
      }

      const role = await this.getUserRole();
      // 如果没有角色或角色为未定义，则需要角色选择
      return !role || role === 'undefined' || role === '';
    } catch (error) {
      console.error('检查角色选择状态失败', error);
      return false;
    }
  }

  /**
   * 切换用户角色
   */
  async switchRole(newRole) {
    try {
      if (!['student', 'parent', 'teacher'].includes(newRole)) {
        throw new Error('不支持的用户角色');
      }

      this.currentRole = newRole;
      await storage.set(this.roleKey, newRole);

      console.log('用户角色切换成功', newRole);
      return newRole;
    } catch (error) {
      console.error('切换用户角色失败', error);
      throw error;
    }
  }

  /**
   * 检查登录状态
   */
  async isLoggedIn() {
    try {
      const token = await this.getToken();
      const userInfo = await this.getUserInfo();

      const isLoggedIn = !!(token && userInfo);
      console.log('检查登录状态', {
        isLoggedIn,
        hasToken: !!token,
        hasUserInfo: !!userInfo,
        userId: userInfo?.id,
      });

      return isLoggedIn;
    } catch (error) {
      console.error('❌ 检查登录状态失败', error);
      return false;
    }
  }

  /**
   * 检查Token是否有效
   */
  async isTokenValid() {
    try {
      const token = await this.getToken();

      if (!token) {
        return false;
      }

      // 解析Token payload（简单的JWT解析）
      const payload = this.parseJWT(token);

      if (!payload || !payload.exp) {
        return false;
      }

      // 检查是否过期（提前5分钟判断为过期）
      const now = Math.floor(Date.now() / 1000);
      const bufferTime = 5 * 60; // 5分钟缓冲

      return payload.exp > now + bufferTime;
    } catch (error) {
      console.error('检查Token有效性失败', error);
      return false;
    }
  }

  /**
   * 简单的JWT解析
   */
  parseJWT(token) {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return null;
      }

      let payload = parts[1];

      // JWT使用base64url编码，需要处理padding
      // base64url转base64: 替换 - 为 +, _ 为 /，并添加必要的padding
      payload = payload.replace(/-/g, '+').replace(/_/g, '/');

      // 添加padding使长度为4的倍数
      while (payload.length % 4) {
        payload += '=';
      }

      // 在小程序环境中直接使用base64解码
      const decoded = wx.base64ToArrayBuffer(payload);
      const uint8Array = new Uint8Array(decoded);

      // 将ArrayBuffer转为字符串
      let jsonStr = '';
      for (let i = 0; i < uint8Array.length; i++) {
        jsonStr += String.fromCharCode(uint8Array[i]);
      }

      return JSON.parse(jsonStr);
    } catch (error) {
      console.error('JWT解析失败', error);
      return null;
    }
  }

  /**
   * 刷新Token
   */
  async refreshToken() {
    // 防止并发刷新
    if (this.isRefreshing) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this._performRefreshToken();

    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * 执行刷新Token操作
   */
  async _performRefreshToken() {
    try {
      const currentRefreshToken = await this.getRefreshToken();

      if (!currentRefreshToken) {
        throw new Error('没有有效的刷新Token');
      }

      const response = await getApiClient().request({
        url: '/api/v1/auth/refresh-token',
        method: 'POST',
        data: {
          refresh_token: currentRefreshToken,
        },
        skipAuth: true, // 刷新请求不需要access token
        timeout: config.api.timeout || 10000,
      });

      if (response.success) {
        const { access_token, refresh_token, user, session_id } = response.data;

        // 更新Token和用户信息
        await this.saveUserSession(access_token, refresh_token, user, user.role, session_id);

        console.log('Token刷新成功');
        return {
          access_token,
          refresh_token,
          user,
          session_id,
        };
      } else {
        throw new Error(response.error?.message || 'Token刷新失败');
      }
    } catch (error) {
      console.error('刷新Token失败', error);
      throw error;
    }
  }

  /**
   * 登出
   */
  async logout() {
    try {
      // 使用安全退出系统
      const securitySystem = getSecuritySystem();
      const logoutResult = await securitySystem.performSecureLogout({
        method: 'normal',
        reason: 'user_initiated',
        cleanupLevel: 'standard',
      });

      if (logoutResult.success) {
        console.log('用户登出成功');
      } else {
        console.warn('安全退出过程中遇到问题，但本地状态已清理');
      }

      return logoutResult;
    } catch (error) {
      console.error('登出失败', error);

      // 如果安全退出失败，执行基础清理
      await this.clearUserSession();

      throw error;
    }
  }

  /**
   * 清理用户会话
   */
  async clearUserSession() {
    try {
      // 清理内存
      this.currentToken = null;
      this.currentRefreshToken = null;
      this.currentUser = null;
      this.currentRole = null;
      this.currentSessionId = null;

      // 清理本地存储
      const removePromises = [
        storage.remove(this.tokenKey),
        storage.remove(this.userInfoKey),
        storage.remove(this.roleKey),
      ];

      // 清理可选的存储项
      try {
        await storage.remove(this.refreshTokenKey);
        await storage.remove(this.sessionIdKey);
      } catch (error) {
        // 忽略清理可选项的错误
      }

      await Promise.all(removePromises);

      // 停止Token检查
      this.stopTokenCheck();

      console.log('用户会话清理成功');
    } catch (error) {
      console.error('清理用户会话失败', error);
      throw error;
    }
  }

  /**
   * 启动Token检查定时器
   */
  startTokenCheck() {
    if (this.checkTimer) {
      return;
    }

    this.checkTimer = setInterval(async () => {
      try {
        const isValid = await this.isTokenValid();

        if (!isValid) {
          console.log('Token已过期，尝试刷新');

          try {
            await this.refreshToken();
          } catch (error) {
            console.error('Token刷新失败，用户需要重新登录', error);

            // 清理会话并跳转登录
            await this.clearUserSession();

            wx.showModal({
              title: '登录过期',
              content: '您的登录已过期，请重新登录',
              showCancel: false,
              success: () => {
                wx.redirectTo({
                  url: '/pages/login/index',
                });
              },
            });
          }
        }
      } catch (error) {
        console.error('Token检查失败', error);
      }
    }, this.checkInterval);

    console.log('Token检查定时器启动');
  }

  /**
   * 停止Token检查定时器
   */
  stopTokenCheck() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
      console.log('Token检查定时器停止');
    }
  }

  /**
   * 检查权限
   */
  async checkPermission(requiredRole) {
    try {
      const isLoggedIn = await this.isLoggedIn();

      if (!isLoggedIn) {
        return false;
      }

      const currentRole = await this.getUserRole();

      // 定义角色权限级别
      const roleLevel = {
        student: 1,
        parent: 2,
        teacher: 3,
        admin: 4,
      };

      const currentLevel = roleLevel[currentRole] || 0;
      const requiredLevel = roleLevel[requiredRole] || 0;

      return currentLevel >= requiredLevel;
    } catch (error) {
      console.error('检查权限失败', error);
      return false;
    }
  }

  /**
   * 获取用户头像URL
   */
  async getAvatarUrl() {
    try {
      const userInfo = await this.getUserInfo();
      return userInfo?.avatarUrl || '/assets/images/default-avatar.png';
    } catch (error) {
      console.error('获取头像URL失败', error);
      return '/assets/images/default-avatar.png';
    }
  }

  /**
   * 获取用户显示名称
   */
  async getDisplayName() {
    try {
      const userInfo = await this.getUserInfo();
      return userInfo?.nickName || userInfo?.name || '用户';
    } catch (error) {
      console.error('获取显示名称失败', error);
      return '用户';
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
        screenWidth: systemInfo.screenWidth,
        screenHeight: systemInfo.screenHeight,
        language: systemInfo.language,
        wechatVersion: systemInfo.version,
      };
    } catch (error) {
      console.error('获取设备信息失败', error);
      return {};
    }
  }

  /**
   * 获取用户信息缓存时间
   */
  getUserInfoCacheTime() {
    try {
      const userInfo = wx.getStorageSync('userInfo');
      return userInfo?.lastUpdated || 0;
    } catch (error) {
      console.error('获取缓存时间失败', error);
      return 0;
    }
  }

  /**
   * 检查用户信息是否需要刷新（超过1小时）
   */
  needsUserInfoRefresh() {
    const cacheTime = this.getUserInfoCacheTime();
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;

    return now - cacheTime > oneHour;
  }
}

// 创建单例实例
const authManager = new AuthManager();

// 导出常用方法
module.exports = {
  // 认证管理器实例
  authManager,

  // 常用方法快捷访问
  wechatLogin: () => authManager.wechatLogin(),
  logout: () => authManager.logout(),
  getToken: () => authManager.getToken(),
  getUserInfo: () => authManager.getUserInfo(),
  getUserRole: () => authManager.getUserRole(),
  updateUserInfo: userInfo => authManager.updateUserInfo(userInfo),
  switchRole: role => authManager.switchRole(role),
  needsRoleSelection: () => authManager.needsRoleSelection(),
  isLoggedIn: () => authManager.isLoggedIn(),
  isTokenValid: () => authManager.isTokenValid(),
  refreshToken: () => authManager.refreshToken(),
  checkPermission: role => authManager.checkPermission(role),
  getAvatarUrl: () => authManager.getAvatarUrl(),
  getDisplayName: () => authManager.getDisplayName(),

  // 用于页面路由守卫
  async requireLogin() {
    const isLoggedIn = await authManager.isLoggedIn();
    if (!isLoggedIn) {
      wx.redirectTo({
        url: '/pages/login/index',
      });
      return false;
    }
    return true;
  },

  // 用于权限检查的装饰器
  requireRole(requiredRole) {
    return async function (target, propertyKey, descriptor) {
      const originalMethod = descriptor.value;

      descriptor.value = async function (...args) {
        const hasPermission = await authManager.checkPermission(requiredRole);

        if (!hasPermission) {
          wx.showToast({
            title: '权限不足',
            icon: 'error',
          });
          return;
        }

        return originalMethod.apply(this, args);
      };

      return descriptor;
    };
  },
};
