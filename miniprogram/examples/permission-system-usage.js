/**
 * TODO 2.4 权限控制系统使用示例
 * 展示如何在实际页面中使用各种权限控制功能
 */

const { enhancedPageGuard } = require('../utils/enhanced-page-guard.js');
const { featurePermissionGuard } = require('../utils/feature-permission-guard.js');
const { sensitiveOperationGuard } = require('../utils/sensitive-operation-guard.js');
const { friendlyPermissionDialog } = require('../utils/friendly-permission-dialog.js');

/**
 * 作业管理页面示例 - 完整的权限控制示例
 */
const homeworkManagePage = enhancedPageGuard.createGuardedPage({
  data: {
    homeworkList: [],
    selectedHomework: [],
    userPermissions: {},
    userRole: '',
    canPerformActions: {}
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('[作业管理页面] 页面加载，用户权限:', this.data.userPermissions);
    this.loadHomeworkList();
  },

  /**
   * 加载作业列表
   */
  async loadHomeworkList() {
    try {
      // 检查查看作业权限
      const canView = await featurePermissionGuard.checkFeaturePermission('homework.view');
      if (!canView.success) {
        featurePermissionGuard.handlePermissionFailure(canView, { feature: 'homework.view' });
        return;
      }

      // 模拟加载作业数据
      const homeworkList = [
        { id: 1, title: '数学作业1', status: 'pending', ownerId: 'teacher1' },
        { id: 2, title: '英语作业1', status: 'completed', ownerId: 'teacher1' },
        { id: 3, title: '语文作业1', status: 'pending', ownerId: 'teacher2' }
      ];

      this.setData({ homeworkList });
      
    } catch (error) {
      console.error('[作业管理] 加载作业列表失败:', error);
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '加载作业列表失败',
        retryCallback: () => this.loadHomeworkList()
      });
    }
  },

  /**
   * 创建作业
   */
  async onCreateHomework() {
    try {
      // 检查创建作业权限
      const canCreate = await featurePermissionGuard.checkFeaturePermission('homework.create');
      if (!canCreate.success) {
        featurePermissionGuard.handlePermissionFailure(canCreate, { feature: 'homework.create' });
        return;
      }

      // 跳转到创建页面
      wx.navigateTo({
        url: '/pages/homework/create/index'
      });

    } catch (error) {
      console.error('[作业管理] 创建作业失败:', error);
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '创建作业功能暂时不可用'
      });
    }
  },

  /**
   * 编辑作业
   */
  async onEditHomework(e) {
    const homeworkId = e.currentTarget.dataset.id;
    const homework = this.data.homeworkList.find(h => h.id == homeworkId);

    try {
      // 检查编辑权限
      const canEdit = await featurePermissionGuard.checkFeaturePermission('homework.manage', {
        homeworkId,
        resourceOwnerId: homework.ownerId
      });

      if (!canEdit.success) {
        featurePermissionGuard.handlePermissionFailure(canEdit, { 
          feature: 'homework.manage',
          resourceId: homeworkId 
        });
        return;
      }

      // 跳转到编辑页面
      wx.navigateTo({
        url: `/pages/homework/edit/index?id=${homeworkId}`
      });

    } catch (error) {
      console.error('[作业管理] 编辑作业失败:', error);
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '编辑作业功能暂时不可用'
      });
    }
  },

  /**
   * 删除作业 - 敏感操作示例
   */
  async onDeleteHomework(e) {
    const homeworkId = e.currentTarget.dataset.id;
    const homework = this.data.homeworkList.find(h => h.id == homeworkId);

    try {
      // 检查删除权限
      const canDelete = await featurePermissionGuard.checkFeaturePermission('homework.delete', {
        homeworkId,
        resourceOwnerId: homework.ownerId
      });

      if (!canDelete.success) {
        featurePermissionGuard.handlePermissionFailure(canDelete, { 
          feature: 'homework.delete',
          resourceId: homeworkId 
        });
        return;
      }

      // 敏感操作确认
      const confirmResult = await sensitiveOperationGuard.confirmSensitiveOperation(
        'homework.delete', 
        {
          homeworkId,
          homeworkTitle: homework.title,
          ownerId: homework.ownerId
        }
      );

      if (!confirmResult.success) {
        console.log('[作业管理] 用户取消删除操作');
        return;
      }

      // 执行删除
      await this.deleteHomework(homeworkId);
      
      wx.showToast({
        title: '删除成功',
        icon: 'success'
      });

      // 刷新列表
      this.loadHomeworkList();

    } catch (error) {
      console.error('[作业管理] 删除作业失败:', error);
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '删除作业失败，请稍后重试',
        retryCallback: () => this.onDeleteHomework(e)
      });
    }
  },

  /**
   * 批量删除作业 - 复杂敏感操作示例
   */
  async onBatchDeleteHomework() {
    if (this.data.selectedHomework.length === 0) {
      wx.showToast({
        title: '请选择要删除的作业',
        icon: 'none'
      });
      return;
    }

    try {
      // 检查批量删除权限
      const canBatchDelete = await featurePermissionGuard.checkFeaturePermission('homework.batch_delete');
      if (!canBatchDelete.success) {
        featurePermissionGuard.handlePermissionFailure(canBatchDelete, { 
          feature: 'homework.batch_delete' 
        });
        return;
      }

      // 敏感操作确认（需要密码和理由）
      const confirmResult = await sensitiveOperationGuard.confirmSensitiveOperation(
        'homework.batch_delete',
        {
          count: this.data.selectedHomework.length,
          homeworkIds: this.data.selectedHomework
        }
      );

      if (!confirmResult.success) {
        console.log('[作业管理] 用户取消批量删除操作');
        return;
      }

      // 执行批量删除
      await this.batchDeleteHomework(this.data.selectedHomework);
      
      wx.showToast({
        title: `已删除${this.data.selectedHomework.length}个作业`,
        icon: 'success'
      });

      // 清空选择并刷新列表
      this.setData({ selectedHomework: [] });
      this.loadHomeworkList();

    } catch (error) {
      console.error('[作业管理] 批量删除失败:', error);
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '批量删除失败，请稍后重试'
      });
    }
  },

  /**
   * 导出作业数据 - 敏感数据操作示例
   */
  async onExportHomeworkData() {
    try {
      // 检查导出权限
      const canExport = await featurePermissionGuard.checkFeaturePermission('analysis.export');
      if (!canExport.success) {
        featurePermissionGuard.handlePermissionFailure(canExport, { feature: 'analysis.export' });
        return;
      }

      // 敏感操作确认
      const confirmResult = await sensitiveOperationGuard.confirmSensitiveOperation(
        'data.export_all',
        {
          dataType: 'homework',
          dataCount: this.data.homeworkList.length
        }
      );

      if (!confirmResult.success) {
        return;
      }

      // 执行导出
      await this.exportHomeworkData();
      
      wx.showToast({
        title: '导出成功',
        icon: 'success'
      });

    } catch (error) {
      console.error('[作业管理] 导出数据失败:', error);
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '导出功能暂时不可用'
      });
    }
  },

  /**
   * 选择作业
   */
  onSelectHomework(e) {
    const homeworkId = e.currentTarget.dataset.id;
    const selected = this.data.selectedHomework.includes(homeworkId);
    
    let selectedHomework;
    if (selected) {
      selectedHomework = this.data.selectedHomework.filter(id => id !== homeworkId);
    } else {
      selectedHomework = [...this.data.selectedHomework, homeworkId];
    }

    this.setData({ selectedHomework });
  },

  /**
   * 检查用户角色切换
   */
  onRoleSwitchCheck() {
    // 每次页面显示时检查角色是否变更
    const currentRole = wx.getStorageSync('userRole');
    if (currentRole !== this.data.userRole) {
      console.log('[作业管理] 检测到角色变更，重新加载页面权限');
      // 重新加载页面以获取新的权限
      wx.reLaunch({
        url: '/pages/homework/manage/index'
      });
    }
  },

  // 模拟API调用方法
  async deleteHomework(homeworkId) {
    // 模拟删除API调用
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`删除作业 ${homeworkId} 成功`);
        resolve();
      }, 1000);
    });
  },

  async batchDeleteHomework(homeworkIds) {
    // 模拟批量删除API调用
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`批量删除作业成功:`, homeworkIds);
        resolve();
      }, 2000);
    });
  },

  async exportHomeworkData() {
    // 模拟导出API调用
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log('导出作业数据成功');
        resolve();
      }, 3000);
    });
  }

}, 'pages/homework/manage/index');

