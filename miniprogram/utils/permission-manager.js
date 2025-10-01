// utils/permission-manager.js
// 权限管理工具 - 细粒度权限控制

const { authManager } = require('./auth.js');
const { roleManager } = require('./role-manager.js');
const { errorToast } = require('./error-toast.js');
const { 
  pagePermissionConfig,
  rolePermissionMapping,
  specialPermissionRules,
  permissionHelpers
} = require('./permission-config.js');

/**
 * 权限管理类
 */
class PermissionManager {
  constructor() {
    // 权限定义
    this.permissions = {
      // 作业相关权限
      'homework.view': '查看作业',
      'homework.view_all': '查看所有作业',
      'homework.view_child': '查看孩子作业',
      'homework.submit': '提交作业',
      'homework.edit': '编辑作业',
      'homework.delete': '删除作业',
      'homework.correct': '批改作业',
      'homework.manage': '管理作业',
      'homework.create': '创建作业',
      'homework.assign': '分配作业',

      // 聊天问答相关权限
      'chat.ask': '提问问题',
      'chat.view': '查看对话',
      'chat.view_all': '查看所有对话',
      'chat.view_child': '查看孩子对话',
      'chat.moderate': '审核对话',
      'chat.manage': '管理对话',
      'chat.export': '导出对话',

      // 分析报告相关权限
      'analysis.view_self': '查看个人分析',
      'analysis.view_child': '查看孩子分析',
      'analysis.view_class': '查看班级分析',
      'analysis.view_all': '查看所有分析',
      'analysis.export': '导出分析报告',
      'analysis.compare': '对比分析',
      'analysis.advanced': '高级分析',

      // 用户管理相关权限
      'user.view_self': '查看个人信息',
      'user.edit_self': '编辑个人信息',
      'user.view_family': '查看家庭信息',
      'user.manage_family': '管理家庭成员',
      'user.view_students': '查看学生信息',
      'user.manage_students': '管理学生',
      'user.view_all': '查看所有用户',

      // 个人资料相关权限
      'profile.view_self': '查看个人档案',
      'profile.edit_self': '编辑个人档案',
      'profile.view_family': '查看家庭档案',
      'profile.view_students': '查看学生档案',
      'profile.manage': '管理档案',

      // 系统设置相关权限
      'settings.view': '查看设置',
      'settings.edit': '修改设置',
      'settings.system': '系统设置',
      'settings.role_switch': '角色切换',

      // 文件上传相关权限
      'file.upload': '上传文件',
      'file.download': '下载文件',
      'file.manage': '管理文件',
      'file.view_all': '查看所有文件',

      // 通知相关权限
      'notification.receive': '接收通知',
      'notification.send': '发送通知',
      'notification.manage': '管理通知',

      // 数据导出相关权限
      'export.own_data': '导出个人数据',
      'export.child_data': '导出孩子数据',
      'export.class_data': '导出班级数据',
      'export.all_data': '导出所有数据',

      // 统计相关权限
      'stats.view_self': '查看个人统计',
      'stats.view_child': '查看孩子统计',
      'stats.view_class': '查看班级统计',
      'stats.view_all': '查看全部统计',

      // 管理员权限
      'admin.user_manage': '用户管理',
      'admin.system_config': '系统配置',
      'admin.data_manage': '数据管理',
      'admin.role_manage': '角色管理'
    };

    // 权限组合（复合权限）
    this.permissionGroups = {
      // 基础功能组
      'basic_student': [
        'homework.view', 'homework.submit', 'chat.ask', 
        'analysis.view_self', 'profile.view_self', 'user.view_self'
      ],
      'basic_parent': [
        'homework.view_child', 'chat.view_child', 'analysis.view_child',
        'profile.view_family', 'user.view_family', 'stats.view_child'
      ],
      'basic_teacher': [
        'homework.view_all', 'homework.correct', 'homework.manage',
        'chat.moderate', 'analysis.view_class', 'user.view_students'
      ],

      // 高级功能组
      'advanced_student': [
        'file.upload', 'file.download', 'export.own_data', 
        'settings.view', 'settings.role_switch'
      ],
      'advanced_parent': [
        'export.child_data', 'stats.view_child', 'notification.receive',
        'settings.view', 'settings.role_switch'
      ],
      'advanced_teacher': [
        'homework.create', 'homework.assign', 'export.class_data',
        'notification.send', 'stats.view_class', 'file.manage'
      ],

      // 管理功能组
      'management': [
        'user.manage_students', 'notification.manage', 'file.view_all',
        'stats.view_all', 'settings.system'
      ]
    };

    // 敏感操作权限（需要二次确认）
    this.sensitivePermissions = [
      'homework.delete', 'user.manage_students', 'admin.user_manage',
      'admin.system_config', 'admin.data_manage', 'export.all_data'
    ];

    // 权限检查缓存
    this.permissionCache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
  }

