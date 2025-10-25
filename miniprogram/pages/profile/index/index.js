// pages/profile/index/index.js - 用户信息展示页面

const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { api, apiClient } = require('../../../utils/api.js');
const { errorToast } = require('../../../utils/error-toast.js');
const { avatarUploadManager } = require('../../../utils/avatar-upload.js');
const { syncManager } = require('../../../utils/sync-manager.js');

const pageObject = {
  data: {
    userInfo: null,
    userRole: '',
    loading: true,
    refreshing: false,

    // 显示控制
    showContactInfo: true,

    // 同步状态
    syncStatus: 'idle',
    lastSyncTime: 0,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('个人信息页面加载', options);

    // 移除手动的守卫检查,由 createGuardedPage 统一处理
    await this.initPage();
  },

  /**
   * 生命周期函数--监听页面显示
   */
  async onShow() {
    console.log('🔄 [onShow] 个人信息页面显示');
    console.log('🔄 [onShow] 当前loading状态:', this.data.loading);
    console.log('🔄 [onShow] 当前userInfo.avatarUrl:', this.data.userInfo?.avatarUrl);

    // 每次显示时刷新用户信息（可能在设置页面被修改）
    if (!this.data.loading) {
      console.log('🔄 [onShow] 开始执行refreshUserInfo');
      await this.refreshUserInfo();
      console.log('🔄 [onShow] refreshUserInfo完成, 最终avatarUrl:', this.data.userInfo?.avatarUrl);
    }
  },

  /**
   * 页面下拉刷新
   */
  async onPullDownRefresh() {
    console.log('下拉刷新用户信息');
    await this.refreshUserInfo();
    wx.stopPullDownRefresh();
  },

  /**
   * 初始化页面
   */
  async initPage() {
    try {
      this.setData({ loading: true });

      // 设置同步监听器
      this.setupSyncListener();

      // 加载本地数据
      await this.loadUserInfo();

      // 检查是否需要后台同步（不阻塞页面）
      if (authManager.needsUserInfoRefresh()) {
        this.triggerUserInfoSync();
      }
    } catch (error) {
      console.error('初始化页面失败:', error);
      errorToast.show('页面加载失败，请稍后重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 设置同步监听器
   */
  setupSyncListener() {
    this.syncListener = syncManager.addSyncListener(event => {
      if (event.type === 'statusChange') {
        this.setData({
          syncStatus: event.currentStatus,
          lastSyncTime: Date.now(),
        });

        // 同步成功后刷新用户信息
        if (event.currentStatus === 'success') {
          this.refreshUserInfoFromCache();
        }
      }
    });
  },

  /**
   * 从缓存刷新用户信息
   */
  async refreshUserInfoFromCache() {
    try {
      const [userInfo, userRole] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole(),
      ]);

      this.setData({
        userInfo,
        userRole,
        gradeDisplayText: this.getGradeDisplayName(userInfo?.grade_level),
      });
    } catch (error) {
      console.error('从缓存刷新用户信息失败:', error);
    }
  },

  /**
   * 触发用户信息同步
   */
  triggerUserInfoSync() {
    // 完全异步执行，不阻塞页面加载
    syncManager
      .manualSyncUserInfo()
      .then(() => {
        console.log('后台同步用户信息成功');
        // 同步成功后刷新显示
        this.refreshUserInfoFromCache();
      })
      .catch(error => {
        console.warn('后台同步用户信息失败（静默）:', error);
        // 完全静默失败，不影响用户体验
      });
  },

  /**
   * 加载用户信息
   */
  async loadUserInfo() {
    try {
      console.log('📚 [loadUserInfo] 开始加载用户信息...');

      // 从本地缓存获取基础信息
      const [userInfo, userRole] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole(),
      ]);

      console.log('📚 [loadUserInfo] 本地缓存userInfo:', userInfo);
      console.log('📚 [loadUserInfo] 本地缓存avatarUrl:', userInfo?.avatarUrl);

      this.setData({
        userInfo,
        userRole,
        gradeDisplayText: this.getGradeDisplayName(userInfo?.grade_level),
      });

      console.log('📚 [loadUserInfo] setData完成, 页面avatarUrl:', this.data.userInfo?.avatarUrl);

      // 异步获取最新的服务器信息
      this.fetchLatestUserInfo();
    } catch (error) {
      console.error('加载用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 从服务器获取最新用户信息
   */
  async fetchLatestUserInfo() {
    try {
      console.log('🌐 [服务器获取] 开始获取服务器用户信息...');
      const response = await apiClient.get('/auth/me');

      console.log('🌐 [服务器获取] API响应状态:', response.statusCode);
      console.log('🌐 [服务器获取] API响应数据:', response);
      console.log('🌐 [服务器获取] response.success:', response.success);
      console.log('🌐 [服务器获取] response.data存在:', !!response.data);
      console.log('🌐 [服务器获取] response.data内容:', response.data);

      if (response.success && response.data) {
        console.log('🌐 [服务器获取] 条件判断通过，开始处理数据...');
        const serverUserInfo = response.data;
        console.log('🌐 [服务器获取] 服务器用户信息:', serverUserInfo);

        // 合并本地和服务器信息
        const { avatar_url, ...otherServerData } = serverUserInfo;
        const mergedUserInfo = {
          ...this.data.userInfo,
          ...otherServerData,
          // 优先使用服务器的头像URL（头像在服务器端是权威的）
          avatarUrl: avatar_url || serverUserInfo.avatarUrl || this.data.userInfo?.avatarUrl,
        };

        console.log('🌐 [服务器获取] 服务器avatar_url:', avatar_url);
        console.log('🌐 [服务器获取] 合并后用户信息:', mergedUserInfo);
        console.log('🌐 [setData前] 当前userInfo:', this.data.userInfo);
        console.log('🌐 [setData前] 准备设置的avatarUrl:', mergedUserInfo.avatarUrl);

        this.setData({
          userInfo: mergedUserInfo,
          gradeDisplayText: this.getGradeDisplayName(mergedUserInfo?.grade_level),
        });

        console.log('🌐 [setData后] 页面userInfo:', this.data.userInfo);
        console.log('🌐 [setData后] 页面avatarUrl:', this.data.userInfo?.avatarUrl);

        // 更新本地缓存
        console.log('🌐 [缓存更新前] 准备保存到缓存的mergedUserInfo:', mergedUserInfo);
        console.log('🌐 [缓存更新前] 准备保存的avatarUrl:', mergedUserInfo.avatarUrl);

        await authManager.updateUserInfo(mergedUserInfo);

        // 验证缓存更新后的数据
        const verifyUserInfo = await authManager.getUserInfo();
        console.log('🌐 [缓存更新后] 从缓存读取的userInfo:', verifyUserInfo);
        console.log('🌐 [缓存更新后] 从缓存读取的avatarUrl:', verifyUserInfo?.avatarUrl);

        console.log('🌐 [服务器获取] 本地缓存已更新');
      } else {
        console.warn('🌐 [服务器获取] API响应格式异常:', response);
        console.warn('🌐 [服务器获取] response.success 值:', response.success);
        console.warn('🌐 [服务器获取] response.data 值:', response.data);
        console.warn('🌐 [服务器获取] response 完整结构:', JSON.stringify(response, null, 2));
      }
    } catch (error) {
      console.error('🌐 [服务器获取] 获取服务器用户信息失败:', error);
      console.error('🌐 [服务器获取] 错误详情:', {
        message: error.message,
        statusCode: error.statusCode,
        errMsg: error.errMsg,
        detail: error.detail,
      });
      // 静默失败，使用本地缓存的信息
    }
  },

  /**
   * 刷新用户信息
   */
  async refreshUserInfo() {
    try {
      this.setData({ refreshing: true });

      await this.fetchLatestUserInfo();

      console.log('用户信息刷新成功');
    } catch (error) {
      console.error('刷新用户信息失败:', error);
      errorToast.show('刷新失败，请稍后重试');
    } finally {
      this.setData({ refreshing: false });
    }
  },

  /**
   * 获取角色显示名称
   */
  getRoleDisplayName(role) {
    const roleMap = {
      student: '学生',
      parent: '家长',
      teacher: '教师',
      admin: '管理员',
    };
    return roleMap[role] || role;
  },

  /**
   * 获取年级显示名称
   */
  getGradeDisplayName(grade) {
    const gradeMap = {
      // 小学阶段
      primary_1: '小学一年级',
      primary_2: '小学二年级',
      primary_3: '小学三年级',
      primary_4: '小学四年级',
      primary_5: '小学五年级',
      primary_6: '小学六年级',
      // 初中阶段
      junior_1: '初中一年级',
      junior_2: '初中二年级',
      junior_3: '初中三年级',
      // 高中阶段
      senior_1: '高中一年级',
      senior_2: '高中二年级',
      senior_3: '高中三年级',
    };
    return gradeMap[grade] || grade;
  },

  /**
   * 点击头像 - 进入头像编辑
   */
  onAvatarTap() {
    console.log('点击头像');

    wx.showActionSheet({
      itemList: ['查看大图', '更换头像'],
      success: res => {
        if (res.tapIndex === 0) {
          this.previewAvatar();
        } else if (res.tapIndex === 1) {
          this.changeAvatar();
        }
      },
    });
  },

  /**
   * 预览头像大图
   */
  previewAvatar() {
    const avatarUrl = this.data.userInfo?.avatarUrl;
    avatarUploadManager.previewAvatar(avatarUrl);
  },

  /**
   * 更换头像
   */
  async changeAvatar() {
    try {
      const result = await avatarUploadManager.selectAndUploadAvatar();

      if (result && result.success) {
        // 更新页面显示的用户信息
        const updatedUserInfo = {
          ...this.data.userInfo,
          avatarUrl: result.avatarUrl,
        };

        this.setData({ userInfo: updatedUserInfo });
        console.log('头像更换成功:', result.avatarUrl);
      }
    } catch (error) {
      console.error('更换头像失败:', error);
      // 错误处理已在 avatarUploadManager 中完成
    }
  },

  /**
   * 编辑个人信息
   */
  onEditProfile() {
    console.log('编辑个人信息');

    wx.navigateTo({
      url: '/pages/profile/edit/index',
    });
  },

  /**
   * 进入设置页面
   */
  onSettingsTap() {
    console.log('进入设置');

    wx.navigateTo({
      url: '/pages/profile/settings/index',
    });
  },

  /**
   * 进入帮助中心
   */
  onHelpTap() {
    console.log('进入帮助中心');

    wx.navigateTo({
      url: '/pages/profile/help/index',
    });
  },

  /**
   * 头像加载成功
   */
  onAvatarLoad(e) {
    console.log('🖼️ [头像加载] 头像加载成功:', e.detail);
    console.log('🖼️ [头像加载] 当前avatarUrl:', this.data.userInfo?.avatarUrl);
  },

  /**
   * 头像加载失败
   */
  onAvatarError(e) {
    console.error('🖼️ [头像加载] 头像加载失败:', e.detail);
    console.error('🖼️ [头像加载] 当前avatarUrl:', this.data.userInfo?.avatarUrl);
    console.error('🖼️ [头像加载] 将使用默认头像');
  },

  /**
   * 页面分享
   */
  onShareAppMessage() {
    return {
      title: '五好伴学 - 我的个人信息',
      path: '/pages/profile/index/index',
      imageUrl: '/assets/images/share-profile.png',
    };
  },
};

// 使用守卫包装页面
Page(createGuardedPage(pageObject, 'pages/profile/index/index'));