/**
 * 学生作业提交页面示例 - 功能级权限控制
 */
const studentHomeworkPage = enhancedPageGuard.createGuardedPage({
  data: {
    homework: null,
    submissionContent: '',
    attachments: []
  },

  onLoad(options) {
    const homeworkId = options.id;
    this.loadHomework(homeworkId);
  },

  /**
   * 加载作业详情
   */
  async loadHomework(homeworkId) {
    try {
      // 检查查看权限
      const canView = await featurePermissionGuard.checkFeaturePermission('homework.view', {
        homeworkId
      });

      if (!canView.success) {
        featurePermissionGuard.handlePermissionFailure(canView, { feature: 'homework.view' });
        return;
      }

      // 模拟加载作业数据
      const homework = {
        id: homeworkId,
        title: '数学作业1',
        description: '完成第三章练习题',
        deadline: '2024-12-31 23:59:59',
        status: 'pending'
      };

      this.setData({ homework });

    } catch (error) {
      friendlyPermissionDialog.showPermissionError('network_error', {
        retryCallback: () => this.loadHomework(homeworkId)
      });
    }
  },

  /**
   * 提交作业 - 时间和条件限制示例
   */
  async onSubmitHomework() {
    try {
      // 检查提交权限（包含时间限制等条件）
      const canSubmit = await featurePermissionGuard.checkFeaturePermission('homework.submit', {
        homeworkId: this.data.homework.id,
        content: this.data.submissionContent
      });

      if (!canSubmit.success) {
        featurePermissionGuard.handlePermissionFailure(canSubmit, { feature: 'homework.submit' });
        return;
      }

      // 最终提交确认
      const confirmResult = await sensitiveOperationGuard.confirmSensitiveOperation(
        'homework.submit_final',
        {
          homeworkId: this.data.homework.id,
          content: this.data.submissionContent
        }
      );

      if (!confirmResult.success) {
        return;
      }

      // 执行提交
      await this.submitHomework();
      
      wx.showModal({
        title: '提交成功',
        content: '作业已成功提交，请等待教师批改',
        showCancel: false,
        confirmText: '确定',
        success: () => {
          wx.navigateBack();
        }
      });

    } catch (error) {
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '提交失败，请稍后重试',
        retryCallback: () => this.onSubmitHomework()
      });
    }
  },

  /**
   * 上传附件
   */
  async onUploadAttachment() {
    try {
      wx.chooseMedia({
        count: 1,
        mediaType: ['image', 'video'],
        success: async (res) => {
          const file = res.tempFiles[0];
          
          // 检查文件上传权限
          const canUpload = await featurePermissionGuard.checkFeaturePermission('profile.avatar_upload', {
            fileSize: file.size,
            fileType: file.tempFilePath.split('.').pop().toLowerCase()
          });

          if (!canUpload.success) {
            featurePermissionGuard.handlePermissionFailure(canUpload, { feature: 'file.upload' });
            return;
          }

          // 执行上传
          this.uploadFile(file);
        }
      });

    } catch (error) {
      friendlyPermissionDialog.showPermissionError('server_error', {
        message: '文件选择失败'
      });
    }
  },

  // 模拟API方法
  async submitHomework() {
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log('作业提交成功');
        resolve();
      }, 2000);
    });
  },

  async uploadFile(file) {
    console.log('开始上传文件:', file);
    // 模拟文件上传
  }

}, 'pages/homework/submit/index');

