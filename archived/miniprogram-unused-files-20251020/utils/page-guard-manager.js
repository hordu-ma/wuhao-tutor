// 全局页面权限守卫配置
// 为每个页面自动应用权限控制

const { routeGuard } = require('./route-guard.js');
const { permissionManager } = require('./permission-manager.js');
const { roleManager } = require('./role-manager.js');
const { authManager } = require('./auth.js');

/**
 * 页面权限守卫管理器
 */
class PageGuardManager {
  constructor() {
    // 需要权限守卫的页面配置
    this.pageGuardConfigs = {
      // 作业相关页面
      'pages/homework/list/index': {
        permissions: ['homework.view'],
        roles: ['student', 'parent', 'teacher'],
        description: '作业列表页面',
      },
      'pages/homework/detail/index': {
        permissions: ['homework.view'],
        roles: ['student', 'parent', 'teacher'],
        description: '作业详情页面',
      },
      'pages/homework/submit/index': {
        permissions: ['homework.submit'],
        roles: ['student'],
        description: '作业提交页面',
      },
      'pages/homework/correct/index': {
        permissions: ['homework.correct'],
        roles: ['teacher'],
        description: '作业批改页面',
      },
      'pages/homework/create/index': {
        permissions: ['homework.create'],
        roles: ['teacher'],
        description: '作业创建页面',
      },

      // 聊天问答页面
      'pages/chat/index/index': {
        permissions: ['chat.ask'],
        roles: ['student'],
        description: 'AI问答主页',
        timeRestriction: '06:00-23:00',
      },
      'pages/chat/detail/index': {
        permissions: ['chat.view'],
        roles: ['student', 'parent', 'teacher'],
        description: '对话详情页面',
      },

      // 分析报告页面
      'pages/analysis/report/index': {
        permissions: ['analysis.view_self'],
        roles: ['student'],
        description: '个人学习报告',
        dynamicPermission: true,
      },
      'pages/analysis/progress/index': {
        permissions: ['analysis.view_child'],
        roles: ['parent', 'teacher'],
        description: '学习进度分析',
      },

      // 个人中心页面
      'pages/profile/index/index': {
        permissions: ['profile.view_self'],
        roles: ['student', 'parent', 'teacher'],
        description: '个人中心主页',
      },
      'pages/profile/settings/index': {
        permissions: ['settings.view'],
        roles: ['student', 'parent', 'teacher'],
        description: '设置页面',
      },

      // 角色选择页面
      'pages/role-selection/index': {
        permissions: ['settings.role_switch'],
        roles: ['student', 'parent', 'teacher'],
        description: '角色选择页面',
      },
    };

    // 无需权限检查的公开页面
    this.publicPages = ['pages/index/index', 'pages/login/index', 'pages/profile/help/index'];
  }

  /**
   * 获取页面权限配置
   */
  getPageConfig(pagePath) {
    // 规范化页面路径
    const normalizedPath = this.normalizePath(pagePath);
    return this.pageGuardConfigs[normalizedPath] || null;
  }

  /**
   * 检查是否为公开页面
   */
  isPublicPage(pagePath) {
    const normalizedPath = this.normalizePath(pagePath);
    return this.publicPages.some(
      publicPath => normalizedPath.includes(publicPath) || publicPath.includes(normalizedPath),
    );
  }

  /**
   * 规范化页面路径
   */
  normalizePath(pagePath) {
    if (!pagePath) return '';

    // 移除前导斜杠
    let path = pagePath.startsWith('/') ? pagePath.slice(1) : pagePath;

    // 移除查询参数
    path = path.split('?')[0];

    return path;
  }

  /**
   * 为页面创建权限守卫
   */
  createPageGuard(pageConfig, customOptions = {}) {
    const guardConfig = this.getPageConfig(pageConfig.pagePath || '');

    if (!guardConfig && !this.isPublicPage(pageConfig.pagePath || '')) {
      console.warn('页面权限配置缺失:', pageConfig.pagePath);
    }

    return routeGuard.createPageGuard({
      ...pageConfig,
      requireRole: guardConfig?.roles,
      ...customOptions,

      // 增强的onLoad方法
      onLoad: this.enhanceOnLoad(pageConfig.onLoad, guardConfig, customOptions),

      // 增强的onShow方法
      onShow: this.enhanceOnShow(pageConfig.onShow, guardConfig, customOptions),
    });
  }

  /**
   * 增强页面的onLoad方法
   */
  enhanceOnLoad(originalOnLoad, guardConfig, customOptions) {
    return async function (options) {
      try {
        // 1. 基础路由守卫检查
        const guardResult = await routeGuard.checkPageAuth();
        if (!guardResult.success) {
          return;
        }

        // 2. 页面特定权限检查
        if (guardConfig) {
          const permissionCheckResult = await pageGuardManager.checkPagePermissions(guardConfig);
          if (!permissionCheckResult.success) {
            await pageGuardManager.handlePermissionDenied(permissionCheckResult, guardConfig);
            return;
          }
        }

        // 3. 自定义权限检查
        if (customOptions.customPermissionCheck) {
          const customResult = await customOptions.customPermissionCheck.call(this);
          if (!customResult) {
            return;
          }
        }

        // 4. 执行原始onLoad方法
        if (originalOnLoad) {
          return await originalOnLoad.call(this, options);
        }
      } catch (error) {
        console.error('页面权限守卫执行失败:', error);

        // 安全处理：权限检查失败时重定向到安全页面
        if (
          !pageGuardManager.isPublicPage(getCurrentPages()[getCurrentPages().length - 1]?.route)
        ) {
          wx.switchTab({
            url: '/pages/index/index',
            fail: () => {
              wx.redirectTo({
                url: '/pages/login/index',
              });
            },
          });
        }
      }
    };
  }

