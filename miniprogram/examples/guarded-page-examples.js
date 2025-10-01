// 使用页面权限守卫管理器的示例页面

const { createGuardedPage } = require('../utils/page-guard-manager.js');
const { permissionManager } = require('../utils/permission-manager.js');

/**
 * 示例1：简单的受保护页面
 * 使用预配置的权限守卫
 */
const simpleProtectedPage = createGuardedPage({
  pagePath: 'pages/homework/list/index',
  
  data: {
    homeworkList: []
  },

  async onLoad(options) {
    console.log('作业列表页面加载 - 已通过权限验证');
    // 权限检查已在守卫中完成，这里直接编写业务逻辑
    await this.loadHomeworkList();
  },

  async loadHomeworkList() {
    // 加载作业列表的业务逻辑
    console.log('加载作业列表');
  }
});

/**
 * 示例2：自定义权限检查的页面
 */
const customPermissionPage = createGuardedPage({
  pagePath: 'pages/homework/detail/index',
  
  data: {
    homeworkDetail: null,
    canEdit: false
  },

  async onLoad(options) {
    console.log('作业详情页面加载');
    
    const homeworkId = options.id;
    await this.loadHomeworkDetail(homeworkId);
    await this.checkEditPermission(homeworkId);
  },

  async loadHomeworkDetail(homeworkId) {
    // 加载作业详情
    console.log('加载作业详情:', homeworkId);
  },

  async checkEditPermission(homeworkId) {
    // 检查是否有编辑权限
    const canEdit = await permissionManager.hasPermission('homework.edit');
    this.setData({ canEdit });
  }
}, {
  // 自定义权限检查
  customPermissionCheck: async function() {
    // 这里可以添加页面特定的权限检查逻辑
    const hasSpecialAccess = await permissionManager.hasPermission('homework.view');
    if (!hasSpecialAccess) {
      wx.showToast({
        title: '权限不足',
        icon: 'none'
      });
      return false;
    }
    return true;
  }
});

/**
 * 示例3：需要动态权限检查的页面
 * 例如：家长只能查看自己孩子的学习报告
 */
const dynamicPermissionPage = createGuardedPage({
  pagePath: 'pages/analysis/report/index',
  
  data: {
    studentId: '',
    reportData: null,
    canViewDetail: false
  },

  async onLoad(options) {
    console.log('分析报告页面加载');
    
    const studentId = options.studentId;
    this.setData({ studentId });
    
    // 检查是否能查看特定学生的报告
    const canView = await this.checkStudentAccess(studentId);
    if (!canView) {
      wx.showModal({
        title: '访问限制',
        content: '您只能查看自己孩子的学习报告',
        showCancel: false,
        success: () => {
          wx.navigateBack();
        }
      });
      return;
    }
    
    await this.loadReportData(studentId);
  },

  async checkStudentAccess(studentId) {
    // 动态检查是否有权访问特定学生的数据
    return await permissionManager.checkDynamicPermission(
      'analysis.view_child',
      { studentId }
    );
  },

  async loadReportData(studentId) {
    console.log('加载学生报告:', studentId);
    // 加载报告数据的业务逻辑
  }
});

/**
 * 示例4：多角色共享页面
 * 根据不同角色显示不同功能
 */