/**
 * 权限测试页面示例 - 展示所有权限控制功能
 */
const permissionTestPage = {
  data: {
    testResults: []
  },

  onLoad() {
    this.runPermissionTests();
  },

  /**
   * 运行权限测试
   */
  async runPermissionTests() {
    const tests = [
      // 页面级权限测试
      {
        name: '页面访问权限测试',
        test: async () => {
          return await enhancedPageGuard.checkFeaturePermission('view_analysis');
        }
      },

      // 功能级权限测试
      {
        name: '作业提交权限测试',
        test: async () => {
          return await featurePermissionGuard.checkFeaturePermission('homework.submit');
        }
      },

      // 敏感操作测试
      {
        name: '敏感操作确认测试',
        test: async () => {
          return await sensitiveOperationGuard.confirmSensitiveOperation('homework.delete', {
            homeworkId: 'test_123'
          });
        }
      },

      // 角色权限测试
      {
        name: '角色权限测试',
        test: async () => {
          return await featurePermissionGuard.checkFeaturePermission('students.manage');
        }
      }
    ];

    const results = [];
    for (const test of tests) {
      try {
        const result = await test.test();
        results.push({
          name: test.name,
          success: result.success,
          message: result.message || result.reason
        });
      } catch (error) {
        results.push({
          name: test.name,
          success: false,
          message: error.message
        });
      }
    }

    this.setData({ testResults: results });
  },

  /**
   * 测试友好提示系统
   */
  onTestFriendlyDialog() {
    const errorTypes = [
      'not_logged_in',
      'role_not_allowed', 
      'permission_denied',
      'time_restriction',
      'daily_limit',
      'network_error'
    ];

    const randomError = errorTypes[Math.floor(Math.random() * errorTypes.length)];
    
    friendlyPermissionDialog.showPermissionError(randomError, {
      message: `这是${randomError}类型的测试错误提示`,
      userRole: 'student',
      requiredRoles: ['teacher']
    });
  }
};

module.exports = {
  homeworkManagePage,
  studentHomeworkPage,
  permissionTestPage
};