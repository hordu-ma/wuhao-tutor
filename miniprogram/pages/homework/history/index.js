// pages/homework/history/index.js - 作业历史记录页面

const { authManager } = require('../../../utils/auth.js');
const api = require('../../../utils/api.js');
const utils = require('../../../utils/utils.js');

Page({
  /**
   * 页面的初始数据
   */
  data: {
    // 用户信息
    userInfo: null,
    userRole: '',

    // 历史记录列表
    historyList: [],

    // 分页信息
    currentPage: 1,
    pageSize: 20,
    hasMore: true,
    total: 0,

    // 加载状态
    loading: true,
    refreshing: false,
    loadingMore: false,

    // 筛选条件
    filterOptions: {
      timeRange: 'all', // all, thisWeek, thisMonth, lastMonth, custom
      subject: 'all',
      status: 'all', // all, submitted, corrected, excellent
      sortBy: 'time', // time, score, subject
      sortOrder: 'desc', // desc, asc
    },

    // 筛选选项
    timeRangeOptions: [
      { label: '全部时间', value: 'all' },
      { label: '本周', value: 'thisWeek' },
      { label: '本月', value: 'thisMonth' },
      { label: '上月', value: 'lastMonth' },
      { label: '自定义', value: 'custom' },
    ],

    subjectOptions: [
      '全部科目',
      '语文',
      '数学',
      '英语',
      '物理',
      '化学',
      '生物',
      '历史',
      '地理',
      '政治',
    ],

    statusOptions: [
      { label: '全部状态', value: 'all' },
      { label: '已提交', value: 'submitted' },
      { label: '已批改', value: 'corrected' },
      { label: '优秀作业', value: 'excellent' },
    ],

    // 自定义时间
    customDateRange: {
      startDate: '',
      endDate: '',
    },

    // 统计信息
    statistics: {
      totalCount: 0,
      correctedCount: 0,
      averageScore: 0,
      excellentCount: 0,
    },

    // 弹窗状态
    showFilterPopup: false,
    showDatePicker: false,
    datePickerType: 'start', // start, end

    // 查看模式
    viewMode: 'list', // list, chart

    // 错误状态
    error: null,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('作业历史页面加载', options);

    try {
      await this.initUserInfo();
      await this.loadHistoryData(true);
      await this.loadStatistics();
    } catch (error) {
      console.error('页面初始化失败:', error);
      this.showError('页面加载失败');
    }
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    this.loadMoreData();
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '作业历史记录',
      path: '/pages/homework/history/index',
    };
  },

  /**
   * 初始化用户信息
   */
  async initUserInfo() {
    try {
      const userInfo = await authManager.getUserInfo();
      const userRole = await authManager.getUserRole();

      this.setData({ userInfo, userRole });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 加载历史数据
   */
  async loadHistoryData(reset = false) {
    try {
      if (reset) {
        this.setData({
          loading: true,
          currentPage: 1,
          historyList: [],
          error: null,
        });
      } else {
        this.setData({ loadingMore: true });
      }

      const { currentPage, pageSize, filterOptions } = this.data;

      // TODO: 调用API获取历史数据
      // const response = await api.getHomeworkHistory({
      //   page: currentPage,
      //   pageSize,
      //   ...filterOptions
      // });

      // 模拟数据
      const mockData = this.generateMockHistoryData(currentPage, pageSize);

      if (reset) {
        this.setData({
          historyList: mockData.list,
          total: mockData.total,
          hasMore: mockData.hasMore,
        });
      } else {
        this.setData({
          historyList: [...this.data.historyList, ...mockData.list],
          hasMore: mockData.hasMore,
        });
      }

      this.setData({ currentPage: currentPage + 1 });
    } catch (error) {
      console.error('加载历史数据失败:', error);
      this.setData({ error: '加载失败，请重试' });
    } finally {
      this.setData({
        loading: false,
        refreshing: false,
        loadingMore: false,
      });
    }
  },

  /**
   * 生成模拟历史数据
   */
  generateMockHistoryData(page, pageSize) {
    const subjects = ['数学', '语文', '英语', '物理', '化学'];
    const statuses = ['submitted', 'corrected'];
    const grades = ['A+', 'A', 'B+', 'B', 'C+', 'C'];

    const list = [];
    const startIndex = (page - 1) * pageSize;

    for (let i = 0; i < pageSize && i < 20; i++) {
      const index = startIndex + i;
      const subject = subjects[index % subjects.length];
      const status = statuses[index % statuses.length];
      const score = Math.floor(Math.random() * 40) + 60; // 60-100分
      const totalScore = 100;
      const grade = grades[Math.floor(score / 15)];

      list.push({
        id: `history_${index + 1}`,
        homeworkId: `hw_${index + 1}`,
        title: `${subject}第${index + 1}章练习`,
        subject: subject,
        submittedAt: new Date(Date.now() - index * 24 * 60 * 60 * 1000).toISOString(),
        correctedAt:
          status === 'corrected'
            ? new Date(Date.now() - (index - 1) * 24 * 60 * 60 * 1000).toISOString()
            : null,
        status: status,
        score: status === 'corrected' ? score : null,
        totalScore: totalScore,
        grade: status === 'corrected' ? grade : null,
        teacherName: '李老师',
        isExcellent: score >= 90,
        comment: status === 'corrected' ? '完成得很好，继续保持！' : null,
      });
    }

    return {
      list,
      total: 50,
      hasMore: page * pageSize < 50,
    };
  },

  /**
   * 加载统计信息
   */
  async loadStatistics() {
    try {
      // TODO: 调用API获取统计信息
      // const response = await api.getHomeworkStatistics();

      // 模拟数据
      const statistics = {
        totalCount: 50,
        correctedCount: 45,
        averageScore: 85.5,
        excellentCount: 12,
      };

      this.setData({ statistics });
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  },

  /**
   * 刷新数据
   */
  async refreshData() {
    this.setData({ refreshing: true });
    await Promise.all([this.loadHistoryData(true), this.loadStatistics()]);
  },

  /**
   * 加载更多数据
   */
  loadMoreData() {
    if (!this.data.hasMore || this.data.loadingMore) {
      return;
    }
    this.loadHistoryData(false);
  },

  /**
   * 切换查看模式
   */
  onViewModeChange(e) {
    const { mode } = e.currentTarget.dataset;
    this.setData({ viewMode: mode });
  },

  /**
   * 显示筛选弹窗
   */
  onShowFilter() {
    this.setData({ showFilterPopup: true });
  },

  /**
   * 关闭筛选弹窗
   */
  onCloseFilter() {
    this.setData({ showFilterPopup: false });
  },

  /**
   * 时间范围选择
   */
  onTimeRangeSelect(e) {
    const { value } = e.currentTarget.dataset;
    const filterOptions = { ...this.data.filterOptions };
    filterOptions.timeRange = value;

    this.setData({ filterOptions });

    if (value === 'custom') {
      this.setData({ showDatePicker: true, datePickerType: 'start' });
    }
  },

  /**
   * 科目选择
   */
  onSubjectSelect(e) {
    const { subject } = e.currentTarget.dataset;
    const filterOptions = { ...this.data.filterOptions };
    filterOptions.subject = subject === '全部科目' ? 'all' : subject;

    this.setData({ filterOptions });
  },

  /**
   * 状态选择
   */
  onStatusSelect(e) {
    const { value } = e.currentTarget.dataset;
    const filterOptions = { ...this.data.filterOptions };
    filterOptions.status = value;

    this.setData({ filterOptions });
  },

  /**
   * 排序方式选择
   */
  onSortSelect(e) {
    const { sortBy, sortOrder } = e.currentTarget.dataset;
    const filterOptions = { ...this.data.filterOptions };

    if (sortBy) filterOptions.sortBy = sortBy;
    if (sortOrder) filterOptions.sortOrder = sortOrder;

    this.setData({ filterOptions });
  },

  /**
   * 应用筛选
   */
  onApplyFilter() {
    this.setData({ showFilterPopup: false });
    this.loadHistoryData(true);
  },

  /**
   * 重置筛选
   */
  onResetFilter() {
    this.setData({
      filterOptions: {
        timeRange: 'all',
        subject: 'all',
        status: 'all',
        sortBy: 'time',
        sortOrder: 'desc',
      },
    });
  },

  /**
   * 日期选择
   */
  onDateConfirm(e) {
    const { detail } = e;
    const { datePickerType, customDateRange } = this.data;

    if (datePickerType === 'start') {
      customDateRange.startDate = detail;
      this.setData({
        customDateRange,
        showDatePicker: true,
        datePickerType: 'end',
      });
    } else {
      customDateRange.endDate = detail;
      this.setData({
        customDateRange,
        showDatePicker: false,
      });
    }
  },

  /**
   * 点击历史记录项
   */
  onHistoryItemTap(e) {
    const { item } = e.currentTarget.dataset;

    wx.navigateTo({
      url: `/pages/homework/detail/index?id=${item.homeworkId}`,
    });
  },

  /**
   * 查看统计详情
   */
  onViewStatistics() {
    wx.navigateTo({
      url: '/pages/homework/statistics/index',
    });
  },

  /**
   * 导出历史记录
   */
  onExportHistory() {
    wx.showModal({
      title: '导出功能',
      content: '该功能即将上线，敬请期待',
      showCancel: false,
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
   * 格式化时间
   */
  formatTime(timeString) {
    return utils.formatTime(new Date(timeString));
  },
});
