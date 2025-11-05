// pages/knowledge-graph/index.js - 知识图谱页面
const { createGuardedPage } = require('../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../api/mistakes.js');

const pageObject = {
  data: {
    // 当前选择的科目
    selectedSubject: '数学',
    subjectOptions: ['数学', '语文', '英语', '物理', '化学', '生物', '历史', '地理', '政治'],

    // 加载状态
    loading: false,
    snapshotLoading: false,
    weakChainsLoading: false,

    // 知识图谱快照数据
    snapshot: null,

    // 薄弱知识链
    weakChains: [],

    // 错误状态
    error: null,
  },

  async onLoad(options) {
    console.log('知识图谱页面加载', options);

    if (options.subject) {
      this.setData({
        selectedSubject: options.subject,
      });
    }

    // 加载数据
    await this.loadData();
  },

  onShow() {
    console.log('知识图谱页面显示');
  },

  onPullDownRefresh() {
    this.loadData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 加载所有数据
   */
  async loadData() {
    await Promise.all([this.loadSnapshot(), this.loadWeakChains()]);
  },

  /**
   * 加载知识图谱快照
   */
  async loadSnapshot() {
    if (!this.data.selectedSubject) return;

    try {
      this.setData({ snapshotLoading: true, error: null });

      const response = await mistakesApi.getKnowledgeGraphSnapshot({
        subject: this.data.selectedSubject,
      });

      // 判断响应是否成功：兼容多种响应格式
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response !== null && response !== undefined;

      if (isSuccess) {
        // 兼容两种响应格式
        const snapshot = isStandardFormat ? response.data || response : response;

        this.setData({
          snapshot,
          snapshotLoading: false,
        });
      }
      // 如果响应异常，错误会在 catch 中处理
    } catch (error) {
      console.error('加载知识图谱快照失败', error);
      const errorMessage = error.message || '加载失败,请稍后重试';
      this.setData({
        error: errorMessage,
        snapshotLoading: false,
        snapshot: null,
      });
      // 只在非空数据错误时提示用户
      if (error.status !== 404) {
        wx.showToast({
          title: errorMessage,
          icon: 'none',
          duration: 2000,
        });
      }
    }
  },

  /**
   * 加载薄弱知识链
   */
  async loadWeakChains() {
    if (!this.data.selectedSubject) return;

    try {
      this.setData({ weakChainsLoading: true });

      const response = await mistakesApi.getWeakKnowledgeChains({
        subject: this.data.selectedSubject,
        limit: 5,
      });

      // 判断响应是否成功：兼容多种响应格式
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response !== null && response !== undefined;

      if (isSuccess) {
        // 兼容两种响应格式
        const responseData = isStandardFormat ? response.data || response : response;
        const weakChains = Array.isArray(responseData) ? responseData : responseData.data || [];

        this.setData({
          weakChains,
          weakChainsLoading: false,
        });
      }
      // 如果响应异常，错误会在 catch 中处理
    } catch (error) {
      console.error('加载薄弱知识链失败', error);
      this.setData({
        weakChainsLoading: false,
        weakChains: [],
      });
      // 静默处理错误,不影响主要数据展示
      if (error.status && error.status !== 404) {
        console.warn('获取薄弱知识链失败:', error.message);
      }
    }
  },

  /**
   * 切换科目
   */
  onSubjectChange(e) {
    const subject = e.detail;

    this.setData({
      selectedSubject: subject,
    });

    this.loadData();
  },

  /**
   * 查看知识点详情
   */
  onKnowledgePointTap(e) {
    const { knowledgePoint } = e.currentTarget.dataset;

    if (!knowledgePoint) return;

    // 跳转到错题列表，筛选该知识点
    wx.navigateTo({
      url: `/pages/mistakes/list/index?subject=${this.data.selectedSubject}&knowledge_point=${encodeURIComponent(knowledgePoint)}`,
    });
  },

  /**
   * 查看复习推荐
   */
  onViewRecommendations() {
    wx.navigateTo({
      url: `/pages/review-recommendations/index?subject=${this.data.selectedSubject}`,
    });
  },

  /**
   * 获取掌握度等级
   */
  getMasteryLevel(level) {
    if (level >= 0.7) return { text: '已掌握', type: 'success' };
    if (level >= 0.4) return { text: '学习中', type: 'warning' };
    return { text: '待加强', type: 'danger' };
  },
};

Page(createGuardedPage(pageObject, 'pages/knowledge-graph/index'));
