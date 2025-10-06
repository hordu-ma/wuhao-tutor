const { errorHandler } = require('../../utils/error-handler.js');

Component({
  /**
   * 错误边界组件
   * 用于统一处理组件错误和API错误
   */
  properties: {
    // 是否开启错误捕获
    enableCapture: {
      type: Boolean,
      value: true,
    },
    // 错误展示方式: toast | dialog | inline
    errorDisplay: {
      type: String,
      value: 'toast',
    },
    // 自定义错误处理器
    customHandler: {
      type: String,
      value: '',
    },
    // 是否显示错误详情
    showDetails: {
      type: Boolean,
      value: false,
    },
  },

  data: {
    hasError: false,
    errorInfo: null,
    showErrorDialog: false,
  },

  lifetimes: {
    attached() {
      // 设置全局错误监听
      if (this.properties.enableCapture) {
        this.setupErrorCapture();
      }
    },

    detached() {
      // 清理错误监听
      this.removeErrorCapture();
    },
  },

  methods: {
    /**
     * 设置错误捕获
     */
    setupErrorCapture() {
      // 监听小程序错误
      wx.onError(this.handleError.bind(this));
      
      // 监听未处理的Promise rejection
      wx.onUnhandledRejection(this.handleRejection.bind(this));
    },

    /**
     * 移除错误捕获
     */
    removeErrorCapture() {
      wx.offError(this.handleError);
      wx.offUnhandledRejection(this.handleRejection);
    },

    /**
     * 处理JavaScript错误
     */
    handleError(error) {
      console.error('错误边界捕获到错误:', error);
      
      const errorInfo = {
        type: 'javascript',
        message: error.message || '未知错误',
        stack: error.stack || '',
        timestamp: new Date().toISOString(),
      };

      this.processError(errorInfo);
    },

    /**
     * 处理Promise rejection
     */
    handleRejection(event) {
      console.error('错误边界捕获到Promise rejection:', event);
      
      const errorInfo = {
        type: 'promise',
        message: event.reason?.message || '异步操作失败',
        reason: event.reason,
        timestamp: new Date().toISOString(),
      };

      this.processError(errorInfo);
    },

    /**
     * 处理API错误
     */
    handleApiError(error) {
      const errorInfo = {
        type: 'api',
        code: error.code || 'UNKNOWN_ERROR',
        message: error.message || 'API调用失败',
        details: error.details || {},
        timestamp: new Date().toISOString(),
      };

      this.processError(errorInfo);
    },

    /**
     * 统一错误处理流程
     */
    processError(errorInfo) {
      // 更新组件状态
      this.setData({
        hasError: true,
        errorInfo,
      });

      // 上报错误
      this.reportError(errorInfo);

      // 显示错误信息
      this.displayError(errorInfo);

      // 触发错误事件
      this.triggerEvent('error', errorInfo);
    },

    /**
     * 显示错误信息
     */
    displayError(errorInfo) {
      const { errorDisplay } = this.properties;
      
      switch (errorDisplay) {
        case 'toast':
          this.showErrorToast(errorInfo);
          break;
        case 'dialog':
          this.showErrorDialog(errorInfo);
          break;
        case 'inline':
          // 内联显示由父组件处理
          break;
        default:
          this.showErrorToast(errorInfo);
      }
    },

    /**
     * 显示错误Toast
     */
    showErrorToast(errorInfo) {
      wx.showToast({
        title: errorInfo.message,
        icon: 'error',
        duration: 3000,
      });
    },

    /**
     * 显示错误对话框
     */
    showErrorDialog(errorInfo) {
      this.setData({ showErrorDialog: true });
      
      const content = this.properties.showDetails 
        ? `${errorInfo.message}\n\n错误码: ${errorInfo.code || 'N/A'}`
        : errorInfo.message;

      wx.showModal({
        title: '操作失败',
        content,
        showCancel: true,
        cancelText: '忽略',
        confirmText: '重试',
        success: (res) => {
          this.setData({ showErrorDialog: false });
          
          if (res.confirm) {
            this.triggerEvent('retry', errorInfo);
          }
        },
      });
    },

    /**
     * 上报错误信息
     */
    reportError(errorInfo) {
      try {
        // 使用错误处理工具上报
        errorHandler.report(errorInfo);
      } catch (reportError) {
        console.warn('错误上报失败:', reportError);
      }
    },

    /**
     * 重置错误状态
     */
    resetError() {
      this.setData({
        hasError: false,
        errorInfo: null,
        showErrorDialog: false,
      });
    },

    /**
     * 手动触发错误处理
     */
    catchError(error) {
      if (error?.code && error?.message) {
        // API错误
        this.handleApiError(error);
      } else {
        // 其他错误
        this.handleError(error);
      }
    },
  },

  /**
   * 对外暴露的方法
   */
  export() {
    return {
      catchError: this.catchError.bind(this),
      resetError: this.resetError.bind(this),
    };
  },
});