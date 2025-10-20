Component({
  /**
   * API状态统一展示组件
   * 用于处理加载、错误、空状态等API调用状态
   */
  properties: {
    // 当前状态: loading | error | empty | success
    status: {
      type: String,
      value: 'loading',
    },
    // 加载文本
    loadingText: {
      type: String,
      value: '加载中...',
    },
    // 错误信息
    errorMessage: {
      type: String,
      value: '加载失败',
    },
    // 空状态文本
    emptyText: {
      type: String,
      value: '暂无数据',
    },
    // 空状态图片
    emptyImage: {
      type: String,
      value: 'default',
    },
    // 是否显示重试按钮
    showRetry: {
      type: Boolean,
      value: true,
    },
    // 重试按钮文本
    retryText: {
      type: String,
      value: '重试',
    },
    // 自定义样式类
    customClass: {
      type: String,
      value: '',
    },
    // 最小高度
    minHeight: {
      type: String,
      value: '200rpx',
    },
  },

  data: {
    // 内置的空状态图片映射
    emptyImages: {
      default: 'default',
      search: 'search',
      network: 'network',
      error: 'error',
      history: 'history',
    },
  },

  methods: {
    /**
     * 重试按钮点击事件
     */
    onRetry() {
      this.triggerEvent('retry', {});
    },

    /**
     * 错误详情点击事件
     */
    onErrorDetail() {
      this.triggerEvent('errordetail', {
        message: this.properties.errorMessage,
      });
    },
  },

  observers: {
    status(newStatus) {
      // 状态变化时的处理逻辑
      console.log('API状态变化:', newStatus);
    },
  },
});