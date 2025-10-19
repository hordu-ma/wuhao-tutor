/**
 * 权限不足友好提示系统
 * 提供清晰的错误信息和用户引导
 */

const { roleManager } = require('./role-manager.js');
const { authManager } = require('./auth.js');

/**
 * 权限错误类型配置
 */
const PERMISSION_ERROR_CONFIG = {
  // 未登录错误
  not_logged_in: {
    title: '需要登录',
    icon: '🔐',
    message: '请先登录以使用此功能',
    primaryAction: {
      text: '立即登录',
      type: 'navigate',
      url: '/pages/login/index',
    },
    secondaryAction: {
      text: '稍后再说',
      type: 'close',
    },
    showGuidance: true,
    guidanceSteps: [
      '点击"立即登录"按钮',
      '使用微信账号登录',
      '选择您的角色身份',
      '即可开始使用所有功能',
    ],
  },

  // 角色权限不足
  role_not_allowed: {
    title: '角色权限不足',
    icon: '👤',
    message: '当前角色无法使用此功能',
    primaryAction: {
      text: '切换角色',
      type: 'navigate',
      url: '/pages/role-selection/index',
    },
    secondaryAction: {
      text: '了解更多',
      type: 'info',
    },
    showGuidance: true,
    guidanceSteps: [
      '不同角色拥有不同的功能权限',
      '学生：提交作业、查看成绩、问答互动',
      '家长：查看孩子学习情况、沟通老师',
      '教师：布置作业、批改作业、管理学生',
      '点击"切换角色"来使用相应功能',
    ],
  },

  // 基础权限被拒绝
  permission_denied: {
    title: '权限不足',
    icon: '⚠️',
    message: '您没有执行此操作的权限',
    primaryAction: {
      text: '申请权限',
      type: 'request',
    },
    secondaryAction: {
      text: '返回',
      type: 'close',
    },
    showGuidance: true,
    guidanceSteps: [
      '此功能需要特定权限才能使用',
      '您可以联系管理员申请权限',
      '或检查您的角色是否正确',
      '部分功能仅限特定角色使用',
    ],
  },

  // 条件不满足
  condition_failed: {
    title: '使用条件不满足',
    icon: '📋',
    message: '当前不满足使用条件',
    primaryAction: {
      text: '查看详情',
      type: 'detail',
    },
    secondaryAction: {
      text: '知道了',
      type: 'close',
    },
    showGuidance: false,
  },

  // 时间限制
  time_restriction: {
    title: '时间限制',
    icon: '⏰',
    message: '功能使用时间受限',
    primaryAction: {
      text: '设置提醒',
      type: 'reminder',
    },
    secondaryAction: {
      text: '知道了',
      type: 'close',
    },
    showGuidance: true,
    guidanceSteps: [
      '此功能仅在特定时间段开放',
      '这是为了保障学习作息规律',
      '您可以设置提醒在开放时间使用',
      '合理安排学习时间更有效果',
    ],
  },

  // 次数限制
  daily_limit: {
    title: '使用次数达到上限',
    icon: '📊',
    message: '今日使用次数已达上限',
    primaryAction: {
      text: '查看统计',
      type: 'navigate',
      url: '/pages/statistics/index',
    },
    secondaryAction: {
      text: '明天再来',
      type: 'close',
    },
    showGuidance: true,
    guidanceSteps: [
      '设置使用限制是为了培养良好习惯',
      '适度使用功能更有助于学习效果',
      '明天重置后可以继续使用',
      '您可以查看详细的使用统计',
    ],
  },

  // 资源所有权
  not_owner: {
    title: '无访问权限',
    icon: '🚫',
    message: '您只能操作自己的内容',
    primaryAction: {
      text: '查看我的',
      type: 'navigate_back',
    },
    secondaryAction: {
      text: '知道了',
      type: 'close',
    },
    showGuidance: true,
    guidanceSteps: [
      '为保护隐私安全，您只能访问自己的内容',
      '学生只能查看自己的作业和成绩',
      '家长只能查看自己孩子的信息',
      '这样确保每个人的信息安全',
    ],
  },

  // 网络错误
  network_error: {
    title: '网络连接异常',
    icon: '📡',
    message: '网络连接不稳定，请稍后重试',
    primaryAction: {
      text: '重新尝试',
      type: 'retry',
    },
    secondaryAction: {
      text: '检查网络',
      type: 'network_check',
    },
    showGuidance: true,
    guidanceSteps: [
      '请检查您的网络连接',
      '确保wifi或数据网络正常',
      '可以尝试切换网络环境',
      '或稍后再试',
    ],
  },

  // 服务器错误
  server_error: {
    title: '服务暂时不可用',
    icon: '🔧',
    message: '服务器正在维护，请稍后重试',
    primaryAction: {
      text: '稍后重试',
      type: 'close',
    },
    secondaryAction: {
      text: '反馈问题',
      type: 'feedback',
    },
    showGuidance: true,
    guidanceSteps: [
      '服务器可能正在进行维护',
      '这是为了提供更好的服务体验',
      '请稍后再试或反馈问题',
      '我们会尽快恢复正常服务',
    ],
  },
};

