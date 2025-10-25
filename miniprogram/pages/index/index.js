// pages/index/index.js - 五好伴学小程序首页

const { routeGuard } = require('../../utils/route-guard.js');
const { authManager } = require('../../utils/auth.js');

Page({
  data: {
    userInfo: null,
    hasUserInfo: false,
    canIUseGetUserProfile: !!wx.getUserProfile,
    role: null,
    notifications: [],
    unreadNotificationCount: 0, // 未读消息数量
    recommendations: [], // 个性化推荐内容
    todoItems: [], // 待办事项
    stats: {
      questionCount: 0,
      reportCount: 0,
      todayStudyTime: 0,
    },
    loading: true,
    refreshing: false, // 下拉刷新状态
    isLoggedIn: false,
  },

  async onLoad() {
    console.log('首页加载开始');

    try {
      // 检查登录状态，但不强制要求登录（首页可以部分访问）
      const isLoggedIn = await authManager.isLoggedIn();
      console.log('登录状态:', isLoggedIn);
      this.setData({ isLoggedIn });

      await this.initPage();
      console.log('首页加载完成');
    } catch (error) {
      console.error('首页 onLoad 失败:', error);
      this.setData({
        loading: false,
        userInfo: { nickName: '游客' },
        role: null,
      });
    }
  },

  async onShow() {
    console.log('首页显示');

    // 每次显示时检查登录状态
    const isLoggedIn = await authManager.isLoggedIn();
    console.log('onShow检查登录状态:', isLoggedIn, '当前状态:', this.data.isLoggedIn);

    if (isLoggedIn !== this.data.isLoggedIn) {
      console.log('登录状态变化，重新初始化页面');
      this.setData({ isLoggedIn });
      await this.initPage(); // 登录状态变化时重新初始化
    } else if (isLoggedIn) {
      console.log('用户已登录，刷新数据');
      await this.refreshData();
    }

    // 添加调试：直接检查用户信息并更新页面数据
    if (isLoggedIn) {
      const userInfo = await authManager.getUserInfo();
      const role = await authManager.getUserRole();
      console.log('调试用户信息:', userInfo);
      console.log('调试用户角色:', role);
      console.log('当前页面数据:', this.data.userInfo, this.data.role);

      // 重要：更新页面数据以反映最新的用户信息（包括头像）
      if (userInfo && userInfo !== this.data.userInfo) {
        console.log('🔄 [首页刷新] 用户信息有更新，刷新页面数据');
        this.setData({
          userInfo,
          role,
          hasUserInfo: true,
        });
      }
    }
  },

  onPullDownRefresh() {
    console.log('用户下拉刷新');

    this.setData({ refreshing: true });

    // 执行刷新操作
    this.refreshData()
      .then(() => {
        wx.showToast({
          title: '刷新成功',
          icon: 'success',
          duration: 1000,
        });
      })
      .catch(error => {
        console.error('刷新失败:', error);
        wx.showToast({
          title: '刷新失败，请重试',
          icon: 'error',
          duration: 1500,
        });
      })
      .finally(() => {
        this.setData({ refreshing: false });
        wx.stopPullDownRefresh();
      });
  },

  onReachBottom() {
    console.log('到达页面底部');
    // 这里可以实现加载更多功能
    this.loadMoreData();
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
      console.log('开始初始化已登录用户信息...');

      // 获取用户信息
      const [userInfo, role] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole(),
      ]);

      console.log('获取到的用户信息:', userInfo);
      console.log('获取到的用户角色:', role);

      if (userInfo && role) {
        this.setData({
          userInfo,
          hasUserInfo: true,
          role,
        });

        console.log('✅ 用户信息设置成功');

        // 加载用户数据
        await this.loadUserData();
      } else {
        console.warn('⚠️ 获取用户信息失败，但保持登录状态:', { userInfo, role });

        // 设置默认的用户信息，而不是清除登录状态
        this.setData({
          userInfo: userInfo || { nickName: '学生', id: 'unknown' },
          hasUserInfo: !!userInfo,
          role: role || 'student',
        });
      }
    } catch (error) {
      console.error('❌ 初始化已登录用户失败:', error);

      // 只有在严重错误时才回退到游客模式
      // 先尝试设置默认用户信息
      this.setData({
        userInfo: { nickName: '学生', id: 'unknown' },
        hasUserInfo: false,
        role: 'student',
      });
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
      notifications: [
        {
          id: 'welcome',
          type: 'info',
          title: '欢迎使用五好伴学',
          content: '登录后即可体验完整的AI学习功能',
          time: new Date().toLocaleTimeString(),
        },
      ],
      stats: {
        questionCount: 0,
        reportCount: 0,
        todayStudyTime: 0,
      },
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

      console.log('刷新首页数据');

      await Promise.all([
        this.loadUserStats(),
        this.loadNotifications(),
        this.loadRecommendations(),
        this.loadTodoItems(),
      ]);

      console.log('首页数据刷新完成');
    } catch (error) {
      console.error('刷新数据失败:', error);
      throw error; // 重新抛出错误以便上层处理
    }
  },

  /**
   * 加载更多数据 (到达底部时触发)
   */
  async loadMoreData() {
    try {
      if (!this.data.hasUserInfo) {
        return;
      }

      console.log('加载更多数据');

      // 这里可以加载更多的通知、活动等
      // 暂时显示提示
      wx.showToast({
        title: '暂无更多内容',
        icon: 'none',
        duration: 1500,
      });

      // TODO: 实现加载更多通知的逻辑
      // await this.loadMoreNotifications();
      // await this.loadMoreActivities();
    } catch (error) {
      console.error('加载更多数据失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'error',
        duration: 1500,
      });
    }
  },

  /**
   * 加载用户数据
   */
  async loadUserData() {
    await Promise.all([
      this.loadUserStats(),
      this.loadNotifications(),
      this.loadRecommendations(),
      this.loadTodoItems(),
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
        questionCount: 23,
        reportCount: 3,
        todayStudyTime: 0, // 设为0以展示"待开始"占位信息
      };

      console.log('📊 [统计数据] 设置stats:', stats);
      this.setData({ stats });
      console.log('📊 [统计数据] 页面data.stats:', this.data.stats);
    } catch (error) {
      console.error('加载用户统计失败:', error);
    }
  },

  /**
   * 加载通知数据
   */
  async loadNotifications() {
    try {
      const { role, userInfo } = this.data;

      // TODO: 调用API获取通知数据
      // const response = await api.getNotifications({ limit: 5, role, userId: userInfo?.id });

      // 根据用户角色生成不同的模拟通知数据
      let notifications = [];

      switch (role) {
        case 'student':
          notifications = [
            {
              id: '2',
              title: '学习报告',
              content: '本周学习报告已生成，快来查看吧！',
              type: 'grade',
              priority: 'medium',
              sender: '系统',
              recipient: userInfo?.id || '',
              isRead: false,
              createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toLocaleString(), // 4小时前
              actionUrl: '/pages/analysis/report/index',
            },
            {
              id: '3',
              title: 'AI助手回复',
              content: '您昨天提问的数学问题已有新的回复',
              type: 'chat',
              priority: 'medium',
              sender: 'AI助手',
              recipient: userInfo?.id || '',
              isRead: true,
              createdAt: new Date(Date.now() - 8 * 60 * 60 * 1000).toLocaleString(), // 8小时前
              actionUrl: '/pages/chat/index/index',
            },
          ];
          break;
        case 'parent':
          notifications = [
            {
              id: '4',
              title: '学习进度更新',
              content: '孩子本周完成学习任务，总体表现良好',
              type: 'progress',
              priority: 'medium',
              sender: '系统',
              recipient: userInfo?.id || '',
              isRead: false,
              createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toLocaleString(), // 1小时前
              actionUrl: '/pages/analysis/progress/index',
            },
            {
              id: '5',
              title: '成绩分析报告',
              content: '孩子数学成绩有所提升，建议继续加强练习',
              type: 'grade',
              priority: 'high',
              sender: '数学老师',
              recipient: userInfo?.id || '',
              isRead: false,
              createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toLocaleString(), // 3小时前
              actionUrl: '/pages/analysis/report/index',
            },
            {
              id: '6',
              title: '班级通知',
              content: '下周三将举行期中考试，请做好准备',
              type: 'announcement',
              priority: 'high',
              sender: '班主任',
              recipient: userInfo?.id || '',
              isRead: true,
              createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toLocaleString(), // 1天前
              actionUrl: '/pages/announcements/detail/index?id=6',
            },
          ];
          break;
        case 'teacher':
          notifications = [
            {
              id: '8',
              title: '班级成绩统计',
              content: '本周班级平均分有所提升，详细分析已生成',
              type: 'analysis',
              priority: 'medium',
              sender: '系统',
              recipient: userInfo?.id || '',
              isRead: false,
              createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toLocaleString(), // 2小时前
              actionUrl: '/pages/analysis/class/index',
            },
            {
              id: '9',
              title: '学生提问',
              content: '张三同学向您提问了关于函数的问题',
              type: 'chat',
              priority: 'medium',
              sender: '张三',
              recipient: userInfo?.id || '',
              isRead: true,
              createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toLocaleString(), // 5小时前
              actionUrl: '/pages/chat/teacher/index',
            },
          ];
          break;
        default:
          notifications = [
            {
              id: 'welcome',
              title: '欢迎使用五好伴学',
              content: '登录后即可体验完整的AI学习功能',
              type: 'info',
              priority: 'low',
              sender: '系统',
              recipient: '',
              isRead: false,
              createdAt: new Date().toLocaleString(),
              actionUrl: '/pages/login/index',
            },
          ];
      }

      // 按创建时间排序（最新的在前）
      notifications.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

      this.setData({ notifications });

      // 更新未读消息数量
      const unreadCount = notifications.filter(n => !n.isRead).length;
      this.setData({ unreadNotificationCount: unreadCount });
    } catch (error) {
      console.error('加载通知失败:', error);
    }
  },

  /**
   * 加载个性化推荐内容
   */
  async loadRecommendations() {
    try {
      const { role, stats } = this.data;
      let recommendations = [];

      switch (role) {
        case 'student':
          recommendations = [
            {
              id: 'study_suggestion',
              type: 'learning',
              title: 'AI学习建议',
              content: '根据您的学习情况，建议重点复习数学函数章节，并完成3道相关练习题。',
              icon: 'bulb-o',
              color: '#faad14',
              action: {
                type: 'navigate',
                url: '/pages/study/suggestions/index',
              },
              priority: 1,
            },
            {
              id: 'weak_subjects',
              type: 'improvement',
              title: '薄弱科目提升',
              content: '物理力学部分掌握度较低，推荐观看相关教学视频。',
              icon: 'chart-trending-o',
              color: '#f5222d',
              action: {
                type: 'navigate',
                url: '/pages/study/weak-subjects/index',
              },
              priority: 2,
            },
          ];
          break;
        case 'parent':
          recommendations = [
            {
              id: 'child_progress',
              type: 'monitoring',
              title: '孩子学习进度',
              content: '孩子本周完成率75%，建议关注数学学科的学习情况。',
              icon: 'bar-chart-o',
              color: '#1890ff',
              action: {
                type: 'navigate',
                url: '/pages/analysis/progress/index',
              },
              priority: 1,
            },
            {
              id: 'study_time',
              type: 'reminder',
              title: '学习时间提醒',
              content: '建议每日学习时间保持在2小时左右，劳逸结合。',
              icon: 'clock-o',
              color: '#52c41a',
              action: {
                type: 'navigate',
                url: '/pages/settings/study-time/index',
              },
              priority: 2,
            },
          ];
          break;
        case 'teacher':
          recommendations = [
            {
              id: 'class_performance',
              type: 'analysis',
              title: '班级表现分析',
              content: '本周班级平均成绩提升3分，有2名学生需要重点关注。',
              icon: 'friends-o',
              color: '#1890ff',
              action: {
                type: 'navigate',
                url: '/pages/analysis/class/index',
              },
              priority: 1,
            },
          ];
          break;
      }

      // 根据优先级排序
      recommendations.sort((a, b) => a.priority - b.priority);

      this.setData({ recommendations });
    } catch (error) {
      console.error('加载推荐内容失败:', error);
    }
  },

  /**
   * 加载待办事项
   */
  async loadTodoItems() {
    try {
      const { role } = this.data;
      let todoItems = [];

      switch (role) {
        case 'student':
          todoItems = [
            {
              id: 'review_physics',
              title: '复习物理知识点',
              description: '力学部分重点内容',
              deadline: '明天',
              priority: 'medium',
              completed: false,
              type: 'study',
            },
          ];
          break;
        case 'parent':
          todoItems = [
            {
              id: 'check_progress',
              title: '查看学习进度',
              description: '查看孩子今日学习完成情况',
              deadline: '今天',
              priority: 'medium',
              completed: false,
              type: 'monitoring',
            },
          ];
          break;
        case 'teacher':
          todoItems = [
            {
              id: 'prepare_class',
              title: '准备明天课程',
              description: '第四章教学材料',
              deadline: '明天 08:00',
              priority: 'medium',
              completed: false,
              type: 'preparation',
            },
          ];
          break;
      }

      this.setData({ todoItems });
    } catch (error) {
      console.error('加载待办事项失败:', error);
    }
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

    // 使用通知中的actionUrl或根据类型跳转
    const url = notification.actionUrl || this.getNotificationUrl(notification);

    if (url) {
      wx.navigateTo({
        url,
        fail: () => {
          wx.switchTab({ url });
        },
      });
    }
  },

  /**
   * 根据通知类型获取跳转URL
   */
  getNotificationUrl(notification) {
    switch (notification.type) {
      case 'grade':
        return '/pages/analysis/report/index';
      case 'progress':
        return '/pages/analysis/progress/index';
      case 'chat':
        return '/pages/chat/index/index';
      case 'analysis':
        return '/pages/analysis/class/index';
      case 'announcement':
        return `/pages/announcements/detail/index?id=${notification.id}`;
      case 'info':
        return '/pages/login/index';
      default:
        return '';
    }
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

      // 重新计算未读数量
      const unreadCount = notifications.filter(n => !n.isRead).length;

      this.setData({
        notifications,
        unreadNotificationCount: unreadCount,
      });

      console.log(`通知 ${notificationId} 已标记为已读，未读数量: ${unreadCount}`);
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
   * 点击推荐内容
   */
  onRecommendationTap(e) {
    const { recommendation } = e.currentTarget.dataset;
    if (!recommendation || !recommendation.action) return;

    console.log('点击推荐内容:', recommendation);

    const { action } = recommendation;
    switch (action.type) {
      case 'navigate':
        wx.navigateTo({
          url: action.url,
          fail: () => {
            wx.switchTab({ url: action.url });
          },
        });
        break;
      case 'action':
        this[action.method] && this[action.method](action.params);
        break;
      default:
        console.warn('未知的推荐内容操作类型:', action.type);
    }
  },

  /**
   * 点击待办事项
   */
  onTodoItemTap(e) {
    const { todo } = e.currentTarget.dataset;
    if (!todo) return;

    console.log('点击待办事项:', todo);

    // 根据待办事项类型跳转到相应页面
    let url = '';
    switch (todo.type) {
      case 'study':
        url = '/pages/study/detail/index?id=' + todo.id;
        break;
      case 'preparation':
        url = '/pages/teacher/preparation/index?id=' + todo.id;
        break;
      case 'monitoring':
        url = '/pages/analysis/progress/index';
        break;
      default:
        console.warn('未知的待办事项类型:', todo.type);
        return;
    }

    wx.navigateTo({
      url,
      fail: () => {
        wx.switchTab({ url });
      },
    });
  },

  /**
   * 完成待办事项
   */
  onCompleteTodoItem(e) {
    e.stopPropagation(); // 防止触发父元素的点击事件

    const { todo } = e.currentTarget.dataset;
    if (!todo) return;

    console.log('完成待办事项:', todo);

    // 更新待办事项状态
    const todoItems = this.data.todoItems.map(item => {
      if (item.id === todo.id) {
        return { ...item, completed: true };
      }
      return item;
    });

    this.setData({ todoItems });

    // TODO: 调用API更新待办事项状态
    wx.showToast({
      title: '任务完成',
      icon: 'success',
      duration: 1500,
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

  // ============ 快捷操作方法 ============

  /**
   * 测试登录
   */
  handleTestLogin() {
    console.log('测试登录按钮点击');
    wx.navigateTo({
      url: '/pages/login/index',
    });
  },

  /**
   * 测试刷新
   */
  async handleTestRefresh() {
    console.log('测试刷新按钮点击');
    try {
      this.setData({ loading: true, error: null });
      await this.refreshData();
      wx.showToast({
        title: '刷新成功',
        icon: 'success',
      });
    } catch (error) {
      console.error('刷新失败:', error);
      this.setData({ error: error.message || '刷新失败' });
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 点击登录按钮
   */
  onLoginTap() {
    console.log('点击登录按钮');
    wx.navigateTo({
      url: '/pages/login/index',
    });
  },

  /**
   * 点击设置按钮
   */
  onSettingsTap() {
    console.log('点击设置按钮');

    // 检查是否已登录
    if (!this.data.isLoggedIn) {
      wx.showToast({
        title: '请先登录',
        icon: 'none',
        duration: 2000,
      });
      return;
    }

    // 导航到"我的"页面（更完整的用户中心）
    wx.switchTab({
      url: '/pages/profile/index/index',
      fail: err => {
        console.error('导航到我的页面失败:', err);
        wx.showToast({
          title: '导航失败',
          icon: 'none',
          duration: 2000,
        });
      },
    });
  },
});
