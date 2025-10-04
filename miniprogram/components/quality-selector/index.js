// components/quality-selector/index.js - 图片压缩质量选择器

Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 当前选中的质量预设
    value: {
      type: String,
      value: 'standard' // high, standard, low
    },
    // 是否显示选择器
    show: {
      type: Boolean,
      value: false
    }
  },

  /**
   * 组件的初始数据
   */
  data: {
    // 质量预设配置
    presets: [
      {
        id: 'high',
        name: '高清',
        quality: 0.95,
        maxSizeKB: 1024,
        maxWidth: 1920,
        maxHeight: 2560,
        description: '最佳质量,适合保存重要资料',
        icon: '📷',
        estimatedSize: '约500-1000KB',
        color: '#67c23a'
      },
      {
        id: 'standard',
        name: '标准',
        quality: 0.8,
        maxSizeKB: 500,
        maxWidth: 1080,
        maxHeight: 1920,
        description: '平衡质量与大小,推荐使用',
        icon: '📸',
        estimatedSize: '约200-500KB',
        color: '#409eff',
        recommended: true
      },
      {
        id: 'low',
        name: '省流量',
        quality: 0.6,
        maxSizeKB: 200,
        maxWidth: 720,
        maxHeight: 1280,
        description: '适合网络较慢时使用',
        icon: '📱',
        estimatedSize: '约50-200KB',
        color: '#e6a23c'
      }
    ]
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 选择质量预设
     */
    onSelectPreset(e) {
      const { preset } = e.currentTarget.dataset;
      const selectedPreset = this.data.presets.find(p => p.id === preset);
      
      if (selectedPreset) {
        // 触发选择事件
        this.triggerEvent('change', {
          preset: preset,
          config: {
            quality: selectedPreset.quality,
            maxSizeKB: selectedPreset.maxSizeKB,
            maxWidth: selectedPreset.maxWidth,
            maxHeight: selectedPreset.maxHeight
          }
        });

        // 保存用户偏好
        this.savePreference(preset);

        // 提示已选择
        wx.showToast({
          title: `已选择${selectedPreset.name}`,
          icon: 'success',
          duration: 1500
        });
      }
    },

    /**
     * 保存用户偏好到本地存储
     */
    savePreference(preset) {
      try {
        wx.setStorageSync('image_quality_preference', preset);
      } catch (error) {
        console.error('保存质量偏好失败:', error);
      }
    },

    /**
     * 获取用户偏好
     */
    getPreference() {
      try {
        return wx.getStorageSync('image_quality_preference') || 'standard';
      } catch (error) {
        console.error('读取质量偏好失败:', error);
        return 'standard';
      }
    },

    /**
     * 关闭选择器
     */
    onClose() {
      this.triggerEvent('close');
    },

    /**
     * 阻止事件冒泡
     */
    stopPropagation() {
      // 阻止点击内容区域时关闭弹窗
    }
  },

  lifetimes: {
    attached() {
      // 加载用户偏好
      const preference = this.getPreference();
      if (preference !== this.data.value) {
        this.setData({ value: preference });
      }
    }
  }
});
