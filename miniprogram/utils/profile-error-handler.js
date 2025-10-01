// utils/profile-error-handler.js - 个人信息模块错误处理器

const { errorToast } = require('./error-toast.js');
const { networkMonitor } = require('./network-monitor.js');
const { authManager } = require('./auth.js');

/**
 * 错误类型枚举
 */
const ProfileErrorType = {
  NETWORK_ERROR: 'network_error',
  AUTH_ERROR: 'auth_error', 
  VALIDATION_ERROR: 'validation_error',
  UPLOAD_ERROR: 'upload_error',
  SYNC_ERROR: 'sync_error',
  PERMISSION_ERROR: 'permission_error',
  SERVER_ERROR: 'server_error',
  TIMEOUT_ERROR: 'timeout_error',
  UNKNOWN_ERROR: 'unknown_error'
};

/**
 * 重试策略
 */
const RetryStrategy = {
  IMMEDIATE: 'immediate',
  EXPONENTIAL_BACKOFF: 'exponential_backoff',
  LINEAR_DELAY: 'linear_delay',
  MANUAL: 'manual'
};

/**
 * 个人信息错误处理器
 */
class ProfileErrorHandler {
  constructor() {
    this.retryAttempts = new Map(); // 记录重试次数
    this.maxRetries = 3;
    this.baseDelay = 1000; // 基础延迟时间(ms)
    this.maxDelay = 10000; // 最大延迟时间(ms)
    
    // 错误统计
    this.errorStats = {
      totalErrors: 0,
      networkErrors: 0,
      authErrors: 0,
      validationErrors: 0,
      uploadErrors: 0,
      syncErrors: 0
    };
  }

  /**
   * 处理用户信息更新错误
   */
  async handleUserInfoUpdateError(error, context = {}) {
    const errorType = this.classifyError(error);
    const errorKey = `userInfo_${context.operation || 'update'}`;
    
    this.recordError(errorType);
    
    console.error('用户信息更新错误:', {
      type: errorType,
      error,
      context
    });

    switch (errorType) {
      case ProfileErrorType.NETWORK_ERROR:
        return this.handleNetworkError(error, errorKey, context);
        
      case ProfileErrorType.AUTH_ERROR:
        return this.handleAuthError(error, context);
        
      case ProfileErrorType.VALIDATION_ERROR:
        return this.handleValidationError(error, context);
        
      case ProfileErrorType.SERVER_ERROR:
        return this.handleServerError(error, errorKey, context);
        
      case ProfileErrorType.TIMEOUT_ERROR:
        return this.handleTimeoutError(error, errorKey, context);
        
      default:
        return this.handleUnknownError(error, context);
    }
  }

  /**
   * 处理头像上传错误
   */
  async handleAvatarUploadError(error, context = {}) {
    const errorType = this.classifyError(error);
    const errorKey = 'avatar_upload';
    
    this.recordError(ProfileErrorType.UPLOAD_ERROR);
    
    console.error('头像上传错误:', {
      type: errorType,
      error,
      context
    });

    switch (errorType) {
      case ProfileErrorType.NETWORK_ERROR:
        return this.handleNetworkError(error, errorKey, {
          ...context,
          action: 'uploadAvatar'
        });
        
      case ProfileErrorType.VALIDATION_ERROR:
        return this.handleUploadValidationError(error, context);
        
      case ProfileErrorType.SERVER_ERROR:
        if (error.statusCode === 413) {
          return this.handleFileTooLargeError(error, context);
        }
        return this.handleServerError(error, errorKey, context);
        
      default:
        return this.handleUploadGeneralError(error, context);
    }
  }

  /**
   * 处理同步错误
   */
  async handleSyncError(error, context = {}) {
    const errorType = this.classifyError(error);
    const errorKey = `sync_${context.syncType || 'general'}`;
    
    this.recordError(ProfileErrorType.SYNC_ERROR);
    
    console.error('同步错误:', {
      type: errorType,
      error,
      context
    });

    // 同步错误通常不需要直接显示给用户
    if (context.silent !== false) {
      return { 
        success: false, 
        silent: true,
        needsRetry: this.shouldRetry(errorKey)
      };
    }

    switch (errorType) {
      case ProfileErrorType.NETWORK_ERROR:
        return this.handleNetworkError(error, errorKey, {
          ...context,
          silentRetry: true
        });
        
      case ProfileErrorType.AUTH_ERROR:
        return this.handleAuthError(error, { ...context, silent: true });
        
      default:
        return { 
          success: false, 
          silent: true,
          needsRetry: false
        };
    }
  }

  /**
   * 网络错误处理
   */
  async handleNetworkError(error, errorKey, context = {}) {
    const networkStatus = networkMonitor.getCurrentStatus();
    
    if (!networkStatus.isConnected) {
      this.showNetworkErrorDialog();
      return { 
        success: false, 
        needsRetry: false,
        reason: 'no_network'
      };
    }

    if (this.shouldRetry(errorKey)) {
      const retryResult = await this.attemptRetry(errorKey, context);
      if (retryResult) {
        return retryResult;
      }
    }

    errorToast.show('网络异常，请检查网络连接后重试');
    return { 
      success: false, 
      needsRetry: false,
      reason: 'network_retry_failed'
    };
  }

