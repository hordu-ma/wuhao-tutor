// pages/profile/index/index.js - 用户信息展示页面

const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { api, apiClient } = require('../../../utils/api.js');
const { errorToast } = require('../../../utils/error-toast.js');
const { avatarUploadManager } = require('../../../utils/avatar-upload.js');
const { syncManager } = require('../../../utils/sync-manager.js');

const pageObject = {
  data: {
    userInfo: null,
    userRole: '',
    loading: true,
    refreshing: false,

    // 用户统计信息
    stats: {
      joinDate: '',
      lastLoginDate: '',
      homeworkCount: 0,
      questionCount: 0,
      studyDays: 0,
      totalScore: 0,
      avgScore: 0,
      errorCount: 0,
      studyHours: 0,
    },

    // 显示控制
    showStatsSection: true,
    showContactInfo: true,

    // 同步状态
    syncStatus: 'idle',
    lastSyncTime: 0,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('个人信息页面加载', options);

    // 移除手动的守卫检查,由 createGuardedPage 统一处理
    await this.initPage();
  },

  /**
   * 生命周期函数--监听页面显示
   */
  async onShow() {
    console.log('个人信息页面显示');

    // 每次显示时刷新用户信息（可能在设置页面被修改）
    if (!this.data.loading) {
      await this.refreshUserInfo();
    }
  },

  /**
   * 页面下拉刷新
   */
  async onPullDownRefresh() {
    console.log('下拉刷新用户信息');
    await this.refreshUserInfo();
    wx.stopPullDownRefresh();
  },

  /**
   * 初始化页面
   */
  async initPage() {
    try {
      this.setData({ loading: true });

      // 设置同步监听器
      this.setupSyncListener();

      // 加载本地数据
      await Promise.all([this.loadUserInfo(), this.loadUserStats()]);

      // 检查是否需要后台同步（不阻塞页面）
      if (authManager.needsUserInfoRefresh()) {
        this.triggerUserInfoSync();
      }
    } catch (error) {
      console.error('初始化页面失败:', error);
      errorToast.show('页面加载失败，请稍后重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 设置同步监听器
   */
  setupSyncListener() {
    this.syncListener = syncManager.addSyncListener(event => {
      if (event.type === 'statusChange') {
        this.setData({
          syncStatus: event.currentStatus,
          lastSyncTime: Date.now(),
        });

        // 同步成功后刷新用户信息
        if (event.currentStatus === 'success') {
          this.refreshUserInfoFromCache();
        }
      }
    });
  },

  /**
   * 从缓存刷新用户信息
   */
  async refreshUserInfoFromCache() {
    try {
      const [userInfo, userRole] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole(),
      ]);

      this.setData({ userInfo, userRole });
    } catch (error) {
      console.error('从缓存刷新用户信息失败:', error);
    }
  },

  /**
   * 触发用户信息同步
   */
  triggerUserInfoSync() {
    // 完全异步执行，不阻塞页面加载
    syncManager
      .manualSyncUserInfo()
      .then(() => {
        console.log('后台同步用户信息成功');
        // 同步成功后刷新显示
        this.refreshUserInfoFromCache();
      })
      .catch(error => {
        console.warn('后台同步用户信息失败（静默）:', error);
        // 完全静默失败，不影响用户体验
      });
  },

  /**
   * 加载用户信息
   */
  async loadUserInfo() {
    try {
      // 从本地缓存获取基础信息
      const [userInfo, userRole] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole(),
      ]);

      this.setData({
        userInfo,
        userRole,
      });

      // 异步获取最新的服务器信息
      this.fetchLatestUserInfo();
    } catch (error) {
      console.error('加载用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 从服务器获取最新用户信息
   */
  async fetchLatestUserInfo() {
    try {
      const response = await apiClient.get('/auth/me');

      if (response.success && response.data) {
        const serverUserInfo = response.data;

        // 合并本地和服务器信息
        const mergedUserInfo = {
          ...this.data.userInfo,
          ...serverUserInfo,
          // 保持本地头像URL（如果存在）
          avatarUrl: serverUserInfo.avatar_url || this.data.userInfo?.avatarUrl,
        };

        this.setData({ userInfo: mergedUserInfo });

        // 更新本地缓存
        await authManager.updateUserInfo(mergedUserInfo);
      }
    } catch (error) {
      console.warn('获取服务器用户信息失败:', error);
      // 静默失败，使用本地缓存的信息
    }
  },

  /**
   * 加载用户统计信息
   */
  async loadUserStats() {
    try {
      // 复用学习报告的 analytics 接口（包含所有统计数据）
      const response = await apiClient
        .get('/analytics/learning-stats', {
          params: { time_range: '30d' }, // 最近30天数据
        })
        .catch(() => null);

      let stats = {};

      if (response && response.success && response.data) {
        // 使用 analytics 接口返回的数据
        const data = response.data;
        stats = {
          joinDate: this.formatJoinDate(this.data.userInfo?.createdAt),
          lastLoginDate: this.formatLastLogin(),
          // 真实数据：从 analytics 获取
          homeworkCount: data.image_questions || 0, // 图片提问数（作业问答）
          questionCount: data.total_questions || 0, // 总提问数
          studyDays: data.total_sessions || 0, // 学习会话数（天数）
          avgScore: data.avg_rating > 0 ? Math.round(data.avg_rating * 20) : 0, // 评分转百分制
          errorCount: data.mistake_count || 0, // 错题数
          // 暂未实现的数据显示占位符
          totalScore: '--', // 总分（暂未实现）
          studyHours: '--', // 学习时长（暂未实现）
        };
      } else {
        // API调用失败，使用本地缓存或占位数据
        const cachedStats = wx.getStorageSync('user_stats_cache');

        if (cachedStats && Date.now() - cachedStats.timestamp < 3600000) {
          // 缓存未过期（1小时）
          stats = cachedStats.data;
        } else {
          // 使用占位数据（首次加载或缓存过期）
          stats = {
            joinDate: this.formatJoinDate(this.data.userInfo?.createdAt),
            lastLoginDate: this.formatLastLogin(),
            homeworkCount: '--',
            questionCount: '--',
            studyDays: '--',
            totalScore: '--',
            avgScore: '--',
            errorCount: '--',
            studyHours: '--',
          };
        }
      }

      this.setData({ stats });

      // 缓存统计数据
      wx.setStorageSync('user_stats_cache', {
        data: stats,
        timestamp: Date.now(),
      });
    } catch (error) {
      console.warn('加载统计信息失败:', error);
      // 统计信息加载失败不影响主要功能

      // 尝试使用缓存数据
      const cachedStats = wx.getStorageSync('user_stats_cache');
      if (cachedStats && cachedStats.data) {
        this.setData({ stats: cachedStats.data });
      }
    }
  },

  /**
   * 刷新用户信息
   */
  async refreshUserInfo() {
    try {
      this.setData({ refreshing: true });

      await Promise.all([this.fetchLatestUserInfo(), this.loadUserStats()]);

      console.log('用户信息刷新成功');
    } catch (error) {
      console.error('刷新用户信息失败:', error);
      errorToast.show('刷新失败，请稍后重试');
    } finally {
      this.setData({ refreshing: false });
    }
  },

  /**
   * 格式化加入日期
   */
  formatJoinDate(createdAt) {
    if (!createdAt) return '未知';

    try {
      const date = new Date(createdAt);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}年${month}月${day}日`;
    } catch (error) {
      return '未知';
    }
  },

  /**
   * 格式化最后登录时间
   */
  formatLastLogin(lastLogin) {
    try {
      if (lastLogin) {
        const date = new Date(lastLogin);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return '刚刚';
        if (diffMins < 60) return `${diffMins}分钟前`;
        if (diffHours < 24) return `${diffHours}小时前`;
        if (diffDays < 7) return `${diffDays}天前`;

        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      }

      return '今天';
    } catch (error) {
      return '今天';
    }
  },

  /**
   * 获取角色显示名称
   */
  getRoleDisplayName(role) {
    const roleMap = {
      student: '学生',
      parent: '家长',
      teacher: '教师',
      admin: '管理员',
    };
    return roleMap[role] || role;
  },

  /**
   * 点击头像 - 进入头像编辑
   */
  onAvatarTap() {
    console.log('点击头像');

    wx.showActionSheet({
      itemList: ['查看大图', '更换头像'],
      success: res => {
        if (res.tapIndex === 0) {
          this.previewAvatar();
        } else if (res.tapIndex === 1) {
          this.changeAvatar();
        }
      },
    });
  },

  /**
   * 预览头像大图
   */
  previewAvatar() {
    const avatarUrl = this.data.userInfo?.avatarUrl;
    avatarUploadManager.previewAvatar(avatarUrl);
  },

  /**
   * 更换头像
   */
  async changeAvatar() {
    try {
      const result = await avatarUploadManager.selectAndUploadAvatar();

      if (result && result.success) {
        // 更新页面显示的用户信息
        const updatedUserInfo = {
          ...this.data.userInfo,
          avatarUrl: result.avatarUrl,
        };

        this.setData({ userInfo: updatedUserInfo });
        console.log('头像更换成功:', result.avatarUrl);
      }
    } catch (error) {
      console.error('更换头像失败:', error);
      // 错误处理已在 avatarUploadManager 中完成
    }
  },

  /**
   * 编辑个人信息
   */
  onEditProfile() {
    console.log('编辑个人信息');

    wx.navigateTo({
      url: '/pages/profile/edit/index',
    });
  },

  /**
   * 进入设置页面
   */
  onSettingsTap() {
    console.log('进入设置');

    wx.navigateTo({
      url: '/pages/profile/settings/index',
    });
  },

  /**
   * 进入帮助中心
   */
  onHelpTap() {
    console.log('进入帮助中心');

    wx.navigateTo({
      url: '/pages/profile/help/index',
    });
  },

  /**
   * 查看作业记录
   */
  onViewHomework() {
    console.log('查看作业记录');

    wx.navigateTo({
      url: '/pages/homework/list/index',
    });
  },

  /**
   * 查看问答历史
   */
  onViewQuestions() {
    console.log('查看问答历史');

    wx.navigateTo({
      url: '/pages/chat/history/index',
    });
  },

  /**
   * 页面分享
   */
  onShareAppMessage() {
    return {
      title: '五好伴学 - 我的个人信息',
      path: '/pages/profile/index/index',
      imageUrl: '/assets/images/share-profile.png',
    };
  },
};

// 使用守卫包装页面
Page(createGuardedPage(pageObject, 'pages/profile/index/index'));
