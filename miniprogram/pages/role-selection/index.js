// pages/role-selection/index.js - 角色选择页面

const { authManager } = require('../../utils/auth.js');
const { errorToast } = require('../../utils/error-toast.js');
const { roleManager } = require('../../utils/role-manager.js');
const { roleTabBarIntegration } = require('../../utils/role-tabbar-integration.js');

Page({
  data: {
    userInfo: null,
    currentRole: '',
    selectedRole: '',
    loading: false,
    roles: [] // 将由 roleManager 提供
  },

  async onLoad(options) {
    console.log('角色选择页面加载', options);
    
    // 检查登录状态
    const isLoggedIn = await authManager.isLoggedIn();
    if (!isLoggedIn) {
      wx.redirectTo({
        url: '/pages/login/index'
      });
      return;
    }

    await this.initPage();
  },

  /**
   * 初始化页面
   */
  async initPage() {
    try {
      // 获取用户信息和当前角色
      const [userInfo, currentRole] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole()
      ]);

      // 获取所有角色配置
      const roles = roleManager.getAllRoles();

      this.setData({
        userInfo,
        currentRole,
        selectedRole: currentRole || 'student',
        roles
      });

      console.log('角色选择页面初始化完成', { currentRole });
      
    } catch (error) {
      console.error('初始化页面失败:', error);
      errorToast.show('页面加载失败，请重试');
    }
  },

  /**
   * 选择角色
   */
  onRoleSelect(e) {
    const { role } = e.currentTarget.dataset;
    
    this.setData({
      selectedRole: role
    });

    // 添加触觉反馈
    wx.vibrateShort({
      type: 'light'
    });

    console.log('选择角色:', role);
  },

  /**
   * 确认角色选择
   */
  async onConfirmRole() {
    if (!this.data.selectedRole) {
      errorToast.show('请选择您的角色');
      return;
    }

    if (this.data.loading) {
      return;
    }

    try {
      this.setData({ loading: true });

      // 使用集成管理器执行角色切换（包含TabBar更新）
      const result = await roleTabBarIntegration.switchRole(this.data.selectedRole, {
        showConfirmDialog: this.data.currentRole && this.data.currentRole !== this.data.selectedRole,
        showSuccessToast: true,
        autoNavigate: true,
        updateTabBar: true
      });

      if (result.success && !result.cancelled) {
        console.log('角色设置成功:', result);
      } else if (result.cancelled) {
        console.log('用户取消角色切换');
      }

    } catch (error) {
      console.error('角色设置失败:', error);
      errorToast.show('角色设置失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 跳转到对应的首页
   */
  navigateToHomePage() {
    const { selectedRole } = this.data;
    
    // 根据角色跳转到不同页面
    let targetPage = '/pages/index/index';
    
    if (selectedRole === 'parent') {
      // 家长优先看学情分析
      targetPage = '/pages/analysis/progress/index';
    } else if (selectedRole === 'teacher') {
      // 教师优先看作业管理
      targetPage = '/pages/homework/list/index';
    }

    // 使用 reLaunch 清空页面栈，确保用户无法返回角色选择页
    wx.reLaunch({
      url: targetPage,
      fail: () => {
        // 如果目标页面不存在，回到首页
        wx.reLaunch({
          url: '/pages/index/index'
        });
      }
    });
  },

  /**
   * 获取角色显示名称
   */
  getRoleName(roleKey) {
    const role = this.data.roles.find(r => r.key === roleKey);
    return role ? role.name : roleKey;
  },

  /**
   * 跳过角色选择（使用默认角色）
   */
  async onSkipSelection() {
    try {
      this.setData({ loading: true });

      // 使用默认学生角色
      await authManager.switchRole('student');

      // 跳转到首页
      wx.reLaunch({
        url: '/pages/index/index'
      });

    } catch (error) {
      console.error('使用默认角色失败:', error);
      errorToast.show('操作失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 查看角色详情
   */
  onViewRoleDetails(e) {
    const { role } = e.currentTarget.dataset;
    const roleInfo = this.data.roles.find(r => r.key === role);
    
    if (roleInfo) {
      const features = roleInfo.features.join('\n• ');
      errorToast.confirm(
        `${roleInfo.name}角色说明`,
        `${roleInfo.description}\n\n主要功能：\n• ${features}`,
        {
          confirmText: '我知道了',
          showCancel: false
        }
      );
    }
  },

  /**
   * 页面分享
   */
  onShareAppMessage() {
    return {
      title: '五好伴学 - 选择您的角色',
      path: '/pages/role-selection/index',
      imageUrl: '/assets/images/share-logo.png'
    };
  }
});