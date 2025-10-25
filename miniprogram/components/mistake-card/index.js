// components/mistake-card/index.js
Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 错题数据对象
    mistake: {
      type: Object,
      value: null,
    },

    // 显示模式: 'list' | 'review' | 'detail'
    mode: {
      type: String,
      value: 'list',
    },

    // 是否显示操作按钮
    showActions: {
      type: Boolean,
      value: true,
    },
  },

  /**
   * 组件的初始数据
   */
  data: {},

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 🎯 获取错题类型文本
     */
    getCategoryText(category) {
      const categoryMap = {
        empty_question: '不会做',
        wrong_answer: '答错了',
        hard_question: '有难度',
      };
      return categoryMap[category] || '';
    },

    /**
     * 🎯 获取来源图标
     */
    getSourceIcon(source) {
      const iconMap = {
        learning: 'chat-o', // 学习问答
        manual: 'edit', // 手动添加
        homework: 'records-o', // 作业
      };
      return iconMap[source] || 'records-o';
    },

    /**
     * 获取难度图标
     */
    getDifficultyIcon(level) {
      const iconMap = {
        1: 'smile-o',
        2: 'flower-o',
        3: 'fire-o',
      };
      return iconMap[level] || 'flower-o';
    },

    /**
     * 获取难度文本
     */
    getDifficultyText(level) {
      const textMap = {
        1: '简单',
        2: '中等',
        3: '困难',
      };
      return textMap[level] || '未知';
    },

    /**
     * 获取掌握状态文本
     */
    getMasteryStatusText(status) {
      const textMap = {
        not_mastered: '未掌握',
        reviewing: '复习中',
        mastered: '已掌握',
      };
      return textMap[status] || '未知';
    },

    /**
     * 获取内容预览（最多显示100个字符）
     */
    getContentPreview(content) {
      if (!content) return '';
      return content.length > 100 ? content.substring(0, 100) + '...' : content;
    },

    /**
     * 获取正确率样式类
     */
    getRateClass(rate) {
      if (rate >= 80) return 'rate-high';
      if (rate >= 50) return 'rate-medium';
      return 'rate-low';
    },

    /**
     * 获取下次复习时间文本
     */
    getNextReviewText(nextReviewDate) {
      if (!nextReviewDate) return '';

      const now = new Date();
      const reviewDate = new Date(nextReviewDate);
      const diffDays = Math.ceil((reviewDate - now) / (1000 * 60 * 60 * 24));

      if (diffDays < 0) {
        return '需要复习';
      } else if (diffDays === 0) {
        return '今日复习';
      } else if (diffDays === 1) {
        return '明日复习';
      } else {
        return `${diffDays}天后复习`;
      }
    },

    /**
     * 获取下次复习时间样式类
     */
    getNextReviewClass(nextReviewDate) {
      if (!nextReviewDate) return '';

      const now = new Date();
      const reviewDate = new Date(nextReviewDate);
      const diffDays = Math.ceil((reviewDate - now) / (1000 * 60 * 60 * 24));

      if (diffDays < 0) return 'overdue';
      if (diffDays === 0) return 'today';
      return 'upcoming';
    },

    /**
     * 判断是否需要复习
     */
    isNeedReview(nextReviewDate) {
      if (!nextReviewDate) return false;

      const now = new Date();
      const reviewDate = new Date(nextReviewDate);

      return reviewDate <= now;
    },

    /**
     * 格式化时间
     */
    formatTime(time) {
      if (!time) return '';

      const date = new Date(time);
      const now = new Date();
      const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

      if (diffDays === 0) {
        return '今天 ' + this.formatTimeHHMM(date);
      } else if (diffDays === 1) {
        return '昨天 ' + this.formatTimeHHMM(date);
      } else if (diffDays < 7) {
        return diffDays + '天前';
      } else if (diffDays < 30) {
        return Math.floor(diffDays / 7) + '周前';
      } else if (diffDays < 365) {
        return Math.floor(diffDays / 30) + '月前';
      } else {
        return this.formatDate(date);
      }
    },

    /**
     * 格式化时间为 HH:MM
     */
    formatTimeHHMM(date) {
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      return `${hours}:${minutes}`;
    },

    /**
     * 格式化日期
     */
    formatDate(date) {
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      return `${year}-${month}-${day}`;
    },

    /**
     * 卡片点击事件
     */
    onCardTap(e) {
      const { mistake } = e.currentTarget.dataset;

      this.triggerEvent('tap', {
        mistake: mistake || this.data.mistake,
      });
    },

    /**
     * 查看详情
     */
    onViewDetail(e) {
      e.stopPropagation();
      const { mistake } = e.currentTarget.dataset;

      this.triggerEvent('detail', {
        mistake: mistake || this.data.mistake,
      });
    },

    /**
     * 开始复习
     */
    onStartReview(e) {
      e.stopPropagation();
      const { mistake } = e.currentTarget.dataset;

      this.triggerEvent('review', {
        mistake: mistake || this.data.mistake,
      });
    },

    /**
     * 编辑
     */
    onEdit(e) {
      e.stopPropagation();
      const { mistake } = e.currentTarget.dataset;

      this.triggerEvent('edit', {
        mistake: mistake || this.data.mistake,
      });
    },

    /**
     * 删除
     */
    onDelete(e) {
      e.stopPropagation();
      const { mistake } = e.currentTarget.dataset;

      this.triggerEvent('delete', {
        mistake: mistake || this.data.mistake,
      });
    },
  },
});
