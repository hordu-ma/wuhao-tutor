/**
 * 敏感操作确认模态框组件
 */

const { authManager } = require('../../utils/auth.js');

Component({
  /**
   * 组件的属性列表
   */
  properties: {
    show: {
      type: Boolean,
      value: false
    },
    config: {
      type: Object,
      value: {}
    }
  },

  /**
   * 组件的初始数据
   */
  data: {
    confirmPassword: '',
    confirmReason: '',
    passwordError: '',
    reasonError: '',
    canConfirm: false
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 密码输入处理
     */
    onPasswordInput(e) {
      const password = e.detail.value;
      this.setData({
        confirmPassword: password,
        passwordError: ''
      });
      this.validateInput();
    },

    /**
     * 理由输入处理
     */
    onReasonInput(e) {
      const reason = e.detail.value;
      this.setData({
        confirmReason: reason,
        reasonError: ''
      });
      this.validateInput();
    },

    /**
     * 验证输入
     */
    validateInput() {
      const { sensitiveConfirmModal } = this.data;
      let canConfirm = true;
      let passwordError = '';
      let reasonError = '';

      // 验证密码
      if (sensitiveConfirmModal.requirePassword) {
        if (!this.data.confirmPassword.trim()) {
          canConfirm = false;
          passwordError = '请输入密码';
        } else if (this.data.confirmPassword.length < 6) {
          canConfirm = false;
          passwordError = '密码长度至少6位';
        }
      }

      // 验证理由
      if (sensitiveConfirmModal.requireReason) {
        if (!this.data.confirmReason.trim()) {
          canConfirm = false;
          reasonError = '请输入操作理由';
        } else if (this.data.confirmReason.trim().length < 5) {
          canConfirm = false;
          reasonError = '理由至少5个字符';
        }
      }

      this.setData({
        canConfirm,
        passwordError,
        reasonError
      });
    },

    /**
     * 确认操作
     */
    async onConfirm() {
      if (!this.data.canConfirm) {
        return;
      }

      const { sensitiveConfirmModal } = this.data;
      
      // 如果需要密码验证
      if (sensitiveConfirmModal.requirePassword) {
        const passwordValid = await this.verifyPassword();
        if (!passwordValid) {
          return;
        }
      }

      // 准备额外数据
      const extraData = {};
      if (sensitiveConfirmModal.requirePassword) {
        extraData.password = this.data.confirmPassword;
      }
      if (sensitiveConfirmModal.requireReason) {
        extraData.reason = this.data.confirmReason.trim();
      }

      // 通知父组件确认
      this.triggerEvent('confirm', {
        confirmed: true,
        extraData
      });

      // 清理数据
      this.clearData();
    },

    /**
     * 取消操作
     */
    onCancel() {
      this.triggerEvent('confirm', {
        confirmed: false,
        extraData: null
      });
      this.clearData();
    },

    /**
     * 关闭模态框
     */
    onModalClose() {
      this.onCancel();
    },

    /**
     * 验证密码
     */
    async verifyPassword() {
      try {
        const currentUser = authManager.getCurrentUser();
        if (!currentUser) {
          this.setData({
            passwordError: '用户未登录'
          });
          return false;
        }

        // 这里应该调用后端验证密码
        // 暂时使用简单验证
        const password = this.data.confirmPassword;
        if (password === '123456') { // 临时验证逻辑
          return true;
        }

        // 模拟密码验证API调用
        const verified = await this.callPasswordVerifyAPI(password);
        if (!verified) {
          this.setData({
            passwordError: '密码错误'
          });
          return false;
        }

        return true;

      } catch (error) {
        console.error('[SensitiveConfirmModal] 密码验证失败:', error);
        this.setData({
          passwordError: '密码验证失败，请重试'
        });
        return false;
      }
    },

    /**
     * 调用密码验证API
     */
    async callPasswordVerifyAPI(password) {
      try {
        // 这里应该调用真实的密码验证API
        // 目前返回模拟结果
        return new Promise((resolve) => {
          setTimeout(() => {
            // 模拟验证逻辑
            resolve(password.length >= 6);
          }, 500);
        });

      } catch (error) {
        console.error('[SensitiveConfirmModal] API调用失败:', error);
        return false;
      }
    },

    /**
     * 清理数据
     */
    clearData() {
      this.setData({
        confirmPassword: '',
        confirmReason: '',
        passwordError: '',
        reasonError: '',
        canConfirm: false
      });
    }
  },

  /**
   * 组件生命周期
   */
  lifetimes: {
    attached() {
      console.log('[SensitiveConfirmModal] 组件已加载');
    },

    detached() {
      console.log('[SensitiveConfirmModal] 组件已卸载');
      this.clearData();
    }
  },

  /**
   * 组件所在页面的生命周期
   */
  pageLifetimes: {
    show() {
      // 页面显示时重置状态
      if (this.data.show) {
        this.clearData();
      }
    },

    hide() {
      // 页面隐藏时清理状态
      this.clearData();
    }
  },

  /**
   * 监听属性变化
   */
  observers: {
    'show': function(show) {
      if (!show) {
        this.clearData();
      }
    },

    'config': function(config) {
      if (config) {
        this.setData({
          sensitiveConfirmModal: config
        });
        this.validateInput();
      }
    }
  }
});