// components/ocr-progress/index.js - OCR识别进度显示组件

Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 是否显示
    show: {
      type: Boolean,
      value: false,
    },
    // 图片列表及OCR状态
    images: {
      type: Array,
      value: [],
      // 每个图片对象: { id, path, status: 'pending'|'processing'|'success'|'failed', ocrText, confidence, error }
    },
    // 总体进度百分比
    progress: {
      type: Number,
      value: 0,
    },
  },

  /**
   * 组件的初始数据
   */
  data: {
    // 展开的图片ID
    expandedIds: [],
    // 统计数据
    successCount: 0,
    failedCount: 0,
    // 状态图标映射
    statusIcons: {
      pending: '⏳',
      processing: '🔄',
      success: '✓',
      failed: '✕',
    },
    // 状态文本映射
    statusTexts: {
      pending: '等待识别',
      processing: '识别中...',
      success: '识别完成',
      failed: '识别失败',
    },
    // 状态颜色映射
    statusColors: {
      pending: '#909399',
      processing: '#409eff',
      success: '#67c23a',
      failed: '#f56c6c',
    },
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 切换图片展开状态
     */
    toggleExpand(e) {
      const { imageId } = e.currentTarget.dataset;
      const expandedIds = [...this.data.expandedIds];
      const index = expandedIds.indexOf(imageId);

      if (index > -1) {
        expandedIds.splice(index, 1);
      } else {
        expandedIds.push(imageId);
      }

      this.setData({ expandedIds });
    },

    /**
     * 重试OCR识别
     */
    onRetry(e) {
      const { imageId } = e.currentTarget.dataset;

      wx.showModal({
        title: '重试识别',
        content: '确定要重新识别这张图片吗?',
        success: res => {
          if (res.confirm) {
            this.triggerEvent('retry', { imageId });
          }
        },
      });
    },

    /**
     * 删除图片
     */
    onDelete(e) {
      const { imageId } = e.currentTarget.dataset;

      wx.showModal({
        title: '删除图片',
        content: '确定要删除这张图片吗?',
        success: res => {
          if (res.confirm) {
            this.triggerEvent('delete', { imageId });
          }
        },
      });
    },

    /**
     * 预览图片
     */
    onPreview(e) {
      const { imagePath, index } = e.currentTarget.dataset;
      const urls = this.data.images.filter(img => img.path).map(img => img.path);

      wx.previewImage({
        current: imagePath,
        urls: urls,
      });
    },

    /**
     * 复制OCR文本
     */
    onCopyText(e) {
      const { text } = e.currentTarget.dataset;

      wx.setClipboardData({
        data: text,
        success: () => {
          wx.showToast({
            title: '已复制',
            icon: 'success',
          });
        },
      });
    },

    /**
     * 编辑OCR文本
     */
    onEditText(e) {
      const { imageId, text } = e.currentTarget.dataset;

      this.triggerEvent('edit', {
        imageId,
        text,
      });
    },

    /**
     * 关闭进度面板
     */
    onClose() {
      this.triggerEvent('close');
    },

    /**
     * 获取状态图标
     */
    getStatusIcon(status) {
      return this.data.statusIcons[status] || '❓';
    },

    /**
     * 获取状态文本
     */
    getStatusText(status) {
      return this.data.statusTexts[status] || '未知状态';
    },

    /**
     * 获取置信度等级
     */
    getConfidenceLevel(confidence) {
      if (confidence >= 0.9) return { level: '高', color: '#67c23a' };
      if (confidence >= 0.7) return { level: '中', color: '#e6a23c' };
      return { level: '低', color: '#f56c6c' };
    },

    /**
     * 格式化置信度
     */
    formatConfidence(confidence) {
      return (confidence * 100).toFixed(1) + '%';
    },

    /**
     * 计算统计信息
     */
    getStatistics() {
      const images = this.data.images;
      return {
        total: images.length,
        success: images.filter(img => img.status === 'success').length,
        failed: images.filter(img => img.status === 'failed').length,
        processing: images.filter(img => img.status === 'processing').length,
        pending: images.filter(img => img.status === 'pending').length,
      };
    },

    /**
     * 阻止事件冒泡
     */
    stopPropagation() {
      // 阻止点击内容区域时关闭弹窗
    },
  },

  observers: {
    images: function (images) {
      // 自动展开失败的图片
      const failedIds = images.filter(img => img.status === 'failed').map(img => img.id);

      if (failedIds.length > 0) {
        const expandedIds = [...new Set([...this.data.expandedIds, ...failedIds])];
        this.setData({ expandedIds });
      }
    },
  },
});
