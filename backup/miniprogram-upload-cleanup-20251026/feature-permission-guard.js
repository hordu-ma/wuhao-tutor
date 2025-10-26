// utils/feature-permission-guard.js - 功能级权限验证守卫

const { permissionManager } = require('./permission-manager.js');
const { authManager } = require('./auth.js');
const { errorToast } = require('./error-toast.js');
const { sensitiveOperationGuard } = require('./sensitive-operation-guard.js');
const { friendlyPermissionDialog } = require('./friendly-permission-dialog.js');

/**
 * 功能权限配置映射
 */
const FEATURE_PERMISSION_CONFIG = {
  // 作业相关操作
  'homework.submit': {
    permission: 'homework.submit',
    roles: ['student'],
    conditions: {
      timeRestriction: '06:00-23:00',
      maxDaily: 10
    },
    errorMessage: '您没有提交作业的权限',
    confirmMessage: null
  },
  'homework.correct': {
    permission: 'homework.correct',
    roles: ['teacher'],
    conditions: {
      ownClassOnly: true
    },
    errorMessage: '您没有批改作业的权限',
    confirmMessage: null
  },
  'homework.delete': {
    permission: 'homework.delete',
    roles: ['teacher', 'student'],
    conditions: {
      ownershipRequired: true
    },
    errorMessage: '您没有删除作业的权限',
    confirmMessage: '删除作业后无法恢复，确定要删除吗？',
    sensitive: true
  },
  'homework.manage': {
    permission: 'homework.manage',
    roles: ['teacher'],
    conditions: {
      classPermission: true
    },
    errorMessage: '您没有管理作业的权限',
    confirmMessage: null
  },

  // 问答相关操作
  'chat.ask': {
    permission: 'chat.ask',
    roles: ['student', 'parent', 'teacher'],
    conditions: {
      dailyLimit: 50
    },
    errorMessage: '您没有使用问答功能的权限',
    confirmMessage: null
  },
  'chat.moderate': {
    permission: 'chat.moderate',
    roles: ['teacher'],
    conditions: {},
    errorMessage: '您没有审核对话的权限',
    confirmMessage: null
  },

  // 个人信息相关操作
  'profile.edit': {
    permission: 'profile.edit_self',
    roles: ['student', 'parent', 'teacher'],
    conditions: {
      selfOnly: true
    },
    errorMessage: '您没有编辑个人信息的权限',
    confirmMessage: null
  },
  'profile.avatar_upload': {
    permission: 'file.upload',
    roles: ['student', 'parent', 'teacher'],
    conditions: {
      fileSizeLimit: 5 * 1024 * 1024, // 5MB
      fileTypeLimit: ['jpg', 'jpeg', 'png', 'webp']
    },
    errorMessage: '您没有上传头像的权限',
    confirmMessage: null
  },

  // 分析报告相关操作
  'analysis.view': {
    permission: 'analysis.view_self',
    roles: ['student', 'parent', 'teacher'],
    conditions: {
      scopeRestriction: true
    },
    errorMessage: '您没有查看分析报告的权限',
    confirmMessage: null
  },
  'analysis.export': {
    permission: 'export.own_data',
    roles: ['student', 'parent', 'teacher'],
    conditions: {
      dataScope: 'own'
    },
    errorMessage: '您没有导出数据的权限',
    confirmMessage: '导出的数据包含个人敏感信息，确定要继续吗？'
  },

  // 学生管理相关操作
  'students.view': {
    permission: 'user.view_students',
    roles: ['teacher'],
    conditions: {
      classRestriction: true
    },
    errorMessage: '您没有查看学生信息的权限',
    confirmMessage: null
  },
  'students.manage': {
    permission: 'user.manage_students',
    roles: ['teacher'],
    conditions: {
      classRestriction: true
    },
    errorMessage: '您没有管理学生的权限',
    confirmMessage: '管理学生信息涉及隐私保护，请谨慎操作'
  },

  // 系统设置相关操作
  'settings.modify': {
    permission: 'settings.edit',
    roles: ['student', 'parent', 'teacher'],
    conditions: {},
    errorMessage: '您没有修改设置的权限',
    confirmMessage: null
  },
  'role.switch': {
    permission: 'settings.role_switch',
    roles: ['student', 'parent', 'teacher'],
    conditions: {
      cooldownPeriod: 5 * 60 * 1000 // 5分钟冷却时间
    },
    errorMessage: '您没有切换角色的权限',
    confirmMessage: '切换角色将会更改您的功能权限，确定要继续吗？'
  }
};

