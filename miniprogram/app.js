// app.js - 五好伴学小程序应用入口文件

App({
  globalData: {
    userInfo: undefined,
    token: undefined,
    role: undefined,
    systemInfo: undefined,
  },

  onLaunch(options) {
    console.log('五好伴学小程序启动', options);
    this.initApp();
  },

  onShow(options) {
    console.log('小程序显示', options);
  },

  onHide() {
    console.log('小程序隐藏');
  },

  onError(error) {
    console.error('小程序错误:', error);
    // TODO: 错误上报
  },

  /**
   * 初始化应用
   */
  initApp() {
    // 获取系统信息
    wx.getSystemInfo({
      success: (res) => {
        this.globalData.systemInfo = res;
        console.log('系统信息:', res);
      },
      fail: (err) => {
        console.error('获取系统信息失败:', err);
      },
    });

    // 检查更新
    this.checkUpdate();

    // 初始化用户信息
    this.initUserInfo();
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
   * 初始化用户信息
   */
  initUserInfo() {
    // 尝试从本地存储获取用户信息
    try {
      const userInfo = wx.getStorageSync('user_info');
      const token = wx.getStorageSync('auth_token');
      const role = wx.getStorageSync('user_role');

      if (userInfo && token) {
        this.globalData.userInfo = userInfo;
        this.globalData.token = token;
        this.globalData.role = role;
        console.log('从本地恢复用户信息');
      }
    } catch (error) {
      console.error('读取本地用户信息失败:', error);
    }
  },

  /**
   * 设置用户信息
   */
  setUserInfo(userInfo, token) {
    this.globalData.userInfo = userInfo;
    this.globalData.token = token;
    this.globalData.role = userInfo.role;

    // 保存到本地存储
    try {
      wx.setStorageSync('user_info', userInfo);
      wx.setStorageSync('auth_token', token);
      wx.setStorageSync('user_role', userInfo.role);
    } catch (error) {
      console.error('保存用户信息失败:', error);
    }

    // 执行回调
    if (this.userInfoReadyCallback) {
      this.userInfoReadyCallback(userInfo);
    }
  },

  /**
   * 清除用户信息
   */
  clearUserInfo() {
    this.globalData.userInfo = undefined;
    this.globalData.token = undefined;
    this.globalData.role = undefined;

    try {
      wx.removeStorageSync('user_info');
      wx.removeStorageSync('auth_token');
      wx.removeStorageSync('user_role');
    } catch (error) {
      console.error('清除本地用户信息失败:', error);
    }
  },

  /**
   * 获取用户信息
   */
  getUserInfo() {
    return this.globalData.userInfo;
  },

  /**
   * 获取访问令牌
   */
  getToken() {
    return this.globalData.token;
  },

  /**
   * 获取用户角色
   */
  getUserRole() {
    return this.globalData.role;
  },

  /**
   * 检查登录状态
   */
  isLoggedIn() {
    return !!(this.globalData.userInfo && this.globalData.token);
  },
});
