// 设置页面逻辑
import { request } from '../../../utils/request';
const { authManager } = require('../../../utils/auth.js');

Page({
  data: {
    // 设置项
    settings: {
      notification: true,
      homeworkReminder: true,
      qaNotification: true,
      recordVisible: true,
      autoSaveDraft: true,
      studyReminder: true,
      defaultDifficulty: '中等',
    },

    // 缓存大小
    cacheSize: '计算中...',

    // 应用版本
    appVersion: '1.0.0',

    // 难度选择
    showDifficultySheet: false,
    difficultyOptions: [
      { name: '简单', value: 'easy' },
      { name: '中等', value: 'medium' },
      { name: '困难', value: 'hard' },
      { name: '专家', value: 'expert' },
    ],

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
    this.loadSettings();
    this.calculateCacheSize();
  },

  /**
   * 加载设置
   */
  loadSettings() {
    try {
      const settings = wx.getStorageSync('user_settings');
      if (settings) {
        this.setData({
          settings: {
            ...this.data.settings,
            ...settings,
          },
        });
      }
    } catch (error) {
      console.error('加载设置失败:', error);
    }
  },

  /**
   * 保存设置
   */
  saveSettings() {
    try {
      wx.setStorageSync('user_settings', this.data.settings);
    } catch (error) {
      console.error('保存设置失败:', error);
    }
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
   * 消息通知开关
   */
  onNotificationChange(event) {
    const checked = event.detail;
    this.setData({
      'settings.notification': checked,
    });
    this.saveSettings();

    if (checked) {
      // 请求订阅消息权限
      this.requestSubscribeMessage();
    }
  },

  /**
   * 作业提醒开关
   */
  onHomeworkReminderChange(event) {
    this.setData({
      'settings.homeworkReminder': event.detail,
    });
    this.saveSettings();
  },

  /**
   * 问答通知开关
   */
  onQaNotificationChange(event) {
    this.setData({
      'settings.qaNotification': event.detail,
    });
    this.saveSettings();
  },

  /**
   * 学习记录可见开关
   */
  onRecordVisibleChange(event) {
    this.setData({
      'settings.recordVisible': event.detail,
    });
    this.saveSettings();
  },

  /**
   * 自动保存草稿开关
   */
  onAutoSaveDraftChange(event) {
    this.setData({
      'settings.autoSaveDraft': event.detail,
    });
    this.saveSettings();
  },

  /**
   * 学习提醒开关
   */
  onStudyReminderChange(event) {
    this.setData({
      'settings.studyReminder': event.detail,
    });
    this.saveSettings();
  },

  /**
   * 请求订阅消息权限
   */
  requestSubscribeMessage() {
    wx.requestSubscribeMessage({
      tmplIds: [
        // TODO: 替换为实际的模板ID
        'templateId1',
        'templateId2',
      ],
      success: res => {
        console.log('订阅消息成功:', res);
      },
      fail: err => {
        console.log('订阅消息失败:', err);
      },
    });
  },

  /**
   * 隐私政策
   */
  onPrivacyPolicy() {
    wx.navigateTo({
      url: '/pages/webview/index?url=privacy-policy&title=隐私政策',
    });
  },

  /**
   * 用户协议
   */
  onUserAgreement() {
    wx.navigateTo({
      url: '/pages/webview/index?url=user-agreement&title=用户协议',
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
   * 数据管理
   */
  onDataManagement() {
    wx.showModal({
      title: '数据管理',
      content: '您可以选择导出学习数据或删除所有本地数据',
      confirmText: '导出数据',
      cancelText: '删除数据',
      success: res => {
        if (res.confirm) {
          this.exportData();
        } else if (res.cancel) {
          this.confirmDeleteData();
        }
      },
    });
  },

  /**
   * 导出数据
   */
  exportData() {
    wx.showToast({
      title: '数据导出功能开发中',
      icon: 'none',
    });
  },

  /**
   * 确认删除数据
   */
  confirmDeleteData() {
    wx.showModal({
      title: '警告',
      content: '删除数据后无法恢复，确定要删除吗？',
      confirmText: '确定删除',
      confirmColor: '#f5222d',
      success: res => {
        if (res.confirm) {
          this.deleteAllData();
        }
      },
    });
  },

  /**
   * 删除所有数据
   */
  deleteAllData() {
    try {
      wx.clearStorageSync();
      wx.showToast({
        title: '数据已清除',
        icon: 'success',
      });

      // 跳转到登录页
      setTimeout(() => {
        wx.reLaunch({
          url: '/pages/login/index',
        });
      }, 1500);
    } catch (error) {
      console.error('删除数据失败:', error);
      wx.showToast({
        title: '删除失败',
        icon: 'error',
      });
    }
  },

  /**
   * 默认难度设置
   */
  onDifficultyLevel() {
    this.setData({
      showDifficultySheet: true,
    });
  },

  /**
   * 关闭难度选择
   */
  onCloseDifficultySheet() {
    this.setData({
      showDifficultySheet: false,
    });
  },

  /**
   * 选择难度
   */
  onSelectDifficulty(event) {
    const { name } = event.detail;
    this.setData({
      'settings.defaultDifficulty': name,
      showDifficultySheet: false,
    });
    this.saveSettings();
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
    wx.navigateTo({
      url: '/pages/profile/feedback/index',
    });
  },

  /**
   * 关于我们
   */
  onAbout() {
    wx.navigateTo({
      url: '/pages/profile/about/index',
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
      // 清除除了用户设置和登录信息外的所有缓存
      const settings = wx.getStorageSync('user_settings');
      const token = wx.getStorageSync('token');
      const userInfo = wx.getStorageSync('userInfo');

      wx.clearStorageSync();

      // 恢复重要数据
      if (settings) wx.setStorageSync('user_settings', settings);
      if (token) wx.setStorageSync('token', token);
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
  async performLogout() {
    wx.showLoading({
      title: '退出中...',
    });

    try {
      // ✅ 调用 authManager 的完整退出流程
      await authManager.logout();

      wx.hideLoading();

      wx.showToast({
        title: '已退出登录',
        icon: 'success',
      });

      // 跳转到登录页
      setTimeout(() => {
        wx.reLaunch({
          url: '/pages/login/index',
        });
      }, 1500);
    } catch (error) {
      console.error('退出登录失败:', error);
      wx.hideLoading();

      // 即使出错也强制清理并跳转
      wx.clearStorageSync();

      wx.showToast({
        title: '退出成功',
        icon: 'success',
      });

      setTimeout(() => {
        wx.reLaunch({
          url: '/pages/login/index',
        });
      }, 1500);
    }
  },
});
