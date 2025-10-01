// pages/index/index.js - 五好伴学小程序首页

const { routeGuard } = require('../../utils/route-guard.js');
const { authManager } = require('../../utils/auth.js');

Page({
  data: {
    userInfo: null,
    hasUserInfo: false,
    canIUseGetUserProfile: !!wx.getUserProfile,
    role: null,
    quickActions: [],
    notifications: [],
    stats: {
      homeworkCount: 0,
      questionCount: 0,
      reportCount: 0,
      todayStudyTime: 0,
    },
    loading: true,
    isLoggedIn: false,
  },

  async onLoad() {
    console.log('首页加载');
    
    // 检查登录状态，但不强制要求登录（首页可以部分访问）
    const isLoggedIn = await authManager.isLoggedIn();
    this.setData({ isLoggedIn });
    
    await this.initPage();
  },

  async onShow() {
    console.log('首页显示');
    
    // 每次显示时检查登录状态
    const isLoggedIn = await authManager.isLoggedIn();
    if (isLoggedIn !== this.data.isLoggedIn) {
      this.setData({ isLoggedIn });
      await this.initPage(); // 登录状态变化时重新初始化
    } else if (isLoggedIn) {
      await this.refreshData();
    }
  },

  onPullDownRefresh() {
    this.refreshData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    console.log('到达页面底部');
  },

  onShareAppMessage() {
    return {
      title: '五好伴学 - AI智能学习助手',
      path: '/pages/index/index',
      imageUrl: '/assets/images/share-logo.png',
    };
  },

  /**
   * 初始化页面
   */
  async initPage() {
    try {
      this.setData({ loading: true });

      if (this.data.isLoggedIn) {
        // 已登录用户，加载完整功能
        await this.initLoggedInUser();
      } else {
        // 未登录用户，显示引导页面
        this.initGuestUser();
      }
    } catch (error) {
      console.error('初始化页面失败:', error);
      this.showError('页面加载失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 初始化已登录用户
   */
  async initLoggedInUser() {
    try {
      // 获取用户信息
      const [userInfo, role] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole()
      ]);

      if (userInfo && role) {
        this.setData({
          userInfo,
          hasUserInfo: true,
          role,
        });

        // 初始化快捷操作
        this.initQuickActions(role);

        // 加载用户数据
        await this.loadUserData();
      } else {
        console.warn('获取用户信息失败，清理登录状态');
        await authManager.clearUserSession();
        this.setData({ isLoggedIn: false });
        this.initGuestUser();
      }
    } catch (error) {
      console.error('初始化已登录用户失败:', error);
      // 出错时回退到游客模式
      this.setData({ isLoggedIn: false });
      this.initGuestUser();
    }
  },

  /**
   * 初始化游客用户
   */
  initGuestUser() {
    this.setData({
      userInfo: null,
      hasUserInfo: false,
      role: null,
      quickActions: [
        {
          id: 'login',
          title: '立即登录',
          icon: '/assets/icons/login.png',
          path: '/pages/login/index',
          color: '#1890ff',
        },
        {
          id: 'demo',
          title: '体验演示',
          icon: '/assets/icons/demo.png',
          action: 'showDemo',
          color: '#52c41a',
        }
      ],
      notifications: [
        {
          id: 'welcome',
          type: 'info',
          title: '欢迎使用五好伴学',
          content: '登录后即可体验完整的AI学习功能',
          time: new Date().toLocaleTimeString()
        }
      ],
      stats: {
        homeworkCount: 0,
        questionCount: 0,
        reportCount: 0,
        todayStudyTime: 0,
      }
    });
  },

  /**
   * 刷新数据
   */
  async refreshData() {
    try {
      if (!this.data.hasUserInfo) {
        return;
      }

      await Promise.all([
        this.loadUserStats(),
        this.loadNotifications(),
      ]);
    } catch (error) {
      console.error('刷新数据失败:', error);
    }
  },

  /**
   * 初始化快捷操作
   */
  initQuickActions(role) {
    let actions = [];

    switch (role) {
      case 'student':
        actions = [
          {
            id: 'homework',
            title: '作业',
            icon: '/assets/icons/homework.png',
            path: '/pages/homework/list/index',
            color: '#1890ff',
          },
          {
            id: 'chat',
            title: '问答',
            icon: '/assets/icons/chat.png',
            path: '/pages/chat/index/index',
            color: '#52c41a',
          },
          {
            id: 'report',
            title: '报告',
            icon: '/assets/icons/report.png',
            path: '/pages/analysis/report/index',
            color: '#faad14',
          },
          {
            id: 'profile',
            title: '我的',
            icon: '/assets/icons/profile.png',
            path: '/pages/profile/index/index',
            color: '#722ed1',
          },
        ];
        break;
      case 'parent':
        actions = [
          {
            id: 'progress',
            title: '学情',
            icon: '/assets/icons/progress.png',
            path: '/pages/analysis/progress/index',
            color: '#1890ff',
          },
          {
            id: 'homework',
            title: '作业',
            icon: '/assets/icons/homework.png',
            path: '/pages/homework/list/index',
            color: '#52c41a',
          },
          {
            id: 'report',
            title: '报告',
            icon: '/assets/icons/report.png',
            path: '/pages/analysis/report/index',
            color: '#faad14',
          },
          {
            id: 'settings',
            title: '设置',
            icon: '/assets/icons/settings.png',
            path: '/pages/profile/settings/index',
            color: '#722ed1',
          },
        ];
        break;
      case 'teacher':
        actions = [
          {
            id: 'homework',
            title: '作业管理',
            icon: '/assets/icons/homework.png',
            path: '/pages/homework/list/index',
            color: '#1890ff',
          },
          {
            id: 'analysis',
            title: '班级分析',
            icon: '/assets/icons/analysis.png',
            path: '/pages/analysis/class/index',
            color: '#52c41a',
          },
          {
            id: 'students',
            title: '学生管理',
            icon: '/assets/icons/students.png',
            path: '/pages/students/list/index',
            color: '#faad14',
          },
          {
            id: 'profile',
            title: '个人中心',
            icon: '/assets/icons/profile.png',
            path: '/pages/profile/index/index',
            color: '#722ed1',
          },
        ];
        break;
    }

    this.setData({ quickActions: actions });
  },

  /**
   * 加载用户数据
   */
  async loadUserData() {
    await Promise.all([
      this.loadUserStats(),
      this.loadNotifications(),
    ]);
  },

  /**
   * 加载用户统计数据
   */
  async loadUserStats() {
    try {
      // TODO: 调用API获取用户统计数据
      // const response = await api.getUserStats();

      // 模拟数据
      const stats = {
        homeworkCount: 5,
        questionCount: 23,
        reportCount: 3,
        todayStudyTime: 120,
      };

      this.setData({ stats });
    } catch (error) {
      console.error('加载用户统计失败:', error);
    }
  },

  /**
   * 加载通知数据
   */
  async loadNotifications() {
    try {
      // TODO: 调用API获取通知数据
      // const response = await api.getNotifications({ limit: 3 });

      // 模拟数据
      const notifications = [
        {
          id: '1',
          title: '作业提醒',
          content: '您有2份作业即将到期，请及时完成',
          type: 'homework',
          sender: '系统',
          recipient: this.data.userInfo?.id || '',
          isRead: false,
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          title: '学习报告',
          content: '本周学习报告已生成，快来查看吧',
          type: 'grade',
          sender: '系统',
          recipient: this.data.userInfo?.id || '',
          isRead: false,
          createdAt: new Date().toISOString(),
        },
      ];

      this.setData({ notifications });
    } catch (error) {
      console.error('加载通知失败:', error);
    }
  },

  /**
   * 点击快捷操作
   */
  onQuickActionTap(e) {
    const { action } = e.currentTarget.dataset;
    if (!action) return;

    console.log('点击快捷操作:', action);

    wx.navigateTo({
      url: action.path,
      fail: () => {
        wx.switchTab({
          url: action.path,
        });
      },
    });
  },

  /**
   * 点击通知
   */
  onNotificationTap(e) {
    const { notification } = e.currentTarget.dataset;
    if (!notification) return;

    console.log('点击通知:', notification);

    // 标记为已读
    this.markNotificationRead(notification.id);

    // 根据通知类型跳转到相应页面
    let url = '';
    switch (notification.type) {
      case 'homework':
        url = '/pages/homework/list/index';
        break;
      case 'grade':
        url = '/pages/analysis/report/index';
        break;
      case 'announcement':
        url = '/pages/announcements/detail/index?id=' + notification.id;
        break;
      default:
        return;
    }

    wx.navigateTo({ url });
  },

  /**
   * 标记通知为已读
   */
  async markNotificationRead(notificationId) {
    try {
      // TODO: 调用API标记通知为已读
      // await api.markNotificationRead(notificationId);

      // 更新本地数据
      const notifications = this.data.notifications.map(item => {
        if (item.id === notificationId) {
          return { ...item, isRead: true };
        }
        return item;
      });

      this.setData({ notifications });
    } catch (error) {
      console.error('标记通知已读失败:', error);
    }
  },

  /**
   * 查看更多通知
   */
  onMoreNotificationsTap() {
    wx.navigateTo({
      url: '/pages/notifications/list/index',
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

  /**
   * 格式化学习时长
   */
  formatStudyTime(minutes) {
    if (minutes < 60) {
      return `${minutes}分钟`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}小时${remainingMinutes}分钟` : `${hours}小时`;
  },
});
