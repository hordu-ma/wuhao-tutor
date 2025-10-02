// 关于我们页面
Page({
  data: {
    appVersion: '1.0.0',
    hasUpdate: false,
    cacheSize: '0 MB',

    // 核心功能
    features: [
      {
        id: 1,
        name: 'AI作业批改',
        desc: '智能识别,秒级批改',
        icon: 'edit',
        color: '#667eea',
      },
      {
        id: 2,
        name: '学习问答',
        desc: '随时提问,即时解答',
        icon: 'question-o',
        color: '#f093fb',
      },
      {
        id: 3,
        name: '学情分析',
        desc: '数据驱动,精准诊断',
        icon: 'chart-trending-o',
        color: '#4facfe',
      },
      {
        id: 4,
        name: '错题本',
        desc: '自动归类,巩固复习',
        icon: 'bookmark-o',
        color: '#fa709a',
      },
    ],

    // 团队介绍
    teamIntro:
      '五好伴学团队成立于2024年,由一群热爱教育的工程师和教育专家组成。我们致力于用AI技术赋能K12教育,让每个孩子都能获得个性化的学习辅导。团队成员来自清华、北大、中科院等知名高校,拥有丰富的AI和教育行业经验。',

    // 团队数据
    teamStats: [
      { label: '核心成员', value: '15+' },
      { label: '服务学生', value: '10万+' },
      { label: '批改作业', value: '50万+' },
    ],

    // 技术栈
    techStack: [
      {
        name: '阿里云百炼AI',
        desc: '提供强大的文字识别、图像理解和智能问答能力',
      },
      {
        name: 'FastAPI后端',
        desc: '高性能异步框架,保障服务稳定性和响应速度',
      },
      {
        name: 'PostgreSQL数据库',
        desc: '企业级关系型数据库,确保数据安全可靠',
      },
      {
        name: 'ECharts图表',
        desc: '专业的数据可视化库,直观展示学习数据',
      },
    ],

    // 开源许可
    licenses: [
      {
        name: 'ECharts for WeChat',
        type: 'Apache License 2.0',
        url: 'https://github.com/ecomfe/echarts-for-weixin',
      },
      {
        name: 'Vant Weapp',
        type: 'MIT License',
        url: 'https://github.com/youzan/vant-weapp',
      },
      {
        name: 'FastAPI',
        type: 'MIT License',
        url: 'https://github.com/tiangolo/fastapi',
      },
      {
        name: 'Vue.js',
        type: 'MIT License',
        url: 'https://github.com/vuejs/core',
      },
    ],

    // 法律文档
    legalDocs: [
      { id: 1, name: '用户协议' },
      { id: 2, name: '隐私政策' },
      { id: 3, name: '儿童隐私保护声明' },
      { id: 4, name: '免责声明' },
    ],
  },

  onLoad() {
    // 获取应用版本
    this.getAppVersion();
    // 计算缓存大小
    this.calculateCacheSize();
    // 检查更新
    this.checkUpdateSilently();
  },

  // 获取应用版本
  getAppVersion() {
    const accountInfo = wx.getAccountInfoSync();
    const version = accountInfo.miniProgram.version || '开发版';
    this.setData({ appVersion: version });
  },

  // 计算缓存大小
  calculateCacheSize() {
    wx.getStorageInfo({
      success: res => {
        const sizeKB = res.currentSize;
        const sizeMB = (sizeKB / 1024).toFixed(2);
        this.setData({
          cacheSize: `${sizeMB} MB`,
        });
      },
    });
  },

  // 静默检查更新
  checkUpdateSilently() {
    if (!wx.getUpdateManager) return;

    const updateManager = wx.getUpdateManager();
    updateManager.onCheckForUpdate(res => {
      this.setData({ hasUpdate: res.hasUpdate });
    });
  },

  // 检查更新
  checkUpdate() {
    wx.showLoading({ title: '检查中...' });

    if (!wx.getUpdateManager) {
      wx.hideLoading();
      wx.showModal({
        title: '提示',
        content: '当前微信版本过低,无法使用该功能,请升级到最新微信版本后重试',
        showCancel: false,
      });
      return;
    }

    const updateManager = wx.getUpdateManager();

    updateManager.onCheckForUpdate(res => {
      wx.hideLoading();

      if (res.hasUpdate) {
        wx.showModal({
          title: '发现新版本',
          content: '发现新版本,是否下载并重启应用?',
          success: modalRes => {
            if (modalRes.confirm) {
              wx.showLoading({ title: '下载中...' });

              updateManager.onUpdateReady(() => {
                wx.hideLoading();
                wx.showModal({
                  title: '更新提示',
                  content: '新版本已下载,是否重启应用?',
                  success: readyRes => {
                    if (readyRes.confirm) {
                      updateManager.applyUpdate();
                    }
                  },
                });
              });

              updateManager.onUpdateFailed(() => {
                wx.hideLoading();
                wx.showModal({
                  title: '更新失败',
                  content: '新版本下载失败,请检查网络后重试',
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
          duration: 2000,
        });
      }
    });

    updateManager.onUpdateFailed(() => {
      wx.hideLoading();
      wx.showToast({
        title: '检查更新失败',
        icon: 'none',
        duration: 2000,
      });
    });
  },

  // 清除缓存
  clearCache() {
    wx.showModal({
      title: '清除缓存',
      content: '确定清除所有缓存数据吗?\n(不包括登录信息和用户设置)',
      success: res => {
        if (res.confirm) {
          wx.showLoading({ title: '清除中...' });

          // 获取需要保留的数据
          const keepKeys = ['userInfo', 'token', 'settings'];
          const keepData = {};

          keepKeys.forEach(key => {
            const value = wx.getStorageSync(key);
            if (value) {
              keepData[key] = value;
            }
          });

          // 清除所有缓存
          wx.clearStorage({
            success: () => {
              // 恢复需要保留的数据
              Object.keys(keepData).forEach(key => {
                wx.setStorageSync(key, keepData[key]);
              });

              wx.hideLoading();
              wx.showToast({
                title: '清除成功',
                icon: 'success',
                duration: 2000,
              });

              // 重新计算缓存大小
              setTimeout(() => {
                this.calculateCacheSize();
              }, 500);
            },
            fail: () => {
              wx.hideLoading();
              wx.showToast({
                title: '清除失败',
                icon: 'none',
                duration: 2000,
              });
            },
          });
        }
      },
    });
  },

  // 查看开源许可
  viewLicense(event) {
    const url = event.currentTarget.dataset.url;

    wx.setClipboardData({
      data: url,
      success: () => {
        wx.showModal({
          title: '提示',
          content: '链接已复制,请在浏览器中打开查看',
          showCancel: false,
        });
      },
    });
  },

  // 查看法律文档
  viewLegalDoc(event) {
    const id = event.currentTarget.dataset.id;

    // TODO: 跳转到法律文档详情页
    wx.showToast({
      title: '文档详情开发中',
      icon: 'none',
      duration: 2000,
    });
  },

  // 分享
  onShareAppMessage() {
    return {
      title: '五好伴学 - 专业的K12学习辅导助手',
      path: '/pages/index/index',
      imageUrl: '/assets/images/share-about.png',
    };
  },

  onShareTimeline() {
    return {
      title: '五好伴学 - 专业的K12学习辅导助手',
      query: 'from=timeline',
      imageUrl: '/assets/images/share-about.png',
    };
  },
});
