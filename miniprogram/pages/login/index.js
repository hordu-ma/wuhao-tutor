// pages/login/index.js - 五好伴学小程序登录页

const { authManager } = require('../../utils/auth.js');
const { networkMonitor } = require('../../utils/network-monitor.js');
const { errorToast } = require('../../utils/error-toast.js');

Page({
  data: {
    loading: false,
    canIUseGetUserProfile: !!wx.getUserProfile,
    networkStatus: 'unknown',
    loginError: null,
  },

  onLoad() {
    console.log('登录页面加载');
    this.checkNetworkStatus();
    this.checkAutoLogin();
  },

  onShow() {
    // 清除错误状态
    this.setData({ loginError: null });
  },

  /**
   * 检查网络状态
   */
  checkNetworkStatus() {
    const status = networkMonitor.getCurrentStatus();
    this.setData({
      networkStatus: status.isConnected ? 'connected' : 'disconnected',
    });

    // 监听网络状态变化
    networkMonitor.addListener((currentStatus, previousStatus) => {
      this.setData({
        networkStatus: currentStatus.isConnected ? 'connected' : 'disconnected',
      });

      if (!previousStatus.isConnected && currentStatus.isConnected) {
        // 网络恢复时清除错误状态
        this.setData({ loginError: null });
      }
    });
  },

  /**
   * 检查自动登录
   */
  async checkAutoLogin() {
    try {
      const isLoggedIn = await authManager.isLoggedIn();
      if (isLoggedIn) {
        const isTokenValid = await authManager.isTokenValid();
        if (isTokenValid) {
          // 已登录且Token有效，直接跳转首页
          console.log('检测到有效登录状态，跳转首页');
          wx.switchTab({
            url: '/pages/index/index',
          });
          return;
        } else {
          // Token过期，尝试刷新
          try {
            await authManager.refreshToken();
            console.log('Token刷新成功，跳转首页');
            wx.switchTab({
              url: '/pages/index/index',
            });
            return;
          } catch (refreshError) {
            console.log('Token刷新失败，需要重新登录');
            await authManager.clearUserSession();
          }
        }
      }
    } catch (error) {
      console.error('自动登录检查失败:', error);
    }
  },

  /**
   * 微信登录
   */
  async onWechatLogin() {
    if (this.data.loading) {
      return; // 防止重复点击
    }

    // 检查网络状态
    if (this.data.networkStatus !== 'connected') {
      this.showError('网络连接不可用，请检查网络设置');
      return;
    }

    try {
      this.setData({
        loading: true,
        loginError: null,
      });

      console.log('开始微信登录流程');

      // **关键修复**: 在用户点击事件中直接获取用户信息授权
      const userProfile = await new Promise((resolve, reject) => {
        wx.getUserProfile({
          desc: '用于完善用户资料',
          success: res => resolve(res),
          fail: error => {
            if (error.errMsg && error.errMsg.includes('cancel')) {
              reject(new Error('用户取消授权'));
            } else {
              reject(new Error(error.errMsg || '获取用户信息失败'));
            }
          },
        });
      });

      console.log('用户信息授权成功');

      // 使用认证管理器执行登录（传入已获取的用户信息）
      const result = await authManager.wechatLoginWithProfile(userProfile);

      if (result.success) {
        const { user: userInfo, role } = result.data;
        console.log('登录成功:', { userId: userInfo.id, role });

        // 显示登录成功提示
        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500,
        });

        // 延迟跳转，让用户看到成功提示
        setTimeout(() => {
          // 检查是否需要角色选择
          if (!role || role === 'undefined') {
            // 新用户需要选择角色
            wx.redirectTo({
              url: '/pages/role-selection/index',
            });
            return;
          }

          // 根据用户角色跳转到相应页面
          if (role === 'teacher') {
            wx.switchTab({
              url: '/pages/index/index',
            });
          } else if (role === 'parent') {
            wx.switchTab({
              url: '/pages/analysis/progress/index',
            });
          } else {
            // 默认学生角色
            wx.switchTab({
              url: '/pages/index/index',
            });
          }
        }, 1500);
      } else {
        // 登录失败
        const errorMessage = result.error?.message || '登录失败，请重试';
        this.showError(errorMessage);
        console.error('登录失败:', result.error);
      }
    } catch (error) {
      console.error('登录过程异常:', error);

      let errorMessage = '登录失败，请重试';

      if (error.message) {
        if (error.message.includes('用户取消授权')) {
          errorMessage = '需要获取您的微信信息才能继续使用';
        } else if (error.message.includes('网络')) {
          errorMessage = '网络连接异常，请检查网络后重试';
        } else if (error.message.includes('timeout')) {
          errorMessage = '请求超时，请稍后重试';
        }
      }

      this.showError(errorMessage);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 显示错误信息
   */
  showError(message) {
    this.setData({ loginError: message });
    errorToast.show(message, {
      duration: 3000,
    });
  },

  /**
   * 重试登录
   */
  onRetryLogin() {
    this.setData({ loginError: null });
    this.onWechatLogin();
  },

  /**
   * 查看网络设置
   */
  onCheckNetwork() {
    errorToast.confirm('网络设置', '请检查您的网络连接是否正常，或者尝试切换网络环境', {
      confirmText: '我知道了',
      showCancel: false,
    });
  },
});
