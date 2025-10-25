/**
 * 用户管理 API 模块
 * @description 封装用户相关的后端 API 调用
 * @module api/user
 */

const { request } = require('../utils/request.js');

/**
 * 用户 API
 */
const userAPI = {
  /**
   * 微信登录
   * @param {Object} params - 登录参数
   * @param {string} params.code - 微信授权码
   * @param {string} [params.device_type='mini_program'] - 设备类型
   * @param {string} [params.device_id] - 设备ID
   * @param {string} [params.name] - 姓名（新用户补充信息）
   * @param {string} [params.school] - 学校（新用户补充信息）
   * @param {string} [params.grade_level] - 学段（新用户补充信息）
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 登录结果
   */
  wechatLogin(params, config = {}) {
    if (!params || !params.code) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '微信授权码不能为空',
      });
    }

    return request.post(
      'api/v1/auth/wechat-login',
      {
        device_type: 'mini_program',
        ...params,
      },
      {
        skipAuth: true, // 登录请求不需要认证
        showLoading: true,
        loadingText: '登录中...',
        timeout: 15000, // 15秒超时
        ...config,
      },
    );
  },

  /**
   * 刷新访问令牌
   * @param {Object} params - 刷新参数
   * @param {string} params.refresh_token - 刷新令牌
   * @param {string} [params.device_type='mini_program'] - 设备类型
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 刷新结果
   */
  refreshToken(params, config = {}) {
    if (!params || !params.refresh_token) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '刷新令牌不能为空',
      });
    }

    return request.post(
      'api/v1/auth/refresh-token',
      {
        device_type: 'mini_program',
        ...params,
      },
      {
        skipAuth: true, // 刷新请求不需要access token
        showLoading: false,
        timeout: 10000,
        ...config,
      },
    );
  },

  /**
   * 用户登出
   * @param {Object} params - 登出参数
   * @param {string} [params.device_type='mini_program'] - 设备类型
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 登出结果
   */
  logout(params = {}, config = {}) {
    return request.post(
      'api/v1/auth/logout',
      {
        device_type: 'mini_program',
        ...params,
      },
      {
        showLoading: false,
        showError: false, // 登出失败不显示错误，本地清理即可
        timeout: 5000,
        ...config,
      },
    );
  },

  /**
   * 获取当前用户信息
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 用户信息
   */
  getCurrentUser(config = {}) {
    return request.get(
      'api/v1/auth/me',
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 更新用户信息
   * @param {Object} params - 更新参数
   * @param {string} [params.name] - 姓名
   * @param {string} [params.nickname] - 昵称
   * @param {string} [params.avatar_url] - 头像URL
   * @param {string} [params.school] - 学校
   * @param {string} [params.grade_level] - 学段
   * @param {string} [params.class_name] - 班级
   * @param {string} [params.parent_contact] - 家长联系电话
   * @param {string} [params.parent_name] - 家长姓名
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新结果
   */
  updateProfile(params, config = {}) {
    return request.put('/api/v1/auth/profile', params, {
      showLoading: true,
      loadingText: '保存中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 获取用户活动记录
   * @param {Object} params - 查询参数
   * @param {number} [params.limit=10] - 返回记录数量
   * @param {number} [params.offset=0] - 偏移量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 活动记录
   */
  getActivities(params = {}, config = {}) {
    const { limit = 10, offset = 0 } = params;

    return request.get(
      'api/v1/users/activities',
      {
        limit,
        offset,
      },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取用户统计信息
   * @param {Object} params - 查询参数
   * @param {string} [params.time_range='30d'] - 时间范围
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 统计信息
   */
  getStats(params = {}, config = {}) {
    const { time_range = '30d' } = params;

    return request.get(
      'api/v1/users/stats',
      {
        time_range,
      },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 上传用户头像
   * @param {string} filePath - 本地文件路径
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 上传结果
   */
  uploadAvatar(filePath, config = {}) {
    return request.upload(
      'api/v1/files/upload',
      filePath,
      'file',
      { category: 'avatar' },
      {
        showLoading: true,
        loadingText: '上传头像中...',
        showError: true,
        ...config,
      },
    );
  },

  /**
   * 切换用户角色
   * @param {Object} params - 切换参数
   * @param {string} params.role - 新角色 (student/parent/teacher)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 切换结果
   */
  switchRole(params, config = {}) {
    if (!params || !params.role) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '角色不能为空',
      });
    }

    return request.post('api/v1/users/switch-role', params, {
      showLoading: true,
      loadingText: '切换中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 检查用户权限
   * @param {Object} params - 检查参数
   * @param {string} params.permission - 权限名称
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 权限检查结果
   */
  checkPermission(params, config = {}) {
    if (!params || !params.permission) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '权限名称不能为空',
      });
    }

    return request.get('api/v1/users/permissions/check', params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取用户设置
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 用户设置
   */
  getSettings(config = {}) {
    return request.get(
      'api/v1/users/settings',
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 更新用户设置
   * @param {Object} params - 设置参数
   * @param {boolean} [params.notification_enabled] - 是否启用通知
   * @param {Object} [params.preferences] - 偏好设置
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新结果
   */
  updateSettings(params, config = {}) {
    return request.put('api/v1/users/settings', params, {
      showLoading: true,
      loadingText: '保存设置中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 删除用户账户
   * @param {Object} params - 删除参数
   * @param {string} params.reason - 删除原因
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 删除结果
   */
  deleteAccount(params, config = {}) {
    if (!params || !params.reason) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '删除原因不能为空',
      });
    }

    return request.delete('api/v1/users/account', params, {
      showLoading: true,
      loadingText: '删除账户中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 获取用户偏好设置
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 偏好设置
   */
  getPreferences(config = {}) {
    return request.get(
      'api/v1/user/preferences',
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 更新用户偏好设置
   * @param {Object} params - 偏好参数
   * @param {string} [params.learning_style] - 学习风格
   * @param {Array} [params.preferred_subjects] - 偏好学科
   * @param {string} [params.difficulty_preference] - 难度偏好
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新结果
   */
  updatePreferences(params, config = {}) {
    return request.put('api/v1/user/preferences', params, {
      showLoading: true,
      loadingText: '保存偏好中...',
      showError: true,
      ...config,
    });
  },
};

module.exports = userAPI;
