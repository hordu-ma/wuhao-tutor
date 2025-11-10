// 批改结果卡片组件
Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 批改结果数据
    data: {
      type: Object,
      value: null,
    },
  },

  /**
   * 组件的初始数据
   */
  data: {
    mistakes: [], // 错题列表（错误+未作答）
    correctCount: 0, // 正确题目数量
  },

  /**
   * 数据监听器
   */
  observers: {
    data: function (correctionData) {
      // 🎯 [新增] 数据验证
      if (!correctionData) {
        console.warn('[correction-card] 批改数据为空');
        return;
      }

      if (!correctionData.corrections || !Array.isArray(correctionData.corrections)) {
        console.error('[correction-card] corrections 字段缺失或格式错误');
        wx.showToast({
          title: '批改数据格式错误',
          icon: 'none',
        });
        return;
      }

      if (correctionData.total_questions === undefined) {
        console.warn('[correction-card] total_questions 字段缺失');
      }

      // 过滤出错题和未作答的题目
      const mistakes = correctionData.corrections.filter(item => {
        return item.error_type || item.is_unanswered;
      });

      // 计算正确题目数量
      const correctCount =
        correctionData.total_questions -
        (correctionData.error_count || 0) -
        (correctionData.unanswered_count || 0);

      this.setData({
        mistakes: mistakes,
        correctCount: correctCount,
      });

      console.log('[correction-card] 数据更新:', {
        total: correctionData.total_questions,
        correct: correctCount,
        errors: correctionData.error_count,
        unanswered: correctionData.unanswered_count,
        mistakesCount: mistakes.length,
      });
    },
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 跳转到错题本页面
     */
    goToMistakeBook() {
      const mistakes = this.data.mistakes;

      if (mistakes.length === 0) {
        wx.showToast({
          title: '没有错题',
          icon: 'none',
        });
        return;
      }

      console.log('[correction-card] 跳转到错题本');

      // 跳转到错题本页面
      wx.navigateTo({
        url: '/pages/mistakes/index/index',
      });
    },

    /**
     * 继续练习（全对情况）
     */
    retry() {
      console.log('[correction-card] 继续练习');

      wx.showToast({
        title: '真棒！继续加油',
        icon: 'success',
      });

      // 触发父组件事件
      this.triggerEvent('retry');
    },
  },

  /**
   * 组件生命周期
   */
  lifetimes: {
    attached() {
      console.log('[correction-card] 组件已挂载');
    },

    detached() {
      console.log('[correction-card] 组件已卸载');
    },
  },
});