  /**
   * 认证错误处理
   */
  async handleAuthError(error, context = {}) {
    console.log('处理认证错误');

    try {
      // 尝试刷新Token
      await authManager.refreshToken();
      
      if (context.retryFunction) {
        // 如果提供了重试函数，执行重试
        const retryResult = await context.retryFunction();
        return { success: true, data: retryResult };
      }
      
      return { 
        success: false, 
        needsLogin: true,
        reason: 'auth_refresh_success'
      };
      
    } catch (refreshError) {
      console.error('Token刷新失败:', refreshError);
      
      if (!context.silent) {
        this.showAuthErrorDialog();
      }
      
      return { 
        success: false, 
        needsLogin: true,
        reason: 'auth_refresh_failed'
      };
    }
  }

  /**
   * 验证错误处理
   */
  handleValidationError(error, context = {}) {
    let message = '输入信息有误，请检查后重试';
    
    if (error.message) {
      message = error.message;
    } else if (error.data && error.data.message) {
      message = error.data.message;
    }

    errorToast.show(message);
    
    return { 
      success: false, 
      needsRetry: false,
      reason: 'validation_failed',
      message
    };
  }

  /**
   * 服务器错误处理
   */
  async handleServerError(error, errorKey, context = {}) {
    const statusCode = error.statusCode || error.status;
    
    let message = '服务器异常，请稍后重试';
    let needsRetry = false;

    switch (statusCode) {
      case 500:
        message = '服务器内部错误，请稍后重试';
        needsRetry = this.shouldRetry(errorKey);
        break;
        
      case 502:
      case 503:
      case 504:
        message = '服务暂时不可用，请稍后重试';
        needsRetry = this.shouldRetry(errorKey);
        break;
        
      case 429:
        message = '操作过于频繁，请稍后再试';
        needsRetry = false;
        break;
        
      default:
        if (error.message) {
          message = error.message;
        }
    }

    if (needsRetry) {
      const retryResult = await this.attemptRetry(errorKey, context);
      if (retryResult) {
        return retryResult;
      }
    }

    errorToast.show(message);
    return { 
      success: false, 
      needsRetry: false,
      reason: 'server_error',
      statusCode
    };
  }

  /**
   * 超时错误处理
   */
  async handleTimeoutError(error, errorKey, context = {}) {
    if (this.shouldRetry(errorKey)) {
      const retryResult = await this.attemptRetry(errorKey, context);
      if (retryResult) {
        return retryResult;
      }
    }

    errorToast.show('请求超时，请检查网络后重试');
    return { 
      success: false, 
      needsRetry: false,
      reason: 'timeout'
    };
  }

  /**
   * 文件过大错误处理
   */
  handleFileTooLargeError(error, context = {}) {
    errorToast.show('文件大小超过限制，请选择较小的图片');
    return { 
      success: false, 
      needsRetry: false,
      reason: 'file_too_large'
    };
  }

  /**
   * 上传验证错误处理
   */
  handleUploadValidationError(error, context = {}) {
    let message = '文件格式不支持';
    
    if (error.message) {
      message = error.message;
    }

    errorToast.show(message);
    return { 
      success: false, 
      needsRetry: false,
      reason: 'upload_validation_failed'
    };
  }

  /**
   * 上传通用错误处理
   */
  handleUploadGeneralError(error, context = {}) {
    errorToast.show('上传失败，请重新选择文件');
    return { 
      success: false, 
      needsRetry: false,
      reason: 'upload_general_error'
    };
  }

  /**
   * 未知错误处理
   */
  handleUnknownError(error, context = {}) {
    console.error('未知错误:', error);
    errorToast.show('操作失败，请稍后重试');
    return { 
      success: false, 
      needsRetry: false,
      reason: 'unknown_error'
    };
  }

  /**
   * 分类错误类型
   */
  classifyError(error) {
    if (!error) {
      return ProfileErrorType.UNKNOWN_ERROR;
    }

    // 检查状态码
    const statusCode = error.statusCode || error.status;
    if (statusCode) {
      if (statusCode === 401 || statusCode === 403) {
        return ProfileErrorType.AUTH_ERROR;
      }
      if (statusCode === 422 || statusCode === 400) {
        return ProfileErrorType.VALIDATION_ERROR;
      }
      if (statusCode >= 500) {
        return ProfileErrorType.SERVER_ERROR;
      }
    }

    // 检查错误消息
    const errorMsg = error.errMsg || error.message || '';
    if (errorMsg.includes('timeout') || errorMsg.includes('请求超时')) {
      return ProfileErrorType.TIMEOUT_ERROR;
    }
    if (errorMsg.includes('network') || errorMsg.includes('网络')) {
      return ProfileErrorType.NETWORK_ERROR;
    }
    if (errorMsg.includes('unauthorized') || errorMsg.includes('登录')) {
      return ProfileErrorType.AUTH_ERROR;
    }

    // 检查错误类型
    const errorType = error.type;
    if (errorType) {
      switch (errorType) {
        case 'NETWORK_ERROR':
          return ProfileErrorType.NETWORK_ERROR;
        case 'AUTH_ERROR':
          return ProfileErrorType.AUTH_ERROR;
        case 'VALIDATION_ERROR':
          return ProfileErrorType.VALIDATION_ERROR;
        case 'SERVER_ERROR':
          return ProfileErrorType.SERVER_ERROR;
        case 'TIMEOUT_ERROR':
          return ProfileErrorType.TIMEOUT_ERROR;
      }
    }

    return ProfileErrorType.UNKNOWN_ERROR;
  }

