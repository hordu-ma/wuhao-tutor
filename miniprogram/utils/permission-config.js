// 权限配置文件 - 统一管理页面权限和角色权限映射

/**
 * 页面权限配置映射
 * 定义每个页面需要的最低权限要求
 */
const pagePermissionConfig = {
  // 作业相关页面
  'pages/homework/list/index': {
    permissions: ['homework.view'],
    description: '作业列表页面'
  },
  'pages/homework/detail/index': {
    permissions: ['homework.view'],
    description: '作业详情页面'
  },
  'pages/homework/submit/index': {
    permissions: ['homework.submit'],
    description: '作业提交页面',
    roles: ['student'] // 限制只有学生可以访问
  },

  // 问答相关页面
  'pages/chat/index/index': {
    permissions: ['chat.ask'],
    description: 'AI问答主页',
    roles: ['student'] // 主要面向学生
  },
  'pages/chat/detail/index': {
    permissions: ['chat.view'],
    description: '对话详情页面'
  },

  // 分析报告相关页面
  'pages/analysis/report/index': {
    permissions: ['analysis.view_self'],
    description: '个人学习报告',
    dynamicPermission: true // 需要动态判断权限
  },
  'pages/analysis/progress/index': {
    permissions: ['analysis.view_child'],
    description: '学习进度分析',
    roles: ['parent', 'teacher']
  },

  // 个人中心相关页面
  'pages/profile/index/index': {
    permissions: ['profile.view_self'],
    description: '个人中心主页'
  },
  'pages/profile/settings/index': {
    permissions: ['settings.view'],
    description: '设置页面'
  },
  'pages/profile/help/index': {
    permissions: [], // 无特殊权限要求
    description: '帮助页面',
    public: true
  },

  // 角色选择页面
  'pages/role-selection/index': {
    permissions: ['settings.role_switch'],
    description: '角色选择页面'
  }
};

/**
 * 角色权限映射配置
 * 定义每个角色拥有的详细权限
 */
const rolePermissionMapping = {
  student: {
    // 基础权限
    basic: [
      'homework.view',
      'homework.submit',
      'chat.ask',
      'chat.view',
      'analysis.view_self',
      'profile.view_self',
      'user.view_self'
    ],
    // 高级权限
    advanced: [
      'file.upload',
      'file.download',
      'export.own_data',
      'stats.view_self',
      'settings.view',
      'settings.role_switch'
    ],
    // 限制权限（明确不能访问的功能）
    forbidden: [
      'homework.correct',
      'homework.manage',
      'homework.create',
      'homework.assign',
      'user.manage_students',
      'analysis.view_all',
      'chat.moderate',
      'admin.*'
    ]
  },

  parent: {
    // 基础权限
    basic: [
      'homework.view_child',
      'chat.view_child',
      'analysis.view_child',
      'profile.view_family',
      'user.view_family',
      'stats.view_child'
    ],
    // 高级权限
    advanced: [
      'export.child_data',
      'notification.receive',
      'settings.view',
      'settings.role_switch',
      'file.download'
    ],
    // 限制权限
    forbidden: [
      'homework.submit',
      'chat.ask',
      'homework.correct',
      'homework.create',
      'user.manage_students',
      'admin.*'
    ]
  },

  teacher: {
    // 基础权限
    basic: [
      'homework.view_all',
      'homework.correct',
      'homework.manage',
      'chat.moderate',
      'analysis.view_class',
      'user.view_students',
      'profile.view_students'
    ],
    // 高级权限
    advanced: [
      'homework.create',
      'homework.assign',
      'user.manage_students',
      'export.class_data',
      'notification.send',
      'stats.view_class',
      'file.manage',
      'settings.view',
      'settings.role_switch'
    ],
    // 管理权限
    management: [
      'notification.manage',
      'file.view_all',
      'stats.view_all'
    ],
    // 限制权限
    forbidden: [
      'admin.system_config',
      'admin.data_manage',
      'export.all_data'
    ]
  }
};

/**
 * 特殊权限规则配置
 */
const specialPermissionRules = {
  // 动态权限规则
  dynamic: {
    'analysis.view_child': {
      condition: 'isParentOfTarget',
      description: '只能查看自己孩子的分析'
    },
    'homework.view_child': {
      condition: 'isParentOfTarget',
      description: '只能查看自己孩子的作业'
    },
    'chat.view_child': {
      condition: 'isParentOfTarget',
      description: '只能查看自己孩子的对话'
    }
  },

  // 时间限制权限
  timeRestricted: {
    'homework.submit': {
      timeRange: '06:00-23:00',
      description: '作业提交时间限制'
    },
    'chat.ask': {
      timeRange: '06:00-23:00',
      description: 'AI问答时间限制'
    }
  },

  // 敏感操作权限（需要二次确认）
  sensitive: [
    'homework.delete',
    'user.manage_students',
    'export.all_data',
    'admin.user_manage',
    'admin.system_config',
    'admin.data_manage'
  ]
};

/**
 * 权限组合规则
 */
const permissionCombinationRules = {
  // 互斥权限（不能同时拥有）
  mutuallyExclusive: [
    ['homework.submit', 'homework.correct'], // 学生不能批改作业
    ['chat.ask', 'chat.moderate'] // 提问者不能审核自己的对话
  ],

  // 依赖权限（拥有某权限必须先有基础权限）
  dependencies: {
    'homework.manage': ['homework.view_all'],
    'homework.create': ['homework.manage'],
    'user.manage_students': ['user.view_students'],
    'analysis.view_all': ['analysis.view_class'],
    'export.class_data': ['analysis.view_class']
  }
};

/**
 * 权限检查辅助函数
 */
const permissionHelpers = {
  /**
   * 检查用户是否为目标的父母
   */
  async isParentOfTarget(userId, targetId) {
    try {
      // 这里应该调用后端API检查家庭关系
      // 暂时返回模拟数据
      const familyRelation = await authManager.checkFamilyRelation(userId, targetId);
      return familyRelation && familyRelation.relation === 'parent';
    } catch (error) {
      console.error('检查家庭关系失败:', error);
      return false;
    }
  },

  /**
   * 检查时间限制
   */
  checkTimeRestriction(timeRange) {
    if (!timeRange) return true;
    
    const [startTime, endTime] = timeRange.split('-');
    const now = new Date();
    const currentTime = now.getHours() * 100 + now.getMinutes();
    const start = parseInt(startTime.replace(':', ''));
    const end = parseInt(endTime.replace(':', ''));
    
    return currentTime >= start && currentTime <= end;
  },

  /**
   * 检查权限依赖
   */
  checkPermissionDependencies(permission, userPermissions) {
    const dependencies = permissionCombinationRules.dependencies[permission];
    if (!dependencies) return true;
    
    return dependencies.every(dep => userPermissions.includes(dep));
  },

  /**
   * 检查互斥权限
   */
  checkMutuallyExclusive(userPermissions) {
    for (const exclusiveGroup of permissionCombinationRules.mutuallyExclusive) {
      const hasConflict = exclusiveGroup.filter(perm => 
        userPermissions.includes(perm)
      ).length > 1;
      
      if (hasConflict) {
        return { valid: false, conflict: exclusiveGroup };
      }
    }
    return { valid: true };
  }
};

module.exports = {
  pagePermissionConfig,
  rolePermissionMapping,
  specialPermissionRules,
  permissionCombinationRules,
  permissionHelpers
};