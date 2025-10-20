// utils/api-permission-guard.js - API调用权限管理系统

const { permissionManager } = require('./permission-manager.js');
const { authManager } = require('./auth.js');
const { errorToast } = require('./error-toast.js');

/**
 * API权限配置映射
 */
const API_PERMISSION_CONFIG = {
  // 作业相关API
  'GET /homework': {
    permission: 'homework.view',
    roles: ['student', 'parent', 'teacher'],
    description: '获取作业列表'
  },
  'GET /homework/:id': {
    permission: 'homework.view',
    roles: ['student', 'parent', 'teacher'],
    description: '获取作业详情'
  },
  'POST /homework': {
    permission: 'homework.create',
    roles: ['teacher'],
    description: '创建作业'
  },
  'PUT /homework/:id': {
    permission: 'homework.manage',
    roles: ['teacher'],
    description: '更新作业'
  },
  'DELETE /homework/:id': {
    permission: 'homework.delete',
    roles: ['teacher', 'student'],
    description: '删除作业',
    sensitive: true
  },
  'POST /homework/:id/submit': {
    permission: 'homework.submit',
    roles: ['student'],
    description: '提交作业'
  },
  'POST /homework/:id/correct': {
    permission: 'homework.correct',
    roles: ['teacher'],
    description: '批改作业'
  },

  // 问答相关API
  'POST /chat/ask': {
    permission: 'chat.ask',
    roles: ['student', 'parent', 'teacher'],
    description: '发起问答'
  },
  'GET /chat/history': {
    permission: 'chat.view',
    roles: ['student', 'parent', 'teacher'],
    description: '获取问答历史'
  },
  'GET /chat/sessions': {
    permission: 'chat.view',
    roles: ['student', 'parent', 'teacher'],
    description: '获取会话列表'
  },
  'DELETE /chat/sessions/:id': {
    permission: 'chat.manage',
    roles: ['student', 'teacher'],
    description: '删除会话',
    sensitive: true
  },

  // 用户信息相关API
  'GET /auth/me': {
    permission: 'user.view_self',
    roles: ['student', 'parent', 'teacher'],
    description: '获取个人信息'
  },
  'PUT /auth/profile': {
    permission: 'profile.edit_self',
    roles: ['student', 'parent', 'teacher'],
    description: '更新个人信息'
  },
  'POST /auth/avatar': {
    permission: 'file.upload',
    roles: ['student', 'parent', 'teacher'],
    description: '上传头像'
  },
  'DELETE /auth/avatar': {
    permission: 'profile.edit_self',
    roles: ['student', 'parent', 'teacher'],
    description: '删除头像'
  },

  // 分析报告相关API
  'GET /analysis/report': {
    permission: 'analysis.view_self',
    roles: ['student', 'parent', 'teacher'],
    description: '获取学习报告'
  },
  'GET /analysis/progress': {
    permission: 'analysis.view_self',
    roles: ['student', 'parent', 'teacher'],
    description: '获取学习进度'
  },
  'POST /analysis/export': {
    permission: 'export.own_data',
    roles: ['student', 'parent', 'teacher'],
    description: '导出分析数据',
    sensitive: true
  },

  // 学生管理相关API
  'GET /students': {
    permission: 'user.view_students',
    roles: ['teacher'],
    description: '获取学生列表'
  },
  'GET /students/:id': {
    permission: 'user.view_students',
    roles: ['teacher', 'parent'],
    description: '获取学生详情'
  },
  'PUT /students/:id': {
    permission: 'user.manage_students',
    roles: ['teacher'],
    description: '更新学生信息'
  },

  // 文件相关API
  'POST /files/upload': {
    permission: 'file.upload',
    roles: ['student', 'parent', 'teacher'],
    description: '上传文件'
  },
  'GET /files': {
    permission: 'file.download',
    roles: ['student', 'parent', 'teacher'],
    description: '获取文件列表'
  },
  'DELETE /files/:id': {
    permission: 'file.manage',
    roles: ['teacher'],
    description: '删除文件',
    sensitive: true
  },

  // 设置相关API
  'GET /settings': {
    permission: 'settings.view',
    roles: ['student', 'parent', 'teacher'],
    description: '获取设置'
  },
  'PUT /settings': {
    permission: 'settings.edit',
    roles: ['student', 'parent', 'teacher'],
    description: '更新设置'
  },

  // 管理员API
  'GET /admin/users': {
    permission: 'admin.user_manage',
    roles: ['admin'],
    description: '管理用户列表'
  },
  'PUT /admin/config': {
    permission: 'admin.system_config',
    roles: ['admin'],
    description: '系统配置',
    sensitive: true
  }
};

/**
 * API权限守卫类
 */
class ApiPermissionGuard {
  constructor() {
    this.permissionCache = new Map();
    this.cacheTimeout = 2 * 60 * 1000; // 2分钟缓存
    this.requestLog = [];
    this.maxLogSize = 100;
  }

