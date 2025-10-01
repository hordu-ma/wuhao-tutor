// utils/role-manager.js
// 角色管理工具

const { authManager } = require('./auth.js');
const { errorToast } = require('./error-toast.js');

/**
 * 角色管理类
 */
class RoleManager {
  constructor() {
    // 角色配置
    this.roleConfig = {
      student: {
        key: 'student',
        name: '学生',
        description: '完成作业，学习知识，与AI助手互动',
        icon: 'graduation',
        color: '#1890ff',
        bgColor: '#e6f7ff',
        homePage: '/pages/index/index',
        permissions: [
          'homework.view',
          'homework.submit',
          'chat.ask',
          'analysis.view_self',
          'profile.view_self'
        ],
        features: [
          '智能作业辅导',
          'AI问答互动', 
          '学习报告查看',
          '知识点掌握分析'
        ],
        tabBar: [
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
        key: 'parent',
        name: '家长',
        description: '监督孩子学习，查看学情报告',
        icon: 'friends-o',
        color: '#52c41a',
        bgColor: '#f6ffed',
        homePage: '/pages/analysis/progress/index',
        permissions: [
          'homework.view_child',
          'analysis.view_child',
          'profile.view_family',
          'chat.monitor'
        ],
        features: [
          '孩子学情监控',
          '学习进度跟踪',
          '成绩分析报告',
          '学习建议获取'
        ],
        tabBar: [
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
        key: 'teacher',
        name: '教师',
        description: '管理学生作业，分析班级学情',
        icon: 'manager-o',
        color: '#faad14',
        bgColor: '#fffbe6',
        homePage: '/pages/homework/list/index',
        permissions: [
          'homework.manage',
          'homework.correct',
          'analysis.view_class',
          'students.manage',
          'chat.moderate'
        ],
        features: [
          '作业批改管理',
          '班级分析统计',
          '学生管理系统',
          '教学效果分析'
        ],
        tabBar: [
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
  }

  /**
   * 获取角色配置
   */
  getRoleConfig(roleKey) {
    return this.roleConfig[roleKey] || this.roleConfig.student;
  }

  /**
   * 获取所有角色
   */
  getAllRoles() {
    return Object.values(this.roleConfig);
  }

  /**
   * 获取当前角色配置
   */
  async getCurrentRoleConfig() {
    try {
      const currentRole = await authManager.getUserRole();
      return this.getRoleConfig(currentRole);
    } catch (error) {
      console.error('获取当前角色配置失败:', error);
      return this.roleConfig.student;
    }
  }

  /**
   * 切换角色
   */
  async switchRole(newRoleKey, options = {}) {
    try {
      const { 
        showConfirmDialog = true,
        showSuccessToast = true,
        autoNavigate = true
      } = options;

      // 验证角色
      if (!this.roleConfig[newRoleKey]) {
        throw new Error(`不支持的角色: ${newRoleKey}`);
      }

      const currentRole = await authManager.getUserRole();
      const newRole = this.getRoleConfig(newRoleKey);
      
      // 如果角色相同，直接返回
      if (currentRole === newRoleKey) {
        if (showSuccessToast) {
          errorToast.success('您当前已经是' + newRole.name);
        }
        return { success: true, changed: false };
      }

      // 显示确认对话框
      if (showConfirmDialog) {
        const currentRoleConfig = this.getRoleConfig(currentRole);
        const confirmed = await errorToast.confirm(
          '角色切换确认',
          `确定要从"${currentRoleConfig.name}"切换到"${newRole.name}"吗？\n\n切换后您将看到不同的功能界面。`,
          {
            confirmText: '确认切换',
            cancelText: '取消'
          }
        );

        if (!confirmed) {
          return { success: false, cancelled: true };
        }
      }

      // 执行角色切换
      await authManager.switchRole(newRoleKey);

      // 更新全局状态
      const app = getApp();
      if (app.setUserInfo) {
        const userInfo = await authManager.getUserInfo();
        const token = await authManager.getToken();
        await app.setUserInfo(userInfo, token, newRoleKey);
      }

      // 显示成功提示
      if (showSuccessToast) {
        errorToast.success(`已切换为${newRole.name}角色`);
      }

      // 自动导航到角色主页
      if (autoNavigate) {
        setTimeout(() => {
          wx.reLaunch({
            url: newRole.homePage,
            fail: () => {
              wx.reLaunch({
                url: '/pages/index/index'
              });
            }
          });
        }, 1500);
      }

      return { 
        success: true, 
        changed: true,
        fromRole: currentRole,
        toRole: newRoleKey
      };

    } catch (error) {
      console.error('角色切换失败:', error);
      errorToast.show('角色切换失败: ' + error.message);
      return { success: false, error };
    }
  }

  /**
   * 检查角色权限
   */
  async checkPermission(permission, role = null) {
    try {
      const targetRole = role || await authManager.getUserRole();
      const roleConfig = this.getRoleConfig(targetRole);
      
      return roleConfig.permissions.includes(permission);
    } catch (error) {
      console.error('检查角色权限失败:', error);
      return false;
    }
  }

  /**
   * 获取角色的TabBar配置
   */
  async getRoleTabBar(role = null) {
    try {
      const targetRole = role || await authManager.getUserRole();
      const roleConfig = this.getRoleConfig(targetRole);
      
      return roleConfig.tabBar;
    } catch (error) {
      console.error('获取角色TabBar失败:', error);
      return this.roleConfig.student.tabBar;
    }
  }

  /**
   * 检查是否可以访问页面
   */
  async canAccessPage(pagePath, role = null) {
    try {
      const targetRole = role || await authManager.getUserRole();
      const tabBar = await this.getRoleTabBar(targetRole);
      
      // 检查是否在TabBar中
      const isInTabBar = tabBar.some(item => 
        pagePath.includes(item.pagePath.replace('pages/', ''))
      );

      if (isInTabBar) {
        return true;
      }

      // 根据角色检查特定页面权限
      const roleConfig = this.getRoleConfig(targetRole);
      
      // 这里可以添加更复杂的页面权限逻辑
      if (pagePath.includes('homework/submit') && targetRole !== 'student') {
        return false;
      }

      if (pagePath.includes('analysis/progress') && targetRole === 'student') {
        return false;
      }

      return true;
    } catch (error) {
      console.error('检查页面访问权限失败:', error);
      return true; // 默认允许访问
    }
  }

  /**
   * 获取角色显示名称
   */
  getRoleName(roleKey) {
    const role = this.getRoleConfig(roleKey);
    return role.name;
  }

  /**
   * 获取角色图标
   */
  getRoleIcon(roleKey) {
    const role = this.getRoleConfig(roleKey);
    return role.icon;
  }

  /**
   * 获取角色颜色
   */
  getRoleColor(roleKey) {
    const role = this.getRoleConfig(roleKey);
    return role.color;
  }

  /**
   * 为用户推荐合适的角色
   */
  async recommendRole(userInfo) {
    try {
      // 这里可以根据用户信息推荐角色
      // 比如根据年龄、职业等信息
      
      if (userInfo.profile?.age && userInfo.profile.age < 18) {
        return 'student';
      }
      
      if (userInfo.profile?.occupation === 'teacher') {
        return 'teacher';
      }
      
      // 默认推荐学生角色
      return 'student';
    } catch (error) {
      console.error('推荐角色失败:', error);
      return 'student';
    }
  }
}

// 创建单例实例
const roleManager = new RoleManager();

// 导出
module.exports = {
  RoleManager,
  roleManager,
  
  // 便捷方法
  getRoleConfig: (roleKey) => roleManager.getRoleConfig(roleKey),
  getAllRoles: () => roleManager.getAllRoles(),
  getCurrentRoleConfig: () => roleManager.getCurrentRoleConfig(),
  switchRole: (roleKey, options) => roleManager.switchRole(roleKey, options),
  checkPermission: (permission, role) => roleManager.checkPermission(permission, role),
  getRoleTabBar: (role) => roleManager.getRoleTabBar(role),
  canAccessPage: (pagePath, role) => roleManager.canAccessPage(pagePath, role),
  getRoleName: (roleKey) => roleManager.getRoleName(roleKey),
  getRoleIcon: (roleKey) => roleManager.getRoleIcon(roleKey),
  getRoleColor: (roleKey) => roleManager.getRoleColor(roleKey),
  recommendRole: (userInfo) => roleManager.recommendRole(userInfo)
};