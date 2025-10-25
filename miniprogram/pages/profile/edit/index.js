// pages/profile/edit/index.js - 用户信息编辑页面

const { routeGuard } = require('../../../utils/route-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { api } = require('../../../utils/api.js');
const userAPI = require('../../../api/user.js');
const { errorToast } = require('../../../utils/error-toast.js');
const { avatarUploadManager } = require('../../../utils/avatar-upload.js');
const { syncManager } = require('../../../utils/sync-manager.js');
const { profileErrorHandler } = require('../../../utils/profile-error-handler.js');

Page({
  data: {
    userInfo: null,
    userRole: '',
    loading: true,
    saving: false,
    uploadingAvatar: false,

    // 表单数据
    formData: {
      name: '',
      nickname: '',
      school: '',
      grade_level: '',
      class_name: '',
      institution_name: '', // 机构名称
      contact_info: '', // 联系方式
    },

    // 原始数据（用于检测变更）
    originalData: {},

    // 表单验证状态
    validation: {
      name: { valid: true, message: '' },
      nickname: { valid: true, message: '' },
      institution_name: { valid: true, message: '' },
      contact_info: { valid: true, message: '' },
    },

    // 年级选项 - 完整的K12教育体系
    gradeOptions: [
      // 小学阶段
      { text: '小学一年级', value: 'primary_1' },
      { text: '小学二年级', value: 'primary_2' },
      { text: '小学三年级', value: 'primary_3' },
      { text: '小学四年级', value: 'primary_4' },
      { text: '小学五年级', value: 'primary_5' },
      { text: '小学六年级', value: 'primary_6' },

      // 初中阶段
      { text: '初中一年级（初一）', value: 'junior_1' },
      { text: '初中二年级（初二）', value: 'junior_2' },
      { text: '初中三年级（初三）', value: 'junior_3' },

      // 高中阶段
      { text: '高中一年级（高一）', value: 'senior_1' },
      { text: '高中二年级（高二）', value: 'senior_2' },
      { text: '高中三年级（高三）', value: 'senior_3' },
    ],

    // 显示控制
    showGradePicker: false,
    gradeDefaultIndex: [0], // 年级选择器的默认索引
    gradeDisplayText: '请选择年级', // 年级显示文本
    focusField: '', // 来自页面参数，用于聚焦特定字段
    hasChanges: false, // 是否有未保存的更改
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('用户信息编辑页面加载', options);

    // 执行路由守卫检查
    const guardResult = await routeGuard.checkPageAuth();
    if (!guardResult.success) {
      return;
    }

    // 设置聚焦字段
    if (options.focus) {
      this.setData({ focusField: options.focus });
    }

    await this.initPage();
  },

  /**
   * 页面卸载时检查未保存的更改
   */
  onUnload() {
    if (this.data.hasChanges) {
      wx.showToast({
        title: '有未保存的更改',
        icon: 'none',
      });
    }
  },

  /**
   * 监听页面返回
   */
  onBackPress() {
    if (this.data.hasChanges) {
      return this.showUnsavedChangesDialog();
    }
    return false;
  },

  /**
   * 初始化页面
   */
  async initPage() {
    try {
      this.setData({ loading: true });

      await this.loadUserInfo();
      this.initFormData();
    } catch (error) {
      console.error('初始化页面失败:', error);
      errorToast.show('页面加载失败，请稍后重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 加载用户信息
   */
  async loadUserInfo() {
    try {
      const [userInfo, userRole] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole(),
      ]);

      this.setData({
        userInfo,
        userRole,
      });
    } catch (error) {
      console.error('加载用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 初始化表单数据
   */
  initFormData() {
    const { userInfo } = this.data;

    const formData = {
      name: userInfo?.name || '',
      nickname: userInfo?.nickname || '',
      school: userInfo?.school || '',
      grade_level: userInfo?.grade_level || '',
      class_name: userInfo?.class_name || '',
      institution_name: userInfo?.institution_name || userInfo?.institution || '', // 兼容旧字段
      contact_info: userInfo?.contact_info || userInfo?.parent_contact || '', // 兼容旧字段
    };

    this.setData({
      formData,
      originalData: { ...formData },
    });

    // 更新年级显示文本
    this.updateGradeDisplayText();
  },

  /**
   * 表单输入处理
   */
  onInput(e) {
    const { field } = e.currentTarget.dataset;
    const { value } = e.detail;

    this.setData({
      [`formData.${field}`]: value,
      hasChanges: true,
    });

    // 实时验证
    this.validateField(field, value);
    this.detectChanges();
  },

  /**
   * 验证字段
   */
  validateField(field, value) {
    let valid = true;
    let message = '';

    switch (field) {
      case 'name':
        if (!value.trim()) {
          valid = false;
          message = '姓名不能为空';
        } else if (value.length < 2 || value.length > 20) {
          valid = false;
          message = '姓名长度应在2-20个字符之间';
        } else if (!/^[\u4e00-\u9fa5a-zA-Z\s]+$/.test(value)) {
          valid = false;
          message = '姓名只能包含中文、英文和空格';
        }
        break;

      case 'nickname':
        if (value && (value.length < 2 || value.length > 15)) {
          valid = false;
          message = '昵称长度应在2-15个字符之间';
        }
        break;

      case 'institution_name':
        if (value && value.length > 50) {
          valid = false;
          message = '机构名称不能超过50个字符';
        }
        break;

      case 'contact_info':
        if (value && value.length > 50) {
          valid = false;
          message = '联系方式不能超过50个字符';
        }
        // 可选：如果输入的是手机号，进行格式验证
        if (value && /^1[3-9]\d{9}$/.test(value.replace(/\s|-/g, ''))) {
          // 是手机号格式，无需额外验证
        } else if (value && value.includes('@')) {
          // 简单的邮箱格式验证
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            valid = false;
            message = '请输入正确的邮箱格式';
          }
        }
        break;
    }

    this.setData({
      [`validation.${field}`]: { valid, message },
    });

    return valid;
  },

  /**
   * 验证整个表单
   */
  validateForm() {
    const { formData } = this.data;
    let isValid = true;

    // 验证所有字段
    Object.keys(formData).forEach(field => {
      const fieldValid = this.validateField(field, formData[field]);
      if (!fieldValid) {
        isValid = false;
      }
    });

    return isValid;
  },

  /**
   * 检测数据变更
   */
  detectChanges() {
    const { formData, originalData } = this.data;
    const hasChanges = JSON.stringify(formData) !== JSON.stringify(originalData);

    this.setData({ hasChanges });
  },

  /**
   * 年级选择器
   */
  onGradePickerTap() {
    console.log('🔧 [Grade Picker Debug] 打开年级选择器');
    console.log('🔧 [Grade Picker Debug] 当前年级值:', this.data.formData.grade_level);
    console.log('🔧 [Grade Picker Debug] 年级选项:', this.data.gradeOptions);

    // 计算当前年级的索引
    const currentGradeIndex = this.data.gradeOptions.findIndex(
      item => item.value === this.data.formData.grade_level,
    );

    const defaultIndex = currentGradeIndex >= 0 ? currentGradeIndex : 0;
    console.log('🔧 [Grade Picker Debug] 默认索引:', defaultIndex);

    this.setData({
      showGradePicker: true,
      gradeDefaultIndex: [defaultIndex],
    });
  },

  onGradePickerChange(e) {
    console.log('🔧 [Grade Picker Debug] 年级选择事件:', e.detail);

    const { value, index } = e.detail;

    // 对于单列选择器：
    // value: 直接是选中项的value值，如 'primary_1'
    // index: 直接是选中项的索引，如 0

    let selectedGrade;

    if (typeof index === 'number' && index >= 0 && index < this.data.gradeOptions.length) {
      // 优先使用index，因为它是最可靠的
      selectedGrade = this.data.gradeOptions[index];
    } else if (value) {
      // 如果index不可用，使用value查找
      selectedGrade = this.data.gradeOptions.find(item => item.value === value);
    } else {
      console.error('年级选择器返回了无效的数据:', { value, index });
      return;
    }

    if (!selectedGrade) {
      console.error('未找到匹配的年级选项:', { value, index });
      return;
    }

    console.log('🔧 [Grade Picker Debug] 选中的年级:', selectedGrade);

    this.setData({
      'formData.grade_level': selectedGrade.value,
      showGradePicker: false,
      hasChanges: true,
    });

    // 更新年级显示文本
    this.updateGradeDisplayText();

    this.detectChanges();
  },
  onGradePickerCancel() {
    this.setData({ showGradePicker: false });
  },

  /**
   * 更新年级显示文本
   */
  updateGradeDisplayText() {
    const gradeValue = this.data.formData.grade_level;
    const grade = this.data.gradeOptions.find(item => item.value === gradeValue);
    const displayText = grade ? grade.text : '请选择年级';

    console.log('🔧 [Grade Display Debug] 更新年级显示文本:', {
      gradeValue,
      grade,
      displayText,
    });

    this.setData({
      gradeDisplayText: displayText,
    });
  },

  /**
   * 获取年级显示文本
   */
  getGradeDisplayText(gradeValue) {
    const grade = this.data.gradeOptions.find(item => item.value === gradeValue);
    return grade ? grade.text : '请选择年级';
  },

  /**
   * 保存用户信息
   */
  async onSave() {
    if (this.data.saving) {
      return;
    }

    // 验证表单
    if (!this.validateForm()) {
      wx.showToast({
        title: '请检查输入信息',
        icon: 'error',
      });
      return;
    }

    try {
      this.setData({ saving: true });

      // 准备发送到后端的数据，转换字段名以匹配后端schema
      const rawData = {
        name: this.data.formData.name,
        nickname: this.data.formData.nickname,
        school: this.data.formData.school,
        grade_level: this.data.formData.grade_level,
        class_name: this.data.formData.class_name,
        institution: this.data.formData.institution_name, // 转换字段名
        parent_contact: this.data.formData.contact_info, // 转换字段名
      };

      // 数据预处理：过滤空值和验证格式
      const updateData = {};

      // 手机号正则验证（与后端保持一致）
      const phoneRegex = /^1[3-9]\d{9}$/;

      Object.keys(rawData).forEach(key => {
        const value = rawData[key];

        // 跳过空字符串和null/undefined
        if (value === null || value === undefined || value === '') {
          return;
        }

        // parent_contact需要特殊验证
        if (key === 'parent_contact') {
          if (phoneRegex.test(value)) {
            updateData[key] = value;
          } else {
            console.warn('联系方式格式不正确，已跳过:', value);
          }
          return;
        }

        // 其他字段直接添加
        updateData[key] = value;
      });

      console.log('🔍 [Profile Save Debug] 发送的数据:', updateData);

      // 调用后端API更新用户信息
      const response = await userAPI.updateProfile(updateData);

      if (response.success) {
        // 更新本地缓存
        const updatedUserInfo = {
          ...this.data.userInfo,
          ...this.data.formData,
        };

        await authManager.updateUserInfo(updatedUserInfo);

        // 触发同步确保数据一致性
        try {
          await syncManager.manualSyncUserInfo();
        } catch (syncError) {
          console.warn('同步失败:', syncError);
          // 同步失败不影响保存成功的提示
        }

        // 重置变更状态
        this.setData({
          hasChanges: false,
          originalData: { ...this.data.formData },
        });

        wx.showToast({
          title: '保存成功',
          icon: 'success',
        });

        // 延迟返回上一页
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        throw new Error(response.message || '保存失败');
      }
    } catch (error) {
      console.error('保存用户信息失败:', error);

      // 使用专业的错误处理器
      const errorResult = await profileErrorHandler.handleUserInfoUpdateError(error, {
        operation: 'save',
        retryFunction: async () => {
          // 准备重试数据，使用相同的数据预处理逻辑
          const rawRetryData = {
            name: this.data.formData.name,
            nickname: this.data.formData.nickname,
            school: this.data.formData.school,
            grade_level: this.data.formData.grade_level,
            class_name: this.data.formData.class_name,
            institution: this.data.formData.institution_name,
            parent_contact: this.data.formData.contact_info,
          };

          // 应用相同的数据过滤逻辑
          const retryData = {};
          const phoneRegex = /^1[3-9]\d{9}$/;

          Object.keys(rawRetryData).forEach(key => {
            const value = rawRetryData[key];

            if (value === null || value === undefined || value === '') {
              return;
            }

            if (key === 'parent_contact') {
              if (phoneRegex.test(value)) {
                retryData[key] = value;
              }
              return;
            }

            retryData[key] = value;
          });

          console.log('🔍 [Profile Retry Debug] 重试数据:', retryData);

          const response = await userAPI.updateProfile(retryData);
          if (response.success) {
            const updatedUserInfo = {
              ...this.data.userInfo,
              ...this.data.formData,
            };
            await authManager.updateUserInfo(updatedUserInfo);
            return response;
          }
          throw new Error(response.message || '保存失败');
        },
      });

      if (errorResult.success) {
        // 重试成功
        this.setData({
          hasChanges: false,
          originalData: { ...this.data.formData },
        });

        wx.showToast({
          title: '保存成功',
          icon: 'success',
        });

        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else if (errorResult.needsLogin) {
        // 需要重新登录
        return;
      }
    } finally {
      this.setData({ saving: false });
    }
  },

  /**
   * 取消编辑
   */
  onCancel() {
    if (this.data.hasChanges) {
      this.showUnsavedChangesDialog();
    } else {
      wx.navigateBack();
    }
  },

  /**
   * 显示未保存更改对话框
   */
  showUnsavedChangesDialog() {
    wx.showModal({
      title: '未保存的更改',
      content: '您有未保存的更改，确定要离开吗？',
      confirmText: '离开',
      cancelText: '继续编辑',
      confirmColor: '#f5222d',
      success: res => {
        if (res.confirm) {
          this.setData({ hasChanges: false });
          wx.navigateBack();
        }
      },
    });
  },

  /**
   * 点击头像 - 头像操作菜单
   */
  onAvatarTap() {
    console.log('点击头像');

    const itemList = ['查看大图', '更换头像'];
    const currentAvatarUrl = this.data.userInfo?.avatarUrl;

    // 如果不是默认头像，添加删除选项
    if (currentAvatarUrl && !currentAvatarUrl.includes('default-avatar')) {
      itemList.push('删除头像');
    }

    wx.showActionSheet({
      itemList,
      success: res => {
        if (res.tapIndex === 0) {
          this.previewAvatar();
        } else if (res.tapIndex === 1) {
          this.changeAvatar();
        } else if (res.tapIndex === 2 && itemList.length > 2) {
          this.deleteAvatar();
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
    if (this.data.uploadingAvatar) {
      return;
    }

    try {
      this.setData({ uploadingAvatar: true });

      const result = await avatarUploadManager.selectAndUploadAvatar();

      if (result && result.success) {
        // 更新页面显示的用户信息
        const updatedUserInfo = {
          ...this.data.userInfo,
          avatarUrl: result.avatarUrl,
        };

        this.setData({
          userInfo: updatedUserInfo,
          hasChanges: true,
        });

        console.log('头像更换成功:', result.avatarUrl);
      }
    } catch (error) {
      console.error('更换头像失败:', error);
      // 错误处理已在 avatarUploadManager 中完成
    } finally {
      this.setData({ uploadingAvatar: false });
    }
  },

  /**
   * 删除头像
   */
  async deleteAvatar() {
    wx.showModal({
      title: '删除头像',
      content: '确定要删除当前头像吗？删除后将使用默认头像。',
      confirmText: '删除',
      cancelText: '取消',
      confirmColor: '#f5222d',
      success: async res => {
        if (res.confirm) {
          try {
            const success = await avatarUploadManager.deleteAvatar();

            if (success) {
              // 更新页面显示的用户信息
              const updatedUserInfo = {
                ...this.data.userInfo,
                avatarUrl: '/assets/images/default-avatar.png',
              };

              this.setData({
                userInfo: updatedUserInfo,
                hasChanges: true,
              });
            }
          } catch (error) {
            console.error('删除头像失败:', error);
          }
        }
      },
    });
  },
});
