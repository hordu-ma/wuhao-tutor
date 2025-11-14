// pages/review-recommendations/index.js - 智能复习推荐页面
const { createGuardedPage } = require('../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../api/mistakes.js');

const pageObject = {
  data: {
    selectedSubject: '数学',
    subjectOptions: ['数学', '语文', '英语', '物理', '化学', '生物', '历史', '地理', '政治'],

    loading: false,
    recommendations: [],
    error: null,
  },

  /**
   * 中文学科名称转英文枚举
   * @param {string} chineseSubject - 中文学科名（如"数学"）
   * @returns {string} 英文学科枚举（如"math"）
   */
  convertSubjectToEnglish(chineseSubject) {
    const mapping = {
      数学: 'math',
      语文: 'chinese',
      英语: 'english',
      物理: 'physics',
      化学: 'chemistry',
      生物: 'biology',
      历史: 'history',
      地理: 'geography',
      政治: 'politics',
    };
    return mapping[chineseSubject] || 'math';
  },

  async onLoad(options) {
    console.log('复习推荐页面加载', options);

    if (options.subject) {
      this.setData({
        selectedSubject: options.subject,
      });
    }

    await this.loadRecommendations();
  },

  onPullDownRefresh() {
    this.loadRecommendations().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadRecommendations() {
    if (!this.data.selectedSubject) return;

    try {
      this.setData({ loading: true, error: null });

      // 🆕 转换中文学科名为英文枚举
      const subjectEn = this.convertSubjectToEnglish(this.data.selectedSubject);
      console.log('复习推荐学科转换:', this.data.selectedSubject, '→', subjectEn);

      const response = await mistakesApi.getReviewRecommendations({
        subject: subjectEn, // 使用英文学科名
        limit: 10,
      });

      console.log('复习推荐API响应:', response);

      // 判断响应是否成功：兼容多种响应格式
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response !== null && response !== undefined;

      if (isSuccess) {
        // 兼容两种响应格式
        const responseData = isStandardFormat ? response.data || response : response;
        const recommendations = Array.isArray(responseData)
          ? responseData
          : responseData.data || [];

        console.log('✅ 复习推荐数据:', recommendations.length, '条');

        this.setData({
          recommendations,
          loading: false,
        });
      }
      // 如果响应异常，保持空列表状态，错误会在 catch 中处理
    } catch (error) {
      console.error('加载复习推荐失败', error);

      // 404 表示没有推荐数据
      if (error.statusCode === 404 || error.status === 404) {
        this.setData({
          error: '暂无复习推荐',
          loading: false,
          recommendations: [],
        });
        return;
      }

      const errorMessage = error.message || '加载失败,请稍后重试';
      this.setData({
        error: errorMessage,
        loading: false,
        recommendations: [],
      });

      wx.showToast({
        title: errorMessage,
        icon: 'none',
        duration: 2000,
      });
    }
  },

  onSubjectChange(e) {
    const subject = e.detail;

    this.setData({
      selectedSubject: subject,
    });

    this.loadRecommendations();
  },

  onKnowledgePointTap(e) {
    const { knowledgePoint } = e.currentTarget.dataset;

    if (!knowledgePoint) return;

    wx.navigateTo({
      url: `/pages/mistakes/list/index?subject=${this.data.selectedSubject}&knowledge_point=${encodeURIComponent(knowledgePoint)}`,
    });
  },

  getPriorityLevel(priority) {
    if (priority >= 0.7) return { text: '高优先级', type: 'danger', color: '#f5222d' };
    if (priority >= 0.4) return { text: '中优先级', type: 'warning', color: '#faad14' };
    return { text: '低优先级', type: 'default', color: '#999999' };
  },

  /**
   * 去学习问答
   */
  goToLearning() {
    wx.switchTab({
      url: '/pages/learning/index',
    });
  },

  /**
   * 查看知识图谱
   */
  goToKnowledgeGraph() {
    wx.navigateTo({
      url: `/subpackages/charts/pages/knowledge-graph/index?subject=${this.data.selectedSubject}`,
    });
  },
};

Page(createGuardedPage(pageObject, 'pages/review-recommendations/index'));
