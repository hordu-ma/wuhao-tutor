// pages/homework/list/index.js

const { routeGuard } = require('../../../utils/route-guard.js');
const { permissionManager } = require('../../../utils/permission-manager.js');
const { roleManager } = require('../../../utils/role-manager.js');
const app = getApp();
const config = require('../../../config/index.js');
const api = require('../../../utils/api.js');
const auth = require('../../../utils/auth.js');
const utils = require('../../../utils/utils.js');

Page({
  /**
   * 页面的初始数据
   */
  data: {
    // 当前激活的标签页
    activeTab: 'all',

    // 作业列表数据
    homeworkList: [],

    // 加载状态
    loading: false,
    refreshing: false,
    loadingMore: false,

    // 分页信息
    currentPage: 1,
    pageSize: config.pagination.defaultPageSize,
    hasMore: true,
    total: 0,

    // 用户信息
    userRole: '',
    userInfo: null,

    // 权限状态
    canView: false,
    canSubmit: false,
    canCorrect: false,
    canManage: false,
    canCreate: false,

    // 筛选相关
    showFilterPopup: false,
    selectedSubject: '',
    selectedDifficulty: '',
    subjectOptions: ['全部', '语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治'],
    difficultyOptions: [
      { label: '全部', value: '' },
      { label: '简单', value: 'easy' },
      { label: '中等', value: 'medium' },
      { label: '困难', value: 'hard' }
    ],

    // 搜索关键词
    searchKeyword: '',

    // 错误状态
    error: null
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('作业列表页面加载', options);

    // 执行路由守卫检查
    const guardResult = await routeGuard.checkPageAuth();
    if (!guardResult.success) {
      // 路由守卫失败，页面不应该继续加载
      return;
    }

    // 检查页面访问权限
    const canAccess = await permissionManager.checkPageAccess('pages/homework/list/index');
    if (!canAccess) {
      wx.showModal({
        title: '访问受限',
        content: '您当前的角色无权访问作业列表',
        showCancel: false,
        success: () => {
          wx.switchTab({
            url: '/pages/index/index'
          });
        }
      });
      return;
    }

    // 获取用户信息和权限
    await this.getUserInfo();
    await this.checkUserPermissions();

    // 处理页面参数
    if (options.tab) {
      this.setData({
        activeTab: options.tab
      });
    }

    if (options.subject) {
      this.setData({
        selectedSubject: options.subject
      });
    }

    // 加载作业列表
    this.loadHomeworkList(true);
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    console.log('作业列表页面渲染完成');
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('作业列表页面显示');

    // 检查是否需要刷新数据
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];

    if (currentPage.data.needRefresh) {
      this.loadHomeworkList(true);
      this.setData({
        needRefresh: false
      });
    }
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    console.log('作业列表页面隐藏');
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {
    console.log('作业列表页面卸载');
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    console.log('用户下拉刷新');
    this.onRefresh();
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    console.log('页面触底');
    this.onLoadMore();
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '五好伴学 - 作业列表',
      path: '/pages/homework/list/index',
      imageUrl: config.miniprogram.share.imageUrl
    };
  },

  /**
   * 获取用户信息
   */
  async getUserInfo() {
    try {
      const userInfo = await auth.getUserInfo();
      const userRole = await auth.getUserRole();

      this.setData({
        userInfo,
        userRole
      });

      console.log('用户信息获取成功', { userInfo, userRole });
    } catch (error) {
      console.error('获取用户信息失败', error);

      // 如果获取用户信息失败，跳转到登录页面
      wx.redirectTo({
        url: '/pages/login/index'
      });
    }
  },

  /**
   * 检查用户权限
   */
  async checkUserPermissions() {
    try {
      const canView = await permissionManager.hasPermission('homework.view');
      const canSubmit = await permissionManager.hasPermission('homework.submit');
      const canCorrect = await permissionManager.hasPermission('homework.correct');
      const canManage = await permissionManager.hasPermission('homework.manage');
      const canCreate = await permissionManager.hasPermission('homework.create');

      this.setData({
        canView,
        canSubmit,
        canCorrect,
        canManage,
        canCreate
      });

      console.log('用户权限检查结果', {
        canView, canSubmit, canCorrect, canManage, canCreate
      });

      // 如果连基本查看权限都没有，禁止访问
      if (!canView) {
        wx.showModal({
          title: '权限不足',
          content: '您没有查看作业的权限',
          showCancel: false,
          success: () => {
            wx.switchTab({
              url: '/pages/index/index'
            });
          }
        });
        return false;
      }

      return true;
    } catch (error) {
      console.error('检查用户权限失败', error);
      return false;
    }
  },

  /**
   * 加载作业列表
   */
  async loadHomeworkList(reset = false) {
    if (this.data.loading && !reset) {
      return;
    }

    try {
      // 重置状态
      if (reset) {
        this.setData({
          currentPage: 1,
          homeworkList: [],
          hasMore: true,
          error: null
        });
      }

      this.setData({
        loading: true
      });

      // 构建请求参数
      const params = {
        page: this.data.currentPage,
        pageSize: this.data.pageSize,
        status: this.getStatusFromTab(this.data.activeTab),
        subject: this.data.selectedSubject && this.data.selectedSubject !== '全部'
          ? this.data.selectedSubject : '',
        difficulty: this.data.selectedDifficulty,
        keyword: this.data.searchKeyword
      };

      console.log('加载作业列表请求参数', params);

      // 调用API
      const response = await api.getHomeworkList(params);

      if (response.success) {
        const { list, total, hasMore } = response.data;

        // 更新数据
        const newHomeworkList = reset ? list : [...this.data.homeworkList, ...list];

        this.setData({
          homeworkList: newHomeworkList,
          total,
          hasMore,
          currentPage: this.data.currentPage + (list.length > 0 ? 1 : 0)
        });

        console.log('作业列表加载成功', {
          total: newHomeworkList.length,
          hasMore
        });
      } else {
        throw new Error(response.error?.message || '加载作业列表失败');
      }
    } catch (error) {
      console.error('加载作业列表失败', error);

      this.setData({
        error: error.message
      });

      // 显示错误提示
      wx.showToast({
        title: error.message || '加载失败',
        icon: 'error',
        duration: 2000
      });
    } finally {
      this.setData({
        loading: false,
        refreshing: false,
        loadingMore: false
      });

      // 停止下拉刷新
      wx.stopPullDownRefresh();
    }
  },

  /**
   * 根据标签页获取对应的状态
   */
  getStatusFromTab(tab) {
    const statusMap = {
      'all': '',
      'pending': 'pending',
      'completed': 'completed',
      'overdue': 'overdue'
    };
    return statusMap[tab] || '';
  },

  /**
   * 获取空状态描述
   */
  getEmptyDescription(tab) {
    const descriptions = {
      'all': '还没有作业哦，快去添加吧',
      'pending': '太棒了！没有待完成的作业',
      'completed': '还没有完成过作业，加油哦',
      'overdue': '很好！没有逾期的作业'
    };
    return descriptions[tab] || '暂无数据';
  },

  /**
   * 标签页切换
   */
  onTabChange(e) {
    const { tab } = e.currentTarget.dataset;

    if (tab === this.data.activeTab) {
      return;
    }

    console.log('切换标签页', tab);

    this.setData({
      activeTab: tab
    });

    // 重新加载数据
    this.loadHomeworkList(true);

    // 埋点统计
    if (config.analytics.enabled) {
      wx.reportAnalytics('homework_tab_switch', {
        from_tab: this.data.activeTab,
        to_tab: tab
      });
    }
  },

  /**
   * 下拉刷新
   */
  onRefresh() {
    console.log('下拉刷新');

    this.setData({
      refreshing: true
    });

    this.loadHomeworkList(true);
  },

  /**
   * 加载更多
   */
  onLoadMore() {
    if (!this.data.hasMore || this.data.loadingMore || this.data.loading) {
      return;
    }

    console.log('加载更多');

    this.setData({
      loadingMore: true
    });

    this.loadHomeworkList(false);
  },

  /**
   * 作业卡片点击
   */
  onHomeworkTap(e) {
    const { homework } = e.detail;

    console.log('点击作业', homework);

    // 跳转到作业详情页面
    wx.navigateTo({
      url: `/pages/homework/detail/index?id=${homework.id}`
    });

    // 埋点统计
    if (config.analytics.enabled) {
      wx.reportAnalytics('homework_view', {
        homework_id: homework.id,
        homework_status: homework.status,
        source: 'list'
      });
    }
  },

  /**
   * 作业提交
   */
  async onHomeworkSubmit(e) {
    const { homework } = e.detail;

    console.log('提交作业', homework);

    // 检查提交权限
    const canSubmit = await permissionManager.hasPermission('homework.submit');
    if (!canSubmit) {
      wx.showToast({
        title: '您没有提交作业的权限',
        icon: 'none'
      });
      return;
    }

    // 检查时间限制
    const timeValid = permissionManager.checkTimeRestriction('06:00-23:00');
    if (!timeValid) {
      wx.showToast({
        title: '作业提交时间限制：06:00-23:00',
        icon: 'none'
      });
      return;
    }

    try {
      // 显示加载提示
      wx.showLoading({
        title: '提交中...',
        mask: true
      });

      // 调用提交API
      const response = await api.submitHomework({
        homeworkId: homework.id
      });

      if (response.success) {
        wx.showToast({
          title: '提交成功',
          icon: 'success'
        });

        // 刷新列表
        this.loadHomeworkList(true);

        // 埋点统计
        if (config.analytics.enabled) {
          wx.reportAnalytics('homework_submit', {
            homework_id: homework.id,
            source: 'list'
          });
        }
      } else {
        throw new Error(response.error?.message || '提交失败');
      }
    } catch (error) {
      console.error('提交作业失败', error);

      wx.showToast({
        title: error.message || '提交失败',
        icon: 'error'
      });
    } finally {
      wx.hideLoading();
    }
  },

  /**
   * 创建作业（教师功能）
   */
  async onCreateHomework() {
    console.log('创建作业');

    // 检查创建权限
    const canCreate = await permissionManager.hasPermission('homework.create');
    if (!canCreate) {
      wx.showToast({
        title: '您没有创建作业的权限',
        icon: 'none'
      });
      return;
    }

    // 跳转到作业创建页面
    wx.navigateTo({
      url: '/pages/homework/create/index'
    });

    // 埋点统计
    if (config.analytics.enabled) {
      wx.reportAnalytics('homework_create_click', {
        source: 'list_fab'
      });
    }
  },

  /**
   * 打开筛选弹窗
   */
  onOpenFilter() {
    this.setData({
      showFilterPopup: true
    });
  },

  /**
   * 关闭筛选弹窗
   */
  onCloseFilter() {
    this.setData({
      showFilterPopup: false
    });
  },

  /**
   * 选择科目
   */
  onSubjectSelect(e) {
    const { subject } = e.currentTarget.dataset;

    this.setData({
      selectedSubject: subject
    });
  },

  /**
   * 选择难度
   */
  onDifficultySelect(e) {
    const { difficulty } = e.currentTarget.dataset;

    this.setData({
      selectedDifficulty: difficulty
    });
  },

  /**
   * 重置筛选条件
   */
  onResetFilter() {
    this.setData({
      selectedSubject: '',
      selectedDifficulty: ''
    });
  },

  /**
   * 确认筛选
   */
  onConfirmFilter() {
    console.log('应用筛选条件', {
      subject: this.data.selectedSubject,
      difficulty: this.data.selectedDifficulty
    });

    // 关闭弹窗
    this.setData({
      showFilterPopup: false
    });

    // 重新加载数据
    this.loadHomeworkList(true);

    // 埋点统计
    if (config.analytics.enabled) {
      wx.reportAnalytics('homework_filter', {
        subject: this.data.selectedSubject,
        difficulty: this.data.selectedDifficulty
      });
    }
  },

  /**
   * 搜索作业
   */
  onSearch(e) {
    const keyword = e.detail.value.trim();

    this.setData({
      searchKeyword: keyword
    });

    // 防抖处理
    if (this.searchTimer) {
      clearTimeout(this.searchTimer);
    }

    this.searchTimer = setTimeout(() => {
      console.log('搜索作业', keyword);
      this.loadHomeworkList(true);

      // 埋点统计
      if (config.analytics.enabled) {
        wx.reportAnalytics('homework_search', {
          keyword,
          result_count: this.data.homeworkList.length
        });
      }
    }, 500);
  },

  /**
   * 错误重试
   */
  onRetry() {
    console.log('重试加载');
    this.loadHomeworkList(true);
  }
});
