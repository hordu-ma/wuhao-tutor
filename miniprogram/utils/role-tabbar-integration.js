// 角色切换与TabBar集成工具
// 统一管理角色切换和TabBar更新

const { roleManager } = require('./role-manager.js');
const { tabBarManager } = require('./tabbar-manager.js');
const { authManager } = require('./auth.js');
const { errorToast } = require('./error-toast.js');

/**
 * 角色TabBar集成管理器
 */
class RoleTabBarIntegration {
  constructor() {
    this.isInitialized = false;
    this.currentRole = null;
    this.switchingRole = false;
  }

  /**
   * 初始化集成系统
   */
  async initialize() {
    try {
      if (this.isInitialized) {
        return { success: true, message: '已初始化' };
      }

      console.log('初始化角色TabBar集成系统');

      // 获取当前用户角色
      const isLoggedIn = await authManager.isLoggedIn();
      if (isLoggedIn) {
        this.currentRole = await authManager.getUserRole();
        console.log('当前用户角色:', this.currentRole);
      }

      // 初始化TabBar
      await tabBarManager.initTabBar();

      this.isInitialized = true;
      return { success: true, role: this.currentRole };
    } catch (error) {
      console.error('初始化角色TabBar集成失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 执行角色切换（包含TabBar更新）
   */
  async switchRoleWithTabBar(newRole, options = {}) {
    if (this.switchingRole) {
      console.log('角色切换正在进行中，请稍候');
      return { success: false, message: '角色切换正在进行中' };
    }

    try {
      this.switchingRole = true;
      
      const {
        showConfirmDialog = true,
        showSuccessToast = true,
        autoNavigate = true,
        updateTabBar = true
      } = options;

      console.log(`开始角色切换: ${this.currentRole} -> ${newRole}`);

      // 1. 验证新角色
      const roleConfig = roleManager.getRoleConfig(newRole);
      if (!roleConfig) {
        throw new Error(`无效的角色: ${newRole}`);
      }

      // 2. 检查是否需要切换
      if (this.currentRole === newRole) {
        if (showSuccessToast) {
          errorToast.success(`您当前已经是${roleConfig.name}角色`);
        }
        return { success: true, changed: false, role: newRole };
      }

      // 3. 显示确认对话框
      if (showConfirmDialog) {
        const currentRoleConfig = roleManager.getRoleConfig(this.currentRole);
        const confirmed = await errorToast.confirm(
          '角色切换确认',
          `确定要从"${currentRoleConfig?.name || '当前角色'}"切换到"${roleConfig.name}"吗？\n\n切换后您将看到不同的功能界面和菜单。`,
          {
            confirmText: '确认切换',
            cancelText: '取消'
          }
        );

        if (!confirmed) {
          return { success: false, cancelled: true };
        }
      }

      // 4. 执行后端角色切换
      await authManager.switchRole(newRole);

      // 5. 更新本地状态
      const oldRole = this.currentRole;
      this.currentRole = newRole;

      // 6. 更新TabBar
      if (updateTabBar) {
        const tabBarResult = await tabBarManager.onRoleSwitch(newRole, oldRole);
        if (!tabBarResult.success) {
          console.warn('TabBar更新失败，但角色切换成功:', tabBarResult.error);
        }
      }

      // 7. 更新全局应用状态
      const app = getApp();
      if (app && app.setUserInfo) {
        const userInfo = await authManager.getUserInfo();
        const token = await authManager.getToken();
        await app.setUserInfo(userInfo, token, newRole);
      }

      // 8. 显示成功提示
      if (showSuccessToast) {
        errorToast.success(`已切换为${roleConfig.name}角色`);
      }

      // 9. 自动导航到角色主页
      if (autoNavigate) {
        setTimeout(() => {
          this.navigateToRoleHome(newRole);
        }, 1500);
      }

      console.log('角色切换完成:', { from: oldRole, to: newRole });

      return {
        success: true,
        changed: true,
        fromRole: oldRole,
        toRole: newRole,
        roleConfig
      };

    } catch (error) {
      console.error('角色切换失败:', error);
      errorToast.show('角色切换失败: ' + error.message);
      return { success: false, error: error.message };
    } finally {
      this.switchingRole = false;
    }
  }

  /**
   * 导航到角色主页
   */
  navigateToRoleHome(role) {
    try {
      const roleConfig = roleManager.getRoleConfig(role);
      const homePage = roleConfig.homePage;

      // 检查主页是否在当前TabBar中
      const currentTabBarState = tabBarManager.getCurrentTabBarState();
      const isInTabBar = currentTabBarState.config?.list?.some(item =>
        homePage.includes(item.pagePath)
      );

      if (isInTabBar) {
        // 如果在TabBar中，使用switchTab
        wx.switchTab({
          url: homePage,
          success: () => {
            console.log('成功切换到角色主页:', homePage);
          },
          fail: (error) => {
            console.error('切换到TabBar页面失败:', error);
            // 降级到redirectTo
            wx.redirectTo({
              url: homePage
            });
          }
        });
      } else {
        // 如果不在TabBar中，使用redirectTo
        wx.redirectTo({
          url: homePage,
          success: () => {
            console.log('成功跳转到角色主页:', homePage);
          },
          fail: (error) => {
            console.error('跳转到角色主页失败:', error);
            // 最后降级到首页
            wx.switchTab({
              url: '/pages/index/index'
            });
          }
        });
      }
    } catch (error) {
      console.error('导航到角色主页失败:', error);
    }
  }

  /**
   * 获取当前角色状态
   */
  getCurrentRoleState() {
    return {
      currentRole: this.currentRole,
      isInitialized: this.isInitialized,
      switchingRole: this.switchingRole,
      tabBarState: tabBarManager.getCurrentTabBarState()
    };
  }

  /**
   * 刷新当前角色的TabBar
   */
  async refreshCurrentTabBar() {
    try {
      if (!this.currentRole) {
        console.log('当前无角色，无法刷新TabBar');
        return { success: false, message: '当前无角色' };
      }

      console.log('刷新当前角色TabBar:', this.currentRole);
      
      const result = await tabBarManager.setTabBar(this.currentRole);
      return result;
    } catch (error) {
      console.error('刷新TabBar失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 处理用户登出
   */
  async handleUserLogout() {
    try {
      console.log('处理用户登出，重置TabBar');
      
      this.currentRole = null;
      this.isInitialized = false;
      
      // 重置TabBar到默认状态
      await tabBarManager.resetTabBar();
      
      return { success: true };
    } catch (error) {
      console.error('处理登出失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 处理用户登录
   */
  async handleUserLogin(userRole) {
    try {
      console.log('处理用户登录，设置角色TabBar:', userRole);
      
      this.currentRole = userRole;
      
      // 设置角色对应的TabBar
      const result = await tabBarManager.setTabBar(userRole);
      
      if (result.success) {
        this.isInitialized = true;
      }
      
      return result;
    } catch (error) {
      console.error('处理登录失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 更新TabBar徽标
   */
  async updateTabBarBadges() {
    try {
      if (!this.currentRole) {
        return;
      }

      // 获取当前TabBar配置
      const tabBarState = tabBarManager.getCurrentTabBarState();
      if (!tabBarState.config) {
        return;
      }

      // 根据角色更新不同的徽标
      switch (this.currentRole) {
        case 'student':
          await this.updateStudentTabBarBadges(tabBarState.config);
          break;
        case 'parent':
          await this.updateParentTabBarBadges(tabBarState.config);
          break;
        case 'teacher':
          await this.updateTeacherTabBarBadges(tabBarState.config);
          break;
      }
    } catch (error) {
      console.error('更新TabBar徽标失败:', error);
    }
  }

  /**
   * 更新学生TabBar徽标
   */
  async updateStudentTabBarBadges(tabBarConfig) {
    // 检查作业页面
    const homeworkIndex = tabBarConfig.list.findIndex(item =>
      item.pagePath.includes('homework')
    );
    
    if (homeworkIndex !== -1) {
      // TODO: 检查是否有新作业或待提交作业
      const hasNewHomework = false; // 从API获取
      
      if (hasNewHomework) {
        tabBarManager.showRedDot(homeworkIndex);
      } else {
        tabBarManager.hideRedDot(homeworkIndex);
      }
    }

    // 检查问答页面
    const chatIndex = tabBarConfig.list.findIndex(item =>
      item.pagePath.includes('chat')
    );
    
    if (chatIndex !== -1) {
      // TODO: 检查是否有新的AI回复
      const hasNewReply = false; // 从API获取
      
      if (hasNewReply) {
        tabBarManager.showRedDot(chatIndex);
      } else {
        tabBarManager.hideRedDot(chatIndex);
      }
    }
  }

  /**
   * 更新家长TabBar徽标
   */
  async updateParentTabBarBadges(tabBarConfig) {
    // 检查学情页面
    const progressIndex = tabBarConfig.list.findIndex(item =>
      item.pagePath.includes('progress')
    );
    
    if (progressIndex !== -1) {
      // TODO: 检查是否有新的学习报告
      const hasNewReport = false; // 从API获取
      
      if (hasNewReport) {
        tabBarManager.showRedDot(progressIndex);
      } else {
        tabBarManager.hideRedDot(progressIndex);
      }
    }
  }

  /**
   * 更新教师TabBar徽标
   */
  async updateTeacherTabBarBadges(tabBarConfig) {
    // 检查作业页面
    const homeworkIndex = tabBarConfig.list.findIndex(item =>
      item.pagePath.includes('homework')
    );
    
    if (homeworkIndex !== -1) {
      // TODO: 检查待批改的作业数量
      const pendingCount = 0; // 从API获取
      
      if (pendingCount > 0) {
        tabBarManager.setBadge(homeworkIndex, pendingCount.toString());
      } else {
        tabBarManager.removeBadge(homeworkIndex);
      }
    }
  }
}

// 创建全局实例
const roleTabBarIntegration = new RoleTabBarIntegration();

// 导出
module.exports = {
  RoleTabBarIntegration,
  roleTabBarIntegration,
  
  // 便捷方法
  initialize: () => roleTabBarIntegration.initialize(),
  switchRole: (newRole, options) => roleTabBarIntegration.switchRoleWithTabBar(newRole, options),
  refreshTabBar: () => roleTabBarIntegration.refreshCurrentTabBar(),
  handleLogin: (userRole) => roleTabBarIntegration.handleUserLogin(userRole),
  handleLogout: () => roleTabBarIntegration.handleUserLogout(),
  updateBadges: () => roleTabBarIntegration.updateTabBarBadges(),
  getCurrentState: () => roleTabBarIntegration.getCurrentRoleState()
};