const multiRolePage = createGuardedPage({
  pagePath: 'pages/homework/list/index',
  
  data: {
    userRole: '',
    homeworkList: [],
    canSubmit: false,
    canCorrect: false,
    canCreate: false
  },

  async onLoad(options) {
    console.log('多角色作业页面加载');
    
    await this.initRoleBasedFeatures();
    await this.loadHomeworkList();
  },

  async initRoleBasedFeatures() {
    const userRole = await roleManager.getCurrentUserRole();
    
    // 根据角色检查不同权限
    const [canSubmit, canCorrect, canCreate] = await Promise.all([
      permissionManager.hasPermission('homework.submit'),
      permissionManager.hasPermission('homework.correct'),
      permissionManager.hasPermission('homework.create')
    ]);

    this.setData({
      userRole,
      canSubmit,
      canCorrect,
      canCreate
    });

    console.log('角色权限检查结果:', {
      userRole, canSubmit, canCorrect, canCreate
    });
  },

  async loadHomeworkList() {
    // 根据角色加载不同的作业数据
    const userRole = this.data.userRole;
    let apiMethod;
    
    switch (userRole) {
      case 'student':
        apiMethod = 'getStudentHomework';
        break;
      case 'parent':
        apiMethod = 'getChildHomework';
        break;
      case 'teacher':
        apiMethod = 'getClassHomework';
        break;
      default:
        console.warn('未知角色:', userRole);
        return;
    }
    
    console.log('使用API方法:', apiMethod);
    // 调用相应的API加载数据
  },

  // 学生功能：提交作业
  async submitHomework(homeworkId) {
    if (!this.data.canSubmit) {
      wx.showToast({
        title: '无权限提交作业',
        icon: 'none'
      });
      return;
    }
    
    console.log('提交作业:', homeworkId);
    // 提交作业的业务逻辑
  },

  // 教师功能：批改作业
  async correctHomework(homeworkId) {
    if (!this.data.canCorrect) {
      wx.showToast({
        title: '无权限批改作业',
        icon: 'none'
      });
      return;
    }
    
    console.log('批改作业:', homeworkId);
    // 批改作业的业务逻辑
  },

  // 教师功能：创建作业
  async createHomework() {
    if (!this.data.canCreate) {
      wx.showToast({
        title: '无权限创建作业',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: '/pages/homework/create/index'
    });
  }
});

/**
 * 示例5：敏感操作页面
 * 需要额外确认的页面
 */
const sensitiveOperationPage = createGuardedPage({
  pagePath: 'pages/admin/user-manage/index',
  
  data: {
    userList: [],
    selectedUsers: []
  },

  async onLoad(options) {
    console.log('用户管理页面加载');
    await this.loadUserList();
  },

  async loadUserList() {
    console.log('加载用户列表');
    // 加载用户列表的业务逻辑
  },

  // 删除用户 - 敏感操作
  async deleteUsers() {
    const selectedUsers = this.data.selectedUsers;
    if (selectedUsers.length === 0) {
      wx.showToast({
        title: '请选择要删除的用户',
        icon: 'none'
      });
      return;
    }

    // 敏感操作确认
    const confirmed = await permissionManager.confirmSensitiveOperation(
      'user.manage_students',
      `确定要删除 ${selectedUsers.length} 个用户吗？此操作不可撤销。`
    );

    if (!confirmed) {
      return;
    }

    try {
      console.log('执行删除用户操作:', selectedUsers);
      // 执行删除逻辑
      
      wx.showToast({
        title: '删除成功',
        icon: 'success'
      });
      
      // 重新加载列表
      await this.loadUserList();
    } catch (error) {
      console.error('删除用户失败:', error);
      wx.showToast({
        title: '删除失败',
        icon: 'error'
      });
    }
  }
});

/**
 * 示例6：无需权限的公开页面
 */
const publicPage = {
  data: {
    helpContent: ''
  },

  onLoad(options) {
    console.log('帮助页面加载 - 公开页面无需权限检查');
    this.loadHelpContent();
  },

  loadHelpContent() {
    console.log('加载帮助内容');
    // 加载帮助内容的业务逻辑
  }
};

// 使用示例
module.exports = {
  simpleProtectedPage,
  customPermissionPage,
  dynamicPermissionPage,
  multiRolePage,
  sensitiveOperationPage,
  publicPage
};

// 在实际页面文件中的使用方式：
/*
// pages/homework/list/index.js
const { createGuardedPage } = require('../../utils/page-guard-manager.js');

Page(createGuardedPage({
  pagePath: 'pages/homework/list/index',
  
  data: {
    homeworkList: []
  },

  async onLoad(options) {
    // 权限检查已完成，直接编写业务逻辑
    await this.loadHomeworkList();
  },

  async loadHomeworkList() {
    // 业务逻辑
  }
}));
*/