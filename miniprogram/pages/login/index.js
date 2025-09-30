// pages/login/index.js - 五好伴学小程序登录页

Page({
  data: {
    loading: false,
    canIUseGetUserProfile: !!wx.getUserProfile,
  },

  onLoad() {
    console.log('登录页面加载');
  },

  /**
   * 微信登录
   */
  async onWechatLogin() {
    try {
      this.setData({ loading: true });

      // 检查登录状态
      const loginResult = await this.wxLogin();
      console.log('微信登录结果:', loginResult);

      // 获取用户信息
      let userInfo;
      if (this.data.canIUseGetUserProfile) {
        userInfo = await this.getUserProfile();
      } else {
        // 兼容老版本
        userInfo = await this.getUserInfo();
      }

      console.log('用户信息:', userInfo);

      // TODO: 调用后端API进行登录验证
      // const response = await api.login({ code: loginResult.code, userInfo });

      // 模拟登录成功
      const mockUserInfo = {
        id: 'user_123',
        nickName: userInfo.nickName,
        avatarUrl: userInfo.avatarUrl,
        gender: userInfo.gender,
        country: userInfo.country,
        province: userInfo.province,
        city: userInfo.city,
        language: userInfo.language,
        openid: 'mock_openid',
        role: 'student', // 默认学生角色
      };

      const mockToken = 'mock_token_123';

      // 保存用户信息到全局状态
      const app = getApp();
      if (app.setUserInfo) {
        app.setUserInfo(mockUserInfo, mockToken);
      } else {
        // 兼容处理
        app.globalData.userInfo = mockUserInfo;
        app.globalData.token = mockToken;
        app.globalData.role = mockUserInfo.role;
      }

      // 跳转到首页
      wx.switchTab({
        url: '/pages/index/index',
      });

    } catch (error) {
      console.error('登录失败:', error);
      this.showError('登录失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 微信登录获取code
   */
  wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: resolve,
        fail: reject,
      });
    });
  },

  /**
   * 获取用户信息 (新版本)
   */
  getUserProfile() {
    return new Promise((resolve, reject) => {
      wx.getUserProfile({
        desc: '用于完善用户资料',
        success: (res) => resolve(res.userInfo),
        fail: reject,
      });
    });
  },

  /**
   * 获取用户信息 (兼容老版本)
   */
  getUserInfo() {
    return new Promise((resolve, reject) => {
      wx.getUserInfo({
        success: (res) => resolve(res.userInfo),
        fail: reject,
      });
    });
  },

  /**
   * 显示错误信息
   */
  showError(message) {
    wx.showToast({
      title: message,
      icon: 'error',
      duration: 2000,
    });
  },
});