/**
 * 友好提示管理器
 */
class FriendlyPermissionDialog {
  constructor() {
    this.currentDialog = null;
    this.dialogQueue = [];
    this.isShowing = false;
  }

  /**
   * 显示权限错误提示
   * @param {string} errorType - 错误类型
   * @param {Object} context - 上下文信息
   * @param {Object} options - 额外选项
   */
  async showPermissionError(errorType, context = {}, options = {}) {
    try {
      console.log(`[FriendlyDialog] 显示权限错误提示: ${errorType}`, context);

      // 获取错误配置
      const errorConfig = this.getErrorConfig(errorType, context);
      if (!errorConfig) {
        console.warn(`[FriendlyDialog] 未找到错误配置: ${errorType}`);
        this.showFallbackError(context.message || '操作失败');
        return;
      }

      // 如果有对话框正在显示，加入队列
      if (this.isShowing) {
        this.dialogQueue.push({ errorType, context, options });
        return;
      }

      // 显示对话框
      await this.displayDialog(errorConfig, context, options);
    } catch (error) {
      console.error(`[FriendlyDialog] 显示错误提示失败:`, error);
      this.showFallbackError('系统错误，请稍后重试');
    }
  }

  /**
   * 获取错误配置
   * @param {string} errorType - 错误类型
   * @param {Object} context - 上下文
   * @returns {Object} 错误配置
   */
  getErrorConfig(errorType, context) {
    let config = PERMISSION_ERROR_CONFIG[errorType];
    if (!config) {
      return null;
    }

    // 克隆配置避免修改原始配置
    config = JSON.parse(JSON.stringify(config));

    // 处理动态内容
    if (context.message) {
      config.message = context.message;
    }

    if (context.requiredRoles) {
      config.requiredRoles = context.requiredRoles;
      config.userRole = context.userRole;
    }

    if (context.condition) {
      config.failedCondition = context.condition;
    }

    return config;
  }

  /**
   * 显示对话框
   * @param {Object} config - 错误配置
   * @param {Object} context - 上下文
   * @param {Object} options - 选项
   */
  async displayDialog(config, context, options) {
    this.isShowing = true;
    this.currentDialog = { config, context, options };

    // 准备对话框数据
    const dialogData = this.prepareDialogData(config, context, options);

    // 显示对话框
    return new Promise(resolve => {
      wx.showModal({
        title: dialogData.title,
        content: dialogData.content,
        confirmText: dialogData.confirmText,
        cancelText: dialogData.cancelText,
        showCancel: !!dialogData.cancelText,
        success: async res => {
          if (res.confirm) {
            await this.handlePrimaryAction(config.primaryAction, context);
          } else if (res.cancel) {
            await this.handleSecondaryAction(config.secondaryAction, context);
          }

          this.completeDialog(resolve);
        },
        fail: () => {
          this.completeDialog(resolve);
        },
      });
    });
  }

