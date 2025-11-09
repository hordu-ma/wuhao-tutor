// pages/login/index.js - 五好伴学小程序登录页

const { authManager } = require('../../utils/auth.js');
const { networkMonitor } = require('../../utils/network-monitor.js');
const { errorToast } = require('../../utils/error-toast.js');
const { request } = require('../../utils/request.js');

Page({
  data: {
    loading: false,
    networkStatus: 'unknown',
    loginError: null,
    phone: '',
    password: '',
    showPassword: false,
    agreedToTerms: false, // 是否同意用户协议
  },

  onLoad() {
    console.log('登录页面加载');
    this.checkNetworkStatus();
    this.checkAutoLogin();
  },

  onShow() {
    // 清除错误状态
    this.setData({ loginError: null });
  },

  /**
   * 检查网络状态
   */
  checkNetworkStatus() {
    const status = networkMonitor.getCurrentStatus();
    this.setData({
      networkStatus: status.isConnected ? 'connected' : 'disconnected',
    });

    // 监听网络状态变化
    networkMonitor.addListener((currentStatus, previousStatus) => {
      this.setData({
        networkStatus: currentStatus.isConnected ? 'connected' : 'disconnected',
      });

      if (!previousStatus.isConnected && currentStatus.isConnected) {
        // 网络恢复时清除错误状态
        this.setData({ loginError: null });
      }
    });
  },

  /**
   * 检查自动登录
   */
  async checkAutoLogin() {
    try {
      const isLoggedIn = await authManager.isLoggedIn();
      if (isLoggedIn) {
        const isTokenValid = await authManager.isTokenValid();
        if (isTokenValid) {
          // 已登录且Token有效，直接跳转首页
          console.log('检测到有效登录状态，跳转首页');
          wx.switchTab({
            url: '/pages/index/index',
          });
          return;
        } else {
          // Token过期，尝试刷新
          try {
            await authManager.refreshToken();
            console.log('Token刷新成功，跳转首页');
            wx.switchTab({
              url: '/pages/index/index',
            });
            return;
          } catch (refreshError) {
            console.log('Token刷新失败，需要重新登录');
            await authManager.clearUserSession();
          }
        }
      }
    } catch (error) {
      console.error('自动登录检查失败:', error);
    }
  },

  /**
   * 手机号输入变化
   */
  onPhoneChange(e) {
    this.setData({
      phone: e.detail,
      loginError: null,
    });
  },

  /**
   * 密码输入变化
   */
  onPasswordChange(e) {
    this.setData({
      password: e.detail,
      loginError: null,
    });
  },

  /**
   * 切换密码显示/隐藏
   */
  togglePassword() {
    this.setData({
      showPassword: !this.data.showPassword,
    });
  },

  /**
   * 用户协议勾选状态变化
   */
  onAgreementChange(e) {
    this.setData({
      agreedToTerms: !this.data.agreedToTerms,
    });
  },

  /**
   * 显示用户协议
   */
  showUserAgreement(e) {
    e.stopPropagation();
    wx.showModal({
      title: '用户服务协议',
      content:
        '欢迎使用五好伴学！\n\n本协议是您与五好伴学之间关于使用五好伴学服务所订立的协议。请您仔细阅读本协议，特别是免除或限制责任的条款。\n\n1. 服务内容\n五好伴学为用户提供AI智能学习辅导、作业批改、错题管理等服务。\n\n2. 用户权利与义务\n- 用户有权使用本平台提供的各项服务\n- 用户应遵守法律法规，不得发布违法信息\n- 用户应妥善保管账号密码\n\n3. 隐私保护\n我们重视用户隐私，详见《隐私政策》。\n\n4. 服务变更\n我们保留随时修改或中断服务的权利。',
      showCancel: false,
      confirmText: '我知道了',
      confirmColor: '#1890ff',
    });
  },

  /**
   * 显示隐私政策
   */
  showPrivacyPolicy(e) {
    e.stopPropagation();
    wx.showModal({
      title: '隐私政策',
      content:
        '五好伴学隐私政策\n\n生效日期：2025年11月9日\n\n我们重视您的隐私保护，本政策说明我们如何收集、使用和保护您的个人信息。\n\n1. 信息收集\n- 账号信息：手机号、昵称、头像\n- 学习数据：作业、错题、学习时长\n- 设备信息：设备型号、操作系统版本\n\n2. 信息使用\n- 提供学习服务\n- 改进产品体验\n- 数据分析与统计\n\n3. 信息保护\n- 采用加密技术保护数据传输\n- 严格限制内部访问权限\n- 不会向第三方出售您的个人信息\n\n4. 您的权利\n- 查看、修改个人信息\n- 删除账号及相关数据\n- 撤回授权\n\n如有疑问，请联系客服。',
      showCancel: false,
      confirmText: '我知道了',
      confirmColor: '#1890ff',
    });
  },

  /**
   * 手机号密码登录
   */
  async onLogin() {
    if (this.data.loading) {
      return; // 防止重复点击
    }

    // 检查是否同意用户协议
    if (!this.data.agreedToTerms) {
      this.showError('请先阅读并同意《用户服务协议》及《隐私政策》');
      return;
    }

    // 检查网络状态
    if (this.data.networkStatus !== 'connected') {
      this.showError('网络连接不可用，请检查网络设置');
      return;
    }

    // 验证输入
    const { phone, password } = this.data;

    if (!phone) {
      this.showError('请输入手机号');
      return;
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      this.showError('请输入正确的手机号');
      return;
    }

    if (!password) {
      this.showError('请输入密码');
      return;
    }

    if (password.length < 6) {
      this.showError('密码长度不能少于6位');
      return;
    }

    try {
      this.setData({
        loading: true,
        loginError: null,
      });

      console.log('开始手机号密码登录流程');

      // 调用登录接口
      const response = await request.post('/auth/login', {
        phone: phone,
        password: password,
        device_type: 'mini_program',
        remember_me: false,
      });

      console.log('登录响应:', response);

      if (response && response.access_token) {
        // 保存 token 和用户信息
        await authManager.saveUserSession(
          response.access_token,
          response.refresh_token,
          response.user,
          response.user?.role || 'student',
          response.session_id,
        );

        // 🔧 [修复] 立即同步到 app.globalData
        const app = getApp();
        app.globalData.token = response.access_token;
        app.globalData.userInfo = response.user;

        console.log('登录成功并同步到 globalData:', {
          userId: response.user?.id,
          role: response.user?.role,
          hasToken: !!app.globalData.token,
        });

        // 显示登录成功提示
        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500,
        });

        // 延迟跳转
        setTimeout(() => {
          const role = response.user?.role;

          // 根据用户角色跳转到相应页面
          if (role === 'teacher') {
            wx.switchTab({
              url: '/pages/index/index',
            });
          } else if (role === 'parent') {
            wx.switchTab({
              url: '/pages/analysis/progress/index',
            });
          } else {
            // 默认学生角色
            wx.switchTab({
              url: '/pages/index/index',
            });
          }
        }, 1500);
      } else {
        this.showError('登录失败，请检查用户名和密码');
      }
    } catch (error) {
      console.error('登录过程异常:', error);

      let errorMessage = '登录失败，请重试';

      if (error.message) {
        if (error.message.includes('401') || error.message.includes('认证失败')) {
          errorMessage = '用户名或密码错误';
        } else if (error.message.includes('网络')) {
          errorMessage = '网络连接异常，请检查网络后重试';
        } else if (error.message.includes('timeout')) {
          errorMessage = '请求超时，请稍后重试';
        } else {
          errorMessage = error.message;
        }
      }

      this.showError(errorMessage);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 显示错误信息
   */
  showError(message) {
    this.setData({ loginError: message });
    wx.showToast({
      title: message,
      icon: 'none',
      duration: 3000,
    });
  },
});