/**
 * 功能权限守卫类
 */
class FeaturePermissionGuard {
  constructor() {
    this.operationCache = new Map(); // 操作缓存
    this.dailyCounters = new Map(); // 每日计数器
    this.lastSwitchTime = 0; // 上次角色切换时间
  }

  /**
   * 检查功能权限
   */
  async checkFeaturePermission(featureKey, context = {}) {
    try {
      const config = FEATURE_PERMISSION_CONFIG[featureKey];
      if (!config) {
        console.warn(`未找到功能 ${featureKey} 的权限配置`);
        return { success: false, reason: 'no_config' };
      }

      // 1. 基础权限检查
      const hasBasicPermission = await permissionManager.hasPermission(config.permission);
      if (!hasBasicPermission) {
        return { 
          success: false, 
          reason: 'permission_denied',
          message: config.errorMessage 
        };
      }

      // 2. 角色权限检查
      if (config.roles && config.roles.length > 0) {
        const userRole = await authManager.getUserRole();
        if (!config.roles.includes(userRole)) {
          return { 
            success: false, 
            reason: 'role_not_allowed',
            message: config.errorMessage,
            userRole,
            requiredRoles: config.roles
          };
        }
      }

      // 3. 条件检查
      const conditionResult = await this.checkConditions(config.conditions, context, featureKey);
      if (!conditionResult.success) {
        return { 
          success: false, 
          reason: 'condition_failed',
          message: conditionResult.message || config.errorMessage,
          condition: conditionResult.failedCondition
        };
      }

      // 4. 敏感操作确认
      if (config.sensitive) {
        const confirmResult = await sensitiveOperationGuard.confirmSensitiveOperation(featureKey, context);
        if (!confirmResult.success) {
          return confirmResult;
        }
      } else if (config.confirmMessage) {
        const confirmResult = await this.showConfirmation(config.confirmMessage);
        if (!confirmResult) {
          return { 
            success: false, 
            reason: 'user_cancelled',
            message: '操作已取消'
          };
        }
      }

      // 5. 记录操作
      this.recordOperation(featureKey, context);

      return { 
        success: true, 
        message: '权限验证通过',
        config 
      };

    } catch (error) {
      console.error('功能权限检查失败:', error);
      return { 
        success: false, 
        reason: 'check_error',
        message: '权限检查失败，请稍后重试' 
      };
    }
  }

  /**
   * 检查条件
   */
  async checkConditions(conditions, context, featureKey) {
    try {
      // 时间限制检查
      if (conditions.timeRestriction) {
        const timeValid = this.checkTimeRestriction(conditions.timeRestriction);
        if (!timeValid) {
          return {
            success: false,
            message: `操作时间限制：${conditions.timeRestriction}`,
            failedCondition: 'time_restriction'
          };
        }
      }

      // 每日限制检查
      if (conditions.dailyLimit || conditions.maxDaily) {
        const limit = conditions.dailyLimit || conditions.maxDaily;
        const dailyValid = this.checkDailyLimit(featureKey, limit);
        if (!dailyValid) {
          return {
            success: false,
            message: `每日操作次数已达上限（${limit}次）`,
            failedCondition: 'daily_limit'
          };
        }
      }

      // 所有权检查
      if (conditions.ownershipRequired || conditions.selfOnly) {
        const ownershipValid = await this.checkOwnership(context);
        if (!ownershipValid) {
          return {
            success: false,
            message: '只能操作自己的资源',
            failedCondition: 'ownership'
          };
        }
      }

      // 班级权限检查
      if (conditions.classPermission || conditions.classRestriction) {
        const classValid = await this.checkClassPermission(context);
        if (!classValid) {
          return {
            success: false,
            message: '只能操作所在班级的资源',
            failedCondition: 'class_permission'
          };
        }
      }

      // 文件大小限制检查
      if (conditions.fileSizeLimit && context.fileSize) {
        if (context.fileSize > conditions.fileSizeLimit) {
          const sizeMB = Math.round(conditions.fileSizeLimit / 1024 / 1024);
          return {
            success: false,
            message: `文件大小不能超过 ${sizeMB}MB`,
            failedCondition: 'file_size'
          };
        }
      }

      // 文件类型限制检查
      if (conditions.fileTypeLimit && context.fileType) {
        if (!conditions.fileTypeLimit.includes(context.fileType.toLowerCase())) {
          return {
            success: false,
            message: `不支持的文件类型，仅支持：${conditions.fileTypeLimit.join('、')}`,
            failedCondition: 'file_type'
          };
        }
      }

      // 冷却时间检查
      if (conditions.cooldownPeriod) {
        const cooldownValid = this.checkCooldown(featureKey, conditions.cooldownPeriod);
        if (!cooldownValid) {
          const minutes = Math.ceil(conditions.cooldownPeriod / 60000);
          return {
            success: false,
            message: `操作冷却中，请等待 ${minutes} 分钟后再试`,
            failedCondition: 'cooldown'
          };
        }
      }

      return { success: true };

    } catch (error) {
      console.error('条件检查失败:', error);
      return { 
        success: false, 
        message: '条件检查失败',
        failedCondition: 'check_error'
      };
    }
  }

