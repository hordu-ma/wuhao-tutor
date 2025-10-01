// utils/route-guard.js
// 路由守卫工具 - 页面登录状态检查

const { authManager } = require('./auth.js');
const { permissionManager } = require('./permission-manager.js');
const { roleManager } = require('./role-manager.js');

/**
 * 路由守卫类
 */
class RouteGuard {
  constructor() {
    // 不需要登录的页面列表
    this.publicPages = [
      'pages/login/index',
      'pages/index/index' // 首页可以不登录访问，但功能会受限
    ];

    // 页面权限映射 - 更精细的权限控制
    this.pagePermissions = {
      // 作业相关页面
      'pages/homework/list/index': ['homework.view'],
      'pages/homework/detail/index': ['homework.view'],
      'pages/homework/submit/index': ['homework.submit'],
      
      // 问答相关页面
      'pages/chat/index/index': ['chat.ask'],
      'pages/chat/detail/index': ['chat.view'],
      
      // 分析报告相关页面
      'pages/analysis/report/index': ['analysis.view_self'],
      'pages/analysis/progress/index': ['analysis.view_child'],
      
      // 个人中心相关页面
      'pages/profile/index/index': ['profile.view_self'],
      'pages/profile/settings/index': ['settings.view'],
      'pages/profile/help/index': [], // 无特殊权限要求
      
      // 角色选择页面
      'pages/role-selection/index': ['settings.role_switch']
    };
  }

  /**
   * 检查是否需要登录
   */
  isPublicPage(pagePath) {
    return this.publicPages.some(path => pagePath.includes(path));
  }

  /**
   * 检查页面权限
   */
  async hasPagePermission(pagePath) {
    try {
      // 使用权限管理器的页面访问检查
      return await permissionManager.checkPageAccess(pagePath);
    } catch (error) {
      console.error('检查页面权限失败:', error);
      return true; // 错误时默认允许访问
    }
  }

  /**
   * 获取页面所需权限
   */
  getPagePermissions(pagePath) {
    // 尝试精确匹配
    for (const [path, permissions] of Object.entries(this.pagePermissions)) {
      if (pagePath.includes(path.replace('pages/', ''))) {
        return permissions;
      }
    }
    return [];
  }

  /**
   * 检查角色权限 (兼容性方法)
   */
  async hasRolePermission(role, pagePath) {
    // 使用新的权限系统
    return await this.hasPagePermission(pagePath);
  }

  /**
   * 页面级路由守卫
   * 在页面的 onLoad 方法中调用
   */
  async checkPageAuth(pagePath, options = {}) {
    try {
      // 获取当前页面路径
      const currentPath = pagePath || this.getCurrentPagePath();
      
      console.log('路由守卫检查:', currentPath);

      // 公共页面直接通过
      if (this.isPublicPage(currentPath)) {
        console.log('公共页面，无需登录验证');
        return { success: true, needLogin: false };
      }

      // 检查登录状态
      const isLoggedIn = await authManager.isLoggedIn();
      
      if (!isLoggedIn) {
        console.log('用户未登录，跳转到登录页');
        this.redirectToLogin(currentPath);
        return { success: false, needLogin: true };
      }

      // 检查Token有效性
      const isTokenValid = await authManager.isTokenValid();
      if (!isTokenValid) {
        console.log('Token无效，尝试刷新');
        try {
          await authManager.refreshToken();
          console.log('Token刷新成功');
        } catch (refreshError) {
          console.error('Token刷新失败:', refreshError);
          this.redirectToLogin(currentPath);
          return { success: false, needLogin: true };
        }
      }

      // 检查角色权限
      if (options.requireRole) {
        const userRole = await authManager.getUserRole();
        const hasPermission = await authManager.checkPermission(options.requireRole);
        
        if (!hasPermission) {
          console.log('权限不足:', { userRole, requireRole: options.requireRole });
          this.showPermissionDenied();
          return { success: false, needLogin: false, permissionDenied: true };
        }
      }

      // 检查页面权限
      const hasPermission = await this.hasPagePermission(currentPath);
      if (!hasPermission) {
        console.log('页面权限不足:', { pagePath: currentPath });
        this.showPermissionDenied();
        return { success: false, needLogin: false, permissionDenied: true };
      }

      console.log('路由守卫验证通过');
      return { success: true, needLogin: false };

    } catch (error) {
      console.error('路由守卫检查失败:', error);
      // 出错时为了安全起见，要求重新登录
      this.redirectToLogin(pagePath);
      return { success: false, needLogin: true, error };
    }
  }