  /**
   * 增强页面的onShow方法
   */
  enhanceOnShow(originalOnShow, guardConfig, customOptions) {
    return async function () {
      try {
        // 重新检查登录状态
        const isLoggedIn = await routeGuard.checkAuth({ skipRedirect: true });
        if (
          !isLoggedIn.success &&
          !pageGuardManager.isPublicPage(getCurrentPages()[getCurrentPages().length - 1]?.route)
        ) {
          routeGuard.redirectToLogin();
          return;
        }

        // 执行原始onShow方法
        if (originalOnShow) {
          return await originalOnShow.call(this);
        }
      } catch (error) {
        console.error('页面onShow权限检查失败:', error);
      }
    };
  }

  /**
   * 检查页面权限
   */
  async checkPagePermissions(guardConfig) {
    try {
      const results = {
        success: true,
        failedChecks: [],
      };

      // 检查角色权限
      if (guardConfig.roles && guardConfig.roles.length > 0) {
        const userRole = await authManager.getUserRole();
        if (!guardConfig.roles.includes(userRole)) {
          results.success = false;
          results.failedChecks.push({
            type: 'role',
            required: guardConfig.roles,
            actual: userRole,
          });
        }
      }

      // 检查具体权限
      if (guardConfig.permissions && guardConfig.permissions.length > 0) {
        for (const permission of guardConfig.permissions) {
          const hasPermission = await permissionManager.hasPermission(permission);
          if (!hasPermission) {
            results.success = false;
            results.failedChecks.push({
              type: 'permission',
              permission: permission,
            });
          }
        }
      }

      // 检查时间限制
      if (guardConfig.timeRestriction) {
        const timeValid = permissionManager.checkTimeRestriction(guardConfig.timeRestriction);
        if (!timeValid) {
          results.success = false;
          results.failedChecks.push({
            type: 'time',
            restriction: guardConfig.timeRestriction,
          });
        }
      }

      // 检查动态权限
      if (guardConfig.dynamicPermission) {
        const dynamicResult = await this.checkDynamicPermissions(guardConfig);
        if (!dynamicResult.success) {
          results.success = false;
          results.failedChecks.push({
            type: 'dynamic',
            reason: dynamicResult.reason,
          });
        }
      }

      return results;
    } catch (error) {
      console.error('权限检查失败:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * 检查动态权限
   */
  async checkDynamicPermissions(guardConfig) {
    // 这里可以根据具体业务需求实现动态权限检查
    // 比如检查用户是否有权访问特定资源
    try {
      // 示例：检查家长是否只能访问自己孩子的数据
      const userRole = await authManager.getUserRole();

      if (userRole === 'parent' && guardConfig.permissions.some(p => p.includes('view_child'))) {
        // 实际应用中需要根据页面参数检查资源所有权
        return { success: true };
      }

      return { success: true };
    } catch (error) {
      return {
        success: false,
        reason: error.message,
      };
    }
  }

  /**
   * 处理权限拒绝
   */
  async handlePermissionDenied(permissionResult, guardConfig) {
    const failedChecks = permissionResult.failedChecks || [];

    // 根据失败类型给出不同的提示
    let title = '访问受限';
    let content = '您没有访问此页面的权限';

    const roleFailure = failedChecks.find(check => check.type === 'role');
    const timeFailure = failedChecks.find(check => check.type === 'time');
    const permissionFailure = failedChecks.find(check => check.type === 'permission');

    if (roleFailure) {
      content = `此页面仅限${roleFailure.required.join('、')}访问`;
    } else if (timeFailure) {
      content = `此功能限制访问时间：${timeFailure.restriction}`;
    } else if (permissionFailure) {
      content = '您当前的权限不足以访问此页面';
    }

    // 显示错误提示
    wx.showModal({
      title,
      content,
      showCancel: false,
      confirmText: '返回',
      success: async () => {
        // 根据用户角色跳转到合适的页面
        const userRole = await authManager.getUserRole();
        const roleConfig = roleManager.getRoleConfig(userRole);

        wx.redirectTo({
          url: roleConfig.homePage,
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
   * 批量设置页面权限守卫
   */
  setupPageGuards() {
    console.log('🛡️ 初始化页面权限守卫系统');

    // 在这里可以为全局页面设置默认守卫
    // 实际使用时，每个页面在其Page()调用中使用createPageGuard

    console.log('📋 已配置权限守卫的页面:');
    Object.keys(this.pageGuardConfigs).forEach(pagePath => {
      const config = this.pageGuardConfigs[pagePath];
      console.log(`  - ${pagePath}: ${config.description}`);
    });
  }

  /**
   * 添加页面权限配置
   */
  addPageConfig(pagePath, config) {
    this.pageGuardConfigs[this.normalizePath(pagePath)] = config;
    console.log(`新增页面权限配置: ${pagePath}`);
  }

  /**
   * 移除页面权限配置
   */
  removePageConfig(pagePath) {
    delete this.pageGuardConfigs[this.normalizePath(pagePath)];
    console.log(`移除页面权限配置: ${pagePath}`);
  }
}

// 创建全局实例
const pageGuardManager = new PageGuardManager();

// 导出
module.exports = {
  PageGuardManager,
  pageGuardManager,

  // 便捷方法
  createGuardedPage: (pageConfig, customOptions) =>
    pageGuardManager.createPageGuard(pageConfig, customOptions),

  setupGlobalGuards: () => pageGuardManager.setupPageGuards(),

  addPageConfig: (pagePath, config) => pageGuardManager.addPageConfig(pagePath, config),

  removePageConfig: pagePath => pageGuardManager.removePageConfig(pagePath),
};