  /**
   * 准备对话框数据
   * @param {Object} config - 错误配置
   * @param {Object} context - 上下文
   * @param {Object} options - 选项
   * @returns {Object} 对话框数据
   */
  prepareDialogData(config, context, options) {
    let content = config.message;

    // 添加详细信息
    if (config.requiredRoles && config.userRole) {
      const roleNames = {
        student: '学生',
        parent: '家长',
        teacher: '教师',
      };

      const requiredRoleNames = config.requiredRoles
        .map(role => roleNames[role] || role)
        .join('、');

      content += `\n\n此功能仅限${requiredRoleNames}使用`;
    }

    // 添加引导信息
    if (config.showGuidance && config.guidanceSteps && !options.hideGuidance) {
      content += '\n\n' + config.guidanceSteps.join('\n');
    }

    return {
      title: `${config.icon} ${config.title}`,
      content: content,
      confirmText: config.primaryAction?.text || '确定',
      cancelText: config.secondaryAction?.text || null,
    };
  }

  /**
   * 处理主要操作
   * @param {Object} action - 操作配置
   * @param {Object} context - 上下文
   */
  async handlePrimaryAction(action, context) {
    if (!action) return;

    try {
      switch (action.type) {
        case 'navigate':
          wx.navigateTo({
            url: action.url,
            fail: () => {
              wx.switchTab({ url: action.url });
            },
          });
          break;

        case 'navigate_back':
          wx.navigateBack({
            delta: 1,
            fail: () => {
              wx.switchTab({ url: '/pages/index/index' });
            },
          });
          break;

        case 'request':
          await this.showPermissionRequestDialog(context);
          break;

        case 'detail':
          await this.showDetailDialog(context);
          break;

        case 'reminder':
          await this.showReminderDialog(context);
          break;

        case 'retry':
          if (context.retryCallback) {
            await context.retryCallback();
          }
          break;

        case 'network_check':
          await this.showNetworkCheckDialog();
          break;

        case 'feedback':
          await this.showFeedbackDialog(context);
          break;

        case 'info':
          await this.showInfoDialog(context);
          break;

        case 'close':
        default:
          // 无需特殊处理
          break;
      }
    } catch (error) {
      console.error('[FriendlyDialog] 处理主要操作失败:', error);
    }
  }

  /**
   * 处理次要操作
   * @param {Object} action - 操作配置
   * @param {Object} context - 上下文
   */
  async handleSecondaryAction(action, context) {
    if (!action) return;

    try {
      switch (action.type) {
        case 'info':
          await this.showInfoDialog(context);
          break;

        case 'feedback':
          await this.showFeedbackDialog(context);
          break;

        case 'close':
        default:
          // 无需特殊处理
          break;
      }
    } catch (error) {
      console.error('[FriendlyDialog] 处理次要操作失败:', error);
    }
  }

  /**
   * 显示权限申请对话框
   */
  async showPermissionRequestDialog(context) {
    const currentUser = authManager.getCurrentUser();
    const userRole = await authManager.getUserRole();

    wx.showModal({
      title: '权限申请',
      content: `如需使用此功能，请联系管理员申请权限。\n\n您的角色：${this.getRoleName(userRole)}\n用户ID：${currentUser?.id || '未知'}`,
      confirmText: '复制信息',
      cancelText: '知道了',
      success: res => {
        if (res.confirm) {
          wx.setClipboardData({
            data: `权限申请\n角色：${userRole}\n用户ID：${currentUser?.id}\n功能：${context.feature || '未知'}`,
            success: () => {
              wx.showToast({
                title: '信息已复制到剪贴板',
                icon: 'success',
              });
            },
          });
        }
      },
    });
  }

