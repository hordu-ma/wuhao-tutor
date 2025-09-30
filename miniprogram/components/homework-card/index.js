// components/homework-card/index.js

const config = require('../../config/index.js');
const utils = require('../../utils/utils.js');

Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 作业数据
    homework: {
      type: Object,
      value: {},
      observer: function (newVal, oldVal) {
        if (newVal && newVal !== oldVal) {
          this.processHomeworkData(newVal);
        }
      }
    },

    // 用户角色
    userRole: {
      type: String,
      value: 'student'
    },

    // 是否显示操作按钮
    showActions: {
      type: Boolean,
      value: true
    },

    // 卡片样式
    cardStyle: {
      type: String,
      value: 'default' // default, compact, detailed
    },

    // 是否可点击
    clickable: {
      type: Boolean,
      value: true
    },

    // 是否显示收藏按钮
    showFavorite: {
      type: Boolean,
      value: true
    }
  },

  /**
   * 组件的初始数据
   */
  data: {
    // 处理后的作业数据
    processedHomework: {},

    // 格式化的时间
    formattedCreateTime: '',
    formattedDeadline: '',

    // 截止时间状态
    deadlineStatus: 'normal', // normal, warning, danger

    // 难度信息
    difficultyInfo: {
      text: '',
      icon: ''
    },

    // 状态信息
    statusInfo: {
      text: '',
      color: ''
    },

    // 成绩等级信息
    gradeInfo: {
      text: '',
      level: ''
    },

    // 是否正在提交
    isSubmitting: false
  },

  /**
   * 组件生命周期
   */
  lifetimes: {
    created() {
      console.log('作业卡片组件创建');
    },

    attached() {
      console.log('作业卡片组件附加到页面');
      this.initComponent();
    },

    detached() {
      console.log('作业卡片组件从页面移除');
    }
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 初始化组件
     */
    initComponent() {
      if (this.data.homework && Object.keys(this.data.homework).length > 0) {
        this.processHomeworkData(this.data.homework);
      }
    },

    /**
     * 处理作业数据
     */
    processHomeworkData(homework) {
      if (!homework) return;

      const processedHomework = { ...homework };

      // 处理时间格式化
      const formattedCreateTime = this.formatTime(homework.createTime);
      const formattedDeadline = this.formatTime(homework.deadline);

      // 计算截止时间状态
      const deadlineStatus = this.getDeadlineStatus(homework.deadline);

      // 获取难度信息
      const difficultyInfo = this.getDifficultyInfo(homework.difficulty);

      // 获取状态信息
      const statusInfo = this.getStatusInfo(homework.status);

      // 获取成绩信息
      const gradeInfo = this.getGradeInfo(homework.grade);

      // 处理问题类型
      if (homework.questions && homework.questions.length > 0) {
        processedHomework.questionTypes = this.extractQuestionTypes(homework.questions);
      }

      // 检查是否为新作业（7天内创建）
      processedHomework.isNew = this.isNewHomework(homework.createTime);

      // 检查是否已逾期
      processedHomework.isOverdue = this.isOverdue(homework.deadline, homework.status);

      this.setData({
        processedHomework,
        formattedCreateTime,
        formattedDeadline,
        deadlineStatus,
        difficultyInfo,
        statusInfo,
        gradeInfo
      });
    },

    /**
     * 格式化时间
     */
    formatTime(timestamp) {
      if (!timestamp) return '';

      try {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) {
          // 今天
          return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        } else if (days === 1) {
          // 昨天
          return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        } else if (days < 7) {
          // 一周内
          const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
          return `${weekdays[date.getDay()]} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        } else {
          // 超过一周
          return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        }
      } catch (error) {
        console.error('时间格式化失败', error);
        return '';
      }
    },

    /**
     * 获取截止时间状态
     */
    getDeadlineStatus(deadline) {
      if (!deadline) return 'normal';

      const now = new Date().getTime();
      const deadlineTime = new Date(deadline).getTime();
      const diff = deadlineTime - now;
      const hours = diff / (1000 * 60 * 60);

      if (diff < 0) {
        return 'danger'; // 已过期
      } else if (hours < 24) {
        return 'danger'; // 24小时内
      } else if (hours < 72) {
        return 'warning'; // 72小时内
      } else {
        return 'normal';
      }
    },

    /**
     * 获取截止时间图标
     */
    getDeadlineIcon(deadline) {
      const status = this.getDeadlineStatus(deadline);
      const iconMap = {
        normal: 'clock-o',
        warning: 'warning-o',
        danger: 'close'
      };
      return iconMap[status] || 'clock-o';
    },

    /**
     * 获取难度信息
     */
    getDifficultyInfo(difficulty) {
      const difficultyMap = {
        easy: { text: '简单', icon: 'star-o' },
        medium: { text: '中等', icon: 'star' },
        hard: { text: '困难', icon: 'fire' }
      };
      return difficultyMap[difficulty] || { text: '未知', icon: 'question-o' };
    },

    /**
     * 获取难度文本
     */
    getDifficultyText(difficulty) {
      return this.getDifficultyInfo(difficulty).text;
    },

    /**
     * 获取难度图标
     */
    getDifficultyIcon(difficulty) {
      return this.getDifficultyInfo(difficulty).icon;
    },

    /**
     * 获取状态信息
     */
    getStatusInfo(status) {
      const statusMap = {
        pending: { text: '待开始', color: '#1890ff' },
        in_progress: { text: '进行中', color: '#faad14' },
        completed: { text: '已完成', color: '#52c41a' },
        submitted: { text: '已提交', color: '#722ed1' },
        graded: { text: '已批改', color: '#722ed1' },
        overdue: { text: '已逾期', color: '#f5222d' }
      };
      return statusMap[status] || { text: '未知', color: '#666' };
    },

    /**
     * 获取状态文本
     */
    getStatusText(status) {
      return this.getStatusInfo(status).text;
    },

    /**
     * 获取成绩信息
     */
    getGradeInfo(grade) {
      if (!grade || !grade.score) {
        return { text: '', level: '' };
      }

      const { score, total } = grade;
      const percentage = (score / total) * 100;

      let level, text;
      if (percentage >= 90) {
        level = 'excellent';
        text = '优秀';
      } else if (percentage >= 80) {
        level = 'good';
        text = '良好';
      } else if (percentage >= 60) {
        level = 'average';
        text = '及格';
      } else {
        level = 'poor';
        text = '不及格';
      }

      return { text, level };
    },

    /**
     * 获取成绩等级文本
     */
    getGradeText(level) {
      return this.getGradeInfo({ score: 0, total: 100 }).text;
    },

    /**
     * 提取问题类型
     */
    extractQuestionTypes(questions) {
      if (!questions || !Array.isArray(questions)) return [];

      const types = [...new Set(questions.map(q => q.type))];
      const typeMap = {
        'single_choice': '单选',
        'multiple_choice': '多选',
        'fill_blank': '填空',
        'essay': '简答',
        'calculation': '计算'
      };

      return types.map(type => typeMap[type] || type).slice(0, 3);
    },

    /**
     * 检查是否为新作业
     */
    isNewHomework(createTime) {
      if (!createTime) return false;

      const now = new Date().getTime();
      const createTimestamp = new Date(createTime).getTime();
      const diffDays = (now - createTimestamp) / (1000 * 60 * 60 * 24);

      return diffDays <= 7;
    },

    /**
     * 检查是否已逾期
     */
    isOverdue(deadline, status) {
      if (!deadline || ['completed', 'submitted', 'graded'].includes(status)) {
        return false;
      }

      const now = new Date().getTime();
      const deadlineTime = new Date(deadline).getTime();

      return now > deadlineTime;
    },

    /**
     * 卡片点击事件
     */
    onCardTap(e) {
      if (!this.data.clickable) return;

      const { homework } = e.currentTarget.dataset;

      console.log('作业卡片点击', homework);

      this.triggerEvent('tap', {
        homework: homework || this.data.homework
      });

      // 埋点统计
      if (config.analytics.enabled) {
        wx.reportAnalytics('homework_card_click', {
          homework_id: homework?.id,
          homework_status: homework?.status,
          user_role: this.data.userRole
        });
      }
    },

    /**
     * 开始作业
     */
    onStartHomework(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('开始作业', homework);

      this.triggerEvent('start', {
        homework: homework || this.data.homework
      });
    },

    /**
     * 继续作业
     */
    onContinueHomework(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('继续作业', homework);

      this.triggerEvent('continue', {
        homework: homework || this.data.homework
      });
    },

    /**
     * 查看结果
     */
    onViewResult(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('查看结果', homework);

      this.triggerEvent('view-result', {
        homework: homework || this.data.homework
      });
    },

    /**
     * 重做作业
     */
    onRetryHomework(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('重做作业', homework);

      wx.showModal({
        title: '确认重做',
        content: '重做将清空之前的答题记录，确定要重新开始吗？',
        success: (res) => {
          if (res.confirm) {
            this.triggerEvent('retry', {
              homework: homework || this.data.homework
            });
          }
        }
      });
    },

    /**
     * 查看详情
     */
    onViewDetail(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('查看详情', homework);

      this.triggerEvent('view-detail', {
        homework: homework || this.data.homework
      });
    },

    /**
     * 批改作业（教师）
     */
    onGradeHomework(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('批改作业', homework);

      this.triggerEvent('grade', {
        homework: homework || this.data.homework
      });
    },

    /**
     * 查看统计（教师）
     */
    onViewStatistics(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('查看统计', homework);

      this.triggerEvent('view-statistics', {
        homework: homework || this.data.homework
      });
    },

    /**
     * 更多操作
     */
    onMoreActions(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('更多操作', homework);

      const actions = [];

      if (this.data.userRole === 'teacher') {
        actions.push('编辑作业', '复制作业', '删除作业', '导出数据');
      } else if (this.data.userRole === 'student') {
        actions.push('收藏作业', '分享作业', '举报问题');
      }

      wx.showActionSheet({
        itemList: actions,
        success: (res) => {
          const action = actions[res.tapIndex];
          this.triggerEvent('more-action', {
            homework: homework || this.data.homework,
            action
          });
        }
      });
    },

    /**
     * 查看孩子完成情况（家长）
     */
    onViewChildProgress(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;

      console.log('查看孩子完成情况', homework);

      this.triggerEvent('view-child-progress', {
        homework: homework || this.data.homework
      });
    },

    /**
     * 切换收藏状态
     */
    onToggleFavorite(e) {
      e.stopPropagation();

      const { homework } = e.currentTarget.dataset;
      const currentHomework = homework || this.data.homework;

      console.log('切换收藏', currentHomework);

      // 更新本地状态
      const updatedHomework = {
        ...currentHomework,
        isFavorite: !currentHomework.isFavorite
      };

      this.setData({
        homework: updatedHomework,
        processedHomework: updatedHomework
      });

      // 触发收藏事件
      this.triggerEvent('favorite', {
        homework: updatedHomework,
        isFavorite: updatedHomework.isFavorite
      });

      // 显示提示
      wx.showToast({
        title: updatedHomework.isFavorite ? '已收藏' : '已取消收藏',
        icon: 'success',
        duration: 1500
      });
    },

    /**
     * 提交作业
     */
    async onSubmitHomework(homework) {
      try {
        this.setData({
          isSubmitting: true
        });

        // 触发提交事件
        this.triggerEvent('submit', {
          homework: homework || this.data.homework
        });

      } catch (error) {
        console.error('提交作业失败', error);

        wx.showToast({
          title: '提交失败',
          icon: 'error'
        });
      } finally {
        this.setData({
          isSubmitting: false
        });
      }
    },

    /**
     * 显示作业预览
     */
    showPreview() {
      const homework = this.data.homework;

      if (!homework) return;

      // 构建预览内容
      const previewItems = [];

      if (homework.description) {
        previewItems.push({
          type: 'text',
          content: homework.description
        });
      }

      if (homework.attachments && homework.attachments.length > 0) {
        homework.attachments.forEach(attachment => {
          if (attachment.type === 'image') {
            previewItems.push({
              type: 'image',
              url: attachment.url
            });
          }
        });
      }

      // 显示预览弹窗
      this.triggerEvent('preview', {
        homework,
        items: previewItems
      });
    },

    /**
     * 获取组件数据（供外部调用）
     */
    getComponentData() {
      return {
        homework: this.data.homework,
        processedHomework: this.data.processedHomework,
        userRole: this.data.userRole
      };
    },

    /**
     * 更新作业数据（供外部调用）
     */
    updateHomework(newHomework) {
      this.setData({
        homework: newHomework
      });
      this.processHomeworkData(newHomework);
    }
  }
});
