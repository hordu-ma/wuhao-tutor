/**
 * 认证相关API
 * 用户登录、注册、登出等认证功能
 */

import http from './http'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  ApiResponse
} from '@/types'

/**
 * 认证API类
 */
export class AuthAPI {
  /**
   * 用户登录
   */
  static async login(data: LoginRequest): Promise<LoginResponse> {
    return http.post<LoginResponse>('/auth/login', data, {
      skipAuth: true,
      showLoading: true,
      loadingText: '正在登录...',
    })
  }

  /**
   * 用户注册
   */
  static async register(data: RegisterRequest): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/register', data, {
      skipAuth: true,
      showLoading: true,
      loadingText: '正在注册...',
      showSuccessMessage: true,
      successMessage: '注册成功！',
    })
  }

  /**
   * 用户登出
   */
  static async logout(): Promise<void> {
    return http.post<void>('/auth/logout', {}, {
      showSuccessMessage: true,
      successMessage: '已安全退出',
    })
  }

  /**
   * 刷新访问令牌
   */
  static async refreshToken(): Promise<LoginResponse> {
    const refreshToken = localStorage.getItem('refresh_token') ||
      sessionStorage.getItem('refresh_token')

    return http.post<LoginResponse>('/auth/refresh',
      { refresh_token: refreshToken },
      { skipAuth: true }
    )
  }

  /**
   * 获取当前用户信息
   */
  static async getCurrentUser(): Promise<User> {
    return http.get<User>('/auth/me')
  }

  /**
   * 修改密码
   */
  static async changePassword(data: {
    old_password: string
    new_password: string
    confirm_password: string
  }): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/change-password', data, {
      showSuccessMessage: true,
      successMessage: '密码修改成功！',
    })
  }

  /**
   * 忘记密码 - 发送重置邮件
   */
  static async forgotPassword(email: string): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/forgot-password',
      { email },
      {
        skipAuth: true,
        showSuccessMessage: true,
        successMessage: '密码重置邮件已发送，请查收！',
      }
    )
  }

  /**
   * 重置密码
   */
  static async resetPassword(data: {
    token: string
    new_password: string
    confirm_password: string
  }): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/reset-password', data, {
      skipAuth: true,
      showSuccessMessage: true,
      successMessage: '密码重置成功！',
    })
  }

  /**
   * 验证邮箱
   */
  static async verifyEmail(token: string): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/verify-email',
      { token },
      {
        skipAuth: true,
        showSuccessMessage: true,
        successMessage: '邮箱验证成功！',
      }
    )
  }

  /**
   * 重新发送验证邮件
   */
  static async resendVerification(email: string): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/resend-verification',
      { email },
      {
        skipAuth: true,
        showSuccessMessage: true,
        successMessage: '验证邮件已重新发送！',
      }
    )
  }

  /**
   * 检查用户名是否可用
   */
  static async checkUsername(username: string): Promise<{ available: boolean }> {
    return http.get<{ available: boolean }>('/auth/check-username', {
      params: { username },
      skipAuth: true,
    })
  }

  /**
   * 检查邮箱是否可用
   */
  static async checkEmail(email: string): Promise<{ available: boolean }> {
    return http.get<{ available: boolean }>('/auth/check-email', {
      params: { email },
      skipAuth: true,
    })
  }

  /**
   * 更新用户资料
   */
  static async updateProfile(data: {
    name?: string
    nickname?: string
    email?: string
    avatar?: string
    avatar_url?: string
    school?: string
    grade_level?: string
    class_name?: string
    institution?: string
    parent_contact?: string
    parent_name?: string
    notification_enabled?: boolean
  }): Promise<User> {
    const response = await http.put<any>('/auth/profile', data, {
      showSuccessMessage: true,
      successMessage: '资料更新成功！',
    })
    
    // 处理后端返回的数据结构
    // 后端可能返回 { success: true, data: user, message: '...' } 或直接返回 user
    const user = response.data || response
    
    // 确保 avatar 和 avatar_url 同步
    if (user.avatar_url && !user.avatar) {
      user.avatar = user.avatar_url
    }
    
    return user
  }

  /**
   * 上传用户头像
   */
  static async uploadAvatar(file: File): Promise<{ avatar_url: string }> {
    const formData = new FormData()
    formData.append('file', file)

    return http.upload<{ avatar_url: string }>('/auth/avatar', formData, {
      showLoading: true,
      loadingText: '正在上传头像...',
      showSuccessMessage: true,
      successMessage: '头像上传成功！',
    })
  }

  /**
   * 获取登录历史
   */
  static async getLoginHistory(params?: {
    page?: number
    size?: number
  }) {
    return http.get('/auth/login-history', { params })
  }

  /**
   * 注销账户（软删除）
   */
  static async deactivateAccount(password: string): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/deactivate',
      { password },
      {
        showSuccessMessage: true,
        successMessage: '账户已注销',
      }
    )
  }

  /**
   * 启用两步验证
   */
  static async enableTwoFactor(): Promise<{
    qr_code: string
    secret_key: string
  }> {
    return http.post('/auth/2fa/enable')
  }

  /**
   * 确认两步验证
   */
  static async confirmTwoFactor(data: {
    secret_key: string
    verification_code: string
  }): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/2fa/confirm', data, {
      showSuccessMessage: true,
      successMessage: '两步验证已启用！',
    })
  }

  /**
   * 禁用两步验证
   */
  static async disableTwoFactor(data: {
    password: string
    verification_code: string
  }): Promise<ApiResponse> {
    return http.post<ApiResponse>('/auth/2fa/disable', data, {
      showSuccessMessage: true,
      successMessage: '两步验证已禁用！',
    })
  }
}

// 导出默认实例
export default AuthAPI
