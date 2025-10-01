// app.js - 五好伴学小程序应用入口文件

const { authManager } = require('./utils/auth.js');
const { networkMonitor } = require('./utils/network-monitor.js');
const { tabBarManager } = require('./utils/tabbar-manager.js');

App({
  globalData: {
    userInfo: undefined,
    token: undefined,
    role: undefined,
    systemInfo: undefined,
    isInitialized: false,
    networkStatus: 'unknown'
  },

  onLaunch(options) {
    console.log('五好伴学小程序启动', options);
    this.initApp();
  },

  onShow(options) {
    console.log('小程序显示', options);
    // 如果已初始化，检查登录状态
    if (this.globalData.isInitialized) {
      this.checkUserSession();
    }
  },

  onHide() {
    console.log('小程序隐藏');
  },

  onError(error) {
    console.error('小程序错误:', error);
    // TODO: 错误上报
    this.reportError(error);
  },

  /**
   * 初始化应用
   */
  async initApp() {
    try {
      // 获取系统信息
      await this.getSystemInfo();
      
      // 初始化网络监控
      this.initNetworkMonitor();
      
      // 检查更新
      this.checkUpdate();
      
      // 初始化认证系统
      await this.initAuthSystem();
      
      // 初始化TabBar
      await this.initTabBar();
      
      // 检查用户会话
      await this.checkUserSession();
      
      // 标记初始化完成
      this.globalData.isInitialized = true;
      
      console.log('应用初始化完成');
      
    } catch (error) {
      console.error('应用初始化失败:', error);
      // 初始化失败不应该阻止应用启动
      this.globalData.isInitialized = true;
    }
  },

  /**
   * 获取系统信息
   */
  getSystemInfo() {
    return new Promise((resolve, reject) => {
      wx.getSystemInfo({
        success: (res) => {
          this.globalData.systemInfo = res;
          console.log('系统信息:', res);
          resolve(res);
        },
        fail: (err) => {
          console.error('获取系统信息失败:', err);
          reject(err);
        },
      });
    });
  },

  /**
   * 初始化网络监控
   */
  initNetworkMonitor() {
    try {
      const status = networkMonitor.getCurrentStatus();
      this.globalData.networkStatus = status.isConnected ? 'connected' : 'disconnected';
      
      // 监听网络状态变化
      networkMonitor.addListener((currentStatus, previousStatus) => {
        const newStatus = currentStatus.isConnected ? 'connected' : 'disconnected';
        const oldStatus = this.globalData.networkStatus;
        
        this.globalData.networkStatus = newStatus;
        
        console.log('网络状态变化:', oldStatus, '->', newStatus);
        
        // 触发全局网络状态变化事件
        if (this.onNetworkStatusChange) {
          this.onNetworkStatusChange(currentStatus, previousStatus);
        }
      });
      
      console.log('网络监控初始化完成');
    } catch (error) {
      console.error('网络监控初始化失败:', error);
    }
  },

  /**
   * 初始化TabBar
   */
  async initTabBar() {
    try {
      console.log('初始化TabBar系统');
      
      // 初始化tabBar管理器
      const result = await tabBarManager.initTabBar();
      
      if (result.success) {
        console.log('TabBar初始化成功:', result.role);
      } else {
        console.warn('TabBar初始化失败:', result.error);
      }
      
    } catch (error) {
      console.error('TabBar系统初始化失败:', error);
    }
  },

  /**
   * 初始化认证系统
   */
  async initAuthSystem() {
    try {
      // 认证管理器会自动初始化，这里只需要等待初始化完成
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 监听认证事件
      authManager.on && authManager.on('auth:logout', async () => {
        console.log('用户登出，清理全局状态');
        await this.clearUserInfo();
        
        // 重置TabBar到默认状态
        await tabBarManager.resetTabBar();
      });
      
      console.log('认证系统初始化完成');
    } catch (error) {
      console.error('认证系统初始化失败:', error);
    }
  },

  /**
   * 检查用户会话
   */
  async checkUserSession() {
    try {
      const isLoggedIn = await authManager.isLoggedIn();
      
      if (isLoggedIn) {
        // 获取并更新全局状态
        const [userInfo, token, role] = await Promise.all([
          authManager.getUserInfo(),
          authManager.getToken(),
          authManager.getUserRole()
        ]);
        
        if (userInfo && token) {
          this.globalData.userInfo = userInfo;
          this.globalData.token = token;
          this.globalData.role = role;
          
          console.log('用户会话有效:', { userId: userInfo.id, role });
          
          // 检查Token是否有效
          const isTokenValid = await authManager.isTokenValid();
          if (!isTokenValid) {
            console.log('Token即将过期，尝试刷新');
            try {
              await authManager.refreshToken();
              console.log('Token刷新成功');
            } catch (refreshError) {
              console.error('Token刷新失败:', refreshError);
              await this.handleSessionExpired();
            }
          }
        } else {
          console.log('用户会话数据不完整，清理状态');
          await authManager.clearUserSession();
        }
      } else {
        console.log('用户未登录');
        this.clearUserInfo();
      }
    } catch (error) {
      console.error('检查用户会话失败:', error);
    }
  },

  /**
   * 处理会话过期
   */
  async handleSessionExpired() {
    try {
      await authManager.clearUserSession();
      this.clearUserInfo();
      
      // 如果当前不在登录页，则跳转到登录页
      const pages = getCurrentPages();
      const currentPage = pages[pages.length - 1];
      
      if (currentPage && !currentPage.route.includes('login')) {
        wx.showModal({
          title: '登录过期',
          content: '您的登录已过期，请重新登录',
          showCancel: false,
          success: () => {
            wx.redirectTo({
              url: '/pages/login/index'
            });
          }
        });
      }
    } catch (error) {
      console.error('处理会话过期失败:', error);
    }
  },

  /**
   * 检查小程序更新
   */
  checkUpdate() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager();

      updateManager.onCheckForUpdate((res) => {
        console.log('检查更新结果:', res.hasUpdate);
      });

      updateManager.onUpdateReady(() => {
        wx.showModal({
          title: '更新提示',
          content: '新版本已准备好，是否重启应用？',
          success: (res) => {
            if (res.confirm) {
              updateManager.applyUpdate();
            }
          },
        });
      });

      updateManager.onUpdateFailed(() => {
        console.error('更新失败');
      });
    }
  },

  /**
   * 错误上报
   */
  reportError(error) {
    try {
      // TODO: 实现错误上报逻辑
      console.log('错误上报:', error);
    } catch (e) {
      console.error('错误上报失败:', e);
    }
  },

  /**
   * 设置用户信息
   */
  async setUserInfo(userInfo, token, role) {
    try {
      const oldRole = this.globalData.role;
      
      this.globalData.userInfo = userInfo;
      this.globalData.token = token;
      this.globalData.role = role || userInfo.role;
      
      console.log('全局用户信息已更新');
      
      // 如果角色变化，更新TabBar
      if (oldRole !== this.globalData.role) {
        console.log('用户角色变化，更新TabBar');
        await tabBarManager.onRoleSwitch(this.globalData.role, oldRole);
      }
      
      // 执行回调
      if (this.userInfoReadyCallback) {
        this.userInfoReadyCallback(userInfo);
      }
    } catch (error) {
      console.error('设置用户信息失败:', error);
    }
  },

  /**
   * 清除用户信息
   */
  async clearUserInfo() {
    this.globalData.userInfo = undefined;
    this.globalData.token = undefined;
    this.globalData.role = undefined;
    console.log('全局用户信息已清除');
    
    // 重置TabBar到默认状态
    try {
      await tabBarManager.resetTabBar();
      console.log('TabBar已重置到默认状态');
    } catch (error) {
      console.error('重置TabBar失败:', error);
    }
  },

  /**
   * 获取用户信息
   */
  async getUserInfo() {
    if (this.globalData.userInfo) {
      return this.globalData.userInfo;
    }
    
    // 尝试从认证管理器获取
    try {
      const userInfo = await authManager.getUserInfo();
      if (userInfo) {
        this.globalData.userInfo = userInfo;
      }
      return userInfo;
    } catch (error) {
      console.error('获取用户信息失败:', error);
      return null;
    }
  },

  /**
   * 获取访问令牌
   */
  async getToken() {
    if (this.globalData.token) {
      return this.globalData.token;
    }
    
    // 尝试从认证管理器获取
    try {
      const token = await authManager.getToken();
      if (token) {
        this.globalData.token = token;
      }
      return token;
    } catch (error) {
      console.error('获取访问令牌失败:', error);
      return null;
    }
  },

  /**
   * 获取用户角色
   */
  async getUserRole() {
    if (this.globalData.role) {
      return this.globalData.role;
    }
    
    // 尝试从认证管理器获取
    try {
      const role = await authManager.getUserRole();
      if (role) {
        this.globalData.role = role;
      }
      return role;
    } catch (error) {
      console.error('获取用户角色失败:', error);
      return 'student';
    }
  },

  /**
   * 检查登录状态
   */
  async isLoggedIn() {
    try {
      return await authManager.isLoggedIn();
    } catch (error) {
      console.error('检查登录状态失败:', error);
      return false;
    }
  },

  /**
   * 获取网络状态
   */
  getNetworkStatus() {
    return this.globalData.networkStatus;
  },

  /**
   * 是否已初始化
   */
  isInitialized() {
    return this.globalData.isInitialized;
  }
});