  /**
   * 检查时间限制
   */
  checkTimeRestriction(timeRange) {
    try {
      const [startTime, endTime] = timeRange.split('-');
      const now = new Date();
      const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      
      return currentTime >= startTime && currentTime <= endTime;
    } catch (error) {
      console.warn('时间限制检查失败:', error);
      return true; // 检查失败时允许通过
    }
  }

  /**
   * 检查每日限制
   */
  checkDailyLimit(featureKey, limit) {
    try {
      const today = new Date().toDateString();
      const countKey = `${featureKey}_${today}`;
      const currentCount = this.dailyCounters.get(countKey) || 0;
      
      return currentCount < limit;
    } catch (error) {
      console.warn('每日限制检查失败:', error);
      return true;
    }
  }

  /**
   * 检查所有权
   */
  async checkOwnership(context) {
    try {
      if (!context.resourceOwnerId) {
        return true; // 没有所有者信息时允许通过
      }

      const userInfo = await authManager.getUserInfo();
      return context.resourceOwnerId === userInfo.id;
    } catch (error) {
      console.warn('所有权检查失败:', error);
      return false;
    }
  }

  /**
   * 检查班级权限
   */
  async checkClassPermission(context) {
    try {
      const userInfo = await authManager.getUserInfo();
      const userRole = await authManager.getUserRole();

      if (userRole === 'teacher') {
        // 教师只能操作自己班级的资源
        if (context.classId && userInfo.classes) {
          return userInfo.classes.includes(context.classId);
        }
      } else if (userRole === 'parent') {
        // 家长只能操作自己孩子所在班级的资源
        if (context.studentId && userInfo.children) {
          return userInfo.children.includes(context.studentId);
        }
      }

      return true; // 学生或其他情况允许通过
    } catch (error) {
      console.warn('班级权限检查失败:', error);
      return false;
    }
  }

  /**
   * 检查冷却时间
   */
  checkCooldown(featureKey, cooldownPeriod) {
    try {
      const lastOperationTime = this.operationCache.get(`${featureKey}_last_time`) || 0;
      const now = Date.now();
      
      return (now - lastOperationTime) >= cooldownPeriod;
    } catch (error) {
      console.warn('冷却时间检查失败:', error);
      return true;
    }
  }

  /**
   * 显示确认对话框
   */
  showConfirmation(message) {
    return new Promise((resolve) => {
      wx.showModal({
        title: '操作确认',
        content: message,
        confirmText: '确定',
        cancelText: '取消',
        success: (res) => {
          resolve(res.confirm);
        },
        fail: () => {
          resolve(false);
        }
      });
    });
  }

  /**
   * 记录操作
   */
  recordOperation(featureKey, context) {
    try {
      const now = Date.now();
      const today = new Date().toDateString();

      // 记录操作时间
      this.operationCache.set(`${featureKey}_last_time`, now);

      // 更新每日计数
      const countKey = `${featureKey}_${today}`;
      const currentCount = this.dailyCounters.get(countKey) || 0;
      this.dailyCounters.set(countKey, currentCount + 1);

      // 清理过期的计数记录
      this.cleanupExpiredCounters();

    } catch (error) {
      console.warn('记录操作失败:', error);
    }
  }

  /**
   * 清理过期的计数记录
   */
  cleanupExpiredCounters() {
    try {
      const today = new Date().toDateString();
      const keysToDelete = [];

      for (const [key] of this.dailyCounters) {
        if (!key.endsWith(today)) {
          keysToDelete.push(key);
        }
      }

      keysToDelete.forEach(key => {
        this.dailyCounters.delete(key);
      });
    } catch (error) {
      console.warn('清理过期计数失败:', error);
    }
  }

