// pages/chat/history/index.js - 问答历史记录页面

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

    // 历史对话列表
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

    // 搜索筛选
    searchKeyword: '',
    filterOptions: {
      subject: 'all', // all, math, chinese, english, physics, chemistry
      timeRange: 'all', // all, today, week, month, custom
      questionType: 'all', // all, homework, concept, method, review, explore
      sortBy: 'time', // time, length, subject
      sortOrder: 'desc', // desc, asc
    },

    // 筛选选项配置
    subjectOptions: [
      { label: '全部学科', value: 'all' },
      { label: '数学', value: 'math' },
      { label: '语文', value: 'chinese' },
      { label: '英语', value: 'english' },
      { label: '物理', value: 'physics' },
      { label: '化学', value: 'chemistry' },
    ],

    timeRangeOptions: [
      { label: '全部时间', value: 'all' },
      { label: '今天', value: 'today' },
      { label: '本周', value: 'week' },
      { label: '本月', value: 'month' },
      { label: '自定义', value: 'custom' },
    ],

    questionTypeOptions: [
      { label: '全部类型', value: 'all' },
      { label: '作业练习', value: 'homework' },
      { label: '概念理解', value: 'concept' },
      { label: '方法技巧', value: 'method' },
      { label: '复习总结', value: 'review' },
      { label: '拓展探索', value: 'explore' },
    ],

    // 统计信息
    statistics: {
      totalQuestions: 0,
      averageLength: 0,
      mostActiveSubject: '',
      todayQuestions: 0,
      weekQuestions: 0,
    },

    // UI状态
    showFilterPopup: false,
    showDatePicker: false,
    datePickerType: 'start',
    customDateRange: {
      startDate: '',
      endDate: '',
    },

    // 选中的对话（用于批量操作）
    selectedItems: [],
    selectionMode: false,

    // 错误状态
    error: null,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('问答历史页面加载', options);

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
      title: '问答历史记录',
      path: '/pages/chat/history/index',
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

      const { currentPage, pageSize, filterOptions, searchKeyword } = this.data;

      // TODO: 调用API获取历史数据
      // const response = await api.getChatHistory({
      //   page: currentPage,
      //   pageSize,
      //   search: searchKeyword,
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
    const subjects = ['math', 'chinese', 'english', 'physics', 'chemistry'];
    const questionTypes = ['homework', 'concept', 'method', 'review', 'explore'];
    const questions = [
      '这道数学题怎么解？',
      '请解释一下牛顿第二定律',
      '如何提高英语口语？',
      '古诗词有什么鉴赏技巧？',
      '化学反应的原理是什么？',
    ];

    const list = [];
    const startIndex = (page - 1) * pageSize;

    for (let i = 0; i < pageSize && i < 50; i++) {
      const index = startIndex + i;
      const subject = subjects[index % subjects.length];
      const questionType = questionTypes[index % questionTypes.length];
      const question = questions[index % questions.length];

      const conversationData = {
        id: `chat_${index + 1}`,
        sessionId: `session_${Math.floor(index / 5) + 1}`,
        subject: subject,
        questionType: questionType,
        question: question,
        answer: `这是对"${question}"的详细回答。AI助手会根据问题类型提供相应的解答内容...`,
        timestamp: Date.now() - index * 60 * 60 * 1000, // 每小时一个问题
        questionLength: question.length,
        answerLength: Math.floor(Math.random() * 200) + 50,
        isBookmarked: Math.random() > 0.8, // 20% 概率被收藏
        tags: [`${subject}`, `${questionType}`],
      };

      list.push(conversationData);
    }

    return {
      list,
      total: 100,
      hasMore: page * pageSize < 100,
    };
  },

  /**
   * 加载统计信息
   */
  async loadStatistics() {
    try {
      // TODO: 调用API获取统计信息
      // const response = await api.getChatStatistics();

      // 模拟数据
      const statistics = {
        totalQuestions: 100,
        averageLength: 25.5,
        mostActiveSubject: '数学',
        todayQuestions: 5,
        weekQuestions: 28,
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
   * 搜索输入
   */
  onSearchInput(e) {
    const { value } = e.detail;
    this.setData({ searchKeyword: value });

    // 防抖搜索
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => {
      this.loadHistoryData(true);
    }, 500);
  },

  /**
   * 清空搜索
   */
  onSearchClear() {
    this.setData({ searchKeyword: '' });
    this.loadHistoryData(true);
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
   * 筛选条件选择
   */
  onFilterSelect(e) {
    const { type, value } = e.currentTarget.dataset;
    const filterOptions = { ...this.data.filterOptions };
    filterOptions[type] = value;

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
        subject: 'all',
        timeRange: 'all',
        questionType: 'all',
        sortBy: 'time',
        sortOrder: 'desc',
      },
    });
  },

  /**
   * 点击历史对话项
   */
  onHistoryItemTap(e) {
    const { item } = e.currentTarget.dataset;

    if (this.data.selectionMode) {
      this.toggleItemSelection(item.id);
    } else {
      // 跳转到对话详情或重新开始对话
      wx.navigateTo({
        url: `/pages/chat/index/index?question=${encodeURIComponent(item.question)}&subject=${item.subject}`,
      });
    }
  },

  /**
   * 长按历史项
   */
  onHistoryItemLongPress(e) {
    const { item } = e.currentTarget.dataset;

    wx.showActionSheet({
      itemList: ['收藏/取消收藏', '删除', '分享', '复制问题'],
      success: res => {
        switch (res.tapIndex) {
          case 0:
            this.toggleBookmark(item.id);
            break;
          case 1:
            this.deleteHistoryItem(item.id);
            break;
          case 2:
            this.shareHistoryItem(item);
            break;
          case 3:
            this.copyQuestion(item.question);
            break;
        }
      },
    });
  },

  /**
   * 切换收藏状态
   */
  async toggleBookmark(itemId) {
    try {
      // TODO: 调用API切换收藏状态
      // await api.toggleChatBookmark(itemId);

      const historyList = this.data.historyList.map(item => {
        if (item.id === itemId) {
          return { ...item, isBookmarked: !item.isBookmarked };
        }
        return item;
      });

      this.setData({ historyList });

      wx.showToast({
        title: '操作成功',
        icon: 'success',
      });
    } catch (error) {
      console.error('切换收藏失败:', error);
      this.showError('操作失败');
    }
  },

  /**
   * 删除历史项
   */
  deleteHistoryItem(itemId) {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条问答记录吗？',
      success: async res => {
        if (res.confirm) {
          try {
            // TODO: 调用API删除记录
            // await api.deleteChatHistory(itemId);

            const historyList = this.data.historyList.filter(item => item.id !== itemId);
            this.setData({ historyList });

            wx.showToast({
              title: '删除成功',
              icon: 'success',
            });
          } catch (error) {
            console.error('删除失败:', error);
            this.showError('删除失败');
          }
        }
      },
    });
  },

  /**
   * 分享历史项
   */
  shareHistoryItem(item) {
    wx.setClipboardData({
      data: `问题：${item.question}\n\n答案：${item.answer}`,
      success: () => {
        wx.showToast({
          title: '已复制到剪贴板',
          icon: 'success',
        });
      },
    });
  },

  /**
   * 复制问题
   */
  copyQuestion(question) {
    wx.setClipboardData({
      data: question,
      success: () => {
        wx.showToast({
          title: '问题已复制',
          icon: 'success',
        });
      },
    });
  },

  /**
   * 切换选择模式
   */
  toggleSelectionMode() {
    this.setData({
      selectionMode: !this.data.selectionMode,
      selectedItems: [],
    });
  },

  /**
   * 切换项目选择状态
   */
  toggleItemSelection(itemId) {
    const selectedItems = [...this.data.selectedItems];
    const index = selectedItems.indexOf(itemId);

    if (index > -1) {
      selectedItems.splice(index, 1);
    } else {
      selectedItems.push(itemId);
    }

    this.setData({ selectedItems });
  },

  /**
   * 批量删除
   */
  batchDelete() {
    if (this.data.selectedItems.length === 0) {
      wx.showToast({
        title: '请选择要删除的项目',
        icon: 'none',
      });
      return;
    }

    wx.showModal({
      title: '批量删除',
      content: `确定要删除${this.data.selectedItems.length}条记录吗？`,
      success: async res => {
        if (res.confirm) {
          try {
            // TODO: 调用API批量删除
            // await api.batchDeleteChatHistory(this.data.selectedItems);

            const historyList = this.data.historyList.filter(
              item => !this.data.selectedItems.includes(item.id),
            );

            this.setData({
              historyList,
              selectedItems: [],
              selectionMode: false,
            });

            wx.showToast({
              title: '删除成功',
              icon: 'success',
            });
          } catch (error) {
            console.error('批量删除失败:', error);
            this.showError('删除失败');
          }
        }
      },
    });
  },

  /**
   * 导出历史记录
   */
  exportHistory() {
    wx.showModal({
      title: '导出功能',
      content: '导出功能正在开发中，敬请期待',
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
  formatTime(timestamp) {
    return utils.formatTime(new Date(timestamp));
  },

  /**
   * 获取学科名称
   */
  getSubjectName(subjectId) {
    const subject = this.data.subjectOptions.find(s => s.value === subjectId);
    return subject ? subject.label : subjectId;
  },

  /**
   * 获取问题类型名称
   */
  getQuestionTypeName(typeId) {
    const type = this.data.questionTypeOptions.find(t => t.value === typeId);
    return type ? type.label : typeId;
  },
});