  /**
   * 获取当前页面路径
   */
  getCurrentPagePath() {
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];
    return currentPage ? currentPage.route : '';
  }

  /**
   * 跳转到登录页
   */
  redirectToLogin(returnPath) {
    const loginUrl = returnPath 
      ? `/pages/login/index?returnPath=${encodeURIComponent(returnPath)}`
      : '/pages/login/index';
    
    wx.redirectTo({
      url: loginUrl,
      fail: () => {
        // 如果redirectTo失败，尝试reLaunch
        wx.reLaunch({
          url: '/pages/login/index'
        });
      }
    });
  }

  /**
   * 显示权限不足提示
   */
  showPermissionDenied() {
    wx.showModal({
      title: '访问受限',
      content: '您当前的角色无权访问此页面',
      showCancel: false,
      confirmText: '返回',
      success: () => {
        // 返回上一页或首页
        const pages = getCurrentPages();
        if (pages.length > 1) {
          wx.navigateBack();
        } else {
          wx.switchTab({
            url: '/pages/index/index'
          });
        }
      }
    });
  }

  /**
   * 创建页面守卫混入
   * 使用方法：
   * const pageWithGuard = routeGuard.createPageGuard({
   *   requireAuth: true,
   *   requireRole: 'teacher',
   *   onLoad() {
   *     // 页面逻辑
   *   }
   * });
   * Page(pageWithGuard);
   */
  createPageGuard(pageConfig) {
    const originalOnLoad = pageConfig.onLoad || function() {};
    const originalOnShow = pageConfig.onShow || function() {};
    
    const guardOptions = {
      requireRole: pageConfig.requireRole
    };

    pageConfig.onLoad = async function(options) {
      // 执行路由守卫检查
      const guardResult = await routeGuard.checkPageAuth(null, guardOptions);
      
      if (guardResult.success) {
        // 验证通过，执行原始onLoad
        return originalOnLoad.call(this, options);
      } else {
        // 验证失败，页面不应该继续加载
        console.log('页面访问被路由守卫拦截');
        return;
      }
    };

    pageConfig.onShow = async function() {
      // 页面显示时再次检查（防止在其他页面登出）
      const isLoggedIn = await authManager.isLoggedIn();
      
      if (!isLoggedIn && !routeGuard.isPublicPage(routeGuard.getCurrentPagePath())) {
        routeGuard.redirectToLogin();
        return;
      }
      
      // 验证通过，执行原始onShow
      return originalOnShow.call(this);
    };

    return pageConfig;
  }

  /**
   * 简化的页面守卫装饰器
   */
  requireAuth(requireRole = null) {
    return (pageConfig) => {
      if (requireRole) {
        pageConfig.requireRole = requireRole;
      }
      return this.createPageGuard(pageConfig);
    };
  }
}

// 创建单例实例
const routeGuard = new RouteGuard();

// 导出
module.exports = {
  RouteGuard,
  routeGuard,
  
  // 便捷方法
  checkPageAuth: (pagePath, options) => routeGuard.checkPageAuth(pagePath, options),
  requireAuth: (requireRole) => routeGuard.requireAuth(requireRole),
  createPageGuard: (pageConfig) => routeGuard.createPageGuard(pageConfig),
  
  // 手动检查方法（在页面中直接调用）
  async checkAuth(options = {}) {
    return routeGuard.checkPageAuth(null, options);
  }
};