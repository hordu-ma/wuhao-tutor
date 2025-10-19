// TabBar 管理工具 - 简化版

const { authManager } = require('./auth.js');

/**
 * TabBar管理类 - 简化版
 * 策略：基础TabBar在app.json中静态配置，页面级做访问控制
 */
class TabBarManager {
  constructor() {
    this.isLoggedIn = false;
    this.isInitialized = false;
  }

  /**
   * 初始化TabBar管理器
   */
  async initTabBar() {
    console.log('🚀 初始化TabBar管理器');

    try {
      const isLoggedIn = await authManager.isLoggedIn();
      this.isLoggedIn = isLoggedIn;
      this.isInitialized = true;

      console.log(`📱 TabBar初始化完成 - 登录状态: ${isLoggedIn}`);

      // 现在所有5个TabBar项目都在app.json中配置，无需动态修改
      console.log('📱 TabBar配置已完成，所有功能模块已显示');

      return { success: true, isLoggedIn };
    } catch (error) {
      console.error('TabBar初始化失败:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 登录状态变化时的处理
   */
  async onLoginStatusChange(isLoggedIn) {
    console.log(`🔄 登录状态变化: ${this.isLoggedIn} -> ${isLoggedIn}`);

    this.isLoggedIn = isLoggedIn;

    if (isLoggedIn) {
      console.log('✅ 用户已登录，可以访问所有TabBar功能');
      // 显示成功提示
      wx.showToast({
        title: '登录成功！',
        icon: 'success',
        duration: 2000,
      });
    } else {
      console.log('ℹ️ 用户未登录，点击需要登录的TabBar项目时会提示');
    }

    return { success: true, isLoggedIn };
  }

  /**
   * 检查页面是否需要登录
   */
  async checkLoginRequired(pagePath) {
    const loginRequiredPages = [
      'pages/mistakes/list/index',
      'pages/learning/index/index',
      'pages/analysis/report/index',
    ];

    if (loginRequiredPages.includes(pagePath)) {
      const isLoggedIn = await authManager.isLoggedIn();
      if (!isLoggedIn) {
        wx.showModal({
          title: '需要登录',
          content: '此功能需要登录后使用，是否前往登录？',
          success(res) {
            if (res.confirm) {
              wx.navigateTo({
                url: '/pages/login/index',
              });
            }
          },
        });
        return false;
      }
    }
    return true;
  }

  /**
   * 获取当前TabBar配置信息
   */
  async getCurrentTabBarConfig() {
    const isLoggedIn = await authManager.isLoggedIn();
    return {
      isLoggedIn,
      message: isLoggedIn ? '已登录，可访问所有功能' : '未登录，部分功能受限',
    };
  }

  /**
   * 获取当前登录状态
   */
  getLoginStatus() {
    return this.isLoggedIn;
  }

  // 保留的兼容性方法
  async setTabBar() {
    return await this.initTabBar();
  }

  async filterTabBarByPermissions(tabBarList, isLoggedIn) {
    if (!isLoggedIn) {
      const allowedPages = ['pages/index/index', 'pages/profile/index/index'];
      return tabBarList.filter(item => allowedPages.includes(item.pagePath));
    }
    return tabBarList;
  }

  setTabBarBadge(index, text) {
    try {
      if (wx.setTabBarBadge && typeof index === 'number' && text) {
        wx.setTabBarBadge({
          index,
          text: String(text),
          success: () => console.log(`📱 TabBar徽章设置成功: ${index} - ${text}`),
          fail: error => console.error('TabBar徽章设置失败:', error),
        });
      }
    } catch (error) {
      console.error('setTabBarBadge调用失败:', error);
    }
  }

  removeTabBarBadge(index) {
    try {
      if (wx.removeTabBarBadge && typeof index === 'number') {
        wx.removeTabBarBadge({
          index,
          success: () => console.log(`📱 TabBar徽章移除成功: ${index}`),
          fail: error => console.error('TabBar徽章移除失败:', error),
        });
      }
    } catch (error) {
      console.error('removeTabBarBadge调用失败:', error);
    }
  }

  showTabBarRedDot(index) {
    try {
      if (wx.showTabBarRedDot && typeof index === 'number') {
        wx.showTabBarRedDot({
          index,
          success: () => console.log(`📱 TabBar红点显示成功: ${index}`),
          fail: error => console.error('TabBar红点显示失败:', error),
        });
      }
    } catch (error) {
      console.error('showTabBarRedDot调用失败:', error);
    }
  }

  hideTabBarRedDot(index) {
    try {
      if (wx.hideTabBarRedDot && typeof index === 'number') {
        wx.hideTabBarRedDot({
          index,
          success: () => console.log(`📱 TabBar红点隐藏成功: ${index}`),
          fail: error => console.error('TabBar红点隐藏失败:', error),
        });
      }
    } catch (error) {
      console.error('hideTabBarRedDot调用失败:', error);
    }
  }

  hideTabBar() {
    try {
      if (wx.hideTabBar) {
        wx.hideTabBar({
          animation: true,
          success: () => console.log('📱 TabBar隐藏成功'),
          fail: error => console.error('TabBar隐藏失败:', error),
        });
      }
    } catch (error) {
      console.error('hideTabBar调用失败:', error);
    }
  }

  showTabBar() {
    try {
      if (wx.showTabBar) {
        wx.showTabBar({
          animation: true,
          success: () => console.log('📱 TabBar显示成功'),
          fail: error => console.error('TabBar显示失败:', error),
        });
      }
    } catch (error) {
      console.error('showTabBar调用失败:', error);
    }
  }

  // 兼容性方法 - 保留原有接口但简化实现
  async onRoleSwitch(newRole, oldRole) {
    console.log(`角色切换: ${oldRole} -> ${newRole} (简化版本 - 仅学生角色)`);
    return { success: true };
  }

  getRoleTabBarConfig(role) {
    // 简化版本：只返回基础配置
    return {
      color: '#999999',
      selectedColor: '#1890ff',
      backgroundColor: '#ffffff',
      borderStyle: 'black',
      list: [],
    };
  }

  async resetTabBar() {
    return await this.initTabBar();
  }

  getCurrentTabBarState() {
    return {
      isLoggedIn: this.isLoggedIn,
      isInitialized: this.isInitialized,
    };
  }

  addCustomTabBarConfig(role, config) {
    console.log('addCustomTabBarConfig: 简化版本不支持自定义配置');
  }

  removeCustomTabBarConfig(role) {
    console.log('removeCustomTabBarConfig: 简化版本不支持自定义配置');
  }

  async updateTabBarBadges() {
    console.log('updateTabBarBadges: 简化版本暂不实现');
    return { success: true };
  }

  async checkNewHomework() {
    console.log('checkNewHomework: 简化版本暂不实现');
    return 0;
  }

  async getUnreadMessageCount() {
    console.log('getUnreadMessageCount: 简化版本暂不实现');
    return 0;
  }

  setTabBarStyle(style) {
    try {
      if (wx.setTabBarStyle) {
        wx.setTabBarStyle(style);
      }
    } catch (error) {
      console.error('setTabBarStyle调用失败:', error);
    }
  }

  setTabBarItem(index, item) {
    try {
      if (wx.setTabBarItem) {
        wx.setTabBarItem({
          index,
          ...item,
        });
      }
    } catch (error) {
      console.error('setTabBarItem调用失败:', error);
    }
  }

  async applyTabBarConfig(config) {
    console.log('applyTabBarConfig: 简化版本不支持动态配置');
    return { success: true };
  }
}

// 创建单例
const tabBarManager = new TabBarManager();

module.exports = {
  tabBarManager,
  TabBarManager,
};