  /**
   * 检查API调用权限
   */
  async checkApiPermission(method, url, options = {}) {
    try {
      const apiKey = this.normalizeApiKey(method, url);
      const config = API_PERMISSION_CONFIG[apiKey];

      if (!config) {
        // 没有配置的API默认允许（向后兼容）
        console.warn(`API ${apiKey} 没有权限配置，默认允许访问`);
        return { 
          success: true, 
          reason: 'no_config',
          message: 'API没有权限配置' 
        };
      }

      // 检查缓存
      const cacheKey = `${apiKey}_${await this.getUserCacheKey()}`;
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        return cached;
      }

      // 执行权限检查
      const result = await this.performPermissionCheck(config, apiKey, options);
      
      // 缓存结果（只缓存成功的结果）
      if (result.success) {
        this.setCache(cacheKey, result);
      }

      // 记录请求日志
      this.logApiRequest(method, url, result, options);

      return result;

    } catch (error) {
      console.error('API权限检查失败:', error);
      return { 
        success: false, 
        reason: 'check_error',
        message: 'API权限检查失败' 
      };
    }
  }

  /**
   * 执行权限检查
   */
  async performPermissionCheck(config, apiKey, options) {
    // 1. 登录状态检查
    const isLoggedIn = await authManager.isLoggedIn();
    if (!isLoggedIn) {
      return { 
        success: false, 
        reason: 'not_logged_in',
        message: '请先登录',
        requireLogin: true
      };
    }

    // 2. Token有效性检查
    const isTokenValid = await authManager.isTokenValid();
    if (!isTokenValid) {
      try {
        await authManager.refreshToken();
      } catch (error) {
        return { 
          success: false, 
          reason: 'token_invalid',
          message: '登录已过期，请重新登录',
          requireLogin: true
        };
      }
    }

    // 3. 角色权限检查
    if (config.roles && config.roles.length > 0) {
      const userRole = await authManager.getUserRole();
      if (!config.roles.includes(userRole)) {
        return { 
          success: false, 
          reason: 'role_not_allowed',
          message: `API ${apiKey} 需要角色：${config.roles.join('、')}`,
          userRole,
          requiredRoles: config.roles
        };
      }
    }

    // 4. 具体权限检查
    if (config.permission) {
      const hasPermission = await permissionManager.hasPermission(config.permission);
      if (!hasPermission) {
        return { 
          success: false, 
          reason: 'permission_denied',
          message: `您没有 ${config.description} 的权限`,
          requiredPermission: config.permission
        };
      }
    }

    // 5. 敏感操作检查
    if (config.sensitive && !options.confirmed) {
      return { 
        success: false, 
        reason: 'requires_confirmation',
        message: `${config.description} 是敏感操作，需要用户确认`,
        sensitive: true
      };
    }

    // 6. 资源所有权检查
    if (options.resourceOwnerId) {
      const ownershipValid = await this.checkResourceOwnership(options);
      if (!ownershipValid) {
        return { 
          success: false, 
          reason: 'ownership_denied',
          message: '您只能操作自己的资源'
        };
      }
    }

    return { 
      success: true, 
      message: 'API权限验证通过',
      config 
    };
  }

  /**
   * 检查资源所有权
   */
  async checkResourceOwnership(options) {
    try {
      if (!options.resourceOwnerId) {
        return true; // 没有所有者信息时允许通过
      }

      const userInfo = await authManager.getUserInfo();
      const userRole = await authManager.getUserRole();

      // 管理员可以访问所有资源
      if (userRole === 'admin') {
        return true;
      }

      // 检查是否是资源拥有者
      if (options.resourceOwnerId === userInfo.id) {
        return true;
      }

      // 教师可以访问自己班级学生的资源
      if (userRole === 'teacher' && options.classId && userInfo.classes) {
        return userInfo.classes.includes(options.classId);
      }

      // 家长可以访问自己孩子的资源
      if (userRole === 'parent' && options.studentId && userInfo.children) {
        return userInfo.children.includes(options.studentId);
      }

      return false;
    } catch (error) {
      console.warn('资源所有权检查失败:', error);
      return false;
    }
  }

  /**
   * 标准化API键
   */
  normalizeApiKey(method, url) {
    // 处理动态路径参数
    let normalizedUrl = url;
    
    // 替换ID参数为占位符
    normalizedUrl = normalizedUrl.replace(/\/\d+/g, '/:id');
    normalizedUrl = normalizedUrl.replace(/\/[a-f0-9-]{36}/g, '/:id'); // UUID
    
    // 移除查询参数
    normalizedUrl = normalizedUrl.split('?')[0];
    
    return `${method.toUpperCase()} ${normalizedUrl}`;
  }

  /**
   * 获取用户缓存键
   */
  async getUserCacheKey() {
    try {
      const userInfo = await authManager.getUserInfo();
      const userRole = await authManager.getUserRole();
      return `${userInfo?.id || 'anonymous'}_${userRole}`;
    } catch (error) {
      return 'anonymous';
    }
  }

  /**
   * 缓存相关方法
   */
  getFromCache(key) {
    const cached = this.permissionCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.result;
    }
    return null;
  }

  setCache(key, result) {
    this.permissionCache.set(key, {
      result,
      timestamp: Date.now()
    });
  }

  /**
   * 清理缓存
   */
  clearCache() {
    this.permissionCache.clear();
  }

  /**
   * 记录API请求日志
   */
  logApiRequest(method, url, result, options) {
    try {
      const logEntry = {
        timestamp: Date.now(),
        method,
        url,
        success: result.success,
        reason: result.reason,
        userRole: options.userRole || 'unknown',
        ip: options.ip || 'unknown'
      };

      this.requestLog.push(logEntry);

      // 限制日志大小
      if (this.requestLog.length > this.maxLogSize) {
        this.requestLog.shift();
      }

      // 调试模式下输出日志
      if (options.debug) {
        console.log('API权限检查日志:', logEntry);
      }
    } catch (error) {
      console.warn('记录API日志失败:', error);
    }
  }

  /**
   * 为API客户端创建拦截器
   */
  createApiInterceptor() {
    return {
      // 请求拦截器
      request: async (config) => {
        try {
          const method = config.method || 'GET';
          const url = config.url || '';

          const permissionResult = await this.checkApiPermission(method, url, {
            resourceOwnerId: config.resourceOwnerId,
            classId: config.classId,
            studentId: config.studentId,
            confirmed: config.confirmed,
            debug: config.debug
          });

          if (!permissionResult.success) {
            // 权限检查失败，拦截请求
            const error = new Error(permissionResult.message);
            error.permissionResult = permissionResult;
            throw error;
          }

          // 权限检查通过，继续请求
          return config;
        } catch (error) {
          throw error;
        }
      },

      // 响应拦截器
      response: (response) => {
        // 成功响应的处理
        return response;
      },

      // 错误拦截器
      error: (error) => {
        if (error.permissionResult) {
          // 处理权限相关错误
          this.handlePermissionError(error.permissionResult);
        }
        throw error;
      }
    };
  }

  /**
   * 处理权限错误
   */
  handlePermissionError(result) {
    switch (result.reason) {
      case 'not_logged_in':
      case 'token_invalid':
        this.handleLoginRequired();
        break;
      case 'role_not_allowed':
        this.handleRoleNotAllowed(result);
        break;
      case 'permission_denied':
        this.handlePermissionDenied(result);
        break;
      case 'requires_confirmation':
        this.handleSensitiveOperation(result);
        break;
      case 'ownership_denied':
        this.handleOwnershipDenied(result);
        break;
      default:
        errorToast.show(result.message || 'API访问被拒绝');
    }
  }

  /**
   * 处理登录要求
   */
  handleLoginRequired() {
    wx.showModal({
      title: '需要登录',
      content: '请先登录以继续使用',
      showCancel: false,
      confirmText: '去登录',
      success: () => {
        wx.redirectTo({
          url: '/pages/login/index'
        });
      }
    });
  }

  /**
   * 处理角色权限不足
   */
  handleRoleNotAllowed(result) {
    const roleNames = {
      'student': '学生',
      'parent': '家长',
      'teacher': '教师',
      'admin': '管理员'
    };

    const requiredRoleNames = result.requiredRoles
      .map(role => roleNames[role] || role)
      .join('、');

    wx.showModal({
      title: '角色权限不足',
      content: `此功能需要${requiredRoleNames}权限`,
      showCancel: true,
      cancelText: '返回',
      confirmText: '切换角色',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: '/pages/role-selection/index'
          });
        }
      }
    });
  }

  /**
   * 处理权限被拒绝
   */
  handlePermissionDenied(result) {
    wx.showModal({
      title: '权限不足',
      content: result.message,
      showCancel: false,
      confirmText: '我知道了'
    });
  }

  /**
   * 处理敏感操作
   */
  handleSensitiveOperation(result) {
    wx.showModal({
      title: '敏感操作确认',
      content: result.message,
      confirmText: '确认执行',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          // 用户确认，重新发起带确认标记的请求
          // 这里需要业务层配合处理
          console.log('用户确认敏感操作');
        }
      }
    });
  }

  /**
   * 处理所有权被拒绝
   */
  handleOwnershipDenied(result) {
    wx.showToast({
      title: result.message,
      icon: 'none',
      duration: 3000
    });
  }

  /**
   * 获取API权限配置
   */
  getApiConfig(method, url) {
    const apiKey = this.normalizeApiKey(method, url);
    return API_PERMISSION_CONFIG[apiKey];
  }

  /**
   * 获取请求日志
   */
  getRequestLog() {
    return [...this.requestLog];
  }

  /**
   * 获取调试信息
   */
  getDebugInfo() {
    return {
      cacheSize: this.permissionCache.size,
      logSize: this.requestLog.length,
      apiConfigs: Object.keys(API_PERMISSION_CONFIG).length,
      recentLogs: this.requestLog.slice(-10)
    };
  }
}

// 创建单例实例
const apiPermissionGuard = new ApiPermissionGuard();

module.exports = {
  apiPermissionGuard,
  ApiPermissionGuard,
  API_PERMISSION_CONFIG
};