// utils/error-toast.js
// 全局错误提示工具

/**
 * 统一错误提示类
 */
class ErrorToast {
  constructor() {
    // 错误类型映射
    this.errorMessages = {
      'NETWORK_ERROR': '网络连接异常，请检查网络后重试',
      'TIMEOUT_ERROR': '请求超时，请稍后重试',
      'AUTH_ERROR': '登录已过期，请重新登录',
      'PERMISSION_ERROR': '权限不足，无法访问',
      'VALIDATION_ERROR': '输入信息有误，请检查后重试',
      'BUSINESS_ERROR': '操作失败，请重试',
      'SERVER_ERROR': '服务器繁忙，请稍后重试',
      'UNKNOWN_ERROR': '未知错误，请重试'
    };

    // 当前显示的toast
    this.currentToast = null;
  }

  /**
   * 显示错误提示
   */
  show(error, options = {}) {
    let message = '';
    let icon = 'error';
    let duration = 3000;

    // 处理不同类型的错误
    if (typeof error === 'string') {
      message = error;
    } else if (error && typeof error === 'object') {
      // 错误对象
      if (error.code && this.errorMessages[error.code]) {
        message = this.errorMessages[error.code];
      } else if (error.message) {
        message = error.message;
      } else if (error.errMsg) {
        message = this.parseWxError(error.errMsg);
      } else {
        message = this.errorMessages['UNKNOWN_ERROR'];
      }
    } else {
      message = this.errorMessages['UNKNOWN_ERROR'];
    }

    // 处理特殊错误类型
    if (error && error.code === 'AUTH_ERROR') {
      icon = 'error';
      duration = 2000;
      // 延迟跳转到登录页
      setTimeout(() => {
        wx.redirectTo({
          url: '/pages/login/index'
        });
      }, duration);
    }

    // 合并选项
    const toastOptions = {
      title: message,
      icon: icon,
      duration: duration,
      mask: true,
      ...options
    };

    // 显示toast
    wx.showToast(toastOptions);

    return {
      message,
      duration
    };
  }

  /**
   * 解析微信错误信息
   */
  parseWxError(errMsg) {
    if (errMsg.includes('fail')) {
      if (errMsg.includes('network')) {
        return this.errorMessages['NETWORK_ERROR'];
      } else if (errMsg.includes('timeout')) {
        return this.errorMessages['TIMEOUT_ERROR'];
      } else if (errMsg.includes('cancel')) {
        return '操作已取消';
      } else if (errMsg.includes('auth')) {
        return this.errorMessages['AUTH_ERROR'];
      }
    }
    return errMsg.replace('fail ', '').replace('ok ', '');
  }

  /**
   * 显示成功提示
   */
  success(message, options = {}) {
    const toastOptions = {
      title: message,
      icon: 'success',
      duration: 2000,
      mask: true,
      ...options
    };

    wx.showToast(toastOptions);

    return {
      message,
      duration: toastOptions.duration
    };
  }

  /**
   * 显示加载提示
   */
  loading(message = '加载中...', options = {}) {
    const toastOptions = {
      title: message,
      icon: 'loading',
      duration: 10000, // 长时间显示
      mask: true,
      ...options
    };

    wx.showToast(toastOptions);
    this.currentToast = 'loading';

    return {
      message,
      hide: () => this.hide()
    };
  }

  /**
   * 隐藏当前提示
   */
  hide() {
    wx.hideToast();
    this.currentToast = null;
  }

  /**
   * 显示确认对话框
   */
  confirm(title, content, options = {}) {
    return new Promise((resolve, reject) => {
      const modalOptions = {
        title: title || '提示',
        content: content || '',
        showCancel: true,
        cancelText: '取消',
        confirmText: '确定',
        ...options,
        success: (res) => {
          if (res.confirm) {
            resolve(true);
          } else if (res.cancel) {
            resolve(false);
          }
        },
        fail: (error) => {
          reject(error);
        }
      };

      wx.showModal(modalOptions);
    });
  }

  /**
   * 显示操作菜单
   */
  actionSheet(itemList, options = {}) {
    return new Promise((resolve, reject) => {
      const actionOptions = {
        itemList,
        itemColor: '#000000',
        ...options,
        success: (res) => {
          resolve(res.tapIndex);
        },
        fail: (error) => {
          if (error.errMsg && error.errMsg.includes('cancel')) {
            resolve(-1); // 用户取消
          } else {
            reject(error);
          }
        }
      };

      wx.showActionSheet(actionOptions);
    });
  }

  /**
   * 网络错误处理
   */
  handleNetworkError(error, retryCallback = null) {
    const message = this.parseWxError(error.errMsg || error.message || '网络错误');
    
    if (retryCallback) {
      this.confirm('网络错误', `${message}，是否重试？`, {
        confirmText: '重试',
        cancelText: '取消'
      }).then((retry) => {
        if (retry) {
          retryCallback();
        }
      });
    } else {
      this.show(message);
    }
  }

  /**
   * 权限错误处理
   */
  handlePermissionError(permission) {
    let message = '需要获取相关权限才能继续使用';
    
    switch (permission) {
      case 'scope.userInfo':
        message = '需要获取您的微信信息才能继续使用';
        break;
      case 'scope.camera':
        message = '需要相机权限才能拍照';
        break;
      case 'scope.writePhotosAlbum':
        message = '需要相册权限才能保存图片';
        break;
      case 'scope.record':
        message = '需要录音权限才能录制语音';
        break;
    }

    this.confirm('权限申请', `${message}，是否前往设置开启？`, {
      confirmText: '去设置',
      cancelText: '取消'
    }).then((goSetting) => {
      if (goSetting) {
        wx.openSetting();
      }
    });
  }
}

// 创建单例实例
const errorToast = new ErrorToast();

// 导出
module.exports = {
  ErrorToast,
  errorToast,
  
  // 便捷方法
  showError: (error, options) => errorToast.show(error, options),
  showSuccess: (message, options) => errorToast.success(message, options),
  showLoading: (message, options) => errorToast.loading(message, options),
  hideToast: () => errorToast.hide(),
  confirm: (title, content, options) => errorToast.confirm(title, content, options),
  actionSheet: (itemList, options) => errorToast.actionSheet(itemList, options),
  handleNetworkError: (error, retryCallback) => errorToast.handleNetworkError(error, retryCallback),
  handlePermissionError: (permission) => errorToast.handlePermissionError(permission)
};