  /**
   * 便捷方法：检查作业提交权限
   */
  async canSubmitHomework(homeworkId) {
    return await this.checkFeaturePermission('homework.submit', { 
      homeworkId 
    });
  }

  /**
   * 便捷方法：检查作业批改权限
   */
  async canCorrectHomework(homeworkId, classId) {
    return await this.checkFeaturePermission('homework.correct', { 
      homeworkId, 
      classId 
    });
  }

  /**
   * 便捷方法：检查作业删除权限
   */
  async canDeleteHomework(homeworkId, ownerId) {
    return await this.checkFeaturePermission('homework.delete', { 
      homeworkId, 
      resourceOwnerId: ownerId 
    });
  }

  /**
   * 便捷方法：检查问答权限
   */
  async canAskQuestion() {
    return await this.checkFeaturePermission('chat.ask');
  }

  /**
   * 便捷方法：检查头像上传权限
   */
  async canUploadAvatar(fileSize, fileType) {
    return await this.checkFeaturePermission('profile.avatar_upload', { 
      fileSize, 
      fileType 
    });
  }

  /**
   * 便捷方法：检查角色切换权限
   */
  async canSwitchRole() {
    return await this.checkFeaturePermission('role.switch');
  }

  /**
   * 处理权限检查失败
   */
  handlePermissionFailure(result, context = {}) {
    switch (result.reason) {
      case 'permission_denied':
        friendlyPermissionDialog.showPermissionError('permission_denied', {
          message: result.message,
          feature: context.feature
        });
        break;
      case 'role_not_allowed':
        friendlyPermissionDialog.showPermissionError('role_not_allowed', {
          userRole: result.userRole,
          requiredRoles: result.requiredRoles,
          message: result.message
        });
        break;
      case 'condition_failed':
        this.handleConditionFailure(result, context);
        break;
      case 'user_cancelled':
        // 用户取消，无需额外处理
        break;
      default:
        friendlyPermissionDialog.showPermissionError('server_error', {
          message: result.message || '权限验证失败'
        });
    }
  }

  /**
   * 处理条件失败
   */
  handleConditionFailure(result, context) {
    const conditionTypeMap = {
      'time_restriction': 'time_restriction',
      'daily_limit': 'daily_limit',
      'ownership': 'not_owner',
      'class_permission': 'permission_denied',
      'file_size': 'condition_failed',
      'file_type': 'condition_failed',
      'cooldown': 'condition_failed'
    };

    const errorType = conditionTypeMap[result.condition] || 'condition_failed';
    
    friendlyPermissionDialog.showPermissionError(errorType, {
      message: result.message,
      condition: result.condition,
      requirement: this.getConditionRequirement(result.condition)
    });
  }

  /**
   * 获取条件要求说明
   */
  getConditionRequirement(condition) {
    const requirements = {
      'time_restriction': '请在指定时间段内使用',
      'daily_limit': '每日使用次数有限制',
      'ownership': '只能操作自己的内容',
      'class_permission': '需要相应的班级权限',
      'file_size': '文件大小超出限制',
      'file_type': '文件类型不支持',
      'cooldown': '操作频率过高，请稍后再试'
    };
    
    return requirements[condition] || '未知条件限制';
  }





  /**
   * 获取调试信息
   */
  getDebugInfo() {
    return {
      operationCache: Object.fromEntries(this.operationCache),
      dailyCounters: Object.fromEntries(this.dailyCounters),
      featureConfigs: FEATURE_PERMISSION_CONFIG
    };
  }
}

// 创建单例实例
const featurePermissionGuard = new FeaturePermissionGuard();

// 导出便捷的装饰器函数
const requireFeaturePermission = (featureKey) => {
  return (target, propertyName, descriptor) => {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args) {
      const context = args[0] || {};
      const result = await featurePermissionGuard.checkFeaturePermission(featureKey, context);
      
      if (!result.success) {
        featurePermissionGuard.handlePermissionFailure(result, context);
        return;
      }

      return originalMethod.apply(this, args);
    };

    return descriptor;
  };
};

module.exports = {
  featurePermissionGuard,
  requireFeaturePermission,
  FEATURE_PERMISSION_CONFIG
};