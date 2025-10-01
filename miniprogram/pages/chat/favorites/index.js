// pages/chat/favorites/index.js - 问答收藏管理页面

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

    // 收藏列表
    favoritesList: [],

    // 收藏夹分类
    categories: [
      { id: 'all', name: '全部收藏', icon: 'star-o', count: 0 },
      { id: 'homework', name: '作业练习', icon: 'edit', count: 0 },
      { id: 'concept', name: '概念理解', icon: 'bulb-o', count: 0 },
      { id: 'method', name: '方法技巧', icon: 'medal-o', count: 0 },
      { id: 'review', name: '复习总结', icon: 'bookmark-o', count: 0 },
      { id: 'explore', name: '拓展探索', icon: 'search', count: 0 },
    ],

    // 当前选中分类
    currentCategory: 'all',

    // 分页信息
    currentPage: 1,
    pageSize: 20,
    hasMore: true,
    total: 0,

    // 加载状态
    loading: true,
    refreshing: false,
    loadingMore: false,

    // 搜索和筛选
    searchKeyword: '',
    sortBy: 'time', // time, subject, length
    sortOrder: 'desc', // desc, asc

    // 选中的收藏（用于批量操作）
    selectedItems: [],
    selectionMode: false,

    // UI状态
    showCategoryPicker: false,
    showSortMenu: false,
    showShareOptions: false,

    // 导出选项
    exportFormats: [
      { id: 'text', name: '文本格式', icon: 'notes-o' },
      { id: 'markdown', name: 'Markdown', icon: 'guide-o' },
      { id: 'pdf', name: 'PDF文档', icon: 'description' },
    ],

    // 分享选项
    shareOptions: [
      { id: 'wechat', name: '微信好友', icon: 'wechat' },
      { id: 'moments', name: '朋友圈', icon: 'friends-o' },
      { id: 'copy', name: '复制链接', icon: 'link-o' },
    ],

    // 错误状态
    error: null,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('问答收藏页面加载', options);

    try {
      await this.initUserInfo();
      await this.loadFavoritesData(true);
      await this.updateCategoryCounts();

      // 从其他页面跳转指定分类
      if (options.category) {
        this.switchCategory(options.category);
      }
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
    const category = this.data.categories.find(c => c.id === this.data.currentCategory);
    return {
      title: `我的${category?.name || '收藏'}`,
      path: `/pages/chat/favorites/index?category=${this.data.currentCategory}`,
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
   * 加载收藏数据
   */
  async loadFavoritesData(reset = false) {
    try {
      if (reset) {
        this.setData({
          loading: true,
          currentPage: 1,
          favoritesList: [],
          error: null,
        });
      } else {
        this.setData({ loadingMore: true });
      }

      const { currentPage, pageSize, currentCategory, searchKeyword, sortBy, sortOrder } =
        this.data;

      // TODO: 调用API获取收藏数据
      // const response = await api.getFavorites({
      //   page: currentPage,
      //   pageSize,
      //   category: currentCategory,
      //   search: searchKeyword,
      //   sortBy,
      //   sortOrder
      // });

      // 模拟数据
      const mockData = this.generateMockFavoritesData(currentPage, pageSize);

      if (reset) {
        this.setData({
          favoritesList: mockData.list,
          total: mockData.total,
          hasMore: mockData.hasMore,
        });
      } else {
        this.setData({
          favoritesList: [...this.data.favoritesList, ...mockData.list],
          hasMore: mockData.hasMore,
        });
      }

      this.setData({ currentPage: currentPage + 1 });
    } catch (error) {
      console.error('加载收藏数据失败:', error);
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
   * 生成模拟收藏数据
   */
  generateMockFavoritesData(page, pageSize) {
    const subjects = ['math', 'chinese', 'english', 'physics', 'chemistry'];
    const questionTypes = ['homework', 'concept', 'method', 'review', 'explore'];
    const questions = [
      '如何快速解二次方程？',
      '文言文翻译技巧总结',
      '英语语法易错点梳理',
      '物理公式推导方法',
      '化学实验注意事项',
    ];

    const list = [];
    const startIndex = (page - 1) * pageSize;

    for (let i = 0; i < pageSize && i < 30; i++) {
      const index = startIndex + i;
      const subject = subjects[index % subjects.length];
      const questionType = questionTypes[index % questionTypes.length];
      const question = questions[index % questions.length];

      // 根据当前分类筛选
      if (this.data.currentCategory !== 'all' && questionType !== this.data.currentCategory) {
        continue;
      }

      const favoriteData = {
        id: `fav_${index + 1}`,
        chatId: `chat_${index + 1}`,
        subject: subject,
        questionType: questionType,
        question: question,
        answer: `这是对"${question}"的详细回答，包含了完整的解题思路和方法技巧...`,
        createdAt: Date.now() - index * 60 * 60 * 1000,
        favoriteAt: Date.now() - index * 30 * 60 * 1000,
        tags: [`${subject}`, `${questionType}`, '重点'],
        notes: index % 3 === 0 ? '这个很重要，要重点复习' : '',
        shareCount: Math.floor(Math.random() * 10),
        viewCount: Math.floor(Math.random() * 50) + 10,
      };

      list.push(favoriteData);
    }

    return {
      list,
      total: 50,
      hasMore: page * pageSize < 50,
    };
  },

  /**
   * 更新分类统计
   */
  async updateCategoryCounts() {
    try {
      // TODO: 调用API获取分类统计
      // const counts = await api.getFavoriteCounts();

      // 模拟统计数据
      const mockCounts = {
        all: 48,
        homework: 15,
        concept: 12,
        method: 8,
        review: 7,
        explore: 6,
      };

      const categories = this.data.categories.map(cat => ({
        ...cat,
        count: mockCounts[cat.id] || 0,
      }));

      this.setData({ categories });
    } catch (error) {
      console.error('更新分类统计失败:', error);
    }
  },

  /**
   * 刷新数据
   */
  async refreshData() {
    this.setData({ refreshing: true });
    await Promise.all([this.loadFavoritesData(true), this.updateCategoryCounts()]);
  },

  /**
   * 加载更多数据
   */
  loadMoreData() {
    if (!this.data.hasMore || this.data.loadingMore) {
      return;
    }
    this.loadFavoritesData(false);
  },

  /**
   * 切换分类
   */
  switchCategory(categoryId) {
    const categories = this.data.categories.map(cat => ({
      ...cat,
      active: cat.id === categoryId,
    }));

    this.setData({
      categories,
      currentCategory: categoryId,
    });

    this.loadFavoritesData(true);
  },

  /**
   * 分类点击
   */
  onCategoryTap(e) {
    const { categoryId } = e.currentTarget.dataset;
    this.switchCategory(categoryId);
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
      this.loadFavoritesData(true);
    }, 500);
  },

  /**
   * 清空搜索
   */
  onSearchClear() {
    this.setData({ searchKeyword: '' });
    this.loadFavoritesData(true);
  },

  /**
   * 显示排序菜单
   */
  onShowSortMenu() {
    this.setData({ showSortMenu: true });
  },

  /**
   * 排序选择
   */
  onSortSelect(e) {
    const { sortBy, sortOrder } = e.currentTarget.dataset;

    this.setData({
      sortBy: sortBy || this.data.sortBy,
      sortOrder: sortOrder || this.data.sortOrder,
      showSortMenu: false,
    });

    this.loadFavoritesData(true);
  },

  /**
   * 点击收藏项
   */
  onFavoriteItemTap(e) {
    const { item } = e.currentTarget.dataset;

    if (this.data.selectionMode) {
      this.toggleItemSelection(item.id);
    } else {
      // 跳转到对话详情
      wx.navigateTo({
        url: `/pages/chat/detail/index?id=${item.chatId}`,
      });
    }
  },

  /**
   * 长按收藏项
   */
  onFavoriteItemLongPress(e) {
    const { item } = e.currentTarget.dataset;

    wx.showActionSheet({
      itemList: ['取消收藏', '编辑笔记', '分享', '复制内容', '重新提问'],
      success: res => {
        switch (res.tapIndex) {
          case 0:
            this.removeFavorite(item.id);
            break;
          case 1:
            this.editNotes(item);
            break;
          case 2:
            this.shareFavorite(item);
            break;
          case 3:
            this.copyContent(item);
            break;
          case 4:
            this.askAgain(item);
            break;
        }
      },
    });
  },

  /**
   * 取消收藏
   */
  async removeFavorite(itemId) {
    try {
      // TODO: 调用API取消收藏
      // await api.removeFavorite(itemId);

      const favoritesList = this.data.favoritesList.filter(item => item.id !== itemId);
      this.setData({ favoritesList });

      // 更新分类统计
      await this.updateCategoryCounts();

      wx.showToast({
        title: '已取消收藏',
        icon: 'success',
      });
    } catch (error) {
      console.error('取消收藏失败:', error);
      this.showError('操作失败');
    }
  },

  /**
   * 编辑笔记
   */
  editNotes(item) {
    wx.showModal({
      title: '编辑笔记',
      content: '请输入笔记内容',
      placeholderText: item.notes || '添加您的学习笔记...',
      editable: true,
      success: async res => {
        if (res.confirm) {
          try {
            // TODO: 调用API更新笔记
            // await api.updateFavoriteNotes(item.id, res.content);

            const favoritesList = this.data.favoritesList.map(fav => {
              if (fav.id === item.id) {
                return { ...fav, notes: res.content };
              }
              return fav;
            });

            this.setData({ favoritesList });

            wx.showToast({
              title: '笔记已保存',
              icon: 'success',
            });
          } catch (error) {
            console.error('保存笔记失败:', error);
            this.showError('保存失败');
          }
        }
      },
    });
  },

  /**
   * 分享收藏
   */
  shareFavorite(item) {
    this.setData({
      showShareOptions: true,
      currentShareItem: item,
    });
  },

  /**
   * 执行分享
   */
  onShareOptionSelect(e) {
    const { option } = e.currentTarget.dataset;
    const item = this.data.currentShareItem;

    switch (option.id) {
      case 'copy':
        this.copyContent(item);
        break;
      case 'wechat':
        // TODO: 实现微信分享
        wx.showToast({
          title: '分享功能开发中',
          icon: 'none',
        });
        break;
      case 'moments':
        // TODO: 实现朋友圈分享
        wx.showToast({
          title: '分享功能开发中',
          icon: 'none',
        });
        break;
    }

    this.setData({ showShareOptions: false });
  },

  /**
   * 复制内容
   */
  copyContent(item) {
    const content = `问题：${item.question}\n\n答案：${item.answer}${item.notes ? '\n\n笔记：' + item.notes : ''}`;

    wx.setClipboardData({
      data: content,
      success: () => {
        wx.showToast({
          title: '内容已复制',
          icon: 'success',
        });
      },
    });
  },

  /**
   * 重新提问
   */
  askAgain(item) {
    wx.navigateTo({
      url: `/pages/chat/index/index?question=${encodeURIComponent(item.question)}&subject=${item.subject}`,
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
  batchRemove() {
    if (this.data.selectedItems.length === 0) {
      wx.showToast({
        title: '请选择要删除的项目',
        icon: 'none',
      });
      return;
    }

    wx.showModal({
      title: '批量取消收藏',
      content: `确定要取消收藏${this.data.selectedItems.length}项内容吗？`,
      success: async res => {
        if (res.confirm) {
          try {
            // TODO: 调用API批量取消收藏
            // await api.batchRemoveFavorites(this.data.selectedItems);

            const favoritesList = this.data.favoritesList.filter(
              item => !this.data.selectedItems.includes(item.id),
            );

            this.setData({
              favoritesList,
              selectedItems: [],
              selectionMode: false,
            });

            await this.updateCategoryCounts();

            wx.showToast({
              title: '操作成功',
              icon: 'success',
            });
          } catch (error) {
            console.error('批量删除失败:', error);
            this.showError('操作失败');
          }
        }
      },
    });
  },

  /**
   * 批量导出
   */
  batchExport() {
    if (this.data.selectedItems.length === 0) {
      wx.showToast({
        title: '请选择要导出的项目',
        icon: 'none',
      });
      return;
    }

    wx.showActionSheet({
      itemList: this.data.exportFormats.map(format => format.name),
      success: res => {
        const format = this.data.exportFormats[res.tapIndex];
        this.exportFavorites(this.data.selectedItems, format.id);
      },
    });
  },

  /**
   * 导出收藏
   */
  async exportFavorites(itemIds, format) {
    try {
      wx.showLoading({ title: '导出中...' });

      // TODO: 调用API导出收藏
      // const result = await api.exportFavorites({
      //   itemIds,
      //   format
      // });

      // 模拟导出
      await new Promise(resolve => setTimeout(resolve, 2000));

      wx.hideLoading();
      wx.showToast({
        title: '导出成功',
        icon: 'success',
      });

      // 重置选择状态
      this.setData({
        selectedItems: [],
        selectionMode: false,
      });
    } catch (error) {
      console.error('导出失败:', error);
      wx.hideLoading();
      this.showError('导出失败');
    }
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
    const subjectMap = {
      math: '数学',
      chinese: '语文',
      english: '英语',
      physics: '物理',
      chemistry: '化学',
    };
    return subjectMap[subjectId] || subjectId;
  },

  /**
   * 获取问题类型名称
   */
  getQuestionTypeName(typeId) {
    const typeMap = {
      homework: '作业练习',
      concept: '概念理解',
      method: '方法技巧',
      review: '复习总结',
      explore: '拓展探索',
    };
    return typeMap[typeId] || typeId;
  },
});
