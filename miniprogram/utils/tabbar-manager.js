// tabBar 管理工具 - 角色专属tabBar配置

const { roleManager } = require('./role-manager.js');
const { authManager } = require('./auth.js');
const { permissionManager } = require('./permission-manager.js');

/**
 * TabBar管理类
 */
class TabBarManager {
  constructor() {
    // 角色专属tabBar配置
    this.roleTabBarConfigs = {
      student: {
        color: '#999999',
        selectedColor: '#1890ff',
        backgroundColor: '#ffffff',
        borderStyle: 'black',
        list: [
          {
            pagePath: 'pages/index/index',
            text: '首页',
            iconPath: '/assets/icons/home.png',
            selectedIconPath: '/assets/icons/home-active.png'
          },
          {
            pagePath: 'pages/homework/list/index',
            text: '作业',
            iconPath: '/assets/icons/homework.png',
            selectedIconPath: '/assets/icons/homework-active.png'
          },
          {
            pagePath: 'pages/chat/index/index',
            text: '问答',
            iconPath: '/assets/icons/chat.png',
            selectedIconPath: '/assets/icons/chat-active.png'
          },
          {
            pagePath: 'pages/analysis/report/index',
            text: '报告',
            iconPath: '/assets/icons/report.png',
            selectedIconPath: '/assets/icons/report-active.png'
          },
          {
            pagePath: 'pages/profile/index/index',
            text: '我的',
            iconPath: '/assets/icons/profile.png',
            selectedIconPath: '/assets/icons/profile-active.png'
          }
        ]
      },

      parent: {
        color: '#999999',
        selectedColor: '#52c41a',
        backgroundColor: '#ffffff',
        borderStyle: 'black',
        list: [
          {
            pagePath: 'pages/index/index',
            text: '首页',
            iconPath: '/assets/icons/home.png',
            selectedIconPath: '/assets/icons/home-active.png'
          },
          {
            pagePath: 'pages/analysis/progress/index',
            text: '学情',
            iconPath: '/assets/icons/progress.png',
            selectedIconPath: '/assets/icons/progress-active.png'
          },
          {
            pagePath: 'pages/homework/list/index',
            text: '作业',
            iconPath: '/assets/icons/homework.png',
            selectedIconPath: '/assets/icons/homework-active.png'
          },
          {
            pagePath: 'pages/profile/index/index',
            text: '我的',
            iconPath: '/assets/icons/profile.png',
            selectedIconPath: '/assets/icons/profile-active.png'
          }
        ]
      },

      teacher: {
        color: '#999999',
        selectedColor: '#faad14',
        backgroundColor: '#ffffff',
        borderStyle: 'black',
        list: [
          {
            pagePath: 'pages/index/index',
            text: '首页',
            iconPath: '/assets/icons/home.png',
            selectedIconPath: '/assets/icons/home-active.png'
          },
          {
            pagePath: 'pages/homework/list/index',
            text: '作业',
            iconPath: '/assets/icons/homework.png',
            selectedIconPath: '/assets/icons/homework-active.png'
          },
          {
            pagePath: 'pages/analysis/report/index',
            text: '分析',
            iconPath: '/assets/icons/analysis.png',
            selectedIconPath: '/assets/icons/analysis-active.png'
          },
          {
            pagePath: 'pages/profile/index/index',
            text: '我的',
            iconPath: '/assets/icons/profile.png',
            selectedIconPath: '/assets/icons/profile-active.png'
          }
        ]
      }
    };

    // 默认tabBar配置（未登录或未选择角色时使用）
    this.defaultTabBarConfig = {
      color: '#999999',
      selectedColor: '#1890ff',
      backgroundColor: '#ffffff',
      borderStyle: 'black',
      list: [
        {
          pagePath: 'pages/index/index',
          text: '首页',
          iconPath: '/assets/icons/home.png',
          selectedIconPath: '/assets/icons/home-active.png'
        },
        {
          pagePath: 'pages/profile/index/index',
          text: '我的',
          iconPath: '/assets/icons/profile.png',
          selectedIconPath: '/assets/icons/profile-active.png'
        }
      ]
    };

    // 当前应用的tabBar配置
    this.currentTabBarConfig = null;
    this.currentRole = null;
  }

  /**
   * 获取角色对应的tabBar配置
   */
  getRoleTabBarConfig(role) {
    return this.roleTabBarConfigs[role] || this.defaultTabBarConfig;
  }

  /**
   * 获取当前用户的tabBar配置
   */
  async getCurrentTabBarConfig() {
    try {
      const userRole = await authManager.getUserRole();
      return this.getRoleTabBarConfig(userRole);
    } catch (error) {
      console.error('获取当前tabBar配置失败:', error);
      return this.defaultTabBarConfig;
    }
  }

