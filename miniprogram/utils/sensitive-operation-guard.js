/**
 * 敏感操作二次确认机制
 * 为危险操作添加用户确认流程
 */

const { permissionManager } = require('./permission-manager.js');
const { roleManager } = require('./role-manager.js');

/**
 * 敏感操作配置
 */
const SENSITIVE_OPERATION_CONFIG = {
  // 作业相关敏感操作
  'homework.delete': {
    title: '删除作业',
    message: '确认要删除这个作业吗？删除后将无法恢复。',
    confirmText: '确认删除',
    cancelText: '取消',
    requirePassword: false,
    requireReason: false,
    type: 'warning',
    icon: 'delete'
  },
  'homework.batch_delete': {
    title: '批量删除作业',
    message: '确认要删除选中的 {count} 个作业吗？删除后将无法恢复。',
    confirmText: '确认删除',
    cancelText: '取消',
    requirePassword: true,
    requireReason: true,
    type: 'danger',
    icon: 'delete'
  },
  'homework.submit_final': {
    title: '提交作业',
    message: '确认要最终提交这个作业吗？提交后将无法再次修改。',
    confirmText: '确认提交',
    cancelText: '继续编辑',
    requirePassword: false,
    requireReason: false,
    type: 'warning',
    icon: 'submit'
  },

  // 用户管理敏感操作
  'profile.delete_avatar': {
    title: '删除头像',
    message: '确认要删除当前头像吗？',
    confirmText: '确认删除',
    cancelText: '取消',
    requirePassword: false,
    requireReason: false,
    type: 'warning',
    icon: 'delete'
  },
  'profile.reset_password': {
    title: '重置密码',
    message: '确认要重置密码吗？重置后需要重新登录。',
    confirmText: '确认重置',
    cancelText: '取消',
    requirePassword: true,
    requireReason: false,
    type: 'warning',
    icon: 'reset'
  },

  // 数据管理敏感操作
  'data.export_all': {
    title: '导出全部数据',
    message: '确认要导出全部学习数据吗？导出文件将包含敏感信息。',
    confirmText: '确认导出',
    cancelText: '取消',
    requirePassword: false,
    requireReason: true,
    type: 'info',
    icon: 'export'
  },
  'data.clear_history': {
    title: '清空历史记录',
    message: '确认要清空所有历史记录吗？清空后将无法恢复。',
    confirmText: '确认清空',
    cancelText: '取消',
    requirePassword: true,
    requireReason: true,
    type: 'danger',
    icon: 'clear'
  },

  // 文件管理敏感操作
  'file.delete': {
    title: '删除文件',
    message: '确认要删除文件 "{fileName}" 吗？删除后将无法恢复。',
    confirmText: '确认删除',
    cancelText: '取消',
    requirePassword: false,
    requireReason: false,
    type: 'warning',
    icon: 'delete'
  },
  'file.batch_delete': {
    title: '批量删除文件',
    message: '确认要删除选中的 {count} 个文件吗？删除后将无法恢复。',
    confirmText: '确认删除',
    cancelText: '取消',
    requirePassword: true,
    requireReason: true,
    type: 'danger',
    icon: 'delete'
  },

  // 会话管理敏感操作
  'chat.delete_session': {
    title: '删除对话',
    message: '确认要删除这个对话记录吗？删除后将无法恢复。',
    confirmText: '确认删除',
    cancelText: '取消',
    requirePassword: false,
    requireReason: false,
    type: 'warning',
    icon: 'delete'
  },
  'chat.clear_all': {
    title: '清空所有对话',
    message: '确认要清空所有对话记录吗？清空后将无法恢复。',
    confirmText: '确认清空',
    cancelText: '取消',
    requirePassword: true,
    requireReason: true,
    type: 'danger',
    icon: 'clear'
  },

  // 学生管理敏感操作
  'student.remove': {
    title: '移除学生',
    message: '确认要从班级中移除学生 "{studentName}" 吗？',
    confirmText: '确认移除',
    cancelText: '取消',
    requirePassword: false,
    requireReason: true,
    type: 'warning',
    icon: 'remove'
  },
  'student.batch_remove': {
    title: '批量移除学生',
    message: '确认要移除选中的 {count} 个学生吗？',
    confirmText: '确认移除',
    cancelText: '取消',
    requirePassword: true,
    requireReason: true,
    type: 'danger',
    icon: 'remove'
  },

  // 系统管理敏感操作
  'system.reset_config': {
    title: '重置系统配置',
    message: '确认要将系统配置重置为默认值吗？重置后所有自定义设置将丢失。',
    confirmText: '确认重置',
    cancelText: '取消',
    requirePassword: true,
    requireReason: true,
    type: 'danger',
    icon: 'reset'
  }
};

