// utils/enhanced-page-guard.js - 增强的页面权限守卫系统

const { authManager } = require('./auth.js');
const { permissionManager } = require('./permission-manager.js');
const { roleManager } = require('./role-manager.js');
const { errorToast } = require('./error-toast.js');
const { friendlyPermissionDialog } = require('./friendly-permission-dialog.js');

/**
 * 页面权限配置映射
 */
const PAGE_PERMISSION_CONFIG = {
  // 个人信息相关页面
  'pages/profile/index/index': {
    permissions: ['profile.view_self'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '个人信息展示页面',
  },
  'pages/profile/edit/index': {
    permissions: ['profile.edit_self'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '个人信息编辑页面',
  },
  'pages/profile/settings/index': {
    permissions: ['settings.view'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '设置页面',
  },

  // 作业模块页面
  'pages/homework/list/index': {
    permissions: ['homework.view'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '作业列表页面',
  },
  'pages/homework/detail/index': {
    permissions: ['homework.view'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '作业详情页面',
  },
  'pages/homework/submit/index': {
    permissions: ['homework.submit'],
    roles: ['student'],
    requireLogin: true,
    description: '作业提交页面',
  },

  // 问答模块页面
  'pages/chat/index/index': {
    permissions: ['chat.ask'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '问答页面',
  },
  'pages/chat/detail/index': {
    permissions: ['chat.view'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '问答详情页面',
  },

  // 分析模块页面
  'pages/analysis/report/index': {
    permissions: ['analysis.view_self'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '学习报告页面',
  },
  'pages/analysis/progress/index': {
    permissions: ['analysis.view_self'],
    roles: ['student', 'parent', 'teacher'],
    requireLogin: true,
    description: '学习进度页面',
  },

  // 管理页面（仅教师可访问）
  'pages/homework/manage/index': {
    permissions: ['homework.manage'],
    roles: ['teacher'],
    requireLogin: true,
    description: '作业管理页面',
  },
  'pages/students/list/index': {
    permissions: ['user.view_students'],
    roles: ['teacher'],
    requireLogin: true,
    description: '学生列表页面',
  },

  // 公共页面（无需权限）
  'pages/index/index': {
    permissions: [],
    roles: [],
    requireLogin: false,
    description: '首页',
  },
  'pages/login/index': {
    permissions: [],
    roles: [],
    requireLogin: false,
    description: '登录页面',
  },
  'pages/role-selection/index': {
    permissions: [],
    roles: [],
    requireLogin: true,
    description: '角色选择页面',
  },
};

/**
 * 增强的页面守卫管理器
 */
class EnhancedPageGuard {
  constructor() {
    this.guardEnabled = true;
    this.debugMode = false;
    this.guardResults = new Map(); // 存储守卫结果用于调试
  }

  /**
   * 为页面对象添加权限守卫
   */
  createGuardedPage(pageObject, pagePath) {
    const config = PAGE_PERMISSION_CONFIG[pagePath];

    if (!config) {
      console.warn(`页面 ${pagePath} 没有权限配置，使用默认保护`);
      return this.createDefaultGuardedPage(pageObject);
    }

    return this.createConfiguredGuardedPage(pageObject, config, pagePath);
  }

  /**
   * 创建有配置的守卫页面
   */
  createConfiguredGuardedPage(pageObject, config, pagePath) {
    const originalOnLoad = pageObject.onLoad;
    const originalOnShow = pageObject.onShow;
    const guard = this; // 保存当前实例的引用

    return {
      ...pageObject,

      async onLoad(options) {
        const guardResult = await guard.executePageGuard(config, pagePath, options);

        if (!guardResult.success) {
          return; // 守卫失败，停止页面加载
        }

        // 将权限信息注入页面数据
        if (typeof this.setData === 'function') {
          this.setData({
            userPermissions: guardResult.permissions,
            userRole: guardResult.role,
            canPerformActions: guardResult.actions,
          });
        }

        // 调用原始的onLoad
        if (originalOnLoad) {
          return originalOnLoad.call(this, options);
        }
      },

      async onShow() {
        // 每次显示时重新验证权限（处理角色切换情况）
        const quickCheck = await guard.quickPermissionCheck(config, pagePath);

        if (!quickCheck.success) {
          return; // 快速检查失败，可能权限已变更
        }

        // 调用原始的onShow
        if (originalOnShow) {
          return originalOnShow.call(this);
        }
      },

      // 添加权限检查辅助方法到页面对象
      async hasPermission(permission) {
        return await permissionManager.hasPermission(permission);
      },

      async checkFeatureAccess(feature) {
        return await guard.checkFeaturePermission(feature);
      },
    };
  }

  /**
   * 创建默认守卫页面
   */
  createDefaultGuardedPage(pageObject) {
    const originalOnLoad = pageObject.onLoad;

    return {
      ...pageObject,

      async onLoad(options) {
        // 默认只检查登录状态
        const isLoggedIn = await authManager.isLoggedIn();

        if (!isLoggedIn) {
          console.log('页面需要登录，跳转到登录页');
          wx.redirectTo({
            url: '/pages/login/index',
          });
          return;
        }

        if (originalOnLoad) {
          return originalOnLoad.call(this, options);
        }
      },
    };
  }

  /**
   * 执行页面守卫检查
   */
  async executePageGuard(config, pagePath, options = {}) {
    try {
      const startTime = Date.now();

      // 1. 登录状态检查
      if (config.requireLogin) {
        const isLoggedIn = await authManager.isLoggedIn();
        if (!isLoggedIn) {
          this.handleLoginRequired(pagePath);
          return { success: false, reason: 'not_logged_in' };
        }

        // Token有效性检查
        const isTokenValid = await authManager.isTokenValid();
        if (!isTokenValid) {
          try {
            await authManager.refreshToken();
          } catch (error) {
            this.handleLoginRequired(pagePath);
            return { success: false, reason: 'token_invalid' };
          }
        }
      }

      // 2. 角色权限检查
      if (config.roles && config.roles.length > 0) {
        const userRole = await authManager.getUserRole();
        if (!config.roles.includes(userRole)) {
          this.handleRolePermissionDenied(userRole, config.roles, pagePath);
          return {
            success: false,
            reason: 'role_not_allowed',
            userRole,
            requiredRoles: config.roles,
          };
        }
      }

      // 3. 具体权限检查
      if (config.permissions && config.permissions.length > 0) {
        const permissionResults = await Promise.all(
          config.permissions.map(async permission => ({
            permission,
            hasPermission: await permissionManager.hasPermission(permission),
          })),
        );

        const failedPermissions = permissionResults.filter(result => !result.hasPermission);

        if (failedPermissions.length > 0) {
          this.handlePermissionDenied(failedPermissions, pagePath);
          return {
            success: false,
            reason: 'permission_denied',
            failedPermissions: failedPermissions.map(fp => fp.permission),
          };
        }
      }

      // 4. 动态权限检查（如果有特殊规则）
      if (options.resourceId) {
        const dynamicResult = await this.checkDynamicPermissions(config, options);
        if (!dynamicResult.success) {
          return dynamicResult;
        }
      }

      // 收集用户权限和能执行的操作
      const userPermissions = await this.collectUserPermissions();
      const userRole = await authManager.getUserRole();
      const availableActions = await this.collectAvailableActions(config, userPermissions);

      const guardResult = {
        success: true,
        permissions: userPermissions,
        role: userRole,
        actions: availableActions,
        executionTime: Date.now() - startTime,
      };

      // 调试模式下记录结果
      if (this.debugMode) {
        this.guardResults.set(pagePath, guardResult);
        console.log(`页面守卫执行成功: ${pagePath}`, guardResult);
      }

      return guardResult;
    } catch (error) {
      console.error('页面守卫执行失败:', error);
      this.handleGuardError(error, pagePath);
      return { success: false, reason: 'guard_error', error };
    }
  }

  /**
   * 快速权限检查（用于onShow）
   */
  async quickPermissionCheck(config, pagePath) {
    try {
      if (!config.requireLogin) {
        return { success: true };
      }

      const isLoggedIn = await authManager.isLoggedIn();
      if (!isLoggedIn) {
        this.handleLoginRequired(pagePath);
        return { success: false, reason: 'not_logged_in' };
      }

      if (config.roles && config.roles.length > 0) {
        const userRole = await authManager.getUserRole();
        if (!config.roles.includes(userRole)) {
          this.handleRolePermissionDenied(userRole, config.roles, pagePath);
          return { success: false, reason: 'role_changed' };
        }
      }

      return { success: true };
    } catch (error) {
      console.error('快速权限检查失败:', error);
      return { success: false, reason: 'check_error' };
    }
  }

  /**
   * 检查动态权限
   */
  async checkDynamicPermissions(config, options) {
    // 这里可以根据具体业务逻辑实现动态权限检查
    // 例如：检查用户是否是资源的拥有者
    return { success: true };
  }

  /**
   * 收集用户权限
   */
  async collectUserPermissions() {
    const userRole = await authManager.getUserRole();
    const commonPermissions = ['profile.view_self', 'settings.view', 'settings.role_switch'];

    const roleBasedPermissions = {
      student: ['homework.view', 'homework.submit', 'chat.ask', 'analysis.view_self'],
      parent: ['homework.view_child', 'chat.view_child', 'analysis.view_child'],
      teacher: ['homework.view_all', 'homework.correct', 'homework.manage', 'user.view_students'],
    };

    const allPermissions = [...commonPermissions, ...(roleBasedPermissions[userRole] || [])];

    const permissionResults = await Promise.all(
      allPermissions.map(async permission => ({
        permission,
        hasPermission: await permissionManager.hasPermission(permission),
      })),
    );

    return permissionResults
      .filter(result => result.hasPermission)
      .map(result => result.permission);
  }

  /**
   * 收集可用操作
   */
  async collectAvailableActions(config, userPermissions) {
    const actions = {};

    // 根据权限生成操作映射
    for (const permission of userPermissions) {
      switch (permission) {
        case 'homework.submit':
          actions.canSubmitHomework = true;
          break;
        case 'homework.correct':
          actions.canCorrectHomework = true;
          break;
        case 'homework.manage':
          actions.canManageHomework = true;
          break;
        case 'profile.edit_self':
          actions.canEditProfile = true;
          break;
        case 'user.view_students':
          actions.canViewStudents = true;
          break;
        case 'analysis.view_all':
          actions.canViewAllAnalysis = true;
          break;
      }
    }

    return actions;
  }

  /**
   * 处理登录要求
   */
  handleLoginRequired(pagePath) {
    console.log(`页面 ${pagePath} 需要登录，跳转到登录页`);

    friendlyPermissionDialog.showPermissionError('not_logged_in', {
      pagePath,
      retryCallback: () => {
        wx.redirectTo({
          url: `/pages/login/index?redirect=${encodeURIComponent(pagePath)}`,
        });
      },
    });
  }

  /**
   * 处理角色权限被拒绝
   */
  handleRolePermissionDenied(userRole, requiredRoles, pagePath) {
    console.log(`角色 ${userRole} 无权访问页面 ${pagePath}，需要角色: ${requiredRoles.join(', ')}`);

    friendlyPermissionDialog.showPermissionError('role_not_allowed', {
      userRole,
      requiredRoles,
      pagePath,
    });
  }

  /**
   * 处理权限被拒绝
   */
  handlePermissionDenied(failedPermissions, pagePath) {
    console.log(`页面 ${pagePath} 权限检查失败:`, failedPermissions);

    friendlyPermissionDialog.showPermissionError('permission_denied', {
      failedPermissions,
      pagePath,
      feature: pagePath,
    });
  }

  /**
   * 处理守卫错误
   */
  handleGuardError(error, pagePath) {
    console.error(`页面 ${pagePath} 权限守卫执行出错:`, error);

    friendlyPermissionDialog.showPermissionError('server_error', {
      pagePath,
      error: error.message,
      retryCallback: () => {
        wx.navigateBack({
          fail: () => {
            wx.switchTab({
              url: '/pages/index/index',
            });
          },
        });
      },
    });
  }

  /**
   * 检查特定功能权限
   */
  async checkFeaturePermission(feature) {
    const featurePermissionMap = {
      submit_homework: 'homework.submit',
      correct_homework: 'homework.correct',
      manage_homework: 'homework.manage',
      ask_question: 'chat.ask',
      view_analysis: 'analysis.view_self',
      edit_profile: 'profile.edit_self',
      view_students: 'user.view_students',
    };

    const permission = featurePermissionMap[feature];
    if (!permission) {
      console.warn(`未知功能: ${feature}`);
      return false;
    }

    return await permissionManager.hasPermission(permission);
  }

  /**
   * 启用调试模式
   */
  enableDebugMode() {
    this.debugMode = true;
    console.log('页面守卫调试模式已启用');
  }

  /**
   * 获取调试信息
   */
  getDebugInfo() {
    return {
      guardEnabled: this.guardEnabled,
      debugMode: this.debugMode,
      guardResults: Object.fromEntries(this.guardResults),
      pageConfigs: PAGE_PERMISSION_CONFIG,
    };
  }

  /**
   * 更新页面权限配置
   */
  updatePageConfig(pagePath, config) {
    PAGE_PERMISSION_CONFIG[pagePath] = {
      ...PAGE_PERMISSION_CONFIG[pagePath],
      ...config,
    };
  }

  /**
   * 获取页面权限配置
   */
  getPageConfig(pagePath) {
    return PAGE_PERMISSION_CONFIG[pagePath];
  }
}

// 创建单例实例
const enhancedPageGuard = new EnhancedPageGuard();

// 导出便捷的装饰器函数
const createGuardedPage = (pageObject, pagePath) => {
  return enhancedPageGuard.createGuardedPage(pageObject, pagePath);
};

const requirePermissions = (permissions, roles = []) => {
  return pageObject => {
    const config = {
      permissions: Array.isArray(permissions) ? permissions : [permissions],
      roles: Array.isArray(roles) ? roles : [roles],
      requireLogin: true,
      description: '需要特定权限的页面',
    };

    return enhancedPageGuard.createConfiguredGuardedPage(pageObject, config, 'dynamic_page');
  };
};

module.exports = {
  enhancedPageGuard,
  createGuardedPage,
  requirePermissions,
  PAGE_PERMISSION_CONFIG,
};