  /**
   * 设置tabBar配置
   */
  async setTabBar(role = null) {
    try {
      const targetRole = role || await authManager.getUserRole();
      const tabBarConfig = this.getRoleTabBarConfig(targetRole);

      // 检查是否需要更新
      if (this.currentRole === targetRole && this.currentTabBarConfig) {
        console.log('TabBar配置未变化，跳过更新');
        return { success: true, updated: false };
      }

      console.log(`设置${targetRole}角色的tabBar配置`);

      // 过滤有权限访问的页面
      const filteredList = await this.filterTabBarByPermissions(tabBarConfig.list, targetRole);

      if (filteredList.length === 0) {
        console.warn('没有可访问的tabBar页面');
        return { success: false, error: '没有可访问的页面' };
      }

      // 应用tabBar配置
      const finalConfig = {
        ...tabBarConfig,
        list: filteredList
      };

      // 由于小程序限制，无法动态修改app.json中的tabBar
      // 这里使用 wx.setTabBarStyle 和 wx.setTabBarItem 来更新
      await this.applyTabBarConfig(finalConfig);

      // 更新当前配置
      this.currentTabBarConfig = finalConfig;
      this.currentRole = targetRole;

      console.log('TabBar配置更新成功:', { role: targetRole, items: filteredList.length });

      return { success: true, updated: true, config: finalConfig };
    } catch (error) {
      console.error('设置tabBar失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 根据权限过滤tabBar项目
   */
  async filterTabBarByPermissions(tabBarList, role) {
    const filteredList = [];

    for (const item of tabBarList) {
      try {
        // 检查页面访问权限
        const canAccess = await permissionManager.checkPageAccess(item.pagePath);
        
        if (canAccess) {
          filteredList.push(item);
        } else {
          console.log(`用户${role}无权访问页面: ${item.pagePath}`);
        }
      } catch (error) {
        console.error(`检查页面权限失败: ${item.pagePath}`, error);
        // 权限检查失败时，默认不添加该项
      }
    }

    return filteredList;
  }

  /**
   * 应用tabBar配置到小程序
   */
  async applyTabBarConfig(config) {
    try {
      // 设置tabBar样式
      await this.setTabBarStyle({
        color: config.color,
        selectedColor: config.selectedColor,
        backgroundColor: config.backgroundColor,
        borderStyle: config.borderStyle
      });

      // 设置每个tabBar项目
      for (let index = 0; index < config.list.length; index++) {
        const item = config.list[index];
        await this.setTabBarItem(index, {
          text: item.text,
          iconPath: item.iconPath,
          selectedIconPath: item.selectedIconPath
        });
      }

      console.log('TabBar配置应用成功');
    } catch (error) {
      console.error('应用tabBar配置失败:', error);
      throw error;
    }
  }

  /**
   * 设置tabBar样式
   */
  setTabBarStyle(style) {
    return new Promise((resolve, reject) => {
      wx.setTabBarStyle({
        ...style,
        success: resolve,
        fail: reject
      });
    });
  }

  /**
   * 设置tabBar项目
   */
  setTabBarItem(index, item) {
    return new Promise((resolve, reject) => {
      wx.setTabBarItem({
        index,
        ...item,
        success: resolve,
        fail: reject
      });
    });
  }

  /**
   * 显示tabBar徽标
   */
  showTabBarRedDot(index) {
    wx.showTabBarRedDot({ index });
  }

  /**
   * 隐藏tabBar徽标
   */
  hideTabBarRedDot(index) {
    wx.hideTabBarRedDot({ index });
  }

  /**
   * 设置tabBar徽标文本
   */
  setTabBarBadge(index, text) {
    wx.setTabBarBadge({ index, text });
  }

  /**
   * 移除tabBar徽标文本
   */
  removeTabBarBadge(index) {
    wx.removeTabBarBadge({ index });
  }

  /**
   * 角色切换时更新tabBar
   */
  async onRoleSwitch(newRole, oldRole) {
    console.log(`角色切换: ${oldRole} -> ${newRole}`);

    try {
      // 更新tabBar配置
      const result = await this.setTabBar(newRole);
      
      if (result.success) {
        // 切换到角色对应的首页
        const roleConfig = roleManager.getRoleConfig(newRole);
        const homePage = roleConfig.homePage;

        // 如果首页在tabBar中，切换到该页面
        const homePageInTabBar = result.config.list.find(item => 
          item.pagePath === homePage.replace('/', '')
        );

        if (homePageInTabBar) {
          wx.switchTab({
            url: homePage,
            fail: (error) => {
              console.error('切换到首页失败:', error);
              // 如果切换失败，使用 redirectTo
              wx.redirectTo({
                url: homePage
              });
            }
          });
        } else {
          // 如果首页不在tabBar中，使用 redirectTo
          wx.redirectTo({
            url: homePage
          });
        }

        return result;
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('角色切换tabBar更新失败:', error);
      
      // 显示错误提示
      wx.showToast({
        title: 'TabBar更新失败',
        icon: 'none',
        duration: 2000
      });

      return { success: false, error: error.message };
    }
  }

  /**
   * 初始化tabBar
   */
  async initTabBar() {
    try {
      console.log('初始化tabBar配置');

      // 检查用户登录状态
      const isLoggedIn = await authManager.isLoggedIn();
      
      if (!isLoggedIn) {
        console.log('用户未登录，使用默认tabBar');
        await this.applyTabBarConfig(this.defaultTabBarConfig);
        return { success: true, role: 'guest' };
      }

      // 获取用户角色并设置对应tabBar
      const userRole = await authManager.getUserRole();
      const result = await this.setTabBar(userRole);

      return { ...result, role: userRole };
    } catch (error) {
      console.error('初始化tabBar失败:', error);
      
      // 降级到默认配置
      try {
        await this.applyTabBarConfig(this.defaultTabBarConfig);
        return { success: true, role: 'fallback', error: error.message };
      } catch (fallbackError) {
        console.error('应用默认tabBar失败:', fallbackError);
        return { success: false, error: fallbackError.message };
      }
    }
  }

  /**
   * 重置tabBar到默认状态
   */
  async resetTabBar() {
    try {
      console.log('重置tabBar到默认状态');
      await this.applyTabBarConfig(this.defaultTabBarConfig);
      
      this.currentTabBarConfig = this.defaultTabBarConfig;
      this.currentRole = null;

      return { success: true };
    } catch (error) {
      console.error('重置tabBar失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 获取当前tabBar状态
   */
  getCurrentTabBarState() {
    return {
      role: this.currentRole,
      config: this.currentTabBarConfig,
      initialized: !!this.currentTabBarConfig
    };
  }

  /**
   * 自定义tabBar配置
   */
  addCustomTabBarConfig(role, config) {
    this.roleTabBarConfigs[role] = config;
    console.log(`添加自定义tabBar配置: ${role}`);
  }

  /**
   * 移除自定义tabBar配置
   */
  removeCustomTabBarConfig(role) {
    if (this.roleTabBarConfigs[role]) {
      delete this.roleTabBarConfigs[role];
      console.log(`移除自定义tabBar配置: ${role}`);
    }
  }

  /**
   * 更新tabBar项目的徽标状态
   */
  async updateTabBarBadges() {
    try {
      const currentConfig = this.currentTabBarConfig;
      if (!currentConfig) return;

      // 这里可以根据业务需求更新徽标
      // 例如：未读消息数量、待处理作业数量等

      // 示例：检查作业页面是否有新作业
      const homeworkPageIndex = currentConfig.list.findIndex(item => 
        item.pagePath.includes('homework')
      );

      if (homeworkPageIndex !== -1) {
        // TODO: 检查是否有新作业
        const hasNewHomework = await this.checkNewHomework();
        
        if (hasNewHomework) {
          this.showTabBarRedDot(homeworkPageIndex);
        } else {
          this.hideTabBarRedDot(homeworkPageIndex);
        }
      }

      // 示例：检查个人中心是否有新消息
      const profilePageIndex = currentConfig.list.findIndex(item => 
        item.pagePath.includes('profile')
      );

      if (profilePageIndex !== -1) {
        // TODO: 检查是否有新消息
        const unreadCount = await this.getUnreadMessageCount();
        
        if (unreadCount > 0) {
          this.setTabBarBadge(profilePageIndex, unreadCount.toString());
        } else {
          this.removeTabBarBadge(profilePageIndex);
        }
      }

    } catch (error) {
      console.error('更新tabBar徽标失败:', error);
    }
  }

  /**
   * 检查新作业（示例方法）
   */
  async checkNewHomework() {
    // TODO: 实现检查新作业的逻辑
    return false;
  }

  /**
   * 获取未读消息数量（示例方法）
   */
  async getUnreadMessageCount() {
    // TODO: 实现获取未读消息数量的逻辑
    return 0;
  }
}

// 创建全局实例
const tabBarManager = new TabBarManager();

// 导出
module.exports = {
  TabBarManager,
  tabBarManager,
  
  // 便捷方法
  initTabBar: () => tabBarManager.initTabBar(),
  setTabBar: (role) => tabBarManager.setTabBar(role),
  resetTabBar: () => tabBarManager.resetTabBar(),
  onRoleSwitch: (newRole, oldRole) => tabBarManager.onRoleSwitch(newRole, oldRole),
  updateBadges: () => tabBarManager.updateTabBarBadges(),
  
  // 徽标方法
  showRedDot: (index) => tabBarManager.showTabBarRedDot(index),
  hideRedDot: (index) => tabBarManager.hideTabBarRedDot(index),
  setBadge: (index, text) => tabBarManager.setTabBarBadge(index, text),
  removeBadge: (index) => tabBarManager.removeTabBarBadge(index)
};