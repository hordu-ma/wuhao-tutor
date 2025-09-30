/**
 * 学习卡片组件
 * 用于展示作业、课程、测试等学习相关内容
 */
Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 卡片标题
    title: {
      type: String,
      value: ''
    },
    // 卡片副标题
    subtitle: {
      type: String,
      value: ''
    },
    // 状态：pending-待处理, processing-进行中, completed-已完成, overdue-已逾期
    status: {
      type: String,
      value: 'pending'
    },
    // 截止时间
    deadline: {
      type: String,
      value: ''
    },
    // 学科类型
    subject: {
      type: String,
      value: ''
    },
    // 难度等级：easy-简单, medium-中等, hard-困难
    difficulty: {
      type: String,
      value: 'medium'
    },
    // 进度百分比 (0-100)
    progress: {
      type: Number,
      value: 0
    },
    // 是否显示进度条
    showProgress: {
      type: Boolean,
      value: false
    },
    // 图标名称
    icon: {
      type: String,
      value: 'homework'
    },
    // 右侧额外信息
    extra: {
      type: String,
      value: ''
    },
    // 是否可点击
    clickable: {
      type: Boolean,
      value: true
    },
    // 自定义样式类名
    customClass: {
      type: String,
      value: ''
    }
  },

  /**
   * 组件的初始数据
   */
  data: {
    statusConfig: {
      pending: {
        text: '待处理',
        color: '#faad14',
        bgColor: '#fff7e6'
      },
      processing: {
        text: '进行中',
        color: '#1890ff',
        bgColor: '#e6f7ff'
      },
      completed: {
        text: '已完成',
        color: '#52c41a',
        bgColor: '#f6ffed'
      },
      overdue: {
        text: '已逾期',
        color: '#f5222d',
        bgColor: '#fff2f0'
      }
    },
    difficultyConfig: {
      easy: {
        text: '简单',
        color: '#52c41a'
      },
      medium: {
        text: '中等',
        color: '#faad14'
      },
      hard: {
        text: '困难',
        color: '#f5222d'
      }
    },
    subjectConfig: {
      math: {
        text: '数学',
        color: '#ff6b6b'
      },
      chinese: {
        text: '语文',
        color: '#4ecdc4'
      },
      english: {
        text: '英语',
        color: '#45b7d1'
      },
      physics: {
        text: '物理',
        color: '#96ceb4'
      },
      chemistry: {
        text: '化学',
        color: '#feca57'
      },
      biology: {
        text: '生物',
        color: '#48dbfb'
      },
      history: {
        text: '历史',
        color: '#ff9ff3'
      },
      geography: {
        text: '地理',
        color: '#54a0ff'
      },
      politics: {
        text: '政治',
        color: '#5f27cd'
      }
    }
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 获取状态配置
     */
    getStatusConfig() {
      return this.data.statusConfig[this.data.status] || this.data.statusConfig.pending;
    },

    /**
     * 获取难度配置
     */
    getDifficultyConfig() {
      return this.data.difficultyConfig[this.data.difficulty] || this.data.difficultyConfig.medium;
    },

    /**
     * 获取学科配置
     */
    getSubjectConfig() {
      return this.data.subjectConfig[this.data.subject] || null;
    },

    /**
     * 格式化截止时间
     */
    formatDeadline(deadline) {
      if (!deadline) return '';

      const now = new Date();
      const deadlineDate = new Date(deadline);
      const diffTime = deadlineDate.getTime() - now.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays < 0) {
        return `已逾期 ${Math.abs(diffDays)} 天`;
      } else if (diffDays === 0) {
        return '今日到期';
      } else if (diffDays === 1) {
        return '明日到期';
      } else if (diffDays <= 7) {
        return `${diffDays} 天后到期`;
      } else {
        return deadline.split(' ')[0]; // 返回日期部分
      }
    },

    /**
     * 检查是否逾期
     */
    isOverdue(deadline) {
      if (!deadline) return false;
      const now = new Date();
      const deadlineDate = new Date(deadline);
      return deadlineDate.getTime() < now.getTime();
    },

    /**
     * 点击卡片事件
     */
    onCardTap(e) {
      if (!this.data.clickable) return;

      this.triggerEvent('tap', {
        title: this.data.title,
        subtitle: this.data.subtitle,
        status: this.data.status,
        deadline: this.data.deadline,
        subject: this.data.subject,
        difficulty: this.data.difficulty,
        progress: this.data.progress
      });
    },

    /**
     * 点击更多按钮事件
     */
    onMoreTap(e) {
      e.stopPropagation(); // 阻止事件冒泡
      this.triggerEvent('more', {
        title: this.data.title,
        subtitle: this.data.subtitle,
        status: this.data.status
      });
    },

    /**
     * 点击状态标签事件
     */
    onStatusTap(e) {
      e.stopPropagation(); // 阻止事件冒泡
      this.triggerEvent('statusTap', {
        status: this.data.status,
        title: this.data.title
      });
    }
  },

  /**
   * 组件生命周期
   */
  lifetimes: {
    /**
     * 组件实例刚刚被创建好时
     */
    created() {
      // 组件实例刚刚被创建好时，不能调用 setData
    },

    /**
     * 组件实例进入页面节点树时
     */
    attached() {
      // 检查截止时间，自动设置逾期状态
      if (this.data.deadline && this.isOverdue(this.data.deadline) && this.data.status !== 'completed') {
        this.setData({
          status: 'overdue'
        });
      }
    },

    /**
     * 组件在视图层布局完成后执行
     */
    ready() {
      // 组件在视图层布局完成后执行
    },

    /**
     * 组件实例被移动到节点树另一个位置时
     */
    moved() {
      // 组件实例被移动到节点树另一个位置时执行
    },

    /**
     * 组件实例被从页面节点树移除时
     */
    detached() {
      // 组件实例被从页面节点树移除时执行
    }
  },

  /**
   * 组件所在页面的生命周期
   */
  pageLifetimes: {
    /**
     * 组件所在的页面被展示时
     */
    show() {
      // 页面被展示时，重新检查逾期状态
      if (this.data.deadline && this.isOverdue(this.data.deadline) && this.data.status !== 'completed') {
        this.setData({
          status: 'overdue'
        });
      }
    },

    /**
     * 组件所在的页面被隐藏时
     */
    hide() {
      // 组件所在的页面被隐藏时执行
    },

    /**
     * 组件所在的页面尺寸变化时
     */
    resize(size) {
      // 组件所在的页面尺寸变化时执行
    }
  }
});