  /**
   * 显示详情对话框
   */
  async showDetailDialog(context) {
    let detail = '详细信息：\n';

    if (context.condition) {
      detail += `失败条件：${context.condition}\n`;
    }

    if (context.requirement) {
      detail += `使用要求：${context.requirement}\n`;
    }

    wx.showModal({
      title: '详细信息',
      content: detail,
      showCancel: false,
      confirmText: '知道了',
    });
  }

  /**
   * 显示提醒设置对话框
   */
  async showReminderDialog(context) {
    wx.showModal({
      title: '设置提醒',
      content: '是否在功能开放时间段提醒您？',
      confirmText: '设置提醒',
      cancelText: '暂不设置',
      success: res => {
        if (res.confirm) {
          // 这里可以实现提醒设置逻辑
          wx.showToast({
            title: '提醒设置功能开发中',
            icon: 'none',
          });
        }
      },
    });
  }

  /**
   * 显示网络检查对话框
   */
  async showNetworkCheckDialog() {
    wx.showModal({
      title: '网络检查',
      content:
        '网络检查步骤：\n1. 检查WiFi连接\n2. 检查数据网络\n3. 尝试访问其他网站\n4. 重启网络连接',
      showCancel: false,
      confirmText: '知道了',
    });
  }

  /**
   * 显示反馈对话框
   */
  async showFeedbackDialog(context) {
    wx.showModal({
      title: '问题反馈',
      content: '如需反馈问题，请前往设置页面的"意见反馈"功能。',
      confirmText: '前往反馈',
      cancelText: '知道了',
      success: res => {
        if (res.confirm) {
          wx.navigateTo({
            url: '/pages/feedback/index',
            fail: () => {
              wx.showToast({
                title: '反馈页面开发中',
                icon: 'none',
              });
            },
          });
        }
      },
    });
  }

  /**
   * 显示信息对话框
   */
  async showInfoDialog(context) {
    const roleInfo = this.getRolePermissionInfo();

    wx.showModal({
      title: '角色权限说明',
      content: roleInfo,
      showCancel: false,
      confirmText: '知道了',
    });
  }

  /**
   * 完成对话框
   */
  completeDialog(resolve) {
    this.isShowing = false;
    this.currentDialog = null;

    if (resolve) {
      resolve();
    }

    // 处理队列中的下一个对话框
    if (this.dialogQueue.length > 0) {
      const next = this.dialogQueue.shift();
      setTimeout(() => {
        this.showPermissionError(next.errorType, next.context, next.options);
      }, 100);
    }
  }

  /**
   * 显示回退错误提示
   */
  showFallbackError(message) {
    wx.showToast({
      title: message || '操作失败',
      icon: 'none',
      duration: 3000,
    });
  }

  /**
   * 获取角色名称
   */
  getRoleName(role) {
    const roleNames = {
      student: '学生',
      parent: '家长',
      teacher: '教师',
    };
    return roleNames[role] || role;
  }

  /**
   * 获取角色权限信息
   */
  getRolePermissionInfo() {
    return `角色权限说明：

学生角色：
• 提交和查看作业
• 使用问答功能
• 查看学习报告
• 管理个人信息

家长角色：
• 查看孩子学习情况
• 与教师沟通交流
• 查看学习报告
• 管理个人信息

教师角色：
• 布置和批改作业
• 管理学生信息
• 查看教学数据
• 使用所有教学工具

如需切换角色，请前往角色选择页面。`;
  }

  /**
   * 清空对话框队列
   */
  clearQueue() {
    this.dialogQueue = [];
    console.log('[FriendlyDialog] 对话框队列已清空');
  }

  /**
   * 获取当前状态
   */
  getStatus() {
    return {
      isShowing: this.isShowing,
      queueLength: this.dialogQueue.length,
      currentDialog: this.currentDialog
        ? {
            errorType: this.currentDialog.config.title,
            message: this.currentDialog.config.message,
          }
        : null,
    };
  }
}

// 创建单例实例
const friendlyPermissionDialog = new FriendlyPermissionDialog();

module.exports = {
  friendlyPermissionDialog,
  FriendlyPermissionDialog,
  PERMISSION_ERROR_CONFIG,
};
