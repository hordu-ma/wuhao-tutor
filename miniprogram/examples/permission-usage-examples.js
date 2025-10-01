// 页面权限守卫使用示例
// 展示如何在不同页面中集成权限控制

const { routeGuard } = require('../../utils/route-guard.js');
const { permissionManager } = require('../../utils/permission-manager.js');

/**
 * 作业列表页面 - 基础权限控制示例
 */
const homeworkListPage = {
  data: {
    homeworkList: [],
    userRole: '',
    canSubmit: false,
    canCorrect: false
  },

  async onLoad() {
    // 1. 基础路由守卫检查
    const authResult = await routeGuard.checkPageAuth();
    if (!authResult.success) {
      return; // 守卫已处理跳转
    }

    // 2. 页面级权限检查
    const canView = await permissionManager.hasPermission('homework.view');
    if (!canView) {
      wx.showToast({
        title: '无权限访问',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      return;
    }

    // 3. 功能级权限检查
    await this.checkFeaturePermissions();
    
    // 4. 加载页面数据
    await this.loadHomeworkList();
  },

  /**
   * 检查页面功能权限
   */
  async checkFeaturePermissions() {
    const canSubmit = await permissionManager.hasPermission('homework.submit');
    const canCorrect = await permissionManager.hasPermission('homework.correct');
    
    this.setData({
      canSubmit,
      canCorrect
    });
  },

  /**
   * 提交作业 - 需要权限控制
   */
  async submitHomework(homeworkId) {
    // 检查提交权限
    const canSubmit = await permissionManager.hasPermission('homework.submit');
    if (!canSubmit) {
      wx.showToast({
        title: '无权限提交作业',
        icon: 'none'
      });
      return;
    }

    // 检查时间限制
    const timeValid = permissionManager.checkTimeRestriction('06:00-23:00');
    if (!timeValid) {
      wx.showToast({
        title: '作业提交时间限制：06:00-23:00',
        icon: 'none'
      });
      return;
    }

    // 执行提交逻辑
    try {
      // ... 提交作业的具体逻辑
      wx.showToast({
        title: '提交成功',
        icon: 'success'
      });
    } catch (error) {
      console.error('提交作业失败:', error);
    }
  },

  /**
   * 批改作业 - 需要权限和角色检查
   */
  async correctHomework(homeworkId) {
    // 检查批改权限
    const canCorrect = await permissionManager.hasPermission('homework.correct');
    if (!canCorrect) {
      wx.showToast({
        title: '无权限批改作业',
        icon: 'none'
      });
      return;
    }

    // 动态权限检查 - 只能批改自己班级的作业
    const homeworkData = { classId: 'class123' }; // 从API获取
    const canCorrectThis = await permissionManager.checkDynamicPermission(
      'homework.correct', 
      homeworkData
    );
    
    if (!canCorrectThis) {
      wx.showToast({
        title: '只能批改本班作业',
        icon: 'none'
      });
      return;
    }

    // 执行批改逻辑
    wx.navigateTo({
      url: `/pages/homework/correct/index?id=${homeworkId}`
    });
  },

  async loadHomeworkList() {
    // 根据角色权限加载不同的作业数据
    // ...
  }
};

/**
 * 分析报告页面 - 动态权限控制示例
 */
const analysisReportPage = {
  data: {
    reportData: null,
    userRole: '',
    canViewDetail: false
  },

  async onLoad(options) {
    // 基础守卫检查
    const authResult = await routeGuard.checkPageAuth();
    if (!authResult.success) return;

    const studentId = options.studentId;
    const userRole = await authManager.getUserRole();

    // 动态权限检查
    if (userRole === 'parent') {
      // 家长只能查看自己孩子的报告
      const canViewChild = await permissionManager.checkDynamicPermission(
        'analysis.view_child',
        { studentId }
      );
      
      if (!canViewChild) {
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
    }

    await this.loadReportData(studentId);
  },

  async loadReportData(studentId) {
    // 加载报告数据
    // ...
  }
};

/**
 * 用户管理页面 - 高级权限控制示例
 */
const userManagePage = {
  data: {
    userList: [],
    canEdit: false,
    canDelete: false
  },

  async onLoad() {
    // 检查管理权限
    const canManage = await permissionManager.hasPermission('user.manage_students');
    if (!canManage) {
      wx.showModal({
        title: '权限不足',
        content: '您没有用户管理权限',
        showCancel: false,
        success: () => {
          wx.navigateBack();
        }
      });
      return;
    }

    await this.loadUserList();
  },

  /**
   * 删除用户 - 敏感操作
   */
  async deleteUser(userId) {
    // 敏感操作确认
    const confirmed = await permissionManager.confirmSensitiveOperation(
      'user.manage_students',
      '删除用户是敏感操作，确定要继续吗？'
    );
    
    if (!confirmed) {
      return;
    }

    try {
      // 执行删除逻辑
      await this.performDeleteUser(userId);
      wx.showToast({
        title: '删除成功',
        icon: 'success'
      });
      await this.loadUserList(); // 重新加载列表
    } catch (error) {
      console.error('删除用户失败:', error);
      wx.showToast({
        title: '删除失败',
        icon: 'none'
      });
    }
  },

  async loadUserList() {
    // 加载用户列表
    // ...
  },

  async performDeleteUser(userId) {
    // 实际删除逻辑
    // ...
  }
};

/**
 * 权限装饰器使用示例
 */
class TeacherService {
  /**
   * 创建作业 - 使用权限装饰器
   */
  @permissionManager.requirePermission('homework.create', {
    showError: true,
    errorMessage: '只有教师可以创建作业'
  })
  async createHomework(homeworkData) {
    // 创建作业逻辑
    console.log('创建作业:', homeworkData);
  }

  /**
   * 删除作业 - 敏感操作装饰器
   */
  @permissionManager.requirePermission('homework.delete', {
    requireConfirm: true
  })
  async deleteHomework(homeworkId) {
    // 删除作业逻辑
    console.log('删除作业:', homeworkId);
  }
}

/**
 * 页面守卫快捷使用示例
 */

// 方式1：使用创建器
const protectedPage = routeGuard.createPageGuard({
  requireRole: 'teacher',
  
  onLoad() {
    console.log('页面加载 - 已通过权限检查');
  }
});

// 方式2：使用装饰器
const decoratedPage = routeGuard.requireAuth('student')({
  onLoad() {
    console.log('学生页面加载');
  }
});

// 方式3：手动检查
const manualCheckPage = {
  async onLoad() {
    const authResult = await routeGuard.checkAuth({
      requireRole: 'parent'
    });
    
    if (!authResult.success) {
      return;
    }
    
    console.log('家长页面加载');
  }
};

module.exports = {
  homeworkListPage,
  analysisReportPage,
  userManagePage,
  TeacherService,
  protectedPage,
  decoratedPage,
  manualCheckPage
};