/**
 * 敏感操作确认器
 */
class SensitiveOperationGuard {
  constructor() {
    this.confirmationQueue = [];
    this.activeConfirmation = null;
    this.operationLog = [];
    this.maxLogSize = 50;
  }

  /**
   * 确认敏感操作
   * @param {string} operationKey - 操作键
   * @param {Object} context - 操作上下文
   * @param {Object} options - 选项
   * @returns {Promise<Object>} 确认结果
   */
  async confirmSensitiveOperation(operationKey, context = {}, options = {}) {
    try {
      console.log(`[SensitiveOperation] 开始确认操作: ${operationKey}`, context);

      // 1. 获取操作配置
      const operationConfig = this.getOperationConfig(operationKey, context);
      if (!operationConfig) {
        console.warn(`[SensitiveOperation] 未找到操作配置: ${operationKey}`);
        return { 
          success: true, 
          reason: 'no_config',
          message: '操作未配置确认流程' 
        };
      }

      // 2. 检查操作权限
      const permissionCheck = await this.checkOperationPermission(operationKey, context);
      if (!permissionCheck.success) {
        return permissionCheck;
      }

      // 3. 显示确认对话框
      const confirmationResult = await this.showConfirmationDialog(operationConfig, context, options);
      
      // 4. 记录操作日志
      this.logOperation(operationKey, context, confirmationResult);

      return confirmationResult;

    } catch (error) {
      console.error(`[SensitiveOperation] 操作确认失败: ${operationKey}`, error);
      return {
        success: false,
        reason: 'confirmation_error',
        message: '操作确认过程出现错误'
      };
    }
  }

  /**
   * 获取操作配置
   * @param {string} operationKey - 操作键
   * @param {Object} context - 上下文
   * @returns {Object} 操作配置
   */
  getOperationConfig(operationKey, context) {
    let config = SENSITIVE_OPERATION_CONFIG[operationKey];
    if (!config) {
      return null;
    }

    // 克隆配置以避免修改原始配置
    config = JSON.parse(JSON.stringify(config));

    // 处理动态消息内容
    if (config.message && context) {
      config.message = this.interpolateMessage(config.message, context);
    }

    return config;
  }

  /**
   * 插值消息内容
   * @param {string} message - 消息模板
   * @param {Object} context - 上下文
   * @returns {string} 插值后的消息
   */
  interpolateMessage(message, context) {
    return message.replace(/\{(\w+)\}/g, (match, key) => {
      return context[key] || match;
    });
  }

  /**
   * 检查操作权限
   * @param {string} operationKey - 操作键
   * @param {Object} context - 上下文
   * @returns {Promise<Object>} 权限检查结果
   */
  async checkOperationPermission(operationKey, context) {
    try {
      // 检查用户登录状态
      const currentUser = authManager.getCurrentUser();
      if (!currentUser) {
        return {
          success: false,
          reason: 'not_logged_in',
          message: '请先登录'
        };
      }

      // 检查基础权限
      const hasPermission = await permissionManager.checkPermission(operationKey);
      if (!hasPermission) {
        return {
          success: false,
          reason: 'no_permission',
          message: '您没有执行此操作的权限'
        };
      }

      // 检查资源所有权（如果有资源ID）
      if (context.resourceId) {
        const ownershipCheck = await this.checkResourceOwnership(operationKey, context);
        if (!ownershipCheck.success) {
          return ownershipCheck;
        }
      }

      return { success: true };

    } catch (error) {
      console.error(`[SensitiveOperation] 权限检查失败: ${operationKey}`, error);
      return {
        success: false,
        reason: 'permission_check_error',
        message: '权限检查过程出现错误'
      };
    }
  }

