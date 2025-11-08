// pages/mistakes/list/index.js - 错题列表页面
const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const config = require('../../../config/index.js');
const mistakesApi = require('../../../api/mistakes.js');
const auth = require('../../../utils/auth.js');

const pageObject = {
  /**
   * 页面的初始数据
   */
  data: {
    // 当前激活的标签页
    activeTab: 'all',

    // 错题列表数据
    mistakesList: [],

    // 加载状态
    loading: false,
    refreshing: false,
    loadingMore: false,

    // 分页信息
    currentPage: 1,
    pageSize: config.pagination?.defaultPageSize || 20,
    hasMore: true,
    total: 0,

    // 用户信息
    userRole: '',
    userInfo: null,

    // 筛选相关
    showFilterPopup: false,
    showSearch: false,
    selectedSubject: '',
    selectedDifficulty: '',
    subjectOptions: [
      '全部',
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
    difficultyOptions: [
      { label: '全部', value: '' },
      { label: '简单', value: 1 },
      { label: '中等', value: 2 },
      { label: '困难', value: 3 },
    ],

    // 🎯 智能筛选 - 错题类型
    selectedCategory: '',
    categoryOptions: [
      { label: '全部', value: '' },
      { label: '不会做的题', value: 'empty_question' },
      { label: '答错的题', value: 'wrong_answer' },
      { label: '有难度的题', value: 'hard_question' },
    ],

    // 🎯 智能筛选 - 来源
    selectedSource: '',
    sourceOptions: [
      { label: '全部来源', value: '' },
      { label: '学习问答', value: 'learning' },
      { label: '手动添加', value: 'manual' },
    ],

    // 搜索关键词
    searchKeyword: '',

    // 知识点筛选
    selectedKnowledgePoint: '',
    knowledgePointOptions: [], // 从 API 加载

    // 错误状态
    error: null,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('错题列表页面加载', options);

    // 处理页面参数
    if (options.tab) {
      this.setData({
        activeTab: options.tab,
      });
    }

    if (options.subject) {
      this.setData({
        selectedSubject: options.subject,
      });
    }

    // 🔧 处理知识点筛选参数
    if (options.knowledge_point) {
      const knowledgePoint = decodeURIComponent(options.knowledge_point);
      this.setData({
        selectedKnowledgePoint: knowledgePoint,
      });
    }

    // 加载错题列表
    this.loadMistakesList(true);

    // 加载知识点列表（如果有科目）
    if (this.data.selectedSubject && this.data.selectedSubject !== '全部') {
      this.loadKnowledgePoints();
    }
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('错题列表页面显示');

    // 检查是否需要刷新数据
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];

    if (currentPage.data.needRefresh) {
      this.loadMistakesList(true);
      this.setData({
        needRefresh: false,
      });
    }
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
      title: '五好伴学 - 错题手册',
      path: '/pages/mistakes/list/index',
      imageUrl: config.miniprogram?.share?.imageUrl,
    };
  },

  /**
   * 加载知识点列表
   */
  async loadKnowledgePoints() {
    const { selectedSubject } = this.data;

    if (!selectedSubject || selectedSubject === '全部') {
      this.setData({
        knowledgePointOptions: [],
        selectedKnowledgePoint: '',
      });
      return;
    }

    try {
      const response = await mistakesApi.getKnowledgePointList({
        subject: selectedSubject,
        min_count: 1,
      });

      console.log('知识点列表API响应', response);

      // 判断响应是否成功：兼容多种响应格式
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response !== null && response !== undefined;

      if (isSuccess) {
        // 兼容两种响应格式
        const responseData = isStandardFormat ? response.data || response : response;

        let knowledgePoints = [];

        if (responseData.knowledge_points && Array.isArray(responseData.knowledge_points)) {
          knowledgePoints = responseData.knowledge_points;
        } else if (Array.isArray(responseData)) {
          knowledgePoints = responseData;
        }

        // 添加"全部"选项
        const options = [{ name: '全部知识点', mistake_count: 0 }, ...knowledgePoints];

        this.setData({
          knowledgePointOptions: options,
        });
      }
    } catch (error) {
      console.error('加载知识点列表失败', error);
      // 发生错误时重置选项
      this.setData({
        knowledgePointOptions: [],
      });
    }
  },

  /**
   * 加载错题列表
   */
  async loadMistakesList(reset = false) {
    if (this.data.loading && !reset) {
      return;
    }

    try {
      // 重置状态
      if (reset) {
        this.setData({
          currentPage: 1,
          mistakesList: [],
          hasMore: true,
          error: null,
        });
      }

      this.setData({
        loading: true,
      });

      // 构建请求参数
      const params = {
        page: this.data.currentPage,
        page_size: this.data.pageSize,
        mastery_status: this.getStatusFromTab(this.data.activeTab),
        subject:
          this.data.selectedSubject && this.data.selectedSubject !== '全部'
            ? this.data.selectedSubject
            : undefined,
        difficulty_level: this.data.selectedDifficulty || undefined,
        keyword: this.data.searchKeyword || undefined,
        // 🎯 智能筛选参数
        category: this.data.selectedCategory || undefined,
        source: this.data.selectedSource || undefined,
        // 知识点筛选
        knowledge_point:
          this.data.selectedKnowledgePoint && this.data.selectedKnowledgePoint !== '全部知识点'
            ? this.data.selectedKnowledgePoint
            : undefined,
      };

      console.log('加载错题列表请求参数', params);

      // 调用API
      const response = await mistakesApi.getMistakeList(params);

      console.log('错题列表API响应', response);
      console.log('📊 [Debug] response.statusCode:', response?.statusCode);
      console.log('📊 [Debug] response.data:', response?.data);

      // 判断响应是否成功：兼容多种响应格式
      // 格式1: { data: {...}, statusCode: 200 } - API 客户端标准格式
      // 格式2: { items: [...], total: N } - 直接返回的数据
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response && response.items !== undefined; // 如果有 items 字段，认为是成功的

      console.log('📊 [Debug] isStandardFormat:', isStandardFormat);
      console.log('📊 [Debug] isSuccess:', isSuccess);

      if (isSuccess) {
        // 兼容两种响应格式
        const responseData = isStandardFormat ? response.data || response : response;
        console.log('📊 [Debug] responseData:', responseData);
        console.log('📊 [Debug] responseData.items:', responseData.items);

        const items = responseData.items || [];
        const total = responseData.total || 0;
        const page = responseData.page || this.data.currentPage;
        const page_size = responseData.page_size || this.data.pageSize;

        console.log('📊 [Debug] 提取的数据:', { items: items.length, total, page, page_size });

        const hasMore = items.length >= page_size;

        // 更新数据
        const newMistakesList = reset ? items : [...this.data.mistakesList, ...items];

        this.setData({
          mistakesList: newMistakesList,
          total,
          hasMore,
          currentPage: this.data.currentPage + (items.length > 0 ? 1 : 0),
        });

        console.log('错题列表加载成功', {
          total: newMistakesList.length,
          hasMore,
        });
      }
      // 如果 isSuccess 为 false，说明响应异常，但不抛出错误
      // 让数据保持为空列表状态
    } catch (error) {
      console.error('加载错题列表失败', error);

      const errorMessage = error.message || error.errMsg || '加载失败';

      this.setData({
        error: errorMessage,
      });

      // 显示错误提示
      wx.showToast({
        title: errorMessage,
        icon: 'none',
        duration: 2000,
      });
    } finally {
      this.setData({
        loading: false,
        refreshing: false,
        loadingMore: false,
      });

      // 停止下拉刷新
      wx.stopPullDownRefresh();
    }
  },

  /**
   * 根据标签页获取对应的掌握状态
   */
  getStatusFromTab(tab) {
    const statusMap = {
      all: undefined,
      not_mastered: 'not_mastered',
      reviewing: 'reviewing',
      mastered: 'mastered',
    };
    return statusMap[tab];
  },

  /**
   * 获取空状态描述
   */
  getEmptyDescription(tab) {
    const descriptions = {
      all: '还没有错题，继续加油哦',
      not_mastered: '太棒了！没有未掌握的错题',
      reviewing: '暂无正在复习的错题',
      mastered: '还没有完全掌握的错题，继续努力',
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
      activeTab: tab,
    });

    // 重新加载数据
    this.loadMistakesList(true);
  },

  /**
   * 下拉刷新
   */
  onRefresh() {
    console.log('下拉刷新');

    this.setData({
      refreshing: true,
    });

    this.loadMistakesList(true);
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
      loadingMore: true,
    });

    this.loadMistakesList(false);
  },

  /**
   * 查看错题详情（来自"查看详情"按钮）
   */
  onMistakeDetail(e) {
    // ✅ 防御性编程：检查事件数据
    if (!e || !e.detail) {
      console.error('[列表页] 查看详情事件无效', e);
      return;
    }

    const { mistake } = e.detail;

    if (!mistake || !mistake.id) {
      console.error('[列表页] 错题数据无效', {
        event: e,
        detail: e.detail,
        mistake: mistake,
      });
      wx.showToast({
        title: '错题数据加载失败',
        icon: 'error',
      });
      return;
    }

    console.log('[列表页] 查看错题详情', mistake);

    // 跳转到错题详情页面
    wx.navigateTo({
      url: `/pages/mistakes/detail/index?id=${mistake.id}`,
    });
  },

  /**
   * 删除错题
   */
  async onMistakeDelete(e) {
    // ✅ 防御性编程
    if (!e || !e.detail || !e.detail.mistake) {
      console.error('删除错题事件无效', e);
      return;
    }

    const { mistake } = e.detail;

    console.log('删除错题', mistake);

    // 确认删除
    const res = await wx.showModal({
      title: '确认删除',
      content: '确定要删除这道错题吗？',
      confirmText: '删除',
      confirmColor: '#f5222d',
    });

    if (!res.confirm) {
      return;
    }

    try {
      wx.showLoading({
        title: '删除中...',
        mask: true,
      });

      const response = await mistakesApi.deleteMistake(mistake.id);

      // 判断响应是否成功：检查状态码 200-299
      const isSuccess = response.statusCode >= 200 && response.statusCode < 300;

      if (isSuccess) {
        wx.showToast({
          title: '删除成功',
          icon: 'success',
        });

        // 刷新列表
        this.loadMistakesList(true);
      } else {
        throw new Error(response.data?.message || response.message || '删除失败');
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

  /**
   * 开始复习错题（三阶段递进式复习）
   */
  async onMistakeReview(e) {
    // ✅ 防御性编程
    if (!e || !e.detail || !e.detail.mistake || !e.detail.mistake.id) {
      console.error('[列表页] 复习错题事件无效', e);
      return;
    }

    const { mistake } = e.detail;
    console.log('[列表页] 开始三阶段复习，错题:', mistake);

    try {
      wx.showLoading({
        title: '准备复习中...',
        mask: true,
      });

      // 调用后端 API 启动复习会话
      const sessionData = await mistakesApi.startReviewSession(mistake.id);

      console.log('[列表页] 复习会话创建成功:', sessionData);

      // ✅ 验证返回数据
      if (!sessionData || !sessionData.session_id) {
        throw new Error('会话创建失败：未返回有效的会话ID');
      }

      wx.hideLoading();

      // 跳转到复习页面，传递会话 ID 和错题 ID
      wx.navigateTo({
        url: `/pages/mistakes/review/index?session_id=${sessionData.session_id}&mistake_id=${mistake.id}`,
        success: () => {
          console.log('[列表页] 成功跳转到复习页面');
        },
        fail: err => {
          console.error('[列表页] 跳转复习页面失败:', err);
          wx.showToast({
            title: '跳转失败',
            icon: 'none',
          });
        },
      });
    } catch (error) {
      console.error('[列表页] 启动复习会话失败:', error);
      wx.hideLoading();

      // ✅ 详细的错误提示
      let errorMessage = '启动复习失败';

      if (error.message) {
        errorMessage = error.message;
      }

      // 特殊处理限流错误
      if (error.statusCode === 429 || error.message?.includes('Too Many Requests')) {
        errorMessage = '请求过于频繁，请稍后再试';
      }

      wx.showToast({
        title: errorMessage,
        icon: 'none',
        duration: 2500,
      });
    }
  },

  /**
   * 添加错题
   */
  onAddMistake() {
    console.log('添加错题');

    // 跳转到添加错题页面
    wx.navigateTo({
      url: '/pages/mistakes/add/index',
    });
  },

  /**
   * 打开筛选弹窗
   */
  onOpenFilter() {
    this.setData({
      showFilterPopup: true,
    });
  },

  /**
   * 关闭筛选弹窗
   */
  onCloseFilter() {
    this.setData({
      showFilterPopup: false,
    });
  },

  /**
   * 打开搜索
   */
  onOpenSearch() {
    this.setData({
      showSearch: true,
    });
  },

  /**
   * 关闭搜索
   */
  onCloseSearch() {
    this.setData({
      showSearch: false,
      searchKeyword: '',
    });

    // 重新加载数据
    this.loadMistakesList(true);
  },

  /**
   * 搜索变化
   */
  onSearchChange(e) {
    this.setData({
      searchKeyword: e.detail,
    });
  },

  /**
   * 搜索
   */
  onSearch() {
    console.log('搜索错题', this.data.searchKeyword);
    this.loadMistakesList(true);
  },

  /**
   * 清除搜索
   */
  onSearchClear() {
    this.setData({
      searchKeyword: '',
    });
    this.loadMistakesList(true);
  },

  /**
   * 选择错题类型
   */
  onCategorySelect(e) {
    const { category } = e.currentTarget.dataset;

    this.setData({
      selectedCategory: category,
    });
  },

  /**
   * 选择来源
   */
  onSourceSelect(e) {
    const { source } = e.currentTarget.dataset;

    this.setData({
      selectedSource: source,
    });
  },

  /**
   * 选择科目
   */
  onSubjectSelect(e) {
    const { subject } = e.currentTarget.dataset;

    this.setData({
      selectedSubject: subject,
      selectedKnowledgePoint: '', // 重置知识点筛选
    });

    // 加载该科目的知识点列表
    if (subject && subject !== '全部') {
      this.loadKnowledgePoints();
    } else {
      this.setData({
        knowledgePointOptions: [],
      });
    }
  },

  /**
   * 选择知识点
   */
  onKnowledgePointSelect(e) {
    const { knowledgePoint } = e.currentTarget.dataset;

    this.setData({
      selectedKnowledgePoint: knowledgePoint,
    });
  },

  /**
   * 选择难度
   */
  onDifficultySelect(e) {
    const { difficulty } = e.currentTarget.dataset;

    this.setData({
      selectedDifficulty: difficulty,
    });
  },

  /**
   * 重置筛选条件
   */
  onResetFilter() {
    this.setData({
      selectedSubject: '',
      selectedDifficulty: '',
      selectedCategory: '',
      selectedSource: '',
      selectedKnowledgePoint: '',
      knowledgePointOptions: [],
    });
  },

  /**
   * 确认筛选
   */
  onConfirmFilter() {
    console.log('应用筛选条件', {
      subject: this.data.selectedSubject,
      difficulty: this.data.selectedDifficulty,
    });

    // 关闭弹窗
    this.setData({
      showFilterPopup: false,
    });

    // 重新加载数据
    this.loadMistakesList(true);
  },

  /**
   * 打开知识图谱
   */
  onOpenKnowledgeGraph() {
    console.log('打开知识图谱');
    const subject =
      this.data.selectedSubject && this.data.selectedSubject !== '全部'
        ? this.data.selectedSubject
        : '数学';

    wx.navigateTo({
      url: `/subpackages/charts/pages/knowledge-graph/index?subject=${subject}`,
      fail: err => {
        console.error('导航失败:', err);
        wx.showToast({
          title: '打开失败',
          icon: 'none',
        });
      },
    });
  },
};

// 应用增强的页面守卫
Page(createGuardedPage(pageObject, 'pages/mistakes/list/index'));
