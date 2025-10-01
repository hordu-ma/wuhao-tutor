// components/correction-result/index.js - 批改结果展示组件

Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 批改结果数据
    correction: {
      type: Object,
      value: {},
      observer: function (newVal) {
        if (newVal) {
          this.processCorrectionData(newVal);
        }
      },
    },

    // 显示模式
    mode: {
      type: String,
      value: 'detailed', // detailed, compact, summary
    },

    // 是否显示详细评语
    showComment: {
      type: Boolean,
      value: true,
    },

    // 是否显示题目详情
    showQuestions: {
      type: Boolean,
      value: true,
    },

    // 自定义样式
    customClass: {
      type: String,
      value: '',
    },
  },

  /**
   * 组件的初始数据
   */
  data: {
    // 处理后的批改数据
    processedCorrection: {},

    // 成绩等级信息
    gradeInfo: {
      level: '',
      color: '',
      description: '',
    },

    // 分数百分比
    scorePercentage: 0,

    // 统计信息
    statistics: {
      totalQuestions: 0,
      correctCount: 0,
      incorrectCount: 0,
      correctRate: 0,
    },

    // 是否展开详细信息
    expanded: false,

    // 格式化的时间
    formattedTime: '',
  },

  /**
   * 组件生命周期
   */
  lifetimes: {
    attached() {
      console.log('批改结果组件附加到页面');
      if (this.data.correction && Object.keys(this.data.correction).length > 0) {
        this.processCorrectionData(this.data.correction);
      }
    },
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 处理批改数据
     */
    processCorrectionData(correction) {
      if (!correction || Object.keys(correction).length === 0) return;

      // 计算分数百分比
      const scorePercentage =
        correction.totalScore > 0
          ? Math.round((correction.score / correction.totalScore) * 100)
          : 0;

      // 获取成绩等级信息
      const gradeInfo = this.getGradeInfo(correction.grade, scorePercentage);

      // 计算统计信息
      const statistics = this.calculateStatistics(correction.corrections || []);

      // 格式化时间
      const formattedTime = this.formatTime(correction.correctedAt);

      this.setData({
        processedCorrection: correction,
        scorePercentage,
        gradeInfo,
        statistics,
        formattedTime,
      });
    },

    /**
     * 获取成绩等级信息
     */
    getGradeInfo(grade, percentage) {
      const gradeMap = {
        'A+': { level: 'A+', color: '#52c41a', description: '优秀' },
        A: { level: 'A', color: '#52c41a', description: '优秀' },
        'B+': { level: 'B+', color: '#1890ff', description: '良好' },
        B: { level: 'B', color: '#1890ff', description: '良好' },
        'C+': { level: 'C+', color: '#faad14', description: '中等' },
        C: { level: 'C', color: '#faad14', description: '中等' },
        D: { level: 'D', color: '#fa541c', description: '需要改进' },
        F: { level: 'F', color: '#f5222d', description: '不及格' },
      };

      if (grade && gradeMap[grade]) {
        return gradeMap[grade];
      }

      // 根据分数自动判断等级
      if (percentage >= 95) return gradeMap['A+'];
      if (percentage >= 90) return gradeMap['A'];
      if (percentage >= 85) return gradeMap['B+'];
      if (percentage >= 80) return gradeMap['B'];
      if (percentage >= 75) return gradeMap['C+'];
      if (percentage >= 70) return gradeMap['C'];
      if (percentage >= 60) return gradeMap['D'];
      return gradeMap['F'];
    },

    /**
     * 计算统计信息
     */
    calculateStatistics(corrections) {
      const totalQuestions = corrections.length;
      const correctCount = corrections.filter(item => item.isCorrect).length;
      const incorrectCount = totalQuestions - correctCount;
      const correctRate =
        totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0;

      return {
        totalQuestions,
        correctCount,
        incorrectCount,
        correctRate,
      };
    },

    /**
     * 格式化时间
     */
    formatTime(timeString) {
      if (!timeString) return '';

      const date = new Date(timeString);
      const now = new Date();
      const diff = now - date;
      const diffDays = Math.floor(diff / (1000 * 60 * 60 * 24));
      const diffHours = Math.floor(diff / (1000 * 60 * 60));
      const diffMinutes = Math.floor(diff / (1000 * 60));

      if (diffDays > 0) {
        return `${diffDays}天前`;
      } else if (diffHours > 0) {
        return `${diffHours}小时前`;
      } else if (diffMinutes > 0) {
        return `${diffMinutes}分钟前`;
      } else {
        return '刚刚';
      }
    },

    /**
     * 切换展开状态
     */
    onToggleExpanded() {
      this.setData({
        expanded: !this.data.expanded,
      });
    },

    /**
     * 查看题目详情
     */
    onViewQuestionDetail(e) {
      const { question } = e.currentTarget.dataset;

      this.triggerEvent('questiontap', {
        question: question,
      });
    },

    /**
     * 分享成绩
     */
    onShareScore() {
      const { processedCorrection, gradeInfo } = this.data;

      this.triggerEvent('sharescore', {
        score: processedCorrection.score,
        totalScore: processedCorrection.totalScore,
        grade: gradeInfo.level,
        description: gradeInfo.description,
      });
    },

    /**
     * 查看老师评语详情
     */
    onViewCommentDetail() {
      const { processedCorrection } = this.data;

      wx.showModal({
        title: '教师评语',
        content: processedCorrection.comment || '暂无评语',
        showCancel: false,
        confirmText: '确定',
      });
    },
  },
});
