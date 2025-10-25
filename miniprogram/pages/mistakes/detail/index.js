// pages/mistakes/detail/index.js - 错题详情页面
const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../../api/mistakes.js');

const pageObject = {
  data: {
    mistakeId: '',
    mistakeDetail: null,
    loading: false,
    mode: 'view', // view | review
  },

  async onLoad(options) {
    console.log('错题详情页面加载', options);

    if (options.id) {
      this.setData({
        mistakeId: options.id,
        mode: options.mode || 'view',
      });

      await this.loadMistakeDetail();
    }
  },

  async loadMistakeDetail() {
    try {
      this.setData({ loading: true });

      const response = await mistakesApi.getMistakeDetail(this.data.mistakeId);

      // 🐞 后端API直接返回MistakeDetailResponse对象，不是{success, data}格式
      if (response && response.id) {
        this.setData({
          mistakeDetail: response, // 🛠️ 直接使用response
        });
      } else {
        throw new Error('加载失败：无效的响应数据');
      }
    } catch (error) {
      console.error('加载错题详情失败', error);
      wx.showToast({
        title: error.message || '加载失败',
        icon: 'error',
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  getMasteryStatusTag(status) {
    const statusMap = {
      not_mastered: { type: 'danger', text: '未掌握' },
      reviewing: { type: 'warning', text: '复习中' },
      mastered: { type: 'success', text: '已掌握' },
    };
    return statusMap[status] || { type: 'default', text: '未知' };
  },

  getDifficultyText(level) {
    const difficultyMap = {
      1: '简单',
      2: '中等',
      3: '困难',
    };
    return difficultyMap[level] || '未知';
  },

  async onDelete() {
    const res = await wx.showModal({
      title: '确认删除',
      content: '确定要删除这道错题吗？',
      confirmText: '删除',
      confirmColor: '#f5222d',
    });

    if (!res.confirm) return;

    try {
      wx.showLoading({ title: '删除中...', mask: true });

      const response = await mistakesApi.deleteMistake(this.data.mistakeId);

      // 🛠️ 删除API返回SuccessResponse: {success: true, message: "..."}
      if (response && response.success !== false) {
        wx.showToast({
          title: '删除成功',
          icon: 'success',
        });

        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        throw new Error(response.message || '删除失败');
      }
    } catch (error) {
      console.error('删除错题失败', error);
      wx.showToast({
        title: error.message || '删除失败',
        icon: 'error',
      });
    } finally {
      wx.hideLoading();
    }
  },

  onStartReview() {
    // 开始复习模式
    wx.navigateTo({
      url: `/pages/mistakes/detail/index?id=${this.data.mistakeId}&mode=review`,
    });
  },
};

Page(createGuardedPage(pageObject, 'pages/mistakes/detail/index'));
