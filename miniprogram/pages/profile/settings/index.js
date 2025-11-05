// 设置页面逻辑
import { request } from '../../../utils/request';
const { authManager } = require('../../../utils/auth.js');

Page({
  data: {
    // 缓存大小
    cacheSize: '计算中...',

    // 应用版本
    appVersion: '1.0.0',

    // 对话框
    showDialog: false,
    dialogTitle: '',
    dialogContent: '',
    dialogAction: '',
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('设置页面加载');
    this.calculateCacheSize();
  },

  /**
   * 计算缓存大小
   */
  calculateCacheSize() {
    try {
      const info = wx.getStorageInfoSync();
      const sizeKB = info.currentSize;

      let displaySize = '';
      if (sizeKB < 1024) {
        displaySize = `${sizeKB} KB`;
      } else {
        displaySize = `${(sizeKB / 1024).toFixed(2)} MB`;
      }

      this.setData({
        cacheSize: displaySize,
      });
    } catch (error) {
      console.error('计算缓存大小失败:', error);
      this.setData({
        cacheSize: '未知',
      });
    }
  },

  /**
   * 隐私政策
   */
  onPrivacyPolicy() {
    wx.showModal({
      title: '隐私政策',
      content:
        '五好伴学隐私政策要点：\n\n1. 数据加密传输，端到端保护\n2. 不向第三方共享个人信息\n3. 作业照片仅用于批改和学习分析\n4. 学习数据自动云端同步\n5. 支持数据访问和删除请求\n\n详细内容请联系客服获取',
      confirmText: '我知道了',
      showCancel: false,
    });
  },

  /**
   * 用户协议
   */
  onUserAgreement() {
    wx.showModal({
      title: '用户协议',
      content:
        '五好伴学用户协议要点：\n\n1. 本服务面向K12学生和家长\n2. 请合理使用AI辅导功能\n3. 禁止上传违规内容\n4. 保护账号安全\n5. 遵守学习规范\n\n详细内容请联系客服获取',
      confirmText: '我知道了',
      showCancel: false,
    });
  },

  /**
   * 清除缓存
   */
  onClearCache() {
    this.setData({
      showDialog: true,
      dialogTitle: '清除缓存',
      dialogContent: '清除缓存后，下次启动会重新加载数据。确定要清除吗？',
      dialogAction: 'clearCache',
    });
  },

  /**
   * 检查更新
   */
  onCheckUpdate() {
    wx.showLoading({
      title: '检查中...',
    });

    const updateManager = wx.getUpdateManager();

    updateManager.onCheckForUpdate(res => {
      wx.hideLoading();

      if (res.hasUpdate) {
        wx.showModal({
          title: '发现新版本',
          content: '发现新版本，是否下载更新？',
          success: modalRes => {
            if (modalRes.confirm) {
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
                wx.showModal({
                  title: '更新失败',
                  content: '新版本下载失败，请稍后再试',
                  showCancel: false,
                });
              });
            }
          },
        });
      } else {
        wx.showToast({
          title: '已是最新版本',
          icon: 'success',
        });
      }
    });
  },

  /**
   * 意见反馈
   */
  onFeedback() {
    wx.showModal({
      title: '意见反馈',
      content: '请添加客服微信反馈问题和建议\n客服微信号已复制到剪贴板',
      confirmText: '好的',
      showCancel: false,
      success: () => {
        wx.setClipboardData({
          data: 'wuhao_service',
          success: () => {
            console.log('客服微信号已复制');
          },
        });
      },
    });
  },

  /**
   * 关于我们
   */
  onAbout() {
    wx.showModal({
      title: '关于五好伴学',
      content: `版本：${this.data.appVersion}\n\n五好伴学是专业的K12智能学习辅导平台，提供AI作业批改、学习问答、错题管理和学情分析服务。\n\n客服微信：wuhao_service`,
      confirmText: '复制客服微信',
      cancelText: '知道了',
      success: res => {
        if (res.confirm) {
          wx.setClipboardData({
            data: 'wuhao_service',
            success: () => {
              wx.showToast({
                title: '微信号已复制',
                icon: 'success',
              });
            },
          });
        }
      },
    });
  },

  /**
   * 退出登录
   */
  onLogout() {
    this.setData({
      showDialog: true,
      dialogTitle: '退出登录',
      dialogContent: '确定要退出登录吗？',
      dialogAction: 'logout',
    });
  },

  /**
   * 对话框确认
   */
  onDialogConfirm() {
    const action = this.data.dialogAction;

    if (action === 'clearCache') {
      this.performClearCache();
    } else if (action === 'logout') {
      this.performLogout();
    }

    this.setData({
      showDialog: false,
    });
  },

  /**
   * 对话框取消
   */
  onDialogCancel() {
    this.setData({
      showDialog: false,
    });
  },

  /**
   * 执行清除缓存
   */
  performClearCache() {
    try {
      // 清除除了登录信息外的所有缓存
      const token = wx.getStorageSync('token');
      const refreshToken = wx.getStorageSync('refresh_token');
      const userInfo = wx.getStorageSync('userInfo');

      wx.clearStorageSync();

      // 恢复登录信息
      if (token) wx.setStorageSync('token', token);
      if (refreshToken) wx.setStorageSync('refresh_token', refreshToken);
      if (userInfo) wx.setStorageSync('userInfo', userInfo);

      wx.showToast({
        title: '缓存已清除',
        icon: 'success',
      });

      // 重新计算缓存大小
      this.calculateCacheSize();
    } catch (error) {
      console.error('清除缓存失败:', error);
      wx.showToast({
        title: '清除失败',
        icon: 'error',
      });
    }
  },

  /**
   * 执行退出登录
   */
  // 执行退出登录
  async performLogout() {
    try {
      // 显示加载提示
      wx.showLoading({
        title: '退出中...',
        mask: true,
      });

      // 调用退出接口（跳过二次确认，因为用户已在 van-dialog 中确认）
      await authManager.logout({
        skipConfirmation: true,
      });

      // 清理用户信息
      this.setData({
        userInfo: null,
        avatarUrl: '/images/icons/default-avatar.png',
      });

      // 隐藏加载
      wx.hideLoading();

      // 提示退出成功
      wx.showToast({
        title: '已退出登录',
        icon: 'success',
        duration: 1500,
      });

      // 延迟跳转到登录页
      setTimeout(() => {
        wx.reLaunch({
          url: '/pages/auth/login/index',
        });
      }, 1500);
    } catch (error) {
      console.error('退出登录失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '退出失败',
        icon: 'error',
      });
    }
  },
});