  /**
   * 检查用户是否有特定权限
   */
  async hasPermission(permission, userId = null) {
    try {
      // 构建缓存键
      const currentUser = userId || await authManager.getUserInfo();
      const cacheKey = `${currentUser?.id || 'anonymous'}_${permission}`;

      // 检查缓存
      if (this.permissionCache.has(cacheKey)) {
        const cached = this.permissionCache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.cacheTimeout) {
          return cached.result;
        }
      }

      // 获取用户角色
      const userRole = await authManager.getUserRole();
      
      // 检查角色权限
      const hasRolePermission = await this.checkRolePermission(permission, userRole);
      
      // 缓存结果
      this.permissionCache.set(cacheKey, {
        result: hasRolePermission,
        timestamp: Date.now()
      });

      return hasRolePermission;
    } catch (error) {
      console.error('权限检查失败:', error);
      return false;
    }
  }

  /**
   * 检查角色权限 - 使用新的配置系统
   */
  async checkRolePermission(permission, userRole) {
    try {
      const rolePermissions = rolePermissionMapping[userRole];
      if (!rolePermissions) {
        console.warn('未知角色:', userRole);
        return false;
      }

      // 检查是否在禁止列表中
      const forbiddenPermissions = rolePermissions.forbidden || [];
      const isForbidden = forbiddenPermissions.some(forbiddenPerm => {
        if (forbiddenPerm.endsWith('.*')) {
          const prefix = forbiddenPerm.slice(0, -2);
          return permission.startsWith(prefix);
        }
        return permission === forbiddenPerm;
      });

      if (isForbidden) {
        return false;
      }

      // 检查是否在允许列表中
      const allPermissions = [
        ...(rolePermissions.basic || []),
        ...(rolePermissions.advanced || []),
        ...(rolePermissions.management || [])
      ];

      return allPermissions.includes(permission);
    } catch (error) {
      console.error('角色权限检查失败:', error);
      return false;
    }
  }

  /**
   * 检查页面访问权限
   */
  async checkPageAccess(pagePath, userId = null) {
    try {
      const pageConfig = pagePermissionConfig[pagePath];
      if (!pageConfig) {
        console.log('页面无特殊权限要求:', pagePath);
        return true;
      }

      // 检查是否为公开页面
      if (pageConfig.public) {
        return true;
      }

      // 检查角色限制
      if (pageConfig.roles) {
        const userRole = await authManager.getUserRole();
        if (!pageConfig.roles.includes(userRole)) {
          console.log('角色不匹配:', { userRole, allowedRoles: pageConfig.roles });
          return false;
        }
      }

      // 检查权限要求
      if (pageConfig.permissions && pageConfig.permissions.length > 0) {
        const permissionChecks = await Promise.all(
          pageConfig.permissions.map(permission => this.hasPermission(permission, userId))
        );
        return permissionChecks.every(Boolean);
      }

      return true;
    } catch (error) {
      console.error('页面权限检查失败:', error);
      return false;
    }
  }

  /**
   * 检查用户是否有权限组中的所有权限
   */
  async hasPermissionGroup(groupName, userId = null) {
    try {
      const permissions = this.permissionGroups[groupName];
      if (!permissions) {
        console.warn('权限组不存在:', groupName);
        return false;
      }

      // 检查组内所有权限
      const checks = await Promise.all(
        permissions.map(permission => this.hasPermission(permission, userId))
      );

      return checks.every(Boolean);
    } catch (error) {
      console.error('权限组检查失败:', error);
      return false;
    }
  }

  /**
   * 检查用户是否有权限组中的任一权限
   */
  async hasAnyPermissionInGroup(groupName, userId = null) {
    try {
      const permissions = this.permissionGroups[groupName];
      if (!permissions) {
        return false;
      }

      const checks = await Promise.all(
        permissions.map(permission => this.hasPermission(permission, userId))
      );

      return checks.some(Boolean);
    } catch (error) {
      console.error('权限组检查失败:', error);
      return false;
    }
  }

  /**
   * 获取用户的所有权限
   */
  async getUserPermissions(userId = null) {
    try {
      const userRole = await authManager.getUserRole();
      const roleConfig = roleManager.getRoleConfig(userRole);
      
      return roleConfig.permissions || [];
    } catch (error) {
      console.error('获取用户权限失败:', error);
      return [];
    }
  }

  /**
   * 检查是否为敏感操作
   */
  isSensitivePermission(permission) {
    return this.sensitivePermissions.includes(permission);
  }

  /**
   * 执行敏感操作前的确认
   */
  async confirmSensitiveOperation(permission, customMessage = null) {
    const permissionName = this.permissions[permission] || permission;
    const message = customMessage || `此操作需要"${permissionName}"权限，确定要继续吗？`;

    return errorToast.confirm(
      '权限确认',
      message,
      {
        confirmText: '确认执行',
        cancelText: '取消'
      }
    );
  }

  /**
   * 权限装饰器 - 用于方法权限检查
   */
  requirePermission(permission, options = {}) {
    const { 
      showError = true, 
      errorMessage = null,
      requireConfirm = null 
    } = options;

    return (target, propertyKey, descriptor) => {
      const originalMethod = descriptor.value;

      descriptor.value = async function (...args) {
        // 检查权限
        const hasPermission = await this.hasPermission(permission);
        
        if (!hasPermission) {
          if (showError) {
            const permissionName = this.permissions[permission] || permission;
            const message = errorMessage || `您没有"${permissionName}"权限`;
            errorToast.show(message);
          }
          return;
        }

        // 敏感操作确认
        const needConfirm = requireConfirm !== null ? 
          requireConfirm : this.isSensitivePermission(permission);
          
        if (needConfirm) {
          const confirmed = await this.confirmSensitiveOperation(permission);
          if (!confirmed) {
            return;
          }
        }

        // 执行原方法
        return originalMethod.apply(this, args);
      };

      return descriptor;
    };
  }

  /**
   * 权限检查中间件 - 用于页面权限检查
   */
  async checkPagePermissions(requiredPermissions, options = {}) {
    const { 
      requireAll = true, 
      showError = true,
      redirectOnFail = true 
    } = options;

    try {
      const permissions = Array.isArray(requiredPermissions) ? 
        requiredPermissions : [requiredPermissions];

      const checks = await Promise.all(
        permissions.map(permission => this.hasPermission(permission))
      );

      const hasPermission = requireAll ? 
        checks.every(Boolean) : checks.some(Boolean);

      if (!hasPermission) {
        if (showError) {
          errorToast.show('您没有访问此页面的权限');
        }

        if (redirectOnFail) {
          // 根据角色重定向到合适页面
          const userRole = await authManager.getUserRole();
          const roleConfig = roleManager.getRoleConfig(userRole);
          
          setTimeout(() => {
            wx.redirectTo({
              url: roleConfig.homePage,
              fail: () => {
                wx.switchTab({
                  url: '/pages/index/index'
                });
              }
            });
          }, 1500);
        }

        return false;
      }

      return true;
    } catch (error) {
      console.error('页面权限检查失败:', error);
      return false;
    }
  }

  /**
   * 动态权限检查 - 根据数据内容检查权限
   */
  async checkDynamicPermission(permission, resourceData = {}) {
    try {
      // 基础权限检查
      const hasBasicPermission = await this.hasPermission(permission);
      if (!hasBasicPermission) {
        return false;
      }

      // 动态权限检查逻辑
      const userInfo = await authManager.getUserInfo();
      const userRole = await authManager.getUserRole();

      // 示例：检查是否为资源所有者
      if (resourceData.ownerId && userRole === 'student') {
        return resourceData.ownerId === userInfo.id;
      }

      // 示例：家长只能查看自己孩子的资源
      if (permission.includes('view_child') && userRole === 'parent') {
        return resourceData.studentId && 
               userInfo.children?.includes(resourceData.studentId);
      }

      // 示例：教师只能管理自己班级的资源
      if (permission.includes('view_class') && userRole === 'teacher') {
        return resourceData.classId && 
               userInfo.classes?.includes(resourceData.classId);
      }

      return true;
    } catch (error) {
      console.error('动态权限检查失败:', error);
      return false;
    }
  }

  /**
   * 批量权限检查
   */
  async checkMultiplePermissions(permissions) {
    try {
      const results = {};
      
      const checks = await Promise.all(
        permissions.map(async (permission) => {
          const hasPermission = await this.hasPermission(permission);
          return { permission, hasPermission };
        })
      );

      checks.forEach(({ permission, hasPermission }) => {
        results[permission] = hasPermission;
      });

      return results;
    } catch (error) {
      console.error('批量权限检查失败:', error);
      return {};
    }
  }

  /**
   * 清除权限缓存
   */
  clearPermissionCache(userId = null) {
    if (userId) {
      // 清除特定用户的缓存
      for (const [key] of this.permissionCache) {
        if (key.startsWith(`${userId}_`)) {
          this.permissionCache.delete(key);
        }
      }
    } else {
      // 清除所有缓存
      this.permissionCache.clear();
    }
  }

  /**
   * 获取权限名称
   */
  getPermissionName(permission) {
    return this.permissions[permission] || permission;
  }

  /**
   * 获取所有权限列表
   */
  getAllPermissions() {
    return Object.keys(this.permissions);
  }

  /**
   * 获取权限组列表
   */
  getAllPermissionGroups() {
    return Object.keys(this.permissionGroups);
  }
}

// 创建单例实例
const permissionManager = new PermissionManager();

// 导出
module.exports = {
  PermissionManager,
  permissionManager,
  
  // 便捷方法
  hasPermission: (permission, userId) => permissionManager.hasPermission(permission, userId),
  hasPermissionGroup: (groupName, userId) => permissionManager.hasPermissionGroup(groupName, userId),
  hasAnyPermissionInGroup: (groupName, userId) => permissionManager.hasAnyPermissionInGroup(groupName, userId),
  getUserPermissions: (userId) => permissionManager.getUserPermissions(userId),
  checkPagePermissions: (permissions, options) => permissionManager.checkPagePermissions(permissions, options),
  checkDynamicPermission: (permission, resourceData) => permissionManager.checkDynamicPermission(permission, resourceData),
  checkMultiplePermissions: (permissions) => permissionManager.checkMultiplePermissions(permissions),
  clearPermissionCache: (userId) => permissionManager.clearPermissionCache(userId),
  requirePermission: (permission, options) => permissionManager.requirePermission(permission, options),
  getPermissionName: (permission) => permissionManager.getPermissionName(permission),
  getAllPermissions: () => permissionManager.getAllPermissions(),
  getAllPermissionGroups: () => permissionManager.getAllPermissionGroups()
};