// pages/mistakes/detail/index.js - 错题详情页面
const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../../api/mistakes.js');

const pageObject = {
  data: {
    mistakeId: '',
    mistakeDetail: null,
    knowledgeAnalysis: null, // 知识点分析数据
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
      // 加载知识点分析
      await this.loadKnowledgeAnalysis();
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

      // 🔧 检查是否是404错误（资源不存在）
      const isNotFound =
        error.message?.includes('不存在') ||
        error.message?.includes('404') ||
        error.statusCode === 404;

      if (isNotFound) {
        // 错题已被删除，提示后返回列表页
        wx.showModal({
          title: '提示',
          content: '该错题已被删除',
          showCancel: false,
          success: res => {
            if (res.confirm) {
              // 标记需要刷新列表
              const pages = getCurrentPages();
              if (pages.length >= 2) {
                const prevPage = pages[pages.length - 2];
                if (prevPage.route === 'pages/mistakes/list/index') {
                  prevPage.setData({ needRefresh: true });
                }
              }
              // 返回上一页
              wx.navigateBack();
            }
          },
        });
      } else {
        // 其他错误，只显示提示
        wx.showToast({
          title: error.message || '加载失败',
          icon: 'error',
        });
      }
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 加载知识点分析
   */
  async loadKnowledgeAnalysis() {
    try {
      const response = await mistakesApi.getMistakeKnowledgePoints(this.data.mistakeId);

      if (response && response.knowledge_points) {
        this.setData({
          knowledgeAnalysis: response,
        });
        console.log('知识点分析数据:', response);
      }
    } catch (error) {
      console.error('加载知识点分析失败', error);
      // 静默失败，不影响主要功能
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

      // 判断响应是否成功：检查状态码 200-299
      const isSuccess = response && response.statusCode >= 200 && response.statusCode < 300;

      if (isSuccess) {
        wx.showToast({
          title: '删除成功',
          icon: 'success',
        });

        // 🔧 标记列表页需要刷新
        const pages = getCurrentPages();
        if (pages.length >= 2) {
          const prevPage = pages[pages.length - 2];
          if (prevPage.route === 'pages/mistakes/list/index') {
            prevPage.setData({ needRefresh: true });
          }
        }

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

  async onStartReview() {
    // 开始三阶段复习
    const mistakeId = this.data.mistakeId;

    if (!mistakeId) {
      wx.showToast({
        title: '错题ID无效',
        icon: 'none',
      });
      return;
    }

    console.log('[详情页] 开始复习，错题ID:', mistakeId);

    try {
      wx.showLoading({
        title: '准备复习中...',
        mask: true,
      });

      // 调用后端 API 创建复习会话
      const sessionData = await mistakesApi.startReviewSession(mistakeId);

      console.log('[详情页] 复习会话创建成功:', sessionData);

      wx.hideLoading();

      // 跳转到复习页面
      wx.navigateTo({
        url: `/pages/mistakes/review/index?session_id=${sessionData.session_id}&mistake_id=${mistakeId}`,
        fail: err => {
          console.error('[详情页] 跳转复习页面失败:', err);
          wx.showToast({
            title: '跳转失败',
            icon: 'none',
          });
        },
      });
    } catch (error) {
      console.error('[详情页] 启动复习失败:', error);
      wx.hideLoading();

      wx.showToast({
        title: error.message || '启动复习失败',
        icon: 'none',
        duration: 2000,
      });
    }
  },

  onPreviewImage(e) {
    const url = e.currentTarget.dataset.url;
    const urls = e.currentTarget.dataset.urls || [url];
    wx.previewImage({
      current: url,
      urls: urls,
    });
  },
};

Page(createGuardedPage(pageObject, 'pages/mistakes/detail/index'));