  /**
   * 检查资源所有权
   * @param {string} operationKey - 操作键
   * @param {Object} context - 上下文
   * @returns {Promise<Object>} 所有权检查结果
   */
  async checkResourceOwnership(operationKey, context) {
    try {
      const currentUser = authManager.getCurrentUser();
      const userRole = roleManager.getCurrentRole();

      // 教师角色通常有管理权限
      if (userRole === 'teacher') {
        return { success: true };
      }

      // 学生和家长只能操作自己的资源
      if (context.ownerId && context.ownerId !== currentUser.id) {
        return {
          success: false,
          reason: 'not_owner',
          message: '您只能操作自己的内容'
        };
      }

      return { success: true };

    } catch (error) {
      console.error(`[SensitiveOperation] 所有权检查失败`, error);
      return {
        success: false,
        reason: 'ownership_check_error',
        message: '所有权检查过程出现错误'
      };
    }
  }

  /**
   * 显示确认对话框
   * @param {Object} config - 操作配置
   * @param {Object} context - 上下文
   * @param {Object} options - 选项
   * @returns {Promise<Object>} 确认结果
   */
  async showConfirmationDialog(config, context, options) {
    return new Promise((resolve) => {
      // 如果有其他确认对话框正在显示，加入队列
      if (this.activeConfirmation) {
        this.confirmationQueue.push({ config, context, options, resolve });
        return;
      }

      this.activeConfirmation = { config, context, options, resolve };
      this._showDialog(config, context, options, resolve);
    });
  }

  /**
   * 显示对话框
   * @param {Object} config - 操作配置
   * @param {Object} context - 上下文
   * @param {Object} options - 选项
   * @param {Function} resolve - 回调函数
   */
  _showDialog(config, context, options, resolve) {
    const modalData = {
      title: config.title,
      message: config.message,
      confirmText: config.confirmText,
      cancelText: config.cancelText,
      type: config.type,
      icon: config.icon,
      requirePassword: config.requirePassword,
      requireReason: config.requireReason,
      show: true
    };

    // 使用小程序的模态对话框
    if (config.requirePassword || config.requireReason) {
      // 需要额外输入的复杂确认
      this._showComplexConfirmation(modalData, resolve);
    } else {
      // 简单确认
      this._showSimpleConfirmation(modalData, resolve);
    }
  }

  /**
   * 显示简单确认对话框
   * @param {Object} modalData - 对话框数据
   * @param {Function} resolve - 回调函数
   */
  _showSimpleConfirmation(modalData, resolve) {
    wx.showModal({
      title: modalData.title,
      content: modalData.message,
      confirmText: modalData.confirmText,
      cancelText: modalData.cancelText,
      confirmColor: this._getConfirmColor(modalData.type),
      success: (res) => {
        this._handleConfirmationResult(res.confirm, null, resolve);
      },
      fail: () => {
        this._handleConfirmationResult(false, null, resolve);
      }
    });
  }

  /**
   * 显示复杂确认对话框
   * @param {Object} modalData - 对话框数据
   * @param {Function} resolve - 回调函数
   */
  _showComplexConfirmation(modalData, resolve) {
    // 获取当前页面实例
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];

    if (!currentPage) {
      console.error('[SensitiveOperation] 无法获取当前页面实例');
      this._handleConfirmationResult(false, null, resolve);
      return;
    }

    // 设置页面数据
    currentPage.setData({
      sensitiveConfirmModal: modalData
    });

