// app.js - 五好伴学小程序应用入口文件
const { authManager } = require('./utils/auth.js');
const { networkMonitor } = require('./utils/network-monitor.js');
const { tabBarManager } = require('./utils/tabbar-manager.js');
const { errorHandler } = require('./utils/error-handler.js');
const { feedbackManager, offlineManager } = require('./utils/user-experience.js');
const { preloadManager, memoryManager, networkOptimizer } = require('./utils/performance.js');

App({
  globalData: {
    userInfo: undefined,
    token: undefined,
    // role: 'student', // 简化：固定为学生角色
    systemInfo: undefined,
    isInitialized: false,
    networkStatus: 'unknown',
    // 性能监控数据
    performanceData: {
      appLaunchTime: Date.now(),
      pageLoadTimes: {},
      apiResponseTimes: {},
      errorCount: 0,
    },
  },

  onLaunch(options) {
    console.log('五好伴学小程序启动', options);
    // 记录启动时间
    this.globalData.performanceData.appLaunchTime = Date.now();
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
    const errorStr = typeof error === 'string' ? error : JSON.stringify(error);

    // ✅ 过滤stopPropagation相关错误（组件生命周期问题）
    if (
      errorStr.includes('stopPropagation') ||
      errorStr.includes('regeneratorRuntime') ||
      errorStr.includes('MiniProgramError')
    ) {
      console.warn('[已忽略系统错误]', errorStr);
      return;
    }

    // 过滤微信系统的 unbind download 警告
    if (errorStr.includes('6000100') || errorStr.includes('unbind download')) {
      console.warn('[Vant 系统警告] 已忽略字体资源加载警告:', errorStr);
      return;
    }

    // 过滤字体加载错误（不影响功能）
    if (
      errorStr.includes('Failed to load font') ||
      errorStr.includes('webfont') ||
      errorStr.includes('ERR_CACHE_MISS')
    ) {
      console.warn('[Vant 字体警告] 已忽略外部字体加载失败:', errorStr);
      return;
    }

    // 真正的错误才记录
    console.error('小程序错误:', error);
    errorHandler.handleError(error, {
      type: 'app',
      context: 'global',
    });
    this.globalData.performanceData.errorCount++;
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
      errorHandler.handleError(error, { type: 'app', context: 'init' });
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
        success: res => {
          this.globalData.systemInfo = res;
          console.log('系统信息:', res);
          resolve(res);
        },
        fail: err => {
          console.error('获取系统信息失败:', err);
          reject(err);
        },
      });
    });
  },

  /**
   * 初始化性能和用户体验模块
   */
  initPerformanceModules() {
    try {
      // 初始化页面监听器
      this.initPageMonitor();

      // 初始化网络优化器
      this.initNetworkOptimizer();

      console.log('性能和用户体验模块初始化完成');
    } catch (error) {
      console.error('性能模块初始化失败:', error);
    }
  },

  /**
   * 初始化页面监听器
   */
  initPageMonitor() {
    // 监听页面加载时间
    const originalPage = Page;
    const app = this;

    Page = function (options) {
      const originalOnLoad = options.onLoad;
      const originalOnHide = options.onHide;
      const originalOnUnload = options.onUnload;

      // 包装onLoad
      options.onLoad = function (query) {
        const startTime = Date.now();
        const route = this.route || this.__route__;

        // 记录页面进入
        memoryManager.onPageEnter(route, query);

        if (originalOnLoad) {
          const result = originalOnLoad.call(this, query);

          // 记录加载时间
          const loadTime = Date.now() - startTime;
          app.globalData.performanceData.pageLoadTimes[route] = loadTime;
          console.log(`页面加载时间: ${route} - ${loadTime}ms`);

          return result;
        }
      };

      // 包装onHide/onUnload
      const handlePageLeave = function () {
        const route = this.route || this.__route__;
        memoryManager.onPageLeave(route);
      };

      options.onHide = function () {
        handlePageLeave.call(this);
        if (originalOnHide) {
          return originalOnHide.call(this);
        }
      };

      options.onUnload = function () {
        handlePageLeave.call(this);
        if (originalOnUnload) {
          return originalOnUnload.call(this);
        }
      };

      return originalPage(options);
    };
  },

  /**
   * 初始化网络优化器
   */
  initNetworkOptimizer() {
    // 简化版本，只做响应时间监控
    const app = this;
    const originalRequest = wx.request;

    wx.request = function (options) {
      const startTime = Date.now();
      const originalSuccess = options.success;
      const originalFail = options.fail;

      options.success = function (res) {
        const responseTime = Date.now() - startTime;
        app.globalData.performanceData.apiResponseTimes[options.url] = responseTime;
        console.log(`API响应时间: ${options.url} - ${responseTime}ms`);

        if (originalSuccess) {
          originalSuccess(res);
        }
      };

      options.fail = function (err) {
        console.error(`API请求失败: ${options.url}`, err);
        if (originalFail) {
          originalFail(err);
        }
      };

      return originalRequest(options);
    };
  },
  getSystemInfo() {
    return new Promise((resolve, reject) => {
      wx.getSystemInfo({
        success: res => {
          this.globalData.systemInfo = res;
          console.log('系统信息:', res);
          resolve(res);
        },
        fail: err => {
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
      authManager.on &&
        authManager.on('auth:logout', async () => {
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
        // 获取并更新全局状态 - 简化版，不需要角色判断
        const [userInfo, token] = await Promise.all([
          authManager.getUserInfo(),
          authManager.getToken(),
        ]);

        if (userInfo && token) {
          this.globalData.userInfo = userInfo;
          this.globalData.token = token;

          console.log('用户会话有效:', { userId: userInfo.id, role: 'student' });

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
              url: '/pages/login/index',
            });
          },
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

      updateManager.onCheckForUpdate(res => {
        console.log('检查更新结果:', res.hasUpdate);
      });

      updateManager.onUpdateReady(() => {
        wx.showModal({
          title: '更新提示',
          content: '新版本已准备好，是否重启应用？',
          success: res => {
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
   * 设置用户信息 - 简化版
   */
  async setUserInfo(userInfo, token) {
    try {
      this.globalData.userInfo = userInfo;
      this.globalData.token = token;

      console.log('全局用户信息已更新');

      // 登录状态变化，更新TabBar
      console.log('用户登录状态变化，更新TabBar');
      await tabBarManager.onLoginStatusChange(true);

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
    // this.globalData.role = undefined; // 不再需要role字段
    console.log('全局用户信息已清除');

    // 重置TabBar到访客状态
    try {
      await tabBarManager.onLoginStatusChange(false);
      console.log('TabBar已重置到访客状态');
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
   * 获取用户角色 - 简化版，固定返回student
   */
  async getUserRole() {
    return 'student';
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
  },
});
