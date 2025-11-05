// pages/mistakes/today-review/index.js
const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../../api/mistakes.js');

const pageObject = {
  data: {
    reviewList: [],
    loading: false,
    totalCount: 0,
    completedCount: 0,
  },

  onLoad() {
    this.loadTodayReview();
  },

  onShow() {
    // 从详情页返回时刷新
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];

    if (currentPage.data.needRefresh) {
      this.loadTodayReview();
      this.setData({ needRefresh: false });
    }
  },

  async loadTodayReview() {
    try {
      this.setData({ loading: true });

      const response = await mistakesApi.getTodayReview();

      // 判断响应是否成功：兼容多种响应格式
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response && response.items !== undefined;

      if (isSuccess) {
        // 兼容两种响应格式
        const responseData = isStandardFormat ? response.data || response : response;
        const items = responseData.items || [];

        this.setData({
          reviewList: items,
          totalCount: items.length,
          completedCount: 0,
        });
      }
      // 如果响应异常，错误会在 catch 中处理
    } catch (error) {
      console.error('加载今日复习失败', error);
      wx.showToast({
        title: error.message || '加载失败',
        icon: 'error',
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  onReviewTap(e) {
    const { mistake } = e.detail;

    // 跳转到错题详情（复习模式）
    wx.navigateTo({
      url: `/pages/mistakes/detail/index?id=${mistake.id}&mode=review`,
    });
  },

  onStartBatchReview() {
    if (!this.data.reviewList.length) {
      return;
    }

    // 跳转到第一道题开始复习
    const firstMistake = this.data.reviewList[0];
    wx.navigateTo({
      url: `/pages/mistakes/detail/index?id=${firstMistake.id}&mode=review&batch=true`,
    });
  },
};

Page(createGuardedPage(pageObject, 'pages/mistakes/today-review/index'));