    // 设置确认回调
    currentPage.onSensitiveConfirm = (confirmed, extraData) => {
      currentPage.setData({
        sensitiveConfirmModal: { show: false }
      });
      this._handleConfirmationResult(confirmed, extraData, resolve);
    };
  }

  /**
   * 处理确认结果
   * @param {boolean} confirmed - 是否确认
   * @param {Object} extraData - 额外数据
   * @param {Function} resolve - 回调函数
   */
  _handleConfirmationResult(confirmed, extraData, resolve) {
    const result = {
      success: confirmed,
      reason: confirmed ? 'confirmed' : 'cancelled',
      message: confirmed ? '操作已确认' : '操作已取消',
      extraData: extraData
    };

    resolve(result);
    this._processNextConfirmation();
  }

  /**
   * 处理下一个确认
   */
  _processNextConfirmation() {
    this.activeConfirmation = null;

    if (this.confirmationQueue.length > 0) {
      const next = this.confirmationQueue.shift();
      this.activeConfirmation = next;
      this._showDialog(next.config, next.context, next.options, next.resolve);
    }
  }

  /**
   * 获取确认按钮颜色
   * @param {string} type - 对话框类型
   * @returns {string} 颜色值
   */
  _getConfirmColor(type) {
    const colors = {
      'info': '#576B95',
      'warning': '#FF9500',
      'danger': '#FA5151',
      'success': '#07C160'
    };
    return colors[type] || '#576B95';
  }

  /**
   * 记录操作日志
   * @param {string} operationKey - 操作键
   * @param {Object} context - 上下文
   * @param {Object} result - 结果
   */
  logOperation(operationKey, context, result) {
    const logEntry = {
      operationKey,
      context,
      result,
      timestamp: new Date().toISOString(),
      userId: authManager.getCurrentUser()?.id,
      userRole: roleManager.getCurrentRole()
    };

    this.operationLog.push(logEntry);

    // 限制日志大小
    if (this.operationLog.length > this.maxLogSize) {
      this.operationLog.shift();
    }

    console.log('[SensitiveOperation] 操作日志记录:', logEntry);
  }

  /**
   * 获取操作日志
   * @param {Object} filter - 过滤条件
   * @returns {Array} 操作日志
   */
  getOperationLog(filter = {}) {
    let logs = [...this.operationLog];

    if (filter.operationKey) {
      logs = logs.filter(log => log.operationKey === filter.operationKey);
    }

    if (filter.userId) {
      logs = logs.filter(log => log.userId === filter.userId);
    }

    if (filter.confirmed !== undefined) {
      logs = logs.filter(log => log.result.success === filter.confirmed);
    }

    return logs.reverse(); // 最新的在前
  }

  /**
   * 清空操作日志
   */
  clearOperationLog() {
    this.operationLog = [];
    console.log('[SensitiveOperation] 操作日志已清空');
  }

  /**
   * 批量注册敏感操作
   * @param {Object} operations - 操作配置
   */
  registerOperations(operations) {
    Object.assign(SENSITIVE_OPERATION_CONFIG, operations);
    console.log('[SensitiveOperation] 批量注册敏感操作:', Object.keys(operations));
  }

  /**
   * 注销敏感操作
   * @param {string} operationKey - 操作键
   */
  unregisterOperation(operationKey) {
    delete SENSITIVE_OPERATION_CONFIG[operationKey];
    console.log('[SensitiveOperation] 注销敏感操作:', operationKey);
  }

  /**
   * 检查操作是否需要确认
   * @param {string} operationKey - 操作键
   * @returns {boolean} 是否需要确认
   */
  requiresConfirmation(operationKey) {
    return !!SENSITIVE_OPERATION_CONFIG[operationKey];
  }
}

// 创建单例实例
const sensitiveOperationGuard = new SensitiveOperationGuard();

module.exports = {
  sensitiveOperationGuard,
  SensitiveOperationGuard,
  SENSITIVE_OPERATION_CONFIG
};