// 修改密码页面逻辑
import Toast from '@vant/weapp/toast/toast';
const { request } = require('../../../utils/request.js');
const { authManager } = require('../../../utils/auth.js');

Page({
  data: {
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    isLoading: false,
    canSubmit: false,
  },

  /**
   * 旧密码变化
   */
  onOldPasswordChange(e) {
    this.setData({ oldPassword: e.detail }, () => {
      this.updateSubmitStatus();
    });
  },

  /**
   * 新密码变化
   */
  onNewPasswordChange(e) {
    this.setData({ newPassword: e.detail }, () => {
      this.updateSubmitStatus();
    });
  },

  /**
   * 确认密码变化
   */
  onConfirmPasswordChange(e) {
    this.setData({ confirmPassword: e.detail }, () => {
      this.updateSubmitStatus();
    });
  },

  /**
   * 更新提交按钮状态
   */
  updateSubmitStatus() {
    const { oldPassword, newPassword, confirmPassword } = this.data;
    const canSubmit =
      oldPassword.trim() !== '' && newPassword.trim() !== '' && confirmPassword.trim() !== '';
    this.setData({ canSubmit });
  },

  /**
   * 验证密码
   */
  validatePassword() {
    const { oldPassword, newPassword, confirmPassword } = this.data;

    // 检查是否为空
    if (!oldPassword || !newPassword || !confirmPassword) {
      Toast.fail('请填写完整信息');
      return false;
    }

    // 检查新密码长度
    if (newPassword.length < 6 || newPassword.length > 128) {
      Toast.fail('新密码长度需在6-128位之间');
      return false;
    }

    // 检查两次密码是否一致
    if (newPassword !== confirmPassword) {
      Toast.fail('两次输入的密码不一致');
      return false;
    }

    // 检查新旧密码是否相同
    if (oldPassword === newPassword) {
      Toast.fail('新密码不能与旧密码相同');
      return false;
    }

    return true;
  },

  /**
   * 提交修改
   */
  async handleSubmit() {
    // 验证
    if (!this.validatePassword()) {
      return;
    }

    const { oldPassword, newPassword, confirmPassword } = this.data;

    try {
      this.setData({ isLoading: true });

      // 在发送请求前，确保Token可用
      const token = await authManager.getToken();
      console.log('[ChangePassword] 准备修改密码', {
        hasToken: !!token,
        tokenLength: token ? token.length : 0,
      });

      if (!token) {
        Toast.fail('登录已过期，请重新登录');
        setTimeout(() => {
          this.clearAuthAndRedirect();
        }, 1500);
        return;
      }

      // 调用后端 API
      const response = await request.post('api/v1/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
        password_confirm: confirmPassword,
      });

      console.log('[ChangePassword] 修改密码响应:', response);

      // 修改成功
      Toast.success('密码修改成功');

      // 延迟后清除本地登录信息并跳转
      setTimeout(() => {
        this.clearAuthAndRedirect();
      }, 1500);
    } catch (error) {
      console.error('[ChangePassword] 修改密码失败:', error);

      // 显示错误信息
      let errorMsg = '密码修改失败，请重试';

      if (error.code === 'HTTP_401') {
        errorMsg = '登录已过期，请重新登录';
        // 401错误时清除认证信息
        setTimeout(() => {
          this.clearAuthAndRedirect();
        }, 1500);
      } else if (error.message) {
        errorMsg = error.message;
      }

      Toast.fail(errorMsg);

      this.setData({ isLoading: false });
    }
  },

  /**
   * 清除认证信息并跳转登录
   */
  async clearAuthAndRedirect() {
    try {
      // 使用 authManager 退出登录
      await authManager.logout();
    } catch (error) {
      console.error('退出登录失败:', error);
    }

    // 跳转到登录页
    wx.reLaunch({
      url: '/pages/login/index',
      success: () => {
        Toast.clear();
        wx.showToast({
          title: '请使用新密码登录',
          icon: 'none',
          duration: 2000,
        });
      },
    });
  },
});