  /**
   * 是否应该重试
   */
  shouldRetry(errorKey) {
    const attempts = this.retryAttempts.get(errorKey) || 0;
    return attempts < this.maxRetries;
  }

  /**
   * 尝试重试
   */
  async attemptRetry(errorKey, context = {}) {
    const attempts = this.retryAttempts.get(errorKey) || 0;
    const newAttempts = attempts + 1;
    
    this.retryAttempts.set(errorKey, newAttempts);
    
    // 计算延迟时间
    const delay = this.calculateRetryDelay(newAttempts, context.retryStrategy);
    
    console.log(`第${newAttempts}次重试 ${errorKey}，延迟${delay}ms`);
    
    if (!context.silentRetry) {
      wx.showLoading({
        title: `重试中(${newAttempts}/${this.maxRetries})`,
        mask: true
      });
    }

    await this.delay(delay);
    
    try {
      if (context.retryFunction) {
        const result = await context.retryFunction();
        
        if (!context.silentRetry) {
          wx.hideLoading();
        }
        
        // 重试成功，清除重试记录
        this.retryAttempts.delete(errorKey);
        
        return { 
          success: true, 
          data: result,
          retryAttempts: newAttempts
        };
      }
    } catch (retryError) {
      if (!context.silentRetry) {
        wx.hideLoading();
      }
      
      console.error(`重试${newAttempts}失败:`, retryError);
      
      if (newAttempts >= this.maxRetries) {
        this.retryAttempts.delete(errorKey);
      }
    }
    
    return null;
  }

  /**
   * 计算重试延迟时间
   */
  calculateRetryDelay(attempts, strategy = RetryStrategy.EXPONENTIAL_BACKOFF) {
    switch (strategy) {
      case RetryStrategy.IMMEDIATE:
        return 0;
        
      case RetryStrategy.LINEAR_DELAY:
        return Math.min(attempts * this.baseDelay, this.maxDelay);
        
      case RetryStrategy.EXPONENTIAL_BACKOFF:
        return Math.min(Math.pow(2, attempts - 1) * this.baseDelay, this.maxDelay);
        
      default:
        return this.baseDelay;
    }
  }

  /**
   * 延迟函数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 记录错误统计
   */
  recordError(errorType) {
    this.errorStats.totalErrors++;
    
    switch (errorType) {
      case ProfileErrorType.NETWORK_ERROR:
        this.errorStats.networkErrors++;
        break;
      case ProfileErrorType.AUTH_ERROR:
        this.errorStats.authErrors++;
        break;
      case ProfileErrorType.VALIDATION_ERROR:
        this.errorStats.validationErrors++;
        break;
      case ProfileErrorType.UPLOAD_ERROR:
        this.errorStats.uploadErrors++;
        break;
      case ProfileErrorType.SYNC_ERROR:
        this.errorStats.syncErrors++;
        break;
    }
  }

  /**
   * 显示网络错误对话框
   */
  showNetworkErrorDialog() {
    wx.showModal({
      title: '网络连接异常',
      content: '当前网络不可用，请检查网络设置后重试',
      showCancel: false,
      confirmText: '知道了'
    });
  }

  /**
   * 显示认证错误对话框
   */
  showAuthErrorDialog() {
    wx.showModal({
      title: '登录已过期',
      content: '您的登录状态已过期，请重新登录',
      showCancel: false,
      confirmText: '重新登录',
      success: () => {
        wx.redirectTo({
          url: '/pages/login/index'
        });
      }
    });
  }

  /**
   * 获取错误统计
   */
  getErrorStats() {
    return { ...this.errorStats };
  }

  /**
   * 重置错误统计
   */
  resetErrorStats() {
    this.errorStats = {
      totalErrors: 0,
      networkErrors: 0,
      authErrors: 0,
      validationErrors: 0,
      uploadErrors: 0,
      syncErrors: 0
    };
  }

  /**
   * 清除重试记录
   */
  clearRetryAttempts() {
    this.retryAttempts.clear();
  }
}

// 创建单例实例
const profileErrorHandler = new ProfileErrorHandler();

module.exports = {
  profileErrorHandler,
  ProfileErrorHandler,
  ProfileErrorType,
  RetryStrategy
};