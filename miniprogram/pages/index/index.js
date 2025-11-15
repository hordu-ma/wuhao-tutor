// pages/index/index.js - 五好伴学小程序首页

const { routeGuard } = require('../../utils/route-guard.js');
const { authManager } = require('../../utils/auth.js');

Page({
  data: {
    userInfo: null,
    hasUserInfo: false,
    canIUseGetUserProfile: !!wx.getUserProfile,
    role: null,
    recommendations: [], // 个性化推荐内容
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

      await Promise.all([this.loadUserStats(), this.loadRecommendations()]);

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
    await Promise.all([this.loadUserStats(), this.loadRecommendations()]);
  },

  /**
   * 加载用户统计数据
   */
  async loadUserStats() {
    try {
      const { api } = require('../../utils/api.js');

      // 调用后端API获取真实数据
      const response = await api.analysis.getUserStats();

      console.log('📊 [统计数据] API响应:', response);

      // 微信小程序API返回格式：{ data: {...}, statusCode: 200, header: {...} }
      // 后端数据在 response.data 中
      if (response && response.statusCode === 200 && response.data) {
        const apiResponse = response.data;

        console.log('📊 [统计数据] 后端响应:', apiResponse);

        // 后端返回格式：{ success: true, data: {...}, message: "..." }
        if (apiResponse.success && apiResponse.data) {
          const backendData = apiResponse.data;

          // 映射后端字段到前端展示
          const stats = {
            questionCount: backendData.question_count || 0,
            reportCount: backendData.homework_count || 0,
            todayStudyTime: backendData.study_hours || 0,
          };

          console.log('📊 [统计数据] 设置stats:', stats);
          this.setData({ stats });
          console.log('📊 [统计数据] 页面data.stats:', this.data.stats);
        } else {
          // API返回格式异常，使用默认值
          console.warn('⚠️ [统计数据] API返回格式异常，使用默认值', apiResponse);
          this.setData({
            stats: {
              questionCount: 0,
              reportCount: 0,
              todayStudyTime: 0,
            },
          });
        }
      } else {
        console.warn('⚠️ [统计数据] 响应状态异常:', response);
        this.setData({
          stats: {
            questionCount: 0,
            reportCount: 0,
            todayStudyTime: 0,
          },
        });
      }
    } catch (error) {
      console.error('❌ [统计数据] 加载用户统计失败:', error);

      // 错误降级：显示默认值而不是假数据
      this.setData({
        stats: {
          questionCount: 0,
          reportCount: 0,
          todayStudyTime: 0,
        },
      });

      // 不显示错误提示，避免打扰用户体验
      // 仅在控制台记录，方便调试
    }
  },

  /**
   * 加载个性化推荐内容
   */
  async loadRecommendations() {
    try {
      const { api } = require('../../utils/api.js');

      // 调用后端API获取真实推荐
      const response = await api.analysis.getHomepageRecommendations();

      console.log('📌 [推荐] API响应:', response);

      // 微信小程序API返回格式：{ data: {...}, statusCode: 200, header: {...} }
      if (response && response.statusCode === 200 && response.data) {
        const apiResponse = response.data;

        console.log('📌 [推荐] 后端响应:', apiResponse);

        // 后端返回格式：{ success: true, data: [...], message: "..." }
        if (apiResponse.success && apiResponse.data) {
          // 限制最多3条
          const recommendations = apiResponse.data.slice(0, 3);

          console.log('📌 [推荐] 设置推荐:', recommendations);
          this.setData({ recommendations });
        } else {
          console.warn('⚠️ [推荐] API返回格式异常:', apiResponse);
          this.setData({ recommendations: [] });
        }
      } else {
        console.warn('⚠️ [推荐] 响应状态异常:', response);
        this.setData({ recommendations: [] });
      }
    } catch (error) {
      console.error('❌ [推荐] 加载推荐失败:', error);

      // 错误降级：显示空数组，不影响其他功能
      this.setData({ recommendations: [] });
    }
  },

  /**
   * 点击推荐内容
   */
  onRecommendationTap(e) {
    const { recommendation } = e.currentTarget.dataset;

    console.log('📌 点击推荐内容:', recommendation);

    // 显示提示信息，不跳转
    wx.showToast({
      title: '知识点推荐',
      icon: 'none',
      duration: 2000,
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

  // ========== 快捷功能导航 ==========

  /**
   * 导航到知识图谱
   */
  navigateToKnowledgeGraph() {
    console.log('导航到知识图谱');

    // 🔧 [修复] 检查登录状态
    if (!this.data.isLoggedIn) {
      wx.showToast({
        title: '请先登录',
        icon: 'none',
        duration: 2000,
      });
      wx.navigateTo({
        url: '/pages/login/index',
      });
      return;
    }

    wx.navigateTo({
      url: '/subpackages/charts/pages/knowledge-graph/index?subject=数学',
      fail: err => {
        console.error('导航到知识图谱失败:', err);
        wx.showToast({
          title: '打开失败，请重试',
          icon: 'error',
          duration: 2000,
        });
      },
    });
  },

  /**
   * 导航到错题本
   */
  navigateToMistakes() {
    console.log('导航到错题本');

    // 🔧 [修复] 检查登录状态
    if (!this.data.isLoggedIn) {
      wx.showToast({
        title: '请先登录',
        icon: 'none',
        duration: 2000,
      });
      wx.navigateTo({
        url: '/pages/login/index',
      });
      return;
    }

    // 🔧 [修复] 使用 switchTab 而非 navigateTo，因为错题本是 tabBar 页面
    wx.switchTab({
      url: '/pages/mistakes/list/index',
      fail: err => {
        console.error('导航到错题本失败:', err);
        wx.showToast({
          title: '打开失败，请重试',
          icon: 'error',
          duration: 2000,
        });
      },
    });
  },

  /**
   * 导航到作业问答
   */
  navigateToLearning() {
    console.log('导航到作业问答');

    // 🔧 [修复] 检查登录状态
    if (!this.data.isLoggedIn) {
      wx.showToast({
        title: '请先登录',
        icon: 'none',
        duration: 2000,
      });
      wx.navigateTo({
        url: '/pages/login/index',
      });
      return;
    }

    // 🔧 [修复] 使用 switchTab 而非 navigateTo，因为作业问答是 tabBar 页面
    wx.switchTab({
      url: '/pages/learning/index/index',
      fail: err => {
        console.error('导航到作业问答失败:', err);
        wx.showToast({
          title: '打开失败，请重试',
          icon: 'error',
          duration: 2000,
        });
      },
    });
  },

  /**
   * 导航到学习报告
   */
  navigateToAnalysis() {
    console.log('导航到学习报告');

    // 🔧 [修复] 检查登录状态
    if (!this.data.isLoggedIn) {
      wx.showToast({
        title: '请先登录',
        icon: 'none',
        duration: 2000,
      });
      wx.navigateTo({
        url: '/pages/login/index',
      });
      return;
    }

    // 🔧 学习报告不是 tabBar 页面，使用 navigateTo
    wx.navigateTo({
      url: '/pages/analysis/report/index',
      fail: err => {
        console.error('导航到学习报告失败:', err);
        wx.showToast({
          title: '打开失败，请重试',
          icon: 'error',
          duration: 2000,
        });
      },
    });
  },
});
