const api = require('../../api/index.js');

Page({
  data: {
    plans: [],
    loading: false,
    showGenerateModal: false,
    generating: false,
    generateForm: {
      title: '',
    },
    hasEmptyImage: false, // Check if image exists or use default icon
  },

  onLoad() {
    this.fetchPlans();
  },

  onPullDownRefresh() {
    this.fetchPlans().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async fetchPlans() {
    this.setData({ loading: true });
    try {
      const res = await api.revisions.getRevisionPlanList({
        page: 1,
        page_size: 100, // Simple list for now
      });
      
      const plans = (res.items || []).map(item => ({
        ...item,
        created_at_formatted: item.created_at ? item.created_at.substring(0, 10) : '',
        status_text: this.getStatusText(item.status),
      }));

      this.setData({
        plans,
        loading: false,
      });
    } catch (err) {
      console.error(err);
      this.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none',
      });
    }
  },

  getStatusText(status) {
    const map = {
      'generated': '已生成',
      'processing': '生成中',
      'failed': '失败',
    };
    return map[status] || status;
  },

  onGenerateTap() {
    const now = new Date();
    const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    this.setData({
      showGenerateModal: true,
      'generateForm.title': `复习计划 ${dateStr}`,
    });
  },

  closeGenerateModal() {
    this.setData({
      showGenerateModal: false,
    });
  },

  async confirmGenerate() {
    const { title } = this.data.generateForm;
    if (!title) {
      wx.showToast({
        title: '请输入标题',
        icon: 'none',
      });
      return;
    }

    this.setData({ generating: true });
    try {
      await api.revisions.generateRevisionPlan({
        title,
        cycle_type: '7days',
      });
      
      wx.showToast({
        title: '生成任务已提交',
        icon: 'success',
      });
      
      this.closeGenerateModal();
      this.fetchPlans();
    } catch (err) {
      console.error(err);
      wx.showToast({
        title: '生成失败',
        icon: 'none',
      });
    } finally {
      this.setData({ generating: false });
    }
  },

  onPlanTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/revision-detail/index?id=${id}`,
    });
  },